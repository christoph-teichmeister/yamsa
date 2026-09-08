from django.http import JsonResponse
from django.urls import reverse
from django.views import generic

from apps.room.services.dashboard_tab_service import DashboardTabService
from apps.room.views.mixins import RoomMembershipRequiredMixin


class RoomOfflineManifestView(RoomMembershipRequiredMixin, generic.View):
    """List the URLs a client warms so this room stays usable without a connection.

    The dashboard tabs are most of that list: they are the room's destinations, each a plain read
    that renders the same document whether htmx asked for it or the address bar did, which is what
    lets one cached copy serve both. Taken from the service the navigation itself uses rather than
    written out again, so a tab that moves cannot leave the offline cache behind.

    The expense form is the one page here that is not a tab. It has to be cached all the same: a
    queue for expenses entered in a dead spot is worth nothing if the form to enter them in cannot
    be opened there.
    """

    def get(self, request, *args, **kwargs):
        room_slug = request.room.slug
        urls = [tab.get_url for tab in DashboardTabService(room=request.room).get_tabs_as_list()]
        urls.append(reverse("transaction:create", kwargs={"room_slug": room_slug}))

        return JsonResponse(
            {
                # A UUID field, and the client compares it against the slug in its own URLs.
                "room": str(room_slug),
                "urls": urls,
            }
        )
