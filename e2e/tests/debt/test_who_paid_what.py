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
class TestWhoPaidWhat:
    def test_the_debt_list_leads_there_and_back(self, page, base_url, people, spending_room):
        _login(page, base_url, people[0].email, DEFAULT_PASSWORD)
        debt_list_path = reverse("debt:list", kwargs={"room_slug": spending_room.slug})
        DebtListPage(page, base_url, debt_list_path).navigate()

        page.get_by_role("button", name="Who paid what").click()
        page.wait_for_url(
            lambda url: url.endswith(reverse("debt:money-spent-on-room", kwargs={"room_slug": spending_room.slug}))
        )
        expect(page.get_by_role("heading", name="Who paid what")).to_be_visible()

        page.get_by_role("button", name="Back to debts").click()
        page.wait_for_url(lambda url: url.endswith(debt_list_path))

    def test_each_currency_gets_its_own_total(self, open_insights):
        insights_page = open_insights("debt:money-spent-on-room")

        expect(insights_page.total_spent("€")).to_have_text("1,230.00")
        expect(insights_page.total_spent("Fr")).to_have_text("10.00")

    def test_the_payers_are_listed_with_what_they_laid_out(self, open_insights):
        insights_page = open_insights("debt:money-spent-on-room")

        insights_page.expect_rows("spent", [("Alex", "1,200.00 €"), ("Bea", "30.00 €"), ("Chris", "10.00 Fr")])

    def test_the_open_debts_are_the_optimised_ones(self, open_insights):
        insights_page = open_insights("debt:money-spent-on-room")

        insights_page.expect_rows("owed", [("Bea", "385.00 €"), ("Bea", "10.00 Fr"), ("Chris", "400.00 €")])

    def test_what_others_covered_leaves_out_the_own_share(self, open_insights):
        insights_page = open_insights("debt:money-spent-on-room")

        insights_page.expect_rows(
            "covered", [("Alex", "15.00 €"), ("Bea", "400.00 €"), ("Bea", "10.00 Fr"), ("Chris", "400.00 €")]
        )

    def test_the_spending_trend_is_drawn_per_currency(self, open_insights):
        insights_page = open_insights("debt:money-spent-on-room")

        insights_page.reveal_trend()
        expect(insights_page.trend.locator("#trend-line-chart svg")).to_have_count(2)
        expect(insights_page.trend_range("Last activity")).to_have_attribute("aria-pressed", "true")

    def test_another_range_is_loaded_in_place(self, open_insights, page):
        insights_page = open_insights("debt:money-spent-on-room")
        insights_page.reveal_trend()
        page_url = page.url

        insights_page.choose_trend_range("4w")

        expect(insights_page.trend_range("4w")).to_have_attribute("aria-pressed", "true")
        expect(insights_page.trend_range("Last activity")).to_have_attribute("aria-pressed", "false")
        expect(insights_page.trend.get_by_text("Showing last 4 weeks")).to_be_visible()
        expect(insights_page.trend.locator("#trend-line-chart svg")).to_have_count(2)
        assert page.url == page_url

    def test_the_transactions_tab_still_loads_its_list_from_here(self, open_insights, page):
        # This page's own inline script used to be morphed into the list's, which then never ran
        # and left the feed on its skeleton.
        open_insights("debt:money-spent-on-room")

        page.locator("#transaction-tab").click()

        expect(page.locator("#transaction-feed").get_by_text("Großeinkauf")).to_be_visible()

    def test_a_room_without_expenses_shows_empty_states(self, page, base_url, people, euro):
        room = RoomFactory(created_by=people[0], preferred_currency=euro)
        room.users.add(people[0])
        connection.close()
        _login(page, base_url, people[0].email, DEFAULT_PASSWORD)

        RoomInsightsPage(
            page, base_url, reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug})
        ).navigate()

        expect(page.get_by_text("No spending yet")).to_be_visible()
        expect(page.get_by_text("No payments recorded yet")).to_be_visible()
        expect(page.get_by_text("Nothing owed right now")).to_be_visible()
        page.locator("#spending-trend").scroll_into_view_if_needed()
        expect(page.get_by_text("No data available")).to_be_visible()
