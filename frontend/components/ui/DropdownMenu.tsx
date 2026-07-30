'use client';

import { createContext, useContext, useState, useRef, useEffect, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface DropdownMenuContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DropdownMenuContext = createContext<DropdownMenuContextValue | null>(null);

function useDropdownMenu() {
  const ctx = useContext(DropdownMenuContext);
  if (!ctx) throw new Error('DropdownMenu components must be used within DropdownMenu');
  return ctx;
}

export function DropdownMenu({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div ref={ref} className="relative inline-block">
        {children}
      </div>
    </DropdownMenuContext.Provider>
  );
}

export function DropdownMenuTrigger({ children, asChild }: { children: ReactNode; asChild?: boolean }) {
  const { open, setOpen } = useDropdownMenu();
  if (asChild && children && typeof children === 'object' && 'props' in children) {
    const child = children as React.ReactElement<{ onClick?: (e: React.MouseEvent) => void }>;
    return (
      <div onClick={(e) => { e.stopPropagation(); setOpen(!open); }}>
        {child}
      </div>
    );
  }
  return <div onClick={() => setOpen(!open)}>{children}</div>;
}

export function DropdownMenuContent({
  children,
  align = 'start',
}: {
  children: ReactNode;
  align?: 'start' | 'end';
}) {
  const { open, setOpen } = useDropdownMenu();
  if (!open) return null;
  return (
    <div
      className={cn(
        'absolute z-50 mt-2 min-w-[12rem] rounded-md border bg-popover p-1 shadow-md',
        align === 'end' ? 'right-0' : 'left-0',
      )}
      onClick={() => setOpen(false)}
    >
      {children}
    </div>
  );
}

export function DropdownMenuItem({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick?: () => void;
}) {
  return (
    <div
      className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
    >
      {children}
    </div>
  );
}
