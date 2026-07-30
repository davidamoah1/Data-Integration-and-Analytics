'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { getSearchConfigForRoles } from '@/lib/search';
import { cn } from '@/lib/utils';

export function AdaptiveSearch() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const config = user
    ? getSearchConfigForRoles(user.roles, user.permissions)
    : null;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
      if (e.key === 'Escape') {
        setOpen(false);
        inputRef.current?.blur();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (!config) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <form onSubmit={handleSearch}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setOpen(true)}
            placeholder={config.placeholder}
            className="w-full rounded-lg border bg-background py-2 pl-9 pr-9 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </form>

      {open && config.scopes.length > 0 && (
        <div className="absolute mt-2 w-full rounded-lg border bg-popover shadow-lg">
          <div className="border-b p-2 text-xs font-semibold text-muted-foreground">
            Search across:
          </div>
          <div className="p-2">
            {config.scopes.map((scope) => (
              <button
                key={scope.id}
                onClick={() => {
                  router.push(`/search?scope=${scope.id}`);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
              >
                <span className="font-medium">{scope.label}</span>
              </button>
            ))}
          </div>
          <div className="border-t p-2 text-center text-xs text-muted-foreground">
            Press <kbd className="rounded border bg-muted px-1">⌘K</kbd> to search · <kbd className="rounded border bg-muted px-1">Esc</kbd> to close
          </div>
        </div>
      )}
    </div>
  );
}
