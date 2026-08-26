"""Industry Intelligence Platform.

Specialized analytics engines for each business sector. Each sector gets
its own analytics module that understands the domain-specific metrics,
patterns, and insights that matter to that industry.

Sectors:
  - healthcare: Patient analytics, disease trends, doctor performance, revenue
  - education: Student performance, attendance, fees, teacher analytics
  - banking: Accounts, transactions, loans, risk
  - agriculture: Production, yield, crop analysis
  - government: Budget, projects, regional analytics
  - retail: Sales, inventory, customers
  - manufacturing: Production, downtime, quality
  - ngo: Donors, programs, beneficiaries, impact
"""

from __future__ import annotations

from industry_intelligence.base import (
    AnalyticsResult,
    IndustryAnalytics,
    IndustryAnalyticsRegistry,
)

__all__ = [
    "AnalyticsResult",
    "IndustryAnalytics",
    "IndustryAnalyticsRegistry",
]
