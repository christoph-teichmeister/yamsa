import secrets
import string
import uuid
from functools import cached_property

from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.core.models.mixins.emit_model_created_event_on_save import EmitModelCreatedEventOnSaveMixin
from apps.room.managers import RoomManager


class Room(EmitModelCreatedEventOnSaveMixin, FullCleanOnSaveMixin, CommonInfo):
    class StatusChoices(models.IntegerChoices):
        OPEN = 1, _("Open")
        CLOSED = 2, _("Closed")

    SHARE_HASH_LENGTH = 8
    SHARE_HASH_CHARACTERS = string.ascii_letters + string.digits

    slug = models.UUIDField(unique=True)
    share_hash = models.CharField(max_length=16, unique=True, blank=True, editable=False, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=50)
    status = models.SmallIntegerField(choices=StatusChoices.choices, default=StatusChoices.OPEN)

    preferred_currency = models.ForeignKey("currency.Currency", related_name="rooms", on_delete=models.DO_NOTHING)

    users = models.ManyToManyField("account.User", through="room.UserConnectionToRoom", through_fields=("room", "user"))

    objects = RoomManager()

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = uuid.uuid4()

        if not self.share_hash:
            self.share_hash = self.generate_share_hash()

        super().save(*args, **kwargs)

    @classmethod
    def generate_share_hash(cls) -> str:
        alphabet = cls.SHARE_HASH_CHARACTERS
        while True:
            candidate = "".join(secrets.choice(alphabet) for _ in range(cls.SHARE_HASH_LENGTH))
            if not cls.objects.filter(share_hash=candidate).exists():
                return candidate

    @cached_property
    def room_users(self):
        from apps.account.models import User

        return User.objects.filter(room=self)

    @cached_property
    def has_guests(self):
        return self.room_users.filter(is_guest=True).exists()

    @cached_property
    def capitalised_initials(self):
        return self.name[:2].upper()

    @property
    def can_be_closed(self):
        return not self.debts.filter(settled=False).exists()
