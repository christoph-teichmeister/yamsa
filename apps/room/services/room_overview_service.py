from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from functools import cached_property

from django.urls import reverse

from apps.debt.models import Debt
from apps.room.dataclasses import CurrencyTotal, RoomBalance, RoomOverviewEntry
from apps.room.models import Room


class RoomOverviewService:
    """Build the dashboard room cards in two queries, independent of the number of rooms.

    The balances cannot be annotated onto ``User.room_qs_for_list``: that queryset orders by
    ``last_activity``, itself an aggregate, so an added Sum() would join the GROUP BY and split
    each room across several rows.
    """

    def __init__(self, *, user) -> None:
        self.user = user

    @cached_property
    def _balances_per_room_id(self) -> dict[int, list[RoomBalance]]:
        # Closed rooms are excluded here rather than when the card is built: their tile shows no
        # balance and they are left out of the totals, so their debts are rows nobody reads.
        rows = (
            Debt.objects.filter_open()
            .filter_involving_user(user_id=self.user.id)
            .exclude(room__status=Room.StatusChoices.CLOSED)
            .aggregate_balance_per_room_and_currency(user_id=self.user.id)
        )

        balances_per_room_id = defaultdict(list)
        for row in rows:
            # A row that nets to zero is kept: its debts are still open and payable, and an
            # empty balance list is what tells the card that nothing is owed at all.
            balances_per_room_id[row["room_id"]].append(
                RoomBalance(
                    currency_id=row["currency_id"],
                    currency_sign=row["currency_sign"],
                    owed_by_user=row["owed_by_user"],
                    owed_to_user=row["owed_to_user"],
                )
            )

        return balances_per_room_id

    def _build_entry(self, room_values: dict) -> RoomOverviewEntry:
        is_closed = room_values["status"] == Room.StatusChoices.CLOSED
        target_viewname = Room.dashboard_viewname_for(room_values["status"])

        return RoomOverviewEntry(
            slug=room_values["slug"],
            name=room_values["name"],
            description=room_values["description"],
            status_label=Room.status_label_for(room_values["status"]),
            capitalised_initials=room_values["capitalised_initials"],
            created_by_name=room_values["created_by__name"],
            user_is_in_room=room_values["user_is_in_room"],
            is_closed=is_closed,
            target_url=reverse(target_viewname, kwargs={"room_slug": room_values["slug"]}),
            last_activity_at=room_values["last_activity"],
            last_transaction_at=room_values["last_transaction_at"],
            balances=tuple(self._balances_per_room_id.get(room_values["id"], ())),
        )

    def get_entries(self) -> list[RoomOverviewEntry]:
        """Return one entry per visible room, in room_qs_for_list's order (most recently active first)."""
        return [self._build_entry(room_values) for room_values in self.user.room_qs_for_list]

    @staticmethod
    def sorted_by_last_activity(entries: Iterable[RoomOverviewEntry]) -> list[RoomOverviewEntry]:
        """Order rooms by when they were last used, newest first.

        Ties keep the order they came in, sorted() being stable even in reverse.
        """
        return sorted(entries, key=lambda entry: entry.last_activity_at, reverse=True)

    @staticmethod
    def currency_totals_for(entries: Iterable[RoomOverviewEntry]) -> list[CurrencyTotal]:
        """Sum the given entries' balances into one CurrencyTotal per currency, largest first.

        Takes entries instead of querying, so the caller decides which rooms count and the
        totals cost no extra query. Only each room's net side is added up, and the two
        directions stay apart: a debt the user owes in one room is not cancelled by a debt
        owed to them in another, because different people are on the other end.
        """
        owed_by_user: dict[int, Decimal] = defaultdict(Decimal)
        owed_to_user: dict[int, Decimal] = defaultdict(Decimal)
        signs: dict[int, str] = {}

        for entry in entries:
            for balance in entry.balances:
                signs.setdefault(balance.currency_id, balance.currency_sign)
                if balance.user_owes:
                    owed_by_user[balance.currency_id] += balance.absolute_amount
                elif balance.user_gets_back:
                    owed_to_user[balance.currency_id] += balance.absolute_amount

        totals = [
            CurrencyTotal(
                currency_id=currency_id,
                currency_sign=sign,
                owed_by_user=owed_by_user[currency_id],
                owed_to_user=owed_to_user[currency_id],
            )
            for currency_id, sign in signs.items()
            if owed_by_user[currency_id] or owed_to_user[currency_id]
        ]

        # Ordering only, so comparing amounts across currencies is fine here; currency_id breaks
        # ties so two currencies sharing a sign keep a stable order.
        return sorted(totals, key=lambda total: (-total.owed_by_user, -total.owed_to_user, total.currency_id))
