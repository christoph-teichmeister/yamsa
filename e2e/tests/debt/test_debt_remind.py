import os
from collections.abc import Callable

import pytest
from playwright.sync_api import Page, expect

from apps.account.models import User
from apps.debt.models import Debt, ReminderLog

# Screenshots for manual review are opt-in so a normal run writes nothing.
SHOT_DIR = os.environ.get("YAMSA_E2E_SHOT_DIR")


def _shoot(page: Page, name: str) -> None:
    if not SHOT_DIR:
        return
    page.set_viewport_size({"width": 390, "height": 800})
    for scheme in ("light", "dark"):
        page.emulate_media(color_scheme=scheme)
        page.screenshot(path=f"{SHOT_DIR}/{name}-{scheme}.png")


@pytest.mark.e2e
class TestDebtRemind:
    def test_the_creditor_reminds_once_and_sees_when_the_next_one_is_possible(
        self, debt_list_as: Callable, page: Page, profile_user: User, open_debt: Debt
    ) -> None:
        debt_list_as(profile_user)

        page.get_by_role("button", name="Send reminder").click()

        expect(page.locator("#toast-message-span")).to_contain_text("has been reminded")
        expect(page.get_by_role("button", name="Reminder sent")).to_be_disabled()
        expect(page.get_by_text("Next reminder possible at")).to_be_visible()
        assert ReminderLog.objects.filter(reminder_type=ReminderLog.ReminderType.MANUAL_DEBT).count() == 1
        _shoot(page, "remind-sent")

    def test_the_debtor_gets_no_remind_button(self, debt_list_as: Callable, page: Page, roommate: User) -> None:
        debt_list_as(roommate)

        expect(page.get_by_role("button", name="Send reminder")).to_have_count(0)

    def test_the_button_is_a_comfortable_tap_target(
        self, debt_list_as: Callable, page: Page, profile_user: User
    ) -> None:
        debt_list_as(profile_user)
        page.set_viewport_size({"width": 390, "height": 800})

        box = page.get_by_role("button", name="Send reminder").bounding_box()

        assert box["height"] >= 44
        _shoot(page, "remind-open")
