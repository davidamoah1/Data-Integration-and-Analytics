'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { useTheme } from '@/providers/ThemeProvider';
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AppearanceSettings() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const options = [
    {
      value: 'light' as const,
      label: 'Light',
      description: 'Bright background with dark text',
      icon: Sun,
    },
    {
      value: 'dark' as const,
      label: 'Dark',
      description: 'Dark background with light text',
      icon: Moon,
    },
    {
      value: 'system' as const,
      label: 'System',
      description: 'Follow your device preference',
      icon: Monitor,
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>Choose how DataFlow looks to you. Your preference is saved automatically.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            {options.map((opt) => {
              const Icon = opt.icon;
              const isActive = theme === opt.value;
              return (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={cn(
                    'flex flex-col items-center gap-3 rounded-lg border p-4 text-center transition-all',
                    isActive
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-border hover:border-primary/50 hover:bg-accent',
                  )}
                >
                  <div className={cn(
                    'flex h-12 w-12 items-center justify-center rounded-lg',
                    isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
                  )}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-medium">{opt.label}</p>
                    <p className="text-xs text-muted-foreground">{opt.description}</p>
                  </div>
                  {isActive && (
                    <span className="text-xs font-medium text-primary">Active</span>
                  )}
                </button>
              );
            })}
          </div>
          <div className="mt-4 rounded-lg bg-muted p-3 text-sm text-muted-foreground">
            Currently using <span className="font-medium text-foreground">{resolvedTheme}</span> mode.
            {theme === 'system' && ' (following your system preference)'}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Density</CardTitle>
          <CardDescription>Adjust the spacing and compactness of the interface</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              className="flex flex-col items-center gap-2 rounded-lg border border-primary bg-primary/5 p-4 text-center ring-2 ring-primary/20"
            >
              <p className="font-medium">Comfortable</p>
              <p className="text-xs text-muted-foreground">More padding and spacing</p>
            </button>
            <button
              className="flex flex-col items-center gap-2 rounded-lg border border-border p-4 text-center hover:border-primary/50 hover:bg-accent"
            >
              <p className="font-medium">Compact</p>
              <p className="text-xs text-muted-foreground">Tighter spacing for more content</p>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
