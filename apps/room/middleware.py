from django.urls import get_resolver

from apps.room.models import Room


class RoomToRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before the view (and later middleware) are called.

        resolver_match = get_resolver().resolve(request.path_info)

        if (room_slug := resolver_match.kwargs.get("room_slug")) is not None:
            setattr(request, "room", Room.objects.get(slug=room_slug))

        response = self.get_response(request)

        # Code to be executed for each request/response after the view is called.

        return response
