import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.room.tests.factories import RoomFactory
from e2e.conftest import _login
from e2e.pages.debt_list_page import DebtListPage
from e2e.pages.room_insights_page import RoomInsightsPage


@pytest.mark.e2e
class TestCategoryBreakdown:
    def test_the_debt_list_leads_there(self, page, base_url, people, spending_room):
        _login(page, base_url, people[0].email, DEFAULT_PASSWORD)
        DebtListPage(page, base_url, reverse("debt:list", kwargs={"room_slug": spending_room.slug})).navigate()

        page.get_by_role("button", name="Category breakdown").click()

        page.wait_for_url(
            lambda url: url.endswith(
                reverse("transaction:category-breakdown", kwargs={"room_slug": spending_room.slug})
            )
        )
        expect(page.get_by_role("heading", name="All recorded spend")).to_be_visible()

    def test_each_currency_lists_its_categories_by_amount(self, open_insights):
        insights_page = open_insights("transaction:category-breakdown")

        assert insights_page.legend_items("EUR") == [("Groceries", "1,200.00€"), ("Restaurants & Bars", "30.00€")]
        assert insights_page.legend_items("CHF") == [("Activities", "10.00Fr")]

    def test_each_currency_gets_a_donut_with_a_slice_per_category(self, open_insights, page):
        open_insights("transaction:category-breakdown")

        eur_chart = page.locator('[data-category-breakdown="EUR"] [data-transaction-category-chart]')
        expect(eur_chart.get_by_role("button", name="🛒 Groceries: 1,200.00€")).to_be_visible()
        expect(eur_chart.get_by_role("button", name="🍽️ Restaurants & Bars: 30.00€")).to_be_visible()

    def test_a_legend_entry_opens_the_list_filtered_to_its_category(self, open_insights, page, spending_room):
        insights_page = open_insights("transaction:category-breakdown")

        insights_page.open_legend_entry("EUR", "groceries")

        list_path = reverse("transaction:list", kwargs={"room_slug": spending_room.slug})
        page.wait_for_url(lambda url: list_path in url and "category=groceries" in url and "currency=EUR" in url)
        expect(page.get_by_text("Großeinkauf")).to_be_visible()
        expect(page.get_by_text("Pizza")).to_have_count(0)

    def test_a_room_without_expenses_says_so(self, page, base_url, people, euro):
        room = RoomFactory(created_by=people[0], preferred_currency=euro)
        room.users.add(people[0])
        connection.close()
        _login(page, base_url, people[0].email, DEFAULT_PASSWORD)

        RoomInsightsPage(
            page, base_url, reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug})
        ).navigate()

        expect(page.get_by_text("No tracked expenses yet.")).to_be_visible()
