from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.dashboard_context import DashboardBaseContext


class RoomDashboardView(DashboardBaseContext, generic.DetailView):
    # Deliberately open to non-members: the template shows them only the guest "Who are you?" picker,
    # which is how invited guests without a password get in. RoomShareView inherits this.
    template_name = "room/dashboard.html"
    slug_url_kwarg = "room_slug"
    model = Room
