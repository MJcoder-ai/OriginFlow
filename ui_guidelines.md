# OriginFlow UI Guidelines (v3.1)

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
    }}
  >
    {/* Grid children below */}
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

## 1. Header.tsx

```tsx
<header className="h-16 flex items-center justify-between px-4 bg-white border-b shadow-sm">
  <div className="flex items-center gap-6">
    <button aria-label="Toggle sidebar">☰</button>
  </div>

  <nav role="tablist" className="flex gap-2">
    {['GlobalNav_1', 'GlobalNav_2', 'GlobalNav_3'].map(tab => (
      <button role="tab" aria-selected={false}>{tab}</button>
    ))}
    <button aria-label="Toggle subnav"><SettingsIcon /></button>
  </nav>

  <div className="flex gap-1">
    <Avatar name="AI_1" />
    <Avatar name="Eng_1" />
  </div>
</header>
```

### Accessibility

- Use `role="tablist"` and `aria-selected`
- All interactive elements must have `aria-label` or `title`

---

## 2. Sidebar.tsx

```tsx
<aside className="w-[250px] bg-gray-50 border-r flex flex-col">
  <div className="h-16 flex items-center justify-center border-b">
    <LogoIcon /> OriginFlow
  </div>

  <nav aria-label="Main navigation" className="flex-1 p-4 space-y-2">
    <SidebarItem icon={<ProjectIcon />} label="Projects" />
    <SidebarItem icon={<ComponentIcon />} label="Components" />
  </nav>

  <div className="p-4 border-t">
    <SidebarItem icon={<HelpIcon />} label="Help & Support" />
  </div>
</aside>
```

---

## 3. Toolbar.tsx

```tsx
<section className="h-12 flex items-center justify-between px-6 border-b bg-white shadow-sm">
  <div className="flex gap-3">
    <button>Analyze</button>
    <button>Filter</button>
    <button>Export</button>
  </div>
  <div className="text-sm text-gray-500">Sub-nav active</div>
</section>
```

---

## 4. MainPanel.tsx

```tsx
<main className="overflow-auto bg-gray-100">
  <div className="border-2 border-dashed min-w-[2000px] min-h-[1200px] bg-grid-pattern m-6 relative">
    <p className="absolute inset-0 flex justify-center items-center text-gray-400">
      Drag components here to start
    </p>
  </div>
</main>
```

---

## 5. ChatSidebar.tsx

```tsx
<aside className="w-[350px] flex flex-col h-full border-l bg-white">
  {selectedComponent && (
    <div className="max-h-[250px] overflow-y-auto border-b p-4" role="dialog">
      <h2>Properties</h2>
      {/* form fields */}
    </div>
  )}
  <div className="flex-1 overflow-y-auto p-4 bg-gray-50" aria-label="Chat history">
    <ChatPanel />
  </div>
</aside>
```

---

## 6. ChatInput.tsx

```tsx
<form onSubmit={handleSubmit} className="flex flex-col gap-2 px-4 py-2">
  <textarea
    ref={textareaRef}
    className="w-full resize-none overflow-hidden min-h-[32px] max-h-[120px] border rounded"
    aria-label="Compose message"
    onKeyDown={handleKey}
  />
  <div className="flex justify-end">
    <button type="submit" className="btn-primary">Send</button>
  </div>
</form>
```

---

## 7. StatusBar.tsx

```tsx
const { statusMessages } = useAppStore();
<footer className="h-12 flex items-center px-6 bg-white border-t shadow text-sm" role="status" aria-live="polite">
  {statusMessages[statusMessages.length - 1]?.message ?? 'Ready'}
</footer>
```

---

## Responsive Behavior

| Width            | Behavior                    |
| ---------------- | --------------------------- |
| `> 1280px`       | Full layout                 |
| `768px - 1280px` | ChatSidebar becomes overlay |
| `< 768px`        | Stacked column layout       |

---

## Accessibility

- Landmarks: `<header>`, `<main>`, `<aside>`, `<footer>`
- All buttons must be keyboard-accessible (`Enter`, `Space`)
- Color contrast must meet WCAG 2.1 AA

---

## State Model

```ts
interface AppState {
  sidebarCollapsed: boolean;
  subNavVisible: boolean;
  selectedComponent: Component | null;
  chatMessages: ChatMessage[];
  statusMessages: StatusMessage[];
}
```

---

This document serves as the single source of truth for UI development in OriginFlow. All future changes must respect the constraints and patterns defined here.

