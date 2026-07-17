"""Tests for the Phase 6 AI Intelligence Platform.

These tests cover:
- AI providers and provider manager
- Prompt manager
- AI memory
- AI security layer
- AI cache
- AI model router
- AI assistants registry
- AI engines (SQL, ETL, dashboard, quality, forecasting, anomaly, KPI, search)
- AI workflow engine
- AI plugin system
- AI API routes
"""

import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_ai.db"


from ai.assistants.assistants import get_assistant, list_assistants
from ai.cache import AICache
from ai.config import AI_COST_PER_1K
from ai.engines.ai_quality import AIDataQualityEngine
from ai.engines.ai_search import AISearchEngine
from ai.engines.anomaly_detection import AnomalyDetectionEngine
from ai.engines.forecasting import ForecastingEngine
from ai.engines.kpi_engine import KPIEngine
from ai.engines.nl_to_dashboard import NLToDashboardEngine
from ai.engines.nl_to_etl import NLToETLEngine
from ai.engines.nl_to_sql import NLToSQLEngine
from ai.memory import AIMemory
from ai.model_router import ModelRouter
from ai.models import (
    AIConversation,
    AIKPIRecommendation,
    AIMessage,
    AIPlugin,
)
from ai.plugins import PluginRegistry, register_system_plugins
from ai.prompts.templates import PromptManager
from ai.providers.local_provider import LocalLLMProvider
from ai.providers.manager import ProviderManager
from ai.providers.openai_provider import OpenAIProvider
from ai.security import AISecurityLayer
from ai.workflow import WorkflowEngine

# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def ai_db(db_session):
    """Reuse the conftest db_session fixture for AI tests."""
    return db_session


@pytest.fixture
def ai_client(client):
    """Authenticated test client for AI tests."""
    return client


@pytest.fixture(autouse=True)
def mock_ai_gateway_chat(monkeypatch):
    """Mock AIGateway.chat to avoid external LLM calls in unit tests."""

    def _mock_chat(self, user_message, assistant_type, **kwargs):
        # Return a generic mock response that includes valid JSON when expected
        return {
            "response": json.dumps(
                {
                    "risk_level": "low",
                    "issues_found": [],
                    "fix_suggestions": [
                        {"action": "mock", "column": "a", "description": "mock", "confidence": 0.9}
                    ],
                    "key_findings": [
                        {"finding": "Mock finding", "metric": "sales", "value": "100"}
                    ],
                    "risks": [],
                    "opportunities": [],
                    "trend_analysis": {"direction": "stable"},
                    "sql": "SELECT 1",
                    "explanation": "Mock explanation",
                    "pipeline_steps": [{"type": "extract", "config": {}}],
                    "estimated_duration": "1 minute",
                    "dashboard_config": {"title": "Mock Dashboard"},
                    "charts": [{"type": "bar", "title": "Mock Chart"}],
                    "recommendations": [
                        {
                            "name": "Mock KPI",
                            "description": "Mock",
                            "formula": "SUM(sales)",
                            "unit": "USD",
                            "category": "sales",
                            "target_value": 1000,
                            "threshold_warning": 800,
                            "threshold_critical": 500,
                            "rationale": "Mock",
                        }
                    ],
                }
            ),
            "tokens_used": 10,
            "model_used": "mock",
            "provider": "mock",
            "confidence_score": 0.9,
        }

    monkeypatch.setattr("ai.gateway.AIGateway.chat", _mock_chat)


@pytest.fixture
def mock_engine_chat(monkeypatch):
    """Mock AI engine-level chat methods."""

    def _mock_chat(self, *args, **kwargs):
        return {
            "response": "Mock engine response",
            "tokens_used": 5,
            "model_used": "mock",
            "provider": "mock",
        }

    monkeypatch.setattr("ai.gateway.AIGateway.chat", _mock_chat)


# --- Providers ---------------------------------------------------------------


class TestProviderManager:

    def test_default_provider(self, ai_db):
        manager = ProviderManager(ai_db)
        provider = manager.get_default_provider()
        assert provider is not None
        assert provider.name in ["openai", "gemini", "deepseek", "glm", "claude", "local"]

    def test_provider_list(self, ai_db):
        manager = ProviderManager(ai_db)
        providers = manager.list_providers()
        assert len(providers) >= 6
        names = [p["name"] for p in providers]
        assert "openai" in names
        assert "gemini" in names
        assert "deepseek" in names
        assert "glm" in names
        assert "claude" in names
        assert "local" in names

    def test_openai_provider_is_available(self):
        provider = OpenAIProvider(api_key="test-key")
        assert provider.is_available()

    def test_local_provider(self):
        provider = LocalLLMProvider(base_url="http://localhost:9999/v1")
        assert provider.name == "local"
        assert not provider.is_available()  # No server running in tests

    def test_cost_estimate(self):
        cost = AI_COST_PER_1K["openai"]["gpt-4o-mini"]
        assert cost > 0
        cost = AI_COST_PER_1K["local"]["default"]
        assert cost == 0.0


# --- Prompts -----------------------------------------------------------------


class TestPromptManager:

    def test_built_in_prompts(self, ai_db):
        manager = PromptManager(ai_db)
        for assistant_type in ["data_copilot", "etl_copilot", "decision_copilot", "sql_copilot"]:
            prompt = manager.get_system_prompt(assistant_type)
            assert prompt is not None
            assert len(prompt) > 0
            assert "DataFlow" in prompt or "Copilot" in prompt

    def test_list_assistants(self, ai_db):
        manager = PromptManager(ai_db)
        assistants = manager.list_assistants()
        assert len(assistants) >= 8
        types = [a["type"] for a in assistants]
        assert "decision_copilot" in types
        assert "sql_copilot" in types

    def test_custom_prompt_override(self, ai_db):
        manager = PromptManager(ai_db)
        template = manager.create_custom_prompt(
            name="custom_sql",
            assistant_type="sql_copilot",
            system_prompt="You are a strict SQL generator. Only SELECT allowed.",
        )
        prompt = manager.get_system_prompt("sql_copilot")
        assert "strict SQL generator" in prompt
        assert template.id is not None


# --- Memory ------------------------------------------------------------------


class TestAIMemory:

    def test_create_conversation_and_add_messages(self, ai_db):
        memory = AIMemory(ai_db)
        conv = AIConversation(user_id=1, assistant_type="data_copilot", title="Test")
        ai_db.add(conv)
        ai_db.commit()

        memory.add_message(conv.id, "user", "Hello")
        memory.add_message(conv.id, "assistant", "Hi there")

        history = memory.get_history(conv.id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_get_conversations(self, ai_db):
        memory = AIMemory(ai_db)
        conv = AIConversation(user_id=1, assistant_type="data_copilot", title="Test")
        ai_db.add(conv)
        ai_db.commit()

        conversations = memory.get_conversations(1)
        assert len(conversations) >= 1
        assert any(c["title"] == "Test" for c in conversations)

    def test_feedback(self, ai_db):
        memory = AIMemory(ai_db)
        conv = AIConversation(user_id=1, assistant_type="data_copilot")
        ai_db.add(conv)
        ai_db.commit()
        msg = memory.add_message(conv.id, "assistant", "Response")
        assert memory.set_feedback(msg.id, "positive") is True


# --- Security ----------------------------------------------------------------


class TestAISecurity:

    def test_validate_input(self, ai_db):
        security = AISecurityLayer(ai_db)
        assert security.validate_input("Hello") == "Hello"

    def test_validate_input_empty(self, ai_db):
        security = AISecurityLayer(ai_db)
        with pytest.raises(ValueError):
            security.validate_input("")

    def test_sql_injection_detection(self, ai_db):
        security = AISecurityLayer(ai_db)
        with pytest.raises(ValueError):
            security.validate_input("; DROP TABLE users")

    def test_permissions(self, ai_db):
        security = AISecurityLayer(ai_db)
        assert security.check_permissions("data_copilot", []) is True
        assert security.check_permissions("etl_copilot", ["etl.read"]) is True
        assert security.check_permissions("etl_copilot", ["*"]) is True

        with pytest.raises(PermissionError):
            security.check_permissions("etl_copilot", [])

    def test_redact_credit_card(self, ai_db):
        security = AISecurityLayer(ai_db)
        text = security.redact_sensitive_data("My card is 1234 5678 9012 3456")
        assert "[REDACTED-CC]" in text


# --- Cache -------------------------------------------------------------------


class TestAICache:

    def test_cache_get_set(self):
        cache = AICache(max_entries=2, ttl_seconds=3600)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("missing") is None

    def test_cache_lru_eviction(self):
        cache = AICache(max_entries=2, ttl_seconds=3600)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3


# --- Model Router ------------------------------------------------------------


class TestModelRouter:

    def test_default_route(self, ai_db):
        router = ModelRouter(ai_db)
        provider, model = router.route("sql_copilot")
        assert provider in ["openai", "gemini", "deepseek", "glm", "claude", "local"]
        assert model is not None

    def test_recommendations(self, ai_db):
        router = ModelRouter(ai_db)
        recs = router.get_recommendations("decision_copilot")
        assert len(recs) > 0
        assert "provider" in recs[0]
        assert "model" in recs[0]


# --- Assistants --------------------------------------------------------------


class TestAssistants:

    def test_list_assistants(self):
        assistants = list_assistants()
        types = [a["type"] for a in assistants]
        assert len(assistants) == 8
        assert "data_copilot" in types
        assert "decision_copilot" in types
        assert "sql_copilot" in types

    def test_get_assistant(self, ai_db):
        assistant = get_assistant("decision_copilot", ai_db)
        assert assistant.assistant_type == "decision_copilot"


# --- Plugins -----------------------------------------------------------------


class TestPlugins:

    def test_register_system_plugins(self, ai_db):
        register_system_plugins(ai_db)
        plugins = ai_db.query(AIPlugin).filter(AIPlugin.is_system.is_(True)).all()
        assert len(plugins) >= 6

    def test_activate_deactivate_plugin(self, ai_db):
        register_system_plugins(ai_db)
        registry = PluginRegistry(ai_db)
        plugin = ai_db.query(AIPlugin).filter(AIPlugin.is_system.is_(True)).first()
        assert registry.activate_plugin(plugin.id) is True
        assert plugin.is_active is True
        assert registry.deactivate_plugin(plugin.id) is True
        assert plugin.is_active is False


# --- NL to SQL ---------------------------------------------------------------


class TestNLToSQL:

    def test_validate_safe_sql(self, ai_db):
        engine = NLToSQLEngine(ai_db)
        is_safe, warnings = engine._validate_sql("SELECT * FROM sales LIMIT 10")
        assert is_safe is True

    def test_validate_unsafe_sql(self, ai_db):
        engine = NLToSQLEngine(ai_db)
        is_safe, warnings = engine._validate_sql("DROP TABLE sales")
        assert is_safe is False
        assert any("DROP" in w for w in warnings)

    def test_validate_insert_blocked(self, ai_db):
        engine = NLToSQLEngine(ai_db)
        is_safe, warnings = engine._validate_sql("INSERT INTO sales VALUES (1,2,3)")
        assert is_safe is False

    def test_extract_sql(self, ai_db):
        engine = NLToSQLEngine(ai_db)
        sql, explanation = engine._extract_sql(
            "```sql\nSELECT sales FROM orders\n```\nThis query returns sales."
        )
        assert "SELECT" in sql
        assert "sales" in sql


# --- NL to ETL ---------------------------------------------------------------


class TestNLToETL:

    def test_extract_pipeline(self, ai_db):
        engine = NLToETLEngine(ai_db)
        response = (
            '{"pipeline_steps": [{"type": "extract", "config": {"source": "csv"}}, '
            '{"type": "load", "config": {"mode": "upsert"}}], '
            '"explanation": "Import and upsert", "estimated_duration": "1 minute"}'
        )
        steps, explanation, duration = engine._extract_pipeline(response)
        assert len(steps) == 2
        assert explanation == "Import and upsert"
        assert duration == "1 minute"


# --- NL to Dashboard ---------------------------------------------------------


class TestNLToDashboard:

    def test_extract_dashboard(self, ai_db):
        engine = NLToDashboardEngine(ai_db)
        response = (
            '{"dashboard_config": {"title": "Sales Dashboard", "layout": "grid"}, '
            '"charts": [{"type": "bar", "title": "Sales by Region"}], '
            '"explanation": "Dashboard for sales"}'
        )
        config, charts, explanation = engine._extract_dashboard(response)
        assert config["title"] == "Sales Dashboard"
        assert len(charts) == 1


# --- AI Quality --------------------------------------------------------------


class TestAIQuality:

    def test_quality_on_clean_csv(self, ai_db, tmp_path):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "clean.csv"
        df.to_csv(path, index=False)

        engine = AIDataQualityEngine(ai_db)
        result = engine.analyze(
            "csv", {"file_path": str(path)}, user_id=1, permissions=["etl.read"]
        )
        assert "quality_score" in result
        assert 0 <= result["quality_score"] <= 100
        assert "risk_level" in result


# --- KPI Engine --------------------------------------------------------------


class TestKPIEngine:

    def test_recommend_kpis(self, ai_db):
        engine = KPIEngine(ai_db)
        result = engine.recommend_kpis(domain="sales")
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        # Verify saved to DB
        assert ai_db.query(AIKPIRecommendation).count() > 0


# --- AI Search ---------------------------------------------------------------


class TestAISearch:

    def test_infer_search_type(self, ai_db):
        engine = AISearchEngine(ai_db)
        assert engine._infer_search_type("Show ETL jobs") == "jobs"
        assert engine._infer_search_type("Show forecasts") == "forecasts"
        assert engine._infer_search_type("Show all") == "all"

    def test_search_data(self, ai_db):
        # Add a sample sales record so search_data has something to return
        from datetime import date

        from database.db_setup import SalesRecord

        record = SalesRecord(
            order_id="ORD-001",
            order_date=date(2024, 1, 1),
            region="East",
            category="Technology",
            sales=100.0,
            quantity=1,
            discount=0,
            profit=20.0,
        )
        ai_db.add(record)
        ai_db.commit()

        engine = AISearchEngine(ai_db)
        result = engine.search("sales by region")
        assert "results" in result
        assert result["total"] >= 1


# --- Forecasting -------------------------------------------------------------


class TestForecasting:

    def test_linear_forecast(self, ai_db, tmp_path):
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"order_date": dates, "sales": range(10)})
        path = tmp_path / "forecast.csv"
        df.to_csv(path, index=False)

        engine = ForecastingEngine(ai_db)
        result = engine.forecast(
            source_type="csv",
            source_config={"file_path": str(path)},
            target_column="sales",
            date_column="order_date",
            horizon=5,
            method="linear",
        )
        assert "predictions" in result
        assert len(result["predictions"]) == 5
        assert "accuracy_score" in result


# --- Anomaly Detection -------------------------------------------------------


class TestAnomalyDetection:

    def test_detect_no_anomalies(self, ai_db, tmp_path):
        dates = pd.date_range("2024-01-01", periods=15, freq="D")
        df = pd.DataFrame({"order_date": dates, "sales": [100] * 15})
        path = tmp_path / "anomaly.csv"
        df.to_csv(path, index=False)

        engine = AnomalyDetectionEngine(ai_db)
        result = engine.detect(
            source_type="csv",
            source_config={"file_path": str(path)},
            metric_column="sales",
            date_column="order_date",
            sensitivity=3.0,
        )
        assert result["total_anomalies"] == 0

    def test_detect_spike(self, ai_db, tmp_path):
        dates = pd.date_range("2024-01-01", periods=15, freq="D")
        values = [100] * 14 + [1000]
        df = pd.DataFrame({"order_date": dates, "sales": values})
        path = tmp_path / "spike.csv"
        df.to_csv(path, index=False)

        engine = AnomalyDetectionEngine(ai_db)
        result = engine.detect(
            source_type="csv",
            source_config={"file_path": str(path)},
            metric_column="sales",
            date_column="order_date",
            sensitivity=2.0,
        )
        assert result["total_anomalies"] >= 1


# --- Workflow ----------------------------------------------------------------


class TestWorkflow:

    def test_create_workflow(self, ai_db):
        engine = WorkflowEngine(ai_db)
        result = engine.create_workflow(
            name="Test Workflow",
            steps=[
                {"type": "notify", "config": {"message": "Started"}},
                {"type": "notify", "config": {"message": "Done"}},
            ],
            user_id=1,
        )
        assert result["id"] is not None
        assert len(result["steps"]) == 2

    def test_execute_workflow(self, ai_db):
        engine = WorkflowEngine(ai_db)
        wf = engine.create_workflow(
            name="Execute Test",
            steps=[
                {"type": "notify", "config": {"message": "Step 1"}},
                {"type": "archive", "config": {}},
            ],
            user_id=1,
        )
        run = engine.execute_workflow(wf["id"], user_id=1)
        assert run["status"] == "completed"
        assert len(run["step_results"]) == 2

    def test_workflow_not_found(self, ai_db):
        engine = WorkflowEngine(ai_db)
        result = engine.execute_workflow(99999, user_id=1)
        assert "error" in result


# --- API Routes --------------------------------------------------------------


class TestAIAPI:

    def test_list_assistants(self, ai_client, auth_headers):
        response = ai_client.get("/ai/assistants", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 8

    def test_list_providers(self, ai_client, auth_headers):
        response = ai_client.get("/ai/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 6

    def test_create_provider(self, ai_client, auth_headers):
        payload = {
            "provider_name": "test_provider",
            "display_name": "Test Provider",
            "api_key": "test-key",
            "default_model": "gpt-4o-mini",
            "available_models": ["gpt-4o-mini"],
            "is_active": True,
        }
        response = ai_client.post("/ai/providers", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "test_provider"
        assert data["has_api_key"] is True

    def test_create_duplicate_provider(self, ai_client, auth_headers):
        payload = {
            "provider_name": "duplicate_provider",
            "display_name": "Duplicate Provider",
            "is_active": True,
        }
        ai_client.post("/ai/providers", json=payload, headers=auth_headers)
        response = ai_client.post("/ai/providers", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_prompt_templates_list(self, ai_client, auth_headers):
        response = ai_client.get("/ai/prompts", headers=auth_headers)
        assert response.status_code == 200

    def test_create_prompt_template(self, ai_client, auth_headers):
        payload = {
            "name": "test_prompt",
            "assistant_type": "sql_copilot",
            "system_prompt": "You are a strict SQL generator.",
            "description": "Test prompt",
        }
        response = ai_client.post("/ai/prompts", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_prompt"

    def test_dashboard(self, ai_client, auth_headers):
        response = ai_client.get("/ai/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "provider_status" in data

    def test_usage_stats(self, ai_client, auth_headers):
        response = ai_client.get("/ai/usage/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data

    def test_audit_logs(self, ai_client, auth_headers):
        response = ai_client.get("/ai/audit/logs", headers=auth_headers)
        assert response.status_code == 200

    def test_sql_generate_unauthorized_without_auth(self, ai_client):
        response = ai_client.post("/ai/sql/generate", json={"question": "What is revenue?"})
        assert response.status_code == 401

    def test_workflow_create_and_execute(self, ai_client, auth_headers):
        payload = {
            "name": "API Test Workflow",
            "description": "Test workflow via API",
            "trigger_type": "manual",
            "steps": [
                {"type": "notify", "config": {"message": "API step"}},
            ],
        }
        response = ai_client.post("/ai/workflows", json=payload, headers=auth_headers)
        assert response.status_code == 200
        workflow_id = response.json()["id"]

        response = ai_client.post(f"/ai/workflows/{workflow_id}/execute", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_kpi_recommend(self, ai_client, auth_headers):
        response = ai_client.post(
            "/ai/kpi/recommend", json={"domain": "sales"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_kpi_monitor(self, ai_client, auth_headers):
        response = ai_client.get("/ai/kpi/monitor", headers=auth_headers)
        assert response.status_code == 200

    def test_document_upload_csv(self, ai_client, auth_headers, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("a,b,c\n1,2,3\n4,5,6")
        with open(csv_path, "rb") as f:
            response = ai_client.post(
                "/ai/documents/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.csv"
        assert data["is_indexed"] is True

        # Chat with document
        doc_id = data["document_id"]
        response = ai_client.post(
            f"/ai/documents/{doc_id}/chat",
            json={"document_id": doc_id, "question": "What are the columns?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "answer" in response.json()

    def test_ai_search(self, ai_client, auth_headers):
        response = ai_client.post(
            "/ai/search",
            json={"query": "sales", "search_type": "data"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


# --- Integration: Database models -------------------------------------------


class TestAIModels:

    def test_models_create(self, ai_db):
        conv = AIConversation(user_id=1, assistant_type="data_copilot", title="Test")
        ai_db.add(conv)
        ai_db.commit()
        assert conv.id is not None

        msg = AIMessage(conversation_id=conv.id, role="user", content="Hello")
        ai_db.add(msg)
        ai_db.commit()
        assert msg.id is not None
