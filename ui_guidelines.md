# OriginFlow UI Guidelines (v3.0)

This document defines the implementation specification for all major UI components in the OriginFlow app. It provides layout structure, behavior, styling patterns, accessibility expectations, and code patterns for consistent implementation.

---

## ✨ Global Layout

The app layout is defined using **CSS Grid** inside a full-height flex container:

```tsx
<div className="h-screen flex flex-col">
  <div
    className="grid h-full w-full"
    style={{
      gridTemplateColumns: 'auto 1fr 350px',
      gridTemplateRows: '64px 48px 1fr',
      gridTemplateAreas: `
        "header header header"
        "toolbar toolbar toolbar"
        "sidebar main chat"
      `,
    }}
  >
    {/* Grid Children */}
  </div>
  <StatusBar />
</div>
```

Use responsive overrides:

```css
@media (max-width: 768px) {
  grid-template-areas:
    "header"
    "toolbar"
    "main";
  grid-template-columns: 1fr;
}
```

---

## 1. Header.tsx

### Structure

```tsx
<header className="h-16 flex items-center justify-between px-4 bg-white border-b shadow-sm">
  {/* Left: Sidebar Toggle + Logo */}
  <div className="flex items-center gap-6">
    <button aria-label="Toggle sidebar">...</button>
    <Logo /> <h1>OriginFlow</h1>
  </div>

  {/* Center: Tabs */}
  <nav role="tablist" className="flex gap-2">
    {/* Tabs */}
  </nav>

  {/* Right: Settings + Avatars */}
  <div className="flex items-center gap-4">
    <button aria-label="Toggle subnav"><SettingsIcon /></button>
    <AvatarStack />
  </div>
</header>
```

### Accessibility

- Tabs use `role="tab"`, `aria-selected`
- Buttons use `aria-pressed`, `aria-label`

---

## 2. Sidebar.tsx

### Structure

```tsx
<aside className="w-[250px] bg-gray-50 border-r flex flex-col">
  <div className="h-16 flex items-center justify-center border-b">
    <LogoIcon />
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

### Behavior

- Collapse width: `64px`, uses `justify-center` and tooltips

---

## 3. Toolbar.tsx

### Structure

```tsx
<section className="h-12 flex items-center justify-between px-6 border-b bg-white shadow-sm">
  <div className="flex gap-3">
    <button className="toolbar-btn">Analyze</button>
    <button className="toolbar-btn">Filter</button>
    <button className="toolbar-btn">Export</button>
  </div>
  <div className="text-sm text-gray-500">Sub-nav active</div>
</section>
```

### Transition (show/hide)

```css
.toolbar-enter-active {
  max-height: 48px;
  opacity: 1;
  transition: max-height 300ms, opacity 300ms;
}
```

---

## 4. MainPanel.tsx

### Structure

```tsx
<main className="overflow-auto bg-gray-100">
  <div className="border-2 border-dashed min-w-[2000px] min-h-[1200px] bg-grid-pattern m-6">
    {nodes.length === 0 ? (
      <div className="flex justify-center items-center h-full text-gray-400">
        Drag components here to start
      </div>
    ) : (
      <CanvasNodes />
    )}
  </div>
</main>
```

### Background Grid

```css
.bg-grid-pattern {
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

---

## 5. ChatSidebar.tsx

```tsx
<aside className="w-[350px] flex flex-col h-full border-l bg-white">
  {selectedComponent && (
    <div className="max-h-[250px] overflow-y-auto border-b p-4">...
    </div>
  )}
  <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
    <ChatPanel />
  </div>
  <div className="border-t p-3">
    <ChatInput />
  </div>
</aside>
```

---

## 6. ChatInput.tsx

```tsx
<form onSubmit={handleSubmit} className="flex flex-col gap-2">
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

```tsx
const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSubmit();
  }
};
```

---

## 7. StatusBar.tsx

```tsx
<footer className="fixed bottom-0 left-0 w-full h-12 flex items-center px-6 bg-white border-t shadow text-sm z-50" role="status" aria-live="polite">
  Status: Link Created
</footer>
```

---

## Global Styling Notes

- Use `transition-all duration-300 ease-in-out`
- All icon buttons: `min-width: 44px`, `aria-label`, `hover + focus-visible` states
- Font: Inter / system-ui, `text-sm` or `text-base`
- Use Tailwind's spacing scale consistently
- Grid patterns: apply `.bg-grid-pattern` for canvas zones

---

## Accessibility

- Follow WCAG 2.1 AA
- Label all buttons with `aria-label`
- Use landmarks: `<header>`, `<main>`, `<footer>`, `<nav>`, `<aside>`
- Enable keyboard nav: arrow keys for tabs, `Tab` and `Enter` for focus

---

## Responsive Breakpoints

| Width            | Behavior              |
| ---------------- | --------------------- |
| `> 1280px`       | Full layout           |
| `768px - 1280px` | Chat becomes overlay  |
| `< 768px`        | Stacked column layout |

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

