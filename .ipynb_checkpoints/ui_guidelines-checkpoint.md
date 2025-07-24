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

```tsx
@media (max-width: 1280px) {
  .grid {
    grid-template-columns: auto 1fr;
    grid-template-rows: 64px 48px 1fr 48px 48px;
    grid-template-areas:
      "header header"
      "toolbar toolbar"
      "sidebar main"
      "status status"
      "chatInput chatInput";
  }
}

@media (max-width: 767px) {
  .grid {
    grid-template-columns: 1fr;
    grid-template-rows: 64px 48px 1fr auto 48px;
    grid-template-areas:
      "header"
      "toolbar"
      "main"
      "chatInput"
      "status";
  }
}
```

---

## View-specific Layouts

### Projects View – Canvas Builder

When the route is set to `projects`, the main area should display a drag-and-drop canvas where users build connected component graphs. The canvas is implemented by the `Workspace` component inside `ProjectCanvas`.

#### Key Behaviours:

- **Component Library**: In the sidebar, below navigation, display a list of uploaded datasheets (PDF/CSV) with status icons. Use `FileStagingArea`. Files become draggable components when parsing succeeds.
- **Canvas Interaction**: `Workspace` renders draggable component cards with ports, dashed canvas border, and scrolling for overflow.
- **Status Bar**: Use `addStatusMessage` to show messages such as “Project loaded” or link creation success.

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
    {route === 'components' && <DatasheetSplitView />}
    {/* future views */}
  </main>
);
```

---

## Responsive ChatSidebar (Overlay Mode)

```tsx
const { chatOverlayOpen } = useAppStore();
{chatOverlayOpen && (
  <div className="chat-backdrop" onClick={closeChat} />
  <div ref={chatRef} className="chat-sidebar">...</div>
)}
```

---

## StatusBar State Handling

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

---

## ChatPanel Enhancements

```tsx
<div aria-live="polite" aria-atomic="false" className="chat-messages">
  {messages}
</div>
```

---

## Accessibility: Theme Switching

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

---

## Documentation Changelog

| Version | Date       | Notes                                                                |
| ------- | ---------- | -------------------------------------------------------------------- |
| v3.2.1  | 2024-07-23 | Added layout routing, error state icons, chat trap, theme, mobile UX |
| v3.2    | 2024-06-15 | Initial release with grid-based layout                               |

---

This document serves as the single source of truth for UI development in OriginFlow. All future changes must respect the constraints and patterns defined here.

