# Customer Onboarding

## Overview

The onboarding flow guides new organizations through a 9-step setup process, ensuring they derive value from the platform quickly.

## Onboarding Steps

| Step | Key | Weight | Description |
|------|-----|--------|-------------|
| 1 | `org_creation` | 10% | Organization created |
| 2 | `admin_account` | 10% | Admin account configured |
| 3 | `industry_selection` | 10% | Industry selected (healthcare, education, banking, etc.) |
| 4 | `dataset_upload` | 15% | First dataset uploaded |
| 5 | `connector_setup` | 10% | Data connector configured |
| 6 | `dashboard_creation` | 15% | First dashboard created |
| 7 | `ai_introduction` | 10% | AI Copilot introduced |
| 8 | `sample_data` | 10% | Sample data loaded (optional) |
| 9 | `product_tour` | 10% | Product tour completed |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/saas/onboarding` | Get progress |
| POST | `/saas/onboarding/complete-step` | Complete a step |

## Industry Selection

Available industries:
- Healthcare
- Education
- Banking & Finance
- Agriculture
- Retail
- Government
- Manufacturing
- Logistics
- Telecommunications
- Other

## Sample Data

When `sample_data` step is completed, the system loads:
- Sample datasets relevant to the selected industry
- Pre-built dashboard templates
- Example KPIs
- Sample AI insights

## Tracking

Onboarding progress is tracked per organization:
- `completion_percentage`: 0-100
- `is_complete`: True when all steps done
- `current_step`: Next step to complete
- `completed_at`: Timestamp when fully complete
