"""Service layer for dashboard data operations.

Provides a clean interface for the dashboard to query data from either
the database or uploaded files, with caching support.
"""

from datetime import date

import pandas as pd

from database.repositories import SalesRepository
from etl.logging_config import logger


class DashboardDataService:
    """Service for providing data to the dashboard.

    Supports two data sources:
    1. Database mode — queries MySQL/SQLite via SalesRepository
    2. File mode — processes uploaded CSV/Excel files (existing behavior)
    """

    def __init__(self, sales_repo: SalesRepository | None = None):
        """Initialize the dashboard data service.

        Args:
            sales_repo: Sales repository for database queries.
        """
        self.sales_repo = sales_repo or SalesRepository()

    def load_from_database(
        self,
        region: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> pd.DataFrame:
        """Load sales data from the database with optional filters.

        Args:
            region: Filter by region.
            category: Filter by category.
            date_from: Start date filter.
            date_to: End date filter.

        Returns:
            DataFrame of sales records matching the filters.
        """
        logger.info(
            f"DashboardDataService: Loading from database with filters "
            f"region={region}, category={category}, "
            f"date_from={date_from}, date_to={date_to}"
        )
        return self.sales_repo.get_sales_filtered(
            region=region, category=category, date_from=date_from, date_to=date_to
        )

    def get_kpis_from_database(
        self,
        region: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        """Get aggregate KPIs from the database.

        Args:
            region: Filter by region.
            category: Filter by category.
            date_from: Start date filter.
            date_to: End date filter.

        Returns:
            Dict with KPI values.
        """
        return self.sales_repo.get_kpis(
            region=region, category=category, date_from=date_from, date_to=date_to
        )

    def get_filter_options(self) -> dict:
        """Get available filter options from the database.

        Returns:
            Dict with 'regions', 'categories', and 'date_range' keys.
        """
        return {
            "regions": self.sales_repo.get_distinct_values("region"),
            "categories": self.sales_repo.get_distinct_values("category"),
            "date_range": self.sales_repo.get_date_range(),
        }

    def get_record_count(self) -> int:
        """Get total record count from the database.

        Returns:
            Integer count of records.
        """
        return self.sales_repo.get_record_count()

    @staticmethod
    def detect_columns(df: pd.DataFrame) -> dict:
        """Auto-detect and map column name variants to canonical names.

        Args:
            df: Raw DataFrame from uploaded file.

        Returns:
            Dict mapping canonical names to actual column names.
        """
        cols = {c.lower().replace(" ", "_").replace("-", "_"): c for c in df.columns}
        mapping = {}
        for key, variants in {
            "sales": [
                "sales",
                "revenue",
                "amount",
                "total",
                "sale_amount",
                "total_sales",
                "total_revenue",
                "income",
                "turnover",
                "gross",
                "net_revenue",
                "value",
                "cost",
                "fee",
                "tuition",
                "price",
                "grand_total",
                "net_amount",
                "balance",
                "payment",
            ],
            "profit": ["profit", "net_profit", "earnings", "margin"],
            "quantity": ["quantity", "qty", "units", "count", "volume"],
            "discount": ["discount", "disc", "reduction"],
            "order_id": ["order_id", "id", "order_number", "transaction_id", "orderid"],
            "order_date": ["order_date", "date", "purchase_date", "transaction_date", "created_at"],
            "region": ["region", "area", "zone", "territory", "location"],
            "category": [
                "category",
                "type",
                "product_type",
                "segment",
                "class",
                "program_type",
                "service_type",
                "event_type",
                "project_type",
            ],
            "product_name": ["product_name", "product", "item", "item_name", "description"],
            "customer_name": [
                "customer_name",
                "customer",
                "client",
                "buyer",
                "student_name",
                "patient_name",
                "member_name",
                "donor_name",
                "contractor_name",
            ],
            "department": ["department", "dept", "ward", "faculty", "ministry"],
            "insurance_type": ["insurance_type", "insurance", "insurance_provider"],
            "funding_source": ["funding_source", "funding", "fund_source", "donor_type"],
            "payment_method": ["payment_method", "payment_type", "payment_mode", "payment"],
        }.items():
            for v in variants:
                if v in cols:
                    mapping[key] = cols[v]
                    break
        return mapping

    @staticmethod
    def clean_df(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
        """Clean and standardize an uploaded DataFrame.

        Args:
            df: Raw DataFrame.
            col_map: Column mapping from detect_columns().

        Returns:
            Cleaned DataFrame with standardized column names and types.
        """
        df = df.copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
        reverse = {v.lower().replace(" ", "_").replace("-", "_"): k for k, v in col_map.items()}
        df = df.rename(columns=reverse)
        if "order_id" in df.columns:
            df = df.drop_duplicates(subset=["order_id"], keep="first")
        for c in ["sales", "profit", "discount"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        return df
