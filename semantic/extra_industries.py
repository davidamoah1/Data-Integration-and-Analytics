"""Extended business-entity definitions for additional AEDIP industries.

These entities are loaded into the ENTITY_LIBRARY so the semantic engine can
classify datasets from banking, insurance, hospitality, and telecommunications.
"""

from __future__ import annotations

EXTRA_ENTITIES: dict[str, dict] = {
    # ── Banking ──
    "account": {
        "display_name": "Account",
        "industry": "banking",
        "synonyms": [
            "account",
            "account_id",
            "account_number",
            "bank_account",
            "savings_account",
            "checking_account",
            "balance",
        ],
        "attributes": ["account_id", "customer_id", "account_type", "balance", "open_date"],
        "kpis": ["total_accounts", "active_accounts", "average_balance", "deposit_growth"],
        "relationships": [
            {"target": "customer", "type": "belongs_to", "label": "customer"},
            {"target": "transaction", "type": "has", "label": "transactions"},
        ],
    },
    "transaction": {
        "display_name": "Transaction",
        "industry": "banking",
        "synonyms": [
            "transaction",
            "transaction_id",
            "txn",
            "txn_id",
            "transfer",
            "deposit",
            "withdrawal",
            "transaction_amount",
        ],
        "attributes": ["transaction_id", "account_id", "amount", "type", "date"],
        "kpis": ["total_volume", "total_value", "avg_transaction", "fraud_rate"],
        "relationships": [
            {"target": "account", "type": "from", "label": "account"},
        ],
    },
    "loan": {
        "display_name": "Loan",
        "industry": "banking",
        "synonyms": ["loan", "loan_id", "credit", "mortgage", "personal_loan", "business_loan"],
        "attributes": ["loan_id", "customer_id", "principal", "interest_rate", "status"],
        "kpis": ["total_loans", "total_principal", "default_rate", "approval_rate"],
        "relationships": [
            {"target": "customer", "type": "borrowed_by", "label": "customer"},
        ],
    },
    "card": {
        "display_name": "Card",
        "industry": "banking",
        "synonyms": ["card", "card_id", "credit_card", "debit_card", "atm_card"],
        "attributes": ["card_id", "account_id", "card_type", "limit", "status"],
        "kpis": ["active_cards", "spending_volume", "delinquency_rate"],
        "relationships": [
            {"target": "account", "type": "linked_to", "label": "account"},
        ],
    },
    # ── Insurance ──
    "policy": {
        "display_name": "Policy",
        "industry": "insurance",
        "synonyms": ["policy", "policy_id", "policy_number", "coverage", "insurance_policy"],
        "attributes": ["policy_id", "customer_id", "premium", "coverage_amount", "start_date"],
        "kpis": ["total_policies", "total_premium", "avg_premium", "renewal_rate"],
        "relationships": [
            {"target": "customer", "type": "held_by", "label": "customer"},
            {"target": "claim", "type": "has", "label": "claims"},
        ],
    },
    "claim": {
        "display_name": "Claim",
        "industry": "insurance",
        "synonyms": [
            "claim",
            "claim_id",
            "insurance_claim",
            "claim_amount",
            "settlement",
            "incident",
        ],
        "attributes": ["claim_id", "policy_id", "amount", "status", "date"],
        "kpis": ["total_claims", "claim_value", "approval_rate", "avg_claim_amount"],
        "relationships": [
            {"target": "policy", "type": "on", "label": "policy"},
        ],
    },
    "agent": {
        "display_name": "Agent",
        "industry": "insurance",
        "synonyms": ["agent", "agent_id", "agent_name", "broker", "underwriter"],
        "attributes": ["agent_id", "name", "region", "policies_sold"],
        "kpis": ["agent_count", "policies_per_agent", "commission_total"],
        "relationships": [
            {"target": "policy", "type": "sells", "label": "policies"},
        ],
    },
    # ── Hospitality ──
    "reservation": {
        "display_name": "Reservation",
        "industry": "hospitality",
        "synonyms": [
            "reservation",
            "reservation_id",
            "booking",
            "booking_id",
            "check_in",
            "check_out",
            "nights",
        ],
        "attributes": ["reservation_id", "guest_id", "room_id", "check_in", "check_out"],
        "kpis": ["total_reservations", "occupancy_rate", "revenue_per_room", "avg_length_of_stay"],
        "relationships": [
            {"target": "guest", "type": "made_by", "label": "guest"},
            {"target": "room", "type": "for", "label": "room"},
        ],
    },
    "guest": {
        "display_name": "Guest",
        "industry": "hospitality",
        "synonyms": ["guest", "guest_id", "guest_name", "hotel_guest", "lodging_guest"],
        "attributes": ["guest_id", "name", "email", "loyalty_tier"],
        "kpis": ["total_guests", "repeat_guest_rate", "satisfaction_score"],
        "relationships": [
            {"target": "reservation", "type": "has", "label": "reservations"},
        ],
    },
    "room": {
        "display_name": "Room",
        "industry": "hospitality",
        "synonyms": ["room", "room_id", "room_number", "suite", "room_type"],
        "attributes": ["room_id", "room_type", "rate", "status"],
        "kpis": ["total_rooms", "available_rooms", "adr", "revpar"],
        "relationships": [
            {"target": "reservation", "type": "used_in", "label": "reservations"},
        ],
    },
    "service": {
        "display_name": "Service",
        "industry": "hospitality",
        "synonyms": ["service", "service_id", "amenity", "spa", "restaurant", "minibar"],
        "attributes": ["service_id", "reservation_id", "service_type", "amount", "date"],
        "kpis": ["service_revenue", "service_count", "revenue_per_guest"],
        "relationships": [
            {"target": "reservation", "type": "charges_to", "label": "reservation"},
        ],
    },
    # ── Telecommunications ──
    "subscriber": {
        "display_name": "Subscriber",
        "industry": "telecommunications",
        "synonyms": [
            "subscriber",
            "subscriber_id",
            "msisdn",
            "phone_number",
            "handset_id",
            "imei",
        ],
        "attributes": ["subscriber_id", "plan_id", "activation_date", "status"],
        "kpis": ["total_subscribers", "active_subscribers", "churn_rate", "arpu"],
        "relationships": [
            {"target": "call", "type": "makes", "label": "calls"},
            {"target": "data_usage", "type": "generates", "label": "data usage"},
            {"target": "plan", "type": "on", "label": "plan"},
        ],
    },
    "call": {
        "display_name": "Call",
        "industry": "telecommunications",
        "synonyms": ["call", "call_id", "voice_call", "call_duration", "minutes"],
        "attributes": ["call_id", "subscriber_id", "duration_minutes", "cost", "date"],
        "kpis": ["total_calls", "total_minutes", "avg_call_duration", "revenue"],
        "relationships": [
            {"target": "subscriber", "type": "made_by", "label": "subscriber"},
        ],
    },
    "data_usage": {
        "display_name": "Data Usage",
        "industry": "telecommunications",
        "synonyms": ["data_usage", "data", "data_mb", "data_gb", "internet_usage", "usage"],
        "attributes": ["usage_id", "subscriber_id", "mb_used", "date"],
        "kpis": ["total_data_gb", "avg_usage_per_sub", "overage_revenue"],
        "relationships": [
            {"target": "subscriber", "type": "by", "label": "subscriber"},
        ],
    },
    "plan": {
        "display_name": "Plan",
        "industry": "telecommunications",
        "synonyms": ["plan", "plan_id", "tariff", "subscription_plan", "bundle"],
        "attributes": ["plan_id", "plan_name", "monthly_fee", "data_allowance"],
        "kpis": ["plan_count", "subscribers_per_plan", "plan_revenue"],
        "relationships": [
            {"target": "subscriber", "type": "subscribed_by", "label": "subscribers"},
        ],
    },
}
