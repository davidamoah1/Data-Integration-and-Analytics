"""Data profiling engine â€” computes statistics and quality metrics for a DataFrame."""

from datetime import datetime, timezone

import pandas as pd


class DataProfiler:
    """Profiles a DataFrame and generates a comprehensive data profile report."""

    def profile(self, df: pd.DataFrame, source_name: str = "unknown") -> dict:
        """Generate a full data profile.

        Args:
            df: DataFrame to profile.
            source_name: Name of the data source.

        Returns:
            Dict with profile data including row/column stats, per-column stats,
            and overall quality score.
        """
        profile = {
            "source_name": source_name,
            "profiled_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
        }

        for col in df.columns:
            profile["columns"][col] = self._profile_column(df[col])

        profile["duplicate_rows"] = int(df.duplicated().sum())
        profile["duplicate_percentage"] = round(
            (profile["duplicate_rows"] / max(len(df), 1)) * 100, 2
        )
        profile["quality_score"] = self._compute_quality_score(df, profile)
        return profile

    def _profile_column(self, series: pd.Series) -> dict:
        col_info = {
            "name": series.name,
            "dtype": str(series.dtype),
            "count": int(series.count()),
            "null_count": int(series.isnull().sum()),
            "null_percentage": round((series.isnull().sum() / max(len(series), 1)) * 100, 2),
            "unique_count": int(series.nunique()),
        }

        if pd.api.types.is_numeric_dtype(series):
            col_info.update(self._numeric_stats(series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_info.update(self._datetime_stats(series))
        else:
            col_info.update(self._categorical_stats(series))

        return col_info

    def _numeric_stats(self, series: pd.Series) -> dict:
        clean = series.dropna()
        stats = {
            "min": float(clean.min()) if len(clean) else None,
            "max": float(clean.max()) if len(clean) else None,
            "mean": float(clean.mean()) if len(clean) else None,
            "median": float(clean.median()) if len(clean) else None,
            "std": float(clean.std()) if len(clean) else None,
            "q1": float(clean.quantile(0.25)) if len(clean) else None,
            "q3": float(clean.quantile(0.75)) if len(clean) else None,
            "outliers": int(self._count_outliers(clean)),
        }
        return stats

    def _datetime_stats(self, series: pd.Series) -> dict:
        clean = series.dropna()
        return {
            "min_date": str(clean.min()) if len(clean) else None,
            "max_date": str(clean.max()) if len(clean) else None,
        }

    def _categorical_stats(self, series: pd.Series) -> dict:
        clean = series.dropna().astype(str)
        vc = clean.value_counts()
        return {
            "top_values": vc.head(10).to_dict(),
            "mode": str(clean.mode().iloc[0]) if len(clean) else None,
            "avg_length": round(clean.str.len().mean(), 2) if len(clean) else 0,
        }

    def _count_outliers(self, series: pd.Series) -> int:
        if len(series) < 4:
            return 0
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return int(((series < lower) | (series > upper)).sum())

    def _compute_quality_score(self, df: pd.DataFrame, profile: dict) -> int:
        if len(df) == 0:
            return 0
        total_cells = len(df) * len(df.columns)
        null_cells = int(df.isnull().sum().sum())
        completeness = ((total_cells - null_cells) / max(total_cells, 1)) * 100
        uniqueness = (1 - min(profile["duplicate_percentage"] / 100, 1)) * 100
        return round((completeness * 0.6) + (uniqueness * 0.4))
