import http

import pytest
from django.urls import reverse

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
        owed_per_person = list(context["money_owed_per_person_qs"])

        assert spent_per_person, "expected money_spent_per_person results"
        assert owed_per_person, "expected money_owed_per_person results"

        assert spent_per_person[0]["paid_by_name"] == user.name
        assert spent_per_person[0]["total_spent_per_person"] == expected_total

        assert owed_per_person[0]["paid_for__name"] == guest_user.name
        assert owed_per_person[0]["total_owed_per_person"] == expected_total

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

        assert context["trend_currency_sign"] == room.preferred_currency.sign
        assert context["timeseries"]
        assert context["trend_chart_points"], "expected non-empty trend_chart_points"
        assert float(context["timeseries_max_value"]) == float(expected_total)
        assert context["trend_chart_points"][-1]["value"] == float(context["timeseries_max_value"])
        assert context["trend_range_start"] <= context["trend_range_end"]

    def test_money_spent_on_room_omits_self_owed_entries(self, client, room, user, guest_user):
        _, child_transactions = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(user, guest_user),
        )

        response = client.get(reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        owed_per_person = list(response.context_data["money_owed_per_person_qs"])

        assert owed_per_person, "expected money_owed_per_person results"
        assert len(owed_per_person) == 1
        assert owed_per_person[0]["paid_for__name"] == guest_user.name
        assert owed_per_person[0]["total_owed_per_person"] == sum(
            transaction.value for transaction in child_transactions if transaction.paid_for == guest_user
        )
