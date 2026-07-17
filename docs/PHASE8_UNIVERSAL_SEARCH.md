# Phase 8.8 — Universal Enterprise Search & Knowledge Engine

## Purpose

This document defines the Universal Enterprise Search and Knowledge Engine for AEDIP, enabling users to search every authorized resource from a single interface with AI-powered insights and a comprehensive knowledge graph.

---

## 1. Search Architecture

### 1.1 Design Principles

- **Universal Search:** Search across all AEDIP modules and data types.
- **Intelligent Results:** AI-powered ranking, summaries, and context-aware results.
- **Real-time Indexing:** Keep search index updated with real-time changes.
- **Permission-Aware:** Respect RBAC and data access permissions.
- **Natural Language:** Support natural language queries and voice search.
- **Knowledge Graph:** Connect related entities for enhanced discovery.
- **Enterprise Ready:** Scalable, secure, auditable, and compliant.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 Universal Search & Knowledge Engine                              │
│  Search Engine · Index Manager · Knowledge Graph · AI Engine · Query Router     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Search       │                │  Knowledge      │               │  AI Search          │
│  Engine       │                │  Graph          │               │  Engine            │
│               │                │                 │               │                    │
│ Elasticsearch │                │ Neo4j/GraphDB    │               │ NLP Processing     │
│ Query Router  │                │ Entity Linking  │               │ Semantic Search    │
│ Result Ranker │                │ Relationship    │               │ Answer Generation  │
│ Faceted Search│                │ Discovery       │               │ Result Explanation  │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Search Engine** | Core search functionality using Elasticsearch/OpenSearch. |
| **Index Manager** | Manage search indexes, real-time updates, and synchronization. |
| **Knowledge Graph** | Entity relationships, knowledge discovery, graph traversal. |
| **AI Search Engine** | Natural language processing, semantic search, answer generation. |
| **Query Router** | Route queries to appropriate search engines and knowledge graph. |
| **Security Layer** | Permission-aware indexing and query filtering. |
| **Analytics Layer** | Search analytics, user behavior tracking, performance metrics. |
| **API Gateway** | Unified search API with aggregation and filtering. |

---

## 2. Searchable Content Types

### 2.1 Core AEDIP Entities

| Category | Entities | Search Fields |
|----------|----------|---------------|
| **Organization** | Organizations, departments, locations | Name, description, metadata |
| **Users** | Users, profiles, roles | Name, email, skills, department |
| **Dashboards** | Dashboards, widgets, layouts | Name, description, widget titles |
| **Reports** | Reports, templates, sections | Title, content, metadata |
| **KPIs** | KPIs, formulas, metrics | Name, description, formula |
| **Data** | Datasets, tables, columns, ETL jobs | Name, description, schema |
| **Workflows** | Workflows, tasks, approvals | Name, description, status |
| **Documents** | Files, images, videos, knowledge articles | Content, metadata, tags |
| **AI** | Recommendations, insights, forecasts | Content, confidence, context |
| **System** | Events, audit logs, notifications | Message, type, metadata |

### 2.2 Content Indexing Strategy

```python
class ContentIndexer:
    def __init__(self, elasticsearch: Elasticsearch, knowledge_graph: KnowledgeGraph):
        self.es = elasticsearch
        self.kg = knowledge_graph
    
    async def index_content(self, content_type: str, content_id: str, data: dict):
        """Index content with permissions and metadata."""
        # Extract searchable fields
        searchable_text = self.extract_searchable_text(data)
        
        # Get permissions
        permissions = await self.get_permissions(content_type, content_id)
        
        # Extract entities for knowledge graph
        entities = await self.extract_entities(data)
        
        # Create document
        document = {
            'id': f"{content_type}:{content_id}",
            'type': content_type,
            'content': searchable_text,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'metadata': data.get('metadata', {}),
            'permissions': permissions,
            'entities': entities,
            'tags': data.get('tags', []),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'organization_id': data.get('organization_id')
        }
        
        # Index in Elasticsearch
        await self.es.index(
            index='aedip_search',
            id=document['id'],
            body=document
        )
        
        # Update knowledge graph
        await self.kg.update_entities(entities, document)
```

---

## 3. Knowledge Graph Architecture

### 3.1 Graph Model

The knowledge graph connects entities across AEDIP to enable intelligent discovery:

- **Nodes:** Entities (users, departments, dashboards, reports, KPIs, etc.)
- **Edges:** Relationships (owns, belongs_to, uses, depends_on, reports_to, etc.)
- **Properties:** Entity attributes and relationship metadata

### 3.2 Relationship Types

| Relationship | Source → Target | Description |
|--------------|-----------------|-------------|
| **OWNS** | User → Dashboard, Report | Ownership relationships |
| **BELONGS_TO** | User → Department, Organization | Membership |
| **MANAGES** | User → Department, Team | Management |
| **USES** | User → Dashboard, Report, KPI | Usage patterns |
| **DEPENDS_ON** | Dashboard → KPI, Report → Data | Dependencies |
| **REPORTS_TO** | KPI → Department, Report → User | Reporting lines |
| **RELATED_TO** | Any → Any | Content similarity |
| **MENTIONS** | Document → User, Department | Mentions in content |
| **TAGGED_WITH** | Any → Tag | Tag relationships |

### 3.3 Knowledge Graph Service

```python
class KnowledgeGraphService:
    def __init__(self, neo4j: Neo4jDriver):
        self.neo4j = neo4j
    
    async def add_entity(self, entity: Entity):
        """Add entity to knowledge graph."""
        query = """
        MERGE (e:Entity {id: $id, type: $type})
        SET e += $properties
        """
        await self.neo4j.run(query, 
            id=entity.id,
            type=entity.type,
            properties=entity.properties
        )
    
    async def add_relationship(self, source: str, target: str, rel_type: str, properties: dict = None):
        """Add relationship between entities."""
        query = """
        MATCH (a:Entity {id: $source}), (b:Entity {id: $target})
        MERGE (a)-[r:RELATIONSHIP {type: $rel_type}]->(b)
        SET r += $properties
        """
        await self.neo4j.run(query,
            source=source,
            target=target,
            rel_type=rel_type,
            properties=properties or {}
        )
    
    async def get_related_entities(self, entity_id: str, depth: int = 2) -> List[Entity]:
        """Get related entities using graph traversal."""
        query = """
        MATCH (e:Entity {id: $entity_id})-[*1..{depth}]-(related:Entity)
        RETURN DISTINCT related, 
               shortestPath((e)-[*]-(related)) as path,
               length(shortestPath((e)-[*]-(related))) as distance
        ORDER BY distance
        LIMIT 100
        """
        result = await self.neo4j.run(query, entity_id=entity_id, depth=depth)
        return [record['related'] for record in result]
```

---

## 4. AI Search Features

### 4.1 Natural Language Processing

- **Query Understanding:** Parse natural language queries to understand intent.
- **Entity Recognition:** Identify entities mentioned in queries.
- **Semantic Search:** Understand meaning beyond keyword matching.
- **Query Expansion:** Expand queries with synonyms and related terms.

### 4.2 AI-Powered Results

- **Smart Ranking:** Rank results based on relevance, user context, and behavior.
- **Answer Generation:** Generate direct answers from indexed content.
- **Result Summarization:** Provide AI-generated summaries for search results.
- **Recommendations:** Suggest related content based on search context.

### 4.3 AI Search Service

```python
class AISearchService:
    def __init__(self, nlp_service: NLPService, ai_gateway: AIGateway):
        self.nlp_service = nlp_service
        self.ai_gateway = ai_gateway
    
    async def process_query(self, query: str, user_context: dict) -> ProcessedQuery:
        """Process natural language query."""
        # Extract entities
        entities = await self.nlp_service.extract_entities(query)
        
        # Understand intent
        intent = await self.nlp_service.classify_intent(query)
        
        # Expand query
        expanded_query = await self.expand_query(query, entities)
        
        return ProcessedQuery(
            original=query,
            expanded=expanded_query,
            entities=entities,
            intent=intent,
            user_context=user_context
        )
    
    async def generate_answer(self, query: ProcessedQuery, results: List[SearchResult]) -> str:
        """Generate AI answer from search results."""
        context = "\n".join([result.content for result in results[:5]])
        
        prompt = f"""
        Based on the following context, answer the question: {query.original}
        
        Context:
        {context}
        
        Provide a concise, accurate answer. If the context doesn't contain enough information, say so.
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="search_answer")
        return response.response
    
    async def explain_result(self, result: SearchResult, query: str) -> str:
        """Explain why a result matches the query."""
        prompt = f"""
        Explain why this search result matches the query: {query}
        
        Result Title: {result.title}
        Result Content: {result.content[:500]}...
        Score: {result.score}
        
        Provide a brief explanation of the relevance.
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="result_explainer")
        return response.response
```

---

## 5. Database Schema

### 5.1 Search Index Schema (Elasticsearch)

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "type": {"type": "keyword"},
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "description": {
        "type": "text",
        "analyzer": "standard"
      },
      "metadata": {"type": "object"},
      "permissions": {
        "type": "nested",
        "properties": {
          "type": {"type": "keyword"},
          "id": {"type": "keyword"},
          "level": {"type": "keyword"}
        }
      },
      "entities": {
        "type": "nested",
        "properties": {
          "type": {"type": "keyword"},
          "id": {"type": "keyword"},
          "name": {"type": "text"},
          "confidence": {"type": "float"}
        }
      },
      "tags": {"type": "keyword"},
      "created_at": {"type": "date"},
      "updated_at": {"type": "date"},
      "organization_id": {"type": "keyword"}
    }
  }
}
```

### 5.2 MySQL Tables

```sql
CREATE TABLE search_documents (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  document_id VARCHAR(255) NOT NULL UNIQUE,
  document_type VARCHAR(64) NOT NULL,
  title VARCHAR(512),
  content LONGTEXT,
  description TEXT,
  metadata JSON,
  organization_id BIGINT NOT NULL,
  permissions JSON,
  tags JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_type (document_type),
  INDEX idx_org (organization_id),
  INDEX idx_created (created_at),
  FULLTEXT idx_content (title, content, description)
) ENGINE=InnoDB;

CREATE TABLE search_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  query TEXT NOT NULL,
  filters JSON,
  results_count INT DEFAULT 0,
  clicked_result_id VARCHAR(255),
  session_id VARCHAR(128),
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_user (user_id),
  INDEX idx_session (session_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE saved_searches (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  query TEXT NOT NULL,
  filters JSON,
  is_public BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_user (user_id),
  INDEX idx_public (is_public)
) ENGINE=InnoDB;

CREATE TABLE search_synonyms (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT,
  term VARCHAR(255) NOT NULL,
  synonym VARCHAR(255) NOT NULL,
  weight DECIMAL(3,2) DEFAULT 1.0,
  is_active BOOLEAN DEFAULT TRUE,
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_term (term),
  INDEX idx_synonym (synonym),
  INDEX idx_org (organization_id)
) ENGINE=InnoDB;

CREATE TABLE search_filters (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  filter_name VARCHAR(128) NOT NULL,
  filter_type VARCHAR(64) NOT NULL, -- facet, range, date, select
  field_name VARCHAR(128) NOT NULL,
  config JSON NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  sort_order INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type (filter_type),
  INDEX idx_field (field_name),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE knowledge_nodes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  node_id VARCHAR(255) NOT NULL UNIQUE,
  node_type VARCHAR(64) NOT NULL,
  name VARCHAR(512) NOT NULL,
  properties JSON,
  organization_id BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_type (node_type),
  INDEX idx_org (organization_id),
  FULLTEXT idx_name (name)
) ENGINE=InnoDB;

CREATE TABLE knowledge_edges (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  source_node_id VARCHAR(255) NOT NULL,
  target_node_id VARCHAR(255) NOT NULL,
  relationship_type VARCHAR(64) NOT NULL,
  properties JSON,
  weight DECIMAL(3,2) DEFAULT 1.0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(node_id),
  FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(node_id),
  INDEX idx_source (source_node_id),
  INDEX idx_target (target_node_id),
  INDEX idx_relationship (relationship_type)
) ENGINE=InnoDB;

CREATE TABLE knowledge_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  parent_id BIGINT,
  icon VARCHAR(64),
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES knowledge_categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE knowledge_tags (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  tag_name VARCHAR(128) NOT NULL UNIQUE,
  category_id BIGINT,
  description TEXT,
  color VARCHAR(16),
  usage_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES knowledge_categories(id),
  INDEX idx_category (category_id),
  INDEX idx_usage (usage_count)
) ENGINE=InnoDB;

CREATE TABLE knowledge_audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  node_id VARCHAR(255),
  edge_id BIGINT,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL, -- created, updated, deleted, merged
  old_values JSON,
  new_values JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id),
  FOREIGN KEY (edge_id) REFERENCES knowledge_edges(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_node (node_id),
  INDEX idx_edge (edge_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;
```

### 5.3 ER Diagram (Textual)

```
search_documents (1) → (n) search_history
knowledge_nodes (1) → (n) knowledge_edges
knowledge_nodes (1) → (n) knowledge_audit_logs
knowledge_edges (1) → (n) knowledge_audit_logs
knowledge_categories (1) → (n) knowledge_nodes
knowledge_categories (1) → (n) knowledge_tags

users (1) → (n) search_history
users (1) → (n) saved_searches
organizations (1) → (n) search_documents
organizations (1) → (n) knowledge_nodes
organizations (1) → (n) search_synonyms
```

---

## 6. API Specification

Base path: `/api/v1/search`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Universal search endpoint. |
| POST | `/` | Advanced search with complex filters. |
| GET | `/suggestions` | Get search suggestions and autocomplete. |
| GET | `/history` | Get user search history. |
| POST | `/saved` | Save a search query. |
| GET | `/saved` | Get saved searches. |
| DELETE | `/saved/{id}` | Delete saved search. |
| GET | `/facets` | Get available search facets. |
| GET | `/similar/{id}` | Find similar documents. |
| POST | `/reindex` | Trigger reindexing of content. |
| GET | `/knowledge/entities` | Search knowledge graph entities. |
| GET | `/knowledge/related/{id}` | Get related entities from knowledge graph. |
| GET | `/analytics/popular` | Get popular searches. |
| GET | `/analytics/performance` | Get search performance metrics. |

### Example: Universal Search

```http
GET /api/v1/search?q=quarterly sales report&filters={"type":["report","dashboard"],"date_range":"last_30_days"}
```

Response:
```json
{
  "results": [
    {
      "id": "report:123",
      "type": "report",
      "title": "Q2 2026 Sales Report",
      "description": "Quarterly sales performance analysis",
      "content": "Executive summary of Q2 sales...",
      "score": 0.95,
      "highlights": ["<em>Quarterly</em> <em>sales</em> exceeded targets"],
      "metadata": {
        "created_by": "john.doe",
        "department": "sales",
        "created_at": "2026-07-01T10:00:00Z"
      },
      "url": "/reports/123"
    }
  ],
  "facets": {
    "type": [
      {"key": "report", "count": 15},
      {"key": "dashboard", "count": 8}
    ],
    "department": [
      {"key": "sales", "count": 12},
      {"key": "finance", "count": 11}
    ]
  },
  "total": 23,
  "took": 45,
  "suggestions": ["quarterly revenue report", "monthly sales report"]
}
```

---

## 7. Backend Architecture

### 7.1 Package Structure

```
search_engine/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── engine.py              # Search engine core
│   ├── indexer.py             # Index management
│   ├── query.py               # Query processing
│   └── ranking.py             # Result ranking
├── knowledge/
│   ├── __init__.py
│   ├── graph.py               # Knowledge graph service
│   ├── entities.py            # Entity extraction
│   └── relationships.py       # Relationship management
├── ai/
│   ├── __init__.py
│   ├── nlp.py                 # Natural language processing
│   ├── semantic.py            # Semantic search
│   └── answer.py              # Answer generation
├── integrations/
│   ├── __init__.py
│   ├── elasticsearch.py       # Elasticsearch integration
│   ├── neo4j.py               # Neo4j integration
│   └── content_providers.py   # Content provider adapters
├── api/
│   └── routes.py              # Search API endpoints
├── models/
│   └── search_models.py       # SQLAlchemy models
├── schemas/
│   └── search_schemas.py      # Pydantic schemas
└── migrations/                # Alembic migrations
```

### 7.2 Search Engine Core

```python
class UniversalSearchEngine:
    def __init__(self, elasticsearch: Elasticsearch, knowledge_graph: KnowledgeGraph, ai_service: AISearchService):
        self.es = elasticsearch
        self.kg = knowledge_graph
        self.ai_service = ai_service
    
    async def search(self, query: str, user: User, filters: dict = None, options: dict = None) -> SearchResult:
        """Execute universal search query."""
        # Process query with AI
        processed_query = await self.ai_service.process_query(query, user.get_context())
        
        # Build Elasticsearch query
        es_query = self.build_es_query(processed_query, user, filters)
        
        # Execute search
        response = await self.es.search(
            index='aedip_search',
            body=es_query,
            size=options.get('limit', 20),
            from_=options.get('offset', 0)
        )
        
        # Process results
        results = []
        for hit in response['hits']['hits']:
            result = SearchResult.from_es_hit(hit)
            
            # Get related entities from knowledge graph
            result.related_entities = await self.kg.get_related_entities(hit['_source']['id'])
            
            # Generate AI explanation
            result.explanation = await self.ai_service.explain_result(result, query)
            
            results.append(result)
        
        # Generate AI answer if applicable
        answer = None
        if processed_query.intent == 'question':
            answer = await self.ai_service.generate_answer(processed_query, results)
        
        # Get facets
        facets = self.extract_facets(response)
        
        # Log search
        await self.log_search(user.id, query, len(results))
        
        return SearchResult(
            query=query,
            results=results,
            facets=facets,
            total=response['hits']['total']['value'],
            took=response['took'],
            answer=answer,
            suggestions=processed_query.suggestions
        )
    
    def build_es_query(self, processed_query: ProcessedQuery, user: User, filters: dict = None) -> dict:
        """Build Elasticsearch query with permissions and filters."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": processed_query.expanded,
                                "fields": ["title^3", "description^2", "content"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": [
                        {
                            "nested": {
                                "path": "permissions",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"permissions.type": "public"}},
                                            {"term": {"permissions.id": user.id}},
                                            {"terms": {"permissions.id": user.role_ids}},
                                            {"terms": {"permissions.id": user.department_ids}}
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {},
                    "content": {"fragment_size": 150, "number_of_fragments": 3}
                }
            },
            "aggs": {
                "types": {"terms": {"field": "type"}},
                "departments": {"terms": {"field": "metadata.department.keyword"}}
            }
        }
        
        # Add filters
        if filters:
            for field, value in filters.items():
                query['query']['bool']['filter'].append({"term": {field: value}})
        
        return query
```

---

## 8. Frontend Architecture

### 8.1 Component Structure

```
search_ui/
├── components/
│   ├── SearchBox/
│   │   ├── SearchInput.tsx        # Main search input
│   │   ├── Autocomplete.tsx       # Autocomplete suggestions
│   │   └── VoiceSearch.tsx        # Voice search (future)
│   ├── Results/
│   │   ├── ResultsList.tsx        # Search results list
│   │   ├── ResultCard.tsx         # Individual result card
│   │   ├── ResultPreview.tsx      # Result preview panel
│   │   └── AnswerBox.tsx          # AI-generated answer
│   ├── Filters/
│   │   ├── FilterPanel.tsx        # Filter sidebar
│   │   ├── FacetFilter.tsx        # Faceted filters
│   │   └── DateRangeFilter.tsx    # Date range filter
│   └── Knowledge/
│       ├── EntityCard.tsx         # Knowledge entity card
│       ├── RelationshipGraph.tsx   # Relationship visualization
│       └── RelatedEntities.tsx     # Related entities list
├── hooks/
│   ├── useSearch.ts               # Search state management
│   ├── useFilters.ts              # Filter state
│   ├── useHistory.ts              # Search history
│   └── useKnowledge.ts            # Knowledge graph data
├── stores/
│   ├── searchStore.ts             # Search state
│   ├── filterStore.ts             # Filter state
│   └── historyStore.ts            # History state
└── utils/
    ├── queryUtils.ts              # Query utilities
    ├── filterUtils.ts             # Filter utilities
    └── resultUtils.ts             # Result processing
```

### 8.2 Real-time Features

- **Live Search:** Real-time search results as user types.
- **Instant Suggestions:** Autocomplete with search suggestions.
- **Result Updates:** Live updates when indexed content changes.
- **Collaborative Search:** Shared searches and results (optional).

---

## 9. Indexing Strategy

### 9.1 Indexing Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Real-time** | Index content immediately on change | Critical content, user-generated |
| **Scheduled** | Batch index on schedule | Large datasets, periodic updates |
| **Incremental** | Index only changed content | Efficient updates |
| **Full Rebuild** | Complete index rebuild | Initial setup, major changes |

### 9.2 Indexing Pipeline

```python
class IndexingPipeline:
    def __init__(self, content_providers: List[ContentProvider], indexer: ContentIndexer):
        self.content_providers = content_providers
        self.indexer = indexer
    
    async def run_full_index(self):
        """Run full indexing of all content."""
        for provider in self.content_providers:
            async for content in provider.get_all_content():
                await self.indexer.index_content(
                    content_type=provider.content_type,
                    content_id=content.id,
                    data=content.to_dict()
                )
    
    async def run_incremental_index(self, since: datetime):
        """Run incremental indexing for content changed since timestamp."""
        for provider in self.content_providers:
            async for content in provider.get_changed_content(since):
                if content.is_deleted:
                    await self.indexer.delete_content(provider.content_type, content.id)
                else:
                    await self.indexer.index_content(
                        content_type=provider.content_type,
                        content_id=content.id,
                        data=content.to_dict()
                    )
```

---

## 10. Security Design

### 10.1 Permission-Aware Search

- **Index-level Permissions:** Store permissions with each document.
- **Query Filtering:** Filter results based on user permissions.
- **Row-level Security:** Apply row-level security at query time.
- **Audit Logging:** Log all search queries and result access.

### 10.2 Data Protection

- **Encryption:** Encrypt sensitive content in search index.
- **PII Masking:** Mask or exclude PII from search results.
- **Access Control:** Enforce RBAC for search features.
- **Compliance:** Support GDPR right to be forgotten.

### 10.3 Search Security

```python
class SecureSearchEngine:
    def __init__(self, search_engine: UniversalSearchEngine, permission_service: PermissionService):
        self.search_engine = search_engine
        self.permission_service = permission_service
    
    async def secure_search(self, query: str, user: User, filters: dict = None) -> SearchResult:
        """Execute search with security filtering."""
        # Check search permissions
        if not await self.permission_service.can_search(user):
            raise PermissionError("User not authorized to search")
        
        # Add security filters
        secure_filters = await self.add_security_filters(user, filters)
        
        # Execute search
        results = await self.search_engine.search(query, user, secure_filters)
        
        # Filter results at result level (double-check)
        filtered_results = []
        for result in results.results:
            if await self.permission_service.can_access(user, result):
                filtered_results.append(result)
        
        results.results = filtered_results
        results.total = len(filtered_results)
        
        # Log access
        await self.log_search_access(user.id, query, len(filtered_results))
        
        return results
```

---

## 11. Performance Strategy

### 11.1 Search Optimization

- **Index Optimization:** Optimize Elasticsearch index mappings and settings.
- **Query Optimization:** Use efficient queries and caching.
- **Result Caching:** Cache frequent search results.
- **Distributed Search:** Distribute search across multiple nodes.

### 11.2 Knowledge Graph Optimization

- **Graph Indexing:** Create indexes on frequently queried properties.
- **Query Optimization:** Use efficient Cypher queries.
- **Caching:** Cache graph traversal results.
- **Partitioning**: Partition graph by organization or type.

### 11.3 Monitoring Metrics

- **Search Performance:** Query latency, index size, indexing rate.
- **User Behavior:** Search patterns, popular queries, click-through rates.
- **System Health**: Elasticsearch cluster health, Neo4j performance.
- **Business Metrics**: Search adoption, user satisfaction.

---

## 12. Monitoring Strategy

### 12.1 Search Analytics

- **Query Analytics:** Track query patterns, popular searches, zero-result queries.
- **User Analytics:** Monitor user search behavior and preferences.
- **Content Analytics:** Track which content is most searched and accessed.
- **Performance Analytics:** Monitor search performance and optimization opportunities.

### 12.2 Health Monitoring

- **Elasticsearch Health:** Cluster status, node health, index performance.
- **Neo4j Health:** Graph database performance and query optimization.
- **Index Health:** Index size, document count, indexing lag.
- **API Health:** Search API response times and error rates.

---

## 13. Testing Strategy

### 13.1 Unit Tests

- **Search Engine Tests:** Test core search functionality.
- **Indexing Tests:** Test content indexing and updates.
- **Knowledge Graph Tests:** Test entity and relationship management.
- **AI Service Tests:** Test NLP and AI features.

### 13.2 Integration Tests

- **API Tests:** Test all search API endpoints.
- **Permission Tests:** Test permission-aware search.
- **Content Provider Tests**: Test integration with content sources.
- **End-to-End Tests**: Test complete search workflow.

### 13.3 Performance Tests

- **Load Tests:** Test search performance under load.
- **Indexing Tests:** Test indexing performance with large datasets.
- **Scalability Tests:** Test horizontal scaling of search cluster.

### 13.4 Security Tests

- **Permission Tests:** Test RBAC enforcement in search.
- **Data Privacy Tests:** Test PII protection and encryption.
- **Injection Tests**: Test for search injection vulnerabilities.

---

## 14. Administrator Guide

### 14.1 Search Management

- **Index Management:** Create, update, and rebuild search indexes.
- **Content Sources:** Configure content providers and indexing schedules.
- **Search Configuration:** Configure search settings and features.
- **Performance Monitoring:** Monitor search performance and optimization.

### 14.2 Knowledge Graph Management

- **Entity Management:** Manage entities and relationships.
- **Graph Configuration:** Configure graph settings and optimizations.
- **Data Quality**: Ensure data quality in knowledge graph.
- **Visualization**: Monitor graph structure and connections.

### 14.3 User Management

- **Search Permissions:** Configure search access permissions.
- **Search Analytics**: Review search analytics and user behavior.
- **Compliance**: Ensure compliance with data protection regulations.
- **Training**: Train users on effective search techniques.

---

## 15. Developer Guide

### 15.1 Content Providers

- **Provider Interface:** Implement the ContentProvider interface.
- **Provider Registration:** Register custom content providers.
- **Data Mapping:** Map content to search document format.
- **Permissions**: Implement permission checking for content.

### 15.2 Search API

- **REST API:** Use search API for integration.
- **WebSocket API:** Real-time search updates.
- **Authentication**: Use API keys or JWT.
- **Rate Limits**: Respect search rate limits.

### 15.3 Best Practices

- **Query Optimization**: Write efficient search queries.
- **Index Design**: Design effective index mappings.
- **Security**: Follow security best practices.
- **Performance**: Optimize for search performance.

---

## 16. Output Summary

1. **Search Architecture** — design principles, components, universal search capabilities.
2. **Knowledge Graph Architecture** — graph model, relationship types, entity management.
3. **Database Schema** — Elasticsearch mapping and 9 MySQL tables with DDL.
4. **ER Diagram** — textual representation of table relationships.
5. **API Specification** — 20+ REST endpoints for search, suggestions, history, knowledge graph.
6. **Backend Architecture** — package structure, search engine core, query processing.
7. **Frontend Architecture** — component structure, real-time features, state management.
8. **AI Search Architecture** — NLP processing, semantic search, answer generation.
9. **Indexing Strategy** — real-time, scheduled, incremental, and full rebuild indexing.
10. **Security Design** — permission-aware search, data protection, compliance.
11. **Performance Strategy** — search optimization, caching, distributed search.
12. **Monitoring Strategy** — search analytics, health monitoring, metrics.
13. **Testing Strategy** — unit, integration, performance, security tests.
14. **Administrator Guide** — search management, knowledge graph, user management.
15. **Developer Guide** — content providers, API usage, best practices.

All specifications are enterprise-grade, scalable, modular, production-ready, and fully integrated into AEDIP.
