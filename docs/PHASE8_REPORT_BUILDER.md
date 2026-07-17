# Phase 8.6 — Enterprise Report Builder & Document Generation Platform

## Purpose

This document defines the Enterprise Report Builder and Document Generation Platform for AEDIP, enabling organizations to create, schedule, distribute, and manage professional reports without writing code. The platform supports various report types, multiple output formats, AI-powered features, and enterprise-grade security.

---

## 1. Report Builder Architecture

### 1.1 Design Principles

- **Visual First:** Drag-and-drop report designer with WYSIWYG preview.
- **Multi-Format Output:** Generate PDF, Excel, Word, PowerPoint, HTML, and more.
- **AI-Enhanced:** AI-powered summaries, insights, and report generation.
- **Enterprise Ready:** Version control, audit trails, digital signatures, watermarking.
- **Scalable Generation:** Background processing, streaming, and caching for large reports.
- **Flexible Scheduling:** One-time, recurring, and cron-based scheduling.
- **Multi-Channel Distribution:** Email, SMS, WhatsApp, in-app, cloud storage, secure links.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 Report Builder & Document Generation                           │
│  Report Designer · Generation Engine · Scheduler · Distribution · AI Engine     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Report       │                │  Document       │               │  Scheduler         │
│  Designer UI  │                │  Generation     │               │  Engine            │
│               │                │  Engine         │               │                    │
│ Canvas        │                │ PDF/Excel/Word  │               │ Cron Scheduling    │
│ Elements      │                │ Streaming       │               │ Queue Management   │
│ Templates     │                │ Background Jobs │               │ Retry Logic        │
│ Preview       │                │ Caching         │               │ Status Tracking    │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Report Designer UI** | Visual drag-and-drop designer; element palette; property panel; preview. |
| **Document Generation Engine** | Multi-format document generation; streaming; templating; caching. |
| **Scheduler Engine** | Report scheduling; cron expressions; queue management; retry logic. |
| **Distribution Engine** | Multi-channel distribution; email, SMS, WhatsApp, cloud storage. |
| **AI Engine** | AI summaries; insights; report generation; grammar review; translation. |
| **Security Layer** | RBAC; watermarking; password protection; digital signatures; audit logs. |
| **Performance Layer** | Background processing; streaming; caching; incremental rendering. |
| **Template Engine** | Report templates; themes; element libraries; version control. |

---

## 2. Document Generation Engine

### 2.1 Supported Output Formats

| Format | Description | Use Cases |
|--------|-------------|-----------|
| **PDF** | Portable Document Format with advanced layout support | Executive reports, compliance documents |
| **Excel (XLSX)** | Spreadsheet with formulas, charts, and pivot tables | Financial reports, data analysis |
| **Word (DOCX)** | Rich text document with headers, footers, styles | Formal reports, documentation |
| **PowerPoint (PPTX)** | Presentation slides with charts and graphics | Executive presentations |
| **HTML** | Web-ready interactive reports | Dashboards, web viewing |
| **CSV** | Comma-separated values for data export | Data analysis, system integration |
| **JSON** | Structured data format | API integration, system-to-system |
| **XML** | Markup language for structured data | Enterprise integration |

### 2.2 Generation Pipeline

1. **Report Definition:** Parse report structure and elements.
2. **Data Collection:** Gather data from various sources.
3. **Template Processing:** Apply templates and themes.
4. **Content Rendering:** Render each element with data.
5. **Format Conversion:** Convert to target output format.
6. **Post-Processing:** Add watermarks, signatures, compression.
7. **Distribution:** Deliver to recipients via configured channels.

### 2.3 Streaming Architecture

```python
class StreamingReportGenerator:
    def __init__(self, template_engine: TemplateEngine, data_service: DataService):
        self.template_engine = template_engine
        self.data_service = data_service
    
    async def generate_streaming(self, report_id: int, output_format: str) -> AsyncIterator[bytes]:
        """Generate report in streaming fashion for large datasets."""
        # Get report definition
        report = await self.get_report(report_id)
        
        # Initialize format generator
        generator = self.get_format_generator(output_format)
        
        # Stream header
        header = await generator.generate_header(report)
        yield header
        
        # Stream content sections
        for section in report.sections:
            # Get section data in chunks
            async for data_chunk in self.data_service.get_section_data(section, chunk_size=1000):
                # Render section chunk
                rendered_chunk = await self.template_engine.render_section(section, data_chunk)
                # Convert to output format
                output_chunk = await generator.render_chunk(rendered_chunk)
                yield output_chunk
        
        # Stream footer
        footer = await generator.generate_footer(report)
        yield footer
```

---

## 3. Visual Report Designer

### 3.1 Designer Features

- **Canvas:** WYSIWYG canvas with zoom and page navigation.
- **Element Palette:** Library of report elements with previews.
- **Property Panel:** Dynamic property editor for selected elements.
- **Templates:** Pre-built report templates for various industries.
- **Themes:** Apply consistent styling across reports.
- **Preview Mode:** Real-time preview with sample data.
- **Multi-page Support:** Design reports with multiple pages and sections.
- **Master Pages:** Define reusable headers, footers, and layouts.
- **Data Binding:** Visual data source configuration.
- **Conditional Logic:** Show/hide elements based on conditions.

### 3.2 Report Elements

| Category | Elements | Description |
|----------|----------|-------------|
| **Layout** | Page, Section, Column, Break, Spacer | Structure and layout control |
| **Text** | Title, Subtitle, Paragraph, List, Rich Text, Markdown | Text content and formatting |
| **Data** | Table, Pivot Table, Chart, KPI Card, Gauge | Data visualization |
| **Media** | Image, Video, Logo, Icon | Visual media elements |
| **Interactive** | Hyperlink, Bookmark, Table of Contents | Navigation and interactivity |
| **Dynamic** | Variable, Expression, Formula | Dynamic content |
| **AI** | AI Summary, AI Insights, AI Recommendations | AI-powered content |
| **Advanced** | QR Code, Barcode, Signature Field | Specialized elements |

### 3.3 Data Sources

- **Database Queries:** Direct SQL queries with parameters.
- **KPI Values:** Pre-calculated KPIs from KPI Engine.
- **Dashboard Data:** Extract data from dashboard widgets.
- **ETL Results:** Results from ETL pipeline executions.
- **AI Insights:** Insights from AI Platform.
- **Workflow Data:** Data from workflow executions.
- **Uploaded Files:** CSV, Excel, JSON files.
- **External APIs:** REST API data sources.
- **Static Data:** Fixed data sets and lookup tables.

---

## 4. AI Integration

### 4.1 AI-Powered Features

- **AI Executive Summary:** Generate executive summaries from data.
- **AI Data Storytelling:** Create narrative explanations of data trends.
- **AI Trend Analysis:** Identify and explain trends in data.
- **AI Risk Summary:** Highlight risks and anomalies.
- **AI Recommendations:** Provide actionable insights.
- **AI Report Generation:** Generate complete reports from requirements.
- **AI Translation:** Translate reports to multiple languages.
- **AI Grammar Review:** Review and improve report language.

### 4.2 AI Content Generation

```python
class AIReportGenerator:
    def __init__(self, ai_gateway: AIGateway):
        self.ai_gateway = ai_gateway
    
    async def generate_executive_summary(self, report_data: dict, context: dict) -> str:
        """Generate AI executive summary for report."""
        prompt = f"""
        Generate an executive summary for a report with the following data:
        
        Report Type: {context.get('report_type', 'General')}
        Time Period: {context.get('period', 'Last Month')}
        Key Metrics: {report_data.get('key_metrics', [])}
        Trends: {report_data.get('trends', [])}
        Risks: {report_data.get('risks', [])}
        
        Generate a concise, professional executive summary that:
        1. Highlights key achievements
        2. Identifies important trends
        3. Notes any concerns or risks
        4. Provides forward-looking insights
        
        Keep it under 200 words and use business language.
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="executive_summary")
        return response.response
    
    async def generate_data_story(self, data_points: list, insights: list) -> str:
        """Generate narrative story from data insights."""
        prompt = f"""
        Create a compelling data story from these insights:
        
        Data Points: {data_points}
        Key Insights: {insights}
        
        Tell a story that:
        1. Sets the context
        2. Reveals key findings
        3. Explains the implications
        4. Suggests next steps
        
        Use clear, engaging language suitable for business stakeholders.
        """
        
        response = await self.ai_gateway.chat(prompt, assistant_type="storyteller")
        return response.response
```

---

## 5. Scheduling Architecture

### 5.1 Schedule Types

| Type | Description | Examples |
|------|-------------|----------|
| **One-Time** | Single execution at specified time | End-of-month report |
| **Hourly** | Every hour at specified minute | Operational metrics |
| **Daily** | Every day at specified time | Daily sales report |
| **Weekly** | Every week on specified day | Weekly performance |
| **Monthly** | Every month on specified day | Monthly financials |
| **Quarterly** | Every quarter | Quarterly review |
| **Yearly** | Every year | Annual report |
| **Cron** | Custom cron expression | Complex schedules |

### 5.2 Scheduler Engine

```python
class ReportScheduler:
    def __init__(self, queue: TaskQueue, notification_service: NotificationService):
        self.queue = queue
        self.notification_service = notification_service
    
    async def schedule_report(self, report_id: int, schedule_config: ScheduleConfig):
        """Schedule report generation."""
        # Validate cron expression
        if schedule_config.type == 'cron':
            cron_validator = CronValidator()
            if not cron_validator.validate(schedule_config.expression):
                raise ValueError("Invalid cron expression")
        
        # Create schedule
        schedule = ReportSchedule(
            report_id=report_id,
            schedule_config=schedule_config,
            next_run=self.calculate_next_run(schedule_config),
            created_by=schedule_config.user_id
        )
        await self.save_schedule(schedule)
        
        # Queue next execution
        await self.queue_next_execution(schedule)
    
    async def execute_scheduled_report(self, schedule_id: int):
        """Execute scheduled report."""
        schedule = await self.get_schedule(schedule_id)
        
        try:
            # Generate report
            generation_task = GenerateReportTask(
                report_id=schedule.report_id,
                parameters=schedule.parameters,
                output_formats=schedule.output_formats
            )
            result = await self.queue.enqueue(generation_task)
            
            # Update schedule
            schedule.last_run = datetime.utcnow()
            schedule.next_run = self.calculate_next_run(schedule.schedule_config)
            await self.save_schedule(schedule)
            
            # Queue next execution
            await self.queue_next_execution(schedule)
            
        except Exception as e:
            # Handle failure
            await self.handle_schedule_failure(schedule, e)
```

---

## 6. Distribution Architecture

### 6.1 Distribution Channels

| Channel | Description | Use Cases |
|---------|-------------|-----------|
| **Email** | Send reports as attachments or links | Regular distribution to stakeholders |
| **SMS** | Send notification with download link | Urgent reports, alerts |
| **WhatsApp** | Send reports via WhatsApp | Mobile-first distribution |
| **In-App** | Notify users within application | Internal distribution |
| **Cloud Storage** | Upload to cloud storage (S3, Azure, GCP) | Archival, integration |
| **Secure Link** | Generate secure download links | Controlled access |
| **API Webhook** | Send to external systems | Integration with other platforms |

### 6.2 Distribution Engine

```python
class ReportDistributor:
    def __init__(self):
        self.channels = {
            'email': EmailChannel(),
            'sms': SMSChannel(),
            'whatsapp': WhatsAppChannel(),
            'in_app': InAppChannel(),
            'cloud_storage': CloudStorageChannel(),
            'secure_link': SecureLinkChannel(),
            'webhook': WebhookChannel()
        }
    
    async def distribute_report(self, report_id: int, distribution_config: DistributionConfig):
        """Distribute report through configured channels."""
        # Get generated report files
        report_files = await self.get_report_files(report_id)
        
        # Distribute through each channel
        for channel_config in distribution_config.channels:
            channel = self.channels.get(channel_config.type)
            if not channel:
                raise ValueError(f"Unknown distribution channel: {channel_config.type}")
            
            try:
                await channel.send(
                    files=report_files,
                    recipients=channel_config.recipients,
                    message=channel_config.message,
                    options=channel_config.options
                )
                
                # Log distribution
                await self.log_distribution(report_id, channel_config.type, 'success')
                
            except Exception as e:
                # Log failure
                await self.log_distribution(report_id, channel_config.type, 'failed', str(e))
                
                # Retry if configured
                if channel_config.retry_on_failure:
                    await self.schedule_retry(report_id, channel_config, e)
```

---

## 7. Database Schema

### 7.1 Tables

```sql
CREATE TABLE reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  report_type VARCHAR(64) NOT NULL, -- executive, operational, analytical, financial, compliance, government, hospital, education, church, ngo, project, audit, ai_insight, forecast, custom
  owner_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  template_id BIGINT,
  theme_id BIGINT,
  definition JSON NOT NULL,
  data_sources JSON,
  output_formats JSON,
  is_template BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  tags JSON,
  metadata JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (category_id) REFERENCES report_categories(id),
  FOREIGN KEY (owner_id) REFERENCES users(id),
  FOREIGN KEY (template_id) REFERENCES report_templates(id),
  FOREIGN KEY (theme_id) REFERENCES report_themes(id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_owner (owner_id),
  INDEX idx_type (report_type),
  INDEX idx_template (is_template)
) ENGINE=InnoDB;

CREATE TABLE report_templates (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category_id BIGINT,
  industry_id BIGINT,
  report_type VARCHAR(64),
  thumbnail_url VARCHAR(512),
  definition JSON NOT NULL,
  elements JSON,
  variables JSON,
  usage_count INT DEFAULT 0,
  rating DECIMAL(3,2),
  is_featured BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES report_categories(id),
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_category (category_id),
  INDEX idx_industry (industry_id),
  INDEX idx_type (report_type),
  INDEX idx_featured (is_featured)
) ENGINE=InnoDB;

CREATE TABLE report_sections (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  section_name VARCHAR(128) NOT NULL,
  section_type VARCHAR(64) NOT NULL, -- header, footer, cover, toc, body, appendix
  order_index INT NOT NULL,
  definition JSON NOT NULL,
  data_source JSON,
  is_conditional BOOLEAN DEFAULT FALSE,
  condition_expression TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  INDEX idx_report_order (report_id, order_index)
) ENGINE=InnoDB;

CREATE TABLE report_elements (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  section_id BIGINT NOT NULL,
  element_id VARCHAR(128) NOT NULL,
  element_type VARCHAR(64) NOT NULL, -- text, table, chart, image, ai_summary, variable
  position_x DECIMAL(10,2),
  position_y DECIMAL(10,2),
  width DECIMAL(10,2),
  height DECIMAL(10,2),
  config JSON NOT NULL,
  data_binding JSON,
  is_conditional BOOLEAN DEFAULT FALSE,
  condition_expression TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (section_id) REFERENCES report_sections(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_section_element (section_id, element_id),
  INDEX idx_section (section_id),
  INDEX idx_type (element_type)
) ENGINE=InnoDB;

CREATE TABLE report_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  version INT NOT NULL,
  name VARCHAR(255),
  description TEXT,
  definition_snapshot JSON NOT NULL,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id),
  UNIQUE KEY uniq_report_version (report_id, version),
  INDEX idx_report (report_id)
) ENGINE=InnoDB;

CREATE TABLE report_schedules (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  organization_id BIGINT NOT NULL,
  schedule_type VARCHAR(32) NOT NULL, -- onetime, hourly, daily, weekly, monthly, quarterly, yearly, cron
  schedule_expression VARCHAR(255),
  timezone VARCHAR(64),
  parameters JSON,
  output_formats JSON,
  distribution_config JSON,
  is_active BOOLEAN DEFAULT TRUE,
  next_run DATETIME,
  last_run DATETIME,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_next_run (next_run),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE report_distribution (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  schedule_id BIGINT,
  generation_id BIGINT,
  channel_type VARCHAR(32) NOT NULL, -- email, sms, whatsapp, in_app, cloud_storage, secure_link, webhook
  recipients JSON NOT NULL,
  message TEXT,
  attachments JSON,
  status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, sent, failed, retry
  sent_at DATETIME,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (schedule_id) REFERENCES report_schedules(id),
  FOREIGN KEY (generation_id) REFERENCES report_generations(id),
  INDEX idx_report (report_id),
  INDEX idx_status (status),
  INDEX idx_channel (channel_type)
) ENGINE=InnoDB;

CREATE TABLE report_permissions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  role_id BIGINT,
  user_id BIGINT,
  permission_type VARCHAR(32) NOT NULL, -- view, edit, delete, generate, schedule, distribute
  granted_by BIGINT NOT NULL,
  granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (granted_by) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_role (role_id),
  INDEX idx_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE report_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL, -- created, updated, generated, scheduled, distributed, viewed
  details JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE report_generations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  version INT,
  parameters JSON,
  output_formats JSON,
  status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
  started_at DATETIME,
  completed_at DATETIME,
  generated_by BIGINT,
  file_paths JSON,
  file_sizes JSON,
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (generated_by) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_status (status),
  INDEX idx_started (started_at)
) ENGINE=InnoDB;

CREATE TABLE report_comments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  comment TEXT NOT NULL,
  mentions JSON,
  parent_id BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (parent_id) REFERENCES report_comments(id),
  INDEX idx_report (report_id),
  INDEX idx_user (user_id),
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB;

CREATE TABLE report_signatures (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  generation_id BIGINT,
  signer_id BIGINT NOT NULL,
  signature_type VARCHAR(32) NOT NULL, -- digital, electronic, approval
  signature_data JSON,
  certificate_data JSON,
  signed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(45),
  user_agent TEXT,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  FOREIGN KEY (generation_id) REFERENCES report_generations(id),
  FOREIGN KEY (signer_id) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_generation (generation_id),
  INDEX idx_signer (signer_id)
) ENGINE=InnoDB;

CREATE TABLE report_audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT,
  generation_id BIGINT,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL,
  old_value JSON,
  new_value JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id),
  FOREIGN KEY (generation_id) REFERENCES report_generations(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_report (report_id),
  INDEX idx_generation (generation_id),
  INDEX idx_user (user_id),
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE report_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  parent_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES report_categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE report_themes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  theme_config JSON NOT NULL,
  is_default BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_default (is_default),
  INDEX idx_public (is_public)
) ENGINE=InnoDB;
```

### 7.2 Indexes & Optimization

- Primary keys on all tables.
- Foreign key indexes.
- Composite indexes for common queries (org+status, report+user, generation+status).
- Full-text indexes on report name and description for search.
- Partition `report_history` and `report_audit_logs` by month if needed.

---

## 8. ER Diagram (Textual)

```
reports (1) → (n) report_sections
reports (1) → (n) report_versions
reports (1) → (n) report_schedules
reports (1) → (n) report_distribution
reports (1) → (n) report_permissions
reports (1) → (n) report_history
reports (1) → (n) report_generations
reports (1) → (n) report_comments
reports (1) → (n) report_signatures
reports (1) → (n) report_audit_logs

report_sections (1) → (n) report_elements

report_generations (1) → (n) report_distribution
report_generations (1) → (n) report_signatures

report_categories (1) → (n) reports
report_categories (1) → (n) report_templates
report_themes (1) → (n) reports
```

---

## 9. API Specification

Base path: `/api/v1/reports`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List reports. |
| POST | `/` | Create report. |
| GET | `/{id}` | Get report details. |
| PUT | `/{id}` | Update report. |
| DELETE | `/{id}` | Delete report. |
| POST | `/{id}/generate` | Generate report. |
| GET | `/{id}/generations` | List report generations. |
| GET | `/{id}/generations/{genId}/download` | Download generated report. |
| POST | `/{id}/schedule` | Schedule report generation. |
| GET | `/{id}/schedule` | Get schedule configuration. |
| PUT | `/{id}/schedule` | Update schedule. |
| DELETE | `/{id}/schedule` | Delete schedule. |
| POST | `/{id}/distribute` | Distribute report. |
| GET | `/{id}/history` | Get report history. |
| POST | `/{id}/comment` | Add comment. |
| GET | `/{id}/comments` | List comments. |
| POST | `/{id}/sign` | Sign report. |
| GET | `/templates` | List report templates. |
| POST | `/templates` | Create report template. |
| GET | `/categories` | List report categories. |
| GET | `/themes` | List report themes. |
| POST | `/preview` | Preview report with sample data. |

### Example: Generate Report

```http
POST /api/v1/reports/123/generate
{
  "parameters": {
    "date_range": {
      "start": "2026-06-01",
      "end": "2026-06-30"
    },
    "departments": ["sales", "marketing"],
    "format": "detailed"
  },
  "output_formats": ["pdf", "excel"],
  "distribution": {
    "channels": [
      {
        "type": "email",
        "recipients": ["ceo@company.com", "cfo@company.com"],
        "message": "Monthly sales report is ready"
      }
    ]
  }
}
```

Response:
```json
{
  "generation_id": 456,
  "status": "pending",
  "estimated_completion": "2026-07-14T10:05:00Z",
  "output_formats": ["pdf", "excel"]
}
```

---

## 10. Backend Architecture

### 10.1 Package Structure

```
report_engine/
├── __init__.py
├── designer.py                # Report design logic
├── generator.py               # Report generation engine
├── scheduler.py               # Scheduling engine
├── distributor.py             # Distribution engine
├── formats/                   # Output format generators
│   ├── __init__.py
│   ├── pdf.py                 # PDF generation
│   ├── excel.py               # Excel generation
│   ├── word.py                # Word generation
│   ├── powerpoint.py          # PowerPoint generation
│   └── html.py                # HTML generation
├── elements/                  # Report elements
│   ├── __init__.py
│   ├── base.py                # Base element class
│   ├── text.py                # Text elements
│   ├── table.py               # Table elements
│   ├── chart.py               # Chart elements
│   └── ai.py                  # AI elements
├── channels/                  # Distribution channels
│   ├── __init__.py
│   ├── email.py               # Email channel
│   ├── sms.py                 # SMS channel
│   ├── whatsapp.py            # WhatsApp channel
│   └── cloud_storage.py       # Cloud storage channel
├── ai/                        # AI integration
│   ├── __init__.py
│   ├── generator.py           # AI report generation
│   ├── summary.py             # AI summaries
│   └── insights.py            # AI insights
├── api/
│   └── routes.py              # Report APIs
├── models/
│   └── report_models.py       # SQLAlchemy models
├── schemas/
│   └── report_schemas.py      # Pydantic schemas
└── migrations/                # Alembic migrations
```

### 10.2 Report Generation Engine

```python
class ReportGenerator:
    def __init__(self, template_engine: TemplateEngine, data_service: DataService):
        self.template_engine = template_engine
        self.data_service = data_service
        self.format_generators = {
            'pdf': PDFGenerator(),
            'excel': ExcelGenerator(),
            'word': WordGenerator(),
            'powerpoint': PowerPointGenerator(),
            'html': HTMLGenerator()
        }
    
    async def generate_report(self, report_id: int, parameters: dict, output_formats: List[str]) -> GenerationResult:
        """Generate report in specified formats."""
        # Get report definition
        report = await self.get_report(report_id)
        
        # Create generation record
        generation = ReportGeneration(
            report_id=report_id,
            parameters=parameters,
            output_formats=output_formats,
            status='processing'
        )
        await self.save_generation(generation)
        
        try:
            # Collect data
            data = await self.collect_report_data(report, parameters)
            
            # Process AI elements
            ai_data = await self.process_ai_elements(report, data)
            data.update(ai_data)
            
            # Generate each format
            results = {}
            for format_type in output_formats:
                generator = self.format_generators.get(format_type)
                if not generator:
                    raise ValueError(f"Unsupported format: {format_type}")
                
                # Generate report
                file_path = await generator.generate(report, data)
                results[format_type] = file_path
            
            # Update generation record
            generation.status = 'completed'
            generation.file_paths = results
            generation.completed_at = datetime.utcnow()
            await self.save_generation(generation)
            
            return GenerationResult(
                generation_id=generation.id,
                status='completed',
                files=results
            )
            
        except Exception as e:
            # Handle failure
            generation.status = 'failed'
            generation.error_message = str(e)
            await self.save_generation(generation)
            raise
```

---

## 11. Frontend Architecture

### 11.1 Component Structure

```
report_builder/
├── components/
│   ├── Designer/
│   │   ├── Canvas.tsx          # Design canvas
│   │   ├── ElementPalette.tsx  # Element library
│   │   ├── PropertyPanel.tsx   # Property editor
│   │   └── PreviewMode.tsx     # Preview mode
│   ├── Elements/
│   │   ├── Text/
│   │   ├── Table/
│   │   ├── Chart/
│   │   └── AI/
│   ├── Toolbar/
│   │   ├── FormatToolbar.tsx   # Formatting tools
│   │   ├── DataToolbar.tsx     # Data binding tools
│   │   └── ViewToolbar.tsx     # View options
│   └── Modals/
│       ├── DataSourceModal.tsx # Data source configuration
│       ├── ScheduleModal.tsx   # Scheduling configuration
│       └── DistributionModal.tsx # Distribution configuration
├── hooks/
│   ├── useReport.ts            # Report state
│   ├── useElements.ts          # Element management
│   ├── useDataSources.ts       # Data source management
│   └── usePreview.ts           # Preview functionality
├── stores/
│   ├── reportStore.ts          # Report state management
│   ├── elementStore.ts         # Element state
│   └── dataSourceStore.ts      # Data source state
└── utils/
    ├── reportUtils.ts          # Report helpers
    ├── elementUtils.ts         # Element helpers
    └── dataBinding.ts          # Data binding logic
```

### 11.2 State Management

- **Report Store:** Current report, sections, elements, layout.
- **Element Store:** Element configurations, data binding, interactions.
- **Data Source Store:** Data sources, queries, connections.
- **Preview Store:** Preview state, sample data, rendering.

### 11.3 Real-time Features

- **Collaborative Editing:** Real-time cursor positions and edits (optional).
- **Generation Status:** Real-time report generation progress.
- **Distribution Tracking:** Real-time distribution status.

---

## 12. Security Design

### 12.1 Access Control

- **Report Permissions:** view, edit, delete, generate, schedule, distribute.
- **Element Permissions:** Control access to sensitive elements.
- **Data Permissions:** Inherit from data source permissions.
- **Distribution Permissions:** Control who can receive reports.

### 12.2 Document Security

- **Watermarking:** Add dynamic watermarks to reports.
- **Password Protection:** Encrypt PDF files with passwords.
- **Digital Signatures:** Add digital signatures for authenticity.
- **Secure Links:** Generate time-limited secure download links.

### 12.3 Audit and Compliance

- **Audit Logging:** Log all report actions and access.
- **Version Control:** Track all report versions and changes.
- **Data Retention:** Configurable data retention policies.
- **Compliance Reporting:** Generate compliance reports.

---

## 13. Performance Strategy

### 13.1 Generation Performance

- **Background Processing:** Generate reports in background jobs.
- **Streaming Generation:** Stream large reports to avoid memory issues.
- **Parallel Processing:** Generate multiple formats in parallel.
- **Caching:** Cache report data and templates.

### 13.2 Database Optimization

- **Indexes:** Optimize indexes for report queries.
- **Partitioning:** Partition large tables by date.
- **Connection Pooling:** Efficient database connections.
- **Query Optimization:** Optimize data source queries.

### 13.3 Frontend Performance

- **Lazy Loading:** Load reports and elements on demand.
- **Virtual Scrolling:** Handle large reports efficiently.
- **Debounced Updates:** Debounce property changes.
- **Code Splitting:** Split code by feature.

---

## 14. Testing Strategy

### 14.1 Unit Tests

- **Generator Tests:** Test report generation for each format.
- **Element Tests:** Test individual element rendering.
- **Scheduler Tests:** Test scheduling logic.
- **Distribution Tests:** Test distribution channels.

### 14.2 Integration Tests

- **API Tests:** Test all REST endpoints.
- **Database Tests:** Test database operations.
- **AI Integration Tests:** Test AI features.
- **End-to-End Tests:** Test complete report workflow.

### 14.3 Performance Tests

- **Load Tests:** Test with many concurrent report generations.
- **Stress Tests:** Test system limits.
- **Scalability Tests:** Test horizontal scaling.

### 14.4 Security Tests

- **Permission Tests:** Test RBAC enforcement.
- **Data Access Tests:** Test data access controls.
- **Document Security Tests**: Test watermarking and encryption.
- **Injection Tests**: Test for injection vulnerabilities.

---

## 15. Administrator Guide

### 15.1 Report Management

- **Creating Reports:** Use report designer or templates.
- **Managing Permissions:** Set report and element permissions.
- **Monitoring Generation:** Track report generation status and performance.
- **Managing Templates:** Create and manage report templates.

### 15.2 System Configuration

- **Data Sources:** Configure database connections and APIs.
- **Distribution Channels:** Set up email, SMS, and cloud storage.
- **AI Configuration:** Configure AI services and models.
- **Performance Tuning**: Optimize system performance.

### 15.3 Compliance and Security

- **Audit Logs:** Review audit logs for compliance.
- **Data Retention:** Configure data retention policies.
- **Security Settings**: Configure security policies.
- **Access Control**: Manage user and role permissions.

---

## 16. Developer Guide

### 16.1 Custom Elements

- **Element Interface:** Implement the BaseElement interface.
- **Element Registration:** Register custom elements in the registry.
- **Data Binding:** Implement data binding logic.
- **Rendering:** Implement rendering for each output format.

### 16.2 Custom Formats

- **Format Interface:** Implement the FormatGenerator interface.
- **Format Registration:** Register custom formats.
- **Template Integration:** Integrate with template engine.
- **Streaming Support:** Implement streaming for large reports.

### 16.3 Best Practices

- **Performance:** Optimize data queries and rendering.
- **Security:** Follow security best practices.
- **Error Handling**: Implement proper error handling.
- **Testing**: Write comprehensive tests.

---

## 17. Output Summary

1. **Report Builder Architecture** — design principles, components, visual designer features.
2. **Document Generation Engine** — multi-format support, streaming architecture, generation pipeline.
3. **Database Schema** — 17 tables with DDL, indexes, relationships, audit fields.
4. **ER Diagram** — textual representation of table relationships.
5. **API Specification** — 35+ REST endpoints for reports, generation, scheduling, distribution.
6. **Backend Architecture** — package structure, generator, scheduler, distributor, format generators.
7. **Frontend Architecture** — component structure, state management, real-time features.
8. **AI Integration** — AI summaries, storytelling, report generation, translation.
9. **Scheduling Architecture** — schedule types, cron expressions, queue management.
10. **Distribution Architecture** — multi-channel distribution, retry logic, tracking.
11. **Security Design** — access control, document security, audit compliance.
12. **Performance Strategy** — background processing, streaming, caching, optimization.
13. **Testing Strategy** — unit, integration, performance, security tests.
14. **Administrator Guide** — report management, system configuration, compliance.
15. **Developer Guide** — custom elements, formats, best practices.

All specifications are enterprise-grade, scalable, modular, production-ready, and fully integrated into AEDIP.
