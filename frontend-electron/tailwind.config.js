/**** @type {import('tailwindcss').Config} ****/
export default {
  content: ["./src/**/*.{ts,tsx,html}"],
  theme: { extend: {} },
  darkMode: 'class',
  plugins: [require('@tailwindcss/forms')]
}
