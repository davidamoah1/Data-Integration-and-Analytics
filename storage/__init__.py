"""File storage architecture â€” abstract object storage layer.

Modules:
  models    â€” FileRecord ORM model (metadata only, no blob data)
  storage   â€” Storage backend abstraction (local, R2, S3, Supabase)
  repositories â€” FileRepository for DB metadata access
  service   â€” FileService orchestrating upload/download/delete
  routes    â€” API endpoints for file operations

Architecture:
  API â†’ FileService â†’ StorageBackend (R2/S3/Supabase/Local)
                   â†’ FileRepository â†’ Database (metadata only)
"""
