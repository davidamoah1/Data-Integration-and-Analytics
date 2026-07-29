# Billing

## Overview

The billing system tracks subscription payments, generates invoices, and manages usage-based billing.

## Payment Providers

The payment system is abstracted to support multiple gateways:

| Provider | Status | Regions |
|----------|--------|---------|
| Stripe | Planned | Global |
| Paystack | Planned | Africa |
| Flutterwave | Planned | Africa |
| Manual | Active | All |

### Adding a New Provider

```python
class PaymentProvider:
    def create_customer(self, org_id: int, email: str) -> str: ...
    def create_subscription(self, customer_id: str, plan_id: str) -> str: ...
    def cancel_subscription(self, subscription_id: str) -> bool: ...
    def process_payment(self, invoice_id: int) -> dict: ...
```

## Invoices

Invoices are generated at the start of each billing period:
- `invoice_number`: Unique identifier (e.g., `INV-2024-001`)
- `amount`: Based on plan price and billing cycle
- `status`: `pending`, `paid`, `failed`, `refunded`
- `line_items`: Detailed breakdown
- `billing_period_start` / `billing_period_end`: Coverage dates

## Usage-Based Billing

Current implementation uses flat-rate pricing. The usage tracking infrastructure supports future metered billing:

```python
# Usage is tracked monthly per organization
saas_service.increment_usage(org_id, "api_calls", amount=1)
saas_service.increment_usage(org_id, "ai_requests", amount=1)
```

## Grace Periods

- Trial expiry: 7-day grace period before `expired`
- Failed payment: 7-day grace period before `suspended`
- During grace: Organization retains access (status: `past_due`)
- After grace: Organization access restricted (status: `expired`)
