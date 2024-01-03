from dateutil.relativedelta import relativedelta
from django.db.models import F, fields, Case, When, Value
from django.utils import timezone
from django.views import generic

from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext


class UserListForRoomView(AccountBaseContext, generic.ListView):
    model = User
    context_object_name = "user_qs_for_room"
    template_name = "account/list.html"

    def get_queryset(self):
        return (
            self.model.objects.filter(rooms__slug=self.request.room.slug)
            .values("name", "id", "is_guest")
            .annotate(
                user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"),
                invitation_email_can_be_sent=Case(
                    When(invitation_email_sent_at__lte=timezone.now() - relativedelta(minutes=5), then=Value(True)),
                    When(invitation_email_sent_at__isnull=True, then=Value(True)),
                    default=Value(False),
                    output_field=fields.BooleanField(),
                ),
            )
            .order_by("user_has_seen_this_room", "name")
        )
