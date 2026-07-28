# ML API

The ML platform exposes secure REST endpoints under `/ml`.

## Authentication

All endpoints require a valid JWT Bearer token. The required permissions are:

- Read operations: `ml.read`
- Create/update models: `ml.write`
- Train/predict/forecast: `ml.execute`
- Archive models: `ml.delete`

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ml/readiness` | ML Readiness Assessment |
| POST | `/ml/features` | Automated Feature Engineering |
| POST | `/ml/models` | Create a model registry entry |
| GET | `/ml/models` | List models (optionally filter by type) |
| GET | `/ml/models/{id}` | Get model details |
| DELETE | `/ml/models/{id}` | Archive a model |
| POST | `/ml/models/{id}/train` | Train a model |
| POST | `/ml/models/{id}/retrain` | Retrain and create a new version |
| POST | `/ml/models/{id}/predict` | Generate predictions |
| POST | `/ml/models/{id}/deploy` | Mark model as deployed |
| POST | `/ml/models/{id}/undeploy` | Mark model as not deployed |
| POST | `/ml/forecast` | Generate forecasts |
| POST | `/ml/anomalies` | Detect anomalies |
| POST | `/ml/recommendations` | Generate decision recommendation |
| POST | `/ml/what-if` | Run scenario simulations |
| POST | `/ml/drift` | Detect data drift |
| POST | `/ml/models/compare` | Compare model metrics |
| GET | `/ml/dashboard` | ML dashboard summary |

## Examples

### Readiness

```bash
curl -X POST http://localhost:8000/ml/readiness \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset_source": "customers.csv", "target_column": "churn"}'
```

### Train and Predict

```bash
# create
curl -X POST http://localhost:8000/ml/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Churn Model","model_type":"classification","dataset_source":"customers.csv","target_column":"churn"}'

# train
curl -X POST http://localhost:8000/ml/models/{id}/train \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"include_all":true}'

# predict
curl -X POST http://localhost:8000/ml/models/{id}/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"features":[{"age":35,"income":50000}]}'
```

### Forecast

```bash
curl -X POST http://localhost:8000/ml/forecast \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset_source":"sales.csv","date_column":"date","target_column":"sales","horizon":30}'
```

### Drift

```bash
curl -X POST http://localhost:8000/ml/drift \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_id":"...","current_dataset_source":"current.csv"}'
```
