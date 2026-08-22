"""Enterprise Dataset Library — registry of datasets with full metadata.

Supports 11 industries: Healthcare, Education, Government, Retail, Church, NGO,
Manufacturing, Agriculture, Insurance, Hospitality, Telecommunications.

Each dataset entry contains:
    - source: Where the data originated
    - description: Human-readable description
    - industry: Industry classification
    - license: Data license terms
    - version: Dataset version
    - tags: Searchable tags
    - schema: Column definitions
    - quality_score: Data quality assessment (0-100)

Data tiers:
    - PRODUCTION: User-uploaded or connected database data
    - DEMO: Curated demo datasets for onboarding/training (opt-in)
    - TEST: Fixtures used in unit/integration tests (never in production)
"""

from __future__ import annotations

import enum
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd


class DataTier(str, enum.Enum):
    PRODUCTION = "production"
    DEMO = "demo"
    TEST = "test"


@dataclass
class ColumnSchema:
    name: str
    dtype: str
    description: str
    nullable: bool = True
    unique: bool = False
    sample_values: list[str] = field(default_factory=list)


@dataclass
class DatasetMetadata:
    source: str
    description: str
    industry: str
    license: str
    version: str
    tags: list[str]
    schema: list[ColumnSchema]
    quality_score: float | None = None
    row_count: int | None = None
    column_count: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "description": self.description,
            "industry": self.industry,
            "license": self.license,
            "version": self.version,
            "tags": self.tags,
            "schema": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "description": c.description,
                    "nullable": c.nullable,
                    "unique": c.unique,
                    "sample_values": c.sample_values,
                }
                for c in self.schema
            ],
            "quality_score": self.quality_score,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DatasetEntry:
    id: str
    name: str
    tier: DataTier
    file_path: str | None
    metadata: DatasetMetadata
    approved_for_demo: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "file_path": self.file_path,
            "approved_for_demo": self.approved_for_demo,
            "metadata": self.metadata.to_dict(),
        }


class DatasetLibrary:
    """Registry of all datasets available to the AEDIP platform.

    Production datasets are registered at runtime (user uploads, database connections).
    Demo datasets are pre-registered from the demo_datasets/ directory.
    Test datasets are only available in test environments.
    """

    def __init__(self):
        self._entries: dict[str, DatasetEntry] = {}
        # Demo datasets are only registered when explicitly opted in via
        # SEED_DEMO_DATA=true. Production must never expose demo data.
        import os as _os

        if _os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes"):
            self._register_demo_datasets()

    def register(self, entry: DatasetEntry) -> None:
        """Register a dataset entry."""
        self._entries[entry.id] = entry

    def unregister(self, dataset_id: str) -> None:
        """Remove a dataset from the library."""
        self._entries.pop(dataset_id, None)

    def get(self, dataset_id: str) -> DatasetEntry | None:
        """Get a dataset entry by ID."""
        return self._entries.get(dataset_id)

    def list_all(self) -> list[DatasetEntry]:
        """List all registered datasets."""
        return list(self._entries.values())

    def list_by_tier(self, tier: DataTier) -> list[DatasetEntry]:
        """List datasets by tier."""
        return [e for e in self._entries.values() if e.tier == tier]

    def list_by_industry(self, industry: str) -> list[DatasetEntry]:
        """List datasets by industry."""
        return [e for e in self._entries.values() if e.metadata.industry == industry]

    def list_demo_approved(self) -> list[DatasetEntry]:
        """List demo datasets approved for use in demo dashboards."""
        return [
            e for e in self._entries.values() if e.tier == DataTier.DEMO and e.approved_for_demo
        ]

    def search(self, query: str) -> list[DatasetEntry]:
        """Search datasets by name, tags, or description."""
        q = query.lower()
        return [
            e
            for e in self._entries.values()
            if q in e.name.lower()
            or q in e.metadata.description.lower()
            or any(q in tag.lower() for tag in e.metadata.tags)
            or q in e.metadata.industry.lower()
        ]

    def load_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Load a dataset as a pandas DataFrame."""
        entry = self.get(dataset_id)
        if not entry:
            raise ValueError(f"Dataset '{dataset_id}' not found in library.")
        if not entry.file_path or not os.path.exists(entry.file_path):
            raise FileNotFoundError(f"Dataset file not found: {entry.file_path}")
        if entry.file_path.endswith(".csv"):
            return pd.read_csv(entry.file_path)
        elif entry.file_path.endswith((".xlsx", ".xls")):
            return pd.read_excel(entry.file_path)
        elif entry.file_path.endswith(".json"):
            return pd.read_json(entry.file_path)
        else:
            raise ValueError(f"Unsupported file format: {entry.file_path}")

    def register_production_upload(
        self,
        dataset_id: str,
        name: str,
        file_path: str,
        industry: str = "unknown",
        description: str = "",
        schema: list[ColumnSchema] | None = None,
        quality_score: float | None = None,
        row_count: int | None = None,
        column_count: int | None = None,
    ) -> DatasetEntry:
        """Register a user-uploaded production dataset."""
        now = datetime.now(timezone.utc).isoformat()
        entry = DatasetEntry(
            id=dataset_id,
            name=name,
            tier=DataTier.PRODUCTION,
            file_path=file_path,
            metadata=DatasetMetadata(
                source="user_upload",
                description=description or f"User-uploaded dataset: {name}",
                industry=industry,
                license="proprietary",
                version="1.0",
                tags=["uploaded", industry],
                schema=schema or [],
                quality_score=quality_score,
                row_count=row_count,
                column_count=column_count,
                created_at=now,
                updated_at=now,
            ),
            approved_for_demo=False,
        )
        self.register(entry)
        return entry

    def register_database_connection(
        self,
        dataset_id: str,
        name: str,
        connection_string: str,
        table_name: str,
        industry: str = "unknown",
        description: str = "",
        schema: list[ColumnSchema] | None = None,
    ) -> DatasetEntry:
        """Register a connected database as a production dataset."""
        now = datetime.now(timezone.utc).isoformat()
        entry = DatasetEntry(
            id=dataset_id,
            name=name,
            tier=DataTier.PRODUCTION,
            file_path=None,
            metadata=DatasetMetadata(
                source=f"database:{table_name}",
                description=description or f"Database table: {table_name}",
                industry=industry,
                license="proprietary",
                version="1.0",
                tags=["database", "connected", industry],
                schema=schema or [],
                created_at=now,
                updated_at=now,
            ),
            approved_for_demo=False,
        )
        self.register(entry)
        return entry

    def _register_demo_datasets(self) -> None:
        """Register all demo datasets from the demo_datasets directory."""
        from config import DEMO_DATASETS_DIR

        demo_defs = _DEMO_DATASET_DEFINITIONS

        for industry, definition in demo_defs.items():
            file_name = f"{industry}_demo.csv"
            file_path = os.path.join(DEMO_DATASETS_DIR, file_name)
            dataset_id = f"demo_{industry}"

            entry = DatasetEntry(
                id=dataset_id,
                name=definition["name"],
                tier=DataTier.DEMO,
                file_path=file_path if os.path.exists(file_path) else None,
                metadata=DatasetMetadata(
                    source="generated_demo",
                    description=definition["description"],
                    industry=industry,
                    license="demo-internal",
                    version="1.0",
                    tags=definition["tags"],
                    schema=[ColumnSchema(**col) for col in definition["schema"]],
                    quality_score=definition.get("quality_score"),
                    row_count=definition.get("row_count"),
                    column_count=len(definition["schema"]),
                ),
                approved_for_demo=True,
            )
            self.register(entry)


# ── Demo dataset definitions with full metadata ──

_DEMO_DATASET_DEFINITIONS: dict[str, dict] = {
    "healthcare": {
        "name": "Healthcare Billing Demo",
        "description": "Demo hospital billing dataset with patient admissions, diagnoses, and insurance data.",
        "tags": ["healthcare", "hospital", "billing", "patient", "demo"],
        "quality_score": 85.0,
        "row_count": 200,
        "schema": [
            {
                "name": "patient_id",
                "dtype": "int64",
                "description": "Unique patient identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2", "3"],
            },
            {
                "name": "patient_name",
                "dtype": "object",
                "description": "Patient full name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Patient 001", "Patient 002"],
            },
            {
                "name": "doctor",
                "dtype": "object",
                "description": "Attending physician",
                "nullable": False,
                "unique": False,
                "sample_values": ["Dr. Smith", "Dr. Jones"],
            },
            {
                "name": "admission_date",
                "dtype": "object",
                "description": "Date of admission (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
            {
                "name": "ward",
                "dtype": "object",
                "description": "Hospital ward",
                "nullable": False,
                "unique": False,
                "sample_values": ["ICU", "General", "Pediatric"],
            },
            {
                "name": "diagnosis",
                "dtype": "object",
                "description": "Primary diagnosis",
                "nullable": False,
                "unique": False,
                "sample_values": ["Flu", "Diabetes", "Hypertension"],
            },
            {
                "name": "medicine",
                "dtype": "object",
                "description": "Prescribed medication",
                "nullable": False,
                "unique": True,
                "sample_values": ["Med-001", "Med-002"],
            },
            {
                "name": "lab_test",
                "dtype": "object",
                "description": "Lab test performed",
                "nullable": False,
                "unique": False,
                "sample_values": ["Blood Test", "X-Ray"],
            },
            {
                "name": "billing",
                "dtype": "int64",
                "description": "Billing amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["500", "5000", "15000"],
            },
            {
                "name": "insurance",
                "dtype": "object",
                "description": "Insurance provider",
                "nullable": False,
                "unique": False,
                "sample_values": ["Aetna", "Cigna", "None"],
            },
        ],
    },
    "education": {
        "name": "Education Enrollment Demo",
        "description": "Demo education dataset with student enrollment, grades, and tuition data.",
        "tags": ["education", "student", "enrollment", "tuition", "demo"],
        "quality_score": 87.0,
        "row_count": 200,
        "schema": [
            {
                "name": "student_id",
                "dtype": "int64",
                "description": "Unique student identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "student_name",
                "dtype": "object",
                "description": "Student full name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Student 001"],
            },
            {
                "name": "teacher",
                "dtype": "object",
                "description": "Assigned teacher",
                "nullable": False,
                "unique": False,
                "sample_values": ["Teacher 01"],
            },
            {
                "name": "course",
                "dtype": "object",
                "description": "Course name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Math", "Science"],
            },
            {
                "name": "department",
                "dtype": "object",
                "description": "Academic department",
                "nullable": False,
                "unique": False,
                "sample_values": ["Engineering", "Arts"],
            },
            {
                "name": "attendance",
                "dtype": "int64",
                "description": "Attendance percentage",
                "nullable": False,
                "unique": False,
                "sample_values": ["85", "92", "100"],
            },
            {
                "name": "exam",
                "dtype": "object",
                "description": "Exam identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["Exam-001"],
            },
            {
                "name": "grade",
                "dtype": "object",
                "description": "Letter grade",
                "nullable": False,
                "unique": False,
                "sample_values": ["A", "B", "C"],
            },
            {
                "name": "fee",
                "dtype": "int64",
                "description": "Tuition fee in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "2500", "5000"],
            },
            {
                "name": "enrollment_date",
                "dtype": "object",
                "description": "Enrollment date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "government": {
        "name": "Government Spending Demo",
        "description": "Demo government dataset with project budgets, procurement, and citizen services.",
        "tags": ["government", "budget", "procurement", "public", "demo"],
        "quality_score": 83.0,
        "row_count": 200,
        "schema": [
            {
                "name": "project_id",
                "dtype": "int64",
                "description": "Unique project identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "project_name",
                "dtype": "object",
                "description": "Project name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Gov Project 001"],
            },
            {
                "name": "department",
                "dtype": "object",
                "description": "Government department",
                "nullable": False,
                "unique": False,
                "sample_values": ["Works", "Health"],
            },
            {
                "name": "budget",
                "dtype": "int64",
                "description": "Project budget in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["10000", "5000000"],
            },
            {
                "name": "procurement",
                "dtype": "object",
                "description": "Tender/procurement ID",
                "nullable": False,
                "unique": True,
                "sample_values": ["Tender-0001"],
            },
            {
                "name": "citizen",
                "dtype": "object",
                "description": "Citizen identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["Citizen 00001"],
            },
            {
                "name": "revenue",
                "dtype": "int64",
                "description": "Revenue generated in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["5000", "2000000"],
            },
            {
                "name": "asset",
                "dtype": "object",
                "description": "Asset identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["Asset-0001"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Record date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "retail": {
        "name": "Retail Sales Demo",
        "description": "Demo retail dataset with product sales, inventory, and regional performance.",
        "tags": ["retail", "sales", "inventory", "product", "demo"],
        "quality_score": 88.0,
        "row_count": 200,
        "schema": [
            {
                "name": "order_id",
                "dtype": "int64",
                "description": "Unique order identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "customer",
                "dtype": "object",
                "description": "Customer name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Customer 001"],
            },
            {
                "name": "product",
                "dtype": "object",
                "description": "Product name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Laptop", "Phone"],
            },
            {
                "name": "supplier",
                "dtype": "object",
                "description": "Supplier name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Supplier 01"],
            },
            {
                "name": "inventory",
                "dtype": "int64",
                "description": "Inventory count",
                "nullable": False,
                "unique": False,
                "sample_values": ["0", "250", "500"],
            },
            {
                "name": "sales",
                "dtype": "int64",
                "description": "Sales amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "5000", "10000"],
            },
            {
                "name": "region",
                "dtype": "object",
                "description": "Sales region",
                "nullable": False,
                "unique": False,
                "sample_values": ["North", "South", "East"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Sale date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "church": {
        "name": " Church Tithes Demo",
        "description": "Demo church dataset with tithes, offerings, and ministry activities.",
        "tags": ["church", "tithe", "offering", "ministry", "demo"],
        "quality_score": 86.0,
        "row_count": 200,
        "schema": [
            {
                "name": "member_id",
                "dtype": "int64",
                "description": "Unique member identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "member_name",
                "dtype": "object",
                "description": "Member full name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Member 001"],
            },
            {
                "name": "visitor",
                "dtype": "object",
                "description": "Visitor name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Visitor 001"],
            },
            {
                "name": "branch",
                "dtype": "object",
                "description": "Church branch",
                "nullable": False,
                "unique": False,
                "sample_values": ["Branch A", "Branch B"],
            },
            {
                "name": "ministry",
                "dtype": "object",
                "description": "Ministry name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Youth", "Music"],
            },
            {
                "name": "tithe",
                "dtype": "int64",
                "description": "Tithe amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["10", "500", "1000"],
            },
            {
                "name": "offering",
                "dtype": "int64",
                "description": "Offering amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["5", "250", "500"],
            },
            {
                "name": "event",
                "dtype": "object",
                "description": "Event name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Service", "Bible Study"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Event date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "ngo": {
        "name": "NGO Donations Demo",
        "description": "Demo NGO dataset with donations, grants, and program impact data.",
        "tags": ["ngo", "donation", "grant", "program", "demo"],
        "quality_score": 84.0,
        "row_count": 200,
        "schema": [
            {
                "name": "beneficiary_id",
                "dtype": "int64",
                "description": "Unique beneficiary identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "beneficiary_name",
                "dtype": "object",
                "description": "Beneficiary name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Beneficiary 001"],
            },
            {
                "name": "donor",
                "dtype": "object",
                "description": "Donor organization",
                "nullable": False,
                "unique": False,
                "sample_values": ["USAID", "UNICEF"],
            },
            {
                "name": "program",
                "dtype": "object",
                "description": "Program name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Health", "Education"],
            },
            {
                "name": "project",
                "dtype": "object",
                "description": "Project identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["Project-0001"],
            },
            {
                "name": "donation",
                "dtype": "int64",
                "description": "Donation amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "25000", "50000"],
            },
            {
                "name": "grant",
                "dtype": "object",
                "description": "Grant identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["Grant-0001"],
            },
            {
                "name": "region",
                "dtype": "object",
                "description": "Geographic region",
                "nullable": False,
                "unique": False,
                "sample_values": ["Africa", "Asia"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Record date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "manufacturing": {
        "name": "Manufacturing Production Demo",
        "description": "Demo manufacturing dataset with machine output, downtime, and operator data.",
        "tags": ["manufacturing", "production", "machine", "output", "demo"],
        "quality_score": 86.0,
        "row_count": 200,
        "schema": [
            {
                "name": "machine_id",
                "dtype": "int64",
                "description": "Unique machine identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "machine_name",
                "dtype": "object",
                "description": "Machine name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Machine-001"],
            },
            {
                "name": "production_id",
                "dtype": "int64",
                "description": "Production run identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1001"],
            },
            {
                "name": "output",
                "dtype": "int64",
                "description": "Production output units",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "2500", "5000"],
            },
            {
                "name": "downtime",
                "dtype": "int64",
                "description": "Downtime in minutes",
                "nullable": False,
                "unique": False,
                "sample_values": ["0", "60", "120"],
            },
            {
                "name": "product",
                "dtype": "object",
                "description": "Product name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Widget A", "Widget B"],
            },
            {
                "name": "operator",
                "dtype": "object",
                "description": "Operator name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Operator 01"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Production date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "agriculture": {
        "name": "Agriculture Harvest Demo",
        "description": "Demo agriculture dataset with crop yields, livestock, and weather data.",
        "tags": ["agriculture", "crop", "harvest", "livestock", "demo"],
        "quality_score": 85.0,
        "row_count": 200,
        "schema": [
            {
                "name": "farm_id",
                "dtype": "int64",
                "description": "Unique farm identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "farm_name",
                "dtype": "object",
                "description": "Farm name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Farm-001"],
            },
            {
                "name": "crop",
                "dtype": "object",
                "description": "Crop type",
                "nullable": False,
                "unique": False,
                "sample_values": ["Maize", "Rice", "Wheat"],
            },
            {
                "name": "harvest",
                "dtype": "int64",
                "description": "Harvest amount in kg",
                "nullable": False,
                "unique": False,
                "sample_values": ["500", "25000", "50000"],
            },
            {
                "name": "livestock",
                "dtype": "int64",
                "description": "Livestock count",
                "nullable": False,
                "unique": False,
                "sample_values": ["10", "250", "500"],
            },
            {
                "name": "rainfall",
                "dtype": "int64",
                "description": "Rainfall in mm",
                "nullable": False,
                "unique": False,
                "sample_values": ["200", "1200", "2000"],
            },
            {
                "name": "temperature",
                "dtype": "float64",
                "description": "Temperature in Celsius",
                "nullable": False,
                "unique": False,
                "sample_values": ["15.0", "28.5", "40.0"],
            },
            {
                "name": "fertilizer",
                "dtype": "object",
                "description": "Fertilizer type",
                "nullable": False,
                "unique": False,
                "sample_values": ["NPK", "Urea"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Record date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "insurance": {
        "name": "Insurance Claims Demo",
        "description": "Demo insurance dataset with policies, claims, and coverage data.",
        "tags": ["insurance", "policy", "claim", "premium", "demo"],
        "quality_score": 87.0,
        "row_count": 200,
        "schema": [
            {
                "name": "policy_id",
                "dtype": "int64",
                "description": "Unique policy identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "policy_number",
                "dtype": "object",
                "description": "Policy number",
                "nullable": False,
                "unique": True,
                "sample_values": ["POL000001"],
            },
            {
                "name": "claim_id",
                "dtype": "int64",
                "description": "Claim identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1001"],
            },
            {
                "name": "agent",
                "dtype": "object",
                "description": "Agent name",
                "nullable": False,
                "unique": False,
                "sample_values": ["Agent 01"],
            },
            {
                "name": "premium",
                "dtype": "int64",
                "description": "Premium amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "5000", "10000"],
            },
            {
                "name": "claim_amount",
                "dtype": "int64",
                "description": "Claim amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["0", "25000", "50000"],
            },
            {
                "name": "coverage",
                "dtype": "object",
                "description": "Coverage type",
                "nullable": False,
                "unique": False,
                "sample_values": ["Auto", "Home", "Life"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Policy date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "hospitality": {
        "name": "Hospitality Reservations Demo",
        "description": "Demo hospitality dataset with guest reservations, room types, and service data.",
        "tags": ["hospitality", "hotel", "reservation", "guest", "demo"],
        "quality_score": 86.0,
        "row_count": 200,
        "schema": [
            {
                "name": "reservation_id",
                "dtype": "int64",
                "description": "Unique reservation identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "guest",
                "dtype": "object",
                "description": "Guest name",
                "nullable": False,
                "unique": True,
                "sample_values": ["Guest 001"],
            },
            {
                "name": "room",
                "dtype": "object",
                "description": "Room type",
                "nullable": False,
                "unique": False,
                "sample_values": ["Single", "Suite", "Deluxe"],
            },
            {
                "name": "booking",
                "dtype": "object",
                "description": "Booking reference",
                "nullable": False,
                "unique": True,
                "sample_values": ["Booking-0001"],
            },
            {
                "name": "service",
                "dtype": "object",
                "description": "Service used",
                "nullable": False,
                "unique": False,
                "sample_values": ["Spa", "Restaurant"],
            },
            {
                "name": "amount",
                "dtype": "int64",
                "description": "Charge amount in USD",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "2500", "5000"],
            },
            {
                "name": "nights",
                "dtype": "int64",
                "description": "Number of nights",
                "nullable": False,
                "unique": False,
                "sample_values": ["1", "7", "14"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Reservation date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
    "telecommunications": {
        "name": "Telecommunications Usage Demo",
        "description": "Demo telecom dataset with subscriber usage, call records, and plan data.",
        "tags": ["telecommunications", "telecom", "subscriber", "usage", "demo"],
        "quality_score": 88.0,
        "row_count": 200,
        "schema": [
            {
                "name": "subscriber_id",
                "dtype": "int64",
                "description": "Unique subscriber identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1", "2"],
            },
            {
                "name": "phone_number",
                "dtype": "object",
                "description": "Phone number",
                "nullable": False,
                "unique": True,
                "sample_values": ["+12345670001"],
            },
            {
                "name": "call_id",
                "dtype": "int64",
                "description": "Call identifier",
                "nullable": False,
                "unique": True,
                "sample_values": ["1001"],
            },
            {
                "name": "plan",
                "dtype": "object",
                "description": "Subscription plan",
                "nullable": False,
                "unique": False,
                "sample_values": ["Basic", "Premium", "Unlimited"],
            },
            {
                "name": "data_usage",
                "dtype": "int64",
                "description": "Data usage in MB",
                "nullable": False,
                "unique": False,
                "sample_values": ["100", "25000", "50000"],
            },
            {
                "name": "minutes",
                "dtype": "int64",
                "description": "Call minutes used",
                "nullable": False,
                "unique": False,
                "sample_values": ["10", "1000", "2000"],
            },
            {
                "name": "sms",
                "dtype": "int64",
                "description": "SMS count",
                "nullable": False,
                "unique": False,
                "sample_values": ["0", "250", "500"],
            },
            {
                "name": "date",
                "dtype": "object",
                "description": "Usage date (YYYY-MM-DD)",
                "nullable": False,
                "unique": False,
                "sample_values": ["2024-01-01"],
            },
        ],
    },
}


# Singleton instance
_library: DatasetLibrary | None = None


def get_dataset_library() -> DatasetLibrary:
    """Get the singleton DatasetLibrary instance."""
    global _library
    if _library is None:
        _library = DatasetLibrary()
    return _library
