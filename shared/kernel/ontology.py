from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from semantic.entity_library import ENTITY_LIBRARY
from semantic.knowledge_graph import GraphEdge, GraphNode, KnowledgeGraph


@dataclass(frozen=True)
class OntologyNode:
    id: str
    display_name: str
    description: str
    vocabulary: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    kpis: tuple[str, ...] = ()
    reports: tuple[str, ...] = ()
    dashboards: tuple[str, ...] = ()
    ai_context: dict[str, Any] = field(default_factory=dict)


class OntologyEngine:
    def __init__(self):
        self._nodes: dict[str, OntologyNode] = {}
        self._relationships: dict[str, list[str]] = {}

    def register(self, node: OntologyNode, relationships: list[str] | None = None) -> None:
        self._nodes[node.id] = node
        self._relationships[node.id] = list(relationships or [])

    def get(self, node_id: str) -> OntologyNode:
        return self._nodes[node_id]

    def relationships(self, node_id: str) -> list[str]:
        return list(self._relationships.get(node_id, []))

    def graph_context(self, node_id: str) -> dict[str, Any]:
        node = self.get(node_id)
        return {
            "entity": node.id,
            "vocabulary": list(node.vocabulary),
            "rules": list(node.rules),
            "kpis": list(node.kpis),
            "relationships": self.relationships(node_id),
            "ai_context": node.ai_context,
        }

    @classmethod
    def from_semantic_library(cls) -> OntologyEngine:
        engine = cls()
        for entity_id, entity in ENTITY_LIBRARY.items():
            engine.register(
                OntologyNode(
                    id=entity_id,
                    display_name=entity["display_name"],
                    description=entity.get("description", entity["display_name"]),
                    vocabulary=tuple(entity.get("synonyms", [])),
                    kpis=tuple(entity.get("kpis", [])),
                    ai_context={"industry": entity.get("industry")},
                ),
                entity.get("relationships", []),
            )
        return engine

    def build_knowledge_graph(self) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        for node in self._nodes.values():
            graph.add_node(
                GraphNode(
                    node_id=f"entity:{node.id}",
                    node_type="entity",
                    label=node.display_name,
                    properties={"description": node.description, "vocabulary": list(node.vocabulary)},
                )
            )
        for source, relationships in self._relationships.items():
            for relationship in relationships:
                target = relationship.get("target") if isinstance(relationship, dict) else relationship
                if target not in self._nodes:
                    continue
                edge_type = relationship.get("type", "related_to") if isinstance(relationship, dict) else "related_to"
                graph.add_edge(
                    GraphEdge(source=f"entity:{source}", target=f"entity:{target}", edge_type=edge_type)
                )
        return graph
