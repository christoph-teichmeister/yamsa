from collections.abc import Callable

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import UserFactory
from apps.currency.models import Currency
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.conftest import _login
from e2e.pages.room_insights_page import RoomInsightsPage

CATEGORIES = (
    ("groceries", "Groceries", "🛒"),
    ("restaurants-and-bars", "Restaurants & Bars", "🍽️"),
    ("activities", "Activities", "🎟️"),
)


@pytest.fixture
def euro(transactional_db: None) -> Currency:
    return CurrencyFactory(code="EUR", sign="€", name="Euro")


@pytest.fixture
def franc(transactional_db: None) -> Currency:
    return CurrencyFactory(code="CHF", sign="Fr", name="Swiss franc")


@pytest.fixture
def people(transactional_db: None) -> tuple[User, User, User]:
    # Fixed names: the lists on "Who paid what" are ordered by name, and the assertions read them
    # in that order.
    return UserFactory(name="Alex"), UserFactory(name="Bea"), UserFactory(name="Chris")


@pytest.fixture
def spending_room(people: tuple[User, User, User], euro: Currency, franc: Currency) -> Room:
    """Three expenses across two currencies and three categories.

    EUR: Alex pays 1,200.00 split three ways, Bea pays 30.00 split with Alex. That leaves Chris
    owing Alex 400.00 and Bea owing Alex 385.00 once the debts are optimised.
    CHF: Chris pays 10.00 for Bea alone.
    """
    alex, bea, chris = people
    room = RoomFactory(created_by=alex, preferred_currency=euro)
    room.users.add(alex, bea, chris)
    categories = {
        slug: Category.objects.get_or_create(
            slug=slug, defaults={"name": name, "emoji": emoji, "order_index": order_index}
        )[0]
        for order_index, (slug, name, emoji) in enumerate(CATEGORIES)
    }

    def expense(
        paid_by: User,
        currency: Currency,
        category_slug: str,
        description: str,
        shares: list[tuple[User, str]],
    ) -> None:
        parent_transaction = ParentTransactionFactory(
            room=room,
            paid_by=paid_by,
            currency=currency,
            category=categories[category_slug],
            description=description,
        )
        for participant, value in shares:
            ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=participant, value=value)

    expense(alex, euro, "groceries", "Großeinkauf", [(alex, "400.00"), (bea, "400.00"), (chris, "400.00")])
    expense(bea, euro, "restaurants-and-bars", "Pizza", [(alex, "15.00"), (bea, "15.00")])
    expense(chris, franc, "activities", "Museum", [(bea, "10.00")])
    DebtOptimiseService.process(room_id=room.id)
    # live_server reads from its own thread, and on SQLite this connection would hold the rows.
    connection.close()
    return room


@pytest.fixture
def open_insights(page: Page, base_url: str, people: tuple[User, User, User], spending_room: Room) -> Callable:
    def _open(view_name: str) -> RoomInsightsPage:
        _login(page, base_url, people[0].email, DEFAULT_PASSWORD)
        insights_page = RoomInsightsPage(page, base_url, reverse(view_name, kwargs={"room_slug": spending_room.slug}))
        insights_page.navigate()
        return insights_page

    return _open
