"""
DataFlow Python SDK — Client library for the DataFlow Enterprise Data Intelligence Platform.

Installation:
    pip install dataflow-sdk

Usage:
    from dataflow import DataFlowClient

    client = DataFlowClient(api_key="dfk_...", base_url="http://localhost:8080")

    # Upload a dataset
    result = client.datasets.upload("data.csv")

    # List dashboards
    dashboards = client.analytics.list_dashboards()

    # Ask AI
    answer = client.ai.ask("What are the top trends in my data?")
"""

from __future__ import annotations

import os
from typing import Any

import requests


class DataFlowClient:
    """Main SDK client for the DataFlow platform."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("DATAFLOW_API_KEY", "")
        self.base_url = (
            base_url or os.getenv("DATAFLOW_BASE_URL", "http://localhost:8080")
        ).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }
        )
        self.datasets = DatasetsAPI(self)
        self.analytics = AnalyticsAPI(self)
        self.ai = AIAPI(self)
        self.workflows = WorkflowsAPI(self)
        self.reports = ReportsAPI(self)

    def _get(self, path: str, **kwargs) -> Any:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict | None = None, **kwargs) -> Any:
        if data is not None:
            kwargs["json"] = data
        resp = self.session.post(f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _upload(self, path: str, file_path: str) -> Any:
        with open(file_path, "rb") as f:
            resp = self.session.post(
                f"{self.base_url}{path}", files={"file": f}, headers={"X-API-Key": self.api_key}
            )
        resp.raise_for_status()
        return resp.json()


class DatasetsAPI:
    def __init__(self, client: DataFlowClient):
        self.client = client

    def upload(self, file_path: str) -> dict:
        """Upload a CSV or Excel file."""
        return self.client._upload("/public/datasets/upload", file_path)

    def list(self) -> list[dict]:
        """List all datasets."""
        return self.client._get("/public/datasets").get("data", [])


class AnalyticsAPI:
    def __init__(self, client: DataFlowClient):
        self.client = client

    def list_dashboards(self) -> list[dict]:
        """List all dashboards."""
        return self.client._get("/public/analytics/dashboards").get("data", [])

    def list_kpis(self) -> list[dict]:
        """List all KPIs."""
        return self.client._get("/public/analytics/kpis").get("data", [])


class AIAPI:
    def __init__(self, client: DataFlowClient):
        self.client = client

    def ask(self, question: str) -> dict:
        """Ask the AI Copilot a question."""
        return self.client._post("/public/ai/ask", {"question": question}).get("data", {})


class WorkflowsAPI:
    def __init__(self, client: DataFlowClient):
        self.client = client

    def list(self) -> list[dict]:
        """List all workflows."""
        return self.client._get("/public/workflows").get("data", [])


class ReportsAPI:
    def __init__(self, client: DataFlowClient):
        self.client = client

    def list(self) -> list[dict]:
        """List all reports."""
        return self.client._get("/public/reports").get("data", [])
