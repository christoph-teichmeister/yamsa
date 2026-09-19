import secrets
import string
import uuid
from functools import cached_property

from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.core.models.mixins.emit_model_created_event_on_save import EmitModelCreatedEventOnSaveMixin
from apps.core.utils import determine_upload_to
from apps.room.managers import RoomManager
from apps.room.room_seal import SEAL_ICONS, default_seal_icon, seal_tilt_deg


class Room(EmitModelCreatedEventOnSaveMixin, FullCleanOnSaveMixin, CommonInfo):
    class StatusChoices(models.IntegerChoices):
        OPEN = 1, _("Open")
        CLOSED = 2, _("Closed")

    SHARE_HASH_LENGTH = 8
    SHARE_HASH_CHARACTERS = string.ascii_letters + string.digits

    UPLOAD_FOLDER_NAME = "seal_image"
    SEAL_ICON_CHOICES = [(name, name) for name in SEAL_ICONS]

    slug = models.UUIDField(unique=True)
    share_hash = models.CharField(max_length=16, unique=True, blank=True, editable=False, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=50)
    status = models.SmallIntegerField(choices=StatusChoices.choices, default=StatusChoices.OPEN)

    # A member's own choice for the room's seal - blank/absent falls back to the deterministic
    # default derived from `slug` (see `resolved_seal_icon`). A custom image, once uploaded, is
    # shown in place of either.
    seal_icon = models.CharField(max_length=30, choices=SEAL_ICON_CHOICES, blank=True)
    seal_image = models.ImageField(upload_to=determine_upload_to, max_length=255, null=True, blank=True)

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

    @classmethod
    def dashboard_viewname_for(cls, status: int) -> str:
        """Name the view a room card links to.

        A closed room has no transaction list worth opening, so it leads to its detail page.
        Single source for the rule - the dashboard and the side menu both link room rows.
        """
        return "room:detail" if status == cls.StatusChoices.CLOSED else "transaction:list"

    @classmethod
    def status_label_for(cls, status: int) -> str:
        """Resolve a raw status value to its label, or "" if it maps to no choice.

        Rows coming from a values() queryset are plain dicts and carry no
        get_status_display(), so every such consumer has to resolve the label itself.
        A value outside the choices means broken data; it must degrade to an empty
        badge rather than take down the page that lists the room.
        """
        try:
            return cls.StatusChoices(status).label
        except ValueError:
            return ""

    @cached_property
    def capitalised_initials(self):
        return self.name[:2].upper()

    @property
    def can_be_closed(self):
        return not self.debts.filter(settled=False).exists()

    @property
    def is_closed(self):
        return self.status == self.StatusChoices.CLOSED

    @property
    def can_be_deleted(self):
        return self.is_closed

    @property
    def resolved_seal_icon(self) -> str:
        """The icon to show: the member's own choice, or the deterministic default."""
        return self.seal_icon or default_seal_icon(self.slug)

    @property
    def seal_tilt(self) -> int:
        return seal_tilt_deg(self.slug)

    @property
    def seal_image_url(self) -> str | None:
        """The custom seal image's URL, or None when there is no custom image to show."""
        if not self.seal_image:
            return None
        try:
            return self.seal_image.url
        except Exception:
            return None
