"""Renders the generated client_proposal (persuasive prose + real cost/timeline data) into a properly
formatted PDF — headings, bullet points, and real tables for the investment breakdown and delivery
schedule — instead of the long wall of plain-text paragraphs the proposal email used to be."""
import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, HRFlowable
)

_ACCENT = colors.HexColor("#2d4a6b")
_ACCENT_LIGHT = colors.HexColor("#eef2f6")
_TEXT = colors.HexColor("#1f2937")
_MUTED = colors.HexColor("#6b7280")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("PropTitle", parent=base["Title"], fontSize=22, textColor=_ACCENT, spaceAfter=4),
        "meta": ParagraphStyle("PropMeta", parent=base["Normal"], fontSize=10, textColor=_MUTED, spaceAfter=18),
        "h2": ParagraphStyle("PropH2", parent=base["Heading2"], fontSize=13, textColor=_ACCENT, spaceBefore=18, spaceAfter=8),
        "body": ParagraphStyle("PropBody", parent=base["Normal"], fontSize=10.5, textColor=_TEXT, leading=16, spaceAfter=6),
        "bullet": ParagraphStyle("PropBullet", parent=base["Normal"], fontSize=10.5, textColor=_TEXT, leading=15),
        "tcell": ParagraphStyle("PropTCell", parent=base["Normal"], fontSize=9.5, textColor=_TEXT, leading=13),
        "tcellhead": ParagraphStyle("PropTCellHead", parent=base["Normal"], fontSize=9.5, textColor=colors.white, leading=13, fontName="Helvetica-Bold"),
    }
    return styles


def _money(val) -> str:
    try:
        return f"${float(val):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


# ReportLab's built-in Helvetica font (WinAnsiEncoding) renders em/en dashes and curly quotes fine,
# but has no glyph for U+2011 NON-BREAKING HYPHEN — a character LLM output frequently uses in compound
# words like "production-ready" or "risk-managed". Left unsanitized, those render as solid black boxes
# throughout the PDF. Normalize the handful of Unicode punctuation marks known to cause this.
_CHAR_FIXES = {
    "‑": "-",   # non-breaking hyphen
    "‐": "-",   # hyphen
    " ": " ",   # non-breaking space
    "​": "",    # zero-width space
}


def _sanitize(text: str) -> str:
    if not text:
        return text
    for bad, good in _CHAR_FIXES.items():
        text = text.replace(bad, good)
    return text


def _sanitize_deep(value):
    """Recursively applies _sanitize() to every string in a dict/list, so callers don't need to
    remember to sanitize each field individually."""
    if isinstance(value, str):
        return _sanitize(value)
    if isinstance(value, dict):
        return {k: _sanitize_deep(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_deep(v) for v in value]
    return value


def generate_proposal_pdf(
    client_proposal: Dict[str, Any],
    project_name: str,
    client: str,
    budget: Dict[str, Any] = None,
    timeline: Dict[str, Any] = None,
    resources: Dict[str, Any] = None,
) -> bytes:
    client_proposal = _sanitize_deep(client_proposal or {})
    project_name = _sanitize(project_name or "")
    client = _sanitize(client or "")
    budget = budget or {}
    timeline = timeline or {}
    resources = resources or {}
    styles = _styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )
    story = []

    # --- Header ---
    story.append(Paragraph(f"Proposal: {project_name}", styles["title"]))
    story.append(Paragraph(
        f"Prepared for {client or 'our client'} &nbsp;|&nbsp; {datetime.now().strftime('%B %d, %Y')}",
        styles["meta"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=_ACCENT, spaceAfter=14))

    greeting = (client_proposal.get("client_greeting") or "").strip()
    if greeting:
        story.append(Paragraph(greeting, styles["body"]))
        story.append(Spacer(1, 8))

    def add_text_section(title: str, text: str):
        text = (text or "").strip()
        if not text:
            return
        story.append(Paragraph(title, styles["h2"]))
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, styles["body"]))

    add_text_section("Why Us", client_proposal.get("why_us_summary"))
    add_text_section("Proposed Solution", client_proposal.get("proposed_solution_narrative"))
    add_text_section("Our Team", client_proposal.get("team_and_experience_narrative"))

    # --- Investment: narrative + real cost breakdown as a table, not prose numbers ---
    investment_text = (client_proposal.get("investment_summary") or "").strip()
    if investment_text or budget:
        story.append(Paragraph("Investment", styles["h2"]))
        if investment_text:
            story.append(Paragraph(investment_text, styles["body"]))
            story.append(Spacer(1, 8))

        rows = [[Paragraph("Item", styles["tcellhead"]), Paragraph("Amount", styles["tcellhead"])]]
        line_items = [
            ("Development", budget.get("development_cost")),
            ("Cloud & Infrastructure", (budget.get("cloud_cost") or 0) + (budget.get("infrastructure_cost") or 0)),
            ("Testing & QA", budget.get("testing_cost")),
            ("Post-Launch Support", budget.get("support_cost")),
            ("Risk Contingency", budget.get("buffer_cost")),
        ]
        for label, val in line_items:
            if val:
                rows.append([Paragraph(label, styles["tcell"]), Paragraph(_money(val), styles["tcell"])])
        total = budget.get("bid_price") or budget.get("total_cost")
        if total:
            rows.append([
                Paragraph("<b>Total Investment</b>", styles["tcell"]),
                Paragraph(f"<b>{_money(total)}</b>", styles["tcell"]),
            ])

        if len(rows) > 1:
            t = Table(rows, colWidths=[3.8 * inch, 2.2 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ACCENT_LIGHT]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("LINEABOVE", (0, -1), (-1, -1), 1, _ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(t)
        story.append(Spacer(1, 6))

    # --- Timeline: narrative + per-role schedule as a table ---
    timeline_text = (client_proposal.get("timeline_commitment") or "").strip()
    resource_schedule = timeline.get("resource_schedule") or []
    if timeline_text or resource_schedule:
        story.append(Paragraph("Delivery Timeline", styles["h2"]))
        if timeline_text:
            story.append(Paragraph(timeline_text, styles["body"]))
            story.append(Spacer(1, 8))

        if resource_schedule:
            rows = [[
                Paragraph("Role", styles["tcellhead"]),
                Paragraph("Engaged Weeks", styles["tcellhead"]),
            ]]
            for entry in resource_schedule:
                role = entry.get("role", "")
                start = entry.get("start_week")
                end = entry.get("end_week")
                if role and start is not None and end is not None:
                    rows.append([
                        Paragraph(role, styles["tcell"]),
                        Paragraph(f"Week {start} – Week {end}", styles["tcell"]),
                    ])
            if len(rows) > 1:
                t = Table(rows, colWidths=[3.8 * inch, 2.2 * inch])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ACCENT_LIGHT]),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(t)
        story.append(Spacer(1, 6))

    # --- Differentiators: real bullet list, not a paragraph ---
    differentiators = client_proposal.get("differentiators") or []
    if differentiators:
        story.append(Paragraph("Why This Proposal Stands Out", styles["h2"]))
        items = [ListItem(Paragraph(d, styles["bullet"]), bulletColor=_ACCENT) for d in differentiators if d]
        story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=18, spaceBefore=2, bulletFontSize=10))
        story.append(Spacer(1, 6))

    add_text_section("Next Steps", client_proposal.get("next_steps"))

    doc.build(story)
    return buf.getvalue()
