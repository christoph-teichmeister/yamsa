from django.http import JsonResponse
from django.views import generic

from apps.room.services.dashboard_tab_service import DashboardTabService
from apps.room.views.mixins import RoomMembershipRequiredMixin


class RoomOfflineManifestView(RoomMembershipRequiredMixin, generic.View):
    """List the URLs a client warms so this room stays readable without a connection.

    The dashboard tabs are that list: they are the room's four destinations, each a plain read that
    renders the same document whether htmx asked for it or the address bar did, which is what lets
    one cached copy serve both. Taken from the service the navigation itself uses rather than
    written out again, so a tab that moves cannot leave the offline cache behind.
    """

    def get(self, request, *args, **kwargs):
        tabs = DashboardTabService(room=request.room).get_tabs_as_list()

        return JsonResponse(
            {
                # A UUID field, and the client compares it against the slug in its own URLs.
                "room": str(request.room.slug),
                "urls": [tab.get_url for tab in tabs],
            }
        )
