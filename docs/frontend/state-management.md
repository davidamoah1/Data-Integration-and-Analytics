# State Management

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Frontend Lead

---

## Purpose

Document the Zustand state management architecture.

## Scope

All stores, state patterns, and auth state.

## Audience

Frontend developers.

---

## 1. State Management Library

- **Zustand 4.5.4** — lightweight, hook-based state management
- No Redux, Context API, or React Query used
- Stores are global singletons accessible via custom hooks

## 2. Auth Store

`frontend/stores/authStore.ts`

### State

| Field | Type | Description |
|-------|------|-------------|
| `user` | `User \| null` | Current user object |
| `isAuthenticated` | `boolean` | Auth status |
| `isLoading` | `boolean` | Loading state |
| `error` | `string \| null` | Error message |
| `accessToken` | `string \| null` | JWT access token |
| `refreshToken` | `string \| null` | JWT refresh token |

### Methods

| Method | Description |
|--------|-------------|
| `login(email, password)` | Authenticate user |
| `logout()` | Clear auth state |
| `refreshAuth()` | Refresh access token |
| `hasPermission(perm)` | Check if user has permission |
| `hasRole(role)` | Check if user has role |
| `updateProfile(data)` | Update user profile |

### Permission Checking

```typescript
hasPermission: (permission: string) => boolean
// Returns true if user's permissions include the given permission

hasRole: (role: string) => boolean
// Returns true if user's roles include the given role
```

## 3. API Client

`frontend/lib/api.ts` — Axios-based API client that:
- Attaches JWT bearer token to requests
- Handles token refresh on 401
- Redirects to login on auth failure

## Related Documents

- [routing.md](routing.md) — Routing and route guards
- [navigation.md](navigation.md) — Navigation
- [../backend/authentication.md](../backend/authentication.md) — Backend auth
