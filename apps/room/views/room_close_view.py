from django.views import generic
from django_context_decorator import context
from functools import cached_property

from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin


class RoomCloseView(RoomSpecificMixin, generic.TemplateView):
    # TODO CT: Ja weiß ja nicht
    http_method_names = ["post", "options"]
    template_name = "room/detail.html"

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "settings")

    def post(self, request, *args, **kwargs):
        response = super().get(self, request, *args, **kwargs)

        if self.room.can_be_closed:
            return response
        else:
            return response

