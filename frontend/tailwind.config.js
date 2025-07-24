/**
 * File: frontend/tailwind.config.js
 * Tailwind CSS configuration defining grid layout and theme for OriginFlow UI.
 * Extends default theme with custom grid areas and responsive columns.
 */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      gridTemplateColumns: {
        'layout-collapsed': '64px 1fr 350px',
        'layout-expanded': '250px 1fr 350px',
      },
      gridTemplateRows: {
        layout: '64px 48px 1fr 48px',
      },
      gridArea: {
        header: 'header',
        toolbar: 'toolbar',
        sidebar: 'sidebar',
        main: 'main',
        chat: 'chat',
        chatInput: 'chatInput',
        status: 'status',
      },
    },
  },
  plugins: [],
};
