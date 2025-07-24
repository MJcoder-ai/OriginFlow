# OriginFlow UI Guidelines (v3.2.3)

This document defines the implementation specification for all major UI components in the OriginFlow app. It provides layout structure, responsive behavior, styling patterns, accessibility expectations, and code patterns for consistent implementation.

---

## ✨ Global Layout

OriginFlow uses a **CSS Grid layout** wrapped in a full-height flex column to structure the app into consistent rows and columns.

```tsx
<div className="h-screen flex flex-col">
  <div
    className="grid h-full w-full"
    style={{
      gridTemplateColumns: 'auto 1fr 350px',
      gridTemplateRows: '64px 48px 1fr 48px',
      gridTemplateAreas: `
        "sidebar-header header      chat-history"
        "sidebar        toolbar     chat-history"
        "sidebar        main        chat-history"
        "sidebar-footer status      chat-footer"
      `,
      columnGap: '4px',
      rowGap: '4px',
    }}
  >
    <SidebarHeader />
    <Header />
    <ChatHistory />
    <Sidebar />
    <Toolbar />
    <MainPanel />
    <SidebarFooter />
    <StatusBar />
    <ChatInput />
  </div>
</div>
```

### Grid Area Definitions

| Area           | Grid Area Name   |
| -------------- | ---------------- |
| Sidebar Header | `sidebar-header` |
| Header         | `header`         |
| Toolbar        | `toolbar`        |
| Main Panel     | `main`           |
| Sidebar        | `sidebar`        |
| Sidebar Footer | `sidebar-footer` |
| Chat History   | `chat-history`   |
| Status Bar     | `status`         |
| Chat Input     | `chat-footer`    |

---

## 🔀 View-specific Layouts

### Projects View – Canvas Builder

- Render `<ProjectCanvas />` in the `main` area
- Sidebar contains `FileStagingArea` for component uploads (PDF/CSV)
- Users drag datasheets into canvas to create nodes
- Canvas uses `<Workspace />` with draggable and connectable components
- Component ports allow linking with mouse drag
- Add visual border to canvas container (`border-dashed`)
- Overflow should scroll when nodes exceed viewport

### Components View – Datasheet Split

- Render `<DatasheetSplitView />` in the `main` area
- Left pane: PDF viewer (`<iframe>`, 50% width, scrollable)
- Right pane: Form with editable parsed data, grouped into sections
- Include Save and Confirm & Close buttons in sticky toolbar
- ComponentCanvas handles drag/drop from sidebar and triggers `/api/v1/parse-datasheet`

### Dynamic Routing Example

```tsx
const route = useAppStore((s) => s.route);
<main className="grid-in-main overflow-hidden">
  {route === 'projects' && <ProjectCanvas />}
  {route === 'components' && <DatasheetSplitView />}
</main>
```

---

## 📱 Responsive Behavior

### ≥ 1280px (Full Layout)

- 3-column grid layout

### 768–1279px (Tablet)

- ChatSidebar becomes overlay

```tsx
const { chatOverlayOpen } = useAppStore();
{chatOverlayOpen && (
  <div className="chat-backdrop" onClick={closeChat} />
  <div ref={chatRef} className="chat-sidebar">...</div>
)}
```

### < 768px (Mobile)

- Stacked grid layout

```tsx
.grid {
  grid-template-columns: 1fr;
  grid-template-rows: 64px 48px 1fr auto 48px;
  grid-template-areas:
    "header"
    "toolbar"
    "main"
    "chat-footer"
    "status";
}
```

### Mobile Drawer (Optional)

```tsx
<nav className="fixed inset-0 z-50 bg-white p-4 transform transition-transform" aria-modal="true">
  <ul className="space-y-3">{navItems}</ul>
</nav>
```

---

## 📏 Sidebar Width Sync

```css
:root {
  --sidebar-width-expanded: 250px;
  --sidebar-width-collapsed: 64px;
}
```

```tsx
<aside className={
  `transition-[width] duration-200 ${sidebarCollapsed ? 'w-[var(--sidebar-width-collapsed)]' : 'w-[var(--sidebar-width-expanded)]'}`
}>
```

---

## 💬 ChatPanel Enhancements

- Chat area should scroll independently
- Auto-scroll to bottom on new message
- Prevent scroll if user is reviewing history

```tsx
<div aria-live="polite" aria-atomic="false" className="chat-messages">
  {chatMessages.map(msg => <ChatBubble {...msg} />)}
</div>
```

```tsx
const [userScrolling, setUserScrolling] = useState(false);
useEffect(() => {
  if (!userScrolling) scrollToBottom();
}, [chatMessages]);
```

---

## 📝 ChatInput Enhancements

```tsx
const MAX_CHAT_LENGTH = 2048;
const WARNING_THRESHOLD = 1800;
```

```tsx
<form onSubmit={handleSubmit} className="flex flex-col gap-2 px-4 py-2">
  <textarea
    value={value}
    maxLength={MAX_CHAT_LENGTH}
    aria-label="Compose message"
    placeholder="Type your message..."
    className="resize-none overflow-hidden"
  />
  <div className="flex justify-between text-xs text-gray-500">
    <span>{value.length}/{MAX_CHAT_LENGTH}</span>
    <button type="submit" disabled={!value.trim() || value.length > MAX_CHAT_LENGTH}>Send</button>
  </div>
</form>
```

---

## 📢 StatusBar State Handling

- Must always be visible
- Accepts messages via `addStatusMessage()`
- Uses severity color mapping

```tsx
<footer role="status" aria-live="polite">
  {statusMessages[0] && (
    <div className={`flex items-center ${statusColors[statusMessages[0].type]}`}>
      {statusMessages[0].icon}
      <span>{statusMessages[0].text}</span>
    </div>
  )}
</footer>
```

```ts
const statusColors = {
  success: 'text-green-700 bg-green-50 border-green-200',
  error: 'text-red-700 bg-red-50 border-red-200',
  info: 'text-blue-700 bg-blue-50 border-blue-200',
};
```

---

## 🎨 Accessibility & Theme

### Theme Switching

```tsx
useEffect(() => {
  document.documentElement.dataset.theme = theme;
}, [theme]);
```

```css
[data-theme="dark"] {
  --bg-color: #1a202c;
  --text-color: #e2e8f0;
}
```

### Reduced Motion / High Contrast

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}

@media (prefers-contrast: more) {
  .contrast-safe {
    border-color: #000;
    color: #000;
    background: #fff;
  }
}
```

### General Accessibility

- Use semantic landmarks: `<header>`, `<main>`, `<footer>`, `<aside>`
- Ensure keyboard focus using `focus-visible:ring-*`
- Buttons must have `aria-label`
- Chat input and panel use `aria-live`, `aria-atomic`

---

## 🧠 State Model

```ts
interface AppState {
  sidebarCollapsed: boolean;
  subNavVisible: boolean;
  selectedComponent: Component | null;
  chatMessages: ChatMessage[];
  statusMessages: StatusMessage[];
  chatOverlayOpen: boolean;
  reducedMotion: boolean;
  theme: 'light' | 'dark';
}
```

---

## 📚 Documentation Changelog

| Version | Date       | Notes                                                           |
| ------- | ---------- | --------------------------------------------------------------- |
| v3.2.3  | 2024-07-24 | Merged 3.2.1 + 3.2.2, updated layout, fixed naming + view logic |
| v3.2.2  | 2024-07-24 | Refined grid with explicit footer alignment                     |
| v3.2.1  | 2024-07-23 | Added focus traps, theme system, color coding for statuses      |
| v3.2    | 2024-06-15 | Initial release with grid-based layout                          |

---

This document is the single source of truth for UI implementation in OriginFlow. All developers and AI agents must comply with it to maintain visual, semantic, and behavioral consistency.

