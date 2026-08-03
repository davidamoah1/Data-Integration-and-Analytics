'use client';

import { useEffect, useState } from 'react';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Newspaper, FileText, Plus } from 'lucide-react';
import Link from 'next/link';

interface Publication {
  id: number;
  title: string;
  status: 'draft' | 'in_review' | 'published';
  authors: string;
  created_at: string;
  journal?: string;
}

export default function PublicationsPage() {
  return (
    <RouteGuard roles={['researcher', 'org_admin', 'org_owner', 'super_admin']}>
      <PublicationsContent />
    </RouteGuard>
  );
}

function PublicationsContent() {
  const [publications, setPublications] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Newspaper className="h-6 w-6" />
            Publications
          </h1>
          <p className="mt-1 text-muted-foreground">
            Manage research publications and reports.
          </p>
        </div>
        <Link
          href="/reports"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> New Publication
        </Link>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading publications...</div>
      ) : publications.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Newspaper className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium">No publications yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Create a new publication report from your research data.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {publications.map((pub) => (
            <Card key={pub.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{pub.title}</CardTitle>
                  <Badge
                    variant={
                      pub.status === 'published'
                        ? 'success'
                        : pub.status === 'in_review'
                          ? 'warning'
                          : 'default'
                    }
                  >
                    {pub.status.replace('_', ' ')}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{pub.authors}</p>
                {pub.journal && (
                  <p className="mt-1 text-xs text-muted-foreground">Journal: {pub.journal}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
