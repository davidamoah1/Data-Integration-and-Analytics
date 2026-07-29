'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, Sun, Moon, ChevronDown, LogOut, User as UserIcon, Settings } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useTheme } from '@/providers/ThemeProvider';
import { getInitials } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';

export function TopNav() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-6">
      {/* Page title space */}
      <div className="flex-1" />

      {/* Right actions */}
      <div className="flex items-center gap-4">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>

        {/* Notifications */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="relative rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-destructive" />
          </button>
          {notifOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-lg border bg-popover shadow-lg">
              <div className="border-b p-3 font-medium">Notifications</div>
              <div className="max-h-64 overflow-y-auto p-2">
                <p className="py-4 text-center text-sm text-muted-foreground">No new notifications</p>
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-md p-1 hover:bg-accent"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
              {user ? getInitials(user.full_name) : '?'}
            </div>
            <span className="text-sm font-medium">{user?.full_name || 'User'}</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-lg border bg-popover shadow-lg">
              <div className="border-b p-3">
                <p className="text-sm font-medium">{user?.full_name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
                {user?.roles && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {user.roles.map((role) => (
                      <Badge key={role} variant="secondary" className="text-xs">
                        {role.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="p-1">
                <button
                  onClick={() => { setMenuOpen(false); router.push('/settings'); }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
                >
                  <UserIcon className="h-4 w-4" /> Profile
                </button>
                <button
                  onClick={() => { setMenuOpen(false); router.push('/settings'); }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
                >
                  <Settings className="h-4 w-4" /> Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
                >
                  <LogOut className="h-4 w-4" /> Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
