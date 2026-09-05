import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.transaction.models import Category
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestTransactionListViewFiltering:
    def test_list_view_exposes_active_filter(self, authenticated_client, room, user, guest_user):
        groceries = Category.objects.get(slug="groceries")
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            data={"category": groceries.slug, "currency": room.preferred_currency.code},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_active"] is True
        assert response.context_data["transaction_filter_category"] == groceries
        assert response.context_data["transaction_filter_currency"] == room.preferred_currency

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        assert soup.select_one("#transaction-active-filters") is not None
        filter_inputs = {
            element["name"]: element["value"] for element in soup.select(".transaction-feed-filters input")
        }
        # The feed is loaded via HTMX, so the filters must be re-sent with every batch request.
        assert filter_inputs == {"category": groceries.slug, "currency": room.preferred_currency.code}

    def test_list_view_without_filter_renders_no_filter_chip(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(reverse("transaction:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_active"] is False

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        assert soup.select_one("#transaction-active-filters") is None

    def test_list_view_falls_back_to_raw_value_for_unknown_category(self, authenticated_client, room, user):
        response = authenticated_client.get(
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            data={"category": "does-not-exist"},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_category"] is None
        assert response.context_data["transaction_filter_category_label"] == "does-not-exist"
