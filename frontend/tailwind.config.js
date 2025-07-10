/**
 * File: frontend/tailwind.config.js
 * Tailwind CSS configuration defining grid layout and theme for OriginFlow UI.
 * Extends default theme with custom grid areas and responsive columns.
 */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      gridTemplateColumns: {
        'layout-desktop': '180px 1fr',
        'layout-desktop-collapsed': '60px 1fr',
      },
      gridTemplateRows: {
        'layout-desktop': '48px 48px 1fr 40px',
      },
      gridTemplateAreas: {
        'layout-desktop': [
          "sidebar topbar",
          "sidebar action-bar",
          "sidebar workspace",
          "sidebar statusbar",
        ],
      },
      animation: {
        spin: 'spin 1s linear infinite',
      },
      keyframes: {
        spin: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
}
