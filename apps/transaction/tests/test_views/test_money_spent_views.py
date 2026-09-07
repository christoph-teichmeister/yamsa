import http
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestMoneySpentViews:
    def test_money_spent_on_room_displays_aggregated_context(self, client, room, user, guest_user):
        _, child_transactions = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        expected_total = sum(transaction.value for transaction in child_transactions)

        response = client.get(reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data

        assert context["total_money_spent"], "expected total_money_spent entries"
        total_entry = context["total_money_spent"][0]
        assert total_entry["total_spent"] == expected_total
        assert total_entry["currency_sign"] == room.preferred_currency.sign

        spent_per_person = list(context["money_spent_per_person_qs"])
        covered_per_person = list(context["money_covered_for_person_qs"])

        assert spent_per_person, "expected money_spent_per_person results"
        assert covered_per_person, "expected money_covered_for_person results"

        assert spent_per_person[0]["paid_by_name"] == user.name
        assert spent_per_person[0]["total_spent_per_person"] == expected_total

        assert covered_per_person[0]["paid_for__name"] == guest_user.name
        assert covered_per_person[0]["total_covered_for_person"] == expected_total

    def test_money_spent_trend_view_builds_chart_payload(self, client, room, user, guest_user):
        _, child_transactions = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        expected_total = sum(transaction.value for transaction in child_transactions)

        response = client.get(reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data

        active_period = next(
            (option for option in context["period_options"] if option["key"] == "last-activity"),
            None,
        )
        assert active_period is not None, "expected period option 'last-activity' to be present"
        assert active_period["active"] is True

        assert len(context["trend_series"]) == 1
        series = context["trend_series"][0]
        assert series["currency"] == room.preferred_currency.sign
        assert series["total"] == float(expected_total)
        assert series["points"][0]["value"] == 0.0
        assert series["points"][-1]["value"] == float(expected_total)
        assert context["trend_range_start"] <= context["trend_range_end"]

        chart_data = context["trend_chart_data"]
        assert chart_data["rangeStart"] < chart_data["rangeEnd"]
        assert [entry["currency"] for entry in chart_data["series"]] == [room.preferred_currency.sign]

    def test_money_spent_trend_view_steps_per_transaction_not_per_week(self, client, room, user, guest_user):
        """Regression: weekly buckets collapsed a whole trip into a single jump."""
        now = timezone.now()
        for offset_hours in (5, 4, 3):
            create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user,),
                parent_transaction_kwargs={"paid_at": now - timedelta(hours=offset_hours)},
                child_transaction_kwargs={"value": Decimal("10")},
            )

        response = client.get(
            reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}),
            {"period": "1w"},
        )

        assert response.status_code == http.HTTPStatus.OK
        points = response.context_data["trend_series"][0]["points"]

        # Range start + one step per transaction + range end.
        assert [point["value"] for point in points] == [0.0, 10.0, 20.0, 30.0, 30.0]
        assert [point["delta"] for point in points] == [0.0, 10.0, 10.0, 10.0, 0.0]

    def test_money_spent_trend_view_keeps_currencies_apart(self, client, room, user, guest_user):
        """Regression: same-bucket rows of a second currency silently overwrote the first."""
        now = timezone.now()
        second_currency = CurrencyFactory(sign="Ft")

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"paid_at": now - timedelta(hours=2)},
            child_transaction_kwargs={"value": Decimal("10")},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"paid_at": now - timedelta(hours=1), "currency": second_currency},
            child_transaction_kwargs={"value": Decimal("2500")},
        )

        response = client.get(
            reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}),
            {"period": "1w"},
        )

        assert response.status_code == http.HTTPStatus.OK
        series = response.context_data["trend_series"]

        assert {entry["currency"]: entry["total"] for entry in series} == {
            room.preferred_currency.sign: 10.0,
            "Ft": 2500.0,
        }
        # Totals across currencies are not comparable, so the room's own currency leads.
        assert series[0]["currency"] == room.preferred_currency.sign

    def test_money_spent_trend_view_starts_from_spending_before_the_range(self, client, room, user, guest_user):
        """Regression: the running total restarted at zero whenever the window cut off older expenses."""
        now = timezone.now()
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"paid_at": now - timedelta(weeks=6)},
            child_transaction_kwargs={"value": Decimal("40")},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"paid_at": now - timedelta(hours=1)},
            child_transaction_kwargs={"value": Decimal("10")},
        )

        response = client.get(
            reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}),
            {"period": "1w"},
        )

        assert response.status_code == http.HTTPStatus.OK
        series = response.context_data["trend_series"][0]

        assert series["baseline"] == 40.0
        assert series["points"][0]["value"] == 40.0
        assert series["total"] == 50.0

    def test_money_spent_trend_view_range_matches_the_selected_period(self, client, room, user, guest_user):
        """Regression: the start was snapped back to a Monday, so '7 days' spanned up to 14."""
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        response = client.get(
            reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}),
            {"period": "1w"},
        )

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data

        assert context["trend_range_end"] - context["trend_range_start"] == timedelta(weeks=1)

    def test_money_spent_trend_view_shows_empty_state_without_transactions(self, client, room, user):
        response = client.get(reverse("debt:money-spent-trend", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["trend_series"] == []
        assert "No data available" in response.content.decode()

    def test_money_spent_on_room_omits_self_owed_entries(self, client, room, user, guest_user):
        _, child_transactions = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(user, guest_user),
        )

        response = client.get(reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        covered_per_person = list(response.context_data["money_covered_for_person_qs"])

        assert covered_per_person, "expected money_covered_for_person results"
        assert len(covered_per_person) == 1
        assert covered_per_person[0]["paid_for__name"] == guest_user.name
        assert covered_per_person[0]["total_covered_for_person"] == sum(
            transaction.value for transaction in child_transactions if transaction.paid_for == guest_user
        )

    def test_money_spent_on_room_shows_empty_state_without_transactions(self, client, room, user):
        client.force_login(user)
        response = client.get(reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert "No payments recorded yet" in content
        assert "As soon as someone logs an expense, their share appears here." in content
