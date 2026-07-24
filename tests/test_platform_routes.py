"""Tests for enterprise platform routes — templates, comments, search, branding, industry packs."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DB_TYPE"] = "sqlite"
os.environ["PYTEST_RUNNING"] = "1"


class TestIndustryPacks:
    """Test industry solution pack endpoints."""

    def test_list_industry_packs(self, client, auth_headers):
        resp = client.get("/platform/industry-packs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        pack = data[0]
        assert "key" in pack
        assert "name" in pack
        assert "dashboard_count" in pack
        assert "kpi_count" in pack

    def test_get_specific_pack(self, client, auth_headers):
        resp = client.get("/platform/industry-packs/sme", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "SME" in data["name"]
        assert "dashboards" in data
        assert "kpis" in data

    def test_get_nonexistent_pack(self, client, auth_headers):
        resp = client.get("/platform/industry-packs/nonexistent", headers=auth_headers)
        assert resp.status_code == 404


class TestTemplates:
    """Test template marketplace endpoints."""

    def test_list_templates_empty(self, client, auth_headers):
        resp = client.get("/platform/templates", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_template_as_admin(self, client, auth_headers):
        resp = client.post(
            "/platform/templates",
            headers=auth_headers,
            json={
                "template_type": "dashboard",
                "name": "Test Dashboard Template",
                "description": "A test template",
                "content": {"widgets": []},
                "tags": ["test"],
                "is_public": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Test Dashboard Template"

    def test_get_template(self, client, auth_headers):
        create = client.post(
            "/platform/templates",
            headers=auth_headers,
            json={
                "template_type": "kpi",
                "name": "Test KPI Template",
                "content": {"formula": "SUM(sales)"},
                "is_public": True,
            },
        )
        tid = create.json()["id"]
        resp = client.get(f"/platform/templates/{tid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test KPI Template"

    def test_get_nonexistent_template(self, client, auth_headers):
        resp = client.get("/platform/templates/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_install_template(self, client, auth_headers):
        create = client.post(
            "/platform/templates",
            headers=auth_headers,
            json={
                "template_type": "report",
                "name": "Installable Template",
                "content": {"sections": []},
                "is_public": True,
            },
        )
        tid = create.json()["id"]
        resp = client.post(f"/platform/templates/{tid}/install", headers=auth_headers)
        assert resp.status_code == 200
        assert "installed" in resp.json()["message"] or "already" in resp.json()["message"]

    def test_rate_template(self, client, auth_headers):
        create = client.post(
            "/platform/templates",
            headers=auth_headers,
            json={
                "template_type": "dashboard",
                "name": "Rateable Template",
                "content": {},
                "is_public": True,
            },
        )
        tid = create.json()["id"]
        resp = client.post(f"/platform/templates/{tid}/rate?rating=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["average"] == 5.0
        assert data["count"] == 1


class TestComments:
    """Test collaboration comment endpoints."""

    def test_create_and_list_comment(self, client, auth_headers):
        create = client.post(
            "/platform/comments",
            headers=auth_headers,
            json={
                "resource_type": "dashboard",
                "resource_id": 1,
                "body": "This dashboard needs improvement",
            },
        )
        assert create.status_code == 200
        cid = create.json()["id"]
        assert create.json()["body"] == "This dashboard needs improvement"

        resp = client.get(
            "/platform/comments?resource_type=dashboard&resource_id=1",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        comments = resp.json()
        assert any(c["id"] == cid for c in comments)

    def test_resolve_comment(self, client, auth_headers):
        create = client.post(
            "/platform/comments",
            headers=auth_headers,
            json={
                "resource_type": "kpi",
                "resource_id": 1,
                "body": "Check this KPI",
            },
        )
        cid = create.json()["id"]
        resp = client.post(f"/platform/comments/{cid}/resolve", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Comment resolved"

    def test_resolve_nonexistent_comment(self, client, auth_headers):
        resp = client.post("/platform/comments/99999/resolve", headers=auth_headers)
        assert resp.status_code == 404


class TestSearch:
    """Test enterprise search endpoint."""

    def test_search_returns_results(self, client, auth_headers):
        resp = client.post(
            "/platform/search",
            headers=auth_headers,
            json={"query": "test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "test"
        assert isinstance(data["results"], list)

    def test_search_with_resource_types(self, client, auth_headers):
        resp = client.post(
            "/platform/search",
            headers=auth_headers,
            json={"query": "sales", "resource_types": ["dashboard", "kpi"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        for result in data["results"]:
            assert result["resource_type"] in ("dashboard", "kpi")

    def test_search_empty_query_rejected(self, client, auth_headers):
        resp = client.post(
            "/platform/search",
            headers=auth_headers,
            json={"query": ""},
        )
        assert resp.status_code == 422


class TestBranding:
    """Test organization branding endpoints."""

    def test_get_branding_no_org(self, client, auth_headers):
        resp = client.get("/platform/branding", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "branding" in data

    def test_update_branding_requires_org(self, client, auth_headers):
        resp = client.put(
            "/platform/branding",
            headers=auth_headers,
            json={
                "primary_color": "#FF0000",
                "company_name": "Test Corp",
            },
        )
        assert resp.status_code in (200, 400)


class TestDemoData:
    """Test demo data seeding endpoints."""

    def test_demo_status(self, client, auth_headers):
        resp = client.get("/platform/demo/status", headers=auth_headers)
        assert resp.status_code == 200
        assert "is_seeded" in resp.json()

    def test_seed_demo_data(self, client, auth_headers):
        resp = client.post("/platform/demo/seed", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
