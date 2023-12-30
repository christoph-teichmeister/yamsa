from functools import cached_property
from time import time

from ambient_toolbox.mixins.validation import CleanOnSaveMixin
from ambient_toolbox.models import CommonInfo
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, ExpressionWrapper, Exists, OuterRef, BooleanField

from apps.room.models import Room


class User(CleanOnSaveMixin, CommonInfo, AbstractUser):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    rooms = models.ManyToManyField("room.Room", through="room.UserConnectionToRoom")

    is_guest = models.BooleanField(default=True)

    paypal_me_username = models.CharField(max_length=100, null=True, blank=True)

    wants_to_receive_webpush_notifications = models.BooleanField(default=True)

    invitation_email_sent = models.BooleanField(default=False)
    invitation_email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_guest and not self.is_superuser:
            # If a user has been added and is a guest, give them unique username, email and password
            timestamp = time()
            self.username = f"{self.name}-{timestamp}"
            self.email = f"{self.username}@local.local"
            self.password = f"{self.name}-{timestamp}"

        super().clean()

    def can_be_removed_from_room(self, room_id) -> bool:
        return not (
            Room.objects.filter(
                Q(parent_transactions__paid_by_id=self.id)
                | Q(parent_transactions__child_transactions__paid_for_id=self.id)
                | Q(debts__debitor_id=self.id)
                | Q(debts__creditor_id=self.id),
                id=room_id,
            )
            .distinct()
            .exists()
        )

    @cached_property
    def room_qs_for_list(self):
        return (
            Room.objects.visible_for(user=self)
            .prefetch_related("users")
            .annotate(
                user_is_in_room=ExpressionWrapper(
                    Exists(User.objects.filter(id=self.id, rooms=OuterRef("id"))),
                    output_field=BooleanField(),
                ),
            )
            .order_by("-user_is_in_room", "status", "name")
            .values(
                "created_by__name",
                "description",
                "name",
                "slug",
                "status",
                "user_is_in_room",
            )
        )
