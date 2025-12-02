import pytest
from django.urls import reverse

from apps.room.services.dashboard_tab_service import DashboardTabService
from apps.room.tests.factories import RoomFactory


@pytest.mark.django_db
class TestDashboardTabService:
    def test_get_tabs_includes_expected_routes(self):
        room = RoomFactory()
        tabs = DashboardTabService(room).get_tabs_as_list()

        expected_order = ["transaction", "debt", "people", "room"]
        expected_routes = {
            "transaction": ("bi bi-wallet", "transaction:list"),
            "debt": ("bi bi-piggy-bank", "debt:list"),
            "people": ("bi bi-people", "account:list"),
            "room": ("bi bi-gear", "room:detail"),
        }

        assert [tab.name for tab in tabs] == expected_order
        for tab in tabs:
            icon, route_name = expected_routes[tab.name]
            assert tab.icon_class == icon
            assert tab.get_url == reverse(route_name, kwargs={"room_slug": room.slug})
