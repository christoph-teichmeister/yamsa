from dateutil.relativedelta import relativedelta
from django.db.models import Case, F, QuerySet, Value, When, fields
from django.utils import timezone


class UserQuerySet(QuerySet):
    def get_for_room_slug(self, room_slug: str) -> QuerySet:
        return self.filter(rooms__slug=room_slug)

    def annotate_user_has_seen_this_room(self) -> QuerySet:
        # TODO CT: Test this. How does this know, _which_ room to look at?
        return self.annotate(user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"))

    def annotate_invitation_email_can_be_sent(self) -> QuerySet:
        return self.annotate(
            invitation_email_can_be_sent=Case(
                When(invitation_email_sent_at__lte=timezone.now() - relativedelta(minutes=5), then=Value(True)),
                When(invitation_email_sent_at__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=fields.BooleanField(),
            ),
        )
