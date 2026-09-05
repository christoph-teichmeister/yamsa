from functools import cached_property

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.room.dataclasses import RoomOverviewEntry
from apps.room.services.room_overview_service import RoomOverviewService


class WelcomePartialView(generic.TemplateView):
    """Dashboard: the rooms the user is part of, with their open balance."""

    template_name = "core/_welcome.html"

    # Superusers see every room of the instance through Room.objects.visible_for(). Those are
    # not their rooms and carry no balance, so the dashboard shows a sample rather than a list
    # that grows with the database.
    OTHER_ROOM_LIMIT = 10

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
        return [entry for entry in self._room_entries if entry.user_is_in_room and not entry.is_closed]

    @context
    @property
    def closed_room_entries(self) -> list[RoomOverviewEntry]:
        return [entry for entry in self._room_entries if entry.user_is_in_room and entry.is_closed]

    @context
    @property
    def other_room_entries(self) -> list[RoomOverviewEntry]:
        return self._foreign_room_entries[: self.OTHER_ROOM_LIMIT]

    @context
    @property
    def other_room_overflow_count(self) -> int:
        return max(0, len(self._foreign_room_entries) - self.OTHER_ROOM_LIMIT)

    @cached_property
    def _foreign_room_entries(self) -> list[RoomOverviewEntry]:
        return [entry for entry in self._room_entries if not entry.user_is_in_room]

    @context
    @property
    def has_room_entries(self) -> bool:
        return bool(self._room_entries)
