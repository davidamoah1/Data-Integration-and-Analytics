"""REST API routes for the Enterprise Dataset Library."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from dataset_library import DataTier, get_dataset_library
from shared.dependencies import get_current_user, require_permissions

router = APIRouter(prefix="/api/datasets", tags=["Dataset Library"])


class ProductionDatasetCreate(BaseModel):
    name: str
    file_path: str
    industry: str = "unknown"
    description: str = ""
    quality_score: float | None = None


class DatabaseDatasetCreate(BaseModel):
    name: str
    connection_string: str
    table_name: str
    industry: str = "unknown"
    description: str = ""


@router.get("/")
async def list_datasets(
    tier: str | None = Query(None, description="Filter by tier: production, demo, test"),
    industry: str | None = Query(None, description="Filter by industry"),
    search: str | None = Query(None, description="Search query"),
    current_user: dict = Depends(get_current_user),
):
    """List all datasets in the library, optionally filtered."""
    lib = get_dataset_library()
    if search:
        entries = lib.search(search)
    elif tier:
        try:
            data_tier = DataTier(tier.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}") from None
        entries = lib.list_by_tier(data_tier)
    elif industry:
        entries = lib.list_by_industry(industry.lower())
    else:
        entries = lib.list_all()
    return {"datasets": [e.to_dict() for e in entries], "count": len(entries)}


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    """Get metadata for a specific dataset."""
    lib = get_dataset_library()
    entry = lib.get(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return entry.to_dict()


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    rows: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Preview the first N rows of a dataset."""
    lib = get_dataset_library()
    entry = lib.get(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    try:
        df = lib.load_dataframe(dataset_id)
        return {
            "columns": list(df.columns),
            "rows": df.head(rows).fillna("").to_dict(orient="records"),
            "total_rows": len(df),
            "total_columns": len(df.columns),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {e}") from None


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(dataset_id: str, current_user: dict = Depends(get_current_user)):
    """Get the schema for a specific dataset."""
    lib = get_dataset_library()
    entry = lib.get(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return {
        "dataset_id": dataset_id,
        "schema": [c.__dict__ if hasattr(c, "__dict__") else c for c in entry.metadata.schema],
    }


@router.post("/production/upload")
async def register_production_upload(
    dataset: ProductionDatasetCreate,
    current_user: dict = Depends(require_permissions("datasets.manage")),
):
    """Register a user-uploaded production dataset."""
    lib = get_dataset_library()
    import os
    import uuid

    dataset_id = f"prod_{uuid.uuid4().hex[:12]}"

    # Infer schema from file
    schema = []
    row_count = None
    column_count = None
    quality_score = dataset.quality_score

    if os.path.exists(dataset.file_path):
        try:
            df = pd.read_csv(dataset.file_path, nrows=5)
            row_count = len(pd.read_csv(dataset.file_path))
            column_count = len(df.columns)
            for col in df.columns:
                schema.append(
                    {
                        "name": col,
                        "dtype": str(df[col].dtype),
                        "description": "",
                        "nullable": df[col].isna().any(),
                        "unique": False,
                        "sample_values": [str(v) for v in df[col].dropna().head(3).tolist()],
                    }
                )
        except Exception:
            pass

    from dataset_library import ColumnSchema

    entry = lib.register_production_upload(
        dataset_id=dataset_id,
        name=dataset.name,
        file_path=dataset.file_path,
        industry=dataset.industry,
        description=dataset.description,
        schema=[ColumnSchema(**s) for s in schema] if schema else None,
        quality_score=quality_score,
        row_count=row_count,
        column_count=column_count,
    )
    return entry.to_dict()


@router.post("/production/database")
async def register_database_connection(
    dataset: DatabaseDatasetCreate,
    current_user: dict = Depends(require_permissions("datasets.manage")),
):
    """Register a connected database as a production dataset."""
    lib = get_dataset_library()
    import uuid

    dataset_id = f"db_{uuid.uuid4().hex[:12]}"
    entry = lib.register_database_connection(
        dataset_id=dataset_id,
        name=dataset.name,
        connection_string=dataset.connection_string,
        table_name=dataset.table_name,
        industry=dataset.industry,
        description=dataset.description,
    )
    return entry.to_dict()


@router.delete("/{dataset_id}")
async def unregister_dataset(
    dataset_id: str,
    current_user: dict = Depends(require_permissions("datasets.manage")),
):
    """Remove a dataset from the library."""
    lib = get_dataset_library()
    entry = lib.get(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    if entry.tier == DataTier.DEMO:
        raise HTTPException(status_code=403, detail="Demo datasets cannot be removed.")
    lib.unregister(dataset_id)
    return {"message": f"Dataset '{dataset_id}' removed.", "dataset_id": dataset_id}


@router.get("/industries/list")
async def list_industries(current_user: dict = Depends(get_current_user)):
    """List all supported industries."""
    return {
        "industries": [
            "healthcare",
            "education",
            "government",
            "retail",
            "church",
            "ngo",
            "manufacturing",
            "agriculture",
            "insurance",
            "hospitality",
            "telecommunications",
        ]
    }


@router.get("/tiers/list")
async def list_tiers(current_user: dict = Depends(get_current_user)):
    """List all data tiers."""
    return {"tiers": [{"value": t.value, "name": t.value.title()} for t in DataTier]}
