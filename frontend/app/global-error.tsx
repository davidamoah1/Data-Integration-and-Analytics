'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error('Root layout error:', error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <div
          style={{
            display: 'flex',
            minHeight: '100vh',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            textAlign: 'center',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Something went wrong</h1>
          <p style={{ marginTop: '8px', maxWidth: '420px', color: '#6b7280', fontSize: '14px' }}>
            The application failed to load. Please refresh the page. If this keeps happening,
            contact support{error.digest ? ` (error code ${error.digest})` : ''}.
          </p>
          <button
            onClick={() => reset()}
            style={{
              marginTop: '24px',
              padding: '10px 20px',
              borderRadius: '8px',
              background: '#111827',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
