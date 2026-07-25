"""MODULE 4 — Business Entity Library.

Reusable business entities per industry. Each entity has:
  - name, display_name, industry
  - synonyms (alternative column names)
  - attributes (expected columns)
  - kpis (KPI definitions)
  - relationships (to other entities)
"""

from __future__ import annotations

from semantic.extra_industries import EXTRA_ENTITIES

ENTITY_LIBRARY: dict[str, dict] = {
    # ── Healthcare ──
    "patient": {
        "display_name": "Patient",
        "industry": "healthcare",
        "weight": 3.0,
        "synonyms": [
            "patient_id",
            "patient_name",
            "patient_no",
            "patient_code",
            "medical_record_number",
            "mrn",
        ],
        "attributes": [
            "patient_id",
            "patient_name",
            "age",
            "gender",
            "diagnosis",
            "admission_date",
        ],
        "kpis": [
            "admissions",
            "discharges",
            "average_stay",
            "readmissions",
            "mortality_rate",
            "bed_occupancy",
        ],
        "relationships": [
            {"target": "admission", "type": "has_many", "label": "admissions"},
            {"target": "doctor", "type": "attended_by", "label": "attending doctor"},
            {"target": "diagnosis", "type": "has", "label": "diagnoses"},
            {"target": "billing", "type": "has", "label": "billing records"},
        ],
    },
    "doctor": {
        "display_name": "Doctor",
        "industry": "healthcare",
        "weight": 2.5,
        "synonyms": ["doctor_id", "doctor_name", "physician", "physician_name", "consultant"],
        "attributes": ["doctor_id", "doctor_name", "specialization", "department"],
        "kpis": ["patient_count", "consultations", "procedures", "revenue_generated"],
        "relationships": [
            {"target": "patient", "type": "treats", "label": "patients"},
            {"target": "ward", "type": "assigned_to", "label": "ward"},
        ],
    },
    "admission": {
        "display_name": "Admission",
        "industry": "healthcare",
        "weight": 2.5,
        "synonyms": ["admission_id", "admission_date", "admission_record", "hospitalization"],
        "attributes": [
            "admission_id",
            "patient_id",
            "admission_date",
            "discharge_date",
            "ward",
            "doctor",
        ],
        "kpis": ["total_admissions", "average_stay", "bed_occupancy_rate", "readmission_rate"],
        "relationships": [
            {"target": "patient", "type": "belongs_to", "label": "patient"},
            {"target": "ward", "type": "in", "label": "ward"},
            {"target": "doctor", "type": "attended_by", "label": "doctor"},
        ],
    },
    "ward": {
        "display_name": "Ward",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": ["ward", "ward_name", "hospital_unit", "hospital_ward"],
        "attributes": ["ward_id", "ward_name", "bed_count", "occupancy"],
        "kpis": ["bed_occupancy", "patient_count", "staff_count"],
        "relationships": [
            {"target": "admission", "type": "has_many", "label": "admissions"},
            {"target": "doctor", "type": "has_many", "label": "doctors"},
        ],
    },
    "diagnosis": {
        "display_name": "Diagnosis",
        "industry": "healthcare",
        "weight": 3.0,
        "synonyms": ["diagnosis", "condition", "disease", "icd_code", "diagnosis_code"],
        "attributes": ["diagnosis_code", "diagnosis_name", "severity"],
        "kpis": ["frequency", "mortality_rate", "treatment_success_rate"],
        "relationships": [
            {"target": "patient", "type": "diagnosed_in", "label": "patients"},
        ],
    },
    "medicine": {
        "display_name": "Medicine",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": ["medicine", "medication", "drug", "prescription", "pharmacy"],
        "attributes": ["medicine_id", "medicine_name", "dosage", "stock"],
        "kpis": ["prescription_count", "stock_level", "expiry_alerts"],
        "relationships": [
            {"target": "patient", "type": "prescribed_to", "label": "patients"},
        ],
    },
    "lab_test": {
        "display_name": "Laboratory Test",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": ["lab_test", "laboratory", "lab_result", "test_name"],
        "attributes": ["test_id", "test_name", "result", "patient_id"],
        "kpis": ["test_count", "abnormal_rate", "turnaround_time"],
        "relationships": [
            {"target": "patient", "type": "for", "label": "patient"},
        ],
    },
    "appointment": {
        "display_name": "Appointment",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": ["appointment", "appointment_date", "appointment_id"],
        "attributes": ["appointment_id", "patient_id", "doctor_id", "appointment_date", "status"],
        "kpis": ["total_appointments", "no_show_rate", "cancellation_rate"],
        "relationships": [
            {"target": "patient", "type": "belongs_to", "label": "patient"},
            {"target": "doctor", "type": "with", "label": "doctor"},
        ],
    },
    "insurance": {
        "display_name": "Insurance",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": ["insurance", "insurance_type", "insurance_provider", "payer"],
        "attributes": ["insurance_id", "provider", "coverage_type", "patient_id"],
        "kpis": ["claim_count", "approval_rate", "average_claim", "denial_rate"],
        "relationships": [
            {"target": "patient", "type": "covers", "label": "patient"},
            {"target": "billing", "type": "pays_for", "label": "billing"},
        ],
    },
    "billing": {
        "display_name": "Billing",
        "industry": "healthcare",
        "weight": 2.0,
        "synonyms": [
            "billing",
            "billing_amount",
            "hospital_bill",
            "hospital_charge",
        ],
        "attributes": ["bill_id", "patient_id", "amount", "insurance_id", "status"],
        "kpis": ["total_revenue", "outstanding_amount", "collection_rate", "average_bill"],
        "relationships": [
            {"target": "patient", "type": "belongs_to", "label": "patient"},
            {"target": "insurance", "type": "covered_by", "label": "insurance"},
        ],
    },
    # ── Education ──
    "student": {
        "display_name": "Student",
        "industry": "education",
        "weight": 3.0,
        "synonyms": [
            "student_id",
            "student_name",
            "student_no",
            "student_number",
            "enrollment_id",
            "pupil",
        ],
        "attributes": ["student_id", "student_name", "grade", "department", "enrollment_date"],
        "kpis": ["enrollment_count", "attendance_rate", "pass_rate", "dropout_rate", "gpa_average"],
        "relationships": [
            {"target": "course", "type": "enrolled_in", "label": "courses"},
            {"target": "department", "type": "belongs_to", "label": "department"},
            {"target": "grade", "type": "has", "label": "grades"},
            {"target": "attendance", "type": "has", "label": "attendance"},
        ],
    },
    "teacher": {
        "display_name": "Teacher",
        "industry": "education",
        "weight": 2.5,
        "synonyms": [
            "teacher_id",
            "teacher_name",
            "instructor",
            "professor",
            "lecturer",
            "faculty_member",
        ],
        "attributes": ["teacher_id", "teacher_name", "department", "subject"],
        "kpis": ["course_count", "student_count", "evaluation_score"],
        "relationships": [
            {"target": "course", "type": "teaches", "label": "courses"},
            {"target": "department", "type": "belongs_to", "label": "department"},
        ],
    },
    "course": {
        "display_name": "Course",
        "industry": "education",
        "weight": 2.5,
        "synonyms": ["course", "course_id", "course_name", "subject", "module"],
        "attributes": ["course_id", "course_name", "credits", "department", "teacher_id"],
        "kpis": ["enrollment_count", "pass_rate", "average_grade", "completion_rate"],
        "relationships": [
            {"target": "student", "type": "has_many", "label": "students"},
            {"target": "teacher", "type": "taught_by", "label": "teacher"},
            {"target": "department", "type": "belongs_to", "label": "department"},
        ],
    },
    "department_edu": {
        "display_name": "Department",
        "industry": "education",
        "weight": 2.0,
        "synonyms": ["faculty", "academic_department", "edu_department", "school"],
        "attributes": ["department_id", "department_name", "head", "budget"],
        "kpis": ["student_count", "teacher_count", "course_count", "budget_utilization"],
        "relationships": [
            {"target": "student", "type": "has_many", "label": "students"},
            {"target": "teacher", "type": "has_many", "label": "teachers"},
            {"target": "course", "type": "offers", "label": "courses"},
        ],
    },
    "semester": {
        "display_name": "Semester",
        "industry": "education",
        "weight": 2.0,
        "synonyms": ["semester", "term", "academic_year", "semester_id"],
        "attributes": ["semester_id", "semester_name", "start_date", "end_date"],
        "kpis": ["enrollment_count", "revenue", "course_offered"],
        "relationships": [
            {"target": "course", "type": "has_many", "label": "courses"},
        ],
    },
    "attendance": {
        "display_name": "Attendance",
        "industry": "education",
        "weight": 2.5,
        "synonyms": ["attendance", "attendance_date", "attendance_record"],
        "attributes": ["student_id", "date", "status", "course_id"],
        "kpis": ["attendance_rate", "absenteeism_rate", "late_rate"],
        "relationships": [
            {"target": "student", "type": "belongs_to", "label": "student"},
            {"target": "course", "type": "for", "label": "course"},
        ],
    },
    "exam": {
        "display_name": "Exam",
        "industry": "education",
        "weight": 2.5,
        "synonyms": ["exam", "exam_id", "assessment", "examination"],
        "attributes": ["exam_id", "course_id", "exam_date", "max_score"],
        "kpis": ["average_score", "pass_rate", "top_scorer"],
        "relationships": [
            {"target": "course", "type": "belongs_to", "label": "course"},
            {"target": "grade", "type": "produces", "label": "grades"},
        ],
    },
    "grade": {
        "display_name": "Grade",
        "industry": "education",
        "weight": 3.0,
        "synonyms": ["grade", "score", "marks", "result", "gpa", "cgpa"],
        "attributes": ["student_id", "course_id", "grade", "score"],
        "kpis": ["average_grade", "pass_rate", "distinction_rate", "failure_rate"],
        "relationships": [
            {"target": "student", "type": "belongs_to", "label": "student"},
            {"target": "course", "type": "for", "label": "course"},
            {"target": "exam", "type": "from", "label": "exam"},
        ],
    },
    "graduation": {
        "display_name": "Graduation",
        "industry": "education",
        "weight": 2.0,
        "synonyms": [
            "graduation",
            "graduation_rate",
            "graduated",
            "completion_rate",
            "completion",
            "graduate",
        ],
        "attributes": ["student_id", "graduation_date", "graduation_rate"],
        "kpis": ["graduation_rate", "completion_rate", "on_time_graduation"],
        "relationships": [
            {"target": "student", "type": "achieved_by", "label": "student"},
            {"target": "course", "type": "for", "label": "course"},
        ],
    },
    # ── Church ──
    "member": {
        "display_name": "Member",
        "industry": "church",
        "weight": 3.0,
        "synonyms": ["member", "member_id", "member_name", "member_no", "congregant"],
        "attributes": ["member_id", "member_name", "join_date", "branch", "ministry"],
        "kpis": ["total_members", "new_members", "active_members", "retention_rate"],
        "relationships": [
            {"target": "branch", "type": "belongs_to", "label": "branch"},
            {"target": "ministry", "type": "serves_in", "label": "ministry"},
            {"target": "giving", "type": "contributes", "label": "giving"},
            {"target": "attendance_church", "type": "has", "label": "attendance"},
        ],
    },
    "visitor": {
        "display_name": "Visitor",
        "industry": "church",
        "weight": 2.0,
        "synonyms": ["visitor", "first_timer", "newcomer"],
        "attributes": ["visitor_id", "visitor_name", "visit_date", "invited_by"],
        "kpis": ["visitor_count", "conversion_rate", "retention_rate"],
        "relationships": [
            {"target": "event", "type": "attended", "label": "event"},
        ],
    },
    "ministry": {
        "display_name": "Ministry",
        "industry": "church",
        "weight": 2.0,
        "synonyms": ["ministry", "fellowship", "ministry_name"],
        "attributes": ["ministry_id", "ministry_name", "leader", "member_count"],
        "kpis": ["member_count", "activity_count", "growth_rate"],
        "relationships": [
            {"target": "member", "type": "has_many", "label": "members"},
        ],
    },
    "pastor": {
        "display_name": "Pastor",
        "industry": "church",
        "weight": 2.5,
        "synonyms": ["pastor", "pastor_name", "reverend", "minister", "clergy"],
        "attributes": ["pastor_id", "pastor_name", "branch", "role"],
        "kpis": ["sermon_count", "counseling_count", "baptism_count"],
        "relationships": [
            {"target": "branch", "type": "leads", "label": "branch"},
            {"target": "member", "type": "shepherds", "label": "members"},
        ],
    },
    "offering": {
        "display_name": "Offering",
        "industry": "church",
        "weight": 2.5,
        "synonyms": [
            "offering",
            "offering_amount",
            "giving",
            "tithe",
            "pledge",
        ],
        "attributes": ["offering_id", "member_id", "amount", "date", "type"],
        "kpis": ["total_offering", "average_offering", "giving_rate", "tithe_compliance"],
        "relationships": [
            {"target": "member", "type": "from", "label": "member"},
            {"target": "event", "type": "during", "label": "event"},
        ],
    },
    "tithe": {
        "display_name": "Tithe",
        "industry": "church",
        "weight": 3.0,
        "synonyms": ["tithe", "tithe_amount", "tithes", "tenth"],
        "attributes": ["member_id", "amount", "date"],
        "kpis": ["total_tithe", "tithe_compliance_rate", "average_tithe"],
        "relationships": [
            {"target": "member", "type": "from", "label": "member"},
        ],
    },
    "branch_church": {
        "display_name": "Branch",
        "industry": "church",
        "weight": 2.0,
        "synonyms": ["branch", "branch_name", "campus", "church_branch", "parish"],
        "attributes": ["branch_id", "branch_name", "location", "pastor_id"],
        "kpis": ["member_count", "offering_total", "attendance_rate", "growth_rate"],
        "relationships": [
            {"target": "member", "type": "has_many", "label": "members"},
            {"target": "pastor", "type": "led_by", "label": "pastor"},
        ],
    },
    "event": {
        "display_name": "Event",
        "industry": "church",
        "weight": 2.0,
        "synonyms": ["event", "event_name", "church_service", "event_type"],
        "attributes": ["event_id", "event_name", "event_date", "branch_id", "attendance_count"],
        "kpis": ["total_events", "average_attendance", "offering_per_event"],
        "relationships": [
            {"target": "branch", "type": "at", "label": "branch"},
            {"target": "offering", "type": "generates", "label": "offerings"},
        ],
    },
    # ── Retail / SME ──
    "customer": {
        "display_name": "Customer",
        "industry": "universal",
        "synonyms": ["customer", "customer_id", "customer_name", "client", "buyer"],
        "attributes": ["customer_id", "customer_name", "email", "phone", "region"],
        "kpis": ["total_customers", "new_customers", "retention_rate", "avg_customer_value"],
        "relationships": [
            {"target": "order", "type": "places", "label": "orders"},
        ],
    },
    "order": {
        "display_name": "Order",
        "industry": "retail",
        "weight": 2.5,
        "synonyms": ["order", "order_id", "order_number", "purchase", "sale"],
        "attributes": ["order_id", "customer_id", "order_date", "amount", "status"],
        "kpis": ["total_orders", "avg_order_value", "order_growth", "conversion_rate"],
        "relationships": [
            {"target": "customer", "type": "belongs_to", "label": "customer"},
            {"target": "product", "type": "contains", "label": "products"},
            {"target": "invoice", "type": "generates", "label": "invoice"},
        ],
    },
    "invoice": {
        "display_name": "Invoice",
        "industry": "retail",
        "weight": 2.0,
        "synonyms": ["invoice", "invoice_id", "invoice_number", "receipt"],
        "attributes": ["invoice_id", "order_id", "amount", "date", "status"],
        "kpis": ["total_invoiced", "outstanding", "collection_rate", "avg_invoice"],
        "relationships": [
            {"target": "order", "type": "for", "label": "order"},
        ],
    },
    "product": {
        "display_name": "Product",
        "industry": "universal",
        "synonyms": ["product", "product_id", "product_name", "item", "item_name", "sku"],
        "attributes": ["product_id", "product_name", "category", "price", "cost"],
        "kpis": ["total_products", "top_selling", "profit_margin", "stock_turnover"],
        "relationships": [
            {"target": "order", "type": "ordered_in", "label": "orders"},
            {"target": "supplier", "type": "supplied_by", "label": "supplier"},
            {"target": "inventory", "type": "has", "label": "inventory"},
        ],
    },
    "supplier": {
        "display_name": "Supplier",
        "industry": "retail",
        "weight": 2.0,
        "synonyms": ["supplier", "supplier_id", "supplier_name", "vendor", "vendor_name"],
        "attributes": ["supplier_id", "supplier_name", "contact", "lead_time"],
        "kpis": ["supplier_count", "on_time_delivery", "quality_score"],
        "relationships": [
            {"target": "product", "type": "supplies", "label": "products"},
        ],
    },
    "warehouse": {
        "display_name": "Warehouse",
        "industry": "retail",
        "weight": 2.0,
        "synonyms": ["warehouse", "warehouse_id", "store", "facility"],
        "attributes": ["warehouse_id", "location", "capacity"],
        "kpis": ["utilization", "throughput", "stock_accuracy"],
        "relationships": [
            {"target": "inventory", "type": "stores", "label": "inventory"},
        ],
    },
    "inventory": {
        "display_name": "Inventory",
        "industry": "retail",
        "weight": 2.0,
        "synonyms": ["inventory", "stock", "stock_level", "on_hand"],
        "attributes": ["product_id", "warehouse_id", "quantity", "reorder_level"],
        "kpis": ["stock_value", "turnover_rate", "stockout_rate", "aging_stock"],
        "relationships": [
            {"target": "product", "type": "for", "label": "product"},
            {"target": "warehouse", "type": "in", "label": "warehouse"},
        ],
    },
    # ── Government ──
    "citizen": {
        "display_name": "Citizen",
        "industry": "government",
        "weight": 2.5,
        "synonyms": ["citizen", "citizen_id", "national_id", "ssn", "taxpayer"],
        "attributes": ["citizen_id", "name", "dob", "region", "status"],
        "kpis": ["population", "demographics", "employment_rate"],
        "relationships": [
            {"target": "project_gov", "type": "beneficiary_of", "label": "projects"},
        ],
    },
    "department_gov": {
        "display_name": "Department",
        "industry": "government",
        "weight": 2.0,
        "synonyms": ["agency", "bureau", "directorate", "government_department", "gov_dept"],
        "attributes": ["department_id", "department_name", "budget", "head"],
        "kpis": ["budget_utilization", "project_count", "staff_count", "efficiency_score"],
        "relationships": [
            {"target": "project_gov", "type": "executes", "label": "projects"},
            {"target": "budget_gov", "type": "manages", "label": "budget"},
        ],
    },
    "project_gov": {
        "display_name": "Project",
        "industry": "government",
        "weight": 2.5,
        "synonyms": ["project", "project_id", "project_name", "initiative", "scheme"],
        "attributes": [
            "project_id",
            "project_name",
            "department_id",
            "budget",
            "status",
            "start_date",
            "end_date",
        ],
        "kpis": ["total_projects", "completion_rate", "budget_utilization", "delay_rate"],
        "relationships": [
            {"target": "department_gov", "type": "belongs_to", "label": "department"},
            {"target": "contractor", "type": "executed_by", "label": "contractor"},
            {"target": "budget_gov", "type": "funded_by", "label": "budget"},
        ],
    },
    "budget_gov": {
        "display_name": "Budget",
        "industry": "government",
        "weight": 2.5,
        "synonyms": ["budget", "budget_id", "allocation", "appropriation", "fiscal"],
        "attributes": ["budget_id", "department_id", "allocated", "spent", "fiscal_year"],
        "kpis": ["total_budget", "utilization_rate", "variance", "deficit"],
        "relationships": [
            {"target": "department_gov", "type": "for", "label": "department"},
            {"target": "project_gov", "type": "funds", "label": "projects"},
        ],
    },
    "procurement": {
        "display_name": "Procurement",
        "industry": "government",
        "weight": 2.5,
        "synonyms": ["procurement", "tender", "purchase_order", "rfq", "bid"],
        "attributes": ["procurement_id", "project_id", "contractor_id", "amount", "status"],
        "kpis": ["total_procurement", "avg_contract", "competition_rate", "savings"],
        "relationships": [
            {"target": "project_gov", "type": "for", "label": "project"},
            {"target": "contractor", "type": "awarded_to", "label": "contractor"},
        ],
    },
    "contractor": {
        "display_name": "Contractor",
        "industry": "government",
        "weight": 2.0,
        "synonyms": [
            "contractor",
            "contractor_id",
            "contractor_name",
        ],
        "attributes": ["contractor_id", "contractor_name", "registration", "rating"],
        "kpis": ["contract_count", "total_value", "performance_score", "on_time_rate"],
        "relationships": [
            {"target": "procurement", "type": "wins", "label": "contracts"},
            {"target": "project_gov", "type": "executes", "label": "projects"},
        ],
    },
    "revenue_gov": {
        "display_name": "Revenue",
        "industry": "government",
        "weight": 2.0,
        "synonyms": ["tax_revenue", "collection", "levy", "duties"],
        "attributes": ["revenue_id", "source", "amount", "fiscal_year", "department_id"],
        "kpis": ["total_revenue", "collection_rate", "growth_rate", "per_capita"],
        "relationships": [
            {"target": "department_gov", "type": "collected_by", "label": "department"},
        ],
    },
    "asset_gov": {
        "display_name": "Asset",
        "industry": "government",
        "weight": 2.0,
        "synonyms": ["asset", "asset_value", "asset_type", "infrastructure"],
        "attributes": ["asset_id", "asset_type", "value", "department_id", "status"],
        "kpis": ["total_asset_value", "asset_count", "asset_utilization", "maintenance_cost"],
        "relationships": [
            {"target": "department_gov", "type": "owned_by", "label": "department"},
        ],
    },
    # ── NGO ──
    "beneficiary": {
        "display_name": "Beneficiary",
        "industry": "ngo",
        "weight": 3.0,
        "synonyms": [
            "beneficiary",
            "beneficiary_id",
            "recipient",
            "beneficiary_name",
            "aid_recipient",
        ],
        "attributes": ["beneficiary_id", "name", "location", "program_id", "status"],
        "kpis": ["total_beneficiaries", "reached", "satisfaction_rate", "coverage_rate"],
        "relationships": [
            {"target": "program", "type": "enrolled_in", "label": "programs"},
            {"target": "project_ngo", "type": "benefits_from", "label": "projects"},
        ],
    },
    "grant": {
        "display_name": "Grant",
        "industry": "ngo",
        "weight": 2.5,
        "synonyms": ["grant", "grant_id", "grant_name", "subsidy", "award"],
        "attributes": ["grant_id", "donor_id", "amount", "start_date", "end_date", "status"],
        "kpis": ["total_grants", "utilization_rate", "success_rate", "avg_grant"],
        "relationships": [
            {"target": "donor", "type": "from", "label": "donor"},
            {"target": "program", "type": "funds", "label": "programs"},
        ],
    },
    "donor": {
        "display_name": "Donor",
        "industry": "ngo",
        "weight": 2.5,
        "synonyms": ["donor", "donor_id", "donor_name", "contributor", "sponsor", "funder"],
        "attributes": ["donor_id", "donor_name", "type", "total_given", "contact"],
        "kpis": ["total_donors", "retention_rate", "avg_donation", "lifetime_value"],
        "relationships": [
            {"target": "grant", "type": "provides", "label": "grants"},
            {"target": "donation", "type": "makes", "label": "donations"},
        ],
    },
    "program": {
        "display_name": "Program",
        "industry": "ngo",
        "weight": 2.0,
        "synonyms": [
            "program",
            "program_id",
            "program_name",
            "intervention",
            "activity",
        ],
        "attributes": ["program_id", "program_name", "start_date", "end_date", "budget", "status"],
        "kpis": ["beneficiary_count", "budget_utilization", "impact_score", "completion_rate"],
        "relationships": [
            {"target": "beneficiary", "type": "serves", "label": "beneficiaries"},
            {"target": "grant", "type": "funded_by", "label": "grants"},
            {"target": "project_ngo", "type": "contains", "label": "projects"},
        ],
    },
    "project_ngo": {
        "display_name": "Project",
        "industry": "ngo",
        "weight": 2.0,
        "synonyms": ["field_project", "ngo_project", "relief_project", "community_project"],
        "attributes": ["project_id", "project_name", "program_id", "location", "budget", "status"],
        "kpis": ["total_projects", "completion_rate", "budget_utilization", "beneficiary_reach"],
        "relationships": [
            {"target": "program", "type": "belongs_to", "label": "program"},
            {"target": "beneficiary", "type": "serves", "label": "beneficiaries"},
        ],
    },
    "donation": {
        "display_name": "Donation",
        "industry": "ngo",
        "weight": 2.5,
        "synonyms": ["donation", "donation_id", "pledge", "funding_source"],
        "attributes": ["donation_id", "donor_id", "amount", "date", "type", "program_id"],
        "kpis": ["total_donations", "avg_donation", "growth_rate", "donor_retention"],
        "relationships": [
            {"target": "donor", "type": "from", "label": "donor"},
            {"target": "program", "type": "for", "label": "program"},
        ],
    },
    # ── Manufacturing ──
    "machine": {
        "display_name": "Machine",
        "industry": "manufacturing",
        "weight": 3.0,
        "synonyms": [
            "machine",
            "machine_id",
            "machine_name",
            "equipment",
            "equipment_id",
        ],
        "attributes": ["machine_id", "machine_name", "line", "status"],
        "kpis": ["machine_count", "utilization_rate", "availability_rate", "downtime_hours"],
        "relationships": [
            {"target": "production", "type": "produces", "label": "production"},
        ],
    },
    "production": {
        "display_name": "Production",
        "industry": "manufacturing",
        "weight": 2.5,
        "synonyms": [
            "production",
            "production_id",
            "production_record",
            "output_quantity",
            "units_produced",
            "batch",
        ],
        "attributes": ["production_id", "machine_id", "product_id", "quantity", "date"],
        "kpis": ["total_production", "production_rate", "yield_rate", "throughput"],
        "relationships": [
            {"target": "machine", "type": "produced_by", "label": "machine"},
            {"target": "product", "type": "produces", "label": "product"},
        ],
    },
    "downtime": {
        "display_name": "Downtime",
        "industry": "manufacturing",
        "weight": 2.5,
        "synonyms": ["downtime", "downtime_id", "stoppage", "breakdown", "unplanned_downtime"],
        "attributes": ["downtime_id", "machine_id", "start_time", "end_time", "reason"],
        "kpis": ["total_downtime", "downtime_frequency", "mttr", "mtbf"],
        "relationships": [
            {"target": "machine", "type": "affects", "label": "machine"},
        ],
    },
    "product_manufacturing": {
        "display_name": "Product",
        "industry": "manufacturing",
        "weight": 2.0,
        "synonyms": ["manufactured_product", "finished_good", "assembly", "component_part"],
        "attributes": ["product_id", "product_name", "unit_cost", "target_yield"],
        "kpis": ["product_count", "yield_rate", "defect_rate", "cost_per_unit"],
        "relationships": [
            {"target": "production", "type": "produced_in", "label": "production"},
        ],
    },
    # ── Agriculture ──
    "farm": {
        "display_name": "Farm",
        "industry": "agriculture",
        "weight": 3.0,
        "synonyms": ["farm", "farm_id", "farm_name", "plot", "field", "parcel"],
        "attributes": ["farm_id", "farm_name", "location", "size_hectares"],
        "kpis": ["farm_count", "total_hectares", "yield_per_hectare"],
        "relationships": [
            {"target": "crop", "type": "grows", "label": "crops"},
            {"target": "livestock", "type": "raises", "label": "livestock"},
        ],
    },
    "crop": {
        "display_name": "Crop",
        "industry": "agriculture",
        "weight": 3.0,
        "synonyms": ["crop", "crop_id", "crop_name", "cultivar"],
        "attributes": ["crop_id", "crop_name", "farm_id", "planting_date", "harvest_date"],
        "kpis": ["total_harvest", "yield_per_hectare", "crop_count", "harvest_value"],
        "relationships": [
            {"target": "farm", "type": "grown_on", "label": "farm"},
        ],
    },
    "livestock": {
        "display_name": "Livestock",
        "industry": "agriculture",
        "weight": 2.5,
        "synonyms": ["livestock", "animal", "herd", "cattle", "poultry", "sheep", "goat"],
        "attributes": ["livestock_id", "farm_id", "animal_type", "count", "health_status"],
        "kpis": ["total_livestock", "mortality_rate", "growth_rate", "herd_value"],
        "relationships": [
            {"target": "farm", "type": "raised_on", "label": "farm"},
        ],
    },
    "weather": {
        "display_name": "Weather",
        "industry": "agriculture",
        "weight": 2.0,
        "synonyms": [
            "weather",
            "weather_id",
            "rainfall",
            "temperature",
            "humidity",
            "precipitation",
        ],
        "attributes": ["weather_id", "farm_id", "date", "rainfall_mm", "temperature_c"],
        "kpis": ["total_rainfall", "avg_temperature", "frost_days", "dry_days"],
        "relationships": [
            {"target": "farm", "type": "recorded_at", "label": "farm"},
        ],
    },
    # ── Cross-industry / Universal ──
    "revenue": {
        "display_name": "Revenue",
        "industry": "universal",
        "synonyms": [
            "sales",
            "revenue",
            "amount",
            "total",
            "income",
            "turnover",
            "fee",
            "tuition",
            "tuition_fee",
            "price",
            "payment",
            "grand_total",
        ],
        "attributes": ["amount", "date"],
        "kpis": ["total_revenue", "avg_revenue", "growth_rate", "revenue_by_category"],
        "relationships": [],
    },
    "expense": {
        "display_name": "Expense",
        "industry": "universal",
        "synonyms": ["expense", "cost", "expenditure", "spending", "outflow", "payment_made"],
        "attributes": ["amount", "date", "category"],
        "kpis": ["total_expense", "avg_expense", "budget_variance"],
        "relationships": [],
    },
    "balance": {
        "display_name": "Balance",
        "industry": "universal",
        "synonyms": ["balance", "current_balance", "available_balance", "closing_balance", "opening_balance"],
        "attributes": ["amount", "date"],
        "kpis": ["total_balance", "avg_balance"],
        "relationships": [],
    },
    "account_universal": {
        "display_name": "Account",
        "industry": "universal",
        "synonyms": ["account", "account_id"],
        "attributes": ["account_id", "name"],
        "kpis": ["account_count"],
        "relationships": [],
    },
    "transaction_universal": {
        "display_name": "Transaction",
        "industry": "universal",
        "synonyms": ["transaction", "transfer", "deposit", "withdrawal", "payment_amount"],
        "attributes": ["transaction_id", "amount", "date"],
        "kpis": ["total_transactions", "avg_transaction"],
        "relationships": [],
    },
    "date": {
        "display_name": "Date",
        "industry": "universal",
        "synonyms": [
            "date",
            "order_date",
            "transaction_date",
            "created_at",
            "timestamp",
            "recorded_date",
            "entry_date",
        ],
        "attributes": ["date"],
        "kpis": ["date_range", "records_per_period"],
        "relationships": [],
    },
    "region": {
        "display_name": "Region",
        "industry": "universal",
        "synonyms": [
            "region",
            "area",
            "zone",
            "territory",
            "location",
            "district",
            "county",
            "city",
            "country",
        ],
        "attributes": ["region_name"],
        "kpis": ["records_by_region", "revenue_by_region"],
        "relationships": [],
    },
    "department": {
        "display_name": "Department",
        "industry": "universal",
        "synonyms": ["department", "dept", "division", "unit", "section"],
        "attributes": ["department_id", "department_name", "head"],
        "kpis": ["department_count", "budget_utilization"],
        "relationships": [],
    },
}


def get_all_entities() -> dict[str, dict]:
    """Return the full entity library."""
    return ENTITY_LIBRARY


def get_entities_by_industry(industry: str) -> dict[str, dict]:
    """Return entities for a specific industry plus universal entities."""
    return {
        k: v
        for k, v in ENTITY_LIBRARY.items()
        if v["industry"] == industry or v["industry"] == "universal"
    }


def get_entity(entity_key: str) -> dict | None:
    """Get a single entity by key."""
    return ENTITY_LIBRARY.get(entity_key)


def get_all_synonyms() -> dict[str, str]:
    """Return a mapping of all synonyms to entity keys."""
    synonym_map = {}
    for entity_key, entity in ENTITY_LIBRARY.items():
        for syn in entity["synonyms"]:
            synonym_map[syn.lower()] = entity_key
    return synonym_map


def get_all_industries() -> list[str]:
    """Return all supported industries."""
    industries = set()
    for entity in ENTITY_LIBRARY.values():
        if entity["industry"] != "universal":
            industries.add(entity["industry"])
    return sorted(industries)


# Merge extended industry entity definitions (banking, insurance, hospitality,
# telecommunications) into the core library.
ENTITY_LIBRARY.update(EXTRA_ENTITIES)
