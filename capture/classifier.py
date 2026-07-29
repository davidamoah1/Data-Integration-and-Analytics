"""Document type classification for the Smart Data Capture platform.

Uses keyword/pattern scoring against the `capture.document_types` registry.
This is deliberately simple, transparent, and dependency-free (no ML model
download required) while still being effective on the register/form-style
documents this platform targets, whose headers/titles reliably contain
identifying phrases (e.g. "OPD REGISTER", "INVOICE", "ADMISSION REGISTER").

If no type scores above the confidence floor, the document is routed to the
user for manual type selection (`needs_type_confirmation`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from capture.document_types import ALL_DOCUMENT_TYPES, DocumentTypeSpec

CONFIDENCE_FLOOR = 0.35  # below this, ask the user to pick the type manually


@dataclass
class ClassificationResult:
    document_type: DocumentTypeSpec | None
    confidence: float
    needs_confirmation: bool
    candidates: list[tuple[str, float]]  # [(type_key, score), ...] top matches


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def classify_text(ocr_text: str) -> ClassificationResult:
    text = _normalize(ocr_text or "")

    if not text.strip():
        return ClassificationResult(None, 0.0, True, [])

    scores: dict[str, float] = {}
    for doc_type in ALL_DOCUMENT_TYPES:
        score = 0.0
        matched = 0
        for kw in doc_type.keywords:
            kw_norm = kw.lower()
            if kw_norm in text:
                # Longer, more specific keywords count for more.
                weight = 1.0 + (len(kw_norm.split()) - 1) * 0.5
                score += weight
                matched += 1
        if matched:
            # Normalize by keyword count so types with many keywords don't
            # win purely on volume; reward types with proportionally more hits.
            score = score / max(len(doc_type.keywords), 1) * (1 + matched * 0.1)
        scores[doc_type.key] = score

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_key, top_score = ranked[0] if ranked else (None, 0.0)

    # Squash raw score into a 0..1-ish confidence heuristically.
    confidence = min(top_score / 1.5, 1.0) if top_score > 0 else 0.0

    best_type = next((d for d in ALL_DOCUMENT_TYPES if d.key == top_key), None) if top_key else None
    needs_confirmation = confidence < CONFIDENCE_FLOOR or best_type is None

    candidates = [(k, round(s, 3)) for k, s in ranked[:5] if s > 0]

    return ClassificationResult(
        document_type=best_type,
        confidence=round(confidence, 3),
        needs_confirmation=needs_confirmation,
        candidates=candidates,
    )
