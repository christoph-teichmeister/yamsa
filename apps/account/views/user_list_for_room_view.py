from django.db.models import QuerySet
from django.views import generic

from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.room.views.mixins import RoomMembershipRequiredMixin


class UserListForRoomView(RoomMembershipRequiredMixin, AccountBaseContext, generic.ListView):
    model = User
    context_object_name = "user_qs_for_room"
    template_name = "account/list.html"

    def get_queryset(self) -> QuerySet:
        return (
            self.model.objects.get_for_room_slug(room_slug=self.request.room.slug)
            .annotate_user_has_seen_this_room(room_id=self.request.room.id)
            .annotate_invitation_email_can_be_sent()
            .order_by("user_has_seen_this_room", "name")
        )

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context["is_member"] = self.request.room.users.filter(pk=self.request.user.pk).exists()
        return context
