const theme = require('./styles/tailwind.theme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./pages/**/*.{js,jsx}', './components/**/*.{js,jsx}', './src/**/*.{js,jsx,ts,tsx}', './services/**/*.{js,jsx}'],
  theme: {
    extend: theme
  },
  plugins: []
};
