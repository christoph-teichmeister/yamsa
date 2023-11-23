from django.utils.functional import cached_property
from django_context_decorator import context

from apps.account.models import User
from apps.room.models import Room


class RoomSpecificMixin:
    _room = None

    def dispatch(self, request, *args, **kwargs):
        # Set room here, so that only one query is made and room is accessible throughout the other methods
        self._room = Room.objects.get(slug=self.kwargs.get("room_slug"))
        return super().dispatch(request, *args, **kwargs)

    @context
    @cached_property
    def room(self):
        return self._room

    @context
    @cached_property
    def room_users(self):
        # TODO CT: Look for this and replace
        return User.objects.filter(room=self._room)
