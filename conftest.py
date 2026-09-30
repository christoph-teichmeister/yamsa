from datetime import timedelta
from io import BytesIO

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import RequestFactory
from django.test.client import Client
from django.utils import timezone
from PIL import Image

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import GuestUserFactory, SuperuserFactory, UserFactory
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.factories import CategoryFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.fixture
def user(db: None):
    return UserFactory()


@pytest.fixture
def guest_user(db: None):
    return GuestUserFactory()


@pytest.fixture
def authenticated_user(request: pytest.FixtureRequest, user: User, guest_user: User):
    param = request.param
    if param == "user":
        return user

    if param == "guest_user":
        return guest_user

    msg = f"authenticated_user fixture does not support '{param}'."
    raise ValueError(msg)


@pytest.fixture
def room(db: None, user: User, guest_user: User):
    room_instance = RoomFactory(created_by=user)
    room_instance.users.add(user, guest_user)
    return room_instance


@pytest.fixture
def closed_room(db: None, user: User, guest_user: User):
    room_instance = RoomFactory(created_by=user, status=Room.StatusChoices.CLOSED)
    room_instance.users.add(user, guest_user)
    return room_instance


@pytest.fixture
def superuser(db: None):
    return SuperuserFactory()


@pytest.fixture
def authenticated_client(client: Client, user: User):
    client.defaults["HTTP_HX_REQUEST"] = "true"
    request = RequestFactory().get("/")
    assert client.login(request=request, email=user.email, password=DEFAULT_PASSWORD)
    return client


@pytest.fixture
def superuser_htmx_client(superuser: User) -> Client:
    client = Client()
    client.defaults["HTTP_HX_REQUEST"] = "true"
    client.force_login(superuser)
    return client


@pytest.fixture
def room_with_stale_activity(room: Room, user: User):
    reminder_category = CategoryFactory(
        slug=f"room-reminder-{room.pk}",
        name="Room reminder",
        emoji="🧹",
    )
    transaction = ParentTransactionFactory(
        room=room,
        paid_by=user,
        currency=room.preferred_currency,
        category=reminder_category,
    )
    timestamp = timezone.now() - timedelta(days=settings.INACTIVITY_REMINDER_DAYS + 4)
    ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=timestamp)
    return room


@pytest.fixture
def attach_profile_picture():
    """Give a user a real picture, so their avatar renders as an image rather than as an initial."""

    def _attach(user_instance: User) -> User:
        buffer = BytesIO()
        Image.new("RGB", (64, 64), color=(255, 255, 255)).save(buffer, format="PNG")
        user_instance.profile_picture.save("avatar.png", ContentFile(buffer.getvalue()), save=True)
        return user_instance

    return _attach
