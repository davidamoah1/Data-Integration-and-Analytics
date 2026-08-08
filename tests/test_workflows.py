"""Tests for the enterprise workflow engine."""

from __future__ import annotations

import pytest

from workflows.engine import WorkflowEngine
from workflows.models import WorkflowVersion
from workflows.nodes import NODE_REGISTRY, WorkflowContext
from workflows.service import WorkflowService


class TestNodeRegistry:
    def test_all_required_node_types_registered(self):
        required = {
            "read_csv",
            "read_excel",
            "read_sql",
            "read_rest",
            "read_sftp",
            "validate_data",
            "clean_data",
            "transform_data",
            "aggregate_data",
            "merge_data",
            "join_data",
            "execute_sql",
            "execute_python",
            "ai_analysis",
            "semantic_mapping",
            "metadata_generation",
            "dashboard_generation",
            "report_generation",
            "export_dataset",
            "export_csv",
            "export_excel",
            "export_pdf",
            "save_dataset",
            "archive_dataset",
            "send_email",
            "send_sms",
            "send_webhook",
            "approval_step",
            "manual_review",
        }
        assert required.issubset(set(NODE_REGISTRY.keys()))


class TestWorkflowContext:
    def test_resolve_plain_value(self):
        ctx = WorkflowContext("exec-1", {}, {"name": "Alice"})
        assert ctx.resolve_ref("Alice") == "Alice"

    def test_resolve_reference(self):
        from workflows.nodes import NodeResult

        ctx = WorkflowContext("exec-1", {}, {})
        result = NodeResult(data="hello")
        ctx.set_output("node-1", result)
        assert ctx.resolve_ref("{{node-1.data}}") == "hello"


class TestWorkflowEngineExecution:
    def test_simple_csv_to_validate_workflow(self, db_session):
        nodes = [
            {
                "id": "source",
                "type": "read_csv",
                "config": {
                    "content": "name,age\nAlice,30\nBob,25\n",
                },
            },
            {
                "id": "validate",
                "type": "validate_data",
                "config": {
                    "dataset": "{{source.data}}",
                    "dataset_name": "people.csv",
                },
            },
        ]
        edges = [{"source": "source", "target": "validate"}]
        version = WorkflowVersion(
            workflow_id=1,
            version_number=1,
            status="published",
            nodes=nodes,
            edges=edges,
            config={},
        )
        db_session.add(version)
        db_session.commit()

        engine = WorkflowEngine(db_session)
        execution = engine.execute(
            workflow_id=1,
            version=version,
            triggered_by=1,
            organization_id=1,
            trigger_type="manual",
        )
        assert execution.status == "completed"
        assert "source" in execution.node_results
        assert "validate" in execution.node_results

    def test_failed_node_records_error(self, db_session):
        nodes = [
            {
                "id": "bad_validate",
                "type": "validate_data",
                "config": {
                    "dataset": "missing",
                    "dataset_name": "bad.csv",
                },
            },
        ]
        version = WorkflowVersion(
            workflow_id=2,
            version_number=1,
            status="published",
            nodes=nodes,
            edges=[],
            config={},
        )
        db_session.add(version)
        db_session.commit()

        engine = WorkflowEngine(db_session)
        execution = engine.execute(
            workflow_id=2,
            version=version,
            triggered_by=1,
            organization_id=1,
        )
        assert execution.status == "failed"
        assert execution.errors


class TestWorkflowServiceTenantIsolation:
    def test_user_cannot_access_other_org_workflow(self, db_session):
        service = WorkflowService(db_session, {"id": 1, "organization_id": 1, "roles": ["analyst"]})
        # create a workflow in org 2 directly
        from workflows.models import WorkflowDefinition

        wf = WorkflowDefinition(organization_id=2, created_by=2, name="Other Org")
        db_session.add(wf)
        db_session.commit()

        with pytest.raises(Exception):  # AuthorizationError
            service.get_definition(wf.id)

    def test_super_admin_can_access_any_workflow(self, db_session):
        from workflows.models import WorkflowDefinition

        wf = WorkflowDefinition(organization_id=2, created_by=2, name="Other Org")
        db_session.add(wf)
        db_session.commit()

        service = WorkflowService(
            db_session, {"id": 1, "organization_id": 1, "roles": ["super_admin"]}
        )
        assert service.get_definition(wf.id).name == "Other Org"


class TestWorkflowVersioning:
    def test_publishing_archives_previous_version(self, db_session):
        from workflows.models import WorkflowDefinition

        wf = WorkflowDefinition(organization_id=1, created_by=1, name="Versioned")
        db_session.add(wf)
        db_session.commit()

        v1 = WorkflowVersion(
            workflow_id=wf.id, version_number=1, status="published", nodes=[], edges=[], config={}
        )
        v2 = WorkflowVersion(
            workflow_id=wf.id, version_number=2, status="draft", nodes=[], edges=[], config={}
        )
        db_session.add_all([v1, v2])
        db_session.commit()

        service = WorkflowService(
            db_session, {"id": 1, "organization_id": 1, "roles": ["super_admin"]}
        )
        service.publish_version(wf.id, v2.id)
        db_session.refresh(v1)
        db_session.refresh(v2)
        db_session.refresh(wf)

        assert v1.status == "archived"
        assert v2.status == "published"
        assert wf.published_version_id == v2.id


class TestWorkflowAPI:
    def test_create_and_execute_workflow(self, client, auth_headers):
        create_resp = client.post(
            "/workflows",
            json={
                "name": "Test Workflow",
                "description": "A simple workflow",
                "nodes": [
                    {
                        "id": "source",
                        "type": "read_csv",
                        "config": {"content": "name,age\nAlice,30\n"},
                    },
                    {
                        "id": "meta",
                        "type": "metadata_generation",
                        "config": {"dataset": "{{source.data}}"},
                    },
                ],
                "edges": [{"source": "source", "target": "meta"}],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        wf_id = create_resp.json()["id"]

        # Publish first version
        versions = client.get(f"/workflows/{wf_id}/versions", headers=auth_headers).json()
        version_id = versions[0]["id"]
        pub_resp = client.post(
            f"/workflows/{wf_id}/versions/{version_id}/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 200

        exec_resp = client.post(
            f"/workflows/{wf_id}/execute",
            json={"trigger_type": "manual", "inputs": {}},
            headers=auth_headers,
        )
        assert exec_resp.status_code == 200
        data = exec_resp.json()
        assert data["status"] == "completed"
        assert "source" in data["node_results"]
        assert "meta" in data["node_results"]

    def test_list_workflows(self, client, auth_headers):
        list_resp = client.get("/workflows", headers=auth_headers)
        assert list_resp.status_code == 200
        assert isinstance(list_resp.json(), list)

    def test_node_types_endpoint(self, client, auth_headers):
        resp = client.get("/workflows/node-types", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        types = {n["type"] for n in resp.json()["data"]}
        assert "read_csv" in types
        assert "validate_data" in types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
