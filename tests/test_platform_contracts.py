from pathlib import Path

import pytest
from pydantic import ValidationError

from shared.contracts.api import PageRequest
from shared.contracts.events import DomainEvent, EventBus
from shared.contracts.models import KPIContract, MetadataContract
from shared.contracts.plugins import IndustryPackDiscovery, PluginLifecycleRegistry, PluginManifest
from shared.contracts.registry import PLATFORM_CONTRACTS


def contract_payload(contract_name: str) -> dict:
    payload = {
        "id": f"core.{contract_name}",
        "display_name": f"Core {contract_name.title()}",
        "description": f"Versioned core contract for the {contract_name} platform capability.",
    }
    if contract_name == "industry_pack":
        payload["industry"] = "healthcare"
    elif contract_name == "kpi":
        payload.update({"industry": "healthcare", "business_entity": "patient", "formula": "count(patient)"})
    elif contract_name == "report":
        payload["industry"] = "healthcare"
    elif contract_name == "connector":
        payload["source_types"] = ["csv"]
    elif contract_name == "ai_agent":
        payload["role"] = "data_copilot"
    elif contract_name == "plugin":
        payload.update({"plugin_type": "widget", "module_path": "plugins.widget"})
    return payload


class TestPlatformContracts:
    def test_all_required_contracts_are_registered(self):
        assert len(PLATFORM_CONTRACTS.names()) == 18
        assert "metadata" in PLATFORM_CONTRACTS.names()
        assert "security" in PLATFORM_CONTRACTS.names()

    @pytest.mark.parametrize("contract_name", PLATFORM_CONTRACTS.names())
    def test_registered_contracts_validate(self, contract_name):
        contract = PLATFORM_CONTRACTS.validate(contract_name, contract_payload(contract_name))
        assert contract.id == f"core.{contract_name}"

    def test_contract_rejects_duplicate_permissions(self):
        with pytest.raises(ValidationError):
            MetadataContract(
                **contract_payload("metadata"),
                permissions=["metadata.read", "metadata.read"],
            )

    def test_kpi_requires_business_definition(self):
        payload = contract_payload("kpi")
        payload["formula"] = ""
        with pytest.raises(ValidationError):
            KPIContract(**payload)


class TestPluginContracts:
    def test_plugin_lifecycle(self):
        manifest = PluginManifest(
            id="healthcare.widgets",
            name="Healthcare Widgets",
            version="1.0.0",
            plugin_type="widget",
            description="Accessible healthcare dashboard widgets for governed KPIs.",
            entrypoint="healthcare_widgets.plugin",
        )
        registry = PluginLifecycleRegistry()
        registry.install(manifest)
        registry.disable(manifest.id)
        assert registry.get(manifest.id)[1].value == "disabled"
        registry.upgrade(manifest.model_copy(update={"version": "1.1.0"}))
        assert registry.get(manifest.id)[0].version == "1.1.0"
        registry.remove(manifest.id)
        assert registry.list() == []

    def test_industry_pack_discovery_requires_contract_layout(self, tmp_path: Path):
        pack = tmp_path / "healthcare"
        for directory in IndustryPackDiscovery.REQUIRED_DIRECTORIES:
            (pack / directory).mkdir(parents=True)
        (pack / "manifest.yaml").write_text(
            "\n".join(
                [
                    "id: healthcare.pack",
                    "name: Healthcare Pack",
                    "version: 1.0.0",
                    "plugin_type: industry_pack",
                    "description: Governed healthcare semantic intelligence pack.",
                    "entrypoint: healthcare.plugin",
                ]
            ),
            encoding="utf-8",
        )
        discovered = IndustryPackDiscovery.discover(tmp_path)
        assert discovered[0][1].id == "healthcare.pack"


class TestAPIAndEvents:
    def test_api_pagination_contract(self):
        assert PageRequest(page=2, page_size=25, filters={"industry": "healthcare"}).page == 2

    def test_event_bus(self):
        received = []
        event_bus = EventBus()
        event_bus.subscribe("dataset.uploaded", received.append)
        event_bus.publish(DomainEvent(event_type="dataset.uploaded", resource_type="dataset", resource_id=1))
        assert received[0].resource_id == 1
