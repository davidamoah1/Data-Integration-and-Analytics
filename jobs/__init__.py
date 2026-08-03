"""Persistent job model for background processing.

Tracks all long-running tasks across the platform (ETL, OCR, reports,
large imports) with user/org association, progress, and results.

Architecture:
    API → JobService → TaskQueue/WorkerPool → Database
"""
