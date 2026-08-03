"""Smart Onboarding Service — Phase 7.

Provides role-specific guided onboarding flows with step tracking.

Flows:
  - org_admin / org_owner: Create Org → Invite Members → Create Departments → Upload Data → Create Dashboard
  - data_analyst: Upload Dataset → Validate → Analyze → Generate Report
  - viewer: View Dashboard → Explore Reports

New users get a blank workspace — NO demo datasets are auto-loaded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ── Role-Specific Onboarding Flow Definitions ─────────


@dataclass(frozen=True)
class OnboardingStepDef:
    key: str
    title: str
    description: str
    href: str
    icon: str  # lucide icon name
    optional: bool = False
    action_label: str = ""


@dataclass(frozen=True)
class OnboardingFlowDef:
    role: str
    title: str
    description: str
    steps: tuple[OnboardingStepDef, ...]


# Org Admin / Org Owner flow
ADMIN_FLOW = OnboardingFlowDef(
    role="org_admin",
    title="Organization Setup",
    description="Set up your organization step by step",
    steps=(
        OnboardingStepDef(
            key="create_org",
            title="Create Organization",
            description="Your organization is your team's workspace. Set up your org profile with branding and settings.",
            href="/settings",
            icon="Building2",
            action_label="Configure Organization",
        ),
        OnboardingStepDef(
            key="invite_members",
            title="Invite Team Members",
            description="Bring your team on board. Send invitations to colleagues so they can join your workspace.",
            href="/admin",
            icon="Users",
            action_label="Invite Members",
        ),
        OnboardingStepDef(
            key="create_departments",
            title="Create Departments",
            description="Organize your team into departments for better structure and access control.",
            href="/admin/departments",
            icon="LayoutGrid",
            action_label="Create Departments",
        ),
        OnboardingStepDef(
            key="upload_data",
            title="Upload Data",
            description="Import your first dataset. Upload a CSV, Excel, or JSON file to get started.",
            href="/datasets",
            icon="Upload",
            action_label="Upload Dataset",
        ),
        OnboardingStepDef(
            key="create_dashboard",
            title="Create Dashboard",
            description="Build your first dashboard using the Dashboard Builder. Compose widgets adapted to your industry.",
            href="/dashboard/builder",
            icon="LayoutDashboard",
            action_label="Build Dashboard",
        ),
    ),
)

# Analyst flow
ANALYST_FLOW = OnboardingFlowDef(
    role="data_analyst",
    title="Analyst Quick Start",
    description="Get from raw data to insights in 4 steps",
    steps=(
        OnboardingStepDef(
            key="upload_dataset",
            title="Upload Dataset",
            description="Start by uploading a CSV, Excel, or JSON file. This is your raw data for analysis.",
            href="/datasets",
            icon="Upload",
            action_label="Upload Dataset",
        ),
        OnboardingStepDef(
            key="validate",
            title="Validate Data Quality",
            description="Run automatic data validation to check for missing values, duplicates, and quality issues.",
            href="/datasets/workflow",
            icon="CheckCircle2",
            action_label="Validate Data",
        ),
        OnboardingStepDef(
            key="analyze",
            title="Analyze Your Data",
            description="Explore your data with analytics. Create charts, KPIs, and visualizations.",
            href="/analytics",
            icon="BarChart3",
            action_label="Open Analytics",
        ),
        OnboardingStepDef(
            key="generate_report",
            title="Generate Report",
            description="Create a professional report from your analysis to share with stakeholders.",
            href="/reports",
            icon="FileText",
            action_label="Generate Report",
        ),
    ),
)

# Viewer flow
VIEWER_FLOW = OnboardingFlowDef(
    role="viewer",
    title="Welcome to Your Workspace",
    description="Explore dashboards and reports shared with you",
    steps=(
        OnboardingStepDef(
            key="view_dashboard",
            title="View Dashboards",
            description="Explore dashboards built by your team. See KPIs, charts, and key metrics at a glance.",
            href="/dashboard",
            icon="LayoutDashboard",
            action_label="Open Dashboards",
        ),
        OnboardingStepDef(
            key="explore_reports",
            title="Explore Reports",
            description="Browse reports generated by your team. Download or share them as needed.",
            href="/reports",
            icon="FileText",
            action_label="Browse Reports",
        ),
    ),
)

# Researcher flow
RESEARCHER_FLOW = OnboardingFlowDef(
    role="researcher",
    title="Research Workspace Setup",
    description="Import surveys and start your statistical analysis",
    steps=(
        OnboardingStepDef(
            key="import_survey",
            title="Import Survey Data",
            description="Upload your survey data (CSV, Excel, or JSON) to begin analysis.",
            href="/datasets",
            icon="Upload",
            action_label="Import Survey",
        ),
        OnboardingStepDef(
            key="statistical_analysis",
            title="Run Statistical Analysis",
            description="Perform descriptive and inferential statistics on your data.",
            href="/studios/statistics",
            icon="FlaskConical",
            action_label="Open Statistics Studio",
        ),
        OnboardingStepDef(
            key="generate_publication",
            title="Generate Publication Report",
            description="Create a publication-ready report from your analysis.",
            href="/studios/publications",
            icon="Newspaper",
            action_label="Create Publication",
        ),
    ),
)

# Data Entry Officer flow
DATA_ENTRY_FLOW = OnboardingFlowDef(
    role="data_entry_officer",
    title="Data Capture Setup",
    description="Start capturing data from documents",
    steps=(
        OnboardingStepDef(
            key="capture_document",
            title="Capture Your First Document",
            description="Upload a paper document and let Smart Data Capture extract the data using OCR.",
            href="/capture",
            icon="ScanLine",
            action_label="Open Smart Capture",
        ),
        OnboardingStepDef(
            key="review_extracted",
            title="Review Extracted Data",
            description="Check confidence scores and correct any extraction errors.",
            href="/capture/queue",
            icon="CheckSquare",
            action_label="Review Queue",
        ),
        OnboardingStepDef(
            key="submit_data",
            title="Submit Verified Data",
            description="Save the captured and verified data as a dataset for analysis.",
            href="/datasets",
            icon="Database",
            action_label="Submit Data",
        ),
    ),
)

# Super Admin flow
SUPER_ADMIN_FLOW = OnboardingFlowDef(
    role="super_admin",
    title="Platform Administration",
    description="Configure the platform for all organizations",
    steps=(
        OnboardingStepDef(
            key="review_orgs",
            title="Review Organizations",
            description="View and manage all organizations on the platform.",
            href="/admin-portal",
            icon="Building2",
            action_label="Open Admin Portal",
        ),
        OnboardingStepDef(
            key="manage_subscriptions",
            title="Manage Subscriptions",
            description="Review and configure subscription plans for organizations.",
            href="/admin-portal/subscriptions",
            icon="CreditCard",
            action_label="Manage Subscriptions",
        ),
        OnboardingStepDef(
            key="review_organizations",
            title="Review All Organizations",
            description="Check organization health, usage, and compliance.",
            href="/admin-portal/organizations",
            icon="Globe2",
            action_label="Review Organizations",
        ),
    ),
)


# Flow registry
FLOWS: dict[str, OnboardingFlowDef] = {
    "org_admin": ADMIN_FLOW,
    "org_owner": ADMIN_FLOW,
    "data_analyst": ANALYST_FLOW,
    "business_analyst": ANALYST_FLOW,
    "viewer": VIEWER_FLOW,
    "executive": VIEWER_FLOW,
    "dept_officer": VIEWER_FLOW,
    "researcher": RESEARCHER_FLOW,
    "data_entry_officer": DATA_ENTRY_FLOW,
    "super_admin": SUPER_ADMIN_FLOW,
    "dept_manager": ADMIN_FLOW,
    "data_engineer": ANALYST_FLOW,
    "auditor": SUPER_ADMIN_FLOW,
}


def get_flow_for_role(role: str) -> OnboardingFlowDef:
    return FLOWS.get(role, VIEWER_FLOW)


def get_flow_for_roles(roles: list[str]) -> OnboardingFlowDef:
    """Get the onboarding flow for the user's primary role.

    Priority: super_admin > org_owner > org_admin > data_analyst > researcher
    > data_entry_officer > viewer > first role > viewer default.
    """
    priority = [
        "super_admin", "org_owner", "org_admin", "dept_manager",
        "data_analyst", "business_analyst", "data_engineer",
        "researcher", "data_entry_officer", "auditor",
        "executive", "dept_officer", "viewer",
    ]
    for role in priority:
        if role in roles:
            return get_flow_for_role(role)
    if roles:
        return get_flow_for_role(roles[0])
    return get_flow_for_role("viewer")


def flow_to_dict(flow: OnboardingFlowDef) -> dict[str, Any]:
    return {
        "role": flow.role,
        "title": flow.title,
        "description": flow.description,
        "steps": [
            {
                "key": s.key,
                "title": s.title,
                "description": s.description,
                "href": s.href,
                "icon": s.icon,
                "optional": s.optional,
                "action_label": s.action_label,
            }
            for s in flow.steps
        ],
    }


# ── Onboarding Progress Tracker ───────────────────────


class OnboardingService:
    """Tracks onboarding progress per user.

    Uses the user.onboarding_data JSON field to store step completion.
    No demo datasets are loaded — users start with a blank workspace.
    """

    def get_status(self, user: Any) -> dict[str, Any]:
        """Get onboarding status for a user."""
        flow = get_flow_for_roles(user.get("roles", []))
        onboarding_data = user.get("onboarding_data") or {}
        completed_steps = onboarding_data.get("completed_steps", [])
        skipped = onboarding_data.get("skipped", False)
        current_step_idx = onboarding_data.get("current_step", 0)

        total = len(flow.steps)
        completed = len([s for s in completed_steps if s in [step.key for step in flow.steps]])
        percentage = int((completed / total) * 100) if total > 0 else 0

        is_complete = completed == total or skipped

        return {
            "flow": flow_to_dict(flow),
            "completed_steps": completed_steps,
            "current_step_index": current_step_idx,
            "current_step": flow.steps[current_step_idx].key if current_step_idx < total else None,
            "total_steps": total,
            "completed_count": completed,
            "percentage": percentage,
            "is_complete": is_complete,
            "skipped": skipped,
        }

    def complete_step(self, user: Any, step_key: str) -> dict[str, Any]:
        """Mark a step as completed."""
        flow = get_flow_for_roles(user.get("roles", []))
        valid_keys = [s.key for s in flow.steps]

        if step_key not in valid_keys:
            raise ValueError(f"Invalid step key: {step_key}. Valid steps: {valid_keys}")

        onboarding_data = dict(user.get("onboarding_data") or {})
        completed_steps = list(set(onboarding_data.get("completed_steps", []) + [step_key]))
        onboarding_data["completed_steps"] = completed_steps

        # Advance current step
        step_idx = valid_keys.index(step_key)
        next_idx = min(step_idx + 1, len(valid_keys) - 1)
        onboarding_data["current_step"] = next_idx

        # Check if all steps are done
        all_done = all(k in completed_steps for k in valid_keys)
        if all_done:
            onboarding_data["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()

        return onboarding_data

    def skip_onboarding(self, user: Any) -> dict[str, Any]:
        """Skip onboarding entirely."""
        onboarding_data = dict(user.get("onboarding_data") or {})
        onboarding_data["skipped"] = True
        onboarding_data["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()
        return onboarding_data

    def reset_onboarding(self, user: Any) -> dict[str, Any]:
        """Reset onboarding progress."""
        onboarding_data = dict(user.get("onboarding_data") or {})
        onboarding_data.pop("completed_steps", None)
        onboarding_data.pop("current_step", None)
        onboarding_data.pop("skipped", None)
        onboarding_data.pop("onboarding_completed_at", None)
        onboarding_data["completed_steps"] = []
        onboarding_data["current_step"] = 0
        return onboarding_data

    def get_next_action(self, user: Any) -> dict[str, Any] | None:
        """Get the next recommended action for the user."""
        status = self.get_status(user)
        if status["is_complete"]:
            return None

        flow = get_flow_for_roles(user.get("roles", []))
        completed = set(status["completed_steps"])

        for step in flow.steps:
            if step.key not in completed:
                return {
                    "step_key": step.key,
                    "title": step.title,
                    "description": step.description,
                    "href": step.href,
                    "icon": step.icon,
                    "action_label": step.action_label,
                }
        return None
