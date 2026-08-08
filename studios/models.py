"""Models for all Data Intelligence Studios.

Studios:
  1. Data Workspace — spreadsheet-like dataset editing
  2. Data Cleaning — AI-powered cleaning with approval workflow
  3. Statistics — statistical tests and analysis records
  4. ML Lab — no-code machine learning experiments
  5. Research Studio — research projects and hypotheses
  6. Presentation Studio — generated presentations and reports
  7. Industry Intelligence — industry-specific KPI templates
  8. Visualization Engine — intelligent chart recommendations
  9. AI Mentors — conversational AI role-based assistants
  10. Collaboration — comments, shares, workspaces
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt

# ═══════════════════════════════════════════════════════════════
# Studio 1: Data Workspace
# ═══════════════════════════════════════════════════════════════


class DataWorkspace(Base):
    """A spreadsheet-like workspace for viewing and editing datasets."""

    __tablename__ = "studio_data_workspaces"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(BigInt, nullable=False)
    columns_config = Column(
        JSON, nullable=True
    )  # [{name, type, format, calculated_formula, validation_rules}]
    filters = Column(JSON, nullable=True)  # active filters
    sort_config = Column(JSON, nullable=True)  # [{column, direction}]
    conditional_formatting = Column(JSON, nullable=True)  # rules
    pivot_config = Column(JSON, nullable=True)  # pivot table settings
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class WorkspaceVersion(Base):
    """Version history for data workspace changes."""

    __tablename__ = "studio_workspace_versions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    workspace_id = Column(BigInt, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    change_description = Column(String(500), nullable=True)
    changes = Column(JSON, nullable=True)  # diff of what changed
    changed_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class CalculatedColumn(Base):
    """AI-assisted or user-defined calculated column."""

    __tablename__ = "studio_calculated_columns"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    workspace_id = Column(BigInt, nullable=False, index=True)
    column_name = Column(String(200), nullable=False)
    formula = Column(Text, nullable=False)  # e.g. "profit / revenue * 100"
    formula_type = Column(
        String(20), default="expression", nullable=False
    )  # expression, python, sql
    data_type = Column(
        String(20), default="float", nullable=False
    )  # float, int, string, date, boolean
    ai_generated = Column(Boolean, default=False, nullable=False)
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 2: Data Cleaning Engine
# ═══════════════════════════════════════════════════════════════


class CleaningJob(Base):
    """An AI-powered data cleaning job."""

    __tablename__ = "studio_cleaning_jobs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=False, index=True)
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, analyzing, awaiting_approval, applied, rejected
    issues_found = Column(JSON, nullable=True)  # list of detected issues
    transformations = Column(JSON, nullable=True)  # proposed transformations
    approved_changes = Column(JSON, nullable=True)  # user-approved subset
    summary = Column(JSON, nullable=True)  # before/after stats
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)


# ═══════════════════════════════════════════════════════════════
# Studio 3: Statistics Engine
# ═══════════════════════════════════════════════════════════════


class StatisticalAnalysis(Base):
    """Record of a statistical analysis performed."""

    __tablename__ = "studio_statistical_analyses"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=False, index=True)
    analysis_type = Column(
        String(50), nullable=False
    )  # descriptive, ttest, anova, chi_square, correlation, regression, survival, timeseries, bayesian
    test_name = Column(String(100), nullable=True)  # specific test name
    parameters = Column(JSON, nullable=True)  # input parameters
    results = Column(
        JSON, nullable=True
    )  # full results including statistics, p-values, confidence intervals
    interpretation = Column(Text, nullable=True)  # plain-language explanation
    assumptions = Column(JSON, nullable=True)  # assumptions checked
    assumptions_met = Column(Boolean, nullable=True)
    limitations = Column(Text, nullable=True)
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 4: ML Lab
# ═══════════════════════════════════════════════════════════════


class MLExperiment(Base):
    """A machine learning experiment."""

    __tablename__ = "studio_ml_experiments"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    task_type = Column(
        String(30), nullable=False
    )  # classification, regression, clustering, forecasting, anomaly_detection
    algorithm = Column(
        String(50), nullable=True
    )  # random_forest, xgboost, logistic_regression, kmeans, arima, etc.
    features = Column(JSON, nullable=True)  # selected feature columns
    target = Column(String(200), nullable=True)  # target column (supervised)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)  # accuracy, precision, recall, f1, rmse, mae, etc.
    feature_importance = Column(JSON, nullable=True)
    model_summary = Column(Text, nullable=True)  # AI-generated explanation
    status = Column(
        String(20), default="created", nullable=False
    )  # created, training, completed, failed
    is_no_code = Column(Boolean, default=True, nullable=False)
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ModelComparison(Base):
    """Comparison of multiple ML models on the same dataset."""

    __tablename__ = "studio_model_comparisons"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    task_type = Column(String(30), nullable=False)
    experiment_ids = Column(JSON, nullable=True)  # list of experiment IDs
    comparison_results = Column(JSON, nullable=True)  # ranked models with metrics
    best_model_id = Column(BigInt, nullable=True)
    recommendation = Column(Text, nullable=True)  # AI recommendation
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 5: Research Studio
# ═══════════════════════════════════════════════════════════════


class ResearchProject(Base):
    """A research project with hypotheses and analysis workflow."""

    __tablename__ = "studio_research_projects"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    research_question = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    status = Column(
        String(20), default="design", nullable=False
    )  # design, data_collection, analysis, interpretation, complete
    dataset_ids = Column(JSON, nullable=True)  # linked datasets
    industry = Column(String(100), nullable=True)
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ResearchHypothesis(Base):
    """A hypothesis within a research project."""

    __tablename__ = "studio_research_hypotheses"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    project_id = Column(BigInt, nullable=False, index=True)
    hypothesis = Column(Text, nullable=False)
    null_hypothesis = Column(Text, nullable=True)
    alternative_hypothesis = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=True)  # suggested statistical test
    significance_level = Column(Float, default=0.05, nullable=False)
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, testing, supported, rejected, inconclusive
    analysis_id = Column(BigInt, nullable=True)  # link to StatisticalAnalysis
    result_summary = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ResearchReport(Base):
    """A generated research report."""

    __tablename__ = "studio_research_reports"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    project_id = Column(BigInt, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    sections = Column(JSON, nullable=True)  # [{title, content, charts, tables}]
    methodology_text = Column(Text, nullable=True)
    references = Column(JSON, nullable=True)
    is_publication_ready = Column(Boolean, default=False, nullable=False)
    format = Column(String(20), default="markdown", nullable=False)  # markdown, pdf, html
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 6: Presentation Studio
# ═══════════════════════════════════════════════════════════════


class Presentation(Base):
    """An AI-generated presentation from analysis results."""

    __tablename__ = "studio_presentations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(30), nullable=False)  # analysis, research, dashboard, ml_experiment
    source_id = Column(BigInt, nullable=True)
    slides = Column(JSON, nullable=True)  # [{title, content, chart_url, speaker_notes, layout}]
    format = Column(String(20), default="web", nullable=False)  # web, pptx, pdf
    template = Column(
        String(50), default="executive", nullable=False
    )  # executive, analytical, research, pitch
    is_generated = Column(Boolean, default=False, nullable=False)
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 7: Industry Intelligence Engine
# ═══════════════════════════════════════════════════════════════


class IndustryTemplate(Base):
    """Industry-specific KPI and dashboard templates."""

    __tablename__ = "studio_industry_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    industry = Column(
        String(50), nullable=False, index=True
    )  # healthcare, education, banking, etc.
    template_name = Column(String(200), nullable=False)
    template_type = Column(
        String(30), nullable=False
    )  # kpi, dashboard, report, model, recommendation
    config = Column(JSON, nullable=True)  # full template configuration
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class IndustryKPI(Base):
    """Pre-defined industry KPIs."""

    __tablename__ = "studio_industry_kpis"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    industry = Column(String(50), nullable=False, index=True)
    kpi_name = Column(String(200), nullable=False)
    kpi_code = Column(String(100), nullable=False)
    formula = Column(Text, nullable=True)  # how to calculate
    unit = Column(String(20), nullable=True)  # %, $, count, ratio
    target = Column(String(100), nullable=True)  # benchmark target
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # financial, operational, customer, growth
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 8: Visualization Engine
# ═══════════════════════════════════════════════════════════════


class ChartRecommendation(Base):
    """AI-recommended chart for a dataset/query."""

    __tablename__ = "studio_chart_recommendations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    dataset_id = Column(BigInt, nullable=True, index=True)
    chart_type = Column(
        String(50), nullable=False
    )  # bar, line, scatter, heatmap, box, violin, geo, network, etc.
    chart_category = Column(
        String(30), nullable=False
    )  # business, statistical, scientific, geographic, network
    title = Column(String(300), nullable=True)
    config = Column(JSON, nullable=True)  # full chart configuration
    reasoning = Column(Text, nullable=True)  # why this chart was recommended
    data_summary = Column(JSON, nullable=True)  # summary of the data used
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 9: AI Mentors
# ═══════════════════════════════════════════════════════════════


class AIMentorSession(Base):
    """A conversation session with an AI mentor."""

    __tablename__ = "studio_ai_mentor_sessions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    user_id = Column(BigInt, nullable=False, index=True)
    mentor_type = Column(
        String(50), nullable=False
    )  # data_mentor, research_assistant, business_consultant, statistical_advisor, dashboard_designer
    title = Column(String(300), nullable=True)
    messages = Column(JSON, nullable=True)  # [{role, content, timestamp, metadata}]
    context = Column(JSON, nullable=True)  # dataset_id, analysis_id, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


# ═══════════════════════════════════════════════════════════════
# Studio 10: Collaboration
# ═══════════════════════════════════════════════════════════════


class WorkspaceComment(Base):
    """A comment on a workspace, dataset, or analysis."""

    __tablename__ = "studio_comments"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    resource_type = Column(
        String(30), nullable=False
    )  # workspace, dataset, analysis, dashboard, presentation
    resource_id = Column(BigInt, nullable=False, index=True)
    user_id = Column(BigInt, nullable=False)
    parent_id = Column(BigInt, nullable=True)  # for threaded replies
    content = Column(Text, nullable=False)
    mentions = Column(JSON, nullable=True)  # list of mentioned user IDs
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class SharedResource(Base):
    """A shared resource with permissions."""

    __tablename__ = "studio_shared_resources"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    resource_type = Column(String(30), nullable=False)  # workspace, dashboard, presentation, report
    resource_id = Column(BigInt, nullable=False, index=True)
    shared_with_user_id = Column(BigInt, nullable=True)  # specific user
    shared_with_role = Column(String(50), nullable=True)  # org-wide role
    permission = Column(String(20), default="view", nullable=False)  # view, comment, edit, admin
    shared_by = Column(BigInt, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
