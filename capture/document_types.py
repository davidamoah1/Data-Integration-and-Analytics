"""Registry of supported document types across industries.

Each document type defines:
  - key: machine identifier
  - label: human-readable name
  - industry: grouping used for module specialization + UI
  - keywords: terms whose presence in OCR text boosts classification confidence
  - fields: expected fields, used to guide extraction + validation

The Healthcare industry has the deepest field specifications (flagship
vertical for Phase 16). Other industries have solid generic coverage and can
be deepened later without touching the core engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FieldSpec:
    name: str
    label: str
    data_type: str = "text"  # text, number, date, phone, email, currency, enum
    required: bool = False
    keywords: list[str] = field(default_factory=list)  # label variants to find in OCR text
    enum_values: list[str] | None = None


@dataclass
class DocumentTypeSpec:
    key: str
    label: str
    industry: str
    keywords: list[str]
    fields: list[FieldSpec]


# ─── Healthcare (flagship vertical) ─────────────────────────────────────────

HEALTHCARE_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="opd_register",
        label="OPD Register",
        industry="healthcare",
        keywords=["opd", "outpatient", "out-patient", "consulting room", "attendance register"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name", "patient name"]),
            FieldSpec("age", "Age", "number", True, ["age"]),
            FieldSpec(
                "sex",
                "Sex",
                "enum",
                True,
                ["sex", "gender"],
                enum_values=["M", "F", "Male", "Female"],
            ),
            FieldSpec("date", "Visit Date", "date", True, ["date"]),
            FieldSpec("diagnosis", "Diagnosis", "text", False, ["diagnosis", "dx", "complaint"]),
            FieldSpec("department", "Department", "text", False, ["department", "unit", "clinic"]),
            FieldSpec(
                "attending_officer",
                "Attending Officer",
                "text",
                False,
                ["seen by", "clinician", "attended by"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="admission_register",
        label="Admission Register",
        industry="healthcare",
        keywords=["admission register", "ward admission", "admitted", "bed number"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name", "patient name"]),
            FieldSpec("age", "Age", "number", True, ["age"]),
            FieldSpec(
                "sex",
                "Sex",
                "enum",
                True,
                ["sex", "gender"],
                enum_values=["M", "F", "Male", "Female"],
            ),
            FieldSpec(
                "diagnosis", "Diagnosis", "text", False, ["diagnosis", "provisional diagnosis"]
            ),
            FieldSpec("doctor", "Doctor", "text", False, ["doctor", "physician", "consultant"]),
            FieldSpec("ward", "Ward", "text", True, ["ward"]),
            FieldSpec("bed_number", "Bed Number", "text", False, ["bed", "bed no", "bed number"]),
            FieldSpec(
                "admission_date",
                "Admission Date",
                "date",
                True,
                ["admission date", "date admitted"],
            ),
            FieldSpec(
                "discharge_date",
                "Discharge Date",
                "date",
                False,
                ["discharge date", "date discharged"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="laboratory_form",
        label="Laboratory Form",
        industry="healthcare",
        keywords=["laboratory", "lab request", "specimen", "reference range", "test result"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name", "patient name"]),
            FieldSpec("test_name", "Test Name", "text", True, ["test", "investigation"]),
            FieldSpec("result", "Result", "text", True, ["result", "value"]),
            FieldSpec("units", "Units", "text", False, ["units", "unit"]),
            FieldSpec(
                "reference_range",
                "Reference Range",
                "text",
                False,
                ["reference range", "normal range"],
            ),
            FieldSpec(
                "technician", "Technician", "text", False, ["technician", "analyst", "performed by"]
            ),
            FieldSpec("date", "Test Date", "date", False, ["date"]),
        ],
    ),
    DocumentTypeSpec(
        key="pharmacy_register",
        label="Pharmacy Register",
        industry="healthcare",
        keywords=["pharmacy", "dispensary", "drug register", "batch number", "expiry date"],
        fields=[
            FieldSpec("drug_name", "Drug", "text", True, ["drug", "medicine", "item"]),
            FieldSpec("quantity", "Quantity", "number", True, ["quantity", "qty"]),
            FieldSpec(
                "batch_number", "Batch Number", "text", False, ["batch", "batch no", "batch number"]
            ),
            FieldSpec(
                "expiry_date", "Expiry Date", "date", False, ["expiry", "exp date", "expiry date"]
            ),
            FieldSpec(
                "supplier", "Supplier", "text", False, ["supplier", "manufacturer", "vendor"]
            ),
        ],
    ),
    DocumentTypeSpec(
        key="patient_card",
        label="Patient Card",
        industry="healthcare",
        keywords=["patient card", "patient id card", "hospital card", "folder number"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name"]),
            FieldSpec(
                "patient_id", "Patient ID", "text", True, ["id", "folder number", "card number"]
            ),
            FieldSpec("age", "Age", "number", False, ["age"]),
            FieldSpec("sex", "Sex", "enum", False, ["sex", "gender"], enum_values=["M", "F"]),
            FieldSpec("phone", "Phone", "phone", False, ["phone", "tel", "contact"]),
            FieldSpec("address", "Address", "text", False, ["address", "residence"]),
        ],
    ),
    DocumentTypeSpec(
        key="nhis_claim_form",
        label="NHIS Claim Form",
        industry="healthcare",
        keywords=["nhis", "national health insurance", "claim form", "membership number"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name"]),
            FieldSpec(
                "membership_number",
                "Membership Number",
                "text",
                True,
                ["membership number", "nhis number"],
            ),
            FieldSpec("diagnosis", "Diagnosis", "text", False, ["diagnosis"]),
            FieldSpec("service_date", "Service Date", "date", False, ["date of service", "date"]),
            FieldSpec(
                "amount_claimed", "Amount Claimed", "currency", False, ["amount", "claim amount"]
            ),
        ],
    ),
    DocumentTypeSpec(
        key="theatre_register",
        label="Theatre Register",
        industry="healthcare",
        keywords=["theatre register", "operation", "surgery", "surgeon"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name"]),
            FieldSpec("procedure", "Procedure", "text", True, ["procedure", "operation"]),
            FieldSpec("surgeon", "Surgeon", "text", False, ["surgeon"]),
            FieldSpec("anesthetist", "Anesthetist", "text", False, ["anesthetist", "anaesthetist"]),
            FieldSpec("date", "Date", "date", True, ["date"]),
        ],
    ),
    DocumentTypeSpec(
        key="delivery_register",
        label="Delivery Register",
        industry="healthcare",
        keywords=["delivery register", "maternity", "labour ward", "birth weight"],
        fields=[
            FieldSpec("mother_name", "Mother's Name", "text", True, ["mother", "mother's name"]),
            FieldSpec("delivery_date", "Delivery Date", "date", True, ["date of delivery", "date"]),
            FieldSpec("mode_of_delivery", "Mode of Delivery", "text", False, ["mode of delivery"]),
            FieldSpec("birth_weight", "Birth Weight", "text", False, ["birth weight", "weight"]),
            FieldSpec("outcome", "Outcome", "text", False, ["outcome", "condition"]),
        ],
    ),
    DocumentTypeSpec(
        key="referral_form",
        label="Referral Form",
        industry="healthcare",
        keywords=["referral form", "referred to", "referring facility"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name"]),
            FieldSpec(
                "referring_facility",
                "Referring Facility",
                "text",
                False,
                ["referring facility", "from"],
            ),
            FieldSpec("referred_to", "Referred To", "text", True, ["referred to", "to"]),
            FieldSpec(
                "reason", "Reason for Referral", "text", False, ["reason", "reason for referral"]
            ),
            FieldSpec("date", "Date", "date", False, ["date"]),
        ],
    ),
    DocumentTypeSpec(
        key="discharge_form",
        label="Discharge Form",
        industry="healthcare",
        keywords=["discharge summary", "discharge form", "discharged on"],
        fields=[
            FieldSpec("patient_name", "Patient Name", "text", True, ["name"]),
            FieldSpec(
                "diagnosis", "Final Diagnosis", "text", False, ["final diagnosis", "diagnosis"]
            ),
            FieldSpec(
                "discharge_date",
                "Discharge Date",
                "date",
                True,
                ["discharge date", "date discharged"],
            ),
            FieldSpec(
                "condition_on_discharge",
                "Condition on Discharge",
                "text",
                False,
                ["condition on discharge"],
            ),
            FieldSpec(
                "follow_up", "Follow-up Instructions", "text", False, ["follow up", "follow-up"]
            ),
        ],
    ),
]

# ─── Education ──────────────────────────────────────────────────────────────

EDUCATION_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="student_register",
        label="Student Register",
        industry="education",
        keywords=["student register", "class list", "enrollment"],
        fields=[
            FieldSpec("student_name", "Student Name", "text", True, ["name"]),
            FieldSpec("student_id", "Student ID", "text", False, ["id", "index number"]),
            FieldSpec("class_name", "Class", "text", False, ["class", "grade"]),
            FieldSpec("date_of_birth", "Date of Birth", "date", False, ["dob", "date of birth"]),
        ],
    ),
    DocumentTypeSpec(
        key="attendance_sheet",
        label="Attendance Sheet",
        industry="education",
        keywords=["attendance sheet", "present", "absent", "attendance register"],
        fields=[
            FieldSpec("student_name", "Student Name", "text", True, ["name"]),
            FieldSpec("date", "Date", "date", True, ["date"]),
            FieldSpec(
                "status",
                "Status",
                "enum",
                False,
                ["status", "present/absent"],
                enum_values=["Present", "Absent"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="examination_results",
        label="Examination Results",
        industry="education",
        keywords=["examination results", "score sheet", "grade sheet", "marks"],
        fields=[
            FieldSpec("student_name", "Student Name", "text", True, ["name"]),
            FieldSpec("subject", "Subject", "text", False, ["subject"]),
            FieldSpec("score", "Score", "number", False, ["score", "marks", "grade"]),
        ],
    ),
    DocumentTypeSpec(
        key="admission_form",
        label="Admission Form",
        industry="education",
        keywords=["admission form", "application for admission"],
        fields=[
            FieldSpec("applicant_name", "Applicant Name", "text", True, ["name"]),
            FieldSpec("date_of_birth", "Date of Birth", "date", False, ["dob", "date of birth"]),
            FieldSpec("guardian_name", "Guardian Name", "text", False, ["guardian", "parent"]),
            FieldSpec("phone", "Phone", "phone", False, ["phone", "contact"]),
        ],
    ),
    DocumentTypeSpec(
        key="transcript",
        label="Transcript",
        industry="education",
        keywords=["transcript", "academic record", "cumulative gpa"],
        fields=[
            FieldSpec("student_name", "Student Name", "text", True, ["name"]),
            FieldSpec("student_id", "Student ID", "text", False, ["id", "index number"]),
            FieldSpec("gpa", "GPA", "number", False, ["gpa", "cgpa"]),
        ],
    ),
]

# ─── Government ─────────────────────────────────────────────────────────────

GOVERNMENT_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="census_form",
        label="Census Form",
        industry="government",
        keywords=["census", "household survey", "population count"],
        fields=[
            FieldSpec(
                "household_head",
                "Household Head",
                "text",
                True,
                ["household head", "head of household"],
            ),
            FieldSpec(
                "household_size",
                "Household Size",
                "number",
                False,
                ["household size", "number of members"],
            ),
            FieldSpec("address", "Address", "text", False, ["address", "location"]),
            FieldSpec("date", "Date", "date", False, ["date"]),
        ],
    ),
    DocumentTypeSpec(
        key="permit",
        label="Permit",
        industry="government",
        keywords=["permit", "license", "authorization"],
        fields=[
            FieldSpec("applicant_name", "Applicant Name", "text", True, ["name", "applicant"]),
            FieldSpec(
                "permit_number", "Permit Number", "text", False, ["permit number", "license number"]
            ),
            FieldSpec("issue_date", "Issue Date", "date", False, ["issue date", "date issued"]),
            FieldSpec("expiry_date", "Expiry Date", "date", False, ["expiry date", "valid until"]),
        ],
    ),
    DocumentTypeSpec(
        key="tax_form",
        label="Tax Form",
        industry="government",
        keywords=["tax form", "tax identification", "revenue"],
        fields=[
            FieldSpec("taxpayer_name", "Taxpayer Name", "text", True, ["name", "taxpayer"]),
            FieldSpec("tin", "Tax ID Number", "text", False, ["tin", "tax id"]),
            FieldSpec("amount_due", "Amount Due", "currency", False, ["amount due", "tax due"]),
            FieldSpec("period", "Period", "text", False, ["period", "tax period"]),
        ],
    ),
]

# ─── Business (generic across Banking, Retail, Manufacturing, Logistics, Insurance) ─

BUSINESS_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="invoice",
        label="Invoice",
        industry="business",
        keywords=["invoice", "invoice number", "bill to", "amount due"],
        fields=[
            FieldSpec(
                "invoice_number", "Invoice Number", "text", True, ["invoice number", "invoice no"]
            ),
            FieldSpec("vendor_name", "Vendor", "text", False, ["vendor", "from", "seller"]),
            FieldSpec("customer_name", "Customer", "text", False, ["bill to", "customer"]),
            FieldSpec("date", "Invoice Date", "date", False, ["date", "invoice date"]),
            FieldSpec(
                "total_amount",
                "Total Amount",
                "currency",
                True,
                ["total", "amount due", "grand total"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="receipt",
        label="Receipt",
        industry="business",
        keywords=["receipt", "cash received", "paid", "thank you"],
        fields=[
            FieldSpec(
                "receipt_number", "Receipt Number", "text", False, ["receipt number", "receipt no"]
            ),
            FieldSpec("date", "Date", "date", False, ["date"]),
            FieldSpec("total_amount", "Total Amount", "currency", True, ["total", "amount"]),
            FieldSpec(
                "payment_method", "Payment Method", "text", False, ["payment method", "paid via"]
            ),
        ],
    ),
    DocumentTypeSpec(
        key="purchase_order",
        label="Purchase Order",
        industry="business",
        keywords=["purchase order", "po number", "ship to"],
        fields=[
            FieldSpec(
                "po_number", "PO Number", "text", True, ["po number", "purchase order number"]
            ),
            FieldSpec("supplier_name", "Supplier", "text", False, ["supplier", "vendor"]),
            FieldSpec("date", "Date", "date", False, ["date"]),
            FieldSpec("total_amount", "Total Amount", "currency", False, ["total", "amount"]),
        ],
    ),
    DocumentTypeSpec(
        key="inventory_sheet",
        label="Inventory Sheet",
        industry="business",
        keywords=["inventory", "stock count", "quantity on hand"],
        fields=[
            FieldSpec("item_name", "Item", "text", True, ["item", "product"]),
            FieldSpec("quantity", "Quantity", "number", True, ["quantity", "qty", "stock"]),
            FieldSpec("unit_price", "Unit Price", "currency", False, ["unit price", "price"]),
        ],
    ),
    DocumentTypeSpec(
        key="delivery_note",
        label="Delivery Note",
        industry="business",
        keywords=["delivery note", "goods delivered", "received by"],
        fields=[
            FieldSpec(
                "delivery_number",
                "Delivery Number",
                "text",
                False,
                ["delivery number", "delivery no"],
            ),
            FieldSpec("recipient_name", "Recipient", "text", False, ["received by", "recipient"]),
            FieldSpec("date", "Date", "date", False, ["date"]),
        ],
    ),
]

# ─── Generic Forms (cross-industry) ─────────────────────────────────────────

FORM_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="generic_form",
        label="Generic Form",
        industry="business",
        keywords=["form", "application form", "registration form", "questionnaire"],
        fields=[
            FieldSpec("form_title", "Form Title", "text", False, ["form title", "title"]),
            FieldSpec("applicant_name", "Applicant Name", "text", True, ["name", "applicant"]),
            FieldSpec("date", "Date", "date", False, ["date"]),
            FieldSpec("phone", "Phone", "phone", False, ["phone", "tel", "contact"]),
            FieldSpec("email", "Email", "email", False, ["email", "e-mail"]),
            FieldSpec("address", "Address", "text", False, ["address", "location"]),
            FieldSpec("id_number", "ID Number", "text", False, ["id", "id number", "reference"]),
            FieldSpec("signature", "Signature", "text", False, ["signature", "signed by"]),
        ],
    ),
    DocumentTypeSpec(
        key="survey_form",
        label="Survey Form",
        industry="business",
        keywords=["survey", "questionnaire", "feedback form", "response"],
        fields=[
            FieldSpec("respondent_name", "Respondent Name", "text", False, ["name", "respondent"]),
            FieldSpec("date", "Date", "date", False, ["date"]),
            FieldSpec("location", "Location", "text", False, ["location", "area"]),
            FieldSpec("response_1", "Response 1", "text", False, ["q1", "response 1"]),
            FieldSpec("response_2", "Response 2", "text", False, ["q2", "response 2"]),
            FieldSpec("response_3", "Response 3", "text", False, ["q3", "response 3"]),
        ],
    ),
    DocumentTypeSpec(
        key="application_form",
        label="Application Form",
        industry="business",
        keywords=["application form", "apply", "applicant details"],
        fields=[
            FieldSpec("applicant_name", "Applicant Name", "text", True, ["name", "applicant"]),
            FieldSpec("date_of_birth", "Date of Birth", "date", False, ["dob", "date of birth"]),
            FieldSpec("phone", "Phone", "phone", False, ["phone", "tel", "contact"]),
            FieldSpec("email", "Email", "email", False, ["email", "e-mail"]),
            FieldSpec("address", "Address", "text", False, ["address"]),
            FieldSpec("id_number", "ID Number", "text", False, ["id", "id number"]),
            FieldSpec(
                "application_date", "Application Date", "date", False, ["application date", "date"]
            ),
        ],
    ),
]

# ─── Certificates ───────────────────────────────────────────────────────────
# Certificate-specific document types covering academic, professional,
# training, and membership certificates. Each type defines the fields
# expected on that certificate variant. The extraction engine uses these
# field specs (keywords + data types) to locate and validate values in
# OCR text. Fields are optional unless marked required — a real
# certificate may not contain every field listed here.

CERTIFICATE_TYPES: list[DocumentTypeSpec] = [
    DocumentTypeSpec(
        key="academic_certificate",
        label="Academic Certificate",
        industry="certificates",
        keywords=[
            "certificate",
            "academic",
            "university",
            "college",
            "degree",
            "bachelor",
            "master",
            "doctorate",
            "phd",
            "awarded",
            "conferred",
            "graduation",
            "faculty",
            "school of",
        ],
        fields=[
            FieldSpec(
                "full_name",
                "Full Name",
                "text",
                True,
                ["name", "full name", "this is to certify", "awarded to", "conferred upon"],
            ),
            FieldSpec(
                "qualification",
                "Qualification",
                "text",
                True,
                ["degree", "qualification", "bachelor of", "master of", "doctor of"],
            ),
            FieldSpec(
                "programme",
                "Programme",
                "text",
                False,
                ["programme", "program", "course", "major", "field of study"],
            ),
            FieldSpec(
                "institution",
                "Institution",
                "text",
                True,
                ["university", "college", "institute", "school", "awarded by", "issued by"],
            ),
            FieldSpec(
                "date_awarded",
                "Date Awarded",
                "date",
                False,
                ["date awarded", "awarded on", "date of award", "conferred on"],
            ),
            FieldSpec(
                "graduation_date", "Graduation Date", "date", False, ["graduation", "graduated on"]
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "cert no", "serial number", "registration number"],
            ),
            FieldSpec(
                "grade", "Grade/Class", "text", False, ["grade", "class", "division", "honors"]
            ),
            FieldSpec("gpa", "GPA/CGPA", "number", False, ["gpa", "cgpa", "grade point"]),
            FieldSpec(
                "department", "Department", "text", False, ["department", "faculty of", "school of"]
            ),
            FieldSpec("country", "Country", "text", False, ["country", "location"]),
        ],
    ),
    DocumentTypeSpec(
        key="degree_certificate",
        label="Degree Certificate",
        industry="certificates",
        keywords=[
            "degree",
            "bachelor",
            "master",
            "doctorate",
            "phd",
            "bachelor of",
            "master of",
            "doctor of",
            "b.sc",
            "m.sc",
            "b.a",
            "m.a",
            "awarded",
            "conferred",
        ],
        fields=[
            FieldSpec(
                "full_name",
                "Full Name",
                "text",
                True,
                ["name", "awarded to", "conferred upon", "this is to certify"],
            ),
            FieldSpec(
                "degree",
                "Degree",
                "text",
                True,
                ["degree", "bachelor of", "master of", "doctor of"],
            ),
            FieldSpec(
                "programme",
                "Programme",
                "text",
                False,
                ["programme", "program", "major", "specialization"],
            ),
            FieldSpec(
                "institution", "Institution", "text", True, ["university", "college", "institute"]
            ),
            FieldSpec(
                "date_awarded",
                "Date Awarded",
                "date",
                False,
                ["date awarded", "awarded on", "conferred on"],
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
            FieldSpec(
                "grade", "Grade/Class", "text", False, ["grade", "class", "honors", "distinction"]
            ),
            FieldSpec("gpa", "GPA/CGPA", "number", False, ["gpa", "cgpa"]),
            FieldSpec("department", "Department", "text", False, ["department", "faculty"]),
        ],
    ),
    DocumentTypeSpec(
        key="diploma",
        label="Diploma",
        industry="certificates",
        keywords=[
            "diploma",
            "diploma in",
            "higher diploma",
            "postgraduate diploma",
            "advanced diploma",
            "issued",
            "completed",
        ],
        fields=[
            FieldSpec(
                "full_name", "Full Name", "text", True, ["name", "awarded to", "this is to certify"]
            ),
            FieldSpec("qualification", "Qualification", "text", True, ["diploma", "qualification"]),
            FieldSpec("programme", "Programme", "text", False, ["programme", "program", "course"]),
            FieldSpec(
                "institution",
                "Institution",
                "text",
                True,
                ["institution", "college", "institute", "school"],
            ),
            FieldSpec(
                "date_awarded",
                "Date Awarded",
                "date",
                False,
                ["date awarded", "awarded on", "date of issue"],
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
            FieldSpec("grade", "Grade", "text", False, ["grade", "class"]),
            FieldSpec("credits", "Credits", "number", False, ["credits", "credit hours"]),
        ],
    ),
    DocumentTypeSpec(
        key="professional_certificate",
        label="Professional Certificate",
        industry="certificates",
        keywords=[
            "professional",
            "certification",
            "certified",
            "licensed",
            "professional certificate",
            "certificate of proficiency",
            "accreditation",
            "chartered",
        ],
        fields=[
            FieldSpec(
                "full_name",
                "Full Name",
                "text",
                True,
                ["name", "certified", "awarded to", "this is to certify"],
            ),
            FieldSpec(
                "qualification",
                "Qualification",
                "text",
                True,
                ["certification", "certificate", "qualification", "professional"],
            ),
            FieldSpec(
                "institution",
                "Issuing Organization",
                "text",
                True,
                ["issued by", "organization", "body", "institute", "society"],
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "date of issue"],
            ),
            FieldSpec(
                "expiry_date",
                "Expiry Date",
                "date",
                False,
                ["expiry", "expires", "valid until", "renewal date"],
            ),
            FieldSpec(
                "certificate_number",
                "Certificate/License Number",
                "text",
                False,
                ["certificate number", "license number", "registration number", "credential id"],
            ),
            FieldSpec(
                "license_number",
                "License Number",
                "text",
                False,
                ["license number", "licence number", "license no"],
            ),
            FieldSpec(
                "verification_code",
                "Verification Code",
                "text",
                False,
                ["verification code", "verify", "auth code"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="training_certificate",
        label="Training Certificate",
        industry="certificates",
        keywords=[
            "training",
            "training certificate",
            "certificate of training",
            "workshop",
            "completed training",
            "course completion",
        ],
        fields=[
            FieldSpec(
                "full_name", "Full Name", "text", True, ["name", "awarded to", "this is to certify"]
            ),
            FieldSpec(
                "course",
                "Course/Training",
                "text",
                True,
                ["course", "training", "workshop", "programme"],
            ),
            FieldSpec(
                "institution",
                "Issuing Organization",
                "text",
                True,
                ["issued by", "organization", "training provider"],
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "completed on"],
            ),
            FieldSpec(
                "duration", "Duration", "text", False, ["duration", "hours", "days", "weeks"]
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="certificate_of_completion",
        label="Certificate of Completion",
        industry="certificates",
        keywords=[
            "certificate of completion",
            "completed",
            "successfully completed",
            "course completion",
            "program completion",
        ],
        fields=[
            FieldSpec(
                "full_name", "Full Name", "text", True, ["name", "awarded to", "this is to certify"]
            ),
            FieldSpec(
                "course",
                "Course/Programme",
                "text",
                True,
                ["course", "programme", "program", "module"],
            ),
            FieldSpec(
                "institution",
                "Issuing Organization",
                "text",
                True,
                ["issued by", "organization", "institution"],
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "completed on"],
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
            FieldSpec(
                "hours", "Hours/Credits", "number", False, ["hours", "credits", "credit hours"]
            ),
        ],
    ),
    DocumentTypeSpec(
        key="certificate_of_attendance",
        label="Certificate of Attendance",
        industry="certificates",
        keywords=[
            "certificate of attendance",
            "attended",
            "attendance",
            "participated",
            "participation",
        ],
        fields=[
            FieldSpec(
                "full_name", "Full Name", "text", True, ["name", "attended", "this is to certify"]
            ),
            FieldSpec(
                "event",
                "Event/Conference",
                "text",
                True,
                ["event", "conference", "workshop", "seminar"],
            ),
            FieldSpec(
                "institution", "Issuing Organization", "text", True, ["issued by", "organization"]
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "date of attendance"],
            ),
            FieldSpec("location", "Location", "text", False, ["location", "venue", "city"]),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="membership_certificate",
        label="Membership Certificate",
        industry="certificates",
        keywords=[
            "membership",
            "member",
            "membership certificate",
            "fellow",
            "associate member",
            "certified member",
        ],
        fields=[
            FieldSpec(
                "full_name", "Full Name", "text", True, ["name", "member", "this is to certify"]
            ),
            FieldSpec(
                "membership_type",
                "Membership Type",
                "text",
                False,
                ["membership", "member", "fellow", "associate"],
            ),
            FieldSpec(
                "institution",
                "Organization",
                "text",
                True,
                ["organization", "society", "institute", "association"],
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "member since"],
            ),
            FieldSpec(
                "member_id",
                "Member ID",
                "text",
                False,
                ["member id", "membership number", "registration number"],
            ),
            FieldSpec(
                "certificate_number",
                "Certificate Number",
                "text",
                False,
                ["certificate number", "serial number"],
            ),
        ],
    ),
    DocumentTypeSpec(
        key="license_certification",
        label="License/Certification",
        industry="certificates",
        keywords=[
            "license",
            "licence",
            "licensed",
            "certification",
            "certified",
            "registered",
            "registration",
            "authorized",
            "authorised",
            "practice license",
            "professional license",
        ],
        fields=[
            FieldSpec(
                "full_name",
                "Full Name",
                "text",
                True,
                ["name", "licensed", "certified", "registered"],
            ),
            FieldSpec(
                "license_type",
                "License Type",
                "text",
                True,
                ["license", "licence", "certification", "registration"],
            ),
            FieldSpec(
                "institution",
                "Issuing Authority",
                "text",
                True,
                ["issued by", "authority", "board", "agency"],
            ),
            FieldSpec(
                "license_number",
                "License Number",
                "text",
                False,
                ["license number", "licence number", "registration number"],
            ),
            FieldSpec(
                "date_issued",
                "Date Issued",
                "date",
                False,
                ["date issued", "issued on", "effective date"],
            ),
            FieldSpec(
                "expiry_date",
                "Expiry Date",
                "date",
                False,
                ["expiry", "expires", "valid until", "renewal"],
            ),
            FieldSpec(
                "verification_code",
                "Verification Code",
                "text",
                False,
                ["verification code", "verify"],
            ),
        ],
    ),
]


# ─── Combined registry ──────────────────────────────────────────────────────

ALL_DOCUMENT_TYPES: list[DocumentTypeSpec] = (
    HEALTHCARE_TYPES
    + EDUCATION_TYPES
    + GOVERNMENT_TYPES
    + BUSINESS_TYPES
    + FORM_TYPES
    + CERTIFICATE_TYPES
)

DOCUMENT_TYPES_BY_KEY: dict[str, DocumentTypeSpec] = {d.key: d for d in ALL_DOCUMENT_TYPES}

INDUSTRIES: list[str] = ["healthcare", "education", "government", "business", "certificates"]


def get_document_type(key: str) -> DocumentTypeSpec | None:
    return DOCUMENT_TYPES_BY_KEY.get(key)


def list_document_types(industry: str | None = None) -> list[DocumentTypeSpec]:
    if industry:
        return [d for d in ALL_DOCUMENT_TYPES if d.industry == industry]
    return ALL_DOCUMENT_TYPES


# Generic fields extracted for every document regardless of type, used as a
# fallback / supplement when the classified type has no matching field or
# when classification confidence is too low to select a specific type.
GENERIC_FIELDS: list[FieldSpec] = [
    FieldSpec("full_name", "Name", "text", False, ["name"]),
    FieldSpec("date", "Date", "date", False, ["date"]),
    FieldSpec("phone", "Phone", "phone", False, ["phone", "tel", "mobile", "contact"]),
    FieldSpec("email", "Email", "email", False, ["email", "e-mail"]),
    FieldSpec("amount", "Amount", "currency", False, ["amount", "total", "price"]),
    FieldSpec("id_number", "ID Number", "text", False, ["id", "id number", "reference number"]),
    FieldSpec("address", "Address", "text", False, ["address", "location"]),
]
