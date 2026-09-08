import hashlib
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
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.account.managers import UserManager
from apps.account.utils.paypal import normalize_paypal_me_username
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

    # A list asks for a picture per row, and MediaCloudinaryStorage answers exists() with an HTTP
    # request. An upload name carries a uuid4 (determine_upload_to) and is therefore never reused,
    # so a name that exists keeps existing. A miss is not cached as long, because the same branch
    # also catches a storage that is momentarily unreachable.
    PROFILE_PICTURE_EXISTS_CACHE_TIMEOUT = 60 * 60 * 24
    PROFILE_PICTURE_MISSING_CACHE_TIMEOUT = 60

    # Cloudinary delivers the avatar at twice the size the lists paint it, instead of the original
    # the upload limit allows (3 MB).
    AVATAR_TRANSFORMATION = "c_fill,g_auto,h_128,w_128,f_auto,q_auto"
    CLOUDINARY_UPLOAD_MARKER = "/image/upload/"

    def _build_fallback_profile_picture_url(self) -> str:
        static_url = settings.STATIC_URL
        if not static_url.endswith("/"):
            static_url = f"{static_url}/"
        return f"{static_url}{self.PROFILE_PICTURE_FALLBACK_PATH.lstrip('/')}"

    def _profile_picture_exists(self) -> bool:
        picture = self.profile_picture
        # The name, not the pk: it identifies the file the answer is about, and a re-upload asks
        # under a new one rather than reading a stale entry.
        digest = hashlib.sha256(picture.name.encode()).hexdigest()
        cache_key = f"profile-picture-exists:{digest}"

        cached_answer = cache.get(cache_key)
        if cached_answer is not None:
            return cached_answer

        try:
            picture_exists = picture.storage.exists(picture.name)
        except Exception:
            picture_exists = False

        cache.set(
            cache_key,
            picture_exists,
            self.PROFILE_PICTURE_EXISTS_CACHE_TIMEOUT if picture_exists else self.PROFILE_PICTURE_MISSING_CACHE_TIMEOUT,
        )
        return picture_exists

    def _has_profile_picture(self) -> bool:
        picture = self.profile_picture
        if not picture or not getattr(picture, "name", None):
            return False
        return self._profile_picture_exists()

    def _as_avatar_url(self, url: str) -> str:
        """Narrow a Cloudinary delivery URL to the avatar size; leave every other storage alone."""
        marker = self.CLOUDINARY_UPLOAD_MARKER
        head, separator, tail = url.partition(marker)
        if not separator:
            return url
        return f"{head}{marker}{self.AVATAR_TRANSFORMATION}/{tail}"

    @property
    def profile_picture_fallback_url(self) -> str:
        return self._build_fallback_profile_picture_url()

    @cached_property
    def avatar_url(self) -> str | None:
        """The thumbnail of this user, or None when there is no picture to show.

        None rather than the placeholder: a caller that has room for a picture but none to show
        renders the user's initial instead, and only the caller knows how big it has to be.
        """
        if not self._has_profile_picture():
            return None

        try:
            url = self.profile_picture.url
        except Exception:
            return None

        return self._as_avatar_url(url)

    @property
    def profile_picture_url(self) -> str:
        """The picture at its stored size, for the profile page and its dialog."""
        fallback_url = self._build_fallback_profile_picture_url()

        if not self._has_profile_picture():
            return fallback_url

        try:
            return self.profile_picture.url
        except Exception:
            return fallback_url

    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    paypal_me_username = models.CharField(max_length=100, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=determine_upload_to, max_length=255, null=True, blank=True)
    language = models.CharField(max_length=5, choices=settings.LANGUAGES, blank=True)

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

    def get_full_name(self) -> str:
        return self.name

    def clean(self):
        if self.is_guest and not self.is_superuser:
            # If a user has been added and is a guest, give them unique email and password
            timestamp = time()
            self.email = f"{self.name}-{timestamp}@local.local"
            self.password = f"{self.name}-{timestamp}"

        self.email = self.__class__.objects.normalize_email(self.email)

        # Here rather than in a field validator: a validator runs before this method and can only
        # reject, so a pasted "@name" would be refused instead of reduced to the handle it carries.
        try:
            self.paypal_me_username = normalize_paypal_me_username(self.paypal_me_username)
        except ValidationError as error:
            raise ValidationError({"paypal_me_username": error}) from error

        super().clean()

    @cached_property
    def room_qs_for_list(self) -> dict:
        return (
            Room.objects.visible_for(user=self)
            .prefetch_related("users")
            .annotate_user_is_in_room_for_user_id(user_id=self.id)
            .annotate_last_activity()
            .annotate_capitalised_initials()
            .order_by("-user_is_in_room", "status", "-last_activity", "pk")
            .values(
                "capitalised_initials",
                "created_by__name",
                "description",
                "id",
                "last_activity",
                "last_transaction_at",
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
