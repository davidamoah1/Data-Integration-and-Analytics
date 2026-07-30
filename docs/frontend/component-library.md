# Component Library

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document reusable UI components.

## Scope

All shared components in the frontend.

## Audience

Frontend developers.

---

## 1. Auth Components

| Component | Path | Purpose |
|-----------|------|---------|
| `RouteGuard` | `components/auth/RouteGuard.tsx` | Route-level permission guard |
| `Can` | `components/auth/Can.tsx` | Conditional rendering by permission |

## 2. Layout Components

| Component | Path | Purpose |
|-----------|------|---------|
| `Sidebar` | `components/layout/Sidebar.tsx` | Navigation sidebar with permission filtering |
| `Header` | `components/layout/Header.tsx` | Top header bar |

## 3. UI Components

| Component | Path | Purpose |
|-----------|------|---------|
| `EmptyState` | `components/ui/EmptyState.tsx` | Empty state with icon, title, description, CTA |
| `ErrorState` | `components/ui/ErrorState.tsx` | Error state with retry button |
| `LoadingSpinner` | `components/ui/LoadingSpinner.tsx` | Loading indicator |
| `Badge` | `components/ui/Badge.tsx` | Status badge |
| `Card` | `components/ui/Card.tsx` | Content card |

## 4. Settings Components

| Component | Path | Purpose |
|-----------|------|---------|
| `AuditLogSettings` | `components/settings/AuditLogSettings.tsx` | Audit log viewer in settings |
| `ProfileSettings` | `components/settings/ProfileSettings.tsx` | Profile settings form |

## 5. Landing Components

| Component | Path | Purpose |
|-----------|------|---------|
| `Testimonials` | `components/landing/Testimonials.tsx` | Customer testimonials |
| `Hero` | `components/landing/Hero.tsx` | Landing hero section |

## 6. Providers

| Component | Path | Purpose |
|-----------|------|---------|
| `ThemeProvider` | `providers/ThemeProvider.tsx` | Light/dark/system theme |

## 7. Pattern: Permission Gating

```tsx
// Route-level
<RouteGuard permission="users.read">
  <AdminPage />
</RouteGuard>

// Element-level
<Can permission="datasets.upload" fallback={<span>Read only</span>}>
  <UploadButton />
</Can>

// Sidebar visibility
const isVisible = (item: NavItem) => {
  if (item.permission && !hasPermission(item.permission)) return false;
  if (item.role && !hasRole(item.role)) return false;
  return true;
};
```

## Related Documents

- [design-system.md](design-system.md) — Design system
- [routing.md](routing.md) — Routing
- [state-management.md](state-management.md) — State management
