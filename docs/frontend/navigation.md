# Navigation

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document sidebar, breadcrumbs, and navigation patterns.

## Scope

All navigation components and patterns.

## Audience

Frontend developers.

---

## 1. Sidebar Structure

`frontend/components/layout/Sidebar.tsx`

Five navigation groups with permission-based filtering:

### Overview
- Dashboard (`/dashboard`) — no permission required
- Studios (`/studios`) — no permission required
- Templates (`/templates`) — no permission required

### Data
- Smart Capture (`/capture`) — no permission required
- Datasets (`/datasets`) — `datasets.view`
- Analytics (`/analytics`) — `analytics.view`
- Reports (`/reports`) — `reports.view`

### Intelligence
- Analytics Assistant (`/ai`) — `ai.use`
- Scheduler (`/scheduler`) — no permission required

### Administration
- Notifications (`/notifications`) — no permission required
- Members (`/admin`) — `users.read`
- Admin Portal (`/admin-portal`) — role: `super_admin`
- Audit Logs (`/audit`) — `audit.view`

### Platform
- Billing (`/billing`) — no permission required (placeholder)
- Connectors (`/connectors`) — no permission required (placeholder)
- Marketplace (`/marketplace`) — no permission required (placeholder)
- API Keys (`/api-keys`) — no permission required (future)
- Webhooks (`/webhooks`) — no permission required (placeholder)
- Settings (`/settings`) — no permission required

## 2. Visibility Logic

```typescript
const isVisible = (item: NavItem) => {
  if (item.permission && !hasPermission(item.permission)) return false;
  if (item.role && !hasRole(item.role)) return false;
  return true;
};
```

Empty groups (all items hidden) are not rendered.

## 3. Active State

Active route determined by:
```typescript
const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
```

Active items get `bg-sidebar-accent text-white`; inactive items get hover states.

## 4. User Info Display

Sidebar shows:
- User full name
- User email (truncated)
- Up to 2 role badges

## Related Documents

- [routing.md](routing.md) — Route structure
- [state-management.md](state-management.md) — Auth store
- [../governance/frontend-navigation-matrix.md](../governance/frontend-navigation-matrix.md) — Full nav matrix
