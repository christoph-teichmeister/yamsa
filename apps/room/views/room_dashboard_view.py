from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.dashboard_base_context import DashboardBaseContext


class RoomDashboardView(DashboardBaseContext, generic.DetailView):
    template_name = "room/dashboard.html"
    slug_url_kwarg = "room_slug"
    model = Room
