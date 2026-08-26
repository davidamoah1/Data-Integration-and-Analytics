"""ML platform REST API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ml.schemas import (
    AnomalyRequest,
    AnomalyResponse,
    DecisionRecommendationRequest,
    DecisionRecommendationResponse,
    DriftRequest,
    DriftResponse,
    FeatureEngineeringRequest,
    FeatureEngineeringResponse,
    ForecastRequest,
    ForecastResponse,
    MLReadinessRequest,
    MLReadinessResponse,
    ModelCompareRequest,
    ModelCreateRequest,
    ModelResponse,
    PredictRequest,
    PredictResponse,
    TrainingRunResponse,
    WhatIfRequest,
    WhatIfResponse,
)
from ml.service import MLService
from shared.database import get_db
from shared.dependencies import DbSession, require_permissions

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


def get_ml_service(
    db: DbSession = Depends(), current_user: dict = Depends(require_permissions("ml.read"))
) -> MLService:
    return MLService(db, current_user)


@router.post("/readiness", response_model=MLReadinessResponse)
async def ml_readiness(
    req: MLReadinessRequest,
    service: MLService = Depends(get_ml_service),
):
    return service.readiness(req.dataset_source, req.target_column, req.sample_limit)


@router.post("/features", response_model=FeatureEngineeringResponse)
async def engineer_features(
    req: FeatureEngineeringRequest,
    service: MLService = Depends(get_ml_service),
):
    return service.engineer_features(req.dataset_source, req.model_dump())


@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    req: ModelCreateRequest,
    _: dict = Depends(require_permissions("ml.write")),
    service: MLService = Depends(get_ml_service),
):
    return _model_response(service.create_model(req.model_dump()))


@router.get("/models")
async def list_models(
    model_type: str | None = None,
    service: MLService = Depends(get_ml_service),
):
    return [_model_response(m) for m in service.list_models(model_type)]


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, service: MLService = Depends(get_ml_service)):
    return _model_response(service.get_model(model_id))


@router.delete("/models/{model_id}", dependencies=[Depends(require_permissions("ml.delete"))])
async def delete_model(
    model_id: str,
    service: MLService = Depends(get_ml_service),
):
    service.delete_model(model_id)
    return {"success": True, "message": "Model archived"}


@router.post(
    "/models/{model_id}/train",
    response_model=TrainingRunResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def train_model(
    model_id: str,
    payload: dict[str, Any],
    service: MLService = Depends(get_ml_service),
):
    run = service.train_model(model_id, payload)
    return _run_response(run)


@router.post(
    "/models/{model_id}/retrain",
    response_model=TrainingRunResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def retrain_model(
    model_id: str,
    payload: dict[str, Any],
    service: MLService = Depends(get_ml_service),
):
    run = service.retrain_model(model_id, payload)
    return _run_response(run)


def _run_training_in_background(model_id: str, payload: dict[str, Any], user: dict[str, Any]):
    """Run model training outside the request cycle."""
    db = next(get_db())
    try:
        service = MLService(db, user)
        service.train_model(model_id, payload)
    finally:
        db.close()


@router.post("/models/{model_id}/train-async")
async def train_model_async(
    model_id: str,
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_permissions("ml.execute")),
):
    background_tasks.add_task(_run_training_in_background, model_id, payload, current_user)
    return {"success": True, "message": "Training started in background", "model_id": model_id}


@router.post(
    "/models/{model_id}/predict",
    response_model=PredictResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def predict(
    model_id: str,
    req: PredictRequest,
    horizon: int = 30,
    service: MLService = Depends(get_ml_service),
):
    predictions = service.predict(model_id, req.features, horizon=horizon)
    return PredictResponse(model_id=model_id, predictions=predictions)


@router.post("/models/{model_id}/deploy", dependencies=[Depends(require_permissions("ml.write"))])
async def deploy_model(
    model_id: str,
    service: MLService = Depends(get_ml_service),
):
    service.update_deployment(model_id, "deployed")
    return {"success": True, "message": "Model deployed"}


@router.post("/models/{model_id}/undeploy", dependencies=[Depends(require_permissions("ml.write"))])
async def undeploy_model(
    model_id: str,
    service: MLService = Depends(get_ml_service),
):
    service.update_deployment(model_id, "not_deployed")
    return {"success": True, "message": "Model undeployed"}


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def forecast(req: ForecastRequest, service: MLService = Depends(get_ml_service)):
    result = service.forecast(req.model_dump())
    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("errors", "Forecast failed"))
    return ForecastResponse(
        model_id=result.get("model_id", ""),
        algorithm=result["algorithm"],
        horizon=req.horizon,
        forecast=result.get("values", []),
        lower=result.get("lower"),
        upper=result.get("upper"),
    )


@router.post(
    "/anomalies",
    response_model=AnomalyResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def detect_anomalies(req: AnomalyRequest, service: MLService = Depends(get_ml_service)):
    result = service.detect_anomalies(req.model_dump())
    return AnomalyResponse(**result)


@router.post(
    "/recommendations",
    response_model=DecisionRecommendationResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def recommend(
    req: DecisionRecommendationRequest,
    service: MLService = Depends(get_ml_service),
):
    return service.recommend(req.model_dump())


@router.post(
    "/what-if",
    response_model=WhatIfResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def what_if(req: WhatIfRequest, service: MLService = Depends(get_ml_service)):
    return WhatIfResponse(scenarios=service.what_if(req.model_dump()))


@router.post(
    "/drift",
    response_model=DriftResponse,
    dependencies=[Depends(require_permissions("ml.execute"))],
)
async def detect_drift(req: DriftRequest, service: MLService = Depends(get_ml_service)):
    return DriftResponse(**service.detect_drift(req.model_dump()))


@router.get("/dashboard")
async def ml_dashboard(service: MLService = Depends(get_ml_service)):
    return service.dashboard_summary()


@router.post("/models/compare", dependencies=[Depends(require_permissions("ml.execute"))])
async def compare_models(
    req: ModelCompareRequest,
    service: MLService = Depends(get_ml_service),
):
    return service.compare_models(req.model_ids)


def _model_response(model) -> dict[str, Any]:
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "model_type": model.model_type.value,
        "status": model.status.value,
        "algorithm": model.algorithm,
        "target_column": model.target_column,
        "feature_columns": model.feature_columns,
        "metrics": model.metrics,
        "dataset_source": model.dataset_source,
        "version": model.version,
        "deployment_status": model.deployment_status,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def _run_response(run) -> dict[str, Any]:
    return {
        "id": run.id,
        "model_id": run.model_id,
        "status": run.status,
        "algorithm": run.algorithm,
        "train_metrics": run.train_metrics,
        "test_metrics": run.test_metrics,
        "comparison_metrics": run.comparison_metrics,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
