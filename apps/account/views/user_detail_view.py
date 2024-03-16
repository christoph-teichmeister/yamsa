import json

from django.contrib.auth import mixins
from django.views import generic

from apps.account.models import User


class UserDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User

    def dispatch(self, request, *args, **kwargs):
        request_user_shares_room_with_profile_user = request.user.rooms.filter(
            id__in=self.get_object().rooms.values_list("id", flat=True)
        )
        request_user_checks_their_own_profile = request.user.id == kwargs["pk"]

        if not (
            request.user.is_superuser or request_user_shares_room_with_profile_user
        ) and not request_user_checks_their_own_profile:
            # A superuser may see all profiles. If request_user is no superuser, then they may only see their own
            # profile or profiles of users they share a room-connection with
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response["HX-Trigger"] = json.dumps(
            {"notificationsEnabled": self.object.wants_to_receive_webpush_notifications}
        )
        return response
