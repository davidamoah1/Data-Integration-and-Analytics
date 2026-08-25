"""Regression tests for AI Document Chat upload/access security fixes.

Covers:
  - Path traversal protection: a crafted filename cannot escape the
    intended upload directory.
  - Tenant isolation: chat() must not return another organization's
    document content when scoped by organization_id.
"""

from __future__ import annotations

import os
import tempfile

import ai.models  # noqa: F401 — registers tables with shared Base
from ai.engines.document_chat import DocumentChatEngine
from ai.models import AIDocument


def test_upload_document_sanitizes_path_traversal_filename(db_session):
    engine = DocumentChatEngine(db_session)
    malicious_filename = "../../../../tmp/evil_traversal_test.txt"

    result = engine.upload_document(
        filename=malicious_filename,
        file_content=b"hello world",
        file_type="txt",
        user_id=1,
        organization_id=1,
    )

    doc = db_session.query(AIDocument).filter(AIDocument.id == result["document_id"]).first()
    assert doc is not None

    # The file must be written inside the sandboxed upload directory,
    # never at (or above) the traversal target.
    upload_dir = os.path.join(tempfile.gettempdir(), "ai_documents")
    real_upload_dir = os.path.realpath(upload_dir)
    real_file_path = os.path.realpath(doc.file_path)
    assert real_file_path.startswith(real_upload_dir + os.sep)

    escaped_path = os.path.realpath(os.path.join(tempfile.gettempdir(), "evil_traversal_test.txt"))
    assert not os.path.exists(escaped_path)

    # Cleanup
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)


def test_chat_does_not_leak_document_across_organizations(db_session):
    engine = DocumentChatEngine(db_session)

    other_org_doc = AIDocument(
        organization_id=999,
        filename="secret.txt",
        file_type="txt",
        file_size=11,
        file_path=os.path.join(tempfile.gettempdir(), "does-not-matter.txt"),
        extracted_text="TOP SECRET org-999 content",
        user_id=42,
        is_indexed=True,
    )
    db_session.add(other_org_doc)
    db_session.commit()
    db_session.refresh(other_org_doc)

    result = engine.chat(
        document_id=other_org_doc.id,
        question="What does this document say?",
        user_id=1,
        organization_id=1,  # different org than the document
    )

    assert result["answer"] == "Document not found."


def test_chat_allows_access_within_same_organization(db_session, monkeypatch):
    engine = DocumentChatEngine(db_session)

    doc = AIDocument(
        organization_id=1,
        filename="report.txt",
        file_type="txt",
        file_size=20,
        file_path=os.path.join(tempfile.gettempdir(), "does-not-matter.txt"),
        extracted_text="Q3 revenue grew 12%.",
        user_id=1,
        is_indexed=True,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    def fake_chat(self, **kwargs):
        return {"response": "Revenue grew 12% in Q3.", "confidence_score": 0.9}

    monkeypatch.setattr("ai.gateway.AIGateway.chat", fake_chat)

    result = engine.chat(
        document_id=doc.id,
        question="How did revenue perform?",
        user_id=1,
        organization_id=1,
    )

    assert result["answer"] == "Revenue grew 12% in Q3."
