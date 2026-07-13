# Phase 7 — Executive Decision Center (Part 3)
# World-Class UI/UX Design System

## Design Philosophy

- **Every pixel must have a purpose.** No decorative elements.
- **Reduce cognitive load.** Clear hierarchy, white space, and progressive disclosure.
- **Focus on clarity.** Data, labels, and actions are immediately understandable.
- **Action before decoration.** UI elements lead to decisions and workflows.
- **Information hierarchy.** Most important insights are most prominent.
- **Excellent spacing.** Consistent 4px grid and 8px scale.
- **Accessibility first.** WCAG AA minimum, keyboard navigation, screen reader support.
- **Responsive first.** Mobile, tablet, desktop, ultra-wide from day one.
- **Dark and light modes.** Both modes are first-class citizens.

---

## 1. Design Tokens

### Color System

```css
:root {
  /* Brand */
  --color-primary-50: #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-200: #c7d2fe;
  --color-primary-300: #a5b4fc;
  --color-primary-400: #818cf8;
  --color-primary-500: #6366f1;
  --color-primary-600: #4f46e5;
  --color-primary-700: #4338ca;
  --color-primary-800: #3730a3;
  --color-primary-900: #312e81;

  /* Neutrals */
  --color-white: #ffffff;
  --color-gray-50: #f8fafc;
  --color-gray-100: #f1f5f9;
  --color-gray-200: #e2e8f0;
  --color-gray-300: #cbd5e1;
  --color-gray-400: #94a3b8;
  --color-gray-500: #64748b;
  --color-gray-600: #475569;
  --color-gray-700: #334155;
  --color-gray-800: #1e293b;
  --color-gray-900: #0f172a;
  --color-black: #020617;

  /* Semantic */
  --color-success-50: #f0fdf4;
  --color-success-500: #22c55e;
  --color-success-700: #15803d;
  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-700: #b45309;
  --color-danger-50: #fef2f2;
  --color-danger-500: #ef4444;
  --color-danger-700: #b91c1c;
  --color-info-50: #eff6ff;
  --color-info-500: #3b82f6;
  --color-info-700: #1d4ed8;

  /* Backgrounds */
  --color-bg: #ffffff;
  --color-bg-surface: #f8fafc;
  --color-bg-elevated: #ffffff;
  --color-bg-overlay: rgba(15, 23, 42, 0.48);

  /* Text */
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #64748b;
  --color-text-inverse: #ffffff;
  --color-text-link: #4f46e5;

  /* Borders */
  --color-border-default: #e2e8f0;
  --color-border-subtle: #f1f5f9;
  --color-border-focus: #4f46e5;
}

[data-theme='dark'] {
  --color-bg: #0f172a;
  --color-bg-surface: #1e293b;
  --color-bg-elevated: #334155;
  --color-bg-overlay: rgba(0, 0, 0, 0.64);
  --color-text-primary: #f8fafc;
  --color-text-secondary: #cbd5e1;
  --color-text-muted: #94a3b8;
  --color-text-inverse: #0f172a;
  --color-text-link: #818cf8;
  --color-border-default: #334155;
  --color-border-subtle: #1e293b;
}
```

### Typography

```css
:root {
  --font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;    /* 24px */
  --font-size-3xl: 1.875rem;  /* 30px */
  --font-size-4xl: 2.25rem;   /* 36px */

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.625;

  --letter-spacing-tight: -0.025em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.025em;
}
```

### Spacing Scale

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
}
```

### Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.375rem; /* 6px */
  --radius-lg: 0.5rem;   /* 8px */
  --radius-xl: 0.75rem;  /* 12px */
  --radius-2xl: 1rem;    /* 16px */
  --radius-full: 9999px;
}
```

### Elevation

```css
:root {
  --shadow-xs: 0 1px 2px 0 rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.08);
  --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.08);
  --shadow-xl: 0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.08);
  --shadow-focus: 0 0 0 3px rgba(99, 102, 241, 0.25);
}

[data-theme='dark'] {
  --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.24);
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.32), 0 1px 2px -1px rgba(0, 0, 0, 0.32);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.32), 0 2px 4px -2px rgba(0, 0, 0, 0.32);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.32), 0 4px 6px -4px rgba(0, 0, 0, 0.32);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.32), 0 8px 10px -6px rgba(0, 0, 0, 0.32);
  --shadow-focus: 0 0 0 3px rgba(99, 102, 241, 0.35);
}
```

---

## 2. Animation & Motion

### Timing

```css
:root {
  --duration-instant: 75ms;
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 500ms;

  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### Standard Transitions

```css
.transition-fade {
  transition: opacity var(--duration-fast) var(--ease-in-out);
}

.transition-slide {
  transition: transform var(--duration-normal) var(--ease-out),
              opacity var(--duration-normal) var(--ease-in-out);
}

.transition-scale {
  transition: transform var(--duration-fast) var(--ease-spring);
}

.transition-color {
  transition: background-color var(--duration-fast) var(--ease-in-out),
              border-color var(--duration-fast) var(--ease-in-out),
              color var(--duration-fast) var(--ease-in-out);
}

.transition-shadow {
  transition: box-shadow var(--duration-fast) var(--ease-in-out);
}
```

### Motion Patterns

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Button hover | background-color, transform scale(1.02) | 150ms | ease-in-out |
| Card hover | shadow-lg, translateY(-2px) | 200ms | ease-out |
| Modal open | fade + scale(0.98→1) | 200ms | ease-out |
| Modal close | fade + scale(1→0.98) | 150ms | ease-in |
| Sidebar collapse | width + opacity | 300ms | ease-in-out |
| Toast enter | slide in + fade | 300ms | ease-spring |
| Toast exit | slide out + fade | 200ms | ease-in |
| Chart load | staggered fade + scale | 400ms | ease-out |
| Skeleton pulse | opacity 0.4 → 0.8 | 1500ms | ease-in-out |
| Spinner rotate | rotate 360° | 800ms | linear |
| KPI count | count-up number | 800ms | ease-out |
| Alert pulse | subtle shadow pulse | 2000ms | ease-in-out |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 3. Icon System

- **Library**: Lucide React.
- **Stroke width**: 1.5px default, 2px for emphasis.
- **Sizes**: 12px, 16px, 20px, 24px, 32px.
- **Color**: inherits `currentColor`; use semantic colors for status.
- **Usage**: always paired with text labels for accessibility.

### Icon Mapping

| Concept | Icon |
|---------|------|
| Dashboard | LayoutDashboard |
| Health | HeartPulse |
| Alerts | Bell / AlertTriangle |
| KPIs | BarChart3 |
| Forecast | TrendingUp |
| Recommendations | Sparkles |
| Reports | FileText |
| ETL | Workflow |
| AI | Bot |
| Tasks | CheckCircle2 |
| Approvals | Gavel |
| Departments | Building2 |
| Users | Users |
| Settings | Settings |
| Search | Search |
| Notifications | Bell |
| Menu | Menu |
| Filter | SlidersHorizontal |
| Download | Download |
| Export | Share |
| Calendar | Calendar |
| Clock | Clock |
| Success | CheckCircle2 |
| Warning | AlertTriangle |
| Error | XCircle |
| Info | Info |
| Expand | Maximize2 |
| Collapse | Minimize2 |

---

## 4. Illustration & Empty States

### Style
- Flat, minimal vector illustrations.
- Limited palette: primary, neutrals, one accent.
- No unnecessary details; reinforce the message.
- Use Lucide icons for simple empty states; custom SVGs for complex ones.

### Empty State Components

```tsx
<EmptyState
  icon={FolderOpen}
  title="No reports yet"
  description="Create your first report to see it here."
  action={<Button>Create Report</Button>}
/>
```

### Loading States
- Skeleton screens matching final layout.
- Shimmer animation using gradient overlay.
- Never show blank space or spinners alone for large areas.
- Inline spinners for buttons and small actions.

### Error States
- Friendly error card with icon, message, and retry action.
- Inline validation messages below inputs.
- Toast for non-blocking errors.
- Full-page error boundary with fallback UI.

### Success States
- Toast with checkmark and brief message.
- Inline checkmarks for completed actions.
- Confetti-free; use subtle color and icon changes.

---

## 5. Component Library

### Buttons

```tsx
<Button variant="primary" size="md">Action</Button>
<Button variant="secondary" size="sm">Secondary</Button>
<Button variant="ghost" size="icon"><IconSettings /></Button>
<Button variant="danger" isLoading>Delete</Button>
```

| Variant | Background | Text | Use Case |
|---------|------------|------|----------|
| Primary | primary-600 | white | Main CTA |
| Secondary | white | gray-900 | Secondary action |
| Ghost | transparent | gray-700 | Low-emphasis |
| Destructive | danger-500 | white | Delete, remove |
| Link | transparent | primary-600 | Inline link |

**States**: hover (lighten/darken 10%), active (scale 0.98), focus (shadow-focus), disabled (opacity 50%, no hover), loading (spinner + preserved width).

### Cards

```tsx
<Card>
  <CardHeader title="Revenue" subtitle="Last 30 days" />
  <CardContent>
    <KpiValue value={128400} change={8.4} />
  </CardContent>
  <CardFooter>
    <Button variant="ghost" size="sm">View Details</Button>
  </CardFooter>
</Card>
```

- Background: `--color-bg-elevated`.
- Border: 1px solid `--color-border-default`.
- Shadow: `--shadow-sm` default, `--shadow-md` on hover.
- Radius: `--radius-lg`.
- Padding: `--space-4` to `--space-6`.

### Forms & Inputs

```tsx
<Input label="Email" placeholder="you@org.com" error="Required" />
<Select label="Department" options={[]} />
<Textarea label="Notes" rows={4} />
<DatePicker label="Start Date" />
<SearchInput placeholder="Search anything..." />
```

- Height: 40px (compact), 44px (default).
- Radius: `--radius-md`.
- Border: `--color-border-default`.
- Focus: `border-primary-500`, `shadow-focus`.
- Error: `border-danger-500`, danger text.
- Disabled: `bg-gray-100`, opacity 60%.
- Label: 14px, medium, secondary text.
- Helper text: 12px, muted.

### Tables / Data Grid

```tsx
<DataGrid
  columns={columns}
  data={data}
  sorting
  filtering
  pagination
  columnVisibility
  export
  stickyHeader
  selection="multi"
  bulkActions={[]}
/>
```

- Header: 48px, gray-50 background, semibold text.
- Row: 52px, hover state gray-50.
- Selected row: primary-50 background.
- Sticky header on scroll.
- Inline filters per column.
- Pagination: 25/50/100 rows.
- Export: CSV, Excel, PDF.

### Tabs

```tsx
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="details">Details</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">...</TabsContent>
</Tabs>
```

- Active tab: primary underline + primary text.
- Inactive: secondary text.
- Hover: secondary text darkens.
- Radius: top only if card-style.

### Badges & Chips

```tsx
<Badge variant="success">On Track</Badge>
<Chip variant="neutral" removable>Filter</Chip>
```

| Variant | Background | Text | Border |
|---------|------------|------|--------|
| Neutral | gray-100 | gray-700 | gray-200 |
| Primary | primary-50 | primary-700 | primary-200 |
| Success | success-50 | success-700 | success-200 |
| Warning | warning-50 | warning-700 | warning-200 |
| Danger | danger-50 | danger-700 | danger-200 |
| Info | info-50 | info-700 | info-200 |

### Dialogs & Modals

```tsx
<Dialog>
  <DialogTrigger>Open</DialogTrigger>
  <DialogContent>
    <DialogHeader title="Confirm" description="Are you sure?" />
    <DialogFooter>
      <Button variant="secondary">Cancel</Button>
      <Button variant="destructive">Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

- Overlay: `--color-bg-overlay` with blur(4px).
- Max width: 400px (small), 560px (medium), 720px (large).
- Radius: `--radius-xl`.
- Close on Escape, click outside, or X button.
- Focus trap inside modal.

### Toast Notifications

```tsx
toast({
  title: "Report generated",
  description: "Your monthly report is ready.",
  variant: "success",
  duration: 5000,
});
```

- Position: bottom-right desktop, top-center mobile.
- Auto-dismiss: 5 seconds.
- Pause on hover.
- Icons per variant.
- Stacked with 8px gap.

### Dropdowns

```tsx
<DropdownMenu>
  <DropdownMenuTrigger>...</DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem>View</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem destructive>Delete</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

- Background: `--color-bg-elevated`.
- Shadow: `--shadow-lg`.
- Radius: `--radius-lg`.
- Item height: 36px.
- Keyboard navigation: ↑↓, Enter, Escape.

---

## 6. Layout System

### Grid

- 12-column grid.
- Gutter: 24px desktop, 16px tablet, 12px mobile.
- Container max-width: 1440px.
- Padding: 24px desktop, 16px tablet, 12px mobile.

### Breakpoints

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Widget Sizing

| Size | Width | Height | Use Case |
|------|-------|--------|----------|
| Small | 3 cols | 240px | KPI card, status |
| Medium | 6 cols | 320px | Chart, feed |
| Large | 9 cols | 400px | Forecast, KPI panel |
| Full | 12 cols | auto | Alerts, recommendations |

### Spacing Patterns
- Section gap: `--space-6` (24px).
- Card internal gap: `--space-4` (16px).
- Between related items: `--space-2` (8px).
- Between unrelated items: `--space-4` (16px).

---

## 7. Sidebar

### Structure

```
┌─────────────────┐
│ Logo            │
│                 │
│ Search (Ctrl+K) │
│                 │
│ Favorites       │
│ Pinned Modules  │
│ Recent Pages    │
│ Industry Modules│
│                 │
│ AI Assistant    │
│                 │
│ Settings        │
│ Profile         │
└─────────────────┘
```

### Behavior
- Default width: 264px.
- Collapsible to 72px (icon only).
- Persistent collapsed state per user.
- Active module highlighted with primary left border and background.
- Tooltip on collapsed state.
- Keyboard shortcut: `Ctrl/Cmd + B` to toggle.

### Sections
1. **Search** — Command palette trigger.
2. **Favorites** — User pinned modules.
3. **Pinned Modules** — Role-based default modules.
4. **Recent Pages** — Last 5 visited.
5. **Industry Modules** — Health, Education, Agriculture, etc.
6. **Bottom** — AI Assistant, Settings, Profile.

---

## 8. Top Bar

### Structure

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Menu │ Page Title │                    │ Search │ Notif │ AI │ Create │ Theme │ Profile │
└──────────────────────────────────────────────────────────────────────────┘
```

### Components
- **Menu toggle** — for mobile and sidebar collapse.
- **Page title & breadcrumb**.
- **Workspace switcher** — organization selector.
- **Department switcher** — context filter.
- **Global search** — Command palette trigger.
- **Notifications** — bell with badge and dropdown panel.
- **AI Copilot** — opens AI assistant side panel.
- **Quick Create** — dropdown for common actions.
- **Theme toggle** — light/dark.
- **Profile** — avatar dropdown.

### Height
- 64px desktop, 56px mobile.
- Sticky top with subtle shadow on scroll.
- Background: `--color-bg-elevated` with bottom border.

---

## 9. Command Palette

### Trigger
- Keyboard: `Ctrl/Cmd + K`.
- UI: search input in top bar and sidebar.

### Features
- Search across modules, reports, dashboards, alerts, KPIs, users.
- Navigate to any page.
- Run AI commands: "Generate report for last month."
- Execute quick actions: "Run ETL job 12."
- Recent searches and commands.

### Layout

```
┌─────────────────────────────────────┐
│ ⌘K   Search anything...             │
├─────────────────────────────────────┤
│ Suggested                           │
│ Go to Decision Center               │
│ Go to Reports                       │
│ Generate AI Summary                 │
│ Run ETL Job                         │
├─────────────────────────────────────┤
│ Recent                              │
│ Revenue report                      │
│ Alert #1024                         │
└─────────────────────────────────────┘
```

### Accessibility
- `role="dialog"` with `aria-modal="true"`.
- `aria-label="Command palette"`.
- Arrow keys navigate, Enter selects, Escape closes.
- Announce result count to screen reader.

---

## 10. Decision Center Layout

### Desktop (≥1280px)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                                            │
├────────────────────────────┬─────────────────────────────────────────────────────┤
│ SIDEBAR                    │ MAIN CONTENT                                        │
│                            │                                                     │
│                            │ Welcome Panel                                       │
│                            │ ┌─────────────────────────────────────────────────┐ │
│                            │ │ Good Morning, Larry · Today · Org · Role ·    │ │
│                            │ │ Tasks · Meetings · Notifications              │ │
│                            │ └─────────────────────────────────────────────────┘ │
│                            │                                                     │
│                            │ ┌──────────┐ ┌────────────────────────────────────┐ │
│                            │ │ Health   │ │ AI Daily Briefing                  │ │
│                            │ │ Score    │ │                                    │ │
│                            │ │ 1/3      │ │ 2/3                                │ │
│                            │ └──────────┘ └────────────────────────────────────┘ │
│                            │                                                     │
│                            │ Critical Alerts (full width)                       │
│                            │                                                     │
│                            │ ┌────────────────────┐ ┌────────────────────────┐ │
│                            │ │ Decision Feed      │ │ Department Performance │ │
│                            │ │ 1/2                │ │ 1/2                    │ │
│                            │ └────────────────────┘ └────────────────────────┘ │
│                            │                                                     │
│                            │ Executive KPIs (full width)                        │
│                            │                                                     │
│                            │ ┌──────────────────┐ ┌──────────────────────────┐ │
│                            │ │ Forecast Panel   │ │ Pending Actions          │ │
│                            │ │ 1/2              │ │ 1/2                      │ │
│                            │ └──────────────────┘ └──────────────────────────┘ │
│                            │                                                     │
│                            │ AI Recommendations (full width)                    │
│                            │                                                     │
│                            │ ┌────────────────┐ ┌────────────────────────────┐ │
│                            │ │ Upcoming Reports│ │ Quick Actions + Recent     │ │
│                            │ │ 1/3            │ │ Activity 2/3               │ │
│                            │ └────────────────┘ └────────────────────────────┘ │
│                            │                                                     │
└────────────────────────────┴─────────────────────────────────────────────────────┘
```

### Tablet (768px–1279px)
- Sidebar collapses to icon rail or hamburger menu.
- Two-column widgets become single column.
- KPI cards wrap to 2 per row.
- Health Score and AI Briefing stack vertically.

### Mobile (<768px)
- Single column, stacked sections.
- Top bar condenses to hamburger + title + search + profile.
- Bottom navigation bar for quick actions.
- KPI cards swipeable horizontally.
- Sections collapsible.

### Ultra-Wide (≥1920px)
- Side panels for real-time feeds or AI assistant.
- More KPIs visible per row.
- Larger charts with additional context.

---

## 11. Widget Specifications

### Welcome Panel
- Background: subtle gradient from primary-50 to white (light), from gray-900 to gray-800 (dark).
- Greeting: 3xl bold, primary-700 (light), white (dark).
- Date/role: sm secondary text.
- Task/notification chips: badge + count + link.
- Height: 120px desktop, auto mobile.

### Organization Health Score™
- Circular progress ring: 120px diameter, stroke 12px, primary gradient.
- Center: large score (3xl) + label (sm).
- Surrounding: 8 category mini bars, color-coded by score.
- Trend: arrow + percentage vs last month.
- Recommendations: 3 linked chips below.
- Click category → drill-down modal.

### AI Daily Briefing
- Left accent border: primary-500, 4px.
- Header: "AI Daily Briefing" with refresh icon and timestamp.
- Bullets: 14px medium text, icon prefix per topic.
- Links: each bullet links to source.
- Background: primary-50/5% in dark.

### Critical Alerts
- Tabs: High (red), Medium (amber), Low (blue) with counts.
- Cards: left 4px severity border.
- Title: semibold, 14px.
- Impact: secondary text, 1 line.
- Recommended action: primary link.
- Owner avatar + due date on right.
- Hover: shadow-md.

### Decision Feed™
- Timeline with icon dots.
- Each item: icon, title, timestamp, category badge, action link.
- Alternating subtle background for readability.
- Infinite scroll or pagination.
- Filter bar: type, date, status.

### Department Performance
- Grid of cards: 3 columns desktop, 2 tablet, 1 mobile.
- Card: status dot, name, health score, 3 KPIs, trend, recommendation.
- Status dot: green/yellow/red.
- Hover: lift + shadow.
- Click → department detail page.

### Executive KPIs
- Horizontal row of cards: 6 desktop, 4 tablet, 2 swipeable mobile.
- Card: value (2xl bold), target (sm), sparkline, status badge.
- Status: success/warning/danger.
- Click → detail modal.

### Forecast Panel
- Line chart: actual (solid) + forecast (dashed) + confidence band (shaded).
- Legend below chart.
- Right side: risks and opportunities lists.
- Horizon selector: 30/60/90/365 days.
- KPI selector dropdown.

### Pending Actions
- Grouped by type: Approvals, Reports, Workflow, ETL, Validation, Tasks.
- Each item: checkbox, title, owner, due date, action button.
- Overdue items highlighted with danger tint.
- Swipe actions on mobile.

### AI Recommendations
- Filter chips: High / Medium / Low value.
- Cards: value badge (color), title, why, expected benefit, estimated impact, owner suggestion, action buttons (accept, reject, schedule).
- Sort by value and confidence.

### Upcoming Reports
- Calendar-style list with date on left, title, type badge, owner, status.
- Click → generate or submit.
- Overdue items in danger color.

### Quick Actions
- Grid of icon buttons: 4 columns desktop, 2 tablet, 3 scrollable mobile.
- Each: icon, label, subtle hover background.
- Permission-aware: hide actions user cannot perform.

### Recent Activity
- Compact list: icon, description, timestamp, actor.
- Grouped by today/yesterday/earlier.
- Click → detail view.

### Security Status & System Health
- Compact status cards.
- Green/yellow/red indicators.
- Mini sparklines or uptime counters.
- Link to monitoring module.

---

## 12. Charts

All charts built with Recharts (React) + Plotly (complex) + D3 (custom).

| Chart | Use Case | Component |
|-------|----------|-----------|
| Bar | KPI comparison, category revenue | `BarChart` |
| Line | Trends over time | `LineChart` |
| Area | Revenue over time, cumulative | `AreaChart` |
| Pie | Distribution, proportions | `PieChart` |
| Heatmap | Correlation, activity density | `HeatmapChart` |
| Radar | Multi-dimensional health | `RadarChart` |
| Tree Map | Hierarchical KPIs | `TreeMap` |
| Geo Map | Regional performance | `GeoMap` |
| Timeline | Decision feed, project plan | `TimelineChart` |
| Forecast | Actuals + forecast + confidence | `ForecastChart` |
| Gauge | Single KPI vs target | `GaugeChart` |
| Sparkline | Inline KPI trend | `Sparkline` |

### Chart Tokens

```css
:root {
  --chart-primary: #6366f1;
  --chart-secondary: #22c55e;
  --chart-warning: #f59e0b;
  --chart-danger: #ef4444;
  --chart-info: #3b82f6;
  --chart-grid: #e2e8f0;
  --chart-text: #475569;
  --chart-tooltip-bg: #ffffff;
  --chart-tooltip-border: #e2e8f0;
}

[data-theme='dark'] {
  --chart-grid: #334155;
  --chart-text: #94a3b8;
  --chart-tooltip-bg: #1e293b;
  --chart-tooltip-border: #334155;
}
```

---

## 13. Accessibility Guide

### Requirements
- WCAG 2.1 Level AA compliance.
- Keyboard-only navigation for all interactive elements.
- Screen reader announcements for dynamic updates.
- Color contrast: 4.5:1 normal text, 3:1 large text/UI components.
- Focus indicators: visible, consistent, never hidden.
- Touch targets: minimum 44x44px.

### Implementation
- Semantic HTML: `<nav>`, `<main>`, `<section>`, `<article>`, `<button>`.
- ARIA labels for icon-only buttons and complex components.
- `aria-live="polite"` for feed, alerts, and notifications.
- `aria-expanded`, `aria-controls`, `aria-current` for navigation.
- Skip links for keyboard users.
- Form labels always associated with inputs.
- Charts have alternative text summaries and data tables.

### Focus Management
- Focus trap in modals and command palette.
- Return focus after modal close.
- Logical tab order matching visual layout.
- `:focus-visible` for keyboard focus, `:focus` for mouse.

---

## 14. Responsive Design Strategy

### Breakpoints & Behaviors

| Range | Layout | Sidebar | KPIs | Grid |
|-------|--------|---------|------|------|
| < 640px | Single column | Bottom nav or hidden | 1 swipeable | 1 col |
| 640–1023px | Two columns | Icon rail | 2 per row | 2 col |
| 1024–1439px | Multi-column | Expanded | 4 per row | 3 col |
| ≥1440px | Full dashboard | Expanded | 6 per row | 4 col |
| ≥1920px | Ultra-wide | Expanded + side panels | 8 per row | 4 col |

### Mobile Adaptations
- Sticky bottom nav with 5 primary actions.
- Floating AI assistant button.
- Collapsible sections with chevron.
- Swipeable KPI and department cards.
- Simplified charts with touch tooltips.
- Bottom sheets for filters and actions.

### Tablet Adaptations
- Icon-rail sidebar, expandable on hover.
- Two-column grid for secondary widgets.
- Larger touch targets.
- Split-pane for detail views.

---

## 15. Dark Mode Strategy

### Implementation
- CSS variables switch via `data-theme="dark"` on `<html>`.
- Tailwind `dark:` variants.
- User preference persisted in `decision_center_preferences` and localStorage.
- System preference detection via `prefers-color-scheme`.

### Color Adaptations
- Backgrounds: deep slate (gray-900) to mid slate (gray-800) surfaces.
- Text: white to gray-300.
- Borders: gray-700 to gray-800.
- Shadows: darker, less diffuse.
- Charts: light text and grid lines; adjust series colors for visibility.

### Components in Dark Mode
- Cards: gray-800 background, gray-700 border.
- Inputs: gray-900 background, gray-700 border, white text.
- Buttons: adjusted hover states.
- Alerts: same semantic colors but slightly desaturated.

---

## 16. Frontend Architecture

### Tech Stack
- **Framework**: Next.js 14+ (App Router).
- **Language**: TypeScript.
- **Styling**: Tailwind CSS.
- **Components**: shadcn/ui + custom components.
- **Icons**: Lucide React.
- **Charts**: Recharts, Plotly.js, D3 (custom).
- **State**: React Context + Zustand for global UI state.
- **Data Fetching**: React Query (TanStack Query) + Server Actions.
- **Real-time**: Socket.io client or native WebSocket + EventSource.
- **Animation**: Framer Motion + Tailwind transitions.
- **Forms**: React Hook Form + Zod.

### Directory Structure
```
frontend/
├── app/
│   ├── decision-center/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── loading.tsx
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/                    # shadcn/ui primitives
│   ├── decision-center/       # Decision Center widgets
│   ├── layout/                # Sidebar, TopBar, Shell
│   ├── charts/                # Reusable charts
│   ├── data-grid/             # Enterprise table
│   ├── command-palette/       # Command palette
│   └── ai/                    # AI assistant panel
├── hooks/
│   ├── useDecisionCenter.ts
│   ├── useWebSocket.ts
│   ├── useTheme.ts
│   └── usePermissions.ts
├── lib/
│   ├── api.ts                 # API client
│   ├── utils.ts
│   ├── constants.ts
│   └── tokens.ts              # Design tokens
├── stores/
│   ├── uiStore.ts             # UI state (theme, sidebar, filters)
│   └── decisionCenterStore.ts # Decision Center data
├── providers/
│   ├── QueryProvider.tsx
│   ├── ThemeProvider.tsx
│   └── AuthProvider.tsx
├── types/
│   └── decision-center.ts
└── styles/
    └── animations.css
```

### Component Patterns
- **Container/Presentational** separation for widgets.
- **Compound components** for complex UI (e.g., Card, Dialog, DataGrid).
- **Render props / slots** for flexible widget content.
- **Custom hooks** for data fetching, real-time, and permissions.

### State Management
- **Zustand**: theme, sidebar state, command palette, filters, user preferences.
- **React Query**: server state (Decision Center data, KPIs, alerts, feed) with caching and background refresh.
- **URL state**: date filters, selected department, search query.

### API Integration
- Centralized API client with interceptors for auth and organization headers.
- React Query hooks for each endpoint.
- Optimistic updates for actions (approve, dismiss, assign).
- Background refetch for real-time widgets.

### Real-Time Client
- WebSocket connection on Decision Center page mount.
- Subscribe to organization room.
- Event handlers update React Query cache or Zustand store.
- SSE fallback for notifications.

---

## 17. Page Wireframes (Textual)

### Decision Center Page

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ≡  Executive Decision Center                 🔍  🔔  🤖  +  🌙  👤                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Good Morning, Larry                                                            │ │
│  │ Today is Monday, 13 July 2026 · Acme Health · Hospital Director                  │ │
│  │ [3 Tasks]  [2 Meetings]  [5 Notifications]                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌────────────┐  ┌─────────────────────────────────────────────────────────────┐   │
│  │            │  │ AI Daily Briefing · Generated 08:00                        │   │
│  │   84       │  │ • Revenue increased 8% versus last month.                    │   │
│  │  Health    │  │ • Bed occupancy exceeded 85% in ICU.                         │   │
│  │  Score     │  │ • Three medicines below reorder level.                       │   │
│  │            │  │ • Five ETL jobs completed overnight.                         │   │
│  │ ▓▓▓▓▓▓▓░  │  │ • Data quality score improved to 92.                       │   │
│  │            │  └─────────────────────────────────────────────────────────────┘   │
│  └────────────┘                                                                    │
│                                                                                     │
│  Critical Alerts [High 3] [Medium 5] [Low 8]                                       │
│  ┌────────────────────────────────────────────────────────────────────────────────┐│
│  │ 🔴 Revenue decline 12% in Eastern Region · Impact: $24k · Action: Review policy  ││
│  │    Owner: Sarah M. · Due: Today 5:00 PM                                          ││
│  ├────────────────────────────────────────────────────────────────────────────────┤│
│  │ 🟡 Medicine stock low (Paracetamol) · Impact: 2 days remaining · Action: Reorder ││
│  │    Owner: Pharmacy · Due: Tomorrow                                               ││
│  └────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                     │
│  ┌────────────────────────────────────┐  ┌───────────────────────────────────────┐   │
│  │ Decision Feed                       │  │ Department Performance               │   │
│  │ • Revenue increased 10:23 AM        │  │ ● Clinical   91  [Admissions ↗]      │   │
│  │ • Inventory low  09:45 AM           │  │ ● Pharmacy   76  [Stock ↘]             │   │
│  │ • ETL completed  09:30 AM           │  │ ● Finance    88  [Revenue ↗]           │   │
│  │ • Report submitted 08:15 AM           │  │ ● HR         82  [Staff ↗]             │   │
│  └────────────────────────────────────┘  └───────────────────────────────────────┘   │
│                                                                                     │
│  Executive KPIs                                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │ $1.2M  │ │ 1,240  │ │ 85%    │ │ 42     │ │ 98%    │ │ 156    │              │
│  │ Revenue│ │Admiss. │ │Occup.  │ │Surgeries│ │Quality │ │Staff   │              │
│  │ ↗ 8%   │ │ ↗ 5%   │ │ ⚠️ -3% │ │ ↗ 12%  │ │ ✓ 98%  │ │ → 0%   │              │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘              │
│                                                                                     │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐   │
│  │ Forecast: Admissions              │  │ Pending Actions                    │   │
│  │ [Chart with confidence band]       │  │ • Approve budget (Finance) · Today │   │
│  │ Risks: flu season surge           │  │ • Review ETL failure (IT) · Overdue  │   │
│  │ Opportunities: new ward opening   │  │ • Submit compliance report · 2 days  │   │
│  └────────────────────────────────────┘  └────────────────────────────────────┘   │
│                                                                                     │
│  AI Recommendations                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────┐│
│  │ 🔴 Open a temporary ward before flu season · $120k benefit · 95% confidence    ││
│  │ 🟡 Renegotiate supplier contract for Paracetamol · $15k benefit · 82% conf.    ││
│  │ 🟢 Schedule staff training on new ETL workflow · 5% productivity gain          ││
│  └────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                     │
│  ┌────────────────┐  ┌────────────────────────────────────────────────────┐      │
│  │ Upcoming Reports│  │ Quick Actions                  Recent Activity       │      │
│  │ • Monthly · 15 Jul│  │ Import  Report  ETL  Workflow  • Report generated    │      │
│  │ • Quarterly · 31 Jul│  │ AI  User  Dept  Settings      • ETL completed      │      │
│  │ • Compliance · 5 Aug│  │                               • User invited       │      │
│  └────────────────┘  └────────────────────────────────────────────────────┘      │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 18. UI Specifications Summary

| Element | Token | Value |
|---------|-------|-------|
| Primary button height | 40px | 2.5rem |
| Card radius | 8px | --radius-lg |
| Card padding | 24px | --space-6 |
| Section gap | 24px | --space-6 |
| Top bar height | 64px | 4rem |
| Sidebar width | 264px | 16.5rem |
| Sidebar collapsed | 72px | 4.5rem |
| Body font size | 16px | --font-size-base |
| Heading font weight | 700 | --font-weight-bold |
| Card shadow hover | shadow-md | --shadow-md |
| Focus ring | 3px primary | --shadow-focus |
| Toast duration | 5000ms | --duration-toast |
| Chart tooltip radius | 8px | --radius-lg |
| Table row height | 52px | 3.25rem |
| KPI card min-width | 160px | 10rem |
| Modal overlay | 48% opacity | --color-bg-overlay |

---

## 19. Integration with Existing AEDIP

- **No backend or database changes in Part 3**.
- Design tokens added to frontend theme files.
- Components built to consume Phase 7 Part 2 APIs (`/api/v1/decision-center/*`).
- Reuses existing auth state and organization context.
- Next.js app integrated into existing frontend directory or newly created `frontend/` if not present.
- Charts consume data from existing `dashboard_data_service` and new Decision Center services.
- AI assistant panel connects to existing Phase 6 AI chat APIs.

---

## 20. Output Deliverables

1. **Design System** — color, typography, spacing, radius, elevation tokens.
2. **Component Library** — buttons, cards, inputs, tables, badges, dialogs, toasts, dropdowns, tabs, charts, data grid.
3. **Layout System** — grid, breakpoints, widget sizing, responsive strategy.
4. **Wireframes** — desktop, tablet, mobile, ultra-wide textual wireframes.
5. **Responsive Layouts** — breakpoint behaviors and adaptations.
6. **Design Tokens** — full CSS variable set.
7. **Animation Guide** — timing, easing, motion patterns, reduced motion.
8. **Accessibility Guide** — WCAG AA, keyboard, screen reader, focus management.
9. **Dashboard Mockup Description** — detailed Decision Center section specifications.
10. **UI Specifications** — sizing, spacing, state details.
11. **Frontend Architecture** — Next.js, Tailwind, state management, real-time, API integration, directory structure.

All specifications are production-ready and ready for implementation in **Part 4**.
