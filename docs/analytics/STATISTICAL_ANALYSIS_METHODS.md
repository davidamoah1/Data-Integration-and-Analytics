# Statistical Analysis Methods

This document describes the statistical and analytical methods available in the
Dataflow platform. It covers three complementary layers of analysis:

1. **Core statistics engine** (`studios/statistics_service.py`) — descriptive,
   inferential, and non-parametric statistical tests, exposed through the
   "Pro" analysis mode.
2. **Automated insight detection** (`ai_copilot/insight_generator.py`) — pattern
   detection that runs without an explicit user request, exposed through the
   "Easy" analysis mode.
3. **Industry Intelligence** (`industry_intelligence/`) — sector-specific
   analytics modules that translate raw metrics into domain-relevant KPIs,
   breakdowns, trends, and recommendations.

All three layers operate on a `pandas.DataFrame` produced during the dataset
workflow (upload → profile → clean → analyze) and are surfaced together in the
`Analyze` step of the workflow (`services/dataset_workflow_routes.py`,
`POST /{workflow_id}/analyze`).

## Overview of Methods

| Layer | Module | Purpose |
|---|---|---|
| Descriptive statistics | `StatisticsService.descriptive` | Summarize central tendency, dispersion, and shape of each column |
| Inferential statistics | `StatisticsService.ttest/anova/chi_square/correlation/regression` | Test hypotheses and relationships between variables |
| Non-parametric tests | `StatisticsService.normality_test/mann_whitney/kruskal_wallis` | Robust alternatives when parametric assumptions do not hold |
| Automated insights | `InsightGenerator.generate` | Surface anomalies, trends, correlations, dominance, quality issues, and distribution patterns without a user query |
| Industry intelligence | `industry_intelligence/*.py` | Apply sector-specific KPI logic (retail, healthcare, education, banking, manufacturing, agriculture, government, NGO) |

Every statistical test in `StatisticsService` returns a consistent result
shape: `test_name`, `test_type`, the test statistic(s), `p_value`,
`interpretation` (a plain-language summary), `assumptions` (what must hold for
the test to be valid), and `limitations` (caveats for interpreting the
result). This consistent contract lets the frontend and the AI Copilot render
any test result generically.

## Descriptive Statistics

`StatisticsService.descriptive(df, columns=None)` computes column-level
summaries for either all numeric columns (default) or a specified subset.

For **numeric columns**, it reports:
- `count`, `mean`, `median`, `mode`, `std`, `variance`
- `min`, `max`, `range`
- `q1`, `q3`, `iqr` (interquartile range)
- `skewness`, `kurtosis`
- `sum`
- `cv` (coefficient of variation, as a percentage)

For **categorical columns**, it reports:
- `count`, `unique` (distinct value count)
- `top` and `freq` (most frequent value and its count)
- `value_counts` (top 20 category frequencies)

## Inferential Statistics

All inferential tests are implemented with `scipy.stats` and `scikit-learn`
and are available via `StatisticsService`:

### T-test (`ttest`)
Supports three modes selected via `test_type`:
- `independent` — compares the means of a numeric column across exactly two
  groups defined by `group_col` (`scipy.stats.ttest_ind`); also computes
  **Cohen's d** effect size.
- `paired` — compares two related numeric columns for the same records
  (`scipy.stats.ttest_rel`).
- one-sample (default fallback) — compares a column's mean against 0
  (`scipy.stats.ttest_1samp`).

Returns `t_statistic`, `p_value`, `degrees_of_freedom`, `effect_size`,
`group_stats`, and `reject_null_hypothesis` (based on `alpha`, default 0.05).

### ANOVA (`anova`)
One-way ANOVA (`scipy.stats.f_oneway`) comparing a numeric `value_col` across
multiple groups defined by `group_col`. Returns `f_statistic`, `p_value`,
between/within degrees of freedom, and per-group means/std/n. Notes that
post-hoc tests (e.g., Tukey HSD) are needed to identify which groups differ.

### Chi-Square Test (`chi_square`)
Chi-square test of independence (`scipy.stats.chi2_contingency`) between two
categorical columns, built from a contingency table (`pd.crosstab`). Returns
`chi2_statistic`, `p_value`, `degrees_of_freedom`, and the full
`contingency_table`.

### Correlation (`correlation`)
Computes a correlation matrix (`pearson` by default, or any method supported
by `pandas.DataFrame.corr`) across numeric columns. Identifies the
`strongest_correlations` (top 10 pairs by absolute value), each labeled with
`strength` (`strong` ≥ 0.7, `moderate` ≥ 0.4, `weak` otherwise) and
`direction` (`positive`/`negative`).

### Regression (`regression`)
Linear regression (`sklearn.linear_model.LinearRegression`) predicting a
`target` column from one or more `features`. Returns `r_squared`,
`adjusted_r_squared`, `rmse`, `mse`, per-feature `coefficients`, and
`intercept`.

## Non-parametric Tests

Used when the assumptions of parametric tests (normality, homogeneity of
variance) do not hold:

### Normality Test (`normality_test`)
Shapiro-Wilk test (`scipy.stats.shapiro`) for a single column. Samples down to
5,000 rows for large datasets. Returns `is_normal` (True if `p_value > 0.05`).

### Mann-Whitney U Test (`mann_whitney`)
Non-parametric alternative to the independent t-test
(`scipy.stats.mannwhitneyu`, two-sided) comparing a numeric column across
exactly two groups.

### Kruskal-Wallis Test (`kruskal_wallis`)
Non-parametric alternative to one-way ANOVA (`scipy.stats.kruskal`) comparing
a numeric column across more than two groups.

## Automated Insight Detection

`ai_copilot/insight_generator.py`'s `InsightGenerator.generate(df, col_mapping,
max_insights=15)` runs a set of detectors over the dataset and returns a
prioritized list of `AutoInsight` objects (sorted `critical` → `warning` →
`positive` → `info`). This is the engine behind "Easy" mode analysis and
requires no user-specified test or columns.

Detectors implemented:

- **Anomaly detection** (`_detect_anomalies`) — flags numeric columns with
  outliers using the IQR method (values outside `Q1 - 1.5×IQR` /
  `Q3 + 1.5×IQR`). Severity escalates to `warning` when outliers exceed 10% of
  values.
- **Trend detection** (`_detect_trends`) — finds a date/datetime column, splits
  the time-ordered numeric series in half, and reports a trend when the
  change between first-half and second-half averages exceeds 10%
  (`increasing`/`decreasing`).
- **Correlation detection** (`_detect_correlations`) — computes pairwise
  correlations between numeric columns and reports notable
  strong/moderate relationships along with their direction.
- **Dominance detection** (`_detect_dominance`) — flags categorical columns
  where a single category accounts for more than 60% of records
  (concentration risk), escalating to `warning` above 80%.
- **Data quality issues** (`_detect_quality_issues`) — flags columns with more
  than 20% missing values (`critical` above 50%) and datasets with more than
  5% exact duplicate rows.
- **Distribution patterns** (`_detect_distribution_patterns`) — flags numeric
  columns with notable skew (based on the mean/median/std relationship),
  labeling them left- or right-skewed and suggesting a log transform for
  linear modeling.

Each `AutoInsight` includes a `type`, `severity`, `title`, `description`,
optional `metric`/`value`, and an actionable `recommendation`.

## Industry-Specific Analysis

The `industry_intelligence/` package provides sector-aware analytics that
build on top of raw statistics to produce business-relevant KPIs. Every
sector module subclasses `IndustryAnalytics` (`industry_intelligence/base.py`)
and implements `analyze(df, col_mapping) -> AnalyticsResult`.

Supported sectors (`industry_intelligence/__init__.py`):
- **retail** (`retail.py`) — sales performance, average order value,
  profit/margin, customer analytics (count, revenue per customer), product
  and category breakdowns, inventory and supplier metrics
- **healthcare** (`healthcare.py`) — patient analytics, disease trends, doctor
  performance, revenue
- **education** (`education.py`) — student performance, attendance, fees,
  teacher analytics
- **banking** (`banking.py`) — accounts, transactions, loans, risk
- **manufacturing** (`manufacturing.py`) — production, downtime, quality
- **agriculture** (`agriculture.py`) — production, yield, crop analysis
- **government** (`government.py`) — budget, projects, regional analytics
- **ngo** (`ngo.py`) — donors, programs, beneficiaries, impact

`AnalyticsResult` (`base.py`) is a standard container for:
- `insights`: list of `Insight` (title, value, formatted string, category —
  e.g. `operational`, `financial`, `clinical`, `academic`, `risk` — and an
  optional `alert` level: `ok`/`warning`/`critical`)
- `breakdowns`: list of `Breakdown` (a metric grouped by a dimension, e.g.
  sales by product/category)
- `trends`: list of `Trend` (monthly time series with a computed `direction`:
  `up`/`down`/`stable`)
- `recommendations` and `alerts`: free-text lists

`IndustryAnalytics` provides shared helpers used by all sector modules:
`_find_col` / `_find_numeric_col` / `_find_date_col` (resolve a business
concept, e.g. `"revenue"`, to an actual DataFrame column using a semantic
`col_mapping` or a name heuristic), `_compute_trend` (monthly aggregation with
trend direction), `_compute_breakdown`, and currency/number/percentage
formatters (`_fmt_currency`, `_fmt_number`, `_fmt_pct`).

## Easy vs. Pro Modes

The `Analyze` step of the dataset workflow (`AnalyzeStep.tsx`, backed by
`POST /{workflow_id}/analyze` in `services/dataset_workflow_routes.py`) exposes
two modes via `AnalyzeRequest.mode` (`"easy"` or `"pro"`, default `"easy"`):

- **Easy mode** — designed for non-technical users. The UI presents a natural
  language "Ask Your Data" box with suggested questions. The backend runs
  `InsightGenerator.generate()` (plus the relevant `industry_intelligence`
  analyzer) and returns automated insights and industry analytics without
  requiring the user to choose a test or columns.
- **Pro mode** — designed for analysts/researchers. The UI exposes full
  statistical controls (Descriptive Statistics, Frequency Analysis,
  Cross-Tabulation, Correlation Matrix, Distribution Analysis, etc.). The
  backend dispatches `payload.analysis_type` (one of `descriptive`,
  `correlation`, `ttest`, `anova`, `chi_square`, `regression`, `normality`,
  `mann_whitney`, `kruskal_wallis`) to the matching `StatisticsService` method
  using the user-selected `columns`, `group_column`, and/or `target_column`.

Both modes operate on the same cleaned DataFrame from the workflow and their
results feed into the same downstream Report and Presentation steps (see
`REPORT_AND_PRESENTATION_ENGINE.md`).
