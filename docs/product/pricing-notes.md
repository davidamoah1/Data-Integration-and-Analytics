# Pricing Notes

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Pricing model and tier definitions.

## Scope

All pricing tiers and feature gating.

## Audience

Product managers, sales, and customers.

---

## 1. Pricing Tiers

> **⚠️ Note**: Pricing is not yet finalized. The following is the planned model.

| Tier | Price | Target | Key Features |
|------|-------|--------|-------------|
| Free | $0 | Individual / Personal | Personal workspace, 5 datasets, basic analytics |
| Professional | $29/user/mo | Small teams | Organization workspace, unlimited datasets, dashboards, reports |
| Business | $49/user/mo | Mid-market | Everything in Professional + ETL pipelines, AI assistant, Smart Capture |
| Enterprise | Custom | Large orgs | Everything in Business + SSO, SCIM, MFA, white-label, dedicated support |

## 2. Feature Gating

| Feature | Free | Professional | Business | Enterprise |
|---------|------|---------------|----------|------------|
| Personal workspace | ✅ | — | — | — |
| Organization workspace | — | ✅ | ✅ | ✅ |
| Dataset upload | ✅ (5) | ✅ (unlimited) | ✅ | ✅ |
| Dashboards | ✅ (3) | ✅ | ✅ | ✅ |
| Reports | — | ✅ | ✅ | ✅ |
| ETL pipelines | — | — | ✅ | ✅ |
| AI assistant | — | — | ✅ | ✅ |
| Smart Data Capture | — | — | ✅ | ✅ |
| ML models | — | — | ✅ | ✅ |
| SSO | — | — | — | ✅ |
| SCIM | — | — | — | ✅ |
| MFA | — | — | — | ✅ |
| White-label | — | — | — | ✅ |
| Audit logs | — | ✅ | ✅ | ✅ |
| API access | — | — | ✅ | ✅ |

## 3. Current Implementation

- All features currently available to all users (no feature gating enforced yet)
- `SubscriptionService` creates trial subscriptions for all orgs
- SaaS plan definitions seeded in `saas/services.py:seed_saas_data()`
- Frontend `/billing` page exists as placeholder

## 4. Future Implementation

- Stripe integration for payment processing
- Usage tracking (datasets, users, API calls)
- Feature flag enforcement based on plan
- Billing dashboard with invoices

## Related Documents

- [feature-catalog.md](feature-catalog.md) — Feature catalog
- [roadmap.md](roadmap.md) — Product roadmap
- [../architecture/adr/README.md](../architecture/adr/README.md) — ADR-0012 (Licensing)
