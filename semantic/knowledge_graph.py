"""MODULE 8 â€” Knowledge Graph.

Internal knowledge graph representing entities, relationships,
business concepts, KPIs, industry concepts, and AI context.

Used for analytics, AI reasoning, and semantic search.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from semantic.entity_library import ENTITY_LIBRARY
from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE
from semantic.mapping_engine import SemanticMappingResult


@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    node_id: str
    node_type: str  # entity, kpi, industry, concept, column, alert
    label: str
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    source: str
    target: str
    edge_type: str  # has_kpi, related_to, belongs_to_industry, has_alert
    properties: dict = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """Internal knowledge graph."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    node_index: dict[str, GraphNode] = field(default_factory=dict)

    def add_node(self, node: GraphNode):
        if node.node_id not in self.node_index:
            self.nodes.append(node)
            self.node_index[node.node_id] = node

    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self.node_index.get(node_id)

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """Get all nodes connected to the given node."""
        neighbor_ids = set()
        for edge in self.edges:
            if edge.source == node_id:
                neighbor_ids.add(edge.target)
            elif edge.target == node_id:
                neighbor_ids.add(edge.source)
        return [self.node_index[nid] for nid in neighbor_ids if nid in self.node_index]

    def get_nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes if n.node_type == node_type]

    def search(self, query: str) -> list[GraphNode]:
        """Simple text search across node labels and properties."""
        query_lower = query.lower()
        results = []
        for node in self.nodes:
            if query_lower in node.label.lower():
                results.append(node)
            else:
                for v in node.properties.values():
                    if isinstance(v, str) and query_lower in v.lower():
                        results.append(node)
                        break
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str) and query_lower in item.lower():
                                results.append(node)
                                break
        return results

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "type": n.node_type,
                    "label": n.label,
                    "properties": n.properties,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.edge_type,
                    "properties": e.properties,
                }
                for e in self.edges
            ],
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "entity_nodes": len(self.get_nodes_by_type("entity")),
                "kpi_nodes": len(self.get_nodes_by_type("kpi")),
                "industry_nodes": len(self.get_nodes_by_type("industry")),
            },
        }


class KnowledgeGraphBuilder:
    """Builds a knowledge graph from semantic analysis results."""

    @staticmethod
    def build(mapping_result: SemanticMappingResult) -> KnowledgeGraph:
        """Build a knowledge graph from a semantic mapping result.

        Args:
            mapping_result: Result from SemanticMappingEngine.analyze().

        Returns:
            KnowledgeGraph with all entities, KPIs, relationships, and industry concepts.
        """
        graph = KnowledgeGraph()

        # 1. Add industry node
        industry_id = f"industry:{mapping_result.industry}"
        knowledge = INDUSTRY_KNOWLEDGE.get(mapping_result.industry, {})
        graph.add_node(
            GraphNode(
                node_id=industry_id,
                node_type="industry",
                label=knowledge.get("display_name", mapping_result.industry.title()),
                properties={
                    "description": knowledge.get("description", ""),
                    "confidence": mapping_result.industry_confidence,
                },
            )
        )

        # 2. Add entity nodes (detected in the dataset)
        for entity_key in mapping_result.business_entities:
            entity = ENTITY_LIBRARY.get(entity_key)
            if not entity:
                continue

            node_id = f"entity:{entity_key}"
            graph.add_node(
                GraphNode(
                    node_id=node_id,
                    node_type="entity",
                    label=entity["display_name"],
                    properties={
                        "industry": entity["industry"],
                        "synonyms": entity["synonyms"],
                        "attributes": entity["attributes"],
                    },
                )
            )

            # Link entity to industry
            graph.add_edge(
                GraphEdge(
                    source=node_id,
                    target=industry_id,
                    edge_type="belongs_to_industry",
                )
            )

            # 3. Add KPI nodes for each entity
            for kpi in entity["kpis"]:
                kpi_id = f"kpi:{entity_key}:{kpi}"
                graph.add_node(
                    GraphNode(
                        node_id=kpi_id,
                        node_type="kpi",
                        label=kpi.replace("_", " ").title(),
                        properties={
                            "entity": entity_key,
                            "industry": entity["industry"],
                        },
                    )
                )
                graph.add_edge(
                    GraphEdge(
                        source=node_id,
                        target=kpi_id,
                        edge_type="has_kpi",
                    )
                )

        # 4. Add column nodes and link to entities
        for mapping in mapping_result.semantic_result.mappings:
            col_node_id = f"column:{mapping.column_name}"
            graph.add_node(
                GraphNode(
                    node_id=col_node_id,
                    node_type="column",
                    label=mapping.column_name,
                    properties={
                        "entity": mapping.entity_key,
                        "confidence": mapping.confidence,
                        "method": mapping.match_method,
                        "role": mapping.role,
                    },
                )
            )
            entity_node_id = f"entity:{mapping.entity_key}"
            if entity_node_id in graph.node_index:
                graph.add_edge(
                    GraphEdge(
                        source=col_node_id,
                        target=entity_node_id,
                        edge_type="maps_to",
                        properties={"confidence": mapping.confidence},
                    )
                )

        # 5. Add relationship edges between entities
        for rel in mapping_result.relationship_result.relationships:
            source_id = f"entity:{rel.source_entity}"
            target_id = f"entity:{rel.target_entity}"
            if source_id in graph.node_index and target_id in graph.node_index:
                graph.add_edge(
                    GraphEdge(
                        source=source_id,
                        target=target_id,
                        edge_type=rel.relationship_type,
                        properties={
                            "label": rel.label,
                            "confidence": rel.confidence,
                            "detected_via": rel.detected_via,
                        },
                    )
                )

        # 6. Add alert nodes
        for alert in mapping_result.alerts:
            alert_id = f"alert:{alert['metric']}"
            graph.add_node(
                GraphNode(
                    node_id=alert_id,
                    node_type="alert",
                    label=alert["message"],
                    properties=alert,
                )
            )
            graph.add_edge(
                GraphEdge(
                    source=industry_id,
                    target=alert_id,
                    edge_type="has_alert",
                )
            )

        return graph
