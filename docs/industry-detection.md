# Industry Detection

## Overview

The Industry Detection engine determines the business sector of a dataset using a weighted scoring system that combines column-name matching and value-based signal detection.

## How It Works

### Phase 1: Column-Name Matching

Each column is matched against the **Entity Library** (`semantic/entity_library.py`) using:

1. **Exact synonym match** — confidence 1.0
2. **Partial synonym match** (contains/contained) — confidence > 0.65
3. **Fuzzy match** (character overlap + prefix) — confidence > 0.65
4. **Heuristic** (data type based) — confidence 0.6-0.8

Each matched entity has an **industry** and a **weight**:
- **Strong signals** (weight 3.0): `patient_id`, `student_id`, `loan_id`, `crop_yield`
- **Moderate signals** (weight 2.0-2.5): `doctor`, `teacher`, `prescription`, `harvest`
- **Weak/universal** (no vote): `date`, `region`, `revenue`, `amount`

### Phase 2: Value-Based Signal Detection

The `DataUnderstandingEngine` (`semantic/data_understanding.py`) analyzes column values:

- Entity recognition from sample values
- Statistical pattern detection
- Data distribution analysis

Value-based votes are merged with name-based votes using `VALUE_SIGNAL_WEIGHT = 1.0`.

### Confidence Calculation

```
confidence = (best_industry_votes / total_votes) × 100
```

### Thresholds

| Confidence | Behavior |
|-----------|----------|
| < 70% | Return "unknown" — user confirmation required |
| 70% - 85% | Show recommendation with confidence |
| > 85% | Allow automatic selection |

### Tie-Breaking

If the top two industries have votes within `MIN_VOTE_MARGIN = 0.5`, the result is "unknown".

## Supported Industries

- **Healthcare** — patient, doctor, diagnosis, prescription, ward, vitals
- **Education** — student, teacher, grade, attendance, subject, semester
- **Agriculture** — farm, crop, harvest, yield, fertilizer, livestock
- **Government** — ministry, district, budget, region, program
- **Banking** — account, loan, balance, interest, branch, transaction
- **Retail** — product, customer, sales, inventory, category
- **SME** — business, revenue, expense, employee
- **Logistics** — shipment, vehicle, route, delivery
- **Manufacturing** — production, machine, downtime, quality
- **Telecom** — subscriber, plan, data_usage, call, service

## Alternative Candidates

When multiple industries receive votes, the top alternatives are returned with their vote counts, allowing users to see what other industries were considered.

## User Confirmation

When `needs_confirmation` is `true`, the UI prompts the user to confirm or override the detected industry. This prevents incorrect dashboards from being generated for ambiguous datasets.

## No Hardcoded Assumptions

The engine **never** forces a specific industry (e.g., Banking) on a dataset. If the evidence doesn't support a confident detection, it returns "unknown" and asks for user input.
