from collections.abc import Callable, Iterator

import pytest
from django.db import connection
from playwright.sync_api import Page

from apps.core.event_loop.registry import message_registry
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ParentTransaction
from e2e.tests.transaction.conftest import GROCERIES


def _failing_notification_handler(_context: object) -> None:
    msg = "push service is down"
    raise RuntimeError(msg)


@pytest.fixture
def failing_handler_ahead_of_debts() -> Iterator[None]:
    handlers = message_registry.event_dict[ParentTransactionCreated]
    handlers.insert(0, _failing_notification_handler)
    yield
    handlers.remove(_failing_notification_handler)


@pytest.mark.e2e
@pytest.mark.expects_htmx_errors
class TestTransactionFailingHandler:
    def test_a_failing_handler_does_not_stop_the_debt_recalculation(
        self, open_create_form: Callable, failing_handler_ahead_of_debts: None, room: Room, page: Page
    ) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Kino am Freitag", amount="24.00")
        create_page.choose_category(GROCERIES)

        with page.expect_response(lambda response: response.request.method == "POST"):
            create_page.submit()

        # The failure is still reported (the request errors), but it came after every handler ran.
        connection.close()
        assert ParentTransaction.objects.filter(room=room, description="Kino am Freitag").exists()
        assert Debt.objects.filter(room=room).exists()
