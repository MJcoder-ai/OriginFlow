# OriginFlow UI Guidelines (v3.2.3)

This document defines the implementation specification for all major UI components in the OriginFlow app. It provides layout structure, responsive behavior, styling patterns, accessibility expectations, and code patterns for consistent implementation.

---

## ✨ Global Layout

OriginFlow uses a **CSS Grid layout** wrapped in a full-height flex column to structure the app into consistent rows and columns. The layout now defines five grid rows, giving dedicated space for the toolbar and chat footer.

```tsx
<div className="h-screen flex flex-col">
  <div
    className="grid h-full w-full"
    style={{
      gridTemplateColumns: isSidebarCollapsed ? '64px 1fr 350px' : '250px 1fr 350px',
      gridTemplateRows: '64px 48px 1fr auto auto', // 5 rows
      gridTemplateAreas: `
        "sidebar-header header      chat-history"
        "sidebar        toolbar     chat-history"
        "sidebar        main        chat-history"
        "sidebar        main        chat-input"
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
    <ChatInputArea />
    <ChatFooter />
  </div>
</div>
```

### Grid Area Definitions

| Area            | Grid Area Name   | Notes                                                   |
| --------------- | ---------------- | ------------------------------------------------------- |
| Sidebar Header  | `sidebar-header` | Top-left section for the app logo.                      |
| Sidebar         | `sidebar`        | Main navigation, spanning the three central rows.       |
| Sidebar Footer  | `sidebar-footer` | Bottom-left section for "Help & Support".               |
| Header          | `header`         | Top-center section with the sidebar toggle.             |
| Toolbar         | `toolbar`        | Sits below the header.                                  |
| Main Panel      | `main`           | Main content area, spans two rows to align with the chat. |
| Status Bar      | `status`         | Sits in the bottom-center, aligned with other footers.  |
| Chat History    | `chat-history`   | Main chat message area, spans the top three rows.       |
| Chat Input Area | `chat-input`     | The text area for typing, sits above the chat footer.   |
| Chat Footer     | `chat-footer`    | Bottom-right section for chat action buttons.           |

---

## 🔀 View-specific Layouts

### Projects View – Canvas Builder

- Render `<ProjectCanvas />` in the `main` area
- Sidebar contains `FileStagingArea` for component uploads (PDF/CSV)
- The paperclip upload button shows a spinner and badge while uploads are in progress
- Users drag datasheets into canvas to create nodes
- Canvas uses `<Workspace />` with draggable and connectable components
- Component ports allow linking with mouse drag
- Add visual border to canvas container (`border-dashed`)
- Overflow should scroll when nodes exceed viewport
- `MainPanel.tsx` applies outer padding using `p-4`; `Workspace.tsx` has no padding so the dashed border aligns near the panel edge

### Components View – Datasheet Split

- Render `<DatasheetSplitView />` in the `main` area
- Left pane: PDF viewer (using `react-pdf` with pagination, 50% width)
- Right pane: Form with editable parsed data, grouped into sections
- Include Save and Confirm & Close buttons in sticky toolbar
- ComponentCanvas handles drag/drop from the library or native desktop and triggers asynchronous parsing via `POST /files/{id}/parse`,
  then polls `GET /files/{id}` until `parsing_status` resolves.

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

## 🎨 Styling & Borders

### Vertical Separator

The vertical line separating the main content from the chat column is created by applying a left border to each component in the chat column.

- **Style:** `borderLeft: '1px solid #e5e7eb'`
- **Components:** `ChatHistory`, `ChatInputArea`, `ChatFooter`
- **Rationale:** Ensures a consistent line that matches the color and thickness of the sidebar's right border.

### Invisible Borders

To maintain structural alignment without adding visual clutter, some borders are made invisible by matching their color to the background.

- **Class:** `border-white`
- **Components:**
  - ChatInputArea (top border)
  - ChatFooter (top border)
- **Rationale:** This reserves space for the border in layout calculations while hiding the line from the user.

---

## 📋 Plan Timeline

OriginFlow’s chat sidebar includes a plan timeline that gives users an at‑a‑glance overview of what the AI intends to do next. The timeline sits at the top of the `ChatHistory` area, above the scrollable list of chat messages. Each entry corresponds to a high‑level task returned by the orchestrator and shows a short title, optional description, and a status indicator.

- **Status Icons:** Use the `lucide-react` icons `Circle` (pending), `Loader2` (in progress), `CheckCircle` (complete), and `AlertTriangle` (blocked). Icons should change colour based on status (grey, blue, green, or yellow) and spin when a task is in progress.
- **Layout:** Render tasks as a vertical list inside a container with a light grey background and a bottom border. Use the `<PlanTimeline />` component to encapsulate this behaviour. Hide the timeline entirely when there are no tasks.
- **Interaction:** Timeline items are non-interactive by default; future iterations may enable clicking to expand details or jump to a specific agent output.

```tsx
// ChatHistory.tsx (excerpt)
<div className="grid-in-chat-history flex flex-col h-full bg-white overflow-y-auto min-h-0">
  <PlanTimeline />
  <div className="flex-1 overflow-y-auto p-4">
    {messages.map(m => <ChatMessage key={m.id} message={m} />)}
    {isProcessing && <AiProcessingIndicator />}
  </div>
</div>
```

---

## 🃏 Card Messages

When the AI suggests complex changes—such as recommending a specific inverter, presenting a bill of materials, or summarising a wiring calculation—it should use a **card message** rather than a plain chat bubble. Card messages occupy the full width of the chat column and provide structured information with clear actions.

- **Component:** Use the `<DesignCard />` component. Cards contain a title, description, optional image, a specs table (label/value pairs), and a set of action buttons.
- **Styling:** Cards have a subtle border, shadow, and rounded corners. They should stand apart from chat bubbles but maintain consistent padding.
- **Actions:** Each button triggers a command via `analyzeAndExecute()`. Keep labels concise (e.g. “Accept Component”, “Swap for 8 kW”).
- **Usage:** Populate the `card` field on a `Message` to render a card. Cards override the author alignment to remain left‑aligned.

```ts
interface Message {
  id: string;
  author: 'User' | 'AI';
  text: string;
  card?: DesignCardData;
  type?: 'text' | 'card' | 'status';
}
```

---

## ⚡ Quick Actions & Mode Selector

The chat input area now provides shortcuts for common operations and a high‑level mode switch. These elements live inside the `ChatInputArea` component.

- **Quick Action Bar:** A horizontal list of buttons rendered via `<QuickActionBar />`. Each action has a label and a command string that is sent to the AI when clicked. Quick actions wrap to a new line on narrow screens and appear directly above the text input.
- **Mode Selector:** A dropdown menu rendered by `<ModeSelector />` allows users to choose between Design, Analyze, Manual, and Business modes. This selection informs the orchestrator which tools are available and influences prompt interpretation.
- **Layout:** Place the quick actions and mode selector at the top of the chat input area, with a small margin separating them from the textarea. The existing microphone, upload, and send buttons remain aligned to the right of the input.
- **Responsiveness:** On mobile devices, quick actions and the mode selector stack vertically above the input.

```tsx
// ChatInputArea.tsx (excerpt)
<div className="grid-in-chat-input p-3 bg-white border-t border-white" style={{ borderLeft: '1px solid #e5e7eb' }}>
  <QuickActionBar />
  <div className="flex justify-between items-center mt-2 mb-2">
    <ModeSelector />
  </div>
  <textarea ... />
  {/* upload, mic and send buttons */}
</div>
```

---

## 📝 ChatInputArea Enhancements

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

- Disable the microphone and Send buttons whenever the AI is processing a request.
- Show a spinner at the bottom of `ChatHistory` while the AI is thinking.

---

## 📢 StatusBar State Handling

- Must always be visible
 - Accepts messages via `addStatusMessage()` with optional `icon` and `timeout` parameters
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

