from apps.room.models import Room


class RoomToRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        cleaned_path_list = list(filter(lambda split_content: split_content != "", request.path.split("/")))
        if "room" in cleaned_path_list:
            room_slug = cleaned_path_list[1]
            setattr(request, "room", Room.objects.get(slug=room_slug))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
