# Design System

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document the design system: tokens, colors, typography, and spacing.

## Scope

All design tokens and visual language.

## Audience

Frontend developers and designers.

---

## 1. CSS Framework

- **Tailwind CSS 3.4.7** — utility-first CSS framework
- **tailwindcss-animate** — animation utilities
- **class-variance-authority** — component variant management
- **tailwind-merge** — intelligent Tailwind class merging

## 2. Color System

Tailwind CSS variables mapped to semantic names:

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | White | Dark gray | Page background |
| `--foreground` | Dark gray | White | Text color |
| `--primary` | Brand blue | Brand blue | Primary actions |
| `--primary-foreground` | White | White | Text on primary |
| `--secondary` | Light gray | Dark gray | Secondary actions |
| `--accent` | Light blue | Dark blue | Accent elements |
| `--sidebar` | Dark blue | Darker blue | Sidebar background |
| `--sidebar-foreground` | White | White | Sidebar text |
| `--sidebar-accent` | Blue | Blue | Active nav item |
| `--destructive` | Red | Red | Error/danger actions |
| `--muted` | Light gray | Dark gray | Muted elements |
| `--border` | Light gray | Dark gray | Borders |

## 3. Typography

- **Font**: System font stack (no custom font loaded)
- **Sizes**: Tailwind defaults (`text-xs` to `text-4xl`)
- **Weights**: `font-medium`, `font-semibold`, `font-bold`
- **Line height**: Tailwind defaults

## 4. Spacing

Tailwind spacing scale used throughout:
- `gap-1` (4px) to `gap-8` (32px) for common spacing
- `px-3`, `px-4`, `px-6` for horizontal padding
- `py-2`, `py-3`, `py-4` for vertical padding

## 5. Border Radius

- `rounded-md` (6px) — buttons, inputs
- `rounded-lg` (8px) — cards, panels
- `rounded-full` — avatars, badges

## 6. Key Files

| File | Purpose |
|------|---------|
| `frontend/tailwind.config.ts` | Tailwind configuration with theme tokens |
| `frontend/app/globals.css` | CSS variables for light/dark themes |
| `frontend/lib/utils.ts` | `cn()` helper for class merging |

## Related Documents

- [themes.md](themes.md) — Theme system
- [component-library.md](component-library.md) — Component catalog
- [accessibility.md](accessibility.md) — Accessibility
