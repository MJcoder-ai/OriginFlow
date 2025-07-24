# OriginFlow UI Guidelines (v3.2.2)

This document defines the implementation specification for all major UI components in the OriginFlow app. It provides layout structure, behavior, styling patterns, accessibility expectations, and code patterns for consistent implementation.

---

## ✨ Global Layout

The app layout is defined using **CSS Grid** inside a full-height flex container.

```tsx
<div className="h-screen flex flex-col">
  <div
    className="grid h-full w-full"
    style={{
      gridTemplateColumns: 'auto 1fr 350px',
      gridTemplateRows: '64px 48px 1fr 48px',
      gridTemplateAreas: `
        "header header header"
        "toolbar toolbar toolbar"
        "sidebar main chat"
        "status status chatInput"
      `,
      columnGap: '4px',
      rowGap: '4px',
    }}
  >
    <Header />
    <Toolbar />
    <Sidebar />
    <MainPanel />
    <ChatSidebar />
    <StatusBar />
    <ChatInput />
  </div>
</div>
```

The app title "OriginFlow" is displayed in the header next to the sidebar toggle button. The sidebar itself now shows only the spiral icon.

### Grid Definitions

| Area        | Grid Area Name |
| ----------- | -------------- |
| Header      | `header`       |
| Toolbar     | `toolbar`      |
| Sidebar     | `sidebar`      |
| MainPanel   | `main`         |
| ChatSidebar | `chat`         |
| StatusBar   | `status`       |
| ChatInput   | `chatInput`    |

---

## Sidebar Width Sync

Define custom tokens:

```css
:root {
  --sidebar-width-expanded: 250px;
  --sidebar-width-collapsed: 64px;
}
```

Then apply:

```tsx
<aside className={`transition-[width] duration-200 ${sidebarCollapsed ? 'w-[var(--sidebar-width-collapsed)]' : 'w-[var(--sidebar-width-expanded)]'}`}>
```

---

## Responsive ChatSidebar (Overlay Mode)

```tsx
@media (max-width: 1280px) {
  .grid {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "header header"
      "toolbar toolbar"
      "sidebar main"
      "status chatInput";
  }
}

.chat-sidebar {
  @apply fixed right-0 top-0 h-full w-[350px] z-50 bg-white shadow-xl;
}

.chat-backdrop {
  @apply fixed inset-0 bg-black/30 backdrop-blur-sm;
  animation: fadeIn 150ms ease-in;
}
```

Use focus trap:

```tsx
const { ref: chatRef } = useFocusTrap({ active: isChatOverlayOpen });
```

---

## StatusBar State Handling

```tsx
<footer role="status" aria-live="polite">
  {statusMessages[0]?.text || 'Ready'}
</footer>
```

Color styles:

```ts
const statusColors = {
  success: 'text-green-700 bg-green-50 border-green-200',
  error:   'text-red-700 bg-red-50 border-red-200',
  info:    'text-blue-700 bg-blue-50 border-blue-200',
}
```

Status interface:

```ts
interface StatusMessage {
  id: string;
  text: string;
  type: 'success' | 'error' | 'info';
  icon?: JSX.Element;
}
```

---

## ChatPanel Enhancements

- Scroll-to-bottom on new message unless user is scrolling
- Add `aria-live="polite"` to announce messages
- Optional: Show timestamps

```tsx
const [userScrolling, setUserScrolling] = useState(false);
useEffect(() => {
  if (!userScrolling) scrollToBottom();
}, [chatMessages]);
```

---

## ChatInput Enhancements

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

## Accessibility: Motion, Contrast, and Reduced Motion

<<<<<<< HEAD
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
=======
```tsx
const { statusMessages } = useAppStore();
<footer className="h-12 flex items-center px-6 bg-white border-t shadow text-sm" role="status" aria-live="polite">
  {statusMessages[statusMessages.length - 1]?.message ?? 'Ready'}
</footer>
>>>>>>> 031011c8a8a003f3667759064f5b2208045a14b0
```

---

## Responsive Behavior

| Width       | Behavior                    |
| ----------- | --------------------------- |
| ≥ 1280 px   | Full layout                 |
| 768–1279 px | ChatSidebar becomes overlay |
| < 768 px    | Stack Sidebar + Main layout |

### Mobile Drawer Spec

```tsx
<nav className="fixed inset-0 z-50 bg-white p-4 transform transition-transform" aria-modal="true">
  <ul className="space-y-3">{navItems}</ul>
</nav>
```

---

## Accessibility

- Landmarks: `<header>`, `<main>`, `<aside>`, `<footer>`
- Buttons: `aria-label`, keyboard-accessible
- Contrast: ≥ 4.5:1
- Motion: optional disable via `prefers-reduced-motion`
- Focus: `focus-visible:ring-1 ring-offset-1`

---

## State Model

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

## Documentation Changelog

| Version | Date       | Notes                                                         |
| ------- | ---------- | ------------------------------------------------------------- |
| v3.2.2  | 2025-07-24 | Header now contains the app title; added grid area helpers and `.btn-primary` class |
| v3.2.1  | 2024-07-23 | Added gaps, focus-trap snippet, severity colors, state fields |
| v3.2    | 2024-06-15 | Initial release with grid-based layout                        |

---

This document serves as the single source of truth for UI development in OriginFlow. All future changes must respect the constraints and patterns defined here.

