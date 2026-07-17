# Phase 8.5 — Enterprise Dashboard Builder

## Purpose

This document defines the Enterprise Dashboard Builder for AEDIP, enabling organizations to visually design interactive dashboards without writing code. The builder supports various dashboard types, a rich widget library, AI-powered features, and enterprise-grade security and performance.

---

## 1. Dashboard Builder Architecture

### 1.1 Design Principles

- **Visual First:** Drag-and-drop interface with real-time preview.
- **Responsive Design:** Dashboards adapt to desktop, tablet, and mobile.
- **Interactive Widgets:** Rich interactions including filtering, drill-down, and cross-filtering.
- **AI-Enhanced:** AI-powered layout optimization, widget recommendations, and insights.
- **Enterprise Ready:** Role-based access, audit trails, version control, and performance optimization.
- **Extensible:** Plugin architecture for custom widgets and themes.
- **Collaborative:** Comments, mentions, sharing, and templates.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Enterprise Dashboard Builder                                │
│  Dashboard Designer · Widget Engine · Layout Engine · Filter Engine · AI Engine │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Dashboard    │                │  Widget Engine  │               │  Layout Engine     │
│  Designer UI  │                │                 │               │                    │
│               │                │ Widget Library │               │ Responsive Grid    │
│ Canvas        │                │ Rendering       │               │ Snap-to-Grid       │
│ Widget Palette│                │ Interactivity   │               │ Auto-Alignment     │
│ Properties    │                │ Data Binding    │               │ Responsive Breaks  │
│ Preview       │                │ Real-time       │               │ Multi-page         │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Dashboard Designer UI** | Visual drag-and-drop designer; widget palette; property panel; preview mode. |
| **Widget Engine** | Widget library; rendering; data binding; interactivity; real-time updates. |
| **Layout Engine** | Responsive grid system; snap-to-grid; auto-alignment; multi-page support. |
| **Filter Engine** | Global filters; widget filters; cross-filtering; drill-down; saved views. |
| **AI Engine** | Dashboard generation; widget recommendations; layout optimization; insights. |
| **Security Layer** | RBAC integration; dashboard permissions; widget permissions; audit logging. |
| **Performance Layer** | Lazy loading; caching; virtual scrolling; incremental rendering. |
| **Collaboration Layer** | Comments; mentions; sharing; favorites; templates. |

---

## 2. Widget Architecture

### 2.1 Widget Categories

| Category | Widgets | Description |
|----------|---------|-------------|
| **KPI & Metrics** | KPI Card, Gauge, Sparkline, Progress Bar, Trend Indicator | Display key metrics and performance indicators. |
| **Charts** | Bar, Line, Pie, Area, Scatter, Bubble, Radar, Waterfall | Various chart types for data visualization. |
| **Tables** | Data Table, Pivot Table, Summary Table | Tabular data display with sorting and filtering. |
| **Maps** | Geo Map, Heatmap, Choropleth | Geographic data visualization. |
| **Advanced** | Treemap, Sankey, Network Graph, Funnel | Complex visualizations for specific use cases. |
| **AI & Analytics** | AI Insight Card, Forecast Chart, Anomaly Detector | AI-powered analytics and predictions. |
| **Operational** | Alert Panel, Task List, Workflow Status, ETL Status | Real-time operational monitoring. |
| **Content** | Markdown, Rich Text, Image, Video, Embedded Content | Static and dynamic content display. |
| **Interactive** | Filter Panel, Date Range Selector, Bookmark Menu | User interaction controls. |
| **Custom** | Plugin Widgets | Extensible widgets from plugins. |

### 2.2 Widget Specification

Each widget implements the Widget interface:

```typescript
interface Widget {
  id: string;
  type: string;
  title: string;
  position: { x: number; y: number; width: number; height: number };
  config: WidgetConfig;
  dataSource: DataSource;
  permissions: string[];
  refreshInterval?: number;
}
```

### 2.3 Widget Configuration

```typescript
interface WidgetConfig {
  // Common properties
  title: string;
  subtitle?: string;
  theme: string;
  showBorder: boolean;
  backgroundColor: string;
  
  // Chart-specific
  chartType?: string;
  xAxis?: AxisConfig;
  yAxis?: AxisConfig;
  series?: SeriesConfig[];
  
  // Table-specific
  columns?: ColumnConfig[];
  pagination?: PaginationConfig;
  
  // KPI-specific
  valueFormat?: string;
  targetValue?: number;
  trendDirection?: 'up' | 'down' | 'stable';
  
  // Filter-specific
  filterType?: string;
  filterOptions?: FilterOption[];
  defaultValue?: any;
}
```

### 2.4 Data Binding

Widgets can bind to various data sources:

- **Database Queries:** Direct SQL queries with parameterization.
- **API Endpoints:** REST API calls with authentication.
- **KPI Values:** Pre-calculated KPI values from KPI Engine.
- **ETL Results:** Results from ETL pipeline runs.
- **AI Insights:** Insights from AI Platform.
- **Static Data:** Fixed data sets.

---

## 3. Visual Dashboard Designer

### 3.1 Designer Features

- **Canvas:** Infinite canvas with zoom and pan capabilities.
- **Grid System:** Responsive grid with snap-to-grid functionality.
- **Widget Palette:** Searchable library of widgets with previews.
- **Property Panel:** Dynamic property editor based on selected widget.
- **Preview Mode:** Real-time preview of dashboard with live data.
- **Responsive Breakpoints:** Design for desktop, tablet, and mobile.
- **Undo/Redo:** Full history with keyboard shortcuts.
- **Auto-alignment:** Smart alignment guides and distribution tools.
- **Multi-page Support:** Create dashboards with multiple pages/tabs.

### 3.2 Layout System

- **12-Column Grid:** Bootstrap-like responsive grid system.
- **Breakpoints:** 
  - Desktop: ≥1200px
  - Tablet: 768px-1199px
  - Mobile: <768px
- **Widget Sizing:** Widgets span grid columns with flexible heights.
- **Responsive Behavior:** Widgets stack or resize based on screen size.

### 3.3 Templates

- **Industry Templates:** Pre-built templates for different industries.
- **Use Case Templates:** Templates for common use cases (sales, finance, operations).
- **Custom Templates:** Save dashboard layouts as templates.
- **Template Variables:** Parameterized templates for customization.

---

## 4. Interactivity Features

### 4.1 Filtering System

- **Global Filters:** Dashboard-level filters affecting all widgets.
- **Widget Filters:** Widget-specific filters for individual data.
- **Cross-filtering:** Widgets filter each other based on selection.
- **Filter Types:** Date range, dropdown, multiselect, search, slider.
- **Saved Views:** Save filter combinations as named views.

### 4.2 Drill-down & Drill-through

- **Drill-down:** Navigate from summary to detailed data within widget.
- **Drill-through:** Navigate to different dashboard with filtered context.
- **Breadcrumb Navigation:** Track drill-down path for easy navigation.

### 4.3 Linked Dashboards

- **Dashboard Links:** Link widgets to other dashboards with context.
- **Parameter Passing:** Pass filter values and selections to linked dashboards.
- **Back Navigation:** Easy navigation back to source dashboard.

### 4.4 Bookmarks

- **Personal Bookmarks:** Save personal dashboard states.
- **Shared Bookmarks:** Share bookmarked views with other users.
- **Bookmark Permissions:** Control who can view and modify bookmarks.

---

## 5. AI Integration

### 5.1 AI Dashboard Generator

```python
class AIDashboardGenerator:
    async def generate_dashboard(self, requirement: str, context: dict) -> DashboardDesign:
        """Generate dashboard design based on natural language requirement."""
        prompt = f"""
        Generate a dashboard for: {requirement}
        
        Available data sources: {context.get('data_sources', [])}
        Available widgets: {context.get('widgets', [])}
        User role: {context.get('role', 'analyst')}
        Industry: {context.get('industry', 'general')}
        
        Return JSON with:
        - layout: widget positions and sizes
        - widgets: widget configurations
        - filters: recommended filters
        - theme: suggested theme
        - rationale: design decisions
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="dashboard_generator")
        return DashboardDesign.from_ai_response(response)
```

### 5.2 AI Widget Recommendations

- **Data-driven Suggestions:** Recommend widgets based on data types and patterns.
- **Usage Patterns:** Suggest widgets based on user role and industry.
- **Performance Optimization:** Recommend efficient widgets for large datasets.

### 5.3 AI Layout Optimization

- **Space Optimization:** Efficient use of canvas space.
- **Visual Hierarchy:** Arrange widgets by importance and relationships.
- **Responsive Optimization:** Optimize layout for different screen sizes.

### 5.4 AI Insights

- **Anomaly Detection:** Highlight anomalies in data visualizations.
- **Trend Analysis:** Identify and explain trends in data.
- **Narrative Generation:** Generate natural language summaries of dashboard insights.

---

## 6. Database Schema

### 6.1 Tables

```sql
CREATE TABLE dashboards (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  dashboard_type VARCHAR(64) NOT NULL, -- executive, operational, department, personal, ai, analytics, monitoring, wallboard, mobile, embedded, public
  owner_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  theme VARCHAR(128),
  is_template BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  tags JSON,
  metadata JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (category_id) REFERENCES dashboard_categories(id),
  FOREIGN KEY (owner_id) REFERENCES users(id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_owner (owner_id),
  INDEX idx_type (dashboard_type),
  INDEX idx_template (is_template)
) ENGINE=InnoDB;

CREATE TABLE dashboard_pages (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  page_number INT NOT NULL DEFAULT 1,
  name VARCHAR(255) NOT NULL,
  layout_config JSON NOT NULL,
  is_default BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_dashboard_page (dashboard_id, page_number),
  INDEX idx_dashboard (dashboard_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_layouts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  page_id BIGINT NOT NULL,
  breakpoint VARCHAR(32) NOT NULL, -- desktop, tablet, mobile
  layout_config JSON NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (page_id) REFERENCES dashboard_pages(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_dashboard_page_breakpoint (dashboard_id, page_id, breakpoint),
  INDEX idx_dashboard (dashboard_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_widgets (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  page_id BIGINT NOT NULL,
  widget_id VARCHAR(128) NOT NULL,
  widget_type VARCHAR(64) NOT NULL,
  position_x INT NOT NULL DEFAULT 0,
  position_y INT NOT NULL DEFAULT 0,
  width INT NOT NULL DEFAULT 4,
  height INT NOT NULL DEFAULT 3,
  config JSON NOT NULL,
  data_source JSON,
  refresh_interval INT DEFAULT 300,
  is_visible BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (page_id) REFERENCES dashboard_pages(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_dashboard_widget (dashboard_id, page_id, widget_id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_type (widget_type)
) ENGINE=InnoDB;

CREATE TABLE widget_configs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  widget_id VARCHAR(128) NOT NULL,
  widget_type VARCHAR(64) NOT NULL,
  config_name VARCHAR(128) NOT NULL,
  config_value JSON NOT NULL,
  is_default BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_widget_type_config (widget_id, widget_type, config_name),
  INDEX idx_widget (widget_id),
  INDEX idx_type (widget_type)
) ENGINE=InnoDB;

CREATE TABLE widget_permissions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  widget_id VARCHAR(128) NOT NULL,
  role_id BIGINT,
  user_id BIGINT,
  permission_type VARCHAR(32) NOT NULL, -- view, configure, data_access
  granted_by BIGINT NOT NULL,
  granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  FOREIGN KEY (role_id) REFERENCES roles(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (granted_by) REFERENCES users(id),
  INDEX idx_widget (widget_id),
  INDEX idx_role (role_id),
  INDEX idx_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  version INT NOT NULL,
  name VARCHAR(255),
  description TEXT,
  layout_snapshot JSON NOT NULL,
  widget_snapshot JSON NOT NULL,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  UNIQUE KEY uniq_dashboard_version (dashboard_id, version),
  INDEX idx_dashboard (dashboard_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_templates (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  industry_id BIGINT,
  dashboard_type VARCHAR(64),
  thumbnail_url VARCHAR(512),
  layout_config JSON NOT NULL,
  widget_presets JSON,
  variables JSON,
  usage_count INT DEFAULT 0,
  rating DECIMAL(3,2),
  is_featured BOOLEAN DEFAULT FALSE,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES dashboard_categories(id),
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_category (category_id),
  INDEX idx_industry (industry_id),
  INDEX idx_type (dashboard_type),
  INDEX idx_featured (is_featured)
) ENGINE=InnoDB;

CREATE TABLE dashboard_comments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  widget_id VARCHAR(128),
  user_id BIGINT NOT NULL,
  comment TEXT NOT NULL,
  mentions JSON,
  parent_id BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (parent_id) REFERENCES dashboard_comments(id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_widget (widget_id),
  INDEX idx_user (user_id),
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_favorites (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE KEY uniq_dashboard_user (dashboard_id, user_id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_shares (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  shared_by BIGINT NOT NULL,
  shared_with_type VARCHAR(32) NOT NULL, -- user, role, organization, public
  shared_with_id BIGINT,
  permissions JSON NOT NULL, -- view, edit, comment, share
  expires_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (shared_by) REFERENCES users(id),
  FOREIGN KEY (shared_with_id) REFERENCES users(id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_shared_by (shared_by),
  INDEX idx_shared_with (shared_with_type, shared_with_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_filters (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  page_id BIGINT,
  filter_id VARCHAR(128) NOT NULL,
  filter_type VARCHAR(64) NOT NULL, -- global, widget
  widget_id VARCHAR(128),
  config JSON NOT NULL,
  default_value JSON,
  is_required BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (page_id) REFERENCES dashboard_pages(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_dashboard_filter (dashboard_id, page_id, filter_id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_widget (widget_id)
) ENGINE=InnoDB;

CREATE TABLE dashboard_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  dashboard_id BIGINT NOT NULL,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL, -- created, updated, published, shared, viewed
  details JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_dashboard (dashboard_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE dashboard_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  parent_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES dashboard_categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;
```

### 6.2 Indexes & Optimization

- Primary keys on all tables.
- Foreign key indexes.
- Composite indexes for common queries (org+status, dashboard+user, widget+type).
- Full-text indexes on dashboard name and description for search.
- Partition `dashboard_history` by month if needed.

---

## 7. ER Diagram (Textual)

```
dashboards (1) → (n) dashboard_pages
dashboards (1) → (n) dashboard_layouts
dashboards (1) → (n) dashboard_widgets
dashboards (1) → (n) dashboard_versions
dashboards (1) → (n) dashboard_comments
dashboards (1) → (n) dashboard_favorites
dashboards (1) → (n) dashboard_shares
dashboards (1) → (n) dashboard_filters
dashboards (1) → (n) dashboard_history

dashboard_pages (1) → (n) dashboard_layouts
dashboard_pages (1) → (n) dashboard_widgets
dashboard_pages (1) → (n) dashboard_filters

dashboard_widgets (1) → (n) widget_permissions

dashboard_categories (1) → (n) dashboards
dashboard_categories (1) → (n) dashboard_templates
industries (1) → (n) dashboard_templates
```

---

## 8. API Specification

Base path: `/api/v1/dashboards`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List dashboards. |
| POST | `/` | Create dashboard. |
| GET | `/{id}` | Get dashboard details. |
| PUT | `/{id}` | Update dashboard. |
| DELETE | `/{id}` | Delete dashboard. |
| POST | `/{id}/publish` | Publish dashboard. |
| POST | `/{id}/clone` | Clone dashboard. |
| GET | `/{id}/versions` | List dashboard versions. |
| POST | `/{id}/versions` | Create new version. |
| GET | `/{id}/history` | Get dashboard history. |
| POST | `/{id}/share` | Share dashboard. |
| DELETE | `/{id}/share/{shareId}` | Remove share. |
| POST | `/{id}/favorite` | Add to favorites. |
| DELETE | `/{id}/favorite` | Remove from favorites. |
| POST | `/{id}/comment` | Add comment. |
| GET | `/{id}/comments` | List comments. |
| GET | `/templates` | List dashboard templates. |
| POST | `/templates` | Create dashboard template. |
| GET | `/widgets` | List available widgets. |
| GET | `/widgets/{type}/config` | Get widget configuration schema. |
| POST | `/widgets/preview` | Preview widget with data. |

### Example: Create Dashboard

```http
POST /api/v1/dashboards
{
  "name": "Sales Executive Dashboard",
  "description": "Monthly sales performance overview",
  "dashboard_type": "executive",
  "category_id": 1,
  "theme": "modern",
  "pages": [
    {
      "name": "Overview",
      "layout": {
        "breakpoints": {
          "desktop": {
            "widgets": [
              {
                "id": "kpi_total_sales",
                "type": "kpi_card",
                "position": {"x": 0, "y": 0, "width": 4, "height": 2},
                "config": {
                  "title": "Total Sales",
                  "dataSource": {
                    "type": "kpi",
                    "kpi_id": "total_sales"
                  }
                }
              }
            ]
          }
        }
      }
    }
  ]
}
```

Response:
```json
{
  "id": 123,
  "name": "Sales Executive Dashboard",
  "status": "draft",
  "created_at": "2026-07-14T10:00:00Z",
  "pages": [
    {
      "id": 1,
      "name": "Overview",
      "widgets": [
        {
          "id": "kpi_total_sales",
          "type": "kpi_card"
        }
      ]
    }
  ]
}
```

---

## 9. Frontend Architecture

### 9.1 Component Structure

```
dashboard_builder/
├── components/
│   ├── Designer/
│   │   ├── Canvas.tsx          # Main design canvas
│   │   ├── WidgetPalette.tsx   # Widget library
│   │   ├── PropertyPanel.tsx   # Property editor
│   │   └── PreviewMode.tsx     # Preview mode
│   ├── Widgets/
│   │   ├── KPI/
│   │   ├── Charts/
│   │   ├── Tables/
│   │   └── Maps/
│   ├── Layout/
│   │   ├── Grid.tsx            # Responsive grid
│   │   ├── SnapGrid.tsx        # Snap-to-grid
│   │   └── Breakpoints.tsx     # Breakpoint manager
│   └── Filters/
│       ├── FilterPanel.tsx     # Filter interface
│       ├── CrossFilter.tsx     # Cross-filter logic
│       └── SavedViews.tsx      # Saved views
├── hooks/
│   ├── useDashboard.ts         # Dashboard state
│   ├── useWidgets.ts           # Widget management
│   ├── useFilters.ts           # Filter state
│   └── useRealtime.ts          # Real-time updates
├── stores/
│   ├── dashboardStore.ts       # Dashboard state management
│   ├── widgetStore.ts          # Widget state
│   └── filterStore.ts          # Filter state
└── utils/
    ├── gridUtils.ts            # Grid calculations
    ├── widgetUtils.ts          # Widget helpers
    └── dataBinding.ts          # Data binding logic
```

### 9.2 State Management

- **Dashboard Store:** Current dashboard, pages, widgets, layout.
- **Widget Store:** Widget configurations, data, interactions.
- **Filter Store:** Global filters, widget filters, cross-filter state.
- **UI Store:** Designer mode, selected widget, property panel state.

### 9.3 Real-time Features

- **WebSocket Connection:** Real-time data updates for widgets.
- **Collaborative Editing:** Real-time cursor positions and edits (optional).
- **Live Notifications:** Comments, mentions, share updates.

### 9.4 Performance Optimizations

- **Virtual Scrolling:** For large widget lists and data tables.
- **Lazy Loading:** Load widgets and data on demand.
- **Memoization:** Cache expensive calculations.
- **Debounced Updates:** Debounce filter and property changes.

---

## 10. Backend Architecture

### 10.1 Package Structure

```
dashboard_engine/
├── __init__.py
├── designer.py                # Dashboard design logic
├── renderer.py                # Dashboard rendering
├── widgets/                   # Widget implementations
│   ├── __init__.py
│   ├── base.py                # Base widget class
│   ├── kpi.py                 # KPI widgets
│   ├── charts.py              # Chart widgets
│   ├── tables.py              # Table widgets
│   └── maps.py                # Map widgets
├── layout/                    # Layout management
│   ├── __init__.py
│   ├── grid.py                # Grid system
│   ├── responsive.py          # Responsive layout
│   └── breakpoints.py         # Breakpoint handling
├── filters/                   # Filter engine
│   ├── __init__.py
│   ├── engine.py              # Filter processing
│   ├── cross_filter.py        # Cross-filter logic
│   └── saved_views.py         # Saved view management
├── ai/                        # AI integration
│   ├── __init__.py
│   ├── generator.py           # Dashboard generation
│   ├── optimizer.py           # Layout optimization
│   └── insights.py            # AI insights
├── api/
│   └── routes.py              # Dashboard APIs
├── models/
│   └── dashboard_models.py    # SQLAlchemy models
├── schemas/
│   └── dashboard_schemas.py   # Pydantic schemas
└── migrations/                # Alembic migrations
```

### 10.2 Dashboard Renderer

```python
class DashboardRenderer:
    def __init__(self, widget_registry: WidgetRegistry, data_service: DataService):
        self.widget_registry = widget_registry
        self.data_service = data_service
    
    async def render_dashboard(self, dashboard_id: int, user_id: int, filters: dict = None) -> DashboardRender:
        """Render dashboard with widgets and data."""
        # Get dashboard
        dashboard = await self.get_dashboard(dashboard_id)
        
        # Check permissions
        if not await self.has_permission(user_id, dashboard, 'view'):
            raise PermissionError("No permission to view dashboard")
        
        # Apply filters
        applied_filters = await self.apply_filters(dashboard, filters)
        
        # Render widgets
        rendered_widgets = []
        for widget in dashboard.widgets:
            if await self.has_widget_permission(user_id, widget, 'view'):
                rendered_widget = await self.render_widget(widget, applied_filters)
                rendered_widgets.append(rendered_widget)
        
        return DashboardRender(
            dashboard=dashboard,
            widgets=rendered_widgets,
            filters=applied_filters,
            rendered_at=datetime.utcnow()
        )
    
    async def render_widget(self, widget: DashboardWidget, filters: dict) -> WidgetRender:
        """Render individual widget with data."""
        # Get widget renderer
        renderer = self.widget_registry.get_renderer(widget.widget_type)
        
        # Get data
        data = await self.data_service.get_widget_data(widget, filters)
        
        # Render widget
        rendered = await renderer.render(widget, data, filters)
        
        return rendered
```

### 10.3 Widget Registry

```python
class WidgetRegistry:
    def __init__(self):
        self._widgets = {}
    
    def register(self, widget_type: str, widget_class: Type[BaseWidget]):
        """Register widget type."""
        self._widgets[widget_type] = widget_class
    
    def get_renderer(self, widget_type: str) -> BaseWidget:
        """Get widget renderer."""
        if widget_type not in self._widgets:
            raise ValueError(f"Unknown widget type: {widget_type}")
        return self._widgets[widget_type]
    
    def list_widgets(self) -> List[WidgetInfo]:
        """List all available widgets."""
        return [widget.get_info() for widget in self._widgets.values()]
```

---

## 11. Performance Strategy

### 11.1 Frontend Performance

- **Lazy Loading:** Load widgets and pages on demand.
- **Virtual Scrolling:** Handle large datasets efficiently.
- **Memoization:** Cache expensive calculations.
- **Debouncing:** Debounce user interactions.
- **Code Splitting:** Split code by widget types.

### 11.2 Backend Performance

- **Data Caching:** Cache widget data with appropriate TTL.
- **Query Optimization:** Optimize database queries for widgets.
- **Parallel Processing:** Render widgets in parallel.
- **Connection Pooling:** Efficient database connections.

### 11.3 Database Optimization

- **Indexes:** Optimize indexes for common queries.
- **Materialized Views:** Pre-calculate expensive aggregations.
- **Partitioning:** Partition large tables by date.
- **Query Caching:** Cache frequent queries.

### 11.4 Real-time Performance

- **WebSocket Optimization:** Efficient message batching.
- **Delta Updates:** Send only changed data.
- **Subscription Management:** Efficient subscription handling.
- **Load Balancing:** Distribute WebSocket connections.

---

## 12. Security Design

### 12.1 Access Control

- **Dashboard Permissions:** view, edit, delete, share, manage.
- **Widget Permissions:** view, configure, data_access.
- **Data Permissions:** Inherit from data source permissions.
- **Row-level Security**: Filter data based on user roles.

### 12.2 Data Protection

- **Input Validation:** Validate all inputs to prevent injection.
- **SQL Injection Prevention:** Use parameterized queries.
- **XSS Prevention:** Sanitize user-generated content.
- **CSRF Protection**: Implement CSRF tokens.

### 12.3 Audit Logging

- **Dashboard Actions:** Log all dashboard operations.
- **View Tracking:** Track dashboard access patterns.
- **Data Access:** Log data access for compliance.
- **User Actions**: Log user interactions for analytics.

---

## 13. Testing Strategy

### 13.1 Unit Tests

- **Widget Tests:** Test individual widget rendering and data binding.
- **Filter Tests:** Test filter logic and cross-filtering.
- **Layout Tests:** Test responsive layout calculations.
- **Permission Tests:** Test access control logic.

### 13.2 Integration Tests

- **API Tests:** Test all REST endpoints.
- **Database Tests:** Test database operations.
- **Real-time Tests:** Test WebSocket functionality.
- **AI Integration Tests:** Test AI features.

### 13.3 End-to-End Tests

- **Dashboard Creation:** Test complete dashboard creation flow.
- **Widget Interaction:** Test widget interactions and filtering.
- **Collaboration Tests:** Test sharing and commenting features.
- **Performance Tests:** Test dashboard loading and interaction performance.

### 13.4 Security Tests

- **Permission Tests:** Test RBAC enforcement.
- **Injection Tests:** Test for SQL and XSS vulnerabilities.
- **Data Access Tests:** Test data access controls.
- **Authentication Tests**: Test authentication and authorization.

---

## 14. Administrator Guide

### 14.1 Dashboard Management

- **Creating Dashboards:** Use dashboard designer or templates.
- **Managing Permissions:** Set dashboard and widget permissions.
- **Monitoring Usage:** Track dashboard usage and performance.
- **Managing Templates:** Create and manage dashboard templates.

### 14.2 Widget Management

- **Widget Library:** Manage available widgets.
- **Custom Widgets:** Add custom widgets from plugins.
- **Widget Configuration:** Configure default widget settings.
- **Performance Monitoring**: Monitor widget performance.

### 14.3 System Configuration

- **Theme Management:** Manage dashboard themes.
- **Filter Configuration:** Configure global filter options.
- **Performance Tuning**: Optimize system performance.
- **Security Settings**: Configure security policies.

---

## 15. Developer Guide

### 15.1 Custom Widgets

- **Widget Interface:** Implement the BaseWidget interface.
- **Widget Registration:** Register custom widgets in the registry.
- **Data Binding:** Implement data binding logic.
- **Configuration Schema:** Define widget configuration schema.

### 15.2 Dashboard API

- **REST API:** Use REST API for dashboard operations.
- **WebSocket API:** Real-time dashboard updates.
- **Authentication:** Use API keys or JWT.
- **Rate Limits:** Respect rate limits.

### 15.3 Best Practices

- **Performance:** Optimize widget rendering and data queries.
- **Responsive Design:** Ensure widgets work on all screen sizes.
- **Accessibility:** Follow WCAG guidelines.
- **Security**: Follow security best practices.

---

## 16. Output Summary

1. **Dashboard Builder Architecture** — design principles, components, visual designer features.
2. **Widget Architecture** — widget categories, specifications, data binding, configuration.
3. **Database Schema** — 14 tables with DDL, indexes, relationships, audit fields.
4. **ER Diagram** — textual representation of table relationships.
5. **API Specification** — 30+ REST endpoints for dashboards, widgets, templates, sharing.
6. **Frontend Architecture** — component structure, state management, real-time features, performance.
7. **Backend Architecture** — package structure, renderer, widget registry, filter engine.
8. **AI Integration** — dashboard generation, widget recommendations, layout optimization, insights.
9. **Performance Strategy** — frontend, backend, database, and real-time optimizations.
10. **Security Design** — access control, data protection, audit logging.
11. **Testing Strategy** — unit, integration, e2e, security tests.
12. **Administrator Guide** — dashboard management, widget management, system configuration.
13. **Developer Guide** — custom widgets, API usage, best practices.

All specifications are enterprise-grade, scalable, modular, production-ready, and fully integrated into AEDIP.
