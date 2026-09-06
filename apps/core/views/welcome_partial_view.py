from functools import cached_property

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.room.dataclasses import CurrencyTotal, RoomOverviewEntry
from apps.room.services.room_overview_service import RoomOverviewService


class WelcomePartialView(generic.TemplateView):
    """Dashboard: the rooms the user is part of, with their open balance."""

    template_name = "core/_welcome.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))
        return super().get(request, *args, **kwargs)

    @cached_property
    def _room_entries(self) -> list[RoomOverviewEntry]:
        return RoomOverviewService(user=self.request.user).get_entries()

    @context
    @property
    def open_room_entries(self) -> list[RoomOverviewEntry]:
        """Open rooms, the most recently used one first."""
        entries = [entry for entry in self._room_entries if entry.user_is_in_room and not entry.is_closed]
        return RoomOverviewService.sorted_by_last_activity(entries)

    @context
    @property
    def open_balance_totals(self) -> list[CurrencyTotal]:
        return RoomOverviewService.currency_totals_for(self.open_room_entries)

    @context
    @property
    def closed_room_entries(self) -> list[RoomOverviewEntry]:
        entries = [entry for entry in self._room_entries if entry.user_is_in_room and entry.is_closed]
        return RoomOverviewService.sorted_by_last_activity(entries)

    @context
    @property
    def other_room_entries(self) -> list[RoomOverviewEntry]:
        """Every room of the instance a superuser can see but is not a member of.

        Uncapped on purpose: the section is collapsed until it is clicked, and the rooms are
        loaded either way - a cap would only hide rooms from the one user meant to see them all.
        """
        entries = [entry for entry in self._room_entries if not entry.user_is_in_room]
        return RoomOverviewService.sorted_by_last_activity(entries)

    @context
    @property
    def has_room_entries(self) -> bool:
        return bool(self._room_entries)
