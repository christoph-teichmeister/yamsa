from urllib.parse import urlparse

import pytest
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.utils.notification_preferences import build_payment_reminder_unsubscribe_url
from e2e.pages.unsubscribe_page import UnsubscribePage


@pytest.mark.e2e
class TestUnsubscribe:
    def test_opening_the_link_only_asks_and_confirming_unsubscribes(
        self, page: Page, base_url: str, profile_user: User
    ) -> None:
        url = urlparse(build_payment_reminder_unsubscribe_url(profile_user))
        unsubscribe_page = UnsubscribePage(page, base_url, f"{url.path}?{url.query}")

        unsubscribe_page.navigate()

        unsubscribe_page.expect_confirmation()
        profile_user.refresh_from_db()
        assert profile_user.wants_to_receive_payment_reminders

        unsubscribe_page.confirm()

        unsubscribe_page.expect_unsubscribed()
        profile_user.refresh_from_db()
        assert not profile_user.wants_to_receive_payment_reminders
