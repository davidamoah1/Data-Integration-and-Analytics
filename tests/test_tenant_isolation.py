"""Tests proving that organization A cannot access organization B's data.

These tests verify multi-tenant isolation at the database/query level using
TenantQueryManager and verify_resource_ownership.
"""

import pytest
from sqlalchemy.orm import Session as DbSession

from ai.models import AIConversation, AIInsight, AIWorkflow
from etl.models import ETLPipeline, ETLJob, ETLImportTemplate, ETLTransformation
from shared.exceptions import NotFoundError
from shared.tenant import (
    TenantQueryManager,
    assert_same_organization,
    verify_resource_ownership,
)


@pytest.fixture
def two_orgs(db_session: DbSession):
    """Create two organizations and return their IDs."""
    from organizations.models import Organization

    org_a = Organization(name="Org A", slug="org-a", is_active=1)
    org_b = Organization(name="Org B", slug="org-b", is_active=1)
    db_session.add_all([org_a, org_b])
    db_session.flush()
    return org_a.id, org_b.id


# ─── TenantQueryManager isolation tests ──────────────────────────────


class TestTenantQueryManagerList:
    """Verify that list() only returns records for the specified org."""

    def test_list_only_returns_own_org_records(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        # Create pipelines for both orgs
        db_session.add_all([
            ETLPipeline(organization_id=org_a, name="Pipeline A1", status="active"),
            ETLPipeline(organization_id=org_a, name="Pipeline A2", status="active"),
            ETLPipeline(organization_id=org_b, name="Pipeline B1", status="active"),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        mgr_b = TenantQueryManager(db_session, org_b)

        pipelines_a = mgr_a.list(ETLPipeline)
        pipelines_b = mgr_b.list(ETLPipeline)

        assert len(pipelines_a) == 2
        assert len(pipelines_b) == 1
        assert all(p.name.startswith("Pipeline A") for p in pipelines_a)
        assert all(p.name.startswith("Pipeline B") for p in pipelines_b)

    def test_list_with_filters_still_scoped(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        db_session.add_all([
            ETLPipeline(organization_id=org_a, name="A-active", status="active"),
            ETLPipeline(organization_id=org_a, name="A-inactive", status="inactive"),
            ETLPipeline(organization_id=org_b, name="B-active", status="active"),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        result = mgr_a.list(ETLPipeline, status="active")

        assert len(result) == 1
        assert result[0].name == "A-active"


class TestTenantQueryManagerGet:
    """Verify that get() returns None for cross-org resources."""

    def test_get_returns_none_for_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        pipeline_b = ETLPipeline(organization_id=org_b, name="Secret B", status="active")
        db_session.add(pipeline_b)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        result = mgr_a.get(ETLPipeline, pipeline_b.id)

        assert result is None

    def test_get_returns_record_for_own_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        pipeline_a = ETLPipeline(organization_id=org_a, name="My Pipeline", status="active")
        db_session.add(pipeline_a)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        result = mgr_a.get(ETLPipeline, pipeline_a.id)

        assert result is not None
        assert result.name == "My Pipeline"

    def test_get_or_404_raises_for_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        job_b = ETLJob(organization_id=org_b, job_type="import", status="completed")
        db_session.add(job_b)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        with pytest.raises(NotFoundError):
            mgr_a.get_or_404(ETLJob, job_b.id)


class TestTenantQueryManagerCreate:
    """Verify that create() auto-sets organization_id."""

    def test_create_auto_sets_org_id(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        mgr_a = TenantQueryManager(db_session, org_a)

        record = mgr_a.create(ETLPipeline, name="Auto-org", status="active")
        assert record.organization_id == org_a

    def test_create_does_not_leak_to_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        mgr_a = TenantQueryManager(db_session, org_a)
        mgr_b = TenantQueryManager(db_session, org_b)

        mgr_a.create(ETLPipeline, name="Only A", status="active")
        db_session.flush()

        # Org B should not see it
        result = mgr_b.list(ETLPipeline)
        assert len(result) == 0


class TestTenantQueryManagerUpdate:
    """Verify that update() cannot touch other org's records."""

    def test_update_raises_for_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        pipeline_b = ETLPipeline(organization_id=org_b, name="B Pipeline", status="active")
        db_session.add(pipeline_b)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        with pytest.raises(NotFoundError):
            mgr_a.update(ETLPipeline, pipeline_b.id, name="Hacked")


class TestTenantQueryManagerDelete:
    """Verify that delete() cannot remove other org's records."""

    def test_delete_raises_for_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        template_b = ETLImportTemplate(
            organization_id=org_b, name="B Template",
            source_type="csv", source_config={},
        )
        db_session.add(template_b)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        with pytest.raises(NotFoundError):
            mgr_a.delete(ETLImportTemplate, template_b.id)

        # Verify it still exists
        assert db_session.query(ETLImportTemplate).filter_by(id=template_b.id).first() is not None


class TestTenantQueryManagerCount:
    """Verify that count() only counts own org's records."""

    def test_count_is_org_scoped(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        db_session.add_all([
            ETLJob(organization_id=org_a, job_type="import", status="completed"),
            ETLJob(organization_id=org_a, job_type="import", status="failed"),
            ETLJob(organization_id=org_b, job_type="import", status="completed"),
            ETLJob(organization_id=org_b, job_type="import", status="completed"),
            ETLJob(organization_id=org_b, job_type="import", status="failed"),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        mgr_b = TenantQueryManager(db_session, org_b)

        assert mgr_a.count(ETLJob) == 2
        assert mgr_b.count(ETLJob) == 3
        assert mgr_a.count(ETLJob, status="completed") == 1
        assert mgr_b.count(ETLJob, status="completed") == 2


# ─── verify_resource_ownership tests ─────────────────────────────────


class TestVerifyResourceOwnership:
    """Verify cross-org access prevention via verify_resource_ownership."""

    def test_raises_not_found_for_other_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        pipeline_b = ETLPipeline(organization_id=org_b, name="B Only", status="active")
        db_session.add(pipeline_b)
        db_session.flush()

        with pytest.raises(NotFoundError):
            verify_resource_ownership(db_session, ETLPipeline, pipeline_b.id, org_a)

    def test_returns_record_for_own_org(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        pipeline_a = ETLPipeline(organization_id=org_a, name="A Only", status="active")
        db_session.add(pipeline_a)
        db_session.flush()

        result = verify_resource_ownership(db_session, ETLPipeline, pipeline_a.id, org_a)
        assert result.id == pipeline_a.id

    def test_raises_not_found_for_nonexistent_id(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        with pytest.raises(NotFoundError):
            verify_resource_ownership(db_session, ETLPipeline, 999999, org_a)


# ─── assert_same_organization tests ──────────────────────────────────


class TestAssertSameOrganization:
    """Verify the assert_same_organization guard."""

    def test_passes_for_same_org(self):
        user = {"organization_id": 1, "roles": ["analyst"]}
        assert_same_organization(user, 1)

    def test_raises_for_different_org(self):
        user = {"organization_id": 1, "roles": ["analyst"]}
        with pytest.raises(Exception):
            assert_same_organization(user, 2)

    def test_super_admin_bypasses(self):
        user = {"organization_id": 1, "roles": ["super_admin"]}
        assert_same_organization(user, 2)


# ─── AI model isolation tests ────────────────────────────────────────


class TestAIModelIsolation:
    """Verify AI models are properly isolated by organization_id."""

    def test_ai_conversations_isolated(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        db_session.add_all([
            AIConversation(organization_id=org_a, user_id=1, assistant_type="data_copilot"),
            AIConversation(organization_id=org_a, user_id=1, assistant_type="etl_copilot"),
            AIConversation(organization_id=org_b, user_id=2, assistant_type="data_copilot"),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        mgr_b = TenantQueryManager(db_session, org_b)

        assert len(mgr_a.list(AIConversation)) == 2
        assert len(mgr_b.list(AIConversation)) == 1

    def test_ai_workflow_cross_org_blocked(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        wf_b = AIWorkflow(
            organization_id=org_b, name="B Workflow",
            trigger_type="manual", is_active=True, steps=[],
        )
        db_session.add(wf_b)
        db_session.flush()

        with pytest.raises(NotFoundError):
            verify_resource_ownership(db_session, AIWorkflow, wf_b.id, org_a)

    def test_ai_insight_isolated(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        db_session.add_all([
            AIInsight(organization_id=org_a, title="A insight", insight_type="decision",
                      summary="desc", confidence_score=0.9, is_archived=False),
            AIInsight(organization_id=org_b, title="B insight", insight_type="decision",
                      summary="desc", confidence_score=0.8, is_archived=False),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        insights = mgr_a.list(AIInsight)
        assert len(insights) == 1
        assert insights[0].title == "A insight"


# ─── ETL model isolation tests ───────────────────────────────────────


class TestETLModelIsolation:
    """Verify ETL models are properly isolated by organization_id."""

    def test_etl_transformation_isolated(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        db_session.add_all([
            ETLTransformation(
                organization_id=org_a, name="A transform",
                transformation_type="rename", config={},
            ),
            ETLTransformation(
                organization_id=org_b, name="B transform",
                transformation_type="rename", config={},
            ),
        ])
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        result = mgr_a.list(ETLTransformation)
        assert len(result) == 1
        assert result[0].name == "A transform"

    def test_etl_job_cross_org_blocked(self, db_session, two_orgs):
        org_a, org_b = two_orgs
        job_b = ETLJob(organization_id=org_b, job_type="import", status="running")
        db_session.add(job_b)
        db_session.flush()

        mgr_a = TenantQueryManager(db_session, org_a)
        with pytest.raises(NotFoundError):
            mgr_a.get_or_404(ETLJob, job_b.id)
