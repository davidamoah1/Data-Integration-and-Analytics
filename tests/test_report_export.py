"""Unit tests for the report export service."""

import pytest

from services.report_export_service import SUPPORTED_FORMATS, ReportExportService


class _DummyReport:
    title = "Executive Summary"
    report_type = "executive"
    content = "## Summary\nGood results."
    summary = "Good results."
    sections = ["Summary", "Details"]
    data_sources = {
        "sales_by_region": [
            {"region": "North", "sales": 1000.0},
            {"region": "South", "sales": 2000.0},
        ]
    }
    created_at = "2026-07-23"


@pytest.fixture
def dummy_report():
    return _DummyReport()


def test_supported_formats():
    assert "csv" in SUPPORTED_FORMATS
    assert "excel" in SUPPORTED_FORMATS
    assert "pdf" in SUPPORTED_FORMATS


def test_export_csv(dummy_report):
    service = ReportExportService()
    data, media_type, ext = service.export(dummy_report, "csv")
    assert isinstance(data, bytes)
    assert media_type == "text/csv; charset=utf-8"
    assert ext == "csv"
    assert b"North" in data


def test_export_excel(dummy_report):
    service = ReportExportService()
    data, media_type, ext = service.export(dummy_report, "excel")
    assert isinstance(data, bytes)
    assert media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert ext == "xlsx"
    assert data[:4] == b"PK\x03\x04"


def test_export_pdf(dummy_report):
    service = ReportExportService()
    data, media_type, ext = service.export(dummy_report, "pdf")
    assert isinstance(data, bytes)
    assert media_type == "application/pdf"
    assert ext == "pdf"
    assert data[:4] == b"%PDF"


def test_export_xlsx_alias(dummy_report):
    service = ReportExportService()
    data, media_type, ext = service.export(dummy_report, "xlsx")
    assert ext == "xlsx"


def test_export_unsupported_format(dummy_report):
    service = ReportExportService()
    with pytest.raises(ValueError):
        service.export(dummy_report, "doc")
