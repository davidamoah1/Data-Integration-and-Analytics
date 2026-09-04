"""Statistics Engine â€” descriptive, inferential, and advanced statistical analysis."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import StatisticalAnalysis


def _safe_float(v: Any, default: float | None = None) -> float | None:
    """Safely convert any value to JSON-compliant float (replacing NaN/Inf with default)."""
    try:
        if v is None:
            return default
        val = float(v)
        if math.isnan(val) or math.isinf(val):
            return default
        return val
    except (TypeError, ValueError, OverflowError):
        return default


class StatisticsService:
    """Professional statistical analysis engine."""

    def __init__(self, db: DbSession):
        self.db = db

    # ══════════════════════════════════════════════════════════════════════════
    # Descriptive Statistics & Dispersion Bounds
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def descriptive(df: pd.DataFrame, columns: list[str] | None = None) -> dict:
        """Compute comprehensive descriptive statistics and dispersion boundaries."""
        if columns is None:
            columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not columns:
                columns = df.columns.tolist()

        results = {}
        for col in columns:
            if col not in df.columns:
                continue
            data = df[col].dropna()

            if pd.api.types.is_numeric_dtype(data) and len(data) > 0:
                count_val = int(data.count())
                mean_val = _safe_float(data.mean())
                median_val = _safe_float(data.median())
                mode_series = data.mode()
                mode_val = _safe_float(mode_series.iloc[0]) if not mode_series.empty else None
                std_val = _safe_float(data.std(), default=0.0) if count_val > 1 else 0.0
                var_val = _safe_float(data.var(), default=0.0) if count_val > 1 else 0.0
                min_val = _safe_float(data.min())
                max_val = _safe_float(data.max())
                range_val = _safe_float(max_val - min_val) if (max_val is not None and min_val is not None) else None
                q1_val = _safe_float(data.quantile(0.25))
                q3_val = _safe_float(data.quantile(0.75))
                iqr_val = _safe_float(q3_val - q1_val) if (q3_val is not None and q1_val is not None) else None
                skew_val = _safe_float(data.skew(), default=0.0) if count_val > 2 else 0.0
                kurt_val = _safe_float(data.kurtosis(), default=0.0) if count_val > 3 else 0.0
                sum_val = _safe_float(data.sum())
                cv_val = _safe_float(std_val / mean_val * 100) if (mean_val and std_val is not None and mean_val != 0) else None

                # Outlier fences (Tukey's IQR method)
                if q1_val is not None and q3_val is not None and iqr_val is not None:
                    lower_bound = round(q1_val - 1.5 * iqr_val, 2)
                    upper_bound = round(q3_val + 1.5 * iqr_val, 2)
                    outliers = data[(data < lower_bound) | (data > upper_bound)]
                    outlier_count = int(len(outliers))
                    outlier_pct = round(outlier_count / max(count_val, 1) * 100, 1)
                else:
                    lower_bound = None
                    upper_bound = None
                    outlier_count = 0
                    outlier_pct = 0.0

                results[col] = {
                    "count": count_val,
                    "mean": mean_val,
                    "median": median_val,
                    "mode": mode_val,
                    "std": std_val,
                    "variance": var_val,
                    "min": min_val,
                    "max": max_val,
                    "range": range_val,
                    "q1": q1_val,
                    "q3": q3_val,
                    "iqr": iqr_val,
                    "skewness": skew_val,
                    "kurtosis": kurt_val,
                    "sum": sum_val,
                    "cv": cv_val,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "outlier_count": outlier_count,
                    "outlier_pct": outlier_pct,
                }
            else:
                # Categorical or non-numeric
                vc = data.value_counts()
                results[col] = {
                    "count": int(data.count()),
                    "unique": int(data.nunique()),
                    "top": str(vc.index[0]) if len(vc) > 0 else None,
                    "freq": int(vc.iloc[0]) if len(vc) > 0 else 0,
                    "value_counts": {str(k): int(v) for k, v in vc.head(20).items()},
                    "mean": None,
                    "median": None,
                    "mode": None,
                    "std": None,
                    "variance": None,
                    "min": None,
                    "max": None,
                    "range": None,
                    "q1": None,
                    "q3": None,
                    "iqr": None,
                    "skewness": None,
                    "kurtosis": None,
                    "sum": None,
                    "cv": None,
                    "lower_bound": None,
                    "upper_bound": None,
                    "outlier_count": 0,
                    "outlier_pct": 0.0,
                }

        return {
            "analysis_type": "descriptive",
            "columns": list(results.keys()),
            "results": results,
            "interpretation": "Descriptive statistics summarize the central tendency, dispersion, and shape of the data distribution.",
        }

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Inferential Statistics
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    @staticmethod
    def ttest(
        df: pd.DataFrame,
        col1: str,
        col2: str | None = None,
        group_col: str | None = None,
        test_type: str = "independent",
        alpha: float = 0.05,
    ) -> dict:
        """Perform t-test (independent, paired, or one-sample)."""
        if test_type == "independent" and group_col:
            groups = df[group_col].unique()
            if len(groups) != 2:
                raise ValueError("Independent t-test requires exactly 2 groups")
            g1 = df[df[group_col] == groups[0]][col1].dropna()
            g2 = df[df[group_col] == groups[1]][col1].dropna()
            t_stat, p_value = sp_stats.ttest_ind(g1, g2)
            test_name = f"Independent t-test: {col1} by {group_col}"
            group_stats = {
                str(groups[0]): {
                    "mean": float(g1.mean()),
                    "std": float(g1.std()),
                    "n": int(len(g1)),
                },
                str(groups[1]): {
                    "mean": float(g2.mean()),
                    "std": float(g2.std()),
                    "n": int(len(g2)),
                },
            }
        elif test_type == "paired" and col2:
            t_stat, p_value = sp_stats.ttest_rel(df[col1].dropna(), df[col2].dropna())
            test_name = f"Paired t-test: {col1} vs {col2}"
            group_stats = {
                col1: {"mean": float(df[col1].mean()), "std": float(df[col1].std())},
                col2: {"mean": float(df[col2].mean()), "std": float(df[col2].std())},
            }
        else:
            # One-sample t-test against population mean of 0
            data = df[col1].dropna()
            t_stat, p_value = sp_stats.ttest_1samp(data, 0)
            test_name = f"One-sample t-test: {col1}"
            group_stats = {
                "mean": float(data.mean()),
                "std": float(data.std()),
                "n": int(len(data)),
            }

        # Effect size (Cohen's d)
        if test_type == "independent" and group_col:
            pooled_std = math.sqrt(
                ((len(g1) - 1) * g1.std() ** 2 + (len(g2) - 1) * g2.std() ** 2)
                / (len(g1) + len(g2) - 2)
            )
            cohens_d = (g1.mean() - g2.mean()) / pooled_std if pooled_std > 0 else 0
        else:
            cohens_d = None

        reject_null = p_value < alpha
        return {
            "test_name": test_name,
            "test_type": "ttest",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "alpha": alpha,
            "degrees_of_freedom": int(len(df) - 2),
            "effect_size": {"cohens_d": float(cohens_d) if cohens_d else None},
            "group_stats": group_stats,
            "reject_null_hypothesis": bool(reject_null),
            "interpretation": (
                f"The t-test result (t={t_stat:.4f}, p={p_value:.4f}) indicates "
                f"{'a significant' if reject_null else 'no significant'} difference. "
                f"{'The null hypothesis is rejected.' if reject_null else 'The null hypothesis cannot be rejected.'}"
            ),
            "assumptions": [
                "Data is approximately normally distributed",
                "Homogeneity of variance (for independent test)",
                "Observations are independent",
            ],
            "limitations": "Results may be affected by outliers or non-normal distributions. Verify assumptions before interpreting.",
        }

    @staticmethod
    def anova(df: pd.DataFrame, value_col: str, group_col: str, alpha: float = 0.05) -> dict:
        """Perform one-way ANOVA."""
        groups = df.groupby(group_col)[value_col]
        group_data = [g.dropna().values for _, g in groups]
        f_stat, p_value = sp_stats.f_oneway(*group_data)

        group_stats = {}
        for name, g in groups:
            group_stats[str(name)] = {
                "mean": float(g.mean()),
                "std": float(g.std()),
                "n": int(g.count()),
            }

        reject_null = p_value < alpha
        return {
            "test_name": f"One-way ANOVA: {value_col} by {group_col}",
            "test_type": "anova",
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "alpha": alpha,
            "degrees_of_freedom_between": int(len(group_data) - 1),
            "degrees_of_freedom_within": int(len(df) - len(group_data)),
            "group_stats": group_stats,
            "reject_null_hypothesis": bool(reject_null),
            "interpretation": (
                f"ANOVA (F={f_stat:.4f}, p={p_value:.4f}) shows "
                f"{'significant' if reject_null else 'no significant'} differences between groups. "
                f"{'At least one group mean differs.' if reject_null else 'Group means are not significantly different.'}"
            ),
            "assumptions": [
                "Normality of residuals",
                "Homogeneity of variance (homoscedasticity)",
                "Independence of observations",
            ],
            "limitations": "ANOVA tells you if differences exist, but not which groups differ. Consider post-hoc tests (Tukey HSD).",
        }

    @staticmethod
    def chi_square(df: pd.DataFrame, col1: str, col2: str, alpha: float = 0.05) -> dict:
        """Perform chi-square test of independence."""
        contingency = pd.crosstab(df[col1], df[col2])
        chi2, p_value, dof, expected = sp_stats.chi2_contingency(contingency)

        return {
            "test_name": f"Chi-square test: {col1} vs {col2}",
            "test_type": "chi_square",
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "alpha": alpha,
            "degrees_of_freedom": int(dof),
            "contingency_table": contingency.to_dict(),
            "reject_null_hypothesis": bool(p_value < alpha),
            "interpretation": (
                f"Chi-square test (Ï‡Â²={chi2:.4f}, p={p_value:.4f}) indicates "
                f"{'a significant association' if p_value < alpha else 'no significant association'} "
                f"between {col1} and {col2}."
            ),
            "assumptions": [
                "Expected cell frequencies â‰¥ 5",
                "Independence of observations",
                "Categorical variables",
            ],
            "limitations": "Chi-square is sensitive to sample size. Large samples may show significance for trivial effects.",
        }

    @staticmethod
    def correlation(
        df: pd.DataFrame, columns: list[str] | None = None, method: str = "pearson"
    ) -> dict:
        """Compute correlation matrix with safe NaN handling."""
        if columns is None:
            columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        if not columns or len(columns) < 2:
            return {
                "test_name": f"{method.capitalize()} correlation",
                "test_type": "correlation",
                "method": method,
                "correlation_matrix": {},
                "matrix": {},
                "strongest_correlations": [],
                "interpretation": "At least 2 numeric columns are required to compute a bivariate correlation matrix.",
                "assumptions": ["Linearity (for Pearson)", "No outliers (for Pearson)"],
                "limitations": "Correlation does not imply causation.",
            }

        # Filter out columns that are all null or have zero variance
        valid_cols = []
        for col in columns:
            series = df[col].dropna()
            if len(series) > 1 and series.std() > 0:
                valid_cols.append(col)

        if len(valid_cols) < 2:
            valid_cols = columns

        corr_df = df[valid_cols].corr(method=method)

        matrix_dict: dict[str, dict[str, float | None]] = {}
        for r_col in corr_df.index:
            matrix_dict[str(r_col)] = {}
            for c_col in corr_df.columns:
                val = corr_df.loc[r_col, c_col]
                matrix_dict[str(r_col)][str(c_col)] = _safe_float(val, default=1.0 if r_col == c_col else 0.0)

        # Find strongest correlations
        pairs = []
        for i in range(len(valid_cols)):
            for j in range(i + 1, len(valid_cols)):
                r = corr_df.iloc[i, j]
                r_clean = _safe_float(r)
                if r_clean is not None:
                    strength = (
                        "strong" if abs(r_clean) >= 0.7 else "moderate" if abs(r_clean) >= 0.4 else "weak"
                    )
                    pairs.append(
                        {
                            "var1": str(valid_cols[i]),
                            "var2": str(valid_cols[j]),
                            "correlation": round(r_clean, 4),
                            "strength": strength,
                            "direction": "positive" if r_clean > 0 else "negative",
                        }
                    )
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "test_name": f"{method.capitalize()} correlation",
            "test_type": "correlation",
            "method": method,
            "correlation_matrix": matrix_dict,
            "matrix": matrix_dict,
            "strongest_correlations": pairs[:10],
            "interpretation": (
                f"Correlation analysis using {method} method across {len(valid_cols)} numeric variables. "
                f"Found {len([p for p in pairs if p['strength'] == 'strong'])} strong correlations. "
                f"Strongest: {pairs[0]['var1']} and {pairs[0]['var2']} (r={pairs[0]['correlation']:.4f})."
                if pairs
                else f"Evaluated {len(valid_cols)} columns; no significant linear dependencies observed."
            ),
            "assumptions": [
                "Linearity (for Pearson)",
                "Normality (for Pearson)",
                "No outliers (for Pearson)",
            ],
            "limitations": "Correlation does not imply causation. Non-linear relationships may exist even when r is low.",
        }

    @staticmethod
    def regression(df: pd.DataFrame, target: str, features: list[str]) -> dict:
        """Perform linear regression analysis."""
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error, r2_score

        X = df[features].dropna()
        y = df.loc[X.index, target].dropna()
        X = X.loc[y.index]

        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        rmse = math.sqrt(mse)

        return {
            "test_name": f"Linear regression: {target} ~ {', '.join(features)}",
            "test_type": "regression",
            "r_squared": float(r2),
            "adjusted_r_squared": float(1 - (1 - r2) * (len(y) - 1) / (len(y) - len(features) - 1)),
            "rmse": float(rmse),
            "mse": float(mse),
            "coefficients": {f: float(c) for f, c in zip(features, model.coef_, strict=False)},
            "intercept": float(model.intercept_),
            "n_observations": int(len(y)),
            "interpretation": (
                f"Regression model explains {r2*100:.1f}% of variance in {target} (RÂ²={r2:.4f}). "
                f"RMSE = {rmse:.4f}. "
                f"{'Good fit.' if r2 >= 0.7 else 'Moderate fit.' if r2 >= 0.4 else 'Poor fit.'}"
            ),
            "assumptions": [
                "Linearity",
                "Independence of residuals",
                "Homoscedasticity",
                "Normality of residuals",
                "No multicollinearity",
            ],
            "limitations": "RÂ² alone doesn't validate the model. Check residual plots and consider cross-validation.",
        }

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Advanced Statistics
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    @staticmethod
    def normality_test(df: pd.DataFrame, column: str) -> dict:
        """Shapiro-Wilk normality test."""
        data = df[column].dropna()
        if len(data) > 5000:
            data = data.sample(5000, random_state=42)
        statistic, p_value = sp_stats.shapiro(data)

        return {
            "test_name": f"Shapiro-Wilk normality test: {column}",
            "test_type": "normality",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_normal": bool(p_value > 0.05),
            "interpretation": (
                f"Shapiro-Wilk test (W={statistic:.4f}, p={p_value:.4f}). "
                f"Data {'appears' if p_value > 0.05 else 'does not appear'} to be normally distributed."
            ),
            "assumptions": ["Random sampling", "Continuous data"],
            "limitations": "Shapiro-Wilk is sensitive to large sample sizes. Consider Q-Q plots for visual assessment.",
        }

    @staticmethod
    def mann_whitney(df: pd.DataFrame, col: str, group_col: str, alpha: float = 0.05) -> dict:
        """Mann-Whitney U test (non-parametric alternative to t-test)."""
        groups = df[group_col].unique()
        if len(groups) != 2:
            raise ValueError("Mann-Whitney U test requires exactly 2 groups")
        g1 = df[df[group_col] == groups[0]][col].dropna()
        g2 = df[df[group_col] == groups[1]][col].dropna()
        statistic, p_value = sp_stats.mannwhitneyu(g1, g2, alternative="two-sided")

        return {
            "test_name": f"Mann-Whitney U test: {col} by {group_col}",
            "test_type": "mann_whitney",
            "u_statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "reject_null_hypothesis": bool(p_value < alpha),
            "interpretation": (
                f"Mann-Whitney U test (U={statistic:.4f}, p={p_value:.4f}). "
                f"{'Significant' if p_value < alpha else 'No significant'} difference between groups."
            ),
            "assumptions": [
                "Independent observations",
                "Ordinal or continuous data",
                "Similar distributions",
            ],
            "limitations": "Non-parametric test â€” use when t-test assumptions are violated.",
        }

    @staticmethod
    def kruskal_wallis(df: pd.DataFrame, col: str, group_col: str, alpha: float = 0.05) -> dict:
        """Kruskal-Wallis H test (non-parametric ANOVA)."""
        groups = df.groupby(group_col)[col]
        group_data = [g.dropna().values for _, g in groups]
        statistic, p_value = sp_stats.kruskal(*group_data)

        return {
            "test_name": f"Kruskal-Wallis test: {col} by {group_col}",
            "test_type": "kruskal_wallis",
            "h_statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "reject_null_hypothesis": bool(p_value < alpha),
            "interpretation": (
                f"Kruskal-Wallis test (H={statistic:.4f}, p={p_value:.4f}). "
                f"{'Significant' if p_value < alpha else 'No significant'} difference between groups."
            ),
            "assumptions": [
                "Independent observations",
                "Ordinal or continuous data",
                "Similar distribution shapes",
            ],
            "limitations": "Non-parametric alternative to ANOVA. Use when normality assumption is violated.",
        }

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Persistence
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def save_analysis(
        self,
        org_id: int,
        dataset_id: int,
        user_id: int,
        analysis_type: str,
        test_name: str | None,
        parameters: dict,
        results: dict,
        interpretation: str,
        assumptions: list[str] | None = None,
        limitations: str | None = None,
    ) -> StatisticalAnalysis:
        analysis = StatisticalAnalysis(
            organization_id=org_id,
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            test_name=test_name,
            parameters=parameters,
            results=results,
            interpretation=interpretation,
            assumptions=assumptions,
            assumptions_met=None,
            limitations=limitations,
            created_by=user_id,
        )
        self.db.add(analysis)
        self.db.commit()
        return analysis

    def list_analyses(
        self, org_id: int, dataset_id: int | None = None
    ) -> list[StatisticalAnalysis]:
        query = select(StatisticalAnalysis).where(StatisticalAnalysis.organization_id == org_id)
        if dataset_id:
            query = query.where(StatisticalAnalysis.dataset_id == dataset_id)
        return (
            self.db.execute(query.order_by(StatisticalAnalysis.created_at.desc())).scalars().all()
        )

    def get_analysis(self, analysis_id: int, org_id: int) -> StatisticalAnalysis | None:
        return self.db.execute(
            select(StatisticalAnalysis).where(
                StatisticalAnalysis.id == analysis_id,
                StatisticalAnalysis.organization_id == org_id,
            )
        ).scalar_one_or_none()
