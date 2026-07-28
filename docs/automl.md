# AutoML

The AutoML engine trains, compares, and ranks models across multiple problem types.

## Supported Problem Types

- `classification` — LogisticRegression, RandomForestClassifier, GradientBoostingClassifier
- `regression` — LinearRegression, RandomForestRegressor, GradientBoostingRegressor
- `clustering` — KMeans, DBSCAN, AgglomerativeClustering
- `anomaly_detection` — IsolationForest, LocalOutlierFactor

## How It Works

1. Load and clean the dataset with `ml.features.auto_clean`.
2. Engineer features with `FeatureEngineer`.
3. Pass features and target to `AutoMLEngine`.
4. Review the ranking and select the best model.

## Example

```python
from ml.automl import AutoMLEngine
from ml.features import FeatureEngineer, auto_clean
import pandas as pd

df = pd.read_csv("sales.csv")
df, _ = auto_clean(df)

features = FeatureEngineer({"scaling": "standard"})
X = features.fit_transform(df.drop(columns=["revenue"]), df["revenue"])

automl = AutoMLEngine("regression", algorithm="RandomForestRegressor")
result = automl.run(X, df["revenue"], include_all=True)
print(result["best"]["algorithm"], result["best"]["metrics"])
```

## Ranking

- Classification: highest F1 score
- Regression: lowest RMSE
- Clustering: highest silhouette score
- Anomaly: first successful result

## Registry Integration

Training results are stored in `MLTrainingRun` records and linked to `MLModel` versions. Trained artifacts are saved as `joblib` files.
