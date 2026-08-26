"""Tests for ETL API endpoints."""

import io


class TestETLAPI:
    def test_etl_dashboard(self, client, auth_headers):
        resp = client.get("/etl/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_jobs" in data
        assert "running_jobs" in data
        assert "success_rate" in data

    def test_list_pipelines_empty(self, client, auth_headers):
        resp = client.get("/etl/pipelines", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_pipeline(self, client, auth_headers):
        resp = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "API Test Pipeline",
                "description": "Created via API",
                "steps": [
                    {
                        "type": "extract",
                        "source_type": "csv",
                        "source_config": {"file_path": "test.csv"},
                        "source_name": "test.csv",
                    },
                    {"type": "validate"},
                    {"type": "load", "table": "sales", "mode": "insert"},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "API Test Pipeline"
        assert data["current_version"] == 1
        assert len(data["steps"]) == 3

    def test_get_pipeline(self, client, auth_headers):
        create = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "Get Pipeline",
                "steps": [],
            },
        )
        pid = create.json()["id"]
        resp = client.get(f"/etl/pipelines/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Pipeline"

    def test_update_pipeline(self, client, auth_headers):
        create = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "Update Pipeline",
                "steps": [],
            },
        )
        pid = create.json()["id"]
        resp = client.put(
            f"/etl/pipelines/{pid}",
            headers=auth_headers,
            json={
                "steps": [{"type": "extract", "source_type": "json", "source_config": {}}],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["new_version"] == 2

    def test_version_history(self, client, auth_headers):
        create = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "Version Pipeline",
                "steps": [],
            },
        )
        pid = create.json()["id"]
        client.put(f"/etl/pipelines/{pid}", headers=auth_headers, json={"steps": []})
        resp = client.get(f"/etl/pipelines/{pid}/versions", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_rollback(self, client, auth_headers):
        create = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "Rollback Pipeline",
                "steps": [],
            },
        )
        pid = create.json()["id"]
        client.put(f"/etl/pipelines/{pid}", headers=auth_headers, json={"steps": []})
        resp = client.post(
            f"/etl/pipelines/{pid}/rollback", headers=auth_headers, json={"version_number": 1}
        )
        assert resp.status_code == 200
        assert resp.json()["rolled_back_to"] == 1

    def test_list_jobs(self, client, auth_headers):
        resp = client.get("/etl/jobs", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_job_stats(self, client, auth_headers):
        resp = client.get("/etl/jobs/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_jobs" in data
        assert "success_rate" in data

    def test_lineage_graph(self, client, auth_headers):
        resp = client.get("/etl/lineage", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_lineage_entries(self, client, auth_headers):
        resp = client.get("/etl/lineage/entries", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_schedules(self, client, auth_headers):
        resp = client.get("/etl/schedules", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_schedule(self, client, auth_headers):
        create = client.post(
            "/etl/pipelines",
            headers=auth_headers,
            json={
                "name": "Schedule Pipeline",
                "steps": [],
            },
        )
        pid = create.json()["id"]
        resp = client.post(
            "/etl/schedules",
            headers=auth_headers,
            json={
                "pipeline_id": pid,
                "schedule_type": "daily",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["schedule_type"] == "daily"

    def test_list_templates(self, client, auth_headers):
        resp = client.get("/etl/templates", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_ai_hooks(self, client, auth_headers):
        resp = client.get("/etl/ai/hooks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "hooks" in data
        assert len(data["hooks"]) > 0

    def test_transformation_templates(self, client, auth_headers):
        resp = client.post(
            "/etl/transformations/templates",
            headers=auth_headers,
            json={
                "name": "Lower Names",
                "description": "Lowercase name column",
                "transformation_type": "standardize",
                "config": {"column": "name", "operation": "lower"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Lower Names"

    def test_list_transformation_templates(self, client, auth_headers):
        resp = client.get("/etl/transformations/templates", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_upload_file(self, client, auth_headers):
        csv_content = "name,age\nAlice,30\nBob,25\n"
        resp = client.post(
            "/etl/import/upload",
            headers=auth_headers,
            files={"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["row_count"] == 2
        assert "name" in data["columns"]

    def test_import_preview(self, client, auth_headers, tmp_path):
        csv_path = tmp_path / "preview.csv"
        csv_path.write_text("name,age\nAlice,30\nBob,25\n")
        resp = client.post(
            "/etl/import/preview",
            headers=auth_headers,
            json={
                "source_type": "csv",
                "source_config": {"file_path": str(csv_path)},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["row_count"] == 2

    def test_profile_endpoint(self, client, auth_headers, tmp_path):
        csv_path = tmp_path / "profile.csv"
        csv_path.write_text("name,age\nAlice,30\nBob,25\n")
        resp = client.post(
            "/etl/profile",
            headers=auth_headers,
            json={
                "source_type": "csv",
                "source_config": {"file_path": str(csv_path)},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["row_count"] == 2
        assert "quality_score" in data
        assert "columns" in data

    def test_quality_check_endpoint(self, client, auth_headers, tmp_path):
        csv_path = tmp_path / "quality.csv"
        csv_path.write_text("name,email\nAlice,a@test.com\nBob,invalid\n")
        resp = client.post(
            "/etl/quality/check",
            headers=auth_headers,
            json={
                "source_type": "csv",
                "source_config": {"file_path": str(csv_path)},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "checks" in data

    def test_transform_endpoint(self, client, auth_headers, tmp_path):
        csv_path = tmp_path / "transform.csv"
        csv_path.write_text("Name,Age\nAlice,30\nBob,25\n")
        resp = client.post(
            "/etl/transform",
            headers=auth_headers,
            json={
                "source_type": "csv",
                "source_config": {"file_path": str(csv_path)},
                "transformations": [{"type": "rename", "mapping": {"Name": "name"}}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transformations_applied"] == 1

    def test_unauthorized_access(self, client):
        resp = client.get("/etl/pipelines")
        assert resp.status_code in (401, 403)
