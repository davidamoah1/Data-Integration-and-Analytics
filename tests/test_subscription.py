"""Tests for the subscription & licensing module."""

from datetime import datetime, timedelta, timezone

from enterprise.subscription import (
    ALL_FEATURES,
    PLAN_DEFINITIONS,
    SubscriptionService,
)
from organizations.models import Organization


def _create_org(db_session, name="Test Org"):
    org = Organization(name=name, slug=name.lower().replace(" ", "-"), is_active=1)
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


class TestSubscriptionService:
    def test_create_trial(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        sub = svc.create_trial(org.id)

        assert sub.organization_id == org.id
        assert sub.plan == "free_trial"
        assert sub.status == "trialing"
        assert sub.trial_started_at is not None
        assert sub.trial_ends_at is not None
        assert sub.max_users == PLAN_DEFINITIONS["free_trial"]["max_users"]
        assert sub.max_dashboards == PLAN_DEFINITIONS["free_trial"]["max_dashboards"]

    def test_create_trial_idempotent(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        sub1 = svc.create_trial(org.id)
        sub2 = svc.create_trial(org.id)
        assert sub1.id == sub2.id

    def test_upgrade_plan(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        sub = svc.upgrade_plan(org.id, "professional")

        assert sub.plan == "professional"
        assert sub.status == "active"
        assert sub.max_users == PLAN_DEFINITIONS["professional"]["max_users"]
        assert (
            sub.max_ai_queries_per_month
            == PLAN_DEFINITIONS["professional"]["max_ai_queries_per_month"]
        )

    def test_upgrade_creates_if_not_exists(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        sub = svc.upgrade_plan(org.id, "starter")
        assert sub.plan == "starter"
        assert sub.status == "active"

    def test_cancel_subscription(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        sub = svc.cancel_subscription(org.id)

        assert sub.status == "canceled"
        assert sub.canceled_at is not None

    def test_trial_expired(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        sub = svc.create_trial(org.id)

        # Manually set trial end to past
        sub.trial_ends_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        db_session.commit()

        assert svc.check_trial_expired(org.id) is True
        db_session.refresh(sub)
        assert sub.status == "expired"

    def test_trial_not_expired(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        assert svc.check_trial_expired(org.id) is False

    def test_has_feature_in_plan(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)

        assert svc.has_feature(org.id, "dashboards") is True
        assert svc.has_feature(org.id, "ai_copilot") is True

    def test_has_feature_not_in_plan(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)

        assert svc.has_feature(org.id, "sso") is False
        assert svc.has_feature(org.id, "white_label") is False

    def test_has_feature_with_flag_override(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)

        # Override: enable sso even though it's not in free_trial
        svc.set_feature_flag(org.id, "sso", True)
        assert svc.has_feature(org.id, "sso") is True

    def test_has_feature_with_flag_disable(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)

        # Override: disable dashboards even though it's in free_trial
        svc.set_feature_flag(org.id, "dashboards", False)
        assert svc.has_feature(org.id, "dashboards") is False

    def test_get_limits(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        limits = svc.get_limits(org.id)

        assert limits["plan"] == "free_trial"
        assert limits["status"] == "trialing"
        assert limits["max_users"] == PLAN_DEFINITIONS["free_trial"]["max_users"]
        assert "dashboards" in limits["features"]

    def test_get_limits_expired(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        sub = svc.create_trial(org.id)

        sub.trial_ends_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        db_session.commit()

        limits = svc.get_limits(org.id)
        assert limits["status"] == "expired"
        assert limits["max_users"] == 1

    def test_get_limits_no_subscription(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        limits = svc.get_limits(org.id)

        # Returns free_trial defaults
        assert limits["max_users"] == PLAN_DEFINITIONS["free_trial"]["max_users"]

    def test_upgrade_to_enterprise(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        sub = svc.upgrade_plan(org.id, "enterprise")

        assert sub.plan == "enterprise"
        assert sub.max_users == 500
        assert "sso" in sub.features
        assert "white_label" in sub.features
        assert "priority_support" in sub.features

    def test_upgrade_to_government(self, db_session):
        org = _create_org(db_session)
        svc = SubscriptionService(db_session)
        svc.create_trial(org.id)
        sub = svc.upgrade_plan(org.id, "government")

        assert sub.plan == "government"
        assert sub.max_users == 1000
        assert "compliance_reports" in sub.features
        assert "data_residency" in sub.features


class TestPlanDefinitions:
    def test_all_plans_have_required_fields(self):
        for _key, plan in PLAN_DEFINITIONS.items():
            assert "name" in plan
            assert "description" in plan
            assert "trial_days" in plan
            assert "max_users" in plan
            assert "max_dashboards" in plan
            assert "max_pipelines" in plan
            assert "max_ai_queries_per_month" in plan
            assert "max_upload_mb" in plan
            assert "features" in plan
            assert isinstance(plan["features"], list)
            assert len(plan["features"]) > 0

    def test_features_are_consistent(self):
        for _key, plan in PLAN_DEFINITIONS.items():
            for feature in plan["features"]:
                assert feature in ALL_FEATURES

    def test_trial_only_for_free_trial(self):
        for _key, plan in PLAN_DEFINITIONS.items():
            if _key == "free_trial":
                assert plan["trial_days"] == 14
            else:
                assert plan["trial_days"] == 0

    def test_limits_increase_with_plan_tier(self):
        plan_keys = ["free_trial", "starter", "professional", "enterprise", "government"]
        for i in range(len(plan_keys) - 1):
            assert (
                PLAN_DEFINITIONS[plan_keys[i]]["max_users"]
                <= PLAN_DEFINITIONS[plan_keys[i + 1]]["max_users"]
            )
            assert (
                PLAN_DEFINITIONS[plan_keys[i]]["max_dashboards"]
                <= PLAN_DEFINITIONS[plan_keys[i + 1]]["max_dashboards"]
            )


class TestSubscriptionAPI:
    def test_list_plans(self, client):
        resp = client.get("/api/saas/plans")
        assert resp.status_code == 200
        data = resp.json()
        data = data.get("data", data)
        assert len(data) == 5
        keys = [p["plan_code"] for p in data]
        assert "free" in keys
        assert "enterprise" in keys

    def test_list_plans_no_auth_required(self, client):
        resp = client.get("/api/saas/plans")
        assert resp.status_code == 200

    def test_get_current_subscription_no_org(self, client, auth_headers):
        resp = client.get("/api/saas/subscription", headers=auth_headers)
        # Super admin may not have org_id
        assert resp.status_code in (200, 400, 403)

    def test_list_all_features(self, client, auth_headers):
        resp = client.get("/api/saas/features", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        data = data.get("data", data)
        assert "enabled" in data
        assert len(data["enabled"]) > 0
