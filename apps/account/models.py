import random
import string
from functools import cached_property, lru_cache
from time import time

from ambient_toolbox.mixins.validation import CleanOnSaveMixin
from ambient_toolbox.models import CommonInfo
from django.conf import settings
from django.contrib.auth import hashers
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.account.managers import UserManager
from apps.core.utils import determine_upload_to
from apps.room.models import Room, UserConnectionToRoom


@lru_cache
def get_has_seen_room(userconnectiontoroom_set, room_id: int) -> tuple[UserConnectionToRoom, bool]:
    # Refactored because of Error B019
    # => https://docs.astral.sh/ruff/rules/cached-instance-method/#cached-instance-method-b019
    connections = userconnectiontoroom_set.filter(room_id=room_id)
    return connections.first(), connections.filter(user_has_seen_this_room=True).exists()


class User(CleanOnSaveMixin, CommonInfo, AbstractBaseUser, PermissionsMixin):
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("name",)

    UPLOAD_FOLDER_NAME = "profile_picture"
    PROFILE_PICTURE_FALLBACK_PATH = "img/profile-default.svg"

    def _build_fallback_profile_picture_url(self) -> str:
        static_url = settings.STATIC_URL
        if not static_url.endswith("/"):
            static_url = f"{static_url}/"
        return f"{static_url}{self.PROFILE_PICTURE_FALLBACK_PATH.lstrip('/')}"

    @property
    def profile_picture_fallback_url(self) -> str:
        return self._build_fallback_profile_picture_url()

    @property
    def profile_picture_url(self) -> str:
        fallback_url = self._build_fallback_profile_picture_url()
        picture = self.profile_picture

        if not picture or not getattr(picture, "name", None):
            return fallback_url

        try:
            if not picture.storage.exists(picture.name):
                return fallback_url

            return picture.url
        except Exception:
            return fallback_url

    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    paypal_me_username = models.CharField(max_length=100, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=determine_upload_to, null=True, blank=True)
    language = models.CharField(max_length=5, choices=settings.LANGUAGES, null=True, blank=True)

    is_guest = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        _("Staff Status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    wants_to_receive_webpush_notifications = models.BooleanField(default=False)
    wants_to_receive_payment_reminders = models.BooleanField(default=True)
    wants_to_receive_room_reminders = models.BooleanField(default=True)

    rooms = models.ManyToManyField("room.Room", through="room.UserConnectionToRoom", through_fields=("user", "room"))

    invitation_email_sent = models.BooleanField(default=False)
    invitation_email_sent_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_guest and not self.is_superuser:
            # If a user has been added and is a guest, give them unique email and password
            timestamp = time()
            self.email = f"{self.name}-{timestamp}@local.local"
            self.password = f"{self.name}-{timestamp}"

        self.email = self.__class__.objects.normalize_email(self.email)
        super().clean()

    @cached_property
    def room_qs_for_list(self) -> dict:
        return (
            Room.objects.visible_for(user=self)
            .prefetch_related("users")
            .annotate_user_is_in_room_for_user_id(user_id=self.id)
            .annotate_last_transaction_lastmodified_at_date()
            .annotate_capitalised_initials()
            .order_by("-user_is_in_room", "status", "-last_transaction_created_at_date")
            .values(
                "capitalised_initials",
                "created_by__name",
                "description",
                "name",
                "slug",
                "status",
                "user_is_in_room",
            )
        )

    def has_seen_room(self, room_id: int) -> tuple[UserConnectionToRoom, bool]:
        return get_has_seen_room(self.userconnectiontoroom_set, room_id)

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

    def generate_random_password_with_length(self, length: int) -> str:
        characters = string.ascii_letters + string.digits
        new_password = "".join(random.choice(characters) for _ in range(length))

        self.password = hashers.make_password(new_password)
        self.save()

        return new_password


class UserFriendship(CommonInfo):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="friendships")
    friend = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="friended_by")

    class Meta:
        verbose_name = _("User friendship")
        verbose_name_plural = _("User friendships")
        constraints = [models.UniqueConstraint(fields=["user", "friend"], name="unique_user_friendship")]
        indexes = [
            models.Index(fields=["user", "friend"], name="acc_usrfrndshp_usr_frnd_idx"),
            models.Index(fields=["friend", "user"], name="acc_usrfrndshp_frnd_usr_idx"),
        ]

    def __str__(self):
        return f"{self.user} ↔ {self.friend}"

    def clean(self):
        if self.user_id == self.friend_id:
            error_msg = _("Users cannot be friends with themselves.")
            raise ValidationError(error_msg)

        super().clean()
