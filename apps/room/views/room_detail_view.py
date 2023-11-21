from django.db.models import F
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.models import Room
from apps.webpush.dataclasses import NotificationPayload
from apps.webpush.services import NotificationSendService


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room

    @context
    @cached_property
    def room_users(self):
        return (
            self.object.userconnectiontoroom_set.all()
            .select_related("user")
            .values("user_has_seen_this_room")
            .annotate(
                name=F("user__name"),
                id=F("user__id"),
                is_guest=F("user__is_guest"),
            )
            .order_by("user_has_seen_this_room", "name")
        )

    @context
    @cached_property
    def preferred_currency_sign(self):
        return self.object.preferred_currency.sign

    @context
    @cached_property
    def currency_signs(self):
        return Currency.objects.all()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        if not self.request.user.is_anonymous:
            connection = self.object.userconnectiontoroom_set.filter(
                user_id=self.request.user.id, user_has_seen_this_room=False
            ).first()
            if connection is not None:
                connection.user_has_seen_this_room = True
                connection.save()

        # TODO CT: Remove this at some point
        notification_service = NotificationSendService()
        notification_service.send_notification_to_user(
            user=self.request.user,
            payload=NotificationPayload(
                head="Debug Notification",
                body="Click me, to go to the welcome page",
                actions=[
                    {
                        "action": "click-me-action",
                        "type": "button",
                        "title": "Go to user profile",
                        "url": reverse(viewname="account-user-detail", kwargs={"pk": self.request.user.id}),
                    },
                ],
                click_url=reverse(viewname="core-welcome"),
            ),
            ttl=1000,
        )

        return response
