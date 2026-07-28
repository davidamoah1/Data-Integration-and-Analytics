# Model Registry

The model registry stores trained models, versions, training runs, predictions, forecasts, and drift records.

## Entities

- `MLModel` — registered model with version, owner, and deployment status
- `MLTrainingRun` — each training or retraining execution
- `MLPrediction` — individual batch predictions
- `MLForecast` — forecast outputs
- `MLAnomalyJob` — anomaly detection job configuration and latest results
- `MLDriftRecord` — drift monitoring events

## Ownership and Isolation

All entities are scoped to an `organization_id` and `created_by` user. Super admins can view models across organizations.

## Lifecycle

1. Create a model record (`POST /ml/models`)
2. Train the model (`POST /ml/models/{id}/train`)
3. Review metrics and deploy (`POST /ml/models/{id}/deploy`)
4. Retrain to create a new version (`POST /ml/models/{id}/retrain`)
5. Detect drift and compare versions
6. Archive or deprecate old versions

## Versioning

- A new `MLModel` starts at version 1.
- Retraining creates a child model with `parent_model_id` and increments the version.
- Users can compare models by metrics and deployment status.

## Example

```python
from ml.service import MLService

service = MLService(db, current_user)
model = service.create_model({
    "name": "Churn Predictor",
    "model_type": "classification",
    "dataset_source": "customers.csv",
    "target_column": "churn"
})
run = service.train_model(model.id, {"include_all": True})
service.update_deployment(model.id, "deployed")
```
