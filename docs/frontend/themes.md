# Themes

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document the theme system (light, dark, system).

## Scope

Theme provider, CSS variables, and theme switching.

## Audience

Frontend developers.

---

## 1. Theme Provider

`frontend/providers/ThemeProvider.tsx`

### Supported Themes

| Theme | Description |
|-------|-------------|
| `light` | Light mode |
| `dark` | Dark mode |
| `system` | Follow OS preference |

### Implementation

- Theme stored in `localStorage` under key `dataflow-theme`
- System preference detected via `window.matchMedia('(prefers-color-scheme: dark)')`
- Theme applied by adding `dark` class to `<html>` element
- Listens for system theme changes when in `system` mode

### API

```typescript
const { theme, setTheme, resolvedTheme } = useTheme();
// theme: 'light' | 'dark' | 'system'
// setTheme(next): sets and persists theme
// resolvedTheme: 'light' | 'dark' (actual applied theme)
```

## 2. CSS Variables

Theme colors defined as CSS variables in `frontend/app/globals.css`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --primary: 221 83% 53%;
  /* ... */
}

.dark {
  --background: 222 47% 11%;
  --foreground: 210 40% 98%;
  --primary: 221 83% 53%;
  /* ... */
}
```

Tailwind config maps these to utility classes (`bg-background`, `text-foreground`, etc.).

## Related Documents

- [design-system.md](design-system.md) — Design system
- [component-library.md](component-library.md) — Components
