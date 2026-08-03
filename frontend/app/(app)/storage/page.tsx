"use client";

import { RouteGuard } from "@/components/auth/RouteGuard";
import { FileManager } from "@/components/storage/FileManager";
import { HardDrive } from "lucide-react";

export default function StoragePage() {
  return (
    <RouteGuard roles={["org_admin", "org_owner", "data_analyst", "etl_developer", "viewer"]}>
      <div className="container mx-auto max-w-4xl space-y-6 p-6">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <HardDrive className="h-6 w-6" />
            File Storage
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload and manage files in object storage. Files are stored in R2/S3/Supabase, not in the database.
          </p>
        </div>

        <FileManager />
      </div>
    </RouteGuard>
  );
}
