"""File storage architecture — abstract object storage layer.

Modules:
  models    — FileRecord ORM model (metadata only, no blob data)
  storage   — Storage backend abstraction (local, R2, S3, Supabase)
  repositories — FileRepository for DB metadata access
  service   — FileService orchestrating upload/download/delete
  routes    — API endpoints for file operations

Architecture:
  API → FileService → StorageBackend (R2/S3/Supabase/Local)
                   → FileRepository → Database (metadata only)
"""
