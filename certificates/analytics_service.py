"""Approved Certificate Analytics Service.

This is the SINGLE source of truth for analytics computed exclusively
from certificates that have been approved through the Certificate
Intelligence workflow (CaptureDocument.status == "approved").

All analytics queries enforce:
  - organization_id == current org (tenant isolation)
  - status == "approved" (approved-only)
  - document_type IN CERTIFICATE_DOC_TYPES (certificate documents only)

No endpoint or function in this module is capable of aggregating
rejected, pending, unverified, or deleted certificates.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from capture.models import CaptureDocument, CaptureField

logger = logging.getLogger(__name__)

# Certificate document types — same set as routes.py
CERTIFICATE_DOC_TYPES = {
    "academic_certificate",
    "degree_certificate",
    "diploma",
    "professional_certificate",
    "training_certificate",
    "certificate_of_completion",
    "certificate_of_attendance",
    "membership_certificate",
    "license_certification",
}

# Field names that represent the certificate name/qualification
CERT_NAME_FIELDS = ("qualification", "course", "programme", "degree")

# Field names that represent the completion/issue date (in priority order)
DATE_FIELDS = ("date_awarded", "date_issued", "graduation_date")

# Field name for the recipient/student
RECIPIENT_FIELDS = ("student_name", "full_name")

# Field name for the issuing organization
INSTITUTION_FIELDS = ("institution",)

# Field name for the course
COURSE_FIELDS = ("course", "programme")

# Field name for certificate number
CERT_NUMBER_FIELDS = ("certificate_number", "license_number")

NOT_AVAILABLE = "Not Available"


def _approved_cert_query(org_id: int):
    """Base query predicate: approved certificates for a given org.

    This is the CANONICAL approval predicate. Every analytics function
    in this module starts with this query. Never bypass it.
    """
    return select(CaptureDocument).where(
        CaptureDocument.organization_id == org_id,
        CaptureDocument.status == "approved",
        CaptureDocument.document_type.in_(CERTIFICATE_DOC_TYPES),
    )


def _load_field_map(
    db: DbSession, doc_ids: list[int]
) -> dict[int, dict[str, str]]:
    """Batch-load all fields for the given document IDs.

    Returns {document_id: {field_name: value}}.
    """
    if not doc_ids:
        return {}
    rows = (
        db.execute(
            select(CaptureField).where(CaptureField.document_id.in_(doc_ids))
        )
        .scalars()
        .all()
    )
    result: dict[int, dict[str, str]] = {}
    for r in rows:
        result.setdefault(r.document_id, {})[r.field_name] = r.value or ""
    return result


def _pick_field(field_map: dict[str, str], candidates: tuple[str, ...]) -> str:
    """Return the first non-empty value from candidate field names."""
    for name in candidates:
        val = field_map.get(name, "")
        if val and val.strip():
            return val.strip()
    return ""


def _parse_year(value: str | None) -> str | None:
    """Extract a 4-digit year from a date string."""
    if not value:
        return None
    # Try ISO format first
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y")
        except ValueError:
            continue
    # Fallback: look for a 4-digit year anywhere
    m = re.search(r"\b(19|20)\d{2}\b", value)
    if m:
        return m.group(0)
    return None


def _parse_date(value: str | None) -> date | None:
    """Parse a date string into a date object."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _normalize_name(value: str) -> str:
    """Normalize a name for grouping (title-case, collapse whitespace)."""
    if not value:
        return value
    return re.sub(r"\s+", " ", value.strip().title())


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass
class ApprovedAnalyticsFilters:
    """Server-side filters for approved certificate analytics."""

    certificate_name: str | None = None
    certificate_type: str | None = None
    issuing_organization: str | None = None
    course: str | None = None
    recipient: str | None = None
    date_from: str | None = None  # ISO format YYYY-MM-DD
    date_to: str | None = None
    year: int | None = None

    def applies_to_doc(self, doc: CaptureDocument, field_map: dict[str, str]) -> bool:
        """Check if a document matches these filters."""
        if self.certificate_type and doc.document_type != self.certificate_type:
            return False
        if self.certificate_name:
            cert_name = _pick_field(field_map, CERT_NAME_FIELDS)
            if self.certificate_name.lower() not in cert_name.lower():
                return False
        if self.issuing_organization:
            inst = _pick_field(field_map, INSTITUTION_FIELDS)
            if self.issuing_organization.lower() not in inst.lower():
                return False
        if self.course:
            course_val = _pick_field(field_map, COURSE_FIELDS)
            if self.course.lower() not in course_val.lower():
                return False
        if self.recipient:
            recip = _pick_field(field_map, RECIPIENT_FIELDS)
            if self.recipient.lower() not in recip.lower():
                return False
        if self.date_from or self.date_to or self.year:
            date_val = _pick_field(field_map, DATE_FIELDS)
            parsed = _parse_date(date_val) if date_val else None
            if self.year:
                if parsed is None or parsed.year != self.year:
                    return False
            if self.date_from:
                from_date = _parse_date(self.date_from)
                if from_date and (parsed is None or parsed < from_date):
                    return False
            if self.date_to:
                to_date = _parse_date(self.date_to)
                if to_date and (parsed is None or parsed > to_date):
                    return False
        return True


@dataclass
class KPIs:
    total_approved: int = 0
    unique_recipients: int = 0
    certificate_types: int = 0
    certificate_names: int = 0
    issuing_organizations: int = 0
    courses: int = 0
    avg_certs_per_person: float = 0.0
    completed_this_month: int = 0
    completed_this_year: int = 0
    latest_completion_date: str | None = None
    earliest_completion_date: str | None = None


@dataclass
class DataQuality:
    total: int = 0
    recipient_identified: int = 0
    certificate_name_identified: int = 0
    completion_date_identified: int = 0
    institution_identified: int = 0
    certificate_number_identified: int = 0
    course_identified: int = 0


@dataclass
class ApprovedAnalyticsResult:
    kpis: KPIs
    data_quality: DataQuality
    by_name: dict[str, int]
    by_type: dict[str, int]
    by_issuer: dict[str, int]
    by_course: dict[str, int]
    trends: dict[str, int]  # year -> count
    recipients: list[dict[str, Any]]
    certs_per_person: dict[str, int]  # "1 cert" -> count
    insights: list[str]
    records: list[dict[str, Any]]
    total: int


# ── Service ───────────────────────────────────────────────────────────────


class ApprovedCertificateAnalyticsService:
    """Analytics service for approved certificates only.

    Every method enforces:
      - organization_id == org_id (tenant isolation)
      - status == "approved" (approved-only)
      - document_type IN CERTIFICATE_DOC_TYPES
    """

    def __init__(self, db: DbSession):
        self.db = db

    def _get_approved_docs(
        self, org_id: int, filters: ApprovedAnalyticsFilters | None = None
    ) -> list[CaptureDocument]:
        """Fetch approved certificate documents for an org."""
        query = _approved_cert_query(org_id).order_by(CaptureDocument.id.desc())
        docs = list(self.db.execute(query.limit(10000)).scalars().all())
        if not filters:
            return docs
        # Apply filters that can be done at DB level
        if filters.certificate_type:
            docs = [d for d in docs if d.document_type == filters.certificate_type]
        return docs

    def _get_field_maps(self, doc_ids: list[int]) -> dict[int, dict[str, str]]:
        return _load_field_map(self.db, doc_ids)

    def get_summary(
        self,
        org_id: int,
        filters: ApprovedAnalyticsFilters | None = None,
    ) -> ApprovedAnalyticsResult:
        """Compute the full analytics summary for approved certificates."""
        docs = self._get_approved_docs(org_id, filters)
        field_maps = self._get_field_maps([d.id for d in docs])

        # Apply field-level filters
        if filters:
            docs = [
                d for d in docs
                if filters.applies_to_doc(d, field_maps.get(d.id, {}))
            ]

        total = len(docs)
        now = datetime.now(timezone.utc)
        this_month = now.month
        this_year = now.year

        # Aggregations
        by_name: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_issuer: dict[str, int] = {}
        by_course: dict[str, int] = {}
        by_year: dict[str, int] = {}
        recipient_set: set[str] = set()
        recipient_counts: dict[str, int] = {}
        dates: list[date] = []
        dq = DataQuality(total=total)

        for doc in docs:
            fm = field_maps.get(doc.id, {})

            # Certificate name
            cert_name = _pick_field(fm, CERT_NAME_FIELDS)
            display_name = cert_name if cert_name else NOT_AVAILABLE
            by_name[display_name] = by_name.get(display_name, 0) + 1
            if cert_name:
                dq.certificate_name_identified += 1

            # Type
            type_label = doc.document_type_label or doc.document_type or NOT_AVAILABLE
            by_type[type_label] = by_type.get(type_label, 0) + 1

            # Issuer
            inst = _pick_field(fm, INSTITUTION_FIELDS)
            display_inst = inst if inst else NOT_AVAILABLE
            by_issuer[display_inst] = by_issuer.get(display_inst, 0) + 1
            if inst:
                dq.institution_identified += 1

            # Course
            course_val = _pick_field(fm, COURSE_FIELDS)
            display_course = course_val if course_val else NOT_AVAILABLE
            by_course[display_course] = by_course.get(display_course, 0) + 1
            if course_val:
                dq.course_identified += 1

            # Recipient
            recip = _pick_field(fm, RECIPIENT_FIELDS)
            recip_norm = _normalize_name(recip) if recip else ""
            if recip_norm:
                recipient_set.add(recip_norm)
                recipient_counts[recip_norm] = recipient_counts.get(recip_norm, 0) + 1
                dq.recipient_identified += 1

            # Date
            date_val = _pick_field(fm, DATE_FIELDS)
            parsed_date = _parse_date(date_val) if date_val else None
            if parsed_date:
                dates.append(parsed_date)
                dq.completion_date_identified += 1
                yr = parsed_date.strftime("%Y")
                by_year[yr] = by_year.get(yr, 0) + 1
            elif date_val:
                year_str = _parse_year(date_val)
                if year_str:
                    by_year[year_str] = by_year.get(year_str, 0) + 1

            # Certificate number
            cert_num = _pick_field(fm, CERT_NUMBER_FIELDS)
            if cert_num:
                dq.certificate_number_identified += 1

        # Recompute this_month / this_year from parsed dates
        completed_this_month = sum(
            1 for d in dates if d.year == this_year and d.month == this_month
        )
        completed_this_year = sum(1 for d in dates if d.year == this_year)

        # Sort dicts by count descending
        by_name = dict(sorted(by_name.items(), key=lambda kv: kv[1], reverse=True))
        by_type = dict(sorted(by_type.items(), key=lambda kv: kv[1], reverse=True))
        by_issuer = dict(sorted(by_issuer.items(), key=lambda kv: kv[1], reverse=True))
        by_course = dict(sorted(by_course.items(), key=lambda kv: kv[1], reverse=True))
        by_year = dict(sorted(by_year.items()))

        # KPIs
        unique_recipients = len(recipient_set)
        kpis = KPIs(
            total_approved=total,
            unique_recipients=unique_recipients,
            certificate_types=len(by_type),
            certificate_names=len(by_name),
            issuing_organizations=len([k for k in by_issuer if k != NOT_AVAILABLE]),
            courses=len([k for k in by_course if k != NOT_AVAILABLE]),
            avg_certs_per_person=round(total / unique_recipients, 2) if unique_recipients else 0.0,
            completed_this_month=completed_this_month,
            completed_this_year=completed_this_year,
            latest_completion_date=max(dates).isoformat() if dates else None,
            earliest_completion_date=min(dates).isoformat() if dates else None,
        )

        # Certs per person distribution
        certs_per_person: dict[str, int] = {}
        for count in recipient_counts.values():
            if count >= 4:
                key = "4+ certificates"
            else:
                key = f"{count} certificate{'s' if count > 1 else ''}"
            certs_per_person[key] = certs_per_person.get(key, 0) + 1
        certs_per_person = dict(sorted(certs_per_person.items(), key=lambda kv: int(kv[0][0])))

        # Top recipients
        top_recipients = sorted(recipient_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]
        recipients_list = [
            {"name": name, "approved_certificates": count}
            for name, count in top_recipients
        ]

        # Insights
        insights = self._generate_insights(
            total, by_name, by_type, by_issuer, by_year, recipient_counts, kpis
        )

        # Records (for table / drill-down)
        records = []
        for doc in docs:
            fm = field_maps.get(doc.id, {})
            records.append({
                "id": doc.id,
                "recipient": _pick_field(fm, RECIPIENT_FIELDS) or NOT_AVAILABLE,
                "certificate_name": _pick_field(fm, CERT_NAME_FIELDS) or NOT_AVAILABLE,
                "certificate_type": doc.document_type_label or doc.document_type or NOT_AVAILABLE,
                "course": _pick_field(fm, COURSE_FIELDS) or NOT_AVAILABLE,
                "issuing_organization": _pick_field(fm, INSTITUTION_FIELDS) or NOT_AVAILABLE,
                "completion_date": _pick_field(fm, DATE_FIELDS) or NOT_AVAILABLE,
                "certificate_number": _pick_field(fm, CERT_NUMBER_FIELDS) or NOT_AVAILABLE,
                "verification_status": doc.verification_status,
                "approved_at": doc.approved_at.isoformat() if doc.approved_at else None,
                "batch_id": doc.batch_id,
                "filename": doc.filename,
            })

        return ApprovedAnalyticsResult(
            kpis=kpis,
            data_quality=dq,
            by_name=by_name,
            by_type=by_type,
            by_issuer=by_issuer,
            by_course=by_course,
            trends=by_year,
            recipients=recipients_list,
            certs_per_person=certs_per_person,
            insights=insights,
            records=records,
            total=total,
        )

    def _generate_insights(
        self,
        total: int,
        by_name: dict[str, int],
        by_type: dict[str, int],
        by_issuer: dict[str, int],
        by_year: dict[str, int],
        recipient_counts: dict[str, int],
        kpis: KPIs,
    ) -> list[str]:
        """Generate dynamically computed insights from real data."""
        insights: list[str] = []
        if total == 0:
            return insights

        # Top certificate name
        top_name = next(iter(by_name.items()), None)
        if top_name and top_name[0] != NOT_AVAILABLE:
            pct = round(top_name[1] / total * 100, 1)
            insights.append(
                f'"{top_name[0]}" represents {pct}% of all approved certificates ({top_name[1]} of {total}).'
            )

        # Top issuer
        top_issuer = next(iter(by_issuer.items()), None)
        if top_issuer and top_issuer[0] != NOT_AVAILABLE:
            pct = round(top_issuer[1] / total * 100, 1)
            insights.append(
                f'"{top_issuer[0]}" issued the highest number of approved certificates ({top_issuer[1]} of {total}).'
            )

        # Multi-cert recipients
        multi = sum(1 for c in recipient_counts.values() if c >= 3)
        if multi > 0:
            insights.append(
                f"{multi} recipient{'s have' if multi != 1 else ' has'} completed at least three approved certificates."
            )

        # Year-over-year trend
        years = sorted(by_year.keys())
        if len(years) >= 2:
            prev_year_count = by_year[years[-2]]
            curr_year_count = by_year[years[-1]]
            if prev_year_count > 0:
                change = round((curr_year_count - prev_year_count) / prev_year_count * 100, 1)
                direction = "increased" if change > 0 else "decreased" if change < 0 else "remained stable"
                insights.append(
                    f"Approved certificates {direction} by {abs(change)}% comparing {years[-2]} ({prev_year_count}) vs {years[-1]} ({curr_year_count})."
                )
            else:
                insights.append(
                    f"{curr_year_count} approved certificates were recorded in {years[-1]}, up from none in {years[-2]}."
                )

        # Average certs per person
        if kpis.unique_recipients > 0:
            insights.append(
                f"On average, each recipient holds {kpis.avg_certs_per_person} approved certificate(s)."
            )

        return insights

    def get_records(
        self,
        org_id: int,
        filters: ApprovedAnalyticsFilters | None = None,
        search: str | None = None,
        sort_by: str = "approved_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get paginated approved certificate records."""
        allowed_sort = {"approved_at", "recipient", "certificate_name", "issuing_organization", "completion_date"}
        if sort_by not in allowed_sort:
            sort_by = "approved_at"
        if sort_order not in ("asc", "desc"):
            sort_order = "desc"

        result = self.get_summary(org_id, filters)
        records = result.records

        # Search
        if search:
            search_lower = search.lower()
            records = [
                r for r in records
                if any(search_lower in str(r.get(k, "")).lower() for k in (
                    "recipient", "certificate_name", "certificate_type",
                    "issuing_organization", "course", "certificate_number",
                ))
            ]

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "approved_at":
            records.sort(key=lambda r: r.get("approved_at") or "", reverse=reverse)
        else:
            records.sort(key=lambda r: r.get(sort_by, "").lower() if r.get(sort_by) else "zzz", reverse=reverse)

        total = len(records)
        page = records[offset:offset + limit]

        return {
            "records": page,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_filter_options(self, org_id: int) -> dict[str, list[str]]:
        """Get available filter values (certificate names, types, issuers, courses, recipients)."""
        docs = self._get_approved_docs(org_id)
        field_maps = self._get_field_maps([d.id for d in docs])

        names: set[str] = set()
        types: set[str] = set()
        issuers: set[str] = set()
        courses: set[str] = set()
        recipients: set[str] = set()

        for doc in docs:
            fm = field_maps.get(doc.id, {})
            val = _pick_field(fm, CERT_NAME_FIELDS)
            if val:
                names.add(val)
            if doc.document_type:
                types.add(doc.document_type_label or doc.document_type)
            val = _pick_field(fm, INSTITUTION_FIELDS)
            if val:
                issuers.add(val)
            val = _pick_field(fm, COURSE_FIELDS)
            if val:
                courses.add(val)
            val = _pick_field(fm, RECIPIENT_FIELDS)
            if val:
                recipients.add(_normalize_name(val))

        return {
            "certificate_names": sorted(names),
            "certificate_types": sorted(types),
            "issuing_organizations": sorted(issuers),
            "courses": sorted(courses),
            "recipients": sorted(recipients),
        }
