import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestTransactionListViewFiltering:
    def test_list_view_exposes_active_filter(self, authenticated_client, room, user, guest_user):
        groceries = Category.objects.get(slug="groceries")
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"category": groceries},
        )

        response = authenticated_client.get(
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            data={"category": groceries.slug, "currency": room.preferred_currency.code},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_active"] is True
        assert response.context_data["transaction_filter_category_label"] == str(groceries)
        assert response.context_data["transaction_filter_currency_label"] == room.preferred_currency.code

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        assert soup.select_one("#transaction-active-filters") is not None
        filter_inputs = {
            element["name"]: element["value"] for element in soup.select(".transaction-feed-filters input")
        }
        # The feed is loaded via HTMX, so the filters must be re-sent with every batch request.
        assert filter_inputs == {"category": groceries.slug, "currency": room.preferred_currency.code}

    def test_list_view_wires_the_filters_into_every_feed_request(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(reverse("transaction:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        soup = BeautifulSoup(response.content.decode(), "html.parser")

        # Without this the filter is dropped as soon as the user types in the search field.
        assert soup.select_one("#transaction-search")["hx-include"] == ".transaction-feed-filters"
        assert soup.select_one("#transaction-table-body")["hx-include"] == (
            "#transaction-search, .transaction-feed-filters"
        )
        # The wrapper is rendered even unfiltered: htmx logs a console error for an hx-include
        # selector that matches nothing, and unfiltered is the common case.
        assert soup.select_one(".transaction-feed-filters") is not None
        assert soup.select(".transaction-feed-filters input") == []

    def test_list_view_without_filter_renders_no_filter_chip(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(reverse("transaction:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_active"] is False

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        assert soup.select_one("#transaction-active-filters") is None

    def test_list_view_ignores_a_category_from_another_room(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user)
        foreign_category = (
            RoomCategoryService(room=other_room)
            .create_room_category(name="Sauna evenings", emoji="🧖", color="#123456")
            .category
        )
        # The foreign category needs a transaction of its own, otherwise it is out of every room's
        # scope and the test would pass for the wrong reason.
        create_parent_transaction_with_optimisation(
            room=other_room,
            paid_by=user,
            paid_for_tuple=(user,),
            parent_transaction_kwargs={"category": foreign_category},
        )

        response = authenticated_client.get(
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            data={"category": foreign_category.slug},
        )

        assert response.status_code == http.HTTPStatus.OK
        # The chip must not name a category this room cannot see - it falls back to the raw slug.
        assert response.context_data["transaction_filter_category_label"] == foreign_category.slug
        assert str(foreign_category) not in response.content.decode()

    def test_list_view_falls_back_to_raw_value_for_unknown_category(self, authenticated_client, room, user):
        response = authenticated_client.get(
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            data={"category": "does-not-exist"},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["transaction_filter_category_label"] == "does-not-exist"
