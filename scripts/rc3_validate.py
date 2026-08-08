"""RC3 real-world validation runner.

Loads synthetic industry datasets, runs the semantic pipeline, checks industry
detection, KPI/dashboard relevance, and report export. Writes a JSON report.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from semantic.service import SemanticIntelligenceService
from services.report_export_service import ReportExportService

INDUSTRIES = [
    "healthcare",
    "education",
    "church",
    "government",
    "retail",
    "ngo",
    "manufacturing",
    "banking",
    "insurance",
    "agriculture",
    "hospitality",
    "telecommunications",
]

PHASE4_REQUIRED = {
    "healthcare": ["admission", "bed occupancy", "diagnosis", "laboratory", "pharmacy", "patient"],
    "education": ["enrollment", "attendance", "graduation", "performance", "student"],
    "church": ["attendance", "visitor", "offering", "growth", "member"],
    "retail": ["sales", "revenue", "inventory", "order"],
    "government": ["budget", "project", "revenue", "asset"],
    "manufacturing": ["production", "machine", "utilization", "downtime", "yield"],
    "agriculture": ["farm", "yield", "harvest", "livestock", "weather"],
    "ngo": ["beneficiary", "donor", "funding", "program"],
    "banking": ["account", "transaction", "loan", "card"],
    "insurance": ["policy", "claim", "premium", "agent"],
    "hospitality": ["reservation", "guest", "room", "service"],
    "telecommunications": ["subscriber", "call", "data usage", "plan"],
}

# Blocklist for cross-industry contamination: a phase-4 dashboard should
# not contain keywords strongly tied to another industry.
CONTAMINATION_BLOCKLIST = {
    "healthcare": [
        "enrollment",
        "offering",
        "sales",
        "donor",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "education": [
        "patient",
        "offering",
        "sales",
        "donor",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "church": [
        "patient",
        "enrollment",
        "sales",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "retail": [
        "patient",
        "enrollment",
        "offering",
        "beneficiary",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "government": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "manufacturing": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "agriculture": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "ngo": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "subscriber",
    ],
    "banking": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "crop",
        "policy",
        "reservation",
        "subscriber",
        "diagnosis",
    ],
    "insurance": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "crop",
        "account",
        "reservation",
        "subscriber",
        "diagnosis",
    ],
    "hospitality": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "crop",
        "account",
        "policy",
        "subscriber",
        "diagnosis",
    ],
    "telecommunications": [
        "patient",
        "enrollment",
        "offering",
        "sales",
        "beneficiary",
        "machine",
        "crop",
        "account",
        "policy",
        "reservation",
        "diagnosis",
    ],
}


def _find_datasets() -> dict[str, Path]:
    base = Path(__file__).resolve().parent.parent / "dataset" / "industries"
    return {name: base / f"{name}.csv" for name in INDUSTRIES}


def _extract_text_for_contamination(result: dict, detected_entities: list[str]) -> str:
    parts = [e.lower().replace("_", " ") for e in detected_entities]
    kpis = result.get("kpis", {}).get("kpis", [])
    for kpi in kpis:
        for key in ("key", "label", "name", "category"):
            parts.append(str(kpi.get(key, "")).lower().replace("_", " "))
        parts.append(str(kpi.get("entity", "")).lower().replace("_", " "))
    dashboard = result.get("dashboard", {})
    parts.append(str(dashboard.get("title", "")).lower().replace("_", " "))
    for widget in dashboard.get("widgets", []):
        for key in ("title", "metric", "key", "entity"):
            parts.append(str(widget.get(key, "")).lower().replace("_", " "))
    return " ".join(parts)


def _validate_phase4(name: str, detected: str, result: dict, detected_entities: list[str]) -> dict:
    required = PHASE4_REQUIRED.get(name, [])
    text = _extract_text_for_contamination(result, detected_entities)
    missing = [term for term in required if term not in text]
    blocklist = CONTAMINATION_BLOCKLIST.get(name, [])
    contaminants = [term for term in blocklist if term in text]
    return {
        "industry_matches": detected == name,
        "detected_industry": detected,
        "required_terms_present": missing,
        "cross_industry_terms": contaminants,
        "passed": detected == name and not missing and not contaminants,
    }


def _run_report_export() -> dict:
    sample_report = {
        "title": "RC3 Executive Validation Report",
        "summary": "Automated validation summary across all target industries.",
        "sections": [
            {
                "heading": "Industry Detection",
                "content": "All target industries detected correctly.",
            },
            {"heading": "KPIs", "content": "Sector-specific KPIs generated."},
        ],
        "recommendations": ["Promote to production after manual UX sign-off."],
    }
    exporter = ReportExportService()
    results = {}
    for fmt in ("csv", "excel", "pdf"):
        start = time.perf_counter()
        data, _, extension = exporter.export(sample_report, fmt)
        elapsed = time.perf_counter() - start
        results[fmt] = {
            "bytes": len(data),
            "extension": extension,
            "time_seconds": round(elapsed, 3),
        }
    return results


def main() -> None:
    datasets = _find_datasets()
    industry_results: dict[str, dict] = {}
    overall_pass = True

    for name in INDUSTRIES:
        path = datasets[name]
        print(f"Validating {name} ...")
        read_start = time.perf_counter()
        df = pd.read_csv(path)
        read_time = time.perf_counter() - read_start

        detect_start = time.perf_counter()
        detected_info = SemanticIntelligenceService.detect_industry(df)
        detect_time = time.perf_counter() - detect_start

        analyze_start = time.perf_counter()
        full_result = SemanticIntelligenceService.analyze_dataset(df, table_name=name)
        analyze_time = time.perf_counter() - analyze_start

        detected = detected_info.get("industry", "unknown")
        detected_entities = detected_info.get("detected_entities", [])
        phase4 = _validate_phase4(name, detected, full_result, detected_entities)

        industry_results[name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "detected_industry": detected,
            "confidence": detected_info.get("confidence"),
            "detected_entities": detected_info.get("detected_entities", []),
            "kpi_count": len(full_result["kpis"].get("kpis", [])),
            "dashboard_title": full_result["dashboard"].get("title"),
            "phase4_validation": phase4,
            "timings": {
                "upload_read_seconds": round(read_time, 3),
                "industry_detection_seconds": round(detect_time, 3),
                "full_analysis_seconds": round(analyze_time, 3),
            },
        }
        overall_pass = overall_pass and phase4.get("passed", True)

    report_export = _run_report_export()

    report = {
        "validation": "AEDIP v1.0 RC3 Real-World Certification",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_phase4_pass": overall_pass,
        "industries": industry_results,
        "report_export": report_export,
    }

    out_path = (
        Path(__file__).resolve().parent.parent / "docs" / "AEDIP_V1.0_RC3_VALIDATION_REPORT.json"
    )
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Validation report written to {out_path}")
    print(f"Overall Phase-4 pass: {overall_pass}")


if __name__ == "__main__":
    main()
