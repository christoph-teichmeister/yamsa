from collections import defaultdict
from decimal import Decimal
from functools import cached_property

from django.urls import reverse

from apps.debt.models import Debt
from apps.room.dataclasses import RoomBalance, RoomOverviewEntry
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
        rows = (
            Debt.objects.filter_open()
            .filter_involving_user(user_id=self.user.id)
            .aggregate_balance_per_room_and_currency(user_id=self.user.id)
        )

        balances_per_room_id = defaultdict(list)
        for row in rows:
            balance = RoomBalance(
                currency_sign=row["currency_sign"],
                owed_by_user=row["owed_by_user"],
                owed_to_user=row["owed_to_user"],
            )
            if balance.net_amount == Decimal("0"):
                continue
            balances_per_room_id[row["room_id"]].append(balance)

        return balances_per_room_id

    def _build_entry(self, room_values: dict) -> RoomOverviewEntry:
        is_closed = room_values["status"] == Room.StatusChoices.CLOSED
        target_viewname = "room:detail" if is_closed else "transaction:list"

        return RoomOverviewEntry(
            slug=room_values["slug"],
            name=room_values["name"],
            description=room_values["description"],
            status=room_values["status"],
            # Resolved here because room_qs_for_list yields plain dicts, which have no get_status_display().
            status_label=Room.StatusChoices(room_values["status"]).label,
            capitalised_initials=room_values["capitalised_initials"],
            created_by_name=room_values["created_by__name"],
            user_is_in_room=room_values["user_is_in_room"],
            is_closed=is_closed,
            target_url=reverse(target_viewname, kwargs={"room_slug": room_values["slug"]}),
            balances=tuple(self._balances_per_room_id.get(room_values["id"], ())),
        )

    def get_entries(self) -> list[RoomOverviewEntry]:
        return [self._build_entry(room_values) for room_values in self.user.room_qs_for_list]
