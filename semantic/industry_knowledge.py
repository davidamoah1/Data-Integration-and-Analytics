"""MODULE 6 â€” Industry Knowledge Base.

Knowledge libraries for every supported industry containing:
  - Business entities
  - Relationships
  - KPIs
  - Business rules
  - Metrics
  - Charts
  - Reports
  - Alerts
  - AI prompts
  - Recommendations
"""

from __future__ import annotations

INDUSTRY_KNOWLEDGE: dict[str, dict] = {
    "healthcare": {
        "display_name": "Healthcare",
        "description": "Hospital & clinic analytics: patients, admissions, billing, insurance",
        "entities": [
            "patient",
            "doctor",
            "admission",
            "ward",
            "diagnosis",
            "medicine",
            "lab_test",
            "appointment",
            "insurance",
            "billing",
        ],
        "key_relationships": [
            "Patient â†’ Admission â†’ Doctor â†’ Ward â†’ Treatment â†’ Billing",
        ],
        "kpis": {
            "operational": [
                "total_admissions",
                "average_stay",
                "bed_occupancy",
                "readmission_rate",
                "discharge_rate",
            ],
            "financial": [
                "total_revenue",
                "collection_rate",
                "outstanding_amount",
                "avg_bill",
                "insurance_coverage",
            ],
            "clinical": [
                "mortality_rate",
                "treatment_success",
                "infection_rate",
                "patient_satisfaction",
            ],
        },
        "business_rules": [
            "Bed occupancy should not exceed 95%",
            "Readmission rate > 15% indicates quality issues",
            "Insurance denial rate > 20% requires process review",
            "Average stay > 7 days may indicate care inefficiency",
        ],
        "recommended_charts": ["treemap", "sunburst", "funnel", "bar", "line"],
        "report_templates": [
            "Executive Summary â€” Hospital Performance",
            "Department Efficiency Report",
            "Insurance & Billing Analysis",
            "Patient Demographics Report",
        ],
        "alerts": [
            {
                "metric": "bed_occupancy",
                "threshold": ">95",
                "severity": "critical",
                "message": "Bed occupancy critical",
            },
            {
                "metric": "readmission_rate",
                "threshold": ">15",
                "severity": "warning",
                "message": "High readmission rate",
            },
            {
                "metric": "insurance_denial_rate",
                "threshold": ">20",
                "severity": "warning",
                "message": "High insurance denial rate",
            },
        ],
        "ai_prompts": [
            "Analyze patient admission trends and identify peak periods",
            "Which departments have the highest bed occupancy?",
            "What is the insurance coverage breakdown by provider?",
            "Identify patients at risk of readmission",
        ],
        "recommendations": [
            "Monitor bed occupancy during peak admission months",
            "Track insurance denial patterns by provider",
            "Review average stay by department for efficiency gains",
        ],
    },
    "education": {
        "display_name": "Education",
        "description": "School & university analytics: students, courses, grades, attendance",
        "entities": [
            "student",
            "teacher",
            "course",
            "department_edu",
            "semester",
            "attendance",
            "exam",
            "grade",
        ],
        "key_relationships": [
            "Student â†’ Course â†’ Department â†’ Grades â†’ Attendance",
        ],
        "kpis": {
            "operational": [
                "enrollment_count",
                "attendance_rate",
                "course_completion",
                "dropout_rate",
            ],
            "academic": [
                "pass_rate",
                "avg_grade",
                "distinction_rate",
                "gpa_average",
                "failure_rate",
            ],
            "financial": [
                "tuition_revenue",
                "collection_rate",
                "fee_outstanding",
                "budget_utilization",
            ],
        },
        "business_rules": [
            "Attendance rate below 75% triggers intervention",
            "Pass rate should be above 80%",
            "Dropout rate > 10% requires investigation",
            "Fee collection rate should exceed 90%",
        ],
        "recommended_charts": ["waterfall", "bar", "line", "pie", "heatmap"],
        "report_templates": [
            "Academic Performance Report",
            "Enrollment & Demographics",
            "Department Efficiency Report",
            "Fee Collection Analysis",
        ],
        "alerts": [
            {
                "metric": "attendance_rate",
                "threshold": "<75",
                "severity": "warning",
                "message": "Low attendance rate",
            },
            {
                "metric": "dropout_rate",
                "threshold": ">10",
                "severity": "critical",
                "message": "High dropout rate",
            },
            {
                "metric": "fee_collection_rate",
                "threshold": "<90",
                "severity": "warning",
                "message": "Low fee collection",
            },
        ],
        "ai_prompts": [
            "Analyze student enrollment trends by department",
            "Which courses have the highest failure rates?",
            "What is the attendance pattern by day of week?",
            "Identify students at risk of dropping out",
        ],
        "recommendations": [
            "Monitor attendance patterns for early intervention",
            "Track grade distribution by course and teacher",
            "Review fee collection efficiency by semester",
        ],
    },
    "church": {
        "display_name": "Church",
        "description": "Church & ministry analytics: members, giving, attendance, outreach",
        "entities": [
            "member",
            "visitor",
            "ministry",
            "pastor",
            "offering",
            "tithe",
            "branch_church",
            "event",
        ],
        "key_relationships": [
            "Member â†’ Branch â†’ Ministry â†’ Giving â†’ Attendance",
        ],
        "kpis": {
            "operational": [
                "total_members",
                "attendance_rate",
                "new_members",
                "retention_rate",
                "visitor_conversion",
            ],
            "financial": [
                "total_offering",
                "tithe_compliance",
                "avg_offering",
                "giving_rate",
                "offering_growth",
            ],
            "ministry": ["ministry_participation", "event_attendance", "outreach_impact"],
        },
        "business_rules": [
            "Member retention should be above 85%",
            "Tithe compliance rate should exceed 60%",
            "Visitor conversion target: 30%",
            "Attendance decline > 10% requires outreach review",
        ],
        "recommended_charts": ["rose", "line", "bar", "pie", "area"],
        "report_templates": [
            "Church Growth & Health Report",
            "Giving & Tithe Analysis",
            "Ministry Performance Report",
            "Event Attendance Summary",
        ],
        "alerts": [
            {
                "metric": "retention_rate",
                "threshold": "<85",
                "severity": "warning",
                "message": "Low member retention",
            },
            {
                "metric": "attendance_decline",
                "threshold": ">10",
                "severity": "warning",
                "message": "Attendance declining",
            },
            {
                "metric": "tithe_compliance",
                "threshold": "<60",
                "severity": "warning",
                "message": "Low tithe compliance",
            },
        ],
        "ai_prompts": [
            "Analyze offering trends over the last 12 months",
            "Which branches have the highest growth rate?",
            "What is the giving pattern by event type?",
            "Identify members who have stopped giving",
        ],
        "recommendations": [
            "Track giving patterns by member segment",
            "Monitor attendance trends by branch and event type",
            "Review visitor conversion strategies",
        ],
    },
    "retail": {
        "display_name": "Retail / SME",
        "description": "Retail & SME analytics: sales, customers, products, inventory",
        "entities": [
            "customer",
            "order",
            "invoice",
            "product",
            "supplier",
            "warehouse",
            "inventory",
        ],
        "key_relationships": [
            "Customer â†’ Order â†’ Product â†’ Supplier â†’ Inventory",
        ],
        "kpis": {
            "operational": ["total_orders", "avg_order_value", "conversion_rate", "order_growth"],
            "financial": ["total_revenue", "gross_profit", "profit_margin", "revenue_growth"],
            "inventory": ["stock_turnover", "stockout_rate", "inventory_value", "aging_stock"],
        },
        "business_rules": [
            "Profit margin should be above 15%",
            "Stock turnover rate > 4 is healthy",
            "Customer retention should exceed 70%",
            "Stockout rate > 5% requires inventory review",
        ],
        "recommended_charts": ["line", "bar", "scatter", "heatmap", "pie"],
        "report_templates": [
            "Sales Performance Report",
            "Customer Analysis Report",
            "Inventory Health Report",
            "Profitability Analysis",
        ],
        "alerts": [
            {
                "metric": "profit_margin",
                "threshold": "<15",
                "severity": "warning",
                "message": "Low profit margin",
            },
            {
                "metric": "stockout_rate",
                "threshold": ">5",
                "severity": "warning",
                "message": "High stockout rate",
            },
            {
                "metric": "customer_retention",
                "threshold": "<70",
                "severity": "warning",
                "message": "Low customer retention",
            },
        ],
        "ai_prompts": [
            "Analyze sales trends and identify seasonal patterns",
            "Which products have the highest profit margin?",
            "What is the customer segmentation by revenue?",
            "Identify slow-moving inventory items",
        ],
        "recommendations": [
            "Monitor product profitability by category",
            "Track customer lifetime value segments",
            "Review inventory turnover by product line",
        ],
    },
    "government": {
        "display_name": "Government",
        "description": "Government analytics: projects, budgets, procurement, contractors",
        "entities": [
            "citizen",
            "department_gov",
            "project_gov",
            "budget_gov",
            "procurement",
            "contractor",
            "revenue_gov",
        ],
        "key_relationships": [
            "Department â†’ Project â†’ Contractor â†’ Procurement â†’ Budget",
        ],
        "kpis": {
            "operational": [
                "total_projects",
                "completion_rate",
                "delay_rate",
                "project_efficiency",
            ],
            "financial": [
                "total_budget",
                "utilization_rate",
                "variance",
                "total_revenue",
                "deficit",
            ],
            "procurement": ["total_procurement", "competition_rate", "avg_contract", "savings"],
        },
        "business_rules": [
            "Budget utilization should be between 85% and 100%",
            "Project delay rate > 20% requires review",
            "Procurement competition rate should exceed 70%",
            "Budget deficit > 10% requires fiscal review",
        ],
        "recommended_charts": ["icicle", "bar", "line", "treemap", "waterfall"],
        "report_templates": [
            "Government Performance Report",
            "Budget Utilization Analysis",
            "Procurement & Contractor Report",
            "Project Status Dashboard",
        ],
        "alerts": [
            {
                "metric": "budget_utilization",
                "threshold": "<85",
                "severity": "warning",
                "message": "Low budget utilization",
            },
            {
                "metric": "project_delay_rate",
                "threshold": ">20",
                "severity": "critical",
                "message": "High project delay rate",
            },
            {
                "metric": "deficit",
                "threshold": ">10",
                "severity": "critical",
                "message": "Budget deficit exceeds threshold",
            },
        ],
        "ai_prompts": [
            "Analyze project completion rates by department",
            "Which contractors have the best performance scores?",
            "What is the budget utilization by ministry?",
            "Identify projects at risk of delay",
        ],
        "recommendations": [
            "Monitor project timelines against budget allocation",
            "Track contractor performance across projects",
            "Review procurement competition by category",
        ],
    },
    "ngo": {
        "display_name": "NGO",
        "description": "NGO analytics: donors, grants, programs, beneficiaries, impact",
        "entities": ["beneficiary", "grant", "donor", "program", "project_ngo", "donation"],
        "key_relationships": [
            "Donor â†’ Grant â†’ Program â†’ Project â†’ Beneficiary",
        ],
        "kpis": {
            "operational": [
                "beneficiary_count",
                "program_completion",
                "project_completion",
                "coverage_rate",
            ],
            "financial": [
                "total_donations",
                "total_grants",
                "grant_utilization",
                "donor_retention",
                "avg_donation",
            ],
            "impact": [
                "beneficiaries_reached",
                "satisfaction_rate",
                "impact_score",
                "cost_per_beneficiary",
            ],
        },
        "business_rules": [
            "Grant utilization should be above 80%",
            "Donor retention should exceed 75%",
            "Beneficiary coverage target: 90%",
            "Program completion rate should be above 85%",
        ],
        "recommended_charts": ["sunburst", "treemap", "bar", "line", "bubble"],
        "report_templates": [
            "Donor & Funding Report",
            "Program Impact Assessment",
            "Beneficiary Coverage Report",
            "Grant Utilization Analysis",
        ],
        "alerts": [
            {
                "metric": "grant_utilization",
                "threshold": "<80",
                "severity": "warning",
                "message": "Low grant utilization",
            },
            {
                "metric": "donor_retention",
                "threshold": "<75",
                "severity": "warning",
                "message": "Low donor retention",
            },
            {
                "metric": "program_completion",
                "threshold": "<85",
                "severity": "warning",
                "message": "Low program completion",
            },
        ],
        "ai_prompts": [
            "Analyze donation growth trends by funding source",
            "Which programs have the highest impact scores?",
            "What is the beneficiary coverage by region?",
            "Identify donors at risk of churning",
        ],
        "recommendations": [
            "Track donor engagement and retention patterns",
            "Monitor program impact against beneficiary targets",
            "Review grant utilization by funding source",
        ],
    },
    "banking": {
        "display_name": "Banking",
        "description": "Banking analytics: accounts, transactions, loans, cards, deposits",
        "entities": ["account", "transaction", "loan", "card", "customer"],
        "key_relationships": [
            "Customer â†’ Account â†’ Transaction â†’ Card â†’ Loan",
        ],
        "kpis": {
            "operational": [
                "total_accounts",
                "active_accounts",
                "transaction_count",
                "card_count",
            ],
            "financial": [
                "total_balance",
                "total_deposits",
                "total_loans",
                "loan_portfolio_value",
                "interest_income",
            ],
            "risk": [
                "default_rate",
                "non_performing_loans",
                "delinquency_rate",
                "fraud_rate",
            ],
        },
        "business_rules": [
            "Non-performing loan ratio should be below 5%",
            "Capital adequacy ratio should exceed 10%",
            "Loan-to-deposit ratio should be between 70% and 90%",
            "Delinquency rate > 5% requires portfolio review",
        ],
        "recommended_charts": ["line", "bar", "pie", "gauge", "heatmap"],
        "report_templates": [
            "Banking Performance Report",
            "Loan Portfolio Analysis",
            "Transaction Volume Report",
            "Risk Assessment Report",
        ],
        "alerts": [
            {
                "metric": "non_performing_loans",
                "threshold": ">5",
                "severity": "critical",
                "message": "High non-performing loan ratio",
            },
            {
                "metric": "delinquency_rate",
                "threshold": ">5",
                "severity": "warning",
                "message": "Rising delinquency rate",
            },
            {
                "metric": "loan_to_deposit",
                "threshold": ">90",
                "severity": "warning",
                "message": "Loan-to-deposit ratio too high",
            },
        ],
        "ai_prompts": [
            "Analyze transaction volume trends by branch",
            "Which loan products have the highest default rates?",
            "What is the deposit growth by account type?",
            "Identify accounts at risk of closure",
        ],
        "recommendations": [
            "Monitor loan portfolio health by product type",
            "Track transaction patterns for fraud detection",
            "Review branch performance and resource allocation",
        ],
    },
    "manufacturing": {
        "display_name": "Manufacturing",
        "description": "Manufacturing analytics: production, machines, downtime, yield, quality",
        "entities": ["machine", "production", "downtime", "product_manufacturing"],
        "key_relationships": [
            "Machine â†’ Production â†’ Product â†’ Downtime â†’ Quality",
        ],
        "kpis": {
            "operational": [
                "total_production",
                "machine_utilization",
                "active_machines",
                "throughput",
            ],
            "quality": [
                "yield_rate",
                "defect_rate",
                "first_pass_yield",
                "scrap_rate",
            ],
            "maintenance": [
                "total_downtime",
                "mttr",
                "mtbf",
                "oee",
            ],
        },
        "business_rules": [
            "Machine utilization should be above 75%",
            "Yield rate should exceed 95%",
            "Downtime > 10% of operating time requires investigation",
            "OEE (Overall Equipment Effectiveness) target: 85%",
        ],
        "recommended_charts": ["line", "bar", "gauge", "heatmap", "scatter"],
        "report_templates": [
            "Production Performance Report",
            "Machine Utilization Analysis",
            "Downtime & Maintenance Report",
            "Quality Assessment Report",
        ],
        "alerts": [
            {
                "metric": "machine_utilization",
                "threshold": "<75",
                "severity": "warning",
                "message": "Low machine utilization",
            },
            {
                "metric": "downtime_rate",
                "threshold": ">10",
                "severity": "critical",
                "message": "Excessive downtime detected",
            },
            {
                "metric": "defect_rate",
                "threshold": ">5",
                "severity": "warning",
                "message": "High defect rate",
            },
        ],
        "ai_prompts": [
            "Analyze production trends by product line",
            "Which machines have the highest downtime?",
            "What is the yield rate by product category?",
            "Identify production bottlenecks",
        ],
        "recommendations": [
            "Monitor machine performance and schedule preventive maintenance",
            "Track yield rates by product line for quality improvement",
            "Analyze downtime causes to reduce unplanned stoppages",
        ],
    },
    "agriculture": {
        "display_name": "Agriculture",
        "description": "Agriculture analytics: farms, crops, harvest, livestock, weather",
        "entities": ["farm", "crop", "livestock", "weather"],
        "key_relationships": [
            "Farm â†’ Crop â†’ Harvest â†’ Weather â†’ Livestock",
        ],
        "kpis": {
            "operational": [
                "total_harvest",
                "farm_count",
                "yield_per_hectare",
                "livestock_count",
            ],
            "financial": [
                "harvest_value",
                "revenue_per_farm",
                "livestock_value",
                "input_cost",
            ],
            "environmental": [
                "total_rainfall",
                "avg_temperature",
                "frost_days",
                "dry_spells",
            ],
        },
        "business_rules": [
            "Yield per hectare should meet regional benchmark",
            "Livestock mortality rate should be below 5%",
            "Rainfall below 500mm season requires irrigation review",
            "Crop diversification should span at least 3 crop types",
        ],
        "recommended_charts": ["bar", "line", "pie", "heatmap", "scatter"],
        "report_templates": [
            "Harvest & Yield Report",
            "Farm Performance Analysis",
            "Livestock Health Report",
            "Weather Impact Assessment",
        ],
        "alerts": [
            {
                "metric": "livestock_mortality",
                "threshold": ">5",
                "severity": "critical",
                "message": "High livestock mortality",
            },
            {
                "metric": "rainfall",
                "threshold": "<500",
                "severity": "warning",
                "message": "Low rainfall â€” irrigation needed",
            },
            {
                "metric": "yield_decline",
                "threshold": ">15",
                "severity": "warning",
                "message": "Significant yield decline detected",
            },
        ],
        "ai_prompts": [
            "Analyze harvest yields by crop and farm",
            "Which farms have the highest yield per hectare?",
            "What is the livestock distribution by type?",
            "Correlate weather patterns with crop yields",
        ],
        "recommendations": [
            "Monitor yield trends by crop variety for optimization",
            "Track weather impact on harvest scheduling",
            "Review livestock health and mortality patterns",
        ],
    },
    "insurance": {
        "display_name": "Insurance",
        "description": "Insurance analytics: policies, claims, premiums, agents, coverage",
        "entities": ["policy", "claim", "agent"],
        "key_relationships": [
            "Agent â†’ Policy â†’ Claim â†’ Settlement â†’ Customer",
        ],
        "kpis": {
            "operational": [
                "total_policies",
                "active_policies",
                "claim_count",
                "agent_count",
            ],
            "financial": [
                "total_premium",
                "claim_amount",
                "loss_ratio",
                "commission_total",
            ],
            "quality": [
                "claim_approval_rate",
                "avg_processing_time",
                "renewal_rate",
                "customer_satisfaction",
            ],
        },
        "business_rules": [
            "Loss ratio should be below 70%",
            "Claim approval rate should be above 80%",
            "Policy renewal rate should exceed 85%",
            "Average claim processing time should be under 15 days",
        ],
        "recommended_charts": ["line", "bar", "pie", "gauge", "heatmap"],
        "report_templates": [
            "Insurance Portfolio Report",
            "Claims Analysis Report",
            "Premium & Revenue Report",
            "Agent Performance Report",
        ],
        "alerts": [
            {
                "metric": "loss_ratio",
                "threshold": ">70",
                "severity": "critical",
                "message": "High loss ratio",
            },
            {
                "metric": "claim_approval_rate",
                "threshold": "<80",
                "severity": "warning",
                "message": "Low claim approval rate",
            },
            {
                "metric": "renewal_rate",
                "threshold": "<85",
                "severity": "warning",
                "message": "Low policy renewal rate",
            },
        ],
        "ai_prompts": [
            "Analyze claim trends by policy type",
            "Which agents have the highest policy sales?",
            "What is the premium distribution by coverage type?",
            "Identify policies at risk of non-renewal",
        ],
        "recommendations": [
            "Monitor loss ratio by product line for pricing adjustments",
            "Track agent performance and commission patterns",
            "Review claim processing efficiency by category",
        ],
    },
    "hospitality": {
        "display_name": "Hospitality",
        "description": "Hospitality analytics: reservations, guests, rooms, revenue, services",
        "entities": ["reservation", "guest", "room", "service"],
        "key_relationships": [
            "Guest â†’ Reservation â†’ Room â†’ Service â†’ Revenue",
        ],
        "kpis": {
            "operational": [
                "total_reservations",
                "occupancy_rate",
                "total_guests",
                "available_rooms",
            ],
            "financial": [
                "room_revenue",
                "service_revenue",
                "adr",
                "revpar",
            ],
            "guest": [
                "repeat_guest_rate",
                "satisfaction_score",
                "avg_length_of_stay",
                "loyalty_enrollment",
            ],
        },
        "business_rules": [
            "Occupancy rate should be above 65%",
            "ADR (Average Daily Rate) should meet market benchmark",
            "Guest satisfaction should exceed 4.0/5",
            "Repeat guest rate should be above 30%",
        ],
        "recommended_charts": ["line", "bar", "pie", "heatmap", "gauge"],
        "report_templates": [
            "Hospitality Performance Report",
            "Occupancy & Revenue Analysis",
            "Guest Satisfaction Report",
            "Service Revenue Report",
        ],
        "alerts": [
            {
                "metric": "occupancy_rate",
                "threshold": "<65",
                "severity": "warning",
                "message": "Low occupancy rate",
            },
            {
                "metric": "satisfaction_score",
                "threshold": "<4.0",
                "severity": "warning",
                "message": "Guest satisfaction below target",
            },
            {
                "metric": "repeat_guest_rate",
                "threshold": "<30",
                "severity": "warning",
                "message": "Low repeat guest rate",
            },
        ],
        "ai_prompts": [
            "Analyze reservation trends by season",
            "Which room types generate the most revenue?",
            "What is the guest satisfaction by service category?",
            "Identify peak occupancy periods",
        ],
        "recommendations": [
            "Monitor occupancy patterns for pricing optimization",
            "Track guest satisfaction by service category",
            "Review repeat guest engagement strategies",
        ],
    },
    "telecommunications": {
        "display_name": "Telecommunications",
        "description": "Telecommunications analytics: subscribers, calls, data usage, plans, revenue",
        "entities": ["subscriber", "call", "data_usage", "plan"],
        "key_relationships": [
            "Subscriber â†’ Plan â†’ Call â†’ Data Usage â†’ Revenue",
        ],
        "kpis": {
            "operational": [
                "total_subscribers",
                "active_subscribers",
                "total_calls",
                "total_data_gb",
            ],
            "financial": [
                "arpu",
                "plan_revenue",
                "call_revenue",
                "overage_revenue",
            ],
            "network": [
                "churn_rate",
                "call_drop_rate",
                "avg_call_duration",
                "data_per_subscriber",
            ],
        },
        "business_rules": [
            "Churn rate should be below 3%",
            "ARPU should meet or exceed industry benchmark",
            "Call drop rate should be below 2%",
            "Data usage per subscriber should trend upward",
        ],
        "recommended_charts": ["line", "bar", "pie", "gauge", "heatmap"],
        "report_templates": [
            "Telecommunications Performance Report",
            "Subscriber Growth & Churn Report",
            "Revenue Analysis by Plan",
            "Network Usage Report",
        ],
        "alerts": [
            {
                "metric": "churn_rate",
                "threshold": ">3",
                "severity": "critical",
                "message": "High subscriber churn rate",
            },
            {
                "metric": "call_drop_rate",
                "threshold": ">2",
                "severity": "warning",
                "message": "High call drop rate",
            },
            {
                "metric": "arpu_decline",
                "threshold": ">10",
                "severity": "warning",
                "message": "ARPU declining significantly",
            },
        ],
        "ai_prompts": [
            "Analyze subscriber growth and churn trends",
            "Which plans generate the most revenue?",
            "What is the data usage pattern by subscriber segment?",
            "Identify subscribers at risk of churning",
        ],
        "recommendations": [
            "Monitor subscriber churn by plan and segment",
            "Track ARPU trends for pricing strategy",
            "Review network quality metrics for service improvement",
        ],
    },
}


def get_industry_knowledge(industry: str) -> dict | None:
    """Get knowledge base for a specific industry."""
    return INDUSTRY_KNOWLEDGE.get(industry)


def get_all_industries() -> dict[str, dict]:
    """Return all industry knowledge bases."""
    return INDUSTRY_KNOWLEDGE


def get_industry_kpis(industry: str) -> dict:
    """Get KPI definitions for an industry."""
    knowledge = INDUSTRY_KNOWLEDGE.get(industry, {})
    return knowledge.get("kpis", {})


def get_industry_alerts(industry: str) -> list[dict]:
    """Get alert definitions for an industry."""
    knowledge = INDUSTRY_KNOWLEDGE.get(industry, {})
    return knowledge.get("alerts", [])


def get_industry_prompts(industry: str) -> list[str]:
    """Get AI prompt suggestions for an industry."""
    knowledge = INDUSTRY_KNOWLEDGE.get(industry, {})
    return knowledge.get("ai_prompts", [])


def get_industry_recommendations(industry: str) -> list[str]:
    """Get recommendations for an industry."""
    knowledge = INDUSTRY_KNOWLEDGE.get(industry, {})
    return knowledge.get("recommendations", [])
