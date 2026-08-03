"""Data lineage tracking — records data flow from source through transformations to destination."""

from sqlalchemy.orm import Session as DbSession

from etl.models import ETLDataLineage


class LineageTracker:
    """Tracks data lineage for ETL operations."""

    def __init__(self, db: DbSession):
        self.db = db

    def record(
        self,
        source_name: str,
        source_type: str,
        transformation: str | None = None,
        destination_name: str | None = None,
        destination_type: str | None = None,
        job_id: int | None = None,
        pipeline_id: int | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
        extra_data: dict | None = None,
    ):
        """Record a single lineage entry."""
        entry = ETLDataLineage(
            organization_id=organization_id,
            job_id=job_id,
            pipeline_id=pipeline_id,
            source_name=source_name,
            source_type=source_type,
            transformation=transformation,
            destination_name=destination_name,
            destination_type=destination_type,
            user_id=user_id,
            extra_data=extra_data,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def get_lineage(
        self,
        source_name: str | None = None,
        job_id: int | None = None,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Retrieve lineage entries."""
        query = self.db.query(ETLDataLineage)
        if organization_id is not None:
            query = query.filter(ETLDataLineage.organization_id == organization_id)
        if source_name:
            query = query.filter(ETLDataLineage.source_name == source_name)
        if job_id:
            query = query.filter(ETLDataLineage.job_id == job_id)
        entries = query.order_by(ETLDataLineage.created_at.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "job_id": e.job_id,
                "pipeline_id": e.pipeline_id,
                "source_name": e.source_name,
                "source_type": e.source_type,
                "transformation": e.transformation,
                "destination_name": e.destination_name,
                "destination_type": e.destination_type,
                "user_id": e.user_id,
                "extra_data": e.extra_data,
                "created_at": str(e.created_at) if e.created_at else None,
            }
            for e in entries
        ]

    def build_graph(self, job_id: int | None = None, organization_id: int | None = None) -> dict:
        """Build a lineage graph (nodes + edges) for visualization."""
        entries = self.get_lineage(job_id=job_id, organization_id=organization_id, limit=1000)
        nodes = set()
        edges = []
        for e in entries:
            nodes.add((e["source_name"], e["source_type"]))
            if e["destination_name"]:
                nodes.add((e["destination_name"], e["destination_type"]))
                edges.append(
                    {
                        "source": e["source_name"],
                        "target": e["destination_name"],
                        "transformation": e["transformation"],
                    }
                )
        return {
            "nodes": [{"name": n[0], "type": n[1]} for n in nodes],
            "edges": edges,
        }
