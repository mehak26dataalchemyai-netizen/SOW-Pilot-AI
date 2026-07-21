/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae2fd',
          300: '#7cc8fc',
          400: '#38a9f8',
          500: '#0e8ce2',
          600: '#026fc2',
          700: '#03589c',
          800: '#074b81',
          900: '#0c3f6c',
          950: '#082848',
        },
        slate: {
          850: '#141e30',
          900: '#0f172a',
          950: '#020617',
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        'glass-light': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
        'glass-dark': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
