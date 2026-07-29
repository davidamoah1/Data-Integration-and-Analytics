'use client';

import { useEffect } from 'react';
import { WifiOff, RotateCcw } from 'lucide-react';

export default function OfflinePage() {
  useEffect(() => {
    const handleOnline = () => window.location.reload();
    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center">
      <WifiOff className="mb-4 h-16 w-16 text-muted-foreground" />
      <h1 className="text-2xl font-bold">You&apos;re offline</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        DataFlow can&apos;t reach the internet right now. Some cached pages may still be available.
        You&apos;ll be automatically reconnected when your network returns.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        <RotateCcw className="h-4 w-4" /> Try Again
      </button>
    </div>
  );
}
