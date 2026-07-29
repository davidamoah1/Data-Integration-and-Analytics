"""Industry Intelligence Engine — industry-specific KPIs, templates, and recommendations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import IndustryKPI, IndustryTemplate


# Industry KPI definitions (seeded on startup)
INDUSTRY_KPIS = {
    "healthcare": [
        {"kpi_name": "Patient Satisfaction Score", "kpi_code": "patient_satisfaction", "formula": "avg(satisfaction_rating)", "unit": "score", "target": "≥ 4.5", "category": "patient", "description": "Average patient satisfaction rating"},
        {"kpi_name": "Average Length of Stay", "kpi_code": "avg_los", "formula": "sum(days) / count(patients)", "unit": "days", "target": "≤ 4.0", "category": "operational", "description": "Average number of days patients stay"},
        {"kpi_name": "Readmission Rate", "kpi_code": "readmission_rate", "formula": "count(readmitted) / count(discharged) * 100", "unit": "%", "target": "≤ 10%", "category": "quality", "description": "Percentage of patients readmitted within 30 days"},
        {"kpi_name": "Bed Occupancy Rate", "kpi_code": "bed_occupancy", "formula": "occupied_beds / total_beds * 100", "unit": "%", "target": "75-85%", "category": "operational", "description": "Percentage of beds occupied"},
        {"kpi_name": "Mortality Rate", "kpi_code": "mortality_rate", "formula": "count(deaths) / count(admissions) * 100", "unit": "%", "target": "≤ 2%", "category": "quality", "description": "In-hospital mortality rate"},
    ],
    "education": [
        {"kpi_name": "Student Performance Index", "kpi_code": "student_performance", "formula": "avg(test_scores)", "unit": "score", "target": "≥ 75%", "category": "academic", "description": "Average student test performance"},
        {"kpi_name": "Graduation Rate", "kpi_code": "graduation_rate", "formula": "count(graduated) / count(enrolled) * 100", "unit": "%", "target": "≥ 90%", "category": "academic", "description": "Percentage of students who graduate"},
        {"kpi_name": "Dropout Rate", "kpi_code": "dropout_rate", "formula": "count(dropouts) / count(enrolled) * 100", "unit": "%", "target": "≤ 5%", "category": "academic", "description": "Percentage of students who drop out"},
        {"kpi_name": "Teacher-Student Ratio", "kpi_code": "teacher_student_ratio", "formula": "count(teachers) / count(students)", "unit": "ratio", "target": "≤ 1:30", "category": "operational", "description": "Ratio of teachers to students"},
        {"kpi_name": "Attendance Rate", "kpi_code": "attendance_rate", "formula": "present_days / total_days * 100", "unit": "%", "target": "≥ 95%", "category": "operational", "description": "Student attendance rate"},
    ],
    "banking": [
        {"kpi_name": "Net Interest Margin", "kpi_code": "nim", "formula": "(interest_income - interest_expense) / avg_assets * 100", "unit": "%", "target": "3-5%", "category": "financial", "description": "Difference between interest income and expense"},
        {"kpi_name": "Loan Default Rate", "kpi_code": "default_rate", "formula": "defaulted_loans / total_loans * 100", "unit": "%", "target": "≤ 5%", "category": "risk", "description": "Percentage of loans in default"},
        {"kpi_name": "Cost-to-Income Ratio", "kpi_code": "cir", "formula": "operating_costs / operating_income * 100", "unit": "%", "target": "≤ 55%", "category": "financial", "description": "Operating efficiency metric"},
        {"kpi_name": "Customer Acquisition Cost", "kpi_code": "cac", "formula": "marketing_spend / new_customers", "unit": "$", "target": "≤ $50", "category": "growth", "description": "Cost to acquire a new customer"},
        {"kpi_name": "Capital Adequacy Ratio", "kpi_code": "car", "formula": "capital / risk_weighted_assets * 100", "unit": "%", "target": "≥ 10%", "category": "risk", "description": "Bank's capital to risk ratio"},
    ],
    "agriculture": [
        {"kpi_name": "Crop Yield", "kpi_code": "crop_yield", "formula": "total_harvest / cultivated_area", "unit": "tons/ha", "target": "varies by crop", "category": "production", "description": "Crop yield per hectare"},
        {"kpi_name": "Water Usage Efficiency", "kpi_code": "water_efficiency", "formula": "crop_output / water_used", "unit": "kg/m³", "target": "≥ 1.5", "category": "sustainability", "description": "Crop output per unit of water"},
        {"kpi_name": "Cost per Hectare", "kpi_code": "cost_per_hectare", "formula": "total_costs / cultivated_area", "unit": "$/ha", "target": "varies", "category": "financial", "description": "Operating cost per hectare"},
        {"kpi_name": "Revenue per Hectare", "kpi_code": "revenue_per_hectare", "formula": "total_revenue / cultivated_area", "unit": "$/ha", "target": "varies", "category": "financial", "description": "Revenue generated per hectare"},
        {"kpi_name": "Loss Rate", "kpi_code": "loss_rate", "formula": "lost_crop / total_crop * 100", "unit": "%", "target": "≤ 15%", "category": "quality", "description": "Post-harvest loss percentage"},
    ],
    "retail": [
        {"kpi_name": "Sales per Square Meter", "kpi_code": "sales_per_sqm", "formula": "total_sales / store_area", "unit": "$/m²", "target": "varies", "category": "operational", "description": "Retail sales efficiency"},
        {"kpi_name": "Inventory Turnover", "kpi_code": "inventory_turnover", "formula": "cogs / avg_inventory", "unit": "ratio", "target": "≥ 4", "category": "operational", "description": "How quickly inventory is sold"},
        {"kpi_name": "Customer Retention Rate", "kpi_code": "retention_rate", "formula": "returning_customers / total_customers * 100", "unit": "%", "target": "≥ 70%", "category": "customer", "description": "Percentage of returning customers"},
        {"kpi_name": "Average Transaction Value", "kpi_code": "atv", "formula": "total_revenue / num_transactions", "unit": "$", "target": "varies", "category": "financial", "description": "Average value per transaction"},
        {"kpi_name": "Gross Margin", "kpi_code": "gross_margin", "formula": "(revenue - cogs) / revenue * 100", "unit": "%", "target": "≥ 40%", "category": "financial", "description": "Gross profit margin percentage"},
    ],
    "manufacturing": [
        {"kpi_name": "Overall Equipment Effectiveness", "kpi_code": "oee", "formula": "availability * performance * quality", "unit": "%", "target": "≥ 85%", "category": "operational", "description": "Manufacturing effectiveness metric"},
        {"kpi_name": "Defect Rate", "kpi_code": "defect_rate", "formula": "defective_units / total_units * 100", "unit": "%", "target": "≤ 3%", "category": "quality", "description": "Percentage of defective products"},
        {"kpi_name": "Production Cycle Time", "kpi_code": "cycle_time", "formula": "total_production_time / num_units", "unit": "hours", "target": "varies", "category": "operational", "description": "Time to produce one unit"},
        {"kpi_name": "Capacity Utilization", "kpi_code": "capacity_utilization", "formula": "actual_output / maximum_output * 100", "unit": "%", "target": "≥ 80%", "category": "operational", "description": "Percentage of capacity used"},
        {"kpi_name": "On-Time Delivery Rate", "kpi_code": "otd_rate", "formula": "on_time_deliveries / total_deliveries * 100", "unit": "%", "target": "≥ 95%", "category": "customer", "description": "Percentage of on-time deliveries"},
    ],
    "telecom": [
        {"kpi_name": "Average Revenue per User", "kpi_code": "arpu", "formula": "total_revenue / num_subscribers", "unit": "$", "target": "varies", "category": "financial", "description": "Revenue per subscriber"},
        {"kpi_name": "Churn Rate", "kpi_code": "churn_rate", "formula": "lost_subscribers / total_subscribers * 100", "unit": "%", "target": "≤ 2%", "category": "customer", "description": "Monthly subscriber churn"},
        {"kpi_name": "Network Availability", "kpi_code": "network_availability", "formula": "uptime / total_time * 100", "unit": "%", "target": "≥ 99.9%", "category": "operational", "description": "Network uptime percentage"},
        {"kpi_name": "Customer Acquisition Cost", "kpi_code": "cac", "formula": "marketing_spend / new_subscribers", "unit": "$", "target": "≤ $30", "category": "growth", "description": "Cost to acquire new subscriber"},
        {"kpi_name": "Data Revenue Share", "kpi_code": "data_revenue_share", "formula": "data_revenue / total_revenue * 100", "unit": "%", "target": "≥ 50%", "category": "financial", "description": "Data services revenue share"},
    ],
    "logistics": [
        {"kpi_name": "On-Time Delivery", "kpi_code": "otd", "formula": "on_time / total_deliveries * 100", "unit": "%", "target": "≥ 95%", "category": "operational", "description": "Percentage of on-time deliveries"},
        {"kpi_name": "Transportation Cost per Unit", "kpi_code": "cost_per_unit", "formula": "transport_cost / units_shipped", "unit": "$", "target": "varies", "category": "financial", "description": "Cost to ship one unit"},
        {"kpi_name": "Vehicle Utilization", "kpi_code": "vehicle_utilization", "formula": "loaded_hours / total_hours * 100", "unit": "%", "target": "≥ 80%", "category": "operational", "description": "Vehicle usage efficiency"},
        {"kpi_name": "Order Accuracy", "kpi_code": "order_accuracy", "formula": "correct_orders / total_orders * 100", "unit": "%", "target": "≥ 99%", "category": "quality", "description": "Percentage of error-free orders"},
        {"kpi_name": "Average Transit Time", "kpi_code": "transit_time", "formula": "sum(delivery_time) / count(deliveries)", "unit": "hours", "target": "varies", "category": "operational", "description": "Average delivery time"},
    ],
    "government": [
        {"kpi_name": "Service Delivery Time", "kpi_code": "service_time", "formula": "avg(processing_time)", "unit": "days", "target": "≤ 7", "category": "operational", "description": "Average time to deliver services"},
        {"kpi_name": "Citizen Satisfaction", "kpi_code": "citizen_satisfaction", "formula": "avg(satisfaction_score)", "unit": "score", "target": "≥ 4.0", "category": "citizen", "description": "Citizen satisfaction with services"},
        {"kpi_name": "Budget Utilization", "kpi_code": "budget_utilization", "formula": "spent / allocated * 100", "unit": "%", "target": "85-100%", "category": "financial", "description": "Percentage of budget utilized"},
        {"kpi_name": "Digital Service Adoption", "kpi_code": "digital_adoption", "formula": "digital_applications / total_applications * 100", "unit": "%", "target": "≥ 60%", "category": "operational", "description": "Percentage of digital service usage"},
        {"kpi_name": "Compliance Rate", "kpi_code": "compliance_rate", "formula": "compliant_entities / total_entities * 100", "unit": "%", "target": "≥ 90%", "category": "regulatory", "description": "Regulatory compliance rate"},
    ],
}

# Industry template definitions
INDUSTRY_TEMPLATES = {
    "healthcare": [
        {"template_name": "Hospital Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["patient_satisfaction", "avg_los", "readmission_rate", "bed_occupancy"], "charts": ["trend", "gauge", "comparison"]}},
        {"template_name": "Patient Outcomes Report", "template_type": "report", "config": {"sections": ["mortality", "readmission", "satisfaction", "treatment_efficacy"]}},
    ],
    "education": [
        {"template_name": "School Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["student_performance", "graduation_rate", "attendance_rate"], "charts": ["trend", "distribution", "comparison"]}},
        {"template_name": "Student Analytics Report", "template_type": "report", "config": {"sections": ["performance", "attendance", "demographics", "interventions"]}},
    ],
    "banking": [
        {"template_name": "Bank Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["nim", "default_rate", "cir", "car"], "charts": ["trend", "gauge", "risk_matrix"]}},
        {"template_name": "Credit Risk Analysis", "template_type": "model", "config": {"model_type": "classification", "target": "default_probability", "features": ["credit_score", "income", "loan_amount"]}},
    ],
    "agriculture": [
        {"template_name": "Farm Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["crop_yield", "water_efficiency", "revenue_per_hectare"], "charts": ["geographic", "trend", "comparison"]}},
        {"template_name": "Crop Yield Forecast", "template_type": "model", "config": {"model_type": "forecasting", "target": "crop_yield", "features": ["rainfall", "temperature", "fertilizer"]}},
    ],
    "retail": [
        {"template_name": "Store Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["sales_per_sqm", "inventory_turnover", "retention_rate", "atv"], "charts": ["trend", "heatmap", "funnel"]}},
        {"template_name": "Customer Segmentation", "template_type": "model", "config": {"model_type": "clustering", "features": ["purchase_frequency", "avg_basket_size", "recency"]}},
    ],
    "manufacturing": [
        {"template_name": "Production Dashboard", "template_type": "dashboard", "config": {"kpis": ["oee", "defect_rate", "cycle_time", "otd_rate"], "charts": ["gauge", "trend", "pareto"]}},
        {"template_name": "Quality Prediction", "template_type": "model", "config": {"model_type": "classification", "target": "quality_class", "features": ["temperature", "pressure", "speed", "raw_material_quality"]}},
    ],
    "telecom": [
        {"template_name": "Network Performance Dashboard", "template_type": "dashboard", "config": {"kpis": ["arpu", "churn_rate", "network_availability"], "charts": ["geographic", "trend", "gauge"]}},
        {"template_name": "Churn Prediction", "template_type": "model", "config": {"model_type": "classification", "target": "churn", "features": ["tenure", "monthly_charges", "data_usage", "complaints"]}},
    ],
    "logistics": [
        {"template_name": "Operations Dashboard", "template_type": "dashboard", "config": {"kpis": ["otd", "cost_per_unit", "vehicle_utilization", "order_accuracy"], "charts": ["map", "trend", "gauge"]}},
        {"template_name": "Delivery Time Prediction", "template_type": "model", "config": {"model_type": "regression", "target": "delivery_time", "features": ["distance", "weather", "traffic", "vehicle_type"]}},
    ],
    "government": [
        {"template_name": "Service Delivery Dashboard", "template_type": "dashboard", "config": {"kpis": ["service_time", "citizen_satisfaction", "budget_utilization", "digital_adoption"], "charts": ["trend", "geographic", "comparison"]}},
        {"template_name": "Citizen Satisfaction Analysis", "template_type": "report", "config": {"sections": ["satisfaction_trends", "service_comparison", "demographics", "recommendations"]}},
    ],
}


class IndustryIntelligenceService:
    """Service for industry-specific intelligence."""

    SUPPORTED_INDUSTRIES = list(INDUSTRY_KPIS.keys())

    def __init__(self, db: DbSession):
        self.db = db

    def list_industries(self) -> list[str]:
        return self.SUPPORTED_INDUSTRIES

    def get_kpis(self, industry: str) -> list[IndustryKPI]:
        return self.db.execute(
            select(IndustryKPI).where(IndustryKPI.industry == industry)
        ).scalars().all()

    def get_templates(self, industry: str) -> list[IndustryTemplate]:
        return self.db.execute(
            select(IndustryTemplate).where(
                IndustryTemplate.industry == industry,
                IndustryTemplate.is_active == True,  # noqa: E712
            )
        ).scalars().all()

    def get_industry_overview(self, industry: str) -> dict:
        kpis = self.get_kpis(industry)
        templates = self.get_templates(industry)
        return {
            "industry": industry,
            "kpi_count": len(kpis),
            "template_count": len(templates),
            "kpis": [
                {
                    "kpi_name": k.kpi_name,
                    "kpi_code": k.kpi_code,
                    "formula": k.formula,
                    "unit": k.unit,
                    "target": k.target,
                    "category": k.category,
                    "description": k.description,
                }
                for k in kpis
            ],
            "templates": [
                {
                    "template_name": t.template_name,
                    "template_type": t.template_type,
                    "config": t.config,
                    "description": t.description,
                }
                for t in templates
            ],
        }

    @staticmethod
    def recommend_analysis(industry: str, available_columns: list[str]) -> dict:
        """AI-recommended analyses based on industry and available data."""
        recommendations = []

        industry_recs = {
            "healthcare": [
                {"analysis": "Patient outcome prediction", "type": "classification", "reason": "Identify factors affecting patient outcomes"},
                {"analysis": "Readmission risk scoring", "type": "classification", "reason": "Predict which patients are likely to be readmitted"},
                {"analysis": "Length of stay forecasting", "type": "regression", "reason": "Optimize resource allocation"},
            ],
            "education": [
                {"analysis": "Student performance prediction", "type": "regression", "reason": "Identify at-risk students early"},
                {"analysis": "Student segmentation", "type": "clustering", "reason": "Group students by learning patterns"},
                {"analysis": "Dropout risk analysis", "type": "classification", "reason": "Predict and prevent student dropout"},
            ],
            "banking": [
                {"analysis": "Credit risk scoring", "type": "classification", "reason": "Assess loan default probability"},
                {"analysis": "Customer segmentation", "type": "clustering", "reason": "Personalize banking services"},
                {"analysis": "Fraud detection", "type": "anomaly_detection", "reason": "Detect unusual transaction patterns"},
            ],
            "agriculture": [
                {"analysis": "Crop yield prediction", "type": "regression", "reason": "Forecast harvest based on conditions"},
                {"analysis": "Disease detection", "type": "classification", "reason": "Identify crop diseases early"},
                {"analysis": "Weather impact analysis", "type": "correlation", "reason": "Understand weather-crop relationships"},
            ],
            "retail": [
                {"analysis": "Customer segmentation", "type": "clustering", "reason": "Target marketing by customer group"},
                {"analysis": "Sales forecasting", "type": "forecasting", "reason": "Predict future sales trends"},
                {"analysis": "Churn prediction", "type": "classification", "reason": "Identify customers likely to leave"},
            ],
        }

        recs = industry_recs.get(industry, [])
        for r in recs:
            recommendations.append({
                "analysis": r["analysis"],
                "recommended_type": r["type"],
                "reason": r["reason"],
                "suitable_columns": available_columns[:5],
            })

        return {"industry": industry, "recommendations": recommendations}


def seed_industry_data(db: DbSession) -> None:
    """Seed industry KPIs and templates."""
    # Seed KPIs
    for industry, kpis in INDUSTRY_KPIS.items():
        for kpi_data in kpis:
            existing = db.execute(
                select(IndustryKPI).where(
                    IndustryKPI.industry == industry,
                    IndustryKPI.kpi_code == kpi_data["kpi_code"],
                )
            ).scalar_one_or_none()
            if not existing:
                kpi = IndustryKPI(industry=industry, **kpi_data)
                db.add(kpi)

    # Seed templates
    for industry, templates in INDUSTRY_TEMPLATES.items():
        for tmpl_data in templates:
            existing = db.execute(
                select(IndustryTemplate).where(
                    IndustryTemplate.industry == industry,
                    IndustryTemplate.template_name == tmpl_data["template_name"],
                )
            ).scalar_one_or_none()
            if not existing:
                tmpl = IndustryTemplate(
                    industry=industry,
                    template_name=tmpl_data["template_name"],
                    template_type=tmpl_data["template_type"],
                    config=tmpl_data.get("config"),
                    description=tmpl_data.get("description"),
                )
                db.add(tmpl)

    db.commit()
