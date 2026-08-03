"use client";

import { RouteGuard } from "@/components/auth/RouteGuard";
import { JobMonitor } from "@/components/jobs/JobMonitor";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Activity } from "lucide-react";

export default function JobsPage() {
  return (
    <RouteGuard roles={["org_admin", "org_owner", "data_analyst", "etl_developer", "viewer"]}>
      <div className="container mx-auto max-w-5xl space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold">
              <Activity className="h-6 w-6" />
              Background Jobs
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Monitor and manage long-running tasks (ETL, OCR, reports, imports)
            </p>
          </div>
        </div>

        <JobMonitor />
      </div>
    </RouteGuard>
  );
}
