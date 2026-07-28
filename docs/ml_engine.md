# ML Engine

The Enterprise ML Decision Intelligence Platform adds machine learning, predictive analytics, and prescriptive recommendations to the existing DataOps platform. The engine is organized into focused modules that can be used independently or through the secure REST API.

## Architecture

```
Dataset Source
     │
     ▼
┌─────────────────────┐
│ ML Readiness        │  → quality score, warnings, algorithm recommendations
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ Feature Engineering │  → cleaning, encoding, scaling, date/rolling/lag features
└─────────────────────┘
     │
     ▼
┌─────────────────────┐     ┌─────────────────────┐
│ AutoML Engine       │────▶│ Model Registry      │
│ (classification,    │     │ (versions, owners)  │
│  regression,        │     └─────────────────────┘
│  clustering,        │
│  anomaly, time      │     ┌─────────────────────┐
│  series)            │────▶│ Forecasting Engine  │
└─────────────────────┘     └─────────────────────┘
     │
     ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Decision Intel.     │     │ Drift Monitoring    │
│ (recommend, what-if)│     └─────────────────────┘
└─────────────────────┘
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `ml.readiness` | Data quality, missing values, outliers, imbalance, forecast suitability |
| `ml.features` | Automated cleaning, encoding, scaling, polynomial, rolling, lag features |
| `ml.automl` | Algorithm training and ranking for classification, regression, clustering, anomaly detection |
| `ml.forecast` | ARIMA, Exponential Smoothing, and optional Prophet forecasting |
| `ml.anomaly` | Isolation Forest, LOF, and z-score spike detection |
| `ml.metrics` | Classification, regression, forecast, clustering, and anomaly metrics |
| `ml.decision` | Narrative recommendations and what-if scenario generation |
| `ml.drift` | KS and chi-squared drift detection |
| `ml.models` | SQLAlchemy registry for models, training runs, predictions, forecasts, drift records |
| `ml.service` | Orchestration layer with tenant isolation and audit logging |
| `ml.routes` | Secure FastAPI endpoints |

## Tenant Isolation

Every ML resource is scoped to `organization_id`. Super admins can see all models; other users see only their organization's models. All operations are written to the audit log.

## Usage

```python
from ml.readiness import assess_ml_readiness
import pandas as pd

df = pd.read_csv("data.csv")
report = assess_ml_readiness(df, target_column="churn")
print(report["quality_score"], report["suggested_algorithms"])
```
