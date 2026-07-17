"""Tests for organization and department management."""


class TestOrganizationManagement:
    """Tests for organization CRUD."""

    def test_create_organization(self, client, auth_headers):
        """Test creating an organization."""
        response = client.post(
            "/organizations",
            json={
                "name": "Test Corp",
                "slug": "test-corp",
                "description": "A test organization",
                "contact_email": "info@testcorp.com",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Test Corp"
        assert data["slug"] == "test-corp"

    def test_list_organizations(self, client, auth_headers):
        """Test listing organizations."""
        client.post(
            "/organizations",
            json={
                "name": "List Corp",
                "slug": "list-corp",
            },
            headers=auth_headers,
        )

        response = client.get("/organizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_organization(self, client, auth_headers):
        """Test getting a specific organization."""
        create_resp = client.post(
            "/organizations",
            json={
                "name": "Get Corp",
                "slug": "get-corp",
            },
            headers=auth_headers,
        )
        org_id = create_resp.json()["data"]["id"]

        response = client.get(f"/organizations/{org_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Get Corp"

    def test_update_organization(self, client, auth_headers):
        """Test updating an organization."""
        create_resp = client.post(
            "/organizations",
            json={
                "name": "Update Corp",
                "slug": "update-corp",
            },
            headers=auth_headers,
        )
        org_id = create_resp.json()["data"]["id"]

        response = client.put(
            f"/organizations/{org_id}",
            json={
                "name": "Updated Corp Name",
                "description": "Updated description",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Corp Name"

    def test_delete_organization(self, client, auth_headers):
        """Test deleting an organization."""
        create_resp = client.post(
            "/organizations",
            json={
                "name": "Delete Corp",
                "slug": "delete-corp",
            },
            headers=auth_headers,
        )
        org_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/organizations/{org_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/organizations/{org_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_duplicate_slug(self, client, auth_headers):
        """Test creating an org with a duplicate slug."""
        client.post(
            "/organizations",
            json={
                "name": "First Corp",
                "slug": "dup-slug",
            },
            headers=auth_headers,
        )

        response = client.post(
            "/organizations",
            json={
                "name": "Second Corp",
                "slug": "dup-slug",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409


class TestDepartmentManagement:
    """Tests for department CRUD."""

    def test_create_department(self, client, auth_headers):
        """Test creating a department."""
        # First create an org
        org_resp = client.post(
            "/organizations",
            json={
                "name": "Dept Org",
                "slug": "dept-org",
            },
            headers=auth_headers,
        )
        org_id = org_resp.json()["data"]["id"]

        response = client.post(
            "/departments",
            json={
                "organization_id": org_id,
                "name": "Engineering",
                "code": "ENG",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Engineering"
        assert data["organization_id"] == org_id

    def test_list_departments(self, client, auth_headers):
        """Test listing departments."""
        org_resp = client.post(
            "/organizations",
            json={
                "name": "List Dept Org",
                "slug": "list-dept-org",
            },
            headers=auth_headers,
        )
        org_id = org_resp.json()["data"]["id"]

        client.post(
            "/departments",
            json={
                "organization_id": org_id,
                "name": "Sales Dept",
            },
            headers=auth_headers,
        )

        response = client.get("/departments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_departments_by_org(self, client, auth_headers):
        """Test listing departments filtered by organization."""
        org_resp = client.post(
            "/organizations",
            json={
                "name": "Filter Org",
                "slug": "filter-org",
            },
            headers=auth_headers,
        )
        org_id = org_resp.json()["data"]["id"]

        client.post(
            "/departments",
            json={
                "organization_id": org_id,
                "name": "Marketing",
            },
            headers=auth_headers,
        )

        response = client.get(f"/departments?organization_id={org_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(d["organization_id"] == org_id for d in data)

    def test_update_department(self, client, auth_headers):
        """Test updating a department."""
        org_resp = client.post(
            "/organizations",
            json={
                "name": "Update Dept Org",
                "slug": "update-dept-org",
            },
            headers=auth_headers,
        )
        org_id = org_resp.json()["data"]["id"]

        create_resp = client.post(
            "/departments",
            json={
                "organization_id": org_id,
                "name": "Old Name",
            },
            headers=auth_headers,
        )
        dept_id = create_resp.json()["data"]["id"]

        response = client.put(
            f"/departments/{dept_id}",
            json={
                "name": "New Name",
                "code": "NEW",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "New Name"

    def test_delete_department(self, client, auth_headers):
        """Test deleting a department."""
        org_resp = client.post(
            "/organizations",
            json={
                "name": "Delete Dept Org",
                "slug": "delete-dept-org",
            },
            headers=auth_headers,
        )
        org_id = org_resp.json()["data"]["id"]

        create_resp = client.post(
            "/departments",
            json={
                "organization_id": org_id,
                "name": "Delete Me",
            },
            headers=auth_headers,
        )
        dept_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/departments/{dept_id}", headers=auth_headers)
        assert response.status_code == 200
