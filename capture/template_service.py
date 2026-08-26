"""Template learning system for the Smart Data Capture platform.

When users repeatedly correct the same field on the same document_type
within an organization, this records the correction pattern so future
uploads of that layout get a confidence boost on that field (see
`capture.extractors.extract_fields`'s `template_boost` parameter) â€” a real,
inspectable learning signal rather than an opaque ML model.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as DbSession

from capture.models import CaptureCorrection, CaptureTemplate


def record_correction(
    db: DbSession,
    organization_id: int,
    document_id: int,
    field_id: int,
    field_name: str,
    document_type: str | None,
    old_value: str | None,
    new_value: str | None,
    corrected_by: int,
) -> None:
    """Log a correction and update (or create) the org's learned template
    for this document type."""
    db.add(
        CaptureCorrection(
            document_id=document_id,
            field_id=field_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            corrected_by=corrected_by,
        )
    )

    if not document_type:
        db.commit()
        return

    template = (
        db.query(CaptureTemplate)
        .filter(
            CaptureTemplate.organization_id == organization_id,
            CaptureTemplate.document_type == document_type,
        )
        .first()
    )

    if template is None:
        template = CaptureTemplate(
            organization_id=organization_id,
            document_type=document_type,
            template_name=f"Learned template â€” {document_type}",
            field_mapping={},
            documents_learned_from=0,
        )
        db.add(template)
        db.flush()

    mapping = dict(template.field_mapping or {})
    field_info = dict(mapping.get(field_name, {"correction_count": 0, "sample_corrections": []}))
    field_info["correction_count"] = int(field_info.get("correction_count", 0)) + 1
    samples = list(field_info.get("sample_corrections", []))
    if new_value and new_value not in samples:
        samples.append(new_value)
        field_info["sample_corrections"] = samples[-5:]  # keep most recent 5
    mapping[field_name] = field_info
    template.field_mapping = mapping
    template.documents_learned_from += 1

    db.commit()


def get_template_boost(db: DbSession, organization_id: int, document_type: str | None) -> dict:
    """Return the learned field_mapping for this org+document_type, or {}."""
    if not document_type:
        return {}
    template = (
        db.query(CaptureTemplate)
        .filter(
            CaptureTemplate.organization_id == organization_id,
            CaptureTemplate.document_type == document_type,
            CaptureTemplate.is_active.is_(True),
        )
        .first()
    )
    return dict(template.field_mapping or {}) if template else {}
