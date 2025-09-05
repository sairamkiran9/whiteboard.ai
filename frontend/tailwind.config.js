/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'excalidraw-bg': '#fafafb',
        'suggestion': {
          'primary': '#007bff',
          'secondary': '#6c757d',
          'success': '#28a745',
          'warning': '#ffc107',
          'error': '#dc3545'
        }
      }
    },
  },
  plugins: [],
}