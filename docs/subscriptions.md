# Subscriptions

## Plans

| Plan | Monthly | Yearly | Users | Storage | AI Requests | API Calls |
|------|---------|--------|-------|---------|-------------|-----------|
| Free | $0 | $0 | 5 | 500MB | 50/mo | 1,000/mo |
| Starter | $29 | $290 | 15 | 5GB | 500/mo | 10,000/mo |
| Professional | $99 | $990 | 50 | 25GB | 5,000/mo | 50,000/mo |
| Business | $299 | $2,990 | 200 | 100GB | 25,000/mo | 250,000/mo |
| Enterprise | $999 | $9,990 | Unlimited | Unlimited | Unlimited | Unlimited |

## Subscription Lifecycle

```
Created → Active → [Upgrade/Downgrade] → [Cancel] → Cancelled
                → Trial → Past Due (grace 7d) → Expired
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/saas/plans` | List available plans |
| GET | `/saas/subscription` | Get current subscription |
| POST | `/saas/subscribe` | Create subscription |
| POST | `/saas/upgrade` | Upgrade/downgrade |
| POST | `/saas/cancel` | Cancel subscription |
| GET | `/saas/usage` | Get usage metrics |
| GET | `/saas/invoices` | List invoices |

## Trial Periods

- Starter & Professional: 14-day trial
- Business & Enterprise: 30-day trial
- Trials auto-expire to `past_due` with 7-day grace period
- After grace period, subscription becomes `expired`

## Usage Tracking

Monthly usage is tracked per organization:
- Active users
- Storage used (MB)
- AI requests
- API calls
- Workflow executions
- Scheduled jobs
- Model trainings
- Connector usage
