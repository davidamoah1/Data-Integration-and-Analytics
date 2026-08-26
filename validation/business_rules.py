"""Hospital Business Rules Engine â€” configurable clinical and administrative rule validation."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class BusinessRule:
    """A configurable business rule."""

    name: str
    description: str
    category: str  # business, clinical, administrative
    severity: str  # error, warning
    enabled: bool = True
    check_fn: callable = None
    config: dict = field(default_factory=dict)


@dataclass
class BusinessRuleFinding:
    rule_name: str
    category: str
    severity: str
    column: str | None
    affected_rows: int
    message: str
    suggested_fix: str | None = None
    business_impact: str | None = None


class BusinessRuleEngine:
    """Runs hospital business rules against a DataFrame."""

    def __init__(self):
        self._rules: list[BusinessRule] = []
        self._register_default_rules()

    def add_rule(self, rule: BusinessRule):
        self._rules.append(rule)

    def remove_rule(self, name: str):
        self._rules = [r for r in self._rules if r.name != name]

    def disable_rule(self, name: str):
        for r in self._rules:
            if r.name == name:
                r.enabled = False

    def enable_rule(self, name: str):
        for r in self._rules:
            if r.name == name:
                r.enabled = True

    def list_rules(self) -> list[dict]:
        return [
            {
                "name": r.name,
                "description": r.description,
                "category": r.category,
                "severity": r.severity,
                "enabled": r.enabled,
            }
            for r in self._rules
        ]

    def run(self, df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings: list[BusinessRuleFinding] = []
        for rule in self._rules:
            if not rule.enabled or rule.check_fn is None:
                continue
            try:
                result = rule.check_fn(df, rule.config)
                if result:
                    findings.extend(result)
            except Exception as e:
                findings.append(
                    BusinessRuleFinding(
                        rule_name=rule.name,
                        category=rule.category,
                        severity="warning",
                        column=None,
                        affected_rows=0,
                        message=f"Rule '{rule.name}' could not be evaluated: {e}",
                    )
                )
        return findings

    def _register_default_rules(self):
        self._rules = [
            BusinessRule(
                name="unique_patient_id",
                description="Patient ID must be unique.",
                category="business",
                severity="error",
                check_fn=self._check_unique_patient_id,
            ),
            BusinessRule(
                name="dob_not_future",
                description="Date of birth cannot be in the future.",
                category="business",
                severity="error",
                check_fn=self._check_dob_not_future,
            ),
            BusinessRule(
                name="admission_before_discharge",
                description="Admission date cannot be after discharge date.",
                category="clinical",
                severity="error",
                check_fn=self._check_admission_before_discharge,
            ),
            BusinessRule(
                name="realistic_age",
                description="Patient age must be realistic (0-150).",
                category="clinical",
                severity="error",
                check_fn=self._check_realistic_age,
            ),
            BusinessRule(
                name="no_negative_weight",
                description="Negative weight not allowed.",
                category="clinical",
                severity="error",
                check_fn=self._check_negative_weight,
            ),
            BusinessRule(
                name="no_negative_height",
                description="Negative height not allowed.",
                category="clinical",
                severity="error",
                check_fn=self._check_negative_height,
            ),
            BusinessRule(
                name="no_negative_lab_values",
                description="Negative laboratory values not allowed.",
                category="clinical",
                severity="error",
                check_fn=self._check_negative_lab_values,
            ),
            BusinessRule(
                name="male_not_pregnant",
                description="Male patient cannot be pregnant.",
                category="clinical",
                severity="error",
                check_fn=self._check_male_not_pregnant,
            ),
            BusinessRule(
                name="visit_requires_patient",
                description="Visit/admission cannot exist without a matching patient.",
                category="administrative",
                severity="error",
                check_fn=self._check_visit_requires_patient,
            ),
            BusinessRule(
                name="diagnosis_requires_clinician",
                description="Diagnosis requires a clinician/doctor.",
                category="clinical",
                severity="warning",
                check_fn=self._check_diagnosis_requires_clinician,
            ),
            BusinessRule(
                name="medication_requires_prescription",
                description="Medication record requires a prescriber.",
                category="clinical",
                severity="warning",
                check_fn=self._check_medication_requires_prescriber,
            ),
            BusinessRule(
                name="lab_result_requires_order",
                description="Laboratory result requires a test order.",
                category="clinical",
                severity="warning",
                check_fn=self._check_lab_result_requires_order,
            ),
            BusinessRule(
                name="child_age_pediatric",
                description="Child age (under 18) should be classified as pediatric.",
                category="clinical",
                severity="info",
                check_fn=self._check_child_age_pediatric,
            ),
        ]

    # â”€â”€ Rule implementations â”€â”€

    @staticmethod
    def _find_col(df: pd.DataFrame, keywords: list[str]) -> str | None:
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in keywords):
                return col
        return None

    @staticmethod
    def _check_unique_patient_id(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        col = BusinessRuleEngine._find_col(df, ["patient_id", "patientid", "patient_no"])
        if not col:
            return []
        dup_count = int(df[col].duplicated(keep=False).sum())
        if dup_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="unique_patient_id",
                    category="business",
                    severity="error",
                    column=col,
                    affected_rows=dup_count,
                    message=f"{dup_count} duplicate patient IDs found in '{col}'.",
                    suggested_fix="Ensure each patient has a unique ID.",
                    business_impact="Duplicate patient IDs can cause record merging errors and patient safety issues.",
                )
            ]
        return []

    @staticmethod
    def _check_dob_not_future(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        col = BusinessRuleEngine._find_col(df, ["dob", "date_of_birth", "birth_date", "birthdate"])
        if not col:
            return []
        try:
            dob = pd.to_datetime(df[col], errors="coerce")
        except Exception:
            return []
        today = pd.Timestamp.now()
        future_mask = dob > today
        future_count = int(future_mask.sum())
        if future_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="dob_not_future",
                    category="business",
                    severity="error",
                    column=col,
                    affected_rows=future_count,
                    message=f"{future_count} records have date of birth in the future.",
                    suggested_fix="Correct dates of birth to valid past dates.",
                    business_impact="Future birth dates indicate data entry errors.",
                )
            ]
        return []

    @staticmethod
    def _check_admission_before_discharge(
        df: pd.DataFrame, config: dict
    ) -> list[BusinessRuleFinding]:
        adm_col = BusinessRuleEngine._find_col(df, ["admission_date", "admit_date", "admission"])
        dis_col = BusinessRuleEngine._find_col(df, ["discharge_date", "discharge"])
        if not adm_col or not dis_col:
            return []
        if adm_col not in df.columns or dis_col not in df.columns:
            return []
        try:
            adm = pd.to_datetime(df[adm_col], errors="coerce")
            dis = pd.to_datetime(df[dis_col], errors="coerce")
        except Exception:
            return []
        invalid_mask = (adm > dis) & adm.notna() & dis.notna()
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="admission_before_discharge",
                    category="clinical",
                    severity="error",
                    column=f"{adm_col} / {dis_col}",
                    affected_rows=invalid_count,
                    message=f"{invalid_count} records have admission date after discharge date.",
                    suggested_fix="Correct admission or discharge dates so admission precedes discharge.",
                    business_impact="Invalid date sequences affect length-of-stay calculations and billing.",
                )
            ]
        return []

    @staticmethod
    def _check_realistic_age(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        col = BusinessRuleEngine._find_col(df, ["age"])
        if not col or not pd.api.types.is_numeric_dtype(df[col]):
            return []
        invalid_mask = (df[col] < 0) | (df[col] > 150)
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="realistic_age",
                    category="clinical",
                    severity="error",
                    column=col,
                    affected_rows=invalid_count,
                    message=f"{invalid_count} records have age outside 0-150 range.",
                    suggested_fix="Correct age values to be between 0 and 150.",
                    business_impact="Impossible ages indicate data entry errors and affect patient demographics.",
                )
            ]
        return []

    @staticmethod
    def _check_negative_weight(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        col = BusinessRuleEngine._find_col(df, ["weight"])
        if not col or not pd.api.types.is_numeric_dtype(df[col]):
            return []
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="no_negative_weight",
                    category="clinical",
                    severity="error",
                    column=col,
                    affected_rows=neg_count,
                    message=f"{neg_count} records have negative weight values.",
                    suggested_fix="Remove or correct negative weight values.",
                    business_impact="Negative weights are physiologically impossible.",
                )
            ]
        return []

    @staticmethod
    def _check_negative_height(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        col = BusinessRuleEngine._find_col(df, ["height"])
        if not col or not pd.api.types.is_numeric_dtype(df[col]):
            return []
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="no_negative_height",
                    category="clinical",
                    severity="error",
                    column=col,
                    affected_rows=neg_count,
                    message=f"{neg_count} records have negative height values.",
                    suggested_fix="Remove or correct negative height values.",
                    business_impact="Negative heights are physiologically impossible.",
                )
            ]
        return []

    @staticmethod
    def _check_negative_lab_values(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        findings = []
        lab_cols = [
            c for c in df.columns if "lab" in c.lower() and pd.api.types.is_numeric_dtype(df[c])
        ]
        lab_cols += [
            c
            for c in df.columns
            if "result" in c.lower()
            and "test" not in c.lower()
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        for col in lab_cols:
            neg_count = int((df[col] < 0).sum())
            if neg_count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="no_negative_lab_values",
                        category="clinical",
                        severity="error",
                        column=col,
                        affected_rows=neg_count,
                        message=f"Column '{col}': {neg_count} negative laboratory values.",
                        suggested_fix="Remove or correct negative lab values.",
                        business_impact="Negative lab values are typically impossible and indicate data errors.",
                    )
                )
        return findings

    @staticmethod
    def _check_male_not_pregnant(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        gender_col = BusinessRuleEngine._find_col(df, ["gender", "sex"])
        preg_col = BusinessRuleEngine._find_col(df, ["pregnant", "pregnancy", "is_pregnant"])
        if not gender_col or not preg_col:
            return []
        if gender_col not in df.columns or preg_col not in df.columns:
            return []
        gender_lower = df[gender_col].astype(str).str.strip().str.lower()
        preg_lower = df[preg_col].astype(str).str.strip().str.lower()
        male_pregnant = gender_lower.isin(["m", "male"]) & preg_lower.isin(
            ["yes", "true", "1", "pregnant"]
        )
        count = int(male_pregnant.sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="male_not_pregnant",
                    category="clinical",
                    severity="error",
                    column=f"{gender_col} / {preg_col}",
                    affected_rows=count,
                    message=f"{count} male patients marked as pregnant.",
                    suggested_fix="Correct gender or pregnancy status.",
                    business_impact="Clinically impossible records indicate data entry errors.",
                )
            ]
        return []

    @staticmethod
    def _check_visit_requires_patient(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        patient_col = BusinessRuleEngine._find_col(df, ["patient_id", "patientid"])
        visit_col = BusinessRuleEngine._find_col(df, ["visit_id", "admission_id", "visit"])
        if not patient_col or not visit_col:
            return []
        if patient_col not in df.columns or visit_col not in df.columns:
            return []
        null_patients = df[patient_col].isna() | (df[patient_col].astype(str).str.strip() == "")
        count = int(null_patients.sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="visit_requires_patient",
                    category="administrative",
                    severity="error",
                    column=patient_col,
                    affected_rows=count,
                    message=f"{count} visit/admission records have no patient ID.",
                    suggested_fix="Link all visits to valid patient IDs.",
                    business_impact="Orphaned visits cannot be attributed to patients.",
                )
            ]
        return []

    @staticmethod
    def _check_diagnosis_requires_clinician(
        df: pd.DataFrame, config: dict
    ) -> list[BusinessRuleFinding]:
        diag_col = BusinessRuleEngine._find_col(df, ["diagnosis"])
        clin_col = BusinessRuleEngine._find_col(
            df, ["doctor", "clinician", "physician", "attending"]
        )
        if not diag_col or not clin_col:
            return []
        if diag_col not in df.columns or clin_col not in df.columns:
            return []
        has_diag = df[diag_col].notna() & (df[diag_col].astype(str).str.strip() != "")
        no_clin = df[clin_col].isna() | (df[clin_col].astype(str).str.strip() == "")
        count = int((has_diag & no_clin).sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="diagnosis_requires_clinician",
                    category="clinical",
                    severity="warning",
                    column=clin_col,
                    affected_rows=count,
                    message=f"{count} diagnosis records have no attending clinician.",
                    suggested_fix="Assign a clinician to each diagnosis record.",
                    business_impact="Diagnoses without clinicians may not be valid for billing.",
                )
            ]
        return []

    @staticmethod
    def _check_medication_requires_prescriber(
        df: pd.DataFrame, config: dict
    ) -> list[BusinessRuleFinding]:
        med_col = BusinessRuleEngine._find_col(df, ["medication", "drug", "medicine"])
        presc_col = BusinessRuleEngine._find_col(
            df, ["prescribed_by", "prescriber", "prescription"]
        )
        if not med_col or not presc_col:
            return []
        if med_col not in df.columns or presc_col not in df.columns:
            return []
        has_med = df[med_col].notna() & (df[med_col].astype(str).str.strip() != "")
        no_presc = df[presc_col].isna() | (df[presc_col].astype(str).str.strip() == "")
        count = int((has_med & no_presc).sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="medication_requires_prescription",
                    category="clinical",
                    severity="warning",
                    column=presc_col,
                    affected_rows=count,
                    message=f"{count} medication records have no prescriber.",
                    suggested_fix="Assign a prescriber to each medication record.",
                    business_impact="Medications without prescribers may not be valid for billing.",
                )
            ]
        return []

    @staticmethod
    def _check_lab_result_requires_order(
        df: pd.DataFrame, config: dict
    ) -> list[BusinessRuleFinding]:
        result_col = BusinessRuleEngine._find_col(df, ["test_result", "lab_result", "result"])
        order_col = BusinessRuleEngine._find_col(
            df, ["test_order", "ordered_by", "order_id", "lab_order"]
        )
        if not result_col or not order_col:
            return []
        if result_col not in df.columns or order_col not in df.columns:
            return []
        has_result = df[result_col].notna() & (df[result_col].astype(str).str.strip() != "")
        no_order = df[order_col].isna() | (df[order_col].astype(str).str.strip() == "")
        count = int((has_result & no_order).sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="lab_result_requires_order",
                    category="clinical",
                    severity="warning",
                    column=order_col,
                    affected_rows=count,
                    message=f"{count} lab results have no corresponding test order.",
                    suggested_fix="Link lab results to test orders.",
                    business_impact="Lab results without orders may not be billable.",
                )
            ]
        return []

    @staticmethod
    def _check_child_age_pediatric(df: pd.DataFrame, config: dict) -> list[BusinessRuleFinding]:
        age_col = BusinessRuleEngine._find_col(df, ["age"])
        dept_col = BusinessRuleEngine._find_col(df, ["department", "dept", "ward", "unit"])
        if not age_col or not dept_col:
            return []
        if age_col not in df.columns or dept_col not in df.columns:
            return []
        if not pd.api.types.is_numeric_dtype(df[age_col]):
            return []
        children = df[age_col] < 18
        dept_lower = df[dept_col].astype(str).str.strip().str.lower()
        not_pediatric = ~dept_lower.isin(
            ["pediatric", "paediatric", "pediatrics", "paediatrics", "children", "child"]
        )
        count = int((children & not_pediatric).sum())
        if count > 0:
            return [
                BusinessRuleFinding(
                    rule_name="child_age_pediatric",
                    category="clinical",
                    severity="info",
                    column=dept_col,
                    affected_rows=count,
                    message=f"{count} patients under 18 are not in a pediatric department.",
                    suggested_fix="Review department assignment for pediatric patients.",
                    business_impact="Pediatric patients in adult wards may require special protocols.",
                )
            ]
        return []
