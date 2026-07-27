import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '@/stores/authStore';

describe('AuthStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ user: null, isAuthenticated: false, error: null });
  });

  it('starts with no user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('hasPermission returns false when no user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasPermission('users.read')).toBe(false);
  });

  it('hasRole returns false when no user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasRole('super_admin')).toBe(false);
  });

  it('hasPermission returns true for super_admin', () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'admin@test.com',
        full_name: 'Admin',
        roles: ['super_admin'],
        permissions: [],
      },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasPermission('anything')).toBe(true);
  });

  it('hasPermission checks specific permission', () => {
    useAuthStore.setState({
      user: {
        id: 2,
        email: 'viewer@test.com',
        full_name: 'Viewer',
        roles: ['viewer'],
        permissions: ['dashboard.view', 'profile.update'],
      },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasPermission('dashboard.view')).toBe(true);
    expect(result.current.hasPermission('users.read')).toBe(false);
  });

  it('clearError resets error state', () => {
    useAuthStore.setState({ error: 'Some error' });
    const { result } = renderHook(() => useAuthStore());
    act(() => result.current.clearError());
    expect(result.current.error).toBeNull();
  });
});
