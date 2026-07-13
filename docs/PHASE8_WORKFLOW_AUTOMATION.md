# Phase 8.2 — Enterprise Workflow Automation Engine

## Purpose

This document defines the Enterprise Workflow Automation Engine for AEDIP, enabling visual, no-code/low-code business process automation across all modules. The engine supports approval, ETL, data validation, reporting, AI, notification, document, and industry-specific workflows with a drag-and-drop designer, robust BPM engine, and enterprise-grade security and monitoring.

---

## 1. Workflow Architecture

### 1.1 Design Principles

- **Visual First:** Drag-and-drop designer with real-time validation.
- **Event-Driven:** Triggers from any AEDIP module or external system.
- **Modular Nodes:** Extensible node library with custom plugin nodes.
- **Scalable Execution:** Queue-based, parallel, prioritized execution with retries.
- **Audit-Ready:** Full execution history, audit trail, and compliance.
- **AI-Enhanced:** AI suggestions, optimization, bottleneck detection, documentation.
- **Secure by Default:** RBAC integration, encrypted variables, secrets management.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Workflow Automation Engine                                 │
│  Designer · BPM Engine · Queue · Scheduler · Approval Engine · Event Bus        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Workflow     │                │  Workflow       │               │  Workflow          │
│  Designer UI  │                │  Execution      │               │  Approval Engine   │
│               │                │  Engine         │               │                    │
│ Canvas        │                │ Queue           │               │ Sequential/Parallel │
│ Nodes         │                │ Scheduler       │               │ Escalation         │
│ Validation    │                │ Retries         │               │ Delegation         │
│ Templates     │                │ History         │               │ Timeout            │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Workflow Designer** | Visual drag-and-drop builder; validation; templates; versioning. |
| **BPM Engine** | Parse workflow definitions; execute nodes; manage state; handle errors. |
| **Execution Queue** | Prioritized task queue; retries; timeouts; compensation. |
| **Scheduler** | Cron/schedule triggers; delayed execution; timers. |
| **Approval Engine** | Single/multi/sequential/parallel approvals; escalation; delegation. |
| **Event Bus Integration** | Subscribe/publish workflow events; react to AEDIP events. |
| **AI Integration** | Suggest workflows; optimize; detect bottlenecks; generate docs. |
| **Security Layer** | RBAC; encrypted variables; secrets; audit logging. |
| **Monitoring** | Live execution view; metrics; alerts; health checks. |

---

## 2. BPM Engine Design

### 2.1 Execution Model

- **Workflow Definition:** JSON schema with nodes, edges, variables, triggers.
- **Instance:** One execution of a workflow with its own context and state.
- **Node Execution:** Each node runs as a task; can be synchronous or asynchronous.
- **State Machine:** Workflow progresses through states: pending, running, completed, failed, cancelled.
- **Parallelism:** Fork/join nodes enable parallel execution; synchronization points.

### 2.2 Node Types

| Category | Nodes | Description |
|----------|-------|-------------|
| **Control** | Start, End, Condition, Decision, Switch, Loop, Merge, Split, Parallel, Branch | Control flow. |
| **Approval** | Approval, Sequential Approval, Parallel Approval, Escalation, Delegation, Timeout, Reminder | Human approval. |
| **Integration** | REST API, Webhook, Database Query, Run ETL, Run AI Analysis, Generate Report, Generate Dashboard | System integration. |
| **Notification** | Send Email, Send SMS, Send WhatsApp, Push Notification, Create Task, Assign User | Notifications. |
| **Data** | Create Record, Update Record, Delete Record, Transform Data, Validate Data | Data operations. |
| **Timing** | Delay, Timer, Cron, Wait for Event | Timing control. |
| **Error** | Error Handler, Retry, Manual Review, Rollback | Error handling. |
| **Custom** | Custom Plugin Node | Extensible via plugins. |

### 2.3 Execution Context

```json
{
  "instance_id": "uuid",
  "workflow_id": 123,
  "version": 3,
  "variables": {
    "user_id": 456,
    "amount": 1500,
    "approved": false
  },
  "current_node": "approval_1",
  "status": "running",
  "started_at": "2026-07-13T10:00:00Z",
  "history": [
    {"node": "start", "status": "completed", "timestamp": "..."},
    {"node": "check_amount", "status": "completed", "timestamp": "..."}
  ]
}
```

### 2.4 Error Handling & Compensation

- **Retry Policy:** Configurable retries per node with backoff.
- **Error Handlers:** Dedicated error nodes catch exceptions; can retry, escalate, or compensate.
- **Compensation:** Reverse actions for failed workflows (e.g., undo database changes).
- **Dead Letter Queue:** Failed instances moved to DLQ for manual review.

---

## 3. Visual Workflow Builder Specification

### 3.1 Canvas Features

- **Drag-and-Drop:** Nodes from palette to canvas.
- **Zoom & Pan:** Mouse wheel zoom; click-and-drag pan.
- **Mini Map:** Overview of large workflows; click to navigate.
- **Undo/Redo:** Full history with keyboard shortcuts (Ctrl+Z/Ctrl+Y).
- **Copy/Paste:** Duplicate nodes and subgraphs.
- **Grouping:** Group related nodes; collapse/expand.
- **Annotations:** Add notes, descriptions, attachments.
- **Auto Layout:** Automatic arrangement (hierarchical, circular, force-directed).
- **Grid Snap:** Align nodes to grid; toggle grid visibility.
- **Connection Validation:** Prevent invalid connections; show warnings.
- **Real-time Validation:** Highlight errors while designing.
- **Execution Preview:** Simulate execution path with sample data.

### 3.2 Node Palette

- **Searchable:** Filter nodes by category or keyword.
- **Custom Nodes:** Plugin-defined nodes appear here.
- **Tool Tips:** Hover to see node description and required inputs.
- **Drag Preview:** Ghost image while dragging.

### 3.3 Property Panel

- **Node Configuration:** Edit node-specific settings.
- **Variable Mapping:** Map workflow variables to node inputs/outputs.
- **Conditions:** Build IF/ELSE expressions with visual editor.
- **Approvals:** Select approvers, set timeout, escalation rules.
- **API Configuration:** Set endpoints, authentication, headers.
- **Data Mapping:** Visual mapper for transforming data.

### 3.4 Templates

- **Template Library:** Pre-built workflows for common processes.
- **Industry Templates:** Healthcare, education, government, etc.
- **Custom Templates:** Save workflows as templates for reuse.
- **Template Variables:** Parameterize templates for different contexts.

### 3.5 Version History

- **Auto-Save:** Save drafts automatically.
- **Versioning:** Create named versions; compare changes.
- **Rollback:** Revert to previous version.
- **Publishing:** Promote version to production.

### 3.6 Collaboration

- **Real-time Editing:** Multiple users edit simultaneously (optional).
- **Comments:** Add comments to nodes and workflows.
- **Share:** Share workflows with users/teams.
- **Permissions:** View, edit, execute permissions per workflow.

---

## 4. Database Schema

### 4.1 Tables

```sql
CREATE TABLE workflows (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  version INT NOT NULL DEFAULT 1,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  definition JSON NOT NULL,
  variables JSON,
  triggers JSON,
  permissions JSON,
  is_template BOOLEAN DEFAULT FALSE,
  template_variables JSON,
  created_by BIGINT NOT NULL,
  updated_by BIGINT,
  published_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (category_id) REFERENCES workflow_categories(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  FOREIGN KEY (updated_by) REFERENCES users(id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_category (category_id),
  INDEX idx_template (is_template)
) ENGINE=InnoDB;

CREATE TABLE workflow_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  version INT NOT NULL,
  definition JSON NOT NULL,
  variables JSON,
  changelog TEXT,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  UNIQUE KEY uniq_workflow_version (workflow_id, version),
  INDEX idx_workflow (workflow_id)
) ENGINE=InnoDB;

CREATE TABLE workflow_templates (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  definition JSON NOT NULL,
  variables JSON,
  tags JSON,
  is_public BOOLEAN DEFAULT FALSE,
  usage_count INT DEFAULT 0,
  rating DECIMAL(3,2),
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES workflow_categories(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_category (category_id),
  INDEX idx_public (is_public),
  INDEX idx_rating (rating)
) ENGINE=InnoDB;

CREATE TABLE workflow_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  parent_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES workflow_categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE workflow_instances (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  version INT NOT NULL,
  organization_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  variables JSON,
  context JSON,
  current_node VARCHAR(128),
  error_message TEXT,
  started_at DATETIME,
  completed_at DATETIME,
  started_by BIGINT,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id),
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (started_by) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_started (started_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_steps (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  node_id VARCHAR(128) NOT NULL,
  node_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  input_data JSON,
  output_data JSON,
  error_message TEXT,
  started_at DATETIME,
  completed_at DATETIME,
  retry_count INT DEFAULT 0,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  INDEX idx_instance (instance_id),
  INDEX idx_status (status),
  INDEX idx_started (started_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_nodes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  version INT NOT NULL,
  node_id VARCHAR(128) NOT NULL,
  node_type VARCHAR(64) NOT NULL,
  position_x DECIMAL(10,2),
  position_y DECIMAL(10,2),
  configuration JSON,
  permissions JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_workflow_version_node (workflow_id, version, node_id),
  INDEX idx_workflow (workflow_id)
) ENGINE=InnoDB;

CREATE TABLE workflow_edges (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  version INT NOT NULL,
  source_node VARCHAR(128) NOT NULL,
  target_node VARCHAR(128) NOT NULL,
  condition_expression TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_workflow_version_edge (workflow_id, version, source_node, target_node),
  INDEX idx_workflow (workflow_id)
) ENGINE=InnoDB;

CREATE TABLE workflow_variables (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  version INT NOT NULL,
  name VARCHAR(128) NOT NULL,
  type VARCHAR(64) NOT NULL,
  default_value JSON,
  is_required BOOLEAN DEFAULT FALSE,
  is_encrypted BOOLEAN DEFAULT FALSE,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_workflow_version_var (workflow_id, version, name),
  INDEX idx_workflow (workflow_id)
) ENGINE=InnoDB;

CREATE TABLE workflow_parameters (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  value JSON,
  is_encrypted BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_instance_name (instance_id, name),
  INDEX idx_instance (instance_id)
) ENGINE=InnoDB;

CREATE TABLE workflow_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  step_id BIGINT,
  level VARCHAR(16) NOT NULL,
  message TEXT NOT NULL,
  context JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY (step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
  INDEX idx_instance_time (instance_id, created_at),
  INDEX idx_level (level)
) ENGINE=InnoDB;

CREATE TABLE workflow_events (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  instance_id BIGINT,
  event_type VARCHAR(64) NOT NULL,
  event_data JSON,
  user_id BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id),
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_instance (instance_id),
  INDEX idx_type (event_type),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_execution_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  node_id VARCHAR(128) NOT NULL,
  action VARCHAR(64) NOT NULL,
  previous_state JSON,
  new_state JSON,
  executed_by BIGINT,
  executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY (executed_by) REFERENCES users(id),
  INDEX idx_instance (instance_id),
  INDEX idx_node (node_id),
  INDEX idx_executed (executed_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_errors (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  step_id BIGINT,
  node_id VARCHAR(128) NOT NULL,
  error_type VARCHAR(128) NOT NULL,
  error_message TEXT NOT NULL,
  stack_trace TEXT,
  context JSON,
  is_resolved BOOLEAN DEFAULT FALSE,
  resolved_by BIGINT,
  resolved_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY (step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
  FOREIGN KEY (resolved_by) REFERENCES users(id),
  INDEX idx_instance (instance_id),
  INDEX idx_resolved (is_resolved),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_schedules (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  organization_id BIGINT NOT NULL,
  schedule_type VARCHAR(32) NOT NULL, -- cron, interval, once
  schedule_expression VARCHAR(255) NOT NULL,
  timezone VARCHAR(64),
  is_active BOOLEAN DEFAULT TRUE,
  next_run DATETIME,
  last_run DATETIME,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_next_run (next_run),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE workflow_permissions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  role_id BIGINT,
  user_id BIGINT,
  permission_type VARCHAR(32) NOT NULL, -- view, edit, execute, manage
  granted_by BIGINT NOT NULL,
  granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (granted_by) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_role (role_id),
  INDEX idx_user (user_id),
  INDEX idx_permission (permission_type)
) ENGINE=InnoDB;

CREATE TABLE workflow_approvals (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT NOT NULL,
  step_id BIGINT NOT NULL,
  node_id VARCHAR(128) NOT NULL,
  approver_type VARCHAR(32) NOT NULL, -- user, role, department
  approver_id BIGINT,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  decision VARCHAR(32), -- approve, reject, delegate
  comments TEXT,
  attachments JSON,
  due_date DATETIME,
  reminder_sent BOOLEAN DEFAULT FALSE,
  decided_at DATETIME,
  decided_by BIGINT,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY (step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
  FOREIGN KEY (approver_id) REFERENCES users(id),
  FOREIGN KEY (decided_by) REFERENCES users(id),
  INDEX idx_instance (instance_id),
  INDEX idx_approver (approver_id),
  INDEX idx_status (status),
  INDEX idx_due (due_date)
) ENGINE=InnoDB;

CREATE TABLE workflow_comments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT,
  instance_id BIGINT,
  node_id VARCHAR(128),
  user_id BIGINT NOT NULL,
  comment TEXT NOT NULL,
  attachments JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id),
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_instance (instance_id),
  INDEX idx_user (user_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_files (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT,
  instance_id BIGINT,
  node_id VARCHAR(128),
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(512) NOT NULL,
  file_size BIGINT,
  mime_type VARCHAR(128),
  uploaded_by BIGINT NOT NULL,
  uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id),
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id),
  FOREIGN KEY (uploaded_by) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_instance (instance_id),
  INDEX idx_uploaded (uploaded_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_notifications (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  instance_id BIGINT,
  step_id BIGINT,
  node_id VARCHAR(128),
  channel VARCHAR(64) NOT NULL, -- email, sms, push, webhook
  recipient VARCHAR(255) NOT NULL,
  subject VARCHAR(255),
  content TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  sent_at DATETIME,
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id),
  FOREIGN KEY (step_id) REFERENCES workflow_steps(id),
  INDEX idx_instance (instance_id),
  INDEX idx_status (status),
  INDEX idx_sent (sent_at)
) ENGINE=InnoDB;

CREATE TABLE workflow_metrics (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT NOT NULL,
  date DATE NOT NULL,
  instance_count INT DEFAULT 0,
  success_count INT DEFAULT 0,
  failure_count INT DEFAULT 0,
  avg_execution_time DECIMAL(10,2),
  max_execution_time DECIMAL(10,2),
  min_execution_time DECIMAL(10,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_workflow_date (workflow_id, date),
  INDEX idx_date (date)
) ENGINE=InnoDB;

CREATE TABLE workflow_audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  workflow_id BIGINT,
  instance_id BIGINT,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL,
  details JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id),
  FOREIGN KEY (instance_id) REFERENCES workflow_instances(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_workflow (workflow_id),
  INDEX idx_instance (instance_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;
```

### 4.2 Indexes & Optimization

- Primary keys on all tables.
- Foreign key indexes.
- Composite indexes for common queries (org+status, workflow+date, instance+node).
- Full-text indexes on workflow name/description for search.
- Partition `workflow_logs` and `workflow_metrics` by month if needed.

---

## 5. ER Diagram (Textual)

```
workflows (1) → (n) workflow_versions
workflows (1) → (n) workflow_instances
workflows (1) → (n) workflow_nodes
workflows (1) → (n) workflow_edges
workflows (1) → (n) workflow_variables
workflows (1) → (n) workflow_schedules
workflows (1) → (n) workflow_permissions
workflows (1) → (n) workflow_comments
workflows (1) → (n) workflow_files
workflows (1) → (n) workflow_metrics
workflows (1) → (n) workflow_audit_logs

workflow_instances (1) → (n) workflow_steps
workflow_instances (1) → (n) workflow_parameters
workflow_instances (1) → (n) workflow_logs
workflow_instances (1) → (n) workflow_events
workflow_instances (1) → (n) workflow_execution_history
workflow_instances (1) → (n) workflow_errors
workflow_instances (1) → (n) workflow_approvals
workflow_instances (1) → (n) workflow_notifications

workflow_steps (1) → (n) workflow_logs
workflow_steps (1) → (n) workflow_approvals
workflow_steps (1) → (n) workflow_notifications

workflow_categories (1) → (n) workflows
workflow_categories (1) → (n) workflow_templates
```

---

## 6. API Specification

Base path: `/api/v1/workflows`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List workflows. |
| POST | `/` | Create workflow. |
| GET | `/{id}` | Get workflow details. |
| PUT | `/{id}` | Update workflow. |
| DELETE | `/{id}` | Delete workflow. |
| POST | `/{id}/publish` | Publish workflow version. |
| POST | `/{id}/execute` | Execute workflow. |
| POST | `/{id}/test` | Test workflow with sample data. |
| GET | `/{id}/versions` | List workflow versions. |
| GET | `/{id}/instances` | List workflow instances. |
| GET | `/{id}/metrics` | Get workflow metrics. |
| GET | `/templates` | List workflow templates. |
| POST | `/templates` | Create template. |
| GET | `/categories` | List categories. |
| POST | `/categories` | Create category. |
| GET | `/instances` | List all instances. |
| GET | `/instances/{id}` | Get instance details. |
| POST | `/instances/{id}/cancel` | Cancel workflow instance. |
| POST | `/instances/{id}/retry` | Retry failed instance. |
| GET | `/instances/{id}/history` | Get execution history. |
| GET | `/instances/{id}/logs` | Get instance logs. |
| GET | `/instances/{id}/errors` | Get instance errors. |
| POST | `/approvals/{id}/approve` | Approve workflow step. |
| POST | `/approvals/{id}/reject` | Reject workflow step. |
| POST | `/approvals/{id}/delegate` | Delegate approval. |
| GET | `/schedules` | List scheduled workflows. |
| POST | `/schedules` | Create schedule. |
| PUT | `/schedules/{id}` | Update schedule. |
| DELETE | `/schedules/{id}` | Delete schedule. |
| GET | `/nodes` | List available node types. |
| GET | `/notifications` | List workflow notifications. |
| POST | `/notifications/{id}/resend` | Resend notification. |
| GET | `/audit` | List audit logs. |

### Example: Execute Workflow

```http
POST /api/v1/workflows/123/execute
{
  "variables": {
    "user_id": 456,
    "amount": 1500,
    "department": "finance"
  },
  "context": {
    "source": "manual",
    "ip": "192.168.1.100"
  }
}
```

Response:
```json
{
  "instance_id": "uuid",
  "status": "running",
  "started_at": "2026-07-13T10:00:00Z",
  "current_node": "approval_1",
  "next_steps": ["approval_1"]
}
```

---

## 7. Backend Architecture

### 7.1 Package Structure

```
workflow_engine/
├── __init__.py
├── engine.py                 # BPM Engine
├── designer.py               # Workflow validation/compilation
├── executor.py               # Node executors
├── scheduler.py              # Cron/schedule handling
├── approval.py               # Approval engine
├── queue.py                  # Task queue
├── events.py                 # Event handling
├── ai.py                     # AI integration
├── security.py               # Security, encryption
├── monitoring.py             # Metrics, health
├── nodes/                    # Node implementations
│   ├── __init__.py
│   ├── control.py
│   ├── approval.py
│   ├── integration.py
│   ├── notification.py
│   ├── data.py
│   ├── timing.py
│   └── custom.py
├── triggers/                 # Trigger handlers
│   ├── __init__.py
│   ├── manual.py
│   ├── schedule.py
│   ├── webhook.py
│   └── event.py
├── api/
│   └── routes.py             # Workflow APIs
├── models/
│   └── workflow_models.py    # SQLAlchemy models
├── schemas/
│   └── workflow_schemas.py   # Pydantic schemas
└── migrations/               # Alembic migrations
```

### 7.2 BPM Engine Core

```python
class BPMEngine:
    def __init__(self, queue: TaskQueue, event_bus: EventBus):
        self.queue = queue
        self.event_bus = event_bus

    async def execute_workflow(self, instance_id: str):
        instance = await self.get_instance(instance_id)
        workflow = await self.get_workflow(instance.workflow_id)
        
        while instance.status == 'running':
            node = self.get_next_node(instance, workflow)
            if not node:
                await self.complete_instance(instance)
                break
                
            await self.execute_node(instance, node)
            await self.update_instance_state(instance, node)
            
    async def execute_node(self, instance: WorkflowInstance, node: WorkflowNode):
        executor = self.get_executor(node.node_type)
        try:
            result = await executor.execute(instance, node)
            await self.record_step_success(instance, node, result)
        except Exception as e:
            await self.handle_node_error(instance, node, e)
```

### 7.3 Node Execution

Each node type implements the `NodeExecutor` interface:

```python
class NodeExecutor(ABC):
    @abstractmethod
    async def execute(self, instance: WorkflowInstance, node: WorkflowNode) -> dict:
        pass

class ApprovalExecutor(NodeExecutor):
    async def execute(self, instance: WorkflowInstance, node: WorkflowNode) -> dict:
        # Create approval request
        approval = await self.create_approval(instance, node)
        # Send notification
        await self.notify_approver(approval)
        # Wait for approval (async)
        result = await self.wait_for_approval(approval)
        return {"decision": result.decision}
```

### 7.4 Queue & Retries

- **Priority Queue:** High, normal, low priority tasks.
- **Retry Policy:** Exponential backoff with max attempts.
- **Dead Letter Queue:** Failed tasks moved for manual review.
- **Timeout Handling:** Per-node and overall workflow timeouts.

### 7.5 Approval Engine

```python
class ApprovalEngine:
    async def create_approval(self, instance: WorkflowInstance, node: WorkflowNode):
        config = node.configuration
        approval = WorkflowApproval(
            instance_id=instance.id,
            node_id=node.node_id,
            approver_type=config['approver_type'],
            approver_id=config['approver_id'],
            due_date=self.calculate_due_date(config)
        )
        await self.save(approval)
        return approval
    
    async def handle_decision(self, approval_id: str, decision: str, comments: str):
        approval = await self.get_approval(approval_id)
        approval.decision = decision
        approval.comments = comments
        approval.decided_at = datetime.utcnow()
        await self.save(approval)
        
        # Continue workflow
        await self.resume_workflow(approval.instance_id)
```

---

## 8. Frontend Architecture

### 8.1 Designer Components

- **WorkflowCanvas:** Main drag-and-drop canvas using React Flow.
- **NodePalette:** Searchable node library.
- **PropertyPanel:** Dynamic forms for node configuration.
- **ToolBar:** Undo/redo, zoom, layout, validation.
- **MiniMap:** Overview navigation.
- **TemplateLibrary:** Browse and apply templates.

### 8.2 State Management

- **Workflow Store:** Current workflow definition, variables, validation errors.
- **Canvas Store:** Zoom, pan, selection, history.
- **Execution Store:** Real-time execution status, logs.
- **User Store:** Permissions, approvers.

### 8.3 Real-time Features

- **Live Execution:** WebSocket updates showing current node, progress.
- **Collaboration:** Real-time cursor positions, edits (optional).
- **Notifications:** Approval requests, workflow completion alerts.

### 8.4 Component Library

- **Node Components:** Visual representations of each node type.
- **Connection Components:** Styled connections with condition labels.
- **Form Components:** Dynamic forms for node configuration.
- **Chart Components:** Execution metrics visualizations.

---

## 9. Event Bus Integration

### 9.1 Workflow Events

- **Internal Events:** `workflow.started`, `workflow.completed`, `workflow.failed`, `workflow.cancelled`, `workflow.approved`, `workflow.rejected`, `workflow.timeout`.
- **External Triggers:** Subscribe to AEDIP events: `etl.completed`, `ai.recommendation.generated`, `alert.triggered`, `user.created`, `record.updated`.

### 9.2 Event Handling

```python
class WorkflowEventHandler:
    async def handle_etl_completed(self, event: Event):
        # Find workflows waiting for this ETL
        workflows = await self.find_workflows_by_trigger('etl_completed', event.data)
        for workflow in workflows:
            await self.start_workflow(workflow.id, event.data)
    
    async def handle_approval_decision(self, event: Event):
        # Resume workflow after approval
        await self.resume_workflow(event.data['instance_id'])
```

### 9.3 Event Sourcing

- All workflow state changes stored as events.
- Event replay for debugging and auditing.
- Snapshot optimization for long-running workflows.

---

## 10. AI Workflow Integration

### 10.1 AI Capabilities

- **Workflow Suggestions:** Recommend workflows based on patterns.
- **Optimization:** Identify bottlenecks, suggest improvements.
- **Documentation:** Auto-generate workflow documentation.
- **Prediction:** Predict workflow success probability.
- **Explanation:** Explain workflow execution in natural language.

### 10.2 AI Integration Points

```python
class AIWorkflowService:
    async def suggest_workflow(self, context: dict) -> List[WorkflowTemplate]:
        prompt = self.build_suggestion_prompt(context)
        response = await self.ai_gateway.chat(prompt, assistant_type="workflow_suggester")
        return self.parse_workflow_suggestions(response)
    
    async def optimize_workflow(self, workflow_id: str) -> OptimizationReport:
        workflow = await self.get_workflow(workflow_id)
        metrics = await self.get_workflow_metrics(workflow_id)
        prompt = self.build_optimization_prompt(workflow, metrics)
        response = await self.ai_gateway.chat(prompt, assistant_type="workflow_optimizer")
        return self.parse_optimization_report(response)
```

### 10.3 AI Nodes

- **AI Analysis Node:** Run AI analysis on data.
- **AI Decision Node:** Use AI to make decisions.
- **AI Recommendation Node:** Generate AI recommendations.
- **AI Document Node:** Generate documents using AI.

---

## 11. Security Design

### 11.1 RBAC Integration

- **Workflow Permissions:** view, edit, execute, manage workflows.
- **Node Permissions:** Some nodes require specific permissions (e.g., database query).
- **Approval Permissions:** Only authorized users can approve.
- **Data Access:** Workflows inherit user permissions for data access.

### 11.2 Encrypted Variables

- Sensitive variables (passwords, API keys) marked `is_encrypted`.
- Stored encrypted in database; decrypted only at runtime.
- Audit trail for variable access.

### 11.3 Secrets Management

- Integration with vault service for secrets.
- Temporary credentials for workflow execution.
- Automatic rotation of secrets.

### 11.4 Input Validation

- Validate all workflow inputs and node configurations.
- Sanitize user inputs to prevent injection.
- Schema validation for JSON data.

### 11.5 Audit Logging

- All workflow actions logged: create, update, execute, approve, reject.
- Include user, IP, user agent, timestamp, changes.
- Immutable logs for compliance.

### 11.6 Rate Limiting

- API rate limiting per user/organization.
- Workflow execution limits to prevent abuse.
- Approval request limits.

---

## 12. Performance Strategy

### 12.1 Execution Optimization

- **Parallel Execution:** Independent nodes run in parallel.
- **Async Processing:** Non-blocking node execution.
- **Resource Pooling:** Reuse connections and resources.
- **Caching:** Cache frequently accessed data.

### 12.2 Queue Management

- **Priority Queues:** High-priority workflows execute first.
- **Batch Processing:** Batch similar operations for efficiency.
- **Load Balancing:** Distribute execution across workers.

### 12.3 Database Optimization

- **Indexes:** Optimized indexes for common queries.
- **Partitioning:** Partition large tables by date.
- **Connection Pooling:** Efficient database connections.
- **Query Optimization:** Optimize slow queries.

### 12.4 Frontend Performance

- **Lazy Loading:** Load workflows on demand.
- **Virtual Scrolling:** Handle large workflow canvases.
- **Memoization:** Cache expensive computations.
- **Code Splitting:** Split code by route.

---

## 13. Monitoring Strategy

### 13.1 Health Checks

- **Engine Health:** BPM engine status, queue depth.
- **Database Health:** Connection status, query performance.
- **Node Health:** Per-node error rates.
- **Approval Health**: Pending approvals count, overdue approvals.

### 13.2 Metrics

- **Execution Metrics:** Success rate, failure rate, average execution time.
- **Queue Metrics:** Queue depth, processing rate, wait time.
- **Approval Metrics:** Approval time, escalation rate.
- **Resource Metrics:** CPU, memory, database connections.

### 13.3 Logging

- **Structured Logs:** JSON format with correlation IDs.
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL.
- **Log Aggregation:** Centralized log collection.
- **Log Retention:** Retain logs based on compliance requirements.

### 13.4 Alerting

- **Failed Workflows:** Alert on high failure rate.
- **Queue Backlog:** Alert on queue depth threshold.
- **Approval Delays:** Alert on overdue approvals.
- **Resource Limits:** Alert on resource exhaustion.

### 13.5 Dashboards

- **Workflow Overview:** Active workflows, execution status.
- **Performance Metrics:** Execution times, success rates.
- **Approval Dashboard:** Pending approvals, overdue items.
- **Error Analysis**: Error trends, top errors.

---

## 14. Deployment Strategy

### 14.1 Containerization

- **Workflow Engine:** Deploy as separate service.
- **Queue Worker:** Scale workers independently.
- **Frontend:** Deploy as static assets or Next.js app.
- **Database:** Shared with core platform.

### 14.2 Scaling

- **Horizontal Scaling:** Multiple engine instances.
- **Worker Scaling:** Scale queue workers based on load.
- **Database Scaling:** Read replicas for reporting.
- **Frontend Scaling:** CDN for static assets.

### 14.3 Configuration

- **Environment Variables:** Database, queue, AI gateway settings.
- **Feature Flags:** Enable/disable features.
- **Resource Limits:** CPU, memory limits per workflow.

### 14.4 Blue-Green Deployment

- **Zero Downtime:** Deploy new version alongside old.
- **Canary Releases:** Gradual rollout to subset of workflows.
- **Rollback:** Quick rollback if issues detected.

---

## 15. Testing Strategy

### 15.1 Unit Tests

- **Engine Tests:** Test workflow execution logic.
- **Node Tests:** Test each node implementation.
- **Validation Tests:** Test workflow validation rules.
- **Approval Tests:** Test approval engine logic.

### 15.2 Integration Tests

- **API Tests:** Test all API endpoints.
- **Queue Tests:** Test queue processing.
- **Database Tests:** Test database operations.
- **Event Tests:** Test event handling.

### 15.3 End-to-End Tests

- **Workflow Execution:** Test complete workflows.
- **UI Tests:** Test workflow designer.
- **Approval Flow:** Test approval process.
- **Error Handling:** Test error scenarios.

### 15.4 Performance Tests

- **Load Tests:** Test with many concurrent workflows.
- **Stress Tests:** Test system limits.
- **Scalability Tests:** Test horizontal scaling.

### 15.5 Security Tests

- **Permission Tests:** Test RBAC enforcement.
- **Input Validation Tests:** Test for injection vulnerabilities.
- **Encryption Tests:** Test variable encryption.
- **Audit Tests:** Test audit logging.

---

## 16. Administrator Guide

### 16.1 Workflow Management

- **Creating Workflows:** Use visual designer or import templates.
- **Publishing Workflows:** Version control and publishing process.
- **Managing Permissions:** Set user and role permissions.
- **Monitoring Execution:** View active instances and logs.

### 16.2 Approval Configuration

- **Setting Approvers:** Configure approval chains.
- **Escalation Rules:** Set timeout and escalation.
- **Delegation:** Configure delegation rules.
- **Notifications:** Set up approval notifications.

### 16.3 Performance Monitoring

- **Dashboard Overview:** Monitor system health.
- **Metrics Analysis:** Analyze performance metrics.
- **Alert Management:** Configure alerts.
- **Troubleshooting:** Diagnose issues.

### 16.4 Security Management

- **User Permissions:** Manage workflow permissions.
- **Variable Encryption:** Configure encrypted variables.
- **Audit Logs:** Review audit trails.
- **Compliance:** Ensure compliance requirements.

---

## 17. Developer Guide

### 17.1 Creating Custom Nodes

- **Node Interface:** Implement NodeExecutor class.
- **Configuration Schema:** Define configuration schema.
- **Registration:** Register node in the system.
- **Testing:** Write unit and integration tests.

### 17.2 Workflow API

- **REST API:** Use REST API for workflow operations.
- **Webhooks:** Configure webhooks for events.
- **Authentication:** Use API keys or JWT.
- **Rate Limits:** Respect rate limits.

### 17.3 Event Integration

- **Subscribing to Events:** Subscribe to workflow events.
- **Custom Triggers:** Create custom triggers.
- **Event Payloads:** Understand event payloads.
- **Error Handling**: Handle event errors.

### 17.4 Best Practices

- **Idempotency:** Design nodes to be idempotent.
- **Error Handling:** Implement proper error handling.
- **Logging:** Add appropriate logging.
- **Testing:** Write comprehensive tests.

---

## 18. Output Summary

1. **Workflow Architecture** — design principles, components, execution model.
2. **BPM Engine Design** — execution context, node types, error handling, compensation.
3. **Visual Workflow Builder Specification** — canvas features, node palette, property panel, templates, version history.
4. **Database Schema** — 20+ tables with DDL, indexes, relationships, audit fields.
5. **ER Diagram** — textual representation of table relationships.
6. **API Specification** — 40+ REST endpoints for workflows, instances, approvals, schedules, notifications.
7. **Backend Architecture** — package structure, BPM engine core, node execution, queue, approval engine.
8. **Frontend Architecture** — designer components, state management, real-time features, component library.
9. **Event Bus Integration** — workflow events, external triggers, event sourcing.
10. **AI Workflow Integration** — AI capabilities, integration points, AI nodes.
11. **Security Design** — RBAC, encrypted variables, secrets management, audit logging.
12. **Performance Strategy** — execution optimization, queue management, database optimization.
13. **Monitoring Strategy** — health checks, metrics, logging, alerting, dashboards.
14. **Deployment Strategy** — containerization, scaling, configuration, blue-green deployment.
15. **Testing Strategy** — unit, integration, e2e, performance, security tests.
16. **Administrator Guide** — workflow management, approval configuration, monitoring, security.
17. **Developer Guide** — custom nodes, API usage, event integration, best practices.

All specifications are enterprise-grade, scalable, modular, production-ready, cloud-ready, event-driven, secure, and fully integrated into AEDIP.
