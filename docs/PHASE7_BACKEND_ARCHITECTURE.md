# Phase 7 — Executive Decision Center (Part 2)
# Database + Backend + API Architecture

## 1. Complete Database Architecture

### Design Principles
- **Reuse existing tables** whenever possible: `users`, `organizations`, `departments`, `roles`, `permissions`, `sales`, `etl_jobs`, `ai_*`, reports.
- **New tables only for Decision Center-specific concepts**.
- Every new table includes `id`, `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`.
- Soft deletes via `deleted_at`.
- Foreign keys enforce referential integrity; cascades only for `organizations` and `users`.
- JSON columns store flexible widget, forecast, and rule configuration.
- Indexes optimize multi-tenant queries: `organization_id`, `department_id`, `user_id`, `created_at`, `status`.

### New Tables

| Table | Purpose |
|-------|---------|
| `decision_center_preferences` | Per-user Decision Center settings |
| `executive_widgets` | Catalog of available widgets |
| `dashboard_layouts` | User/role/department layouts |
| `dashboard_favorites` | Favorite widgets by user |
| `dashboard_filters` | Saved filter state |
| `organization_health_scores` | Latest computed health score |
| `organization_health_history` | Historical health scores |
| `decision_feed` | Aggregated activity feed |
| `decision_feed_events` | Feed event definitions |
| `recommendations` | AI-generated recommendations |
| `recommendation_actions` | Recommendation lifecycle |
| `forecast_results` | Stored forecasts |
| `forecast_models` | Forecast configuration |
| `executive_alerts` | Active and resolved alerts |
| `alert_rules` | Alert generation rules |
| `alert_history` | Alert state changes |
| `kpi_catalog` | Master list of KPIs |
| `kpi_values` | Time-series KPI values |
| `kpi_targets` | KPI targets by period |
| `kpi_thresholds` | Warning/critical thresholds |
| `department_scores` | Latest department health |
| `department_summary` | Department KPI snapshot |
| `scheduled_reports` | Report schedule |
| `generated_reports` | Report instances |
| `report_templates` | Reusable report templates |
| `daily_briefings` | Generated briefings |
| `briefing_history` | Briefing feedback/history |
| `notification_preferences` | Per-user notification settings |
| `announcement_center` | System announcements |
| `quick_actions` | Available quick actions |
| `user_shortcuts` | User-defined shortcuts |
| `saved_views` | Saved filter/view configurations |
| `widget_permissions` | Widget-level RBAC |
| `dashboard_permissions` | Layout-level RBAC |
| `executive_activity_logs` | Decision Center audit trail |
| `decision_logs` | Decision rationale |
| `approval_queue` | Pending approvals |
| `approval_history` | Approval lifecycle |
| `meeting_briefings` | Briefings for meetings |
| `organization_metrics` | Organization-level metrics |
| `benchmark_metrics`, `benchmark_groups`, `benchmark_results` | Benchmarking |

### DDL (MySQL 8.0)

```sql
CREATE TABLE decision_center_preferences (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    default_landing TINYINT(1) DEFAULT 1,
    preferred_date_range VARCHAR(20) DEFAULT 'this_month',
    default_department_id BIGINT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_settings JSON,
    widget_order JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_user_org (user_id, organization_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE executive_widgets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    widget_key VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description VARCHAR(512),
    category VARCHAR(64) NOT NULL,
    default_position INT DEFAULT 0,
    default_width INT DEFAULT 6,
    default_height INT DEFAULT 4,
    config_schema JSON,
    data_sources JSON,
    is_system TINYINT(1) DEFAULT 0,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_widget_key_org (widget_key, organization_id),
    INDEX idx_organization (organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE dashboard_layouts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    role_id BIGINT NULL,
    department_id BIGINT NULL,
    layout_name VARCHAR(128) DEFAULT 'Default',
    is_default TINYINT(1) DEFAULT 0,
    layout_config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_user (organization_id, user_id),
    INDEX idx_org_role (organization_id, role_id),
    INDEX idx_org_dept (organization_id, department_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE dashboard_favorites (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    widget_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_user_widget (user_id, widget_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (widget_id) REFERENCES executive_widgets(id) ON DELETE CASCADE
);

CREATE TABLE dashboard_filters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    filter_name VARCHAR(128) NOT NULL,
    filter_config JSON NOT NULL,
    is_default TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_user_org (user_id, organization_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE organization_health_scores (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    data_quality_score DECIMAL(5,2) NOT NULL,
    reporting_score DECIMAL(5,2) NOT NULL,
    security_score DECIMAL(5,2) NOT NULL,
    automation_score DECIMAL(5,2) NOT NULL,
    user_activity_score DECIMAL(5,2) NOT NULL,
    system_performance_score DECIMAL(5,2) NOT NULL,
    kpi_performance_score DECIMAL(5,2) NOT NULL,
    compliance_score DECIMAL(5,2) NOT NULL,
    score_breakdown JSON,
    recommendations JSON,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_calculated_at (calculated_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE organization_health_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    category_scores JSON NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_calc (organization_id, calculated_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE decision_feed (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    user_id BIGINT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_source VARCHAR(64) NOT NULL,
    source_id BIGINT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    severity VARCHAR(16) DEFAULT 'info',
    status VARCHAR(32) DEFAULT 'new',
    action_url VARCHAR(512),
    metadata JSON,
    is_read TINYINT(1) DEFAULT 0,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_time (organization_id, created_at),
    INDEX idx_user (user_id),
    INDEX idx_dept (department_id),
    INDEX idx_type (event_type),
    INDEX idx_status (status),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE TABLE decision_feed_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    event_key VARCHAR(64) NOT NULL,
    event_name VARCHAR(128) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    default_severity VARCHAR(16) DEFAULT 'info',
    default_template TEXT,
    is_system TINYINT(1) DEFAULT 1,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_event_key_org (event_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE recommendations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    kpi_id BIGINT NULL,
    generated_by_user_id BIGINT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    rationale TEXT,
    expected_benefit TEXT,
    estimated_impact VARCHAR(64),
    value_rank VARCHAR(16) DEFAULT 'medium',
    category VARCHAR(64),
    status VARCHAR(32) DEFAULT 'new',
    recommended_owner_id BIGINT NULL,
    assigned_owner_id BIGINT NULL,
    due_date DATE NULL,
    evidence JSON,
    ai_confidence DECIMAL(4,3) NULL,
    accepted_at TIMESTAMP NULL,
    rejected_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_status (organization_id, status),
    INDEX idx_org_rank (organization_id, value_rank),
    INDEX idx_department (department_id),
    INDEX idx_owner (assigned_owner_id),
    INDEX idx_due_date (due_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE recommendation_actions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    recommendation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action VARCHAR(32) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE forecast_models (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    kpi_id BIGINT NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    model_type VARCHAR(32) NOT NULL,
    parameters JSON,
    is_active TINYINT(1) DEFAULT 1,
    last_trained_at TIMESTAMP NULL,
    accuracy_score DECIMAL(5,4) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_org_kpi_model (organization_id, kpi_id, model_name),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE forecast_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    kpi_id BIGINT NOT NULL,
    model_id BIGINT NULL,
    forecast_date DATE NOT NULL,
    horizon_days INT NOT NULL,
    forecast_value DECIMAL(18,4) NOT NULL,
    lower_bound DECIMAL(18,4) NULL,
    upper_bound DECIMAL(18,4) NULL,
    confidence_level DECIMAL(4,3) DEFAULT 0.95,
    trend_direction VARCHAR(16),
    risks JSON,
    opportunities JSON,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_kpi_date (organization_id, kpi_id, forecast_date),
    INDEX idx_horizon (horizon_days),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE kpi_catalog (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    kpi_key VARCHAR(64) NOT NULL,
    kpi_name VARCHAR(128) NOT NULL,
    description VARCHAR(512),
    category VARCHAR(64) NOT NULL,
    industry VARCHAR(64) DEFAULT 'general',
    unit VARCHAR(32),
    formula TEXT,
    data_source VARCHAR(128),
    is_system TINYINT(1) DEFAULT 0,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_kpi_key_org (kpi_key, organization_id),
    INDEX idx_category (category),
    INDEX idx_industry (industry),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE kpi_values (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(16) NOT NULL,
    actual_value DECIMAL(18,4) NOT NULL,
    target_value DECIMAL(18,4) NULL,
    variance DECIMAL(18,4) NULL,
    variance_percent DECIMAL(8,4) NULL,
    status VARCHAR(16) DEFAULT 'on_track',
    calculation_method VARCHAR(32),
    source_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_kpi_period (kpi_id, period_start),
    INDEX idx_org_dept_period (organization_id, department_id, period_start),
    FOREIGN KEY (kpi_id) REFERENCES kpi_catalog(id) ON DELETE CASCADE
);

CREATE TABLE kpi_targets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    target_value DECIMAL(18,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_kpi_target (kpi_id, organization_id, department_id, period_start, period_end),
    FOREIGN KEY (kpi_id) REFERENCES kpi_catalog(id) ON DELETE CASCADE
);

CREATE TABLE kpi_thresholds (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    warning_threshold DECIMAL(18,4) NULL,
    critical_threshold DECIMAL(18,4) NULL,
    comparison_type VARCHAR(16) DEFAULT 'lower_is_worse',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_kpi_threshold (kpi_id, organization_id, department_id),
    FOREIGN KEY (kpi_id) REFERENCES kpi_catalog(id) ON DELETE CASCADE
);

CREATE TABLE executive_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    rule_id BIGINT NULL,
    kpi_id BIGINT NULL,
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    impact TEXT,
    recommended_action TEXT,
    owner_id BIGINT NULL,
    due_date DATE NULL,
    status VARCHAR(32) DEFAULT 'new',
    resolved_at TIMESTAMP NULL,
    resolved_by BIGINT NULL,
    resolution_note TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_status (organization_id, status),
    INDEX idx_org_severity (organization_id, severity),
    INDEX idx_owner (owner_id),
    INDEX idx_due_date (due_date),
    INDEX idx_created (created_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE alert_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    kpi_id BIGINT NULL,
    rule_name VARCHAR(128) NOT NULL,
    rule_type VARCHAR(32) NOT NULL,
    condition_config JSON NOT NULL,
    severity VARCHAR(16) NOT NULL,
    message_template TEXT,
    is_active TINYINT(1) DEFAULT 1,
    cooldown_minutes INT DEFAULT 60,
    last_triggered_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_department (department_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE alert_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    from_status VARCHAR(32),
    to_status VARCHAR(32),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL,
    FOREIGN KEY (alert_id) REFERENCES executive_alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE department_scores (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    category_scores JSON,
    recommendations JSON,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_dept_calc (department_id, calculated_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE department_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NOT NULL,
    summary_date DATE NOT NULL,
    status VARCHAR(32) DEFAULT 'on_track',
    health_score DECIMAL(5,2) NULL,
    top_kpis JSON,
    top_recommendations JSON,
    alerts_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_dept_date (department_id, summary_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE report_templates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    template_key VARCHAR(64) NOT NULL,
    template_name VARCHAR(128) NOT NULL,
    description VARCHAR(512),
    report_type VARCHAR(64) NOT NULL,
    frequency VARCHAR(32) NOT NULL,
    template_config JSON,
    required_permissions JSON,
    is_system TINYINT(1) DEFAULT 0,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_template_key_org (template_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE scheduled_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    template_id BIGINT NOT NULL,
    report_name VARCHAR(128) NOT NULL,
    owner_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    schedule_config JSON NOT NULL,
    parameters JSON,
    recipients JSON,
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_next_run (next_run_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE
);

CREATE TABLE generated_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    scheduled_report_id BIGINT NULL,
    template_id BIGINT NOT NULL,
    report_name VARCHAR(128) NOT NULL,
    generated_by BIGINT NOT NULL,
    report_format VARCHAR(16) DEFAULT 'pdf',
    file_path VARCHAR(512),
    file_size BIGINT,
    parameters JSON,
    status VARCHAR(32) DEFAULT 'pending',
    error_message TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_generated (generated_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE daily_briefings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    department_id BIGINT NULL,
    briefing_date DATE NOT NULL,
    summary TEXT,
    bullets JSON,
    data_sources JSON,
    ai_model VARCHAR(64),
    ai_provider VARCHAR(64),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_briefing (organization_id, user_id, department_id, briefing_date),
    INDEX idx_org_date (organization_id, briefing_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE briefing_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    briefing_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action VARCHAR(32) NOT NULL,
    feedback_score INT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (briefing_id) REFERENCES daily_briefings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE notification_preferences (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    channel VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_user_pref (user_id, organization_id, channel, event_type),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE announcement_center (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    priority VARCHAR(16) DEFAULT 'normal',
    target_roles JSON,
    target_departments JSON,
    published_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_active (organization_id, is_active),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE quick_actions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    action_key VARCHAR(64) NOT NULL,
    action_name VARCHAR(128) NOT NULL,
    description VARCHAR(256),
    icon VARCHAR(64),
    target_url VARCHAR(512),
    required_permissions JSON,
    display_order INT DEFAULT 0,
    is_system TINYINT(1) DEFAULT 0,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_action_key_org (action_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE user_shortcuts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    shortcut_name VARCHAR(128) NOT NULL,
    target_url VARCHAR(512) NOT NULL,
    icon VARCHAR(64),
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE saved_views (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    view_name VARCHAR(128) NOT NULL,
    view_type VARCHAR(64) NOT NULL,
    filter_config JSON,
    is_default TINYINT(1) DEFAULT 0,
    is_shared TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_user_org (user_id, organization_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE widget_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    widget_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    can_view TINYINT(1) DEFAULT 1,
    can_configure TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_widget_role (widget_id, role_id),
    FOREIGN KEY (widget_id) REFERENCES executive_widgets(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE dashboard_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    layout_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    can_view TINYINT(1) DEFAULT 1,
    can_edit TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_layout_role (layout_id, role_id),
    FOREIGN KEY (layout_id) REFERENCES dashboard_layouts(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE executive_activity_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id BIGINT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NULL,
    INDEX idx_org_time (organization_id, created_at),
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE decision_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    decision_title VARCHAR(256) NOT NULL,
    context JSON,
    rationale TEXT,
    expected_outcome TEXT,
    actual_outcome TEXT,
    related_alert_id BIGINT NULL,
    related_recommendation_id BIGINT NULL,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_time (organization_id, decided_at),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE approval_queue (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    department_id BIGINT NULL,
    requester_id BIGINT NOT NULL,
    approver_id BIGINT NULL,
    approval_type VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id BIGINT NOT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    due_date DATE NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_status (organization_id, status),
    INDEX idx_approver (approver_id),
    INDEX idx_requester (requester_id),
    INDEX idx_due_date (due_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE approval_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    approval_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action VARCHAR(32) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approval_id) REFERENCES approval_queue(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE meeting_briefings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    meeting_title VARCHAR(256) NOT NULL,
    meeting_date DATE NOT NULL,
    attendees JSON,
    agenda_items JSON,
    briefing_content JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_org_date (organization_id, meeting_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE organization_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    metric_date DATE NOT NULL,
    metric_type VARCHAR(64) NOT NULL,
    metric_value DECIMAL(18,4) NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_org_metric_date (organization_id, metric_type, metric_date),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE benchmark_groups (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT NULL,
    group_name VARCHAR(128) NOT NULL,
    group_description VARCHAR(512),
    industry VARCHAR(64),
    is_system TINYINT(1) DEFAULT 0,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE benchmark_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    organization_id BIGINT NULL,
    metric_key VARCHAR(64) NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    unit VARCHAR(32),
    formula TEXT,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    UNIQUE KEY uk_metric_group (group_id, metric_key),
    FOREIGN KEY (group_id) REFERENCES benchmark_groups(id) ON DELETE CASCADE
);

CREATE TABLE benchmark_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    benchmark_metric_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    benchmark_value DECIMAL(18,4) NOT NULL,
    actual_value DECIMAL(18,4) NOT NULL,
    variance_percent DECIMAL(8,4) NULL,
    benchmark_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NULL, updated_by BIGINT NULL, deleted_at TIMESTAMP NULL,
    INDEX idx_metric_date (benchmark_metric_id, benchmark_date),
    FOREIGN KEY (benchmark_metric_id) REFERENCES benchmark_metrics(id) ON DELETE CASCADE
);
```

---

## 2. ERD

### Core Relationships

```
organizations
├── decision_center_preferences
├── executive_widgets
├── dashboard_layouts
├── organization_health_scores
├── organization_health_history
├── decision_feed
├── decision_feed_events
├── recommendations
├── forecast_models
├── forecast_results
├── kpi_catalog
├── executive_alerts
├── alert_rules
├── department_scores
├── department_summary
├── report_templates
├── scheduled_reports
├── generated_reports
├── daily_briefings
├── notification_preferences
├── announcement_center
├── quick_actions
├── user_shortcuts (per user)
├── saved_views (per user)
├── executive_activity_logs
├── decision_logs
├── approval_queue
├── meeting_briefings
├── organization_metrics
├── benchmark_groups
└── benchmark_results

users
├── decision_center_preferences
├── dashboard_layouts
├── dashboard_favorites
├── saved_views
├── recommendations (owner)
├── executive_alerts (owner, resolver)
├── approval_queue (requester, approver)
├── executive_activity_logs
├── decision_logs
├── meeting_briefings
└── user_shortcuts

roles
├── dashboard_layouts
├── widget_permissions
└── dashboard_permissions

departments
├── dashboard_layouts
├── decision_feed
├── recommendations
├── forecast_results
├── kpi_values / targets / thresholds
├── executive_alerts
├── alert_rules
├── department_scores
├── department_summary
└── approval_queue

kpi_catalog
├── recommendations
├── forecast_models
├── forecast_results
├── kpi_values
├── kpi_targets
├── kpi_thresholds
├── executive_alerts
└── alert_rules

executive_widgets
├── dashboard_favorites
└── widget_permissions

dashboard_layouts
└── dashboard_permissions

executive_alerts
└── alert_history

recommendations
└── recommendation_actions

scheduled_reports
└── generated_reports

daily_briefings
└── briefing_history

approval_queue
└── approval_history

benchmark_groups
└── benchmark_metrics
└── benchmark_results
```

---

## 3. API Specification

### Base & Conventions
- Base path: `/api/v1/decision-center`
- All endpoints return JSON with envelope:
  ```json
  { "success": true, "data": {}, "meta": { "page": 1, "limit": 20, "total": 0 }, "error": null }
  ```
- Authentication: JWT Bearer token.
- Context headers: `X-Organization-ID`, `X-Department-ID`.
- Query params: `page`, `limit`, `sort`, `order`, `q` (search), `from`, `to`, `type`, `status`, `severity`.

### Endpoints

#### Overview
- `GET /api/v1/decision-center` — Full Decision Center payload.
- `GET /api/v1/decision-center/preferences` — User preferences.
- `PUT /api/v1/decision-center/preferences` — Update preferences.

#### Decision Feed
- `GET /api/v1/decision-feed` — List feed items.
- `POST /api/v1/decision-feed/{id}/read` — Mark read.
- `POST /api/v1/decision-feed/{id}/dismiss` — Dismiss.
- `GET /api/v1/decision-feed/events` — Event definitions.

#### Health Score
- `GET /api/v1/organization-health` — Latest score.
- `GET /api/v1/organization-health/history` — Historical scores.
- `GET /api/v1/organization-health/categories` — Category breakdown.
- `POST /api/v1/organization-health/recalculate` — Trigger recalculation.

#### Executive KPIs
- `GET /api/v1/executive-kpis` — List KPIs.
- `GET /api/v1/executive-kpis/{id}` — Detail.
- `GET /api/v1/executive-kpis/{id}/values` — Time series.
- `POST /api/v1/executive-kpis` — Create custom KPI.
- `PUT /api/v1/executive-kpis/{id}` — Update.
- `DELETE /api/v1/executive-kpis/{id}` — Soft delete.
- `POST /api/v1/executive-kpis/{id}/target` — Set target.
- `POST /api/v1/executive-kpis/{id}/threshold` — Set threshold.

#### Alerts
- `GET /api/v1/alerts` — List.
- `GET /api/v1/alerts/{id}` — Detail.
- `POST /api/v1/alerts/{id}/assign` — Assign owner.
- `POST /api/v1/alerts/{id}/resolve` — Resolve.
- `POST /api/v1/alerts/{id}/dismiss` — Dismiss.
- `GET /api/v1/alerts/rules` — Rules.
- `POST /api/v1/alerts/rules` — Create rule.
- `PUT /api/v1/alerts/rules/{id}` — Update rule.
- `DELETE /api/v1/alerts/rules/{id}` — Delete rule.

#### Forecast
- `GET /api/v1/forecast` — Summary.
- `GET /api/v1/forecast/{kpi_id}` — KPI forecast.
- `POST /api/v1/forecast/{kpi_id}` — Generate.
- `GET /api/v1/forecast/models` — Models.
- `POST /api/v1/forecast/models` — Create model.

#### Recommendations
- `GET /api/v1/recommendations` — List.
- `GET /api/v1/recommendations/{id}` — Detail.
- `POST /api/v1/recommendations/{id}/accept` — Accept.
- `POST /api/v1/recommendations/{id}/reject` — Reject.
- `POST /api/v1/recommendations/{id}/assign` — Assign.
- `POST /api/v1/recommendations/{id}/complete` — Complete.
- `POST /api/v1/recommendations/generate` — Trigger AI generation.

#### Daily Briefing
- `GET /api/v1/daily-briefing` — Today’s briefing.
- `POST /api/v1/daily-briefing/generate` — Generate.
- `POST /api/v1/daily-briefing/{id}/feedback` — Feedback.
- `GET /api/v1/daily-briefing/history` — History.

#### Department Summary
- `GET /api/v1/department-summary` — All departments.
- `GET /api/v1/department-summary/{id}` — Single department.
- `GET /api/v1/department-summary/{id}/kpis` — KPIs.
- `GET /api/v1/department-summary/{id}/alerts` — Alerts.
- `GET /api/v1/department-summary/{id}/recommendations` — Recommendations.

#### Reports
- `GET /api/v1/scheduled-reports` — Schedules.
- `POST /api/v1/scheduled-reports` — Create.
- `PUT /api/v1/scheduled-reports/{id}` — Update.
- `DELETE /api/v1/scheduled-reports/{id}` — Delete.
- `POST /api/v1/scheduled-reports/{id}/run` — Run now.
- `GET /api/v1/generated-reports` — Generated reports.
- `GET /api/v1/generated-reports/{id}/download` — Download.

#### Layout & Widgets
- `GET /api/v1/dashboard-layout` — Get layout.
- `POST /api/v1/dashboard-layout` — Save layout.
- `PUT /api/v1/dashboard-layout/{id}` — Update.
- `GET /api/v1/widgets` — Available widgets.
- `POST /api/v1/favorite-widget` — Favorite.
- `DELETE /api/v1/favorite-widget/{id}` — Remove favorite.
- `POST /api/v1/saved-view` — Save view.
- `GET /api/v1/saved-view` — List views.
- `DELETE /api/v1/saved-view/{id}` — Delete view.

#### Actions & Approvals
- `GET /api/v1/quick-actions` — Available actions.
- `POST /api/v1/quick-action` — Execute.
- `GET /api/v1/approvals` — Queue.
- `POST /api/v1/approvals/{id}/approve` — Approve.
- `POST /api/v1/approvals/{id}/reject` — Reject.
- `POST /api/v1/approvals/{id}/delegate` — Delegate.

#### Notifications & Search
- `GET /api/v1/notifications` — Notifications.
- `POST /api/v1/notifications/{id}/read` — Mark read.
- `PUT /api/v1/notification-preferences` — Preferences.
- `GET /api/v1/announcements` — Announcements.
- `GET /api/v1/search?q=...&type=...` — Global search.

#### Real-Time
- WebSocket: `/api/v1/ws/decision-center`
- SSE: `/api/v1/sse/notifications`

---

## 4. Backend Service Architecture

### Package Structure
```
decision_center/
├── __init__.py
├── routes.py              # FastAPI router
├── schemas.py             # Pydantic request/response
├── config.py              # Decision Center settings
├── service.py             # Main orchestrator
├── health_score.py        # Health Score Calculator
├── briefing.py            # Daily Briefing Generator
├── alerts.py              # Alert Service
├── recommendations.py     # Recommendation Service
├── forecast.py            # Forecast Service
├── feed.py                # Decision Feed Service
├── kpis.py                # KPI Resolver
├── departments.py         # Department Summary Service
├── reports.py             # Scheduled Report Service
├── layouts.py             # Dashboard Layout Service
├── widgets.py             # Widget Catalog Service
├── approvals.py           # Approval Queue Service
├── notifications.py       # Notification Service
├── analytics.py           # Executive Analytics
├── benchmarks.py          # Benchmark Service
├── permissions.py         # DC RBAC helpers
├── cache.py               # Cache key helpers
├── tasks.py               # Celery background tasks
└── realtime.py            # WebSocket/SSE manager
```

### Service Responsibilities
- **DecisionCenterService** — Aggregates all sub-services into one payload; applies context filters and caching.
- **HealthScoreService** — Computes category and overall scores; stores latest and historical snapshots.
- **DailyBriefingService** — Generates plain-English briefings using AI engines.
- **AlertService** — Evaluates alert rules, creates alerts, manages lifecycle.
- **RecommendationService** — Ranks and manages AI recommendations.
- **ForecastService** — Runs forecasts, selects best model, returns risks/opportunities.
- **DecisionFeedService** — Aggregates and normalizes events from all modules.
- **KpiService** — Resolves industry-specific KPIs and computes values.
- **DepartmentService** — Computes department health and summaries.
- **ReportService** — Manages templates, schedules, and generated reports.
- **LayoutService / WidgetService** — Serves layouts and widget catalog.
- **ApprovalService / NotificationService** — Approval queue and notifications.
- **AnalyticsService / BenchmarkService** — Activity analytics and benchmarks.

---

## 5. Background Worker Architecture

### Worker Platform
- **Celery** with Redis broker/result backend for heavy tasks.
- **APScheduler** for simple scheduled tasks (existing `scheduler/`).

### Task Definitions
| Task | Schedule | Function |
|------|----------|----------|
| Generate daily briefing | Daily 06:00 | `tasks.generate_daily_briefing` |
| Calculate health score | Hourly | `tasks.calculate_health_score` |
| Refresh forecasts | Daily 02:00 | `tasks.refresh_forecasts` |
| Calculate benchmarks | Weekly Sunday | `tasks.calculate_benchmarks` |
| Refresh KPI values | Hourly | `tasks.refresh_kpi_values` |
| Detect alerts | Every 15 min | `tasks.detect_alerts` |
| Generate recommendations | Every 6 hours | `tasks.generate_recommendations` |
| Refresh dashboard cache | Every 30 min | `tasks.refresh_dashboard_cache` |
| Generate report | Per schedule | `tasks.generate_report` |
| Cleanup old data | Daily 01:00 | `tasks.cleanup_old_data` |

### Queues
- `decision_center.high` — health, alerts, briefing.
- `decision_center.normal` — KPIs, forecasts, recommendations.
- `decision_center.low` — cleanup, analytics, benchmarks.

### Idempotency
- Tasks keyed by `(organization_id, entity_id, date)`.
- Updates existing rows to prevent duplicates.

---

## 6. Notification Architecture

### Channels
- In-app notifications via `decision_feed` and `announcement_center`.
- Email via existing email service.
- SMS via existing gateway.
- WebSocket/SSE push.

### Events
- Alert assigned / due.
- Recommendation accepted / completed.
- Approval pending.
- Report generated.
- Daily briefing ready.
- Health score significant change.
- System announcement.

### Flow
1. Service publishes event to Redis Pub/Sub or Celery.
2. Notification worker reads user preferences.
3. Delivers via selected channels.
4. Logs delivery in `executive_activity_logs`.

---

## 7. Real-Time Architecture

### WebSocket
- Endpoint: `/api/v1/ws/decision-center`
- JWT validation on connect.
- Client joins organization-specific room.
- Push events: new alert, KPI update, feed item, approval update, briefing ready.

### Server-Sent Events
- Endpoint: `/api/v1/sse/notifications`
- Lightweight fallback.
- Streams notification events.

### Event Sources
- Background tasks publish to Redis.
- WebSocket manager broadcasts to connected clients.
- Service layer publishes for immediate actions.

---

## 8. Security Design

### Authentication
- JWT Bearer tokens from existing auth.
- WebSocket/SSE token validation.
- Short-lived tokens; refresh via existing endpoint.

### Authorization
- RBAC permissions:
  - `decision_center.read`, `decision_center.write`, `decision_center.configure`, `decision_center.admin`
  - `widget.{key}.read`, `widget.{key}.configure`
  - `kpi.{key}.read`
  - `alerts.manage`, `recommendations.manage`, `reports.manage`
- Fine-grained `widget_permissions` and `dashboard_permissions`.
- Every endpoint checks permissions via existing dependencies.

### Input Validation
- Pydantic schemas for all bodies.
- Query params sanitized; `limit` capped at 100.
- SQLAlchemy ORM prevents SQL injection.
- JSON configs validated against JSON Schema.

### Data Protection
- Secrets in existing secure config / `ai_provider_configs`.
- Sensitive fields excluded from responses.
- Every action audited in `executive_activity_logs`.
- TLS in transit; TDE at rest.

### Rate Limiting
- Read: 1000/hour per user.
- Write: 100/hour per user.
- AI generation: 50/hour per user.
- Burst: 20/second per IP.

---

## 9. Performance Strategy

### Redis Caching
| Key | TTL | Content |
|-----|-----|---------|
| `dc:health:{org_id}` | 1h | Health score |
| `dc:briefing:{org_id}:{user_id}:{date}` | 24h | Daily briefing |
| `dc:kpis:{org_id}:{dept_id}` | 1h | Executive KPIs |
| `dc:alerts:{org_id}:{status}` | 15m | Alerts |
| `dc:feed:{org_id}:{user_id}` | 1m | Decision feed |
| `dc:forecast:{org_id}:{kpi_id}` | 24h | Forecast |
| `dc:layout:{user_id}:{role_id}` | 1h | Dashboard layout |
| `dc:widgets:{org_id}` | 24h | Widget catalog |

### Database Optimization
- Indexes on `organization_id`, `department_id`, `user_id`, `status`, `created_at`, `period_start`.
- Partition `kpi_values`, `forecast_results`, `decision_feed`, `executive_activity_logs` by `organization_id` or date.
- Read replicas for analytics queries.
- Connection pooling.

### Query Optimization
- Pre-aggregate health scores, department summaries, KPI values.
- Background workers populate materialized summary tables.
- Use `selectinload` or explicit joins; avoid N+1.

### Scalability
- Stateless FastAPI servers behind load balancer.
- Redis cluster for cache and pub/sub.
- Celery workers scaled independently.
- Database read replicas and sharding when needed.

---

## 10. Testing Strategy

### Unit Tests
- `tests/decision_center/test_health_score.py` — scoring logic.
- `tests/decision_center/test_briefing.py` — briefing generation.
- `tests/decision_center/test_alerts.py` — rule evaluation.
- `tests/decision_center/test_kpis.py` — KPI computation.
- `tests/decision_center/test_recommendations.py` — ranking/lifecycle.

### Integration Tests
- `tests/decision_center/test_services.py` — service orchestration.
- `tests/decision_center/test_background_tasks.py` — Celery tasks.
- `tests/decision_center/test_realtime.py` — WebSocket/SSE events.

### API Tests
- `tests/decision_center/test_api.py` — all REST endpoints.
- Validate pagination, filtering, sorting, standard envelope.

### Permission Tests
- `tests/decision_center/test_permissions.py` — widget, KPI, layout, alert permissions.
- Verify unauthorized access is rejected.

### Load Tests
- `tests/decision_center/load/test_decision_center.py` — k6 or Locust.
- Target: 1,000 concurrent users, 95th percentile under 500ms.

### Performance Tests
- Benchmark health score and KPI refresh under 1M rows.
- Forecast generation under 100K time-series points.

### Continuous Integration
- Add `decision_center` tests to existing CI (`pytest tests/decision_center`).
- Coverage target: 85%.

---

## Integration with Existing AEDIP

The Executive Decision Center extends existing phases without redesign:
- **Phase 3 (Auth/RBAC)**: reuses JWT, `users`, `roles`, `permissions`, `get_current_user`, `require_permissions`.
- **Phase 4 (ETL)**: consumes `etl_jobs`, `pipeline_runs`, `etl_quality_results`.
- **Phase 5 (Dashboard)**: reuses data service patterns and extends widgets.
- **Phase 6 (AI)**: consumes `ai_insights`, `ai_forecasts`, `ai_anomaly_alerts`, `ai_kpi_recommendations`, `ai_report_generations`, `AIGateway`.

### Implementation Files (Part 3)
- `decision_center/` package.
- `api/main.py` — register Decision Center router and system widgets.
- `database/db_setup.py` — import Decision Center models.
- `tests/conftest.py` — import Decision Center models.
- `alembic/versions/0004_phase7_decision_center.py` — migration.
- `frontend/app/decision-center/page.tsx` and components.
- Update `requirements.txt` for Celery/Redis/WebSocket if not present.

No existing feature will be redesigned, removed, or replaced.
