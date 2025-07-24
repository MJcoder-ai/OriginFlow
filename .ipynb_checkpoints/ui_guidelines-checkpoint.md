# OriginFlow UI Guidelines (v3.2.1)

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

## View-specific Layouts

### Projects View – Canvas Builder

When the route is set to `projects`, the main area should display a drag-and-drop canvas where users build connected component graphs. The canvas is implemented by the `Workspace` component inside `ProjectCanvas`.

#### Key Behaviours:

- **Component Library**: In the sidebar, below navigation, display a list of uploaded datasheets with status icons. Use `FileStagingArea`. Items are draggable via `@dnd-kit/core`.
- **Canvas Interaction**: `Workspace` renders draggable component cards with ports, dashed canvas border, and scrolling for overflow.
- **Status Bar**: Use `addStatusMessage` to show success/failure messages.

### Components View – Datasheet Split

When route is `components`, the main panel splits vertically into:

- **Left Pane**: PDF preview using `iframe` or viewer, 50% width, scrollable.
- **Right Pane**: Editable form of parsed data. Use `DatasheetSplitView`. Include Save and Confirm & Close buttons in a sticky header.
- **Drag & Drop Parsing**: Dropping a PDF triggers `/api/v1/parse-datasheet` and opens the split view.

### Navigation

Switching between views should persist uploaded data and preserve active selection. Clicking a library item in Projects opens its view in Components.

---

## Adding New Views

1. Extend the `route` enum/type in appStore.ts.
2. Add a new `SidebarItem` for the route.
3. Conditionally render the view inside `MainPanel`:

```tsx
const route = useAppStore((s) => s.route);
return (
  <main className="grid-in-main overflow-hidden">
    {route === 'projects' && <ProjectCanvas />}
    {route === 'components' && <ComponentCanvas />}
    {/* future views */}
  </main>
);
```

---

## Sidebar Width Sync

```css
:root {
  --sidebar-width-expanded: 250px;
  --sidebar-width-collapsed: 64px;
}
```

```tsx
<aside className={`transition-[width] duration-200 ${sidebarCollapsed ? 'w-[var(--sidebar-width-collapsed)]' : 'w-[var(--sidebar-width-expanded)]'}`} />
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

```ts
const statusColors = {
  success: 'text-green-700 bg-green-50 border-green-200',
  error:   'text-red-700 bg-red-50 border-red-200',
  info:    'text-blue-700 bg-blue-50 border-blue-200',
}
```

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

```tsx
const [userScrolling, setUserScrolling] = useState(false);
useEffect(() => {
  if (!userScrolling) scrollToBottom();
}, [chatMessages]);
```

- Use `aria-live="polite"` on chat area.
- Optional: Show message timestamps.

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

---

## Responsive Behavior

| Width       | Behavior                         |
| ----------- | -------------------------------- |
| ≥ 1280 px   | Full layout                      |
| 768–1279 px | ChatSidebar becomes overlay      |
| < 768 px    | Sidebar collapses, layout stacks |

### Mobile Drawer Spec

```tsx
<nav className="fixed inset-0 z-50 bg-white p-4 transform transition-transform" aria-modal="true">
  <ul className="space-y-3">{navItems}</ul>
</nav>
```

---

## Accessibility Summary

- Use semantic tags: `<header>`, `<main>`, `<aside>`, `<footer>`
- All buttons and inputs must be keyboard accessible
- Use `aria-label`, `aria-live`, and `aria-current` where appropriate
- Provide focus rings: `focus-visible:ring-1 ring-offset-1`
- Minimum contrast ratio: 4.5:1

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

| Version | Date       | Notes                                                               |
| ------- | ---------- | ------------------------------------------------------------------- |
| v3.2.1  | 2024-07-23 | Added layout routing, component view behaviors, and overlay support |
| v3.2    | 2024-06-15 | Initial release with grid-based layout                              |

---

This document serves as the single source of truth for UI development in OriginFlow. All future changes must respect the constraints and patterns defined here.

