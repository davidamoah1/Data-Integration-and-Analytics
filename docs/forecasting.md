# Forecasting

The forecasting engine provides time-series predictions with optional confidence intervals.

## Supported Algorithms

- `ARIMA` — auto-regressive integrated moving average
- `ExponentialSmoothing` — Holt-Winters smoothing
- `Prophet` — optional Facebook Prophet (if installed)
- `auto` — selects the first successful algorithm

## Usage

```python
from ml.forecast import ForecastingEngine
import pandas as pd

df = pd.read_csv("sales.csv")
df["date"] = pd.to_datetime(df["date"])

engine = ForecastingEngine(algorithm="auto")
engine.fit(df, date_col="date", target_col="sales")
forecast = engine.predict(horizon=30)
print(forecast["values"])
print(forecast.get("lower"), forecast.get("upper"))
```

## Horizons

Common horizons used by dashboards and APIs:

- 7 days
- 30 days
- 90 days
- 365 days (1 year)

## API

```http
POST /ml/forecast
{
  "dataset_source": "sales.csv",
  "date_column": "date",
  "target_column": "sales",
  "horizon": 30,
  "frequency": "D",
  "algorithm": "auto"
}
```

## Evaluation

Hold-out evaluation uses MAE, MSE, RMSE, and MAPE from `ml.metrics.forecast_metrics`.
