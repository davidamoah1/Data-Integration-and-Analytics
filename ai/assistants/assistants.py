"""AI Assistants — specialized AI personalities with distinct capabilities.

Each assistant has:
- A unique system prompt (managed by PromptManager)
- Specific tools and capabilities
- Permission requirements
- Context requirements

All assistants are routed through the AIGateway which handles
provider selection, memory, caching, security, and audit logging.
"""

from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.security import ASSISTANT_PERMISSIONS


class BaseAssistant:
    """Base class for all AI assistants."""

    assistant_type: str = "data_copilot"
    display_name: str = "Data Copilot"
    description: str = "General data assistant"

    def __init__(self, db: DbSession):
        self.gateway = AIGateway(db)
        self.db = db

    def chat(self, message: str, user_id: Optional[int] = None,
             conversation_id: Optional[int] = None,
             context: Optional[dict] = None,
             permissions: Optional[list[str]] = None,
             stream: bool = False) -> dict:
        """Send a message to this assistant."""
        return self.gateway.chat(
            user_message=message,
            assistant_type=self.assistant_type,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context,
            stream=stream,
            permissions=permissions,
        )

    @classmethod
    def info(cls) -> dict:
        """Return assistant metadata."""
        return {
            "type": cls.assistant_type,
            "display_name": cls.display_name,
            "description": cls.description,
            "required_permissions": ASSISTANT_PERMISSIONS.get(cls.assistant_type, []),
        }


class DataCopilot(BaseAssistant):
    """General data assistant — understands datasets, KPIs, and platform data."""
    assistant_type = "data_copilot"
    display_name = "Data Copilot"
    description = "Understands datasets, reports, charts, dashboards, KPIs, and platform data"


class ETLCopilot(BaseAssistant):
    """ETL assistant — builds pipelines from natural language."""
    assistant_type = "etl_copilot"
    display_name = "ETL Copilot"
    description = "Builds and troubleshoots ETL pipelines from natural language instructions"


class DashboardCopilot(BaseAssistant):
    """Dashboard assistant — generates dashboards from descriptions."""
    assistant_type = "dashboard_copilot"
    display_name = "Dashboard Copilot"
    description = "Creates dashboards and generates appropriate visualizations"


class ReportCopilot(BaseAssistant):
    """Report assistant — generates professional reports."""
    assistant_type = "report_copilot"
    display_name = "Report Copilot"
    description = "Generates executive summaries, monthly reports, and department reports"


class DecisionCopilot(BaseAssistant):
    """Decision assistant — the flagship decision intelligence feature."""
    assistant_type = "decision_copilot"
    display_name = "Decision Copilot"
    description = "Explains what happened, why, what may happen next, and recommends actions"


class ForecastCopilot(BaseAssistant):
    """Forecast assistant — helps with forecasting and trend analysis."""
    assistant_type = "forecast_copilot"
    display_name = "Forecast Copilot"
    description = "Supports forecasting for revenue, attendance, enrollment, demand, and more"


class QualityCopilot(BaseAssistant):
    """Data quality assistant — analyzes and improves data quality."""
    assistant_type = "quality_copilot"
    display_name = "Data Quality Copilot"
    description = "Detects duplicates, outliers, missing values, and recommends fixes"


class SQLCopilot(BaseAssistant):
    """SQL assistant — translates natural language to safe SQL."""
    assistant_type = "sql_copilot"
    display_name = "SQL Copilot"
    description = "Translates natural language questions into validated SQL queries"


# --- Registry ---------------------------------------------------------------

ASSISTANTS: dict[str, type[BaseAssistant]] = {
    "data_copilot": DataCopilot,
    "etl_copilot": ETLCopilot,
    "dashboard_copilot": DashboardCopilot,
    "report_copilot": ReportCopilot,
    "decision_copilot": DecisionCopilot,
    "forecast_copilot": ForecastCopilot,
    "quality_copilot": QualityCopilot,
    "sql_copilot": SQLCopilot,
}


def get_assistant(assistant_type: str, db: DbSession) -> BaseAssistant:
    """Get an assistant instance by type."""
    cls = ASSISTANTS.get(assistant_type, DataCopilot)
    return cls(db)


def list_assistants() -> list[dict]:
    """List all available assistants."""
    return [cls.info() for cls in ASSISTANTS.values()]
