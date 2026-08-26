"""Industry-adaptive widget catalog for the Dashboard Composition Engine.

Pre-built widget definitions organized by industry:
  - Healthcare: patient statistics, admission trends, laboratory reports
  - Education: student performance, enrollment trends
  - Business: sales, inventory, revenue
  - Research: survey analysis, statistical outputs
"""

from __future__ import annotations

import logging

from services.dashboard_composition import (
    ChartSubType,
    DataSourceBinding,
    DataSourceType,
    WidgetDefinition,
    WidgetRegistry,
    WidgetType,
)

logger = logging.getLogger(__name__)


# â”€â”€ Helper functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _kpi(
    key: str, title: str, entity: str, industry: str, group: str = "Overview", order: int = 0, **kw
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.KPI_CARD,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.AGGREGATE,
            source_id=entity,
            aggregation=kw.get("aggregation", "count"),
        ),
        config={"unit": kw.get("unit", ""), "icon": kw.get("icon", "Activity")},
    )


def _chart(
    key: str,
    title: str,
    subtype: ChartSubType,
    entity: str,
    industry: str,
    group: str = "Charts",
    order: int = 0,
    **kw,
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.CHART,
        title=title,
        chart_subtype=subtype,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.DATASET,
            source_id=entity,
            aggregation=kw.get("aggregation", "sum"),
            group_by=kw.get("group_by"),
            time_field=kw.get("time_field"),
        ),
        config={"x_axis": kw.get("x_axis"), "y_axis": kw.get("y_axis")},
    )


def _table(
    key: str, title: str, entity: str, industry: str, group: str = "Details", order: int = 0, **kw
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.TABLE,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.DATASET,
            source_id=entity,
            limit=kw.get("limit", 10),
        ),
        config={"columns": kw.get("columns", [])},
    )


def _trend(
    key: str, title: str, entity: str, industry: str, group: str = "Trends", order: int = 0, **kw
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.TREND,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.DATASET,
            source_id=entity,
            time_field=kw.get("time_field", "date"),
            aggregation=kw.get("aggregation", "sum"),
        ),
        config={
            "trend_field": kw.get("trend_field"),
            "compare_to": kw.get("compare_to", "previous_period"),
        },
    )


def _alert(
    key: str, title: str, entity: str, industry: str, group: str = "Alerts", order: int = 0, **kw
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.ALERT,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.ANALYTICS_ALERT,
            source_id=entity,
        ),
        config={"severity": kw.get("severity", "warning")},
    )


def _report(
    key: str,
    title: str,
    report_type: str,
    industry: str,
    group: str = "Reports",
    order: int = 0,
    **kw,
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.REPORT,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.REPORT,
            source_id=report_type,
        ),
        config={"template": kw.get("template", "standard")},
    )


def _map(
    key: str, title: str, entity: str, industry: str, group: str = "Maps", order: int = 0, **kw
) -> WidgetDefinition:
    return WidgetDefinition(
        key=key,
        widget_type=WidgetType.MAP,
        title=title,
        industries=[industry],
        group=group,
        order=order,
        data_source=DataSourceBinding(
            source_type=DataSourceType.DATASET,
            source_id=entity,
            aggregation=kw.get("aggregation", "count"),
        ),
        config={"geo_field": kw.get("geo_field", "region"), "value_field": kw.get("value_field")},
    )


# â”€â”€ Healthcare Widgets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HEALTHCARE_WIDGETS = [
    _kpi(
        "hc_patients",
        "Total Patients",
        "patient",
        "healthcare",
        "Patient Statistics",
        0,
        icon="Users",
    ),
    _kpi(
        "hc_admissions",
        "Admissions",
        "admission",
        "healthcare",
        "Patient Statistics",
        1,
        icon="ClipboardList",
    ),
    _kpi(
        "hc_discharges",
        "Discharges",
        "admission",
        "healthcare",
        "Patient Statistics",
        2,
        icon="CheckCircle2",
    ),
    _kpi(
        "hc_emergency",
        "Emergency Visits",
        "appointment",
        "healthcare",
        "Patient Statistics",
        3,
        icon="AlertCircle",
    ),
    _kpi(
        "hc_bed_occupancy",
        "Bed Occupancy",
        "ward",
        "healthcare",
        "Patient Statistics",
        4,
        icon="BedDouble",
        aggregation="sum",
    ),
    _kpi(
        "hc_readmissions",
        "Readmission Rate",
        "admission",
        "healthcare",
        "Patient Statistics",
        5,
        icon="RotateCcw",
    ),
    _trend(
        "hc_admission_trend",
        "Admission Trends",
        "admission",
        "healthcare",
        "Admission Trends",
        0,
        time_field="admission_date",
        trend_field="count",
    ),
    _trend(
        "hc_discharge_trend",
        "Discharge Trends",
        "admission",
        "healthcare",
        "Admission Trends",
        1,
        time_field="discharge_date",
        trend_field="count",
    ),
    _chart(
        "hc_disease_dist",
        "Disease Distribution",
        ChartSubType.PIE,
        "patient",
        "healthcare",
        "Clinical Charts",
        0,
        group_by="diagnosis",
    ),
    _chart(
        "hc_ward_util",
        "Ward Utilization",
        ChartSubType.BAR,
        "admission",
        "healthcare",
        "Clinical Charts",
        1,
        group_by="ward",
    ),
    _chart(
        "hc_monthly_admissions",
        "Monthly Admissions",
        ChartSubType.LINE,
        "admission",
        "healthcare",
        "Clinical Charts",
        2,
        time_field="admission_date",
        group_by="month",
    ),
    _table(
        "hc_lab_reports",
        "Laboratory Reports",
        "lab_test",
        "healthcare",
        "Laboratory Reports",
        0,
        columns=["test_name", "patient", "result", "status", "date"],
    ),
    _table(
        "hc_patient_list",
        "Patient List",
        "patient",
        "healthcare",
        "Laboratory Reports",
        1,
        columns=["name", "age", "gender", "diagnosis", "ward"],
    ),
    _alert(
        "hc_critical_alerts",
        "Critical Lab Results",
        "lab_test",
        "healthcare",
        "Alerts",
        0,
        severity="critical",
    ),
    _alert(
        "hc_bed_shortage",
        "Bed Shortage Alert",
        "ward",
        "healthcare",
        "Alerts",
        1,
        severity="warning",
    ),
    _report(
        "hc_clinical_report",
        "Clinical Quality Report",
        "clinical_quality",
        "healthcare",
        "Reports",
        0,
    ),
    _report(
        "hc_revenue_report", "Revenue Cycle Report", "revenue_cycle", "healthcare", "Reports", 1
    ),
]

# â”€â”€ Education Widgets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

EDUCATION_WIDGETS = [
    _kpi(
        "edu_students",
        "Total Students",
        "student",
        "education",
        "Student Statistics",
        0,
        icon="GraduationCap",
    ),
    _kpi("edu_teachers", "Teachers", "teacher", "education", "Student Statistics", 1, icon="Users"),
    _kpi("edu_courses", "Courses", "course", "education", "Student Statistics", 2, icon="BookOpen"),
    _kpi(
        "edu_departments",
        "Departments",
        "department_edu",
        "education",
        "Student Statistics",
        3,
        icon="Building2",
    ),
    _kpi(
        "edu_attendance_rate",
        "Attendance Rate",
        "attendance",
        "education",
        "Student Statistics",
        4,
        icon="CalendarCheck",
        aggregation="avg",
        unit="%",
    ),
    _kpi(
        "edu_graduation_rate",
        "Graduation Rate",
        "graduation",
        "education",
        "Student Statistics",
        5,
        icon="Award",
        aggregation="avg",
        unit="%",
    ),
    _trend(
        "edu_enrollment_trend",
        "Enrollment Trends",
        "student",
        "education",
        "Enrollment Trends",
        0,
        time_field="enrollment_date",
        trend_field="count",
    ),
    _trend(
        "edu_attendance_trend",
        "Attendance Trends",
        "attendance",
        "education",
        "Enrollment Trends",
        1,
        time_field="date",
        trend_field="rate",
    ),
    _chart(
        "edu_perf_by_dept",
        "Performance by Department",
        ChartSubType.BAR,
        "grade",
        "education",
        "Performance Charts",
        0,
        group_by="department_edu",
    ),
    _chart(
        "edu_grade_dist",
        "Grade Distribution",
        ChartSubType.PIE,
        "grade",
        "education",
        "Performance Charts",
        1,
        group_by="grade_level",
    ),
    _chart(
        "edu_enrollment_chart",
        "Enrollment by Department",
        ChartSubType.HORIZONTAL_BAR,
        "student",
        "education",
        "Performance Charts",
        2,
        group_by="department_edu",
    ),
    _table(
        "edu_student_perf",
        "Student Performance",
        "student",
        "education",
        "Performance Details",
        0,
        columns=["name", "grade", "attendance", "course", "status"],
    ),
    _table(
        "edu_exam_results",
        "Exam Results",
        "exam",
        "education",
        "Performance Details",
        1,
        columns=["exam_name", "student", "score", "grade", "date"],
    ),
    _alert(
        "edu_at_risk", "At-Risk Students", "student", "education", "Alerts", 0, severity="warning"
    ),
    _alert(
        "edu_low_attendance",
        "Low Attendance Alert",
        "attendance",
        "education",
        "Alerts",
        1,
        severity="warning",
    ),
    _report(
        "edu_academic_report",
        "Academic Performance Report",
        "academic_performance",
        "education",
        "Reports",
        0,
    ),
    _report("edu_enrollment_report", "Enrollment Report", "enrollment", "education", "Reports", 1),
]

# â”€â”€ Business Widgets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BUSINESS_WIDGETS = [
    _kpi(
        "biz_revenue",
        "Total Revenue",
        "revenue",
        "business",
        "Sales Overview",
        0,
        icon="DollarSign",
        aggregation="sum",
        unit="$",
    ),
    _kpi(
        "biz_orders", "Total Orders", "order", "business", "Sales Overview", 1, icon="ShoppingCart"
    ),
    _kpi("biz_customers", "Customers", "customer", "business", "Sales Overview", 2, icon="Users"),
    _kpi(
        "biz_avg_order",
        "Avg Order Value",
        "order",
        "business",
        "Sales Overview",
        3,
        icon="TrendingUp",
        aggregation="avg",
        unit="$",
    ),
    _kpi("biz_inventory", "Inventory Items", "product", "business", "Inventory", 0, icon="Package"),
    _kpi(
        "biz_low_stock",
        "Low Stock Items",
        "product",
        "business",
        "Inventory",
        1,
        icon="AlertTriangle",
    ),
    _kpi("biz_supplier", "Active Suppliers", "supplier", "business", "Inventory", 2, icon="Truck"),
    _trend(
        "biz_revenue_trend",
        "Revenue Trends",
        "revenue",
        "business",
        "Revenue Trends",
        0,
        time_field="date",
        trend_field="amount",
    ),
    _trend(
        "biz_order_trend",
        "Order Trends",
        "order",
        "business",
        "Revenue Trends",
        1,
        time_field="date",
        trend_field="count",
    ),
    _chart(
        "biz_sales_by_region",
        "Sales by Region",
        ChartSubType.BAR,
        "order",
        "business",
        "Sales Charts",
        0,
        group_by="region",
    ),
    _chart(
        "biz_sales_by_cat",
        "Sales by Category",
        ChartSubType.PIE,
        "order",
        "business",
        "Sales Charts",
        1,
        group_by="category",
    ),
    _chart(
        "biz_monthly_revenue",
        "Monthly Revenue",
        ChartSubType.LINE,
        "revenue",
        "business",
        "Sales Charts",
        2,
        time_field="date",
        group_by="month",
    ),
    _chart(
        "biz_top_products",
        "Top Products",
        ChartSubType.HORIZONTAL_BAR,
        "order",
        "business",
        "Sales Charts",
        3,
        group_by="product",
    ),
    _table(
        "biz_inventory_list",
        "Inventory List",
        "product",
        "business",
        "Inventory Details",
        0,
        columns=["name", "sku", "quantity", "price", "supplier", "status"],
    ),
    _table(
        "biz_recent_orders",
        "Recent Orders",
        "order",
        "business",
        "Inventory Details",
        1,
        columns=["order_id", "customer", "total", "status", "date"],
    ),
    _map(
        "biz_sales_map",
        "Sales by Geography",
        "order",
        "business",
        "Maps",
        0,
        geo_field="region",
        value_field="total",
    ),
    _alert(
        "biz_low_stock_alert",
        "Low Stock Alerts",
        "product",
        "business",
        "Alerts",
        0,
        severity="warning",
    ),
    _alert(
        "biz_revenue_drop",
        "Revenue Drop Alert",
        "revenue",
        "business",
        "Alerts",
        1,
        severity="critical",
    ),
    _report("biz_sales_report", "Sales Report", "executive", "business", "Reports", 0),
    _report("biz_inventory_report", "Inventory Report", "inventory", "business", "Reports", 1),
]

# â”€â”€ Research Widgets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

RESEARCH_WIDGETS = [
    _kpi(
        "res_projects",
        "Research Projects",
        "project_ngo",
        "research",
        "Research Overview",
        0,
        icon="FlaskConical",
    ),
    _kpi(
        "res_surveys",
        "Imported Surveys",
        "survey",
        "research",
        "Research Overview",
        1,
        icon="FileText",
    ),
    _kpi(
        "res_respondents",
        "Total Respondents",
        "respondent",
        "research",
        "Research Overview",
        2,
        icon="Users",
    ),
    _kpi(
        "res_datasets",
        "Research Datasets",
        "dataset",
        "research",
        "Research Overview",
        3,
        icon="Database",
    ),
    _kpi(
        "res_publications",
        "Publications",
        "publication",
        "research",
        "Research Overview",
        4,
        icon="Newspaper",
    ),
    _trend(
        "res_response_trend",
        "Survey Response Trends",
        "respondent",
        "research",
        "Survey Trends",
        0,
        time_field="response_date",
        trend_field="count",
    ),
    _trend(
        "res_publication_trend",
        "Publication Output Trends",
        "publication",
        "research",
        "Survey Trends",
        1,
        time_field="publish_date",
        trend_field="count",
    ),
    _chart(
        "res_survey_dist",
        "Survey Distribution",
        ChartSubType.PIE,
        "survey",
        "research",
        "Statistical Charts",
        0,
        group_by="survey_type",
    ),
    _chart(
        "res_response_by_demo",
        "Responses by Demographic",
        ChartSubType.BAR,
        "respondent",
        "research",
        "Statistical Charts",
        1,
        group_by="demographic",
    ),
    _chart(
        "res_corr_matrix",
        "Correlation Matrix",
        ChartSubType.HEATMAP,
        "dataset",
        "research",
        "Statistical Charts",
        2,
    ),
    _chart(
        "res_dist_plot",
        "Distribution Plot",
        ChartSubType.AREA,
        "dataset",
        "research",
        "Statistical Charts",
        3,
    ),
    _table(
        "res_survey_results",
        "Survey Analysis Results",
        "survey",
        "research",
        "Statistical Outputs",
        0,
        columns=["question", "mean", "std_dev", "count", "significant"],
    ),
    _table(
        "res_stat_summary",
        "Statistical Summary",
        "dataset",
        "research",
        "Statistical Outputs",
        1,
        columns=["variable", "min", "max", "mean", "median", "std_dev"],
    ),
    _alert(
        "res_data_quality",
        "Data Quality Alerts",
        "dataset",
        "research",
        "Alerts",
        0,
        severity="warning",
    ),
    _report(
        "res_survey_report", "Survey Analysis Report", "survey_analysis", "research", "Reports", 0
    ),
    _report(
        "res_stat_report",
        "Statistical Output Report",
        "statistical_output",
        "research",
        "Reports",
        1,
    ),
    _report("res_pub_report", "Publication Report", "publication", "research", "Reports", 2),
]

# â”€â”€ Generic / Cross-Industry Widgets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

GENERIC_WIDGETS = [
    _kpi(
        "gen_dashboards",
        "Total Dashboards",
        "dashboard",
        "generic",
        "Overview",
        0,
        icon="LayoutDashboard",
    ),
    _kpi("gen_datasets", "Total Datasets", "dataset", "generic", "Overview", 1, icon="Database"),
    _kpi("gen_reports", "Total Reports", "report", "generic", "Overview", 2, icon="FileText"),
    _kpi("gen_users", "Active Users", "user", "generic", "Overview", 3, icon="Users"),
    _trend(
        "gen_activity_trend",
        "Activity Trends",
        "activity",
        "generic",
        "Trends",
        0,
        time_field="date",
        trend_field="count",
    ),
    _chart(
        "gen_data_by_type",
        "Data by Type",
        ChartSubType.PIE,
        "dataset",
        "generic",
        "Charts",
        0,
        group_by="type",
    ),
    _table(
        "gen_recent_activity",
        "Recent Activity",
        "activity",
        "generic",
        "Details",
        0,
        columns=["action", "user", "resource", "timestamp"],
    ),
    _alert(
        "gen_system_alerts", "System Alerts", "system", "generic", "Alerts", 0, severity="warning"
    ),
]


# â”€â”€ Registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def register_all_widgets() -> None:
    """Register all industry widget definitions with the WidgetRegistry."""
    all_widgets = (
        HEALTHCARE_WIDGETS
        + EDUCATION_WIDGETS
        + BUSINESS_WIDGETS
        + RESEARCH_WIDGETS
        + GENERIC_WIDGETS
    )
    for widget in all_widgets:
        WidgetRegistry.register(widget)
    logger.info(f"Registered {len(all_widgets)} widget definitions across 5 industries")


# Register on import
register_all_widgets()


# â”€â”€ Industry Dashboard Templates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


INDUSTRY_DASHBOARD_TEMPLATES = {
    "healthcare": {
        "name": "Healthcare Executive Dashboard",
        "description": "Patient statistics, admission trends, laboratory reports",
        "widget_keys": [w.key for w in HEALTHCARE_WIDGETS],
    },
    "education": {
        "name": "Education Executive Dashboard",
        "description": "Student performance, enrollment trends, academic reports",
        "widget_keys": [w.key for w in EDUCATION_WIDGETS],
    },
    "business": {
        "name": "Business Executive Dashboard",
        "description": "Sales, inventory, revenue analytics",
        "widget_keys": [w.key for w in BUSINESS_WIDGETS],
    },
    "research": {
        "name": "Research Analytics Dashboard",
        "description": "Survey analysis, statistical outputs, publication reports",
        "widget_keys": [w.key for w in RESEARCH_WIDGETS],
    },
    "generic": {
        "name": "Executive Dashboard",
        "description": "General-purpose analytics dashboard",
        "widget_keys": [w.key for w in GENERIC_WIDGETS],
    },
}
