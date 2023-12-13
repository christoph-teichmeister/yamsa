from apps.room.models import Room


class RoomToRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        slug_field = filter(lambda field: field.attname == "slug", Room._meta.fields).__next__()

        # TODO CT: Why are the auto-generated slugs not 32 long but 36 instead?

        cleaned_path_list = list(
            filter(lambda split_content: len(split_content) == slug_field.max_length + 4, request.path.split("/"))
        )
        if len(cleaned_path_list) != 0:
            room_slug = cleaned_path_list[0]
            setattr(request, "room", Room.objects.get(slug=room_slug))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
