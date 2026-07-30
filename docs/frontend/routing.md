# Routing

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document the Next.js App Router structure and route protection.

## Scope

All routes, route groups, and navigation guards.

## Audience

Frontend developers.

---

## 1. App Router Structure

Next.js 14 App Router with route groups:

| Group | Path | Auth | Description |
|-------|------|------|-------------|
| Public | `/` | No | Landing page |
| Public | `/login` | No | Login page |
| Public | `/signup` | No | Registration page |
| Public | `/invite` | No | Invitation acceptance |
| Public | `/forgot-password` | No | Password reset request |
| Public | `/reset-password` | No | Password reset form |
| Public | `/about`, `/features`, `/pricing` | No | Marketing pages |
| Public | `/help`, `/contact`, `/feedback` | No | Support pages |
| Authenticated | `/(app)/dashboard` | Yes | Main dashboard |
| Authenticated | `/(app)/datasets` | Yes | Dataset management |
| Authenticated | `/(app)/analytics` | Yes | Dashboard builder |
| Authenticated | `/(app)/reports` | Yes | Reports |
| Authenticated | `/(app)/ai` | Yes | AI assistant |
| Authenticated | `/(app)/capture` | Yes | Smart Data Capture |
| Authenticated | `/(app)/admin` | Yes | User management |
| Authenticated | `/(app)/admin-portal` | Yes + super_admin | Platform admin |
| Authenticated | `/(app)/audit` | Yes | Audit logs |
| Authenticated | `/(app)/settings` | Yes | Settings (tabbed) |
| Error | `/forbidden` | No | 403 page |
| Error | `/offline` | No | Offline indicator |

## 2. Route Protection

### RouteGuard Component

```tsx
<RouteGuard permission="users.read">
  <AdminPage />
</RouteGuard>
```

Logic:
1. If not authenticated → redirect to `/login`
2. If permission required and `!hasPermission(permission)` → redirect to `/forbidden`
3. If role required and `!hasRole(role)` → redirect to `/forbidden`

### Can Component

```tsx
<Can permission="datasets.upload" fallback={<ReadOnlyBadge />}>
  <UploadButton />
</Can>
```

## 3. Navigation

See [navigation.md](navigation.md) for sidebar structure and visibility rules.

## Related Documents

- [navigation.md](navigation.md) — Navigation structure
- [state-management.md](state-management.md) — Auth store
- [../governance/frontend-navigation-matrix.md](../governance/frontend-navigation-matrix.md) — Nav matrix
