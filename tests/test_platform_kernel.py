import pytest

from shared.contracts.plugins import PluginManifest
from shared.kernel import OntologyEngine, PlatformKernel


def manifest() -> PluginManifest:
    return PluginManifest(
        id="healthcare.executive-advisor",
        name="Healthcare Executive Advisor",
        version="1.0.0",
        plugin_type="ai_agent",
        description="Healthcare executive insights using governed semantic and ontology context.",
        entrypoint="healthcare.advisor",
        permissions=["ai.use"],
        capabilities=["semantic", "healthcare", "ai", "report"],
    )


class TestPlatformKernel:
    def test_kernel_lifecycle_and_event_bus(self):
        kernel = PlatformKernel()
        events = []
        kernel.events.subscribe("kernel.started", events.append)
        kernel.start()
        assert events[0].resource_type == "kernel"

    def test_extension_registry_and_marketplace(self):
        kernel = PlatformKernel()
        plugin_events = []
        kernel.events.subscribe("plugin.installed", plugin_events.append)
        kernel.register_extension(manifest(), author="AEDIP")
        assert kernel.capabilities.supports("healthcare.executive-advisor", "healthcare")
        assert kernel.marketplace["healthcare.executive-advisor"].author == "AEDIP"
        assert plugin_events[0].resource_id == "healthcare.executive-advisor"

    def test_command_and_query_buses(self):
        kernel = PlatformKernel()
        kernel.commands.register("dashboard.create", lambda payload: {"id": payload["id"]})
        kernel.queries.register("dashboard.get", lambda parameters: {"id": parameters["id"]})
        assert kernel.commands.dispatch("dashboard.create", {"id": "d1"}) == {"id": "d1"}
        assert kernel.queries.execute("dashboard.get", {"id": "d1"}) == {"id": "d1"}

    def test_unknown_command_is_rejected(self):
        with pytest.raises(KeyError, match="unknown command"):
            PlatformKernel().commands.dispatch("pipeline.run")

    def test_organization_feature_flag_overrides_global_value(self):
        kernel = PlatformKernel()
        kernel.set_feature("ai.preview", False)
        kernel.set_feature("ai.preview", True, organization_id=7)
        assert not kernel.feature_enabled("ai.preview", organization_id=8)
        assert kernel.feature_enabled("ai.preview", organization_id=7)


class TestOntologyEngine:
    def test_semantic_library_builds_ontology_and_graph(self):
        ontology = OntologyEngine.from_semantic_library()
        patient = ontology.get("patient")
        graph = ontology.build_knowledge_graph()
        assert patient.display_name == "Patient"
        assert graph.get_node("entity:patient") is not None
        assert any(edge.source == "entity:patient" for edge in graph.edges)
