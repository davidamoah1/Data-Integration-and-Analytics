"""Banking Intelligence â€” Accounts, transactions, loans, risk analytics.

Specialized analytics for banks and financial institutions:
  - Account analytics (volume, balances, types)
  - Transaction patterns (volume, frequency, trends)
  - Loan portfolio health (defaults, delinquency, NPL)
  - Risk indicators (concentration, fraud patterns)
"""

from __future__ import annotations

import pandas as pd

from industry_intelligence.base import (
    AnalyticsResult,
    Breakdown,
    IndustryAnalytics,
    IndustryAnalyticsRegistry,
    Insight,
    Trend,
)


class BankingAnalytics(IndustryAnalytics):
    industry = "banking"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        account_col = cls._find_col(df, col_mapping, ["account"])
        txn_col = cls._find_col(df, col_mapping, ["transaction"])
        loan_col = cls._find_col(df, col_mapping, ["loan"])
        card_col = cls._find_col(df, col_mapping, ["card"])
        amount_col = cls._find_numeric_col(df, col_mapping, ["revenue", "amount", "balance"])
        date_col = cls._find_date_col(df, col_mapping)
        customer_col = cls._find_col(df, col_mapping, ["customer"])

        # â”€â”€ Account Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if account_col and account_col in df.columns:
            account_count = int(df[account_col].nunique())
            insights.append(
                Insight(
                    title="Total Accounts",
                    value=account_count,
                    formatted=cls._fmt_number(account_count),
                    category="operational",
                    description="Unique bank accounts in the dataset.",
                )
            )

        # â”€â”€ Transaction Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if txn_col and txn_col in df.columns:
            txn_count = int(df[txn_col].nunique())
            insights.append(
                Insight(
                    title="Total Transactions",
                    value=txn_count,
                    formatted=cls._fmt_number(txn_count),
                    category="operational",
                    description="Unique transactions recorded.",
                )
            )

            if account_col and account_col in df.columns and account_count > 0:
                txns_per_account = txn_count / account_count
                insights.append(
                    Insight(
                        title="Transactions per Account",
                        value=txns_per_account,
                        formatted=f"{txns_per_account:.1f}",
                        category="operational",
                        description="Average number of transactions per account.",
                    )
                )

        # â”€â”€ Volume / Amount â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if amount_col and amount_col in df.columns:
            total_volume = float(df[amount_col].sum())
            insights.append(
                Insight(
                    title="Total Transaction Volume",
                    value=total_volume,
                    formatted=cls._fmt_currency(total_volume),
                    category="financial",
                    description="Total monetary volume across all transactions.",
                )
            )

            avg_txn = total_volume / max(len(df), 1)
            insights.append(
                Insight(
                    title="Avg Transaction Value",
                    value=avg_txn,
                    formatted=cls._fmt_currency(avg_txn),
                    category="financial",
                    description="Average value per transaction.",
                )
            )

            if date_col:
                vol_trend = cls._compute_trend(df, date_col, amount_col, "sum")
                if vol_trend:
                    vol_trend.metric = "volume"
                    trends.append(vol_trend)

        # â”€â”€ Loan Portfolio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if loan_col and loan_col in df.columns:
            loan_count = int(df[loan_col].nunique())
            insights.append(
                Insight(
                    title="Total Loans",
                    value=loan_count,
                    formatted=cls._fmt_number(loan_count),
                    category="financial",
                    description="Unique loan records.",
                )
            )

            if amount_col and amount_col in df.columns:
                loan_volume = float(df[amount_col].sum())
                insights.append(
                    Insight(
                        title="Loan Portfolio Value",
                        value=loan_volume,
                        formatted=cls._fmt_currency(loan_volume),
                        category="financial",
                        description="Total value of the loan portfolio.",
                    )
                )

        # â”€â”€ Card Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if card_col and card_col in df.columns:
            card_count = int(df[card_col].nunique())
            insights.append(
                Insight(
                    title="Active Cards",
                    value=card_count,
                    formatted=cls._fmt_number(card_count),
                    category="operational",
                    description="Unique cards issued.",
                )
            )

        # â”€â”€ Customer Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if customer_col and customer_col in df.columns:
            customer_count = int(df[customer_col].nunique())
            insights.append(
                Insight(
                    title="Total Customers",
                    value=customer_count,
                    formatted=cls._fmt_number(customer_count),
                    category="operational",
                    description="Unique banking customers.",
                )
            )

        # â”€â”€ Breakdowns â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if account_col and account_col in df.columns and amount_col and amount_col in df.columns:
            acct_bd = cls._compute_breakdown(df, account_col, amount_col, "sum")
            if acct_bd:
                acct_bd.dimension = "Account"
                acct_bd.metric = "volume"
                breakdowns.append(acct_bd)

        # â”€â”€ Risk Indicators â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if amount_col and amount_col in df.columns:
            # Large transaction detection
            large_txns = df[df[amount_col] > df[amount_col].quantile(0.95)]
            if len(large_txns) > 0:
                insights.append(
                    Insight(
                        title="Large Transactions (>95th pct)",
                        value=len(large_txns),
                        formatted=cls._fmt_number(len(large_txns)),
                        category="risk",
                        description="Transactions above the 95th percentile â€” potential flag for review.",
                        alert="warning" if len(large_txns) > 10 else "ok",
                    )
                )

        recommendations.extend(
            [
                "Monitor transaction volume trends for anomaly detection.",
                "Track loan portfolio health and delinquency rates.",
                "Review large transactions for compliance and fraud prevention.",
                "Analyze customer activity patterns for retention strategies.",
            ]
        )

        for insight in insights:
            if insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} â€” monitor closely.")

        return AnalyticsResult(
            industry="banking",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("banking", BankingAnalytics)
