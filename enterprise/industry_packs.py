"""Industry Solution Packs — pre-built templates for multiple industries.

Each pack contains dashboard templates, KPI templates, ETL templates,
report templates, and AI prompt templates tailored to a specific industry.

Packs: SME, Education, Healthcare, Church, Government, NGO
"""

INDUSTRY_PACKS = {
    "sme": {
        "name": "SME Pack",
        "description": "Small-to-medium enterprise analytics covering sales, inventory, customers, profit, purchases, and cash flow.",
        "dashboards": [
            {
                "name": "Sales Dashboard",
                "description": "Track revenue, orders, average order value, and sales trends over time.",
                "widgets": [
                    {"type": "kpi_card", "title": "Total Revenue", "config": {"metric": "total_sales"}},
                    {"type": "kpi_card", "title": "Total Orders", "config": {"metric": "total_orders"}},
                    {"type": "kpi_card", "title": "Avg Order Value", "config": {"metric": "avg_order_value"}},
                    {"type": "line_chart", "title": "Revenue Over Time", "config": {"x": "order_date", "y": "sales"}},
                    {"type": "bar_chart", "title": "Revenue by Category", "config": {"x": "category", "y": "sales"}},
                    {"type": "bar_chart", "title": "Top Products", "config": {"x": "product_name", "y": "sales", "top_n": 10}},
                ],
            },
            {
                "name": "Inventory Dashboard",
                "description": "Monitor stock levels, reorder points, and inventory turnover.",
                "widgets": [
                    {"type": "kpi_card", "title": "Total SKUs", "config": {"metric": "sku_count"}},
                    {"type": "kpi_card", "title": "Low Stock Items", "config": {"metric": "low_stock_count"}},
                    {"type": "kpi_card", "title": "Inventory Value", "config": {"metric": "inventory_value"}},
                    {"type": "table", "title": "Low Stock Alerts", "config": {"filter": "stock < reorder_point"}},
                    {"type": "bar_chart", "title": "Stock by Category", "config": {"x": "category", "y": "stock_qty"}},
                ],
            },
            {
                "name": "Customer Dashboard",
                "description": "Customer segmentation, acquisition trends, and lifetime value.",
                "widgets": [
                    {"type": "kpi_card", "title": "Total Customers", "config": {"metric": "customer_count"}},
                    {"type": "kpi_card", "title": "New Customers (30d)", "config": {"metric": "new_customers_30d"}},
                    {"type": "kpi_card", "title": "Avg Customer LTV", "config": {"metric": "avg_ltv"}},
                    {"type": "pie_chart", "title": "Customer Segments", "config": {"group_by": "segment"}},
                    {"type": "line_chart", "title": "Customer Growth", "config": {"x": "month", "y": "cumulative_customers"}},
                ],
            },
            {
                "name": "Profit Dashboard",
                "description": "Profit margins, cost breakdown, and profitability by segment.",
                "widgets": [
                    {"type": "kpi_card", "title": "Total Profit", "config": {"metric": "total_profit"}},
                    {"type": "kpi_card", "title": "Profit Margin", "config": {"metric": "margin_pct"}},
                    {"type": "kpi_card", "title": "Top Profit Category", "config": {"metric": "top_profit_category"}},
                    {"type": "bar_chart", "title": "Profit by Region", "config": {"x": "region", "y": "profit"}},
                    {"type": "scatter_plot", "title": "Sales vs Profit", "config": {"x": "sales", "y": "profit"}},
                ],
            },
            {
                "name": "Purchase Analytics",
                "description": "Purchase orders, supplier performance, and procurement costs.",
                "widgets": [
                    {"type": "kpi_card", "title": "Total Purchases", "config": {"metric": "total_purchases"}},
                    {"type": "kpi_card", "title": "Active Suppliers", "config": {"metric": "supplier_count"}},
                    {"type": "bar_chart", "title": "Purchases by Supplier", "config": {"x": "supplier", "y": "amount"}},
                    {"type": "line_chart", "title": "Purchase Trend", "config": {"x": "month", "y": "amount"}},
                ],
            },
            {
                "name": "Cash Flow Dashboard",
                "description": "Cash inflows, outflows, and projected cash position.",
                "widgets": [
                    {"type": "kpi_card", "title": "Cash Inflow", "config": {"metric": "cash_inflow"}},
                    {"type": "kpi_card", "title": "Cash Outflow", "config": {"metric": "cash_outflow"}},
                    {"type": "kpi_card", "title": "Net Cash Flow", "config": {"metric": "net_cash_flow"}},
                    {"type": "line_chart", "title": "Cash Flow Trend", "config": {"x": "month", "y": "net"}},
                ],
            },
        ],
        "kpis": [
            {"name": "Monthly Revenue", "formula": "SUM(sales)", "category": "Sales", "target_value": 100000, "unit": "USD"},
            {"name": "Order Count", "formula": "COUNT(DISTINCT order_id)", "category": "Sales", "target_value": 500, "unit": "orders"},
            {"name": "Avg Order Value", "formula": "AVG(sales)", "category": "Sales", "target_value": 200, "unit": "USD"},
            {"name": "Profit Margin", "formula": "SUM(profit) / SUM(sales) * 100", "category": "Profitability", "target_value": 25, "unit": "%"},
            {"name": "Customer Count", "formula": "COUNT(DISTINCT customer_name)", "category": "Customers", "target_value": 1000, "unit": "customers"},
            {"name": "Inventory Turnover", "formula": "COGS / AVG(inventory_value)", "category": "Inventory", "target_value": 6, "unit": "ratio"},
        ],
        "etl_templates": [
            {"name": "Sales Data Import", "source_type": "csv", "description": "Import sales data from CSV with auto-mapping"},
            {"name": "Inventory Sync", "source_type": "api", "description": "Sync inventory levels from ERP API"},
            {"name": "Customer Import", "source_type": "excel", "description": "Import customer data from Excel spreadsheet"},
        ],
        "report_templates": [
            {"name": "Monthly Sales Report", "sections": ["summary", "revenue_trend", "top_products", "regional_breakdown"]},
            {"name": "Quarterly Profit Report", "sections": ["summary", "profit_margin", "cost_breakdown", "recommendations"]},
            {"name": "Customer Analysis Report", "sections": ["segments", "acquisition", "ltv", "churn_analysis"]},
        ],
        "ai_prompts": [
            {"name": "Sales Analyst", "prompt": "Analyze the sales data and identify top-performing products and regions."},
            {"name": "Inventory Advisor", "prompt": "Review inventory levels and suggest reorder quantities for low-stock items."},
            {"name": "Customer Insights", "prompt": "Segment customers based on purchase behavior and recommend retention strategies."},
        ],
    },
    "education": {
        "name": "Education Pack",
        "description": "Student performance, attendance, examinations, fee collection, and academic analytics for schools and universities.",
        "dashboards": [
            {"name": "Student Dashboard", "description": "Student enrollment, demographics, and performance overview.", "widgets": []},
            {"name": "Attendance Dashboard", "description": "Daily attendance rates, trends, and at-risk students.", "widgets": []},
            {"name": "Examination Dashboard", "description": "Exam results, grade distribution, and pass rates.", "widgets": []},
            {"name": "Fee Collection Dashboard", "description": "Fee collection status, outstanding balances, and payment trends.", "widgets": []},
            {"name": "Academic Performance Dashboard", "description": "GPA trends, subject-wise performance, and comparative analysis.", "widgets": []},
            {"name": "Lecturer Dashboard", "description": "Course load, student feedback, and teaching effectiveness metrics.", "widgets": []},
        ],
        "kpis": [
            {"name": "Enrollment Rate", "formula": "COUNT(enrolled_students)", "category": "Enrollment", "target_value": 500, "unit": "students"},
            {"name": "Attendance Rate", "formula": "AVG(attendance_pct)", "category": "Attendance", "target_value": 90, "unit": "%"},
            {"name": "Pass Rate", "formula": "COUNT(passed) / COUNT(total) * 100", "category": "Exams", "target_value": 85, "unit": "%"},
            {"name": "Fee Collection Rate", "formula": "SUM(collected) / SUM(billed) * 100", "category": "Finance", "target_value": 95, "unit": "%"},
            {"name": "Avg GPA", "formula": "AVG(gpa)", "category": "Performance", "target_value": 3.0, "unit": "GPA"},
        ],
        "etl_templates": [
            {"name": "Student Data Import", "source_type": "csv", "description": "Import student records from SIS export"},
            {"name": "Grade Import", "source_type": "excel", "description": "Import examination grades from spreadsheet"},
            {"name": "Attendance Sync", "source_type": "api", "description": "Sync attendance from biometric/API system"},
        ],
        "report_templates": [
            {"name": "Term Report", "sections": ["enrollment", "attendance", "exam_results", "recommendations"]},
            {"name": "Fee Collection Report", "sections": ["collected", "outstanding", "defaulters", "projections"]},
        ],
        "ai_prompts": [
            {"name": "Performance Analyst", "prompt": "Analyze student performance trends and identify at-risk students."},
            {"name": "Attendance Monitor", "prompt": "Review attendance patterns and flag students with concerning absence rates."},
        ],
    },
    "healthcare": {
        "name": "Healthcare Pack",
        "description": "Patient flow, laboratory, pharmacy, bed occupancy, appointments, and disease trend analytics for healthcare facilities.",
        "dashboards": [
            {"name": "Patient Dashboard", "description": "Patient demographics, admissions, and discharge summaries.", "widgets": []},
            {"name": "Laboratory Dashboard", "description": "Test volumes, turnaround times, and result distribution.", "widgets": []},
            {"name": "Pharmacy Dashboard", "description": "Prescription volumes, drug inventory, and dispensing trends.", "widgets": []},
            {"name": "Bed Occupancy Dashboard", "description": "Ward-wise bed occupancy, admission/discharge flow.", "widgets": []},
            {"name": "Appointment Dashboard", "description": "Appointment scheduling, no-show rates, and wait times.", "widgets": []},
            {"name": "Disease Trend Dashboard", "description": "Disease incidence, outbreak detection, and epidemiological trends.", "widgets": []},
        ],
        "kpis": [
            {"name": "Patient Satisfaction", "formula": "AVG(satisfaction_score)", "category": "Quality", "target_value": 4.5, "unit": "score"},
            {"name": "Bed Occupancy Rate", "formula": "occupied_beds / total_beds * 100", "category": "Operations", "target_value": 80, "unit": "%"},
            {"name": "Lab Turnaround Time", "formula": "AVG(result_time_hours)", "category": "Laboratory", "target_value": 4, "unit": "hours"},
            {"name": "Appointment No-Show Rate", "formula": "no_shows / total_appointments * 100", "category": "Appointments", "warning_threshold": 15, "unit": "%"},
            {"name": "Avg Wait Time", "formula": "AVG(wait_time_minutes)", "category": "Patient Experience", "target_value": 30, "unit": "minutes"},
        ],
        "etl_templates": [
            {"name": "Patient Records Import", "source_type": "csv", "description": "Import patient data from EHR export"},
            {"name": "Lab Results Import", "source_type": "excel", "description": "Import laboratory test results"},
            {"name": "Pharmacy Sync", "source_type": "api", "description": "Sync pharmacy dispensing data"},
        ],
        "report_templates": [
            {"name": "Monthly Operations Report", "sections": ["admissions", "occupancy", "lab_stats", "pharmacy", "appointments"]},
            {"name": "Patient Outcomes Report", "sections": ["satisfaction", "treatment_outcomes", "readmission_rates"]},
        ],
        "ai_prompts": [
            {"name": "Patient Flow Analyst", "prompt": "Analyze patient admission and discharge patterns to optimize bed allocation."},
            {"name": "Outbreak Detector", "prompt": "Review disease incidence data and flag potential outbreaks or concerning trends."},
        ],
    },
    "church": {
        "name": "Church Pack",
        "description": "Membership, attendance, giving, ministry, events, and outreach analytics for churches with multi-branch support.",
        "dashboards": [
            {"name": "Membership Dashboard", "description": "Member count, demographics, and growth trends across branches.", "widgets": []},
            {"name": "Attendance Dashboard", "description": "Service attendance by branch, service time, and trends.", "widgets": []},
            {"name": "Giving Dashboard", "description": "Tithes, offerings, special donations, and giving trends.", "widgets": []},
            {"name": "Ministry Dashboard", "description": "Ministry participation, volunteer engagement, and department metrics.", "widgets": []},
            {"name": "Event Dashboard", "description": "Event attendance, registration, and impact tracking.", "widgets": []},
            {"name": "Outreach Dashboard", "description": "Community outreach, conversions, and follow-up tracking.", "widgets": []},
        ],
        "kpis": [
            {"name": "Total Members", "formula": "COUNT(members)", "category": "Membership", "target_value": 500, "unit": "members"},
            {"name": "Avg Sunday Attendance", "formula": "AVG(attendance)", "category": "Attendance", "target_value": 300, "unit": "people"},
            {"name": "Monthly Giving", "formula": "SUM(donations)", "category": "Giving", "target_value": 50000, "unit": "USD"},
            {"name": "Volunteer Engagement", "formula": "active_volunteers / total_members * 100", "category": "Ministry", "target_value": 30, "unit": "%"},
            {"name": "Outreach Reach", "formula": "COUNT(outreach_contacts)", "category": "Outreach", "target_value": 100, "unit": "contacts"},
        ],
        "etl_templates": [
            {"name": "Member Data Import", "source_type": "csv", "description": "Import member records from church management system"},
            {"name": "Giving Import", "source_type": "excel", "description": "Import donation records from finance spreadsheet"},
            {"name": "Attendance Import", "source_type": "csv", "description": "Import attendance from check-in system"},
        ],
        "report_templates": [
            {"name": "Annual Church Report", "sections": ["membership", "attendance", "giving", "ministry", "outreach"]},
            {"name": "Branch Comparison Report", "sections": ["attendance_by_branch", "giving_by_branch", "growth_by_branch"]},
        ],
        "ai_prompts": [
            {"name": "Membership Analyst", "prompt": "Analyze membership growth trends and identify branches with growth opportunities."},
            {"name": "Giving Advisor", "prompt": "Review giving patterns and suggest strategies for increasing consistent giving."},
        ],
    },
    "government": {
        "name": "Government Pack",
        "description": "Revenue, budget, project monitoring, service delivery, and procurement analytics for government agencies.",
        "dashboards": [
            {"name": "Revenue Dashboard", "description": "Tax collection, revenue sources, and collection efficiency.", "widgets": []},
            {"name": "Budget Dashboard", "description": "Budget allocation, utilization, and variance analysis.", "widgets": []},
            {"name": "Project Monitoring Dashboard", "description": "Project status, milestones, budget utilization, and delays.", "widgets": []},
            {"name": "Service Delivery Dashboard", "description": "Service requests, processing times, and citizen satisfaction.", "widgets": []},
            {"name": "Procurement Dashboard", "description": "Procurement contracts, vendor performance, and spending analysis.", "widgets": []},
        ],
        "kpis": [
            {"name": "Revenue Collection Rate", "formula": "collected / target * 100", "category": "Revenue", "target_value": 95, "unit": "%"},
            {"name": "Budget Utilization", "formula": "spent / allocated * 100", "category": "Budget", "warning_threshold": 90, "unit": "%"},
            {"name": "Project Completion Rate", "formula": "completed / total * 100", "category": "Projects", "target_value": 80, "unit": "%"},
            {"name": "Avg Service Time", "formula": "AVG(processing_days)", "category": "Service Delivery", "target_value": 5, "unit": "days"},
            {"name": "Procurement Compliance", "formula": "compliant_contracts / total_contracts * 100", "category": "Procurement", "target_value": 100, "unit": "%"},
        ],
        "etl_templates": [
            {"name": "Revenue Data Import", "source_type": "csv", "description": "Import revenue collection data from financial system"},
            {"name": "Budget Import", "source_type": "excel", "description": "Import budget allocation and expenditure data"},
            {"name": "Project Status Sync", "source_type": "api", "description": "Sync project status from PMIS"},
        ],
        "report_templates": [
            {"name": "Quarterly Performance Report", "sections": ["revenue", "budget", "projects", "service_delivery"]},
            {"name": "Annual Accountability Report", "sections": ["financials", "projects", "procurement", "citizen_feedback"]},
        ],
        "ai_prompts": [
            {"name": "Budget Analyst", "prompt": "Analyze budget utilization across departments and flag overruns or underutilization."},
            {"name": "Project Monitor", "prompt": "Review project timelines and identify at-risk projects with potential delays."},
        ],
    },
    "ngo": {
        "name": "NGO Pack",
        "description": "Donor, project, beneficiary, grant, and monitoring & evaluation analytics for non-governmental organizations.",
        "dashboards": [
            {"name": "Donor Dashboard", "description": "Donor count, contribution trends, donor retention, and top donors.", "widgets": []},
            {"name": "Project Dashboard", "description": "Active projects, funding status, and impact metrics.", "widgets": []},
            {"name": "Beneficiary Dashboard", "description": "Beneficiary count, demographics, and service delivery coverage.", "widgets": []},
            {"name": "Grant Dashboard", "description": "Grant awards, utilization, reporting deadlines, and compliance.", "widgets": []},
            {"name": "Monitoring & Evaluation Dashboard", "description": "Outcome indicators, impact assessment, and program effectiveness.", "widgets": []},
        ],
        "kpis": [
            {"name": "Total Donors", "formula": "COUNT(donors)", "category": "Donors", "target_value": 200, "unit": "donors"},
            {"name": "Donor Retention Rate", "formula": "returning_donors / total_donors * 100", "category": "Donors", "target_value": 70, "unit": "%"},
            {"name": "Beneficiaries Reached", "formula": "COUNT(beneficiaries)", "category": "Impact", "target_value": 5000, "unit": "people"},
            {"name": "Grant Utilization", "formula": "spent / awarded * 100", "category": "Grants", "target_value": 90, "unit": "%"},
            {"name": "Program Effectiveness", "formula": "outcomes_achieved / outcomes_planned * 100", "category": "M&E", "target_value": 85, "unit": "%"},
        ],
        "etl_templates": [
            {"name": "Donor Data Import", "source_type": "csv", "description": "Import donor records from CRM export"},
            {"name": "Beneficiary Import", "source_type": "excel", "description": "Import beneficiary registration data"},
            {"name": "Grant Data Sync", "source_type": "api", "description": "Sync grant status from grant management system"},
        ],
        "report_templates": [
            {"name": "Donor Impact Report", "sections": ["donations", "projects_funded", "beneficiaries_reached", "outcomes"]},
            {"name": "Grant Compliance Report", "sections": ["utilization", "milestones", "reporting_status", "compliance"]},
            {"name": "Annual Impact Report", "sections": ["programs", "beneficiaries", "outcomes", "financials", "stories"]},
        ],
        "ai_prompts": [
            {"name": "Donor Insights", "prompt": "Analyze donor patterns and suggest strategies for improving donor retention and acquisition."},
            {"name": "Impact Analyst", "prompt": "Review program outcomes and assess effectiveness against targets. Recommend improvements."},
        ],
    },
}


def get_pack_names() -> list[str]:
    """Return list of available industry pack identifiers."""
    return list(INDUSTRY_PACKS.keys())


def get_pack(pack_name: str) -> dict | None:
    """Get a specific industry pack by name."""
    return INDUSTRY_PACKS.get(pack_name)


def get_all_packs() -> dict:
    """Return all industry packs."""
    return INDUSTRY_PACKS
