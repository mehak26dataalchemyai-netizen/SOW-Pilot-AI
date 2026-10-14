import os
import json
import math
import re
from typing import List, Dict, Tuple, Any

class SimpleRetriever:
    """
    A lightweight, pure-Python in-memory search engine using TF-IDF and Cosine Similarity.
    Used to split large SOW documents (up to 400+ pages) into semantic chunks and retrieve
    the most relevant context for LLM agents. Requires zero external dependencies.
    """
    def __init__(self, document_text: str, chunk_size: int = 1500, overlap: int = 300):
        self.chunks = self._chunk_text(document_text, chunk_size, overlap)
        self.vocab: Dict[str, int] = {}
        self.chunk_vectors: List[Dict[int, float]] = []
        self.idf: Dict[int, float] = {}
        self._build_index()

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        # Split by paragraph first to preserve semantic boundaries
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_len = len(para)
            if current_len + para_len > chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                # overlapping strategy: if single paragraph is huge, split it by sentences
                if para_len > chunk_size:
                    sentences = re.split(r'(?<=[.?!])\s+', para)
                    sub_chunk = []
                    sub_len = 0
                    for sent in sentences:
                        if sub_len + len(sent) > chunk_size:
                            if sub_chunk:
                                chunks.append(' '.join(sub_chunk))
                            sub_chunk = [sent]
                            sub_len = len(sent)
                        else:
                            sub_chunk.append(sent)
                            sub_len += len(sent)
                    if sub_chunk:
                        current_chunk = sub_chunk
                        current_len = sub_len
                else:
                    current_chunk = [para]
                    current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 2
                
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
        # Fallback to character-based chunking with overlap if paragraph split yielded nothing
        if not chunks:
            i = 0
            while i < len(text):
                chunks.append(text[i:i+chunk_size])
                i += chunk_size - overlap
                
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        # Simple word tokenization matching alphabetic terms with length >= 2
        return re.findall(r'\b\w{2,}\b', text.lower())

    def _build_index(self):
        if not self.chunks:
            return

        # 1. Build vocabulary and count doc frequencies
        doc_counts: Dict[str, int] = {}
        tokenized_chunks = [self._tokenize(chunk) for chunk in self.chunks]
        
        for tokens in tokenized_chunks:
            seen = set(tokens)
            for token in seen:
                doc_counts[token] = doc_counts.get(token, 0) + 1
                
        # Map tokens to IDs
        self.vocab = {token: idx for idx, token in enumerate(doc_counts.keys())}
        num_docs = len(self.chunks)
        
        # Calculate IDF
        for token, count in doc_counts.items():
            token_id = self.vocab[token]
            self.idf[token_id] = math.log((1 + num_docs) / (1 + count)) + 1
            
        # Calculate TF-IDF vectors for chunks
        for tokens in tokenized_chunks:
            tf: Dict[int, int] = {}
            for token in tokens:
                if token in self.vocab:
                    token_id = self.vocab[token]
                    tf[token_id] = tf.get(token_id, 0) + 1
                    
            vector: Dict[int, float] = {}
            length = 0.0
            for token_id, freq in tf.items():
                tfidf_val = freq * self.idf[token_id]
                vector[token_id] = tfidf_val
                length += tfidf_val ** 2
                
            length = math.sqrt(length)
            if length > 0:
                vector = {tid: val / length for tid, val in vector.items()}
            self.chunk_vectors.append(vector)

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.chunks:
            return self.chunks[:top_k]
            
        # Build query vector
        query_tf: Dict[int, int] = {}
        for token in query_tokens:
            if token in self.vocab:
                token_id = self.vocab[token]
                query_tf[token_id] = query_tf.get(token_id, 0) + 1
                
        query_vector: Dict[int, float] = {}
        length = 0.0
        for token_id, freq in query_tf.items():
            tfidf_val = freq * self.idf[token_id]
            query_vector[token_id] = tfidf_val
            length += tfidf_val ** 2
            
        length = math.sqrt(length)
        if length > 0:
            query_vector = {tid: val / length for tid, val in query_vector.items()}
        else:
            return self.chunks[:top_k]
            
        # Compute cosine similarity
        scores: List[Tuple[int, float]] = []
        for idx, chunk_vector in enumerate(self.chunk_vectors):
            dot_product = 0.0
            for tid, val in query_vector.items():
                if tid in chunk_vector:
                    dot_product += val * chunk_vector[tid]
            scores.append((idx, dot_product))
            
        # Sort and return top_k chunks
        scores.sort(key=lambda x: x[1], reverse=True)
        return [self.chunks[idx] for idx, score in scores[:top_k]]


try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class ProperEmbeddingFunction:
    """
    A proper vector embedding function. 
    1. Attempts to call Google Gemini Embeddings API (models/text-embedding-04) if GEMINI_API_KEY is present.
    2. Otherwise, uses Chroma's built-in SentenceTransformer ONNX model locally.
    3. If that fails (e.g. missing dependencies), falls back to our custom hashed vector model.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    @staticmethod
    def name() -> str:
        """Required by chromadb >= 0.5's EmbeddingFunction interface so it can label/serialize this function."""
        return "sowpilot_proper_embedding_function"

    def get_config(self) -> Dict[str, Any]:
        return {"dimension": self.dimension}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "ProperEmbeddingFunction":
        return ProperEmbeddingFunction(dimension=config.get("dimension", 384))

    def embed_query(self, input: List[str]) -> List[List[float]]:
        """Required by chromadb >= 0.5's EmbeddingFunction interface for query-time embedding."""
        return self.__call__(input)

    def __call__(self, input: List[str]) -> List[List[float]]:
        # A. Try Gemini API
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                response = genai.embed_content(
                    model="models/text-embedding-04",
                    contents=input,
                    task_type="retrieval_document"
                )
                if 'embeddings' in response:
                    return response['embeddings']
            except Exception as e:
                print(f"[VECTOR STORE EMBEDDING] Gemini API failed: {e}. Trying local fallback.")

        # B. Try Chroma's default local ONNX embedding function
        try:
            from chromadb.utils import embedding_functions
            default_ef = embedding_functions.DefaultEmbeddingFunction()
            return default_ef(input)
        except Exception as e:
            # Silence warning if it's just local loading fallback info
            pass

        # C. Custom tf-idf hash fallback (fully zero-dependency, local and fast)
        import re, math
        embeddings = []
        for text in input:
            tokens = re.findall(r'\b\w{2,}\b', text.lower())
            vector = [0.0] * self.dimension
            for t in tokens:
                idx = abs(hash(t)) % self.dimension
                vector[idx] += 1.0
            norm = math.sqrt(sum(v**2 for v in vector))
            if norm > 0:
                vector = [v / norm for v in vector]
            embeddings.append(vector)
        return embeddings


class PersistentVectorStore:
    """
    A persistent vector database.
    Attempts to use the real 'chromadb' package if installed and functional.
    Otherwise, falls back to a custom, pure-Python local persistent store using TF-IDF.
    """
    def __init__(self, db_path: str = None):
        # Always initialize custom database variables to prevent AttributeError on runtime fallback
        if not db_path:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store.json")
        self.db_path = db_path
        self.collections: Dict[str, List[Dict[str, Any]]] = {}
        
        self.use_real_chroma = HAS_CHROMADB
        if self.use_real_chroma:
            try:
                # Store ChromaDB SQLite files in a dedicated local directory
                persist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db_data")
                self.client = chromadb.PersistentClient(path=persist_dir)
                print("[VECTOR STORE] Real ChromaDB client initialized successfully.")
            except Exception as e:
                print(f"[VECTOR STORE WARNING] Failed to initialize real ChromaDB client, using custom fallback: {e}")
                self.use_real_chroma = False

        # Load the custom database as fallback data immediately, so it's ready in case real Chroma fails later
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.collections = json.load(f)
            except Exception as e:
                print(f"[VECTOR STORE ERROR] Failed to load store: {e}")
                self.collections = {}
        else:
            self.collections = {
                "candidate_resumes": [],
                "sow_requirements": []
            }
            self.save()

    def save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.collections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[VECTOR STORE ERROR] Failed to save store: {e}")

    def add_document(self, collection_name: str, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        if self.use_real_chroma:
            try:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=ProperEmbeddingFunction()
                )
                collection.upsert(
                    documents=[text],
                    metadatas=[metadata or {}],
                    ids=[doc_id]
                )
                return
            except Exception as e:
                print(f"[VECTOR STORE WARNING] Real ChromaDB upsert failed: {e}. Falling back to custom store.")
                self.use_real_chroma = False
                
        # Custom store fallback
        if collection_name not in self.collections:
            self.collections[collection_name] = []
        self.collections[collection_name] = [d for d in self.collections[collection_name] if d.get("id") != doc_id]
        self.collections[collection_name].append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        self.save()

    def query(self, collection_name: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.use_real_chroma:
            try:
                # Attempt to query from real ChromaDB
                try:
                    collection = self.client.get_collection(
                        name=collection_name,
                        embedding_function=ProperEmbeddingFunction()
                    )
                except Exception:
                    # Create if it doesn't exist yet
                    collection = self.client.get_or_create_collection(
                        name=collection_name,
                        embedding_function=ProperEmbeddingFunction()
                    )
                    
                results = collection.query(
                    query_texts=[query_text],
                    n_results=top_k
                )
                
                docs = []
                if results and "documents" in results and results["documents"]:
                    documents = results["documents"][0]
                    ids = results["ids"][0]
                    metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(documents)
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(documents)
                    
                    for i in range(len(documents)):
                        # Convert distance to score
                        score = 1.0 - distances[i] if distances[i] <= 1.0 else 0.0
                        docs.append({
                            "id": ids[i],
                            "text": documents[i],
                            "metadata": metadatas[i],
                            "score": score
                        })
                return docs
            except Exception as e:
                print(f"[VECTOR STORE WARNING] Real ChromaDB query failed: {e}. Falling back to custom store.")
                self.use_real_chroma = False

        # Custom store fallback
        docs = self.collections.get(collection_name, [])
        if not docs:
            return []
            
        doc_texts = [d["text"] for d in docs]
        
        def tokenize(text: str) -> List[str]:
            return re.findall(r'\b\w{2,}\b', text.lower())
            
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return docs[:top_k]
            
        doc_counts: Dict[str, int] = {}
        tokenized_docs = [tokenize(t) for t in doc_texts]
        
        for tokens in tokenized_docs:
            seen = set(tokens)
            for token in seen:
                doc_counts[token] = doc_counts.get(token, 0) + 1
                
        vocab = {token: idx for idx, token in enumerate(doc_counts.keys())}
        num_docs = len(docs)
        
        idf = {}
        for token, count in doc_counts.items():
            token_id = vocab[token]
            idf[token_id] = math.log((1 + num_docs) / (1 + count)) + 1
            
        doc_vectors = []
        for tokens in tokenized_docs:
            tf = {}
            for token in tokens:
                if token in vocab:
                    token_id = vocab[token]
                    tf[token_id] = tf.get(token_id, 0) + 1
            vector = {}
            length = 0.0
            for token_id, freq in tf.items():
                tfidf_val = freq * idf[token_id]
                vector[token_id] = tfidf_val
                length += tfidf_val ** 2
            length = math.sqrt(length)
            if length > 0:
                vector = {tid: val / length for tid, val in vector.items()}
            doc_vectors.append(vector)
            
        query_tf = {}
        for token in query_tokens:
            if token in vocab:
                token_id = vocab[token]
                query_tf[token_id] = query_tf.get(token_id, 0) + 1
        query_vector = {}
        length = 0.0
        for token_id, freq in query_tf.items():
            tfidf_val = freq * idf[token_id]
            query_vector[token_id] = tfidf_val
            length += tfidf_val ** 2
        length = math.sqrt(length)
        if length > 0:
            query_vector = {tid: val / length for tid, val in query_vector.items()}
        else:
            return docs[:top_k]
            
        scores = []
        for idx, doc_vector in enumerate(doc_vectors):
            dot_product = 0.0
            for tid, val in query_vector.items():
                if tid in doc_vector:
                    dot_product += val * doc_vector[tid]
            scores.append((idx, dot_product))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            doc_copy = dict(docs[idx])
            doc_copy["score"] = score
            results.append(doc_copy)
        return results

