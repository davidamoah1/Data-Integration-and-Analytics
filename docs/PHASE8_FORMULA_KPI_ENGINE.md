# Phase 8.4 — Enterprise Formula Builder & KPI Engine

## Purpose

This document defines the Enterprise Formula Builder and KPI Engine for AEDIP, enabling organizations to define, manage, version, validate, and calculate KPIs and formulas without writing code. The system supports visual formula building, real-time execution, AI-powered suggestions, and comprehensive governance.

---

## 1. Formula Engine Architecture

### 1.1 Design Principles

- **No-Code Formula Building:** Visual drag-and-drop interface with expression editor.
- **Expressive Language:** Support for mathematical, logical, statistical, financial, and date/time functions.
- **Real-time Execution:** Calculate formulas on-demand, scheduled, or event-driven.
- **Validation First:** Detect circular references, missing variables, and performance issues.
- **Version Control:** Full versioning with approval workflow and rollback.
- **AI-Enhanced:** Generate formulas, optimize performance, detect errors, explain logic.
- **Enterprise Governance:** RBAC, audit trails, approval workflows, benchmarking.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   Formula Builder & KPI Engine                                 │
│  Formula Builder · Expression Parser · Execution Engine · KPI Calculator        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Formula      │                │  KPI Engine     │               │  Validation        │
│  Builder UI   │                │                 │               │  Engine            │
│               │                │                 │               │                    │
│ Drag & Drop   │                │ KPI Definitions │               │ Syntax Check        │
│ Expression    │                │ Targets         │               │ Circular Ref       │
│ Functions     │                │ Thresholds      │               │ Dependency         │
│ Variables     │                │ History         │               │ Performance        │
│ Testing       │                │ Benchmarks      │               │ Sandbox            │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Formula Builder UI** | Visual drag-and-drop builder; expression editor; function palette; variable explorer; test sandbox. |
| **Expression Parser** | Parse formulas into AST; validate syntax; resolve variables; optimize execution plan. |
| **Execution Engine** | Execute formulas; handle caching; manage dependencies; support batch/real-time modes. |
| **KPI Engine** | Manage KPI definitions; calculate values; track history; compare against targets; benchmarking. |
| **Validation Engine** | Syntax validation; circular reference detection; dependency analysis; performance profiling. |
| **AI Integration** | Generate formulas; optimize performance; detect errors; explain logic; recommend KPIs. |
| **Version Control** | Track formula/KPI versions; approval workflow; rollback; change history. |
| **Security Layer** | RBAC integration; encrypted values; audit logging; approval enforcement. |

---

## 2. KPI Engine Architecture

### 2.1 KPI Lifecycle

1. **Definition:** Create KPI with formula, category, owner, targets, thresholds.
2. **Validation:** Validate formula, check dependencies, estimate performance.
3. **Approval:** Submit for approval; workflow execution; version publishing.
4. **Execution:** Calculate on schedule, event, or demand; cache results.
5. **Monitoring:** Track values vs targets; alert on thresholds; trend analysis.
6. **Benchmarking:** Compare against internal/external benchmarks.
7. **Review:** Periodic review; update formula; adjust targets.

### 2.2 KPI Categories

| Industry | KPI Categories | Examples |
|----------|----------------|----------|
| Financial | Revenue, Profit, Costs, Cash Flow, ROI, ROE | Monthly Revenue Growth, Cost-to-Income Ratio |
| Health | Patient Care, Operations, Quality, Safety | Bed Occupancy Rate, Readmission Rate, Average Wait Time |
| Education | Enrollment, Performance, Attendance, Completion | Student Enrollment Rate, Pass Rate, Teacher-Student Ratio |
| Government | Service Delivery, Budget Utilization, Project Completion | Budget Execution Rate, Citizen Satisfaction, Project On-Time Delivery |
| Church | Attendance, Giving, Membership, Engagement | Weekly Attendance, Giving per Member, Visitor Conversion Rate |
| Manufacturing | Production, Quality, Efficiency, Maintenance | OEE, Defect Rate, Production Yield, Downtime Percentage |
| Retail | Sales, Inventory, Customer, Margin | Sales Growth, Inventory Turnover, Customer Retention, Gross Margin |
| Logistics | Delivery, Cost, Efficiency, Fleet | On-Time Delivery Rate, Cost per Shipment, Route Efficiency |

### 2.3 KPI Features

- **Multi-dimensional:** Support for department, region, product, time dimensions.
- **Target Management:** Set absolute, relative, or trend-based targets.
- **Thresholds:** Define warning, critical, and success thresholds.
- **Trend Analysis:** Calculate trend direction, momentum, acceleration.
- **Benchmarking:** Internal peer comparison and external industry benchmarks.
- **AI Explanation:** Natural language explanation of KPI values and changes.
- **Drill-down:** Navigate from KPI to underlying data and formula components.

---

## 3. Formula Language Specification

### 3.1 Supported Operators

| Category | Operators | Description |
|----------|-----------|-------------|
| Arithmetic | +, -, *, /, %, ^, () | Basic arithmetic and exponentiation |
| Comparison | =, !=, <, <=, >, >= | Value comparisons |
| Logical | AND, OR, NOT, IF, CASE | Logical operations and conditionals |
| Membership | IN, BETWEEN, IS NULL, COALESCE | Set and null operations |

### 3.2 Function Library

| Category | Functions | Examples |
|----------|-----------|----------|
| Mathematical | ROUND, CEIL, FLOOR, ABS, SQRT, POWER, LOG, EXP | ROUND(value, 2), ABS(variance) |
| Statistical | MIN, MAX, AVG, SUM, COUNT, COUNT_DISTINCT, MEDIAN, MODE, STDDEV, VARIANCE, PERCENTILE | AVG(sales), PERCENTILE(values, 95) |
| Financial | NPV, IRR, PV, FV, PMT, ROI, ROE, GROWTH_RATE | ROI(gain, cost), GROWTH_RATE(current, previous) |
| Date/Time | DATE, YEAR, MONTH, DAY, HOUR, MINUTE, DATEDIFF, DATEADD, NOW, TODAY | DATEDIFF(end_date, start_date, 'day') |
| String | CONCAT, SUBSTRING, UPPER, LOWER, LENGTH, TRIM, REPLACE | CONCAT(first_name, ' ', last_name) |
| Conditional | IF, CASE, IIF, SWITCH | IF(condition, true_value, false_value) |
| Aggregate | SUM, AVG, COUNT, MIN, MAX (with GROUP BY) | SUM(amount) GROUP BY department |

### 3.3 Variable System

- **Global Variables:** Organization-wide constants (e.g., tax_rate, exchange_rate).
- **Department Variables:** Department-specific values.
- **Time Variables:** Dynamic date/time variables (e.g., current_month, previous_year).
- **Data Variables:** References to database columns and metrics.
- **Calculated Variables:** Intermediate results for complex formulas.

### 3.4 Formula Examples

```
# Revenue Growth Rate
GROWTH_RATE(current_month_revenue, previous_month_revenue)

# Patient Satisfaction Score
AVG(satisfaction_rating) WHERE department = 'Emergency' AND date >= DATEADD(NOW(), -30, 'day')

# OEE (Overall Equipment Effectiveness)
(AVailability * Performance * Quality) / 100

# Class Pass Rate
(COUNT(CASE WHEN grade >= 50 THEN 1 END) / COUNT(*)) * 100

# Monthly Giving Trend
LINEAR_TREND(giving_amount, date) WHERE date >= DATEADD(NOW(), -12, 'month')

# Inventory Turnover
COGS / AVG(inventory_value)

# Customer Lifetime Value
(AVG(order_value) * AVG(frequency_per_year)) / AVG(churn_rate)

# Bed Occupancy Rate
(AVG(occupied_beds) / total_beds) * 100

# Budget Variance
((actual_spend - budgeted_amount) / budgeted_amount) * 100
```

---

## 4. Database Schema

### 4.1 Tables

```sql
CREATE TABLE formulas (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  expression TEXT NOT NULL,
  variables JSON,
  functions JSON,
  version INT NOT NULL DEFAULT 1,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  tags JSON,
  owner_id BIGINT,
  approved_by BIGINT,
  approved_at DATETIME,
  is_template BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (category_id) REFERENCES formula_categories(id),
  FOREIGN KEY (owner_id) REFERENCES users(id),
  FOREIGN KEY (approved_by) REFERENCES users(id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_category (category_id),
  INDEX idx_owner (owner_id)
) ENGINE=InnoDB;

CREATE TABLE formula_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  version INT NOT NULL,
  expression TEXT NOT NULL,
  variables JSON,
  functions JSON,
  changelog TEXT,
  performance_metrics JSON,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  UNIQUE KEY uniq_formula_version (formula_id, version),
  INDEX idx_formula (formula_id)
) ENGINE=InnoDB;

CREATE TABLE formula_variables (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  version INT NOT NULL,
  name VARCHAR(128) NOT NULL,
  type VARCHAR(64) NOT NULL, -- global, department, time, data, calculated
  source VARCHAR(255), -- table.column, constant, calculation
  default_value JSON,
  description TEXT,
  is_required BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_formula_version_var (formula_id, version, name),
  INDEX idx_formula (formula_id)
) ENGINE=InnoDB;

CREATE TABLE formula_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  parent_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES formula_categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE formula_dependencies (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  version INT NOT NULL,
  depends_on_formula_id BIGINT,
  depends_on_variable VARCHAR(128),
  dependency_type VARCHAR(32) NOT NULL, -- formula, variable, table
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  FOREIGN KEY (depends_on_formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  INDEX idx_formula (formula_id),
  INDEX idx_depends_on (depends_on_formula_id)
) ENGINE=InnoDB;

CREATE TABLE formula_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  version INT NOT NULL,
  action VARCHAR(64) NOT NULL, -- created, updated, approved, published
  changes JSON,
  user_id BIGINT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_formula (formula_id),
  INDEX idx_user (user_id),
  INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

CREATE TABLE formula_tests (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  version INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  input_variables JSON,
  expected_output JSON,
  actual_output JSON,
  status VARCHAR(32) NOT NULL, -- passed, failed, error
  error_message TEXT,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_formula (formula_id),
  INDEX idx_status (status)
) ENGINE=InnoDB;

CREATE TABLE kpis (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  formula_id BIGINT NOT NULL,
  formula_version INT NOT NULL,
  unit VARCHAR(64),
  currency VARCHAR(8),
  frequency VARCHAR(32), -- real_time, hourly, daily, weekly, monthly, quarterly, yearly
  owner_id BIGINT,
  tags JSON,
  is_active BOOLEAN DEFAULT TRUE,
  is_benchmarkable BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (category_id) REFERENCES kpi_categories(id),
  FOREIGN KEY (formula_id) REFERENCES formulas(id),
  FOREIGN KEY (owner_id) REFERENCES users(id),
  INDEX idx_org_active (organization_id, is_active),
  INDEX idx_category (category_id),
  INDEX idx_formula (formula_id),
  INDEX idx_owner (owner_id)
) ENGINE=InnoDB;

CREATE TABLE kpi_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  industry_id BIGINT,
  parent_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (parent_id) REFERENCES kpi_categories(id),
  INDEX idx_industry (industry_id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE kpi_targets (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  kpi_id BIGINT NOT NULL,
  department_id BIGINT,
  target_type VARCHAR(32) NOT NULL, -- absolute, percentage, trend
  target_value DECIMAL(18,4),
  target_min DECIMAL(18,4),
  target_max DECIMAL(18,4),
  period_type VARCHAR(32), -- monthly, quarterly, yearly
  start_date DATE,
  end_date DATE,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kpi_id) REFERENCES kpis(id) ON DELETE CASCADE,
  FOREIGN KEY (department_id) REFERENCES departments(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_kpi (kpi_id),
  INDEX idx_department (department_id),
  INDEX idx_period (period_type)
) ENGINE=InnoDB;

CREATE TABLE kpi_thresholds (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  kpi_id BIGINT NOT NULL,
  threshold_type VARCHAR(32) NOT NULL, -- warning, critical, success
  condition_operator VARCHAR(16) NOT NULL, -- lt, lte, gt, gte, eq, ne
  threshold_value DECIMAL(18,4),
  color VARCHAR(16), -- red, yellow, green
  notification_config JSON,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kpi_id) REFERENCES kpis(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_kpi (kpi_id),
  INDEX idx_type (threshold_type)
) ENGINE=InnoDB;

CREATE TABLE kpi_values (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  kpi_id BIGINT NOT NULL,
  organization_id BIGINT NOT NULL,
  department_id BIGINT,
  region_id VARCHAR(128),
  period_type VARCHAR(32),
  period_start DATE,
  period_end DATE,
  value DECIMAL(18,4),
  target_value DECIMAL(18,4),
  variance DECIMAL(18,4),
  variance_percent DECIMAL(8,4),
  trend_direction VARCHAR(16), -- up, down, stable
  calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kpi_id) REFERENCES kpis(id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (department_id) REFERENCES departments(id),
  UNIQUE KEY uniq_kpi_period (kpi_id, organization_id, department_id, region_id, period_type, period_start),
  INDEX idx_kpi_period (kpi_id, period_type, period_start),
  INDEX idx_org_dept (organization_id, department_id)
) ENGINE=InnoDB;

CREATE TABLE kpi_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  kpi_id BIGINT NOT NULL,
  value DECIMAL(18,4),
  previous_value DECIMAL(18,4),
  change_amount DECIMAL(18,4),
  change_percent DECIMAL(8,4),
  period_type VARCHAR(32),
  period_start DATE,
  calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kpi_id) REFERENCES kpis(id) ON DELETE CASCADE,
  INDEX idx_kpi_date (kpi_id, calculated_at),
  INDEX idx_period (period_type, period_start)
) ENGINE=InnoDB;

CREATE TABLE kpi_benchmarks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  kpi_id BIGINT NOT NULL,
  benchmark_type VARCHAR(32) NOT NULL, -- internal, industry, custom
  peer_group JSON,
  percentile_25 DECIMAL(18,4),
  percentile_50 DECIMAL(18,4),
  percentile_75 DECIMAL(18,4),
  average DECIMAL(18,4),
  best_in_class DECIMAL(18,4),
  data_points INT,
  period_end DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kpi_id) REFERENCES kpis(id) ON DELETE CASCADE,
  INDEX idx_kpi_type (kpi_id, benchmark_type),
  INDEX idx_period (period_end)
) ENGINE=InnoDB;

CREATE TABLE formula_permissions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT NOT NULL,
  role_id BIGINT,
  user_id BIGINT,
  permission_type VARCHAR(32) NOT NULL, -- view, edit, approve, use
  granted_by BIGINT NOT NULL,
  granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (granted_by) REFERENCES users(id),
  INDEX idx_formula (formula_id),
  INDEX idx_role (role_id),
  INDEX idx_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE formula_audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  formula_id BIGINT,
  kpi_id BIGINT,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL,
  old_value JSON,
  new_value JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (formula_id) REFERENCES formulas(id),
  FOREIGN KEY (kpi_id) REFERENCES kpis(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_formula (formula_id),
  INDEX idx_kpi (kpi_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;
```

### 4.2 Indexes & Optimization

- Primary keys on all tables.
- Foreign key indexes.
- Composite indexes for common queries (org+status, kpi+period, formula+version).
- Full-text indexes on formula name and description for search.
- Partition `kpi_values` and `kpi_history` by month if needed.

---

## 5. ER Diagram (Textual)

```
formulas (1) → (n) formula_versions
formulas (1) → (n) formula_variables
formulas (1) → (n) formula_dependencies
formulas (1) → (n) formula_history
formulas (1) → (n) formula_tests
formulas (1) → (n) formula_permissions
formulas (1) → (n) formula_audit_logs
formulas (1) → (n) kpis

kpis (1) → (n) kpi_targets
kpis (1) → (n) kpi_thresholds
kpis (1) → (n) kpi_values
kpis (1) → (n) kpi_history
kpis (1) → (n) kpi_benchmarks
kpis (1) → (n) formula_audit_logs

formula_categories (1) → (n) formulas
kpi_categories (1) → (n) kpis
industries (1) → (n) kpi_categories
```

---

## 6. API Specification

Base path: `/api/v1/formulas`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/formulas` | List formulas. |
| POST | `/formulas` | Create formula. |
| GET | `/formulas/{id}` | Get formula details. |
| PUT | `/formulas/{id}` | Update formula. |
| DELETE | `/formulas/{id}` | Delete formula. |
| POST | `/formulas/{id}/validate` | Validate formula. |
| POST | `/formulas/{id}/test` | Test formula with sample data. |
| POST | `/formulas/{id}/publish` | Publish formula version. |
| GET | `/formulas/{id}/versions` | List formula versions. |
| GET | `/formulas/{id}/history` | Get formula change history. |
| GET | `/formulas/categories` | List formula categories. |
| POST | `/formulas/categories` | Create formula category. |
| GET | `/formulas/variables` | List available variables. |
| GET | `/formulas/functions` | List available functions. |

Base path: `/api/v1/kpis`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/kpis` | List KPIs. |
| POST | `/kpis` | Create KPI. |
| GET | `/kpis/{id}` | Get KPI details. |
| PUT | `/kpis/{id}` | Update KPI. |
| DELETE | `/kpis/{id}` | Delete KPI. |
| GET | `/kpis/{id}/values` | Get KPI values. |
| POST | `/kpis/{id}/calculate` | Calculate KPI value. |
| GET | `/kpis/{id}/targets` | Get KPI targets. |
| POST | `/kpis/{id}/targets` | Set KPI target. |
| GET | `/kpis/{id}/thresholds` | Get KPI thresholds. |
| POST | `/kpis/{id}/thresholds` | Set KPI threshold. |
| GET | `/kpis/{id}/history` | Get KPI history. |
| GET | `/kpis/{id}/benchmarks` | Get KPI benchmarks. |
| GET | `/kpis/categories` | List KPI categories. |
| POST | `/kpis/categories` | Create KPI category. |
| GET | `/kpis/dashboard` | Get KPI dashboard data. |

### Example: Create Formula

```http
POST /api/v1/formulas
{
  "name": "Revenue Growth Rate",
  "description": "Month-over-month revenue growth percentage",
  "category_id": 1,
  "expression": "((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100",
  "variables": [
    {
      "name": "current_month_revenue",
      "type": "data",
      "source": "sales.amount WHERE date >= DATEADD(NOW(), -1, 'month')",
      "description": "Revenue for current month"
    },
    {
      "name": "previous_month_revenue",
      "type": "data",
      "source": "sales.amount WHERE date >= DATEADD(NOW(), -2, 'month') AND date < DATEADD(NOW(), -1, 'month')",
      "description": "Revenue for previous month"
    }
  ],
  "tags": ["financial", "growth", "revenue"]
}
```

Response:
```json
{
  "id": 123,
  "name": "Revenue Growth Rate",
  "status": "draft",
  "version": 1,
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "performance_estimate": "fast"
  }
}
```

---

## 7. Backend Architecture

### 7.1 Package Structure

```
formula_engine/
├── __init__.py
├── parser.py                 # Expression parser
├── executor.py               # Formula execution engine
├── validator.py              # Formula validation
├── optimizer.py              # Performance optimization
├── functions/                # Built-in functions
│   ├── __init__.py
│   ├── mathematical.py
│   ├── statistical.py
│   ├── financial.py
│   ├── datetime.py
│   └── string.py
├── kpi/
│   ├── __init__.py
│   ├── calculator.py         # KPI calculation
│   ├── aggregator.py         # Data aggregation
│   ├── benchmarker.py        # Benchmarking
│   └── reporter.py           # KPI reporting
├── ai/
│   ├── __init__.py
│   ├── generator.py          # AI formula generation
│   ├── optimizer.py          # AI optimization
│   └ explainer.py            # AI explanation
├── api/
│   └── routes.py             # Formula/KPI APIs
├── models/
│   └── formula_models.py     # SQLAlchemy models
├── schemas/
│   └── formula_schemas.py    # Pydantic schemas
└── migrations/               # Alembic migrations
```

### 7.2 Expression Parser

```python
class FormulaParser:
    def __init__(self):
        self.lexer = FormulaLexer()
        self.parser = FormulaParserGrammar()
    
    def parse(self, expression: str) -> ASTNode:
        """Parse formula expression into AST."""
        tokens = self.lexer.tokenize(expression)
        ast = self.parser.parse(tokens)
        return ast
    
    def validate(self, ast: ASTNode) -> ValidationResult:
        """Validate AST for syntax and semantic errors."""
        validator = FormulaValidator()
        return validator.validate(ast)
```

### 7.3 Execution Engine

```python
class FormulaExecutor:
    def __init__(self, cache: Cache, db: Database):
        self.cache = cache
        self.db = db
    
    async def execute(self, formula: Formula, variables: dict = None) -> FormulaResult:
        """Execute formula with given variables."""
        # Check cache
        cache_key = self.generate_cache_key(formula, variables)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Parse and validate
        ast = self.parser.parse(formula.expression)
        
        # Resolve variables
        resolved_vars = await self.resolve_variables(formula, variables)
        
        # Execute
        result = await self.evaluate_ast(ast, resolved_vars)
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=300)
        
        return result
    
    async def evaluate_ast(self, node: ASTNode, variables: dict) -> Any:
        """Evaluate AST node recursively."""
        if node.type == 'binary_op':
            left = await self.evaluate_ast(node.left, variables)
            right = await self.evaluate_ast(node.right, variables)
            return self.apply_operator(node.operator, left, right)
        elif node.type == 'function':
            args = [await self.evaluate_ast(arg, variables) for arg in node.args]
            return await self.call_function(node.name, args)
        elif node.type == 'variable':
            return variables.get(node.name)
        elif node.type == 'literal':
            return node.value
        else:
            raise FormulaError(f"Unknown node type: {node.type}")
```

### 7.4 KPI Calculator

```python
class KPICalculator:
    def __init__(self, formula_executor: FormulaExecutor, db: Database):
        self.formula_executor = formula_executor
        self.db = db
    
    async def calculate_kpi(self, kpi: KPI, period: DateRange, dimensions: dict = None) -> KPIValue:
        """Calculate KPI value for given period and dimensions."""
        # Get formula
        formula = await self.get_formula(kpi.formula_id, kpi.formula_version)
        
        # Resolve time variables
        variables = self.resolve_time_variables(period)
        
        # Add dimension variables
        if dimensions:
            variables.update(dimensions)
        
        # Execute formula
        result = await self.formula_executor.execute(formula, variables)
        
        # Get target for comparison
        target = await self.get_target(kpi.id, period, dimensions)
        
        # Calculate variance
        variance = result.value - target.value if target else None
        variance_percent = (variance / target.value * 100) if target and target.value != 0 else None
        
        # Determine trend
        trend = await self.calculate_trend(kpi.id, period)
        
        return KPIValue(
            kpi_id=kpi.id,
            value=result.value,
            target_value=target.value if target else None,
            variance=variance,
            variance_percent=variance_percent,
            trend_direction=trend,
            calculated_at=datetime.utcnow()
        )
```

---

## 8. Frontend Architecture

### 8.1 Formula Builder Components

- **FormulaCanvas:** Visual drag-and-drop canvas for building formulas.
- **ExpressionEditor:** Text-based editor with syntax highlighting and autocomplete.
- **FunctionPalette:** Searchable library of functions with documentation.
- **VariableExplorer:** Tree view of available variables and data sources.
- **TestPanel:** Interface for testing formulas with sample data.
- **ValidationPanel:** Real-time validation feedback with error highlighting.

### 8.2 KPI Management Components

- **KPICard:** Visual KPI card with value, trend, target, and status.
- **KPIEditor:** Form for creating/editing KPI definitions.
- **TargetSetter:** Interface for setting KPI targets and thresholds.
- **BenchmarkViewer:** Visual comparison of KPI against benchmarks.
- **KPIDashboard:** Comprehensive KPI dashboard with filters and drill-downs.

### 8.3 State Management

- **FormulaStore:** Current formula, validation state, execution results.
- **KPIStore:** KPI definitions, values, targets, thresholds.
- **VariableStore:** Available variables, data sources, cache.
- **UserStore:** Permissions, favorites, recent formulas.

### 8.4 Real-time Features

- **Live Calculation:** Real-time formula evaluation as user types.
- **Collaborative Editing:** Multiple users editing formulas (optional).
- **Live KPI Updates:** WebSocket updates for KPI value changes.
- **Notification System:** Alerts for threshold breaches and approvals.

---

## 9. AI Integration

### 9.1 AI Formula Generator

```python
class AIFormulaGenerator:
    def __init__(self, ai_gateway: AIGateway):
        self.ai_gateway = ai_gateway
    
    async def generate_formula(self, requirement: str, context: dict) -> FormulaSuggestion:
        """Generate formula based on natural language requirement."""
        prompt = f"""
        Generate a formula for: {requirement}
        
        Available variables: {context.get('variables', [])}
        Available functions: {context.get('functions', [])}
        
        Return JSON with:
        - expression: formula expression
        - description: what the formula calculates
        - variables: list of variables used
        - confidence: confidence score 0-1
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="formula_generator")
        return FormulaSuggestion.from_ai_response(response)
```

### 9.2 AI Formula Optimizer

- **Performance Analysis:** Identify slow operations and suggest optimizations.
- **Expression Simplification:** Simplify complex expressions.
- **Caching Recommendations:** Suggest caching strategies.
- **Index Suggestions:** Recommend database indexes for data variables.

### 9.3 AI Error Detection

- **Syntax Error Detection:** Identify and fix syntax errors.
- **Logical Error Detection:** Detect potential logical flaws.
- **Data Quality Issues:** Identify potential data problems.
- **Performance Issues:** Detect potential performance bottlenecks.

### 9.4 AI Formula Explanation

```python
class AIFormulaExplainer:
    async def explain_formula(self, formula: Formula, value: float) -> str:
        """Generate natural language explanation of formula and its value."""
        prompt = f"""
        Explain this formula in simple terms:
        Formula: {formula.expression}
        Description: {formula.description}
        Current Value: {value}
        
        Explain:
        1. What the formula calculates
        2. How the current value was derived
        3. What the value means for the business
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="formula_explainer")
        return response.response
```

---

## 10. Validation Engine

### 10.1 Validation Types

- **Syntax Validation:** Check for valid expression syntax.
- **Semantic Validation:** Validate variable references and function calls.
- **Circular Reference Detection:** Detect circular dependencies between formulas.
- **Performance Analysis:** Estimate execution time and resource usage.
- **Data Validation:** Verify data sources exist and are accessible.

### 10.2 Validation Process

```python
class FormulaValidator:
    async def validate(self, formula: Formula) -> ValidationResult:
        """Comprehensive formula validation."""
        result = ValidationResult()
        
        # Syntax validation
        syntax_result = await self.validate_syntax(formula.expression)
        result.add_validation('syntax', syntax_result)
        
        # Semantic validation
        semantic_result = await self.validate_semantics(formula)
        result.add_validation('semantics', semantic_result)
        
        # Circular reference check
        circular_result = await self.check_circular_references(formula)
        result.add_validation('circular', circular_result)
        
        # Performance analysis
        performance_result = await self.analyze_performance(formula)
        result.add_validation('performance', performance_result)
        
        return result
```

### 10.3 Circular Reference Detection

```python
class CircularReferenceDetector:
    async def detect(self, formula_id: int) -> List[CircularReference]:
        """Detect circular references in formula dependencies."""
        # Build dependency graph
        graph = await self.build_dependency_graph(formula_id)
        
        # Detect cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
```

---

## 11. Performance Strategy

### 11.1 Caching Strategy

- **Formula Cache:** Cache parsed ASTs and execution plans.
- **Result Cache:** Cache calculation results with TTL based on data freshness.
- **Variable Cache:** Cache frequently accessed variables.
- **Dependency Cache:** Cache formula dependency graphs.

### 11.2 Query Optimization

- **Predicate Pushdown:** Push filters to database queries.
- **Index Utilization:** Ensure data variables use appropriate indexes.
- **Batch Processing:** Batch multiple calculations together.
- **Parallel Execution:** Execute independent formulas in parallel.

### 11.3 Database Optimization

- **Materialized Views:** Pre-calculate expensive aggregations.
- **Partitioning:** Partition large tables by date.
- **Connection Pooling:** Efficient database connection management.
- **Query Optimization:** Analyze and optimize slow queries.

### 11.4 Frontend Performance

- **Lazy Loading:** Load formulas and KPIs on demand.
- **Virtual Scrolling:** Handle large lists efficiently.
- **Debounced Validation:** Validate formulas as user types with debouncing.
- **Memoization:** Cache expensive calculations in the UI.

---

## 12. Security Design

### 12.1 RBAC Integration

- **Formula Permissions:** view, edit, approve, use formulas.
- **KPI Permissions:** view, edit, manage KPIs.
- **Data Access:** Formulas inherit user permissions for data access.
- **Approval Workflow:** Enforce approval for production formulas.

### 12.2 Data Protection

- **Encrypted Variables:** Sensitive variables stored encrypted.
- **Audit Logging:** All formula/KPI actions logged.
- **Input Validation:** Validate all inputs to prevent injection.
- **SQL Injection Prevention:** Use parameterized queries for data variables.

### 12.3 Execution Security

- **Sandboxed Execution:** Isolate formula execution environment.
- **Resource Limits:** Limit execution time and memory usage.
- **Permission Validation:** Validate data access permissions at runtime.
- **Error Handling:** Prevent information leakage in error messages.

---

## 13. Testing Strategy

### 13.1 Unit Tests

- **Formula Parser Tests:** Test expression parsing and AST generation.
- **Function Tests:** Test all built-in functions.
- **Validator Tests:** Test validation logic.
- **KPI Calculator Tests:** Test KPI calculation logic.

### 13.2 Integration Tests

- **API Tests:** Test all REST endpoints.
- **Database Tests:** Test database operations.
- **Cache Tests:** Test caching behavior.
- **AI Integration Tests:** Test AI features.

### 13.3 Performance Tests

- **Load Tests:** Test with many concurrent formula executions.
- **Stress Tests:** Test system limits.
- **Scalability Tests:** Test horizontal scaling.

### 13.4 Security Tests

- **Permission Tests:** Test RBAC enforcement.
- **Injection Tests:** Test for SQL and formula injection.
- **Data Access Tests:** Test data access controls.
- **Encryption Tests:** Test variable encryption.

---

## 14. Administrator Guide

### 14.1 Formula Management

- **Creating Formulas:** Use visual builder or expression editor.
- **Version Control:** Manage formula versions and approvals.
- **Performance Monitoring:** Monitor formula execution performance.
- **User Permissions:** Manage formula access permissions.

### 14.2 KPI Management

- **KPI Definition:** Create and configure KPIs.
- **Target Setting:** Set targets and thresholds.
- **Benchmarking:** Configure internal and external benchmarks.
- **Monitoring:** Monitor KPI performance and alerts.

### 14.3 System Configuration

- **Function Library:** Manage available functions.
- **Variable Sources:** Configure data sources and variables.
- **Performance Tuning:** Optimize system performance.
- **Security Settings:** Configure security policies.

---

## 15. Developer Guide

### 15.1 Custom Functions

- **Function Interface:** Implement the Function interface.
- **Registration:** Register custom functions in the system.
- **Documentation:** Provide function documentation.
- **Testing:** Write comprehensive tests.

### 15.2 Formula API

- **REST API:** Use REST API for formula operations.
- **WebSocket API:** Real-time formula updates.
- **Authentication:** Use API keys or JWT.
- **Rate Limits:** Respect rate limits.

### 15.3 Best Practices

- **Performance:** Optimize formulas for performance.
- **Readability:** Write clear, well-documented formulas.
- **Testing:** Test formulas thoroughly.
- **Security**: Follow security best practices.

---

## 16. Output Summary

1. **Formula Engine Architecture** — design principles, components, expression language.
2. **KPI Engine Architecture** — lifecycle, categories, features, multi-dimensional support.
3. **Database Schema** — 15 tables with DDL, indexes, relationships, audit fields.
4. **ER Diagram** — textual representation of table relationships.
5. **API Specification** — 30+ REST endpoints for formulas and KPIs.
6. **Backend Architecture** — package structure, parser, executor, KPI calculator.
7. **Frontend Architecture** — builder components, KPI management, state management.
8. **AI Integration** — formula generation, optimization, error detection, explanation.
9. **Validation Engine** — syntax, semantic, circular reference, performance validation.
10. **Performance Strategy** — caching, query optimization, database optimization.
11. **Security Design** — RBAC, data protection, execution security.
12. **Testing Strategy** — unit, integration, performance, security tests.
13. **Administrator Guide** — formula management, KPI management, system configuration.
14. **Developer Guide** — custom functions, API usage, best practices.

All specifications are enterprise-grade, scalable, modular, production-ready, and fully integrated into AEDIP.
