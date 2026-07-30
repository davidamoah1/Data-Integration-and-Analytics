'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { HelpCircle, X } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { getHelpConfigForRoles } from '@/lib/help';
import { cn } from '@/lib/utils';

export function AdaptiveHelp() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const config = user ? getHelpConfigForRoles(user.roles) : null;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!config) return null;

  const filteredTopics = query
    ? config.categories
        .flatMap((c) => c.topics)
        .filter((t) =>
          t.title.toLowerCase().includes(query.toLowerCase()) ||
          t.description.toLowerCase().includes(query.toLowerCase())
        )
    : config.categories.flatMap((c) =>
        c.topics.map((t) => ({ ...t, category: c.label }))
      );

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
        aria-label="Help"
      >
        <HelpCircle className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg border bg-popover shadow-lg">
          <div className="border-b p-3">
            <div className="flex items-center justify-between">
              <span className="font-medium">Help & Guides</span>
              <button
                onClick={() => setOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={config.searchPlaceholder}
              className="mt-2 w-full rounded-md border bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none"
              autoFocus
            />
          </div>

          <div className="max-h-80 overflow-y-auto p-2">
            {filteredTopics.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No help topics found.
              </p>
            ) : (
              filteredTopics.map((topic) => {
                const Icon = topic.icon;
                return (
                  <button
                    key={topic.id}
                    onClick={() => {
                      if (topic.href) {
                        router.push(topic.href);
                      }
                      setOpen(false);
                    }}
                    className="flex w-full items-start gap-3 rounded-md px-3 py-2 text-left hover:bg-accent"
                  >
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{topic.title}</p>
                      <p className="text-xs text-muted-foreground">{topic.description}</p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
