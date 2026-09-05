from functools import cached_property

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.room.dataclasses import RoomOverviewEntry
from apps.room.services.room_overview_service import RoomOverviewService


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))
        return super().get(request, *args, **kwargs)

    @cached_property
    def _room_entries(self) -> list[RoomOverviewEntry]:
        if self.request.user.is_anonymous:
            return []
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
        return [entry for entry in self._room_entries if not entry.user_is_in_room]

    @context
    @property
    def has_room_entries(self) -> bool:
        return bool(self._room_entries)
