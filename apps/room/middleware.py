from django.urls import get_resolver

from apps.room.models import Room


class RoomToRequestMiddleware:
    def __init__(self, get_response):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before the view (and later middleware) are called.

        resolver_match = get_resolver().resolve(request.path_info)

        # If the request tries to access a room...
        if (room_slug := resolver_match.kwargs.get("room_slug")) is not None:
            # ...add room to the request
            room = Room.objects.get(slug=room_slug)
            request.room = room

            if not request.user.is_anonymous:
                # ...check whether the DB knows that the user has seen the room
                connection, has_seen_room = request.user.has_seen_room(room)

                request_user_is_superuser_and_does_not_belong_to_room = (
                        connection is None and request.user.is_superuser
                )
                if not request_user_is_superuser_and_does_not_belong_to_room and not has_seen_room:
                    connection.user_has_seen_this_room = True
                    connection.save()

        response = self.get_response(request)

        # Code to be executed for each request/response after the view is called.

        return response
