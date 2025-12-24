from django.views import generic

from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext


class UserListForRoomView(AccountBaseContext, generic.ListView):
    model = User
    context_object_name = "user_qs_for_room"
    template_name = "account/list.html"

    def get_queryset(self):
        return (
            self.model.objects.get_for_room_slug(room_slug=self.request.room.slug)
            .annotate_user_has_seen_this_room(room_id=self.request.room.id)
            .annotate_invitation_email_can_be_sent()
            .order_by("user_has_seen_this_room", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        room = getattr(request, "room", None)
        is_member = False
        if room and request.user.is_authenticated:
            is_member = room.users.filter(pk=request.user.pk).exists()

        context["is_member"] = is_member
        return context
