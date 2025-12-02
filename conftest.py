from datetime import timedelta

import pytest
from django.conf import settings
from django.test import RequestFactory
from django.utils import timezone

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import GuestUserFactory, SuperuserFactory, UserFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import CategoryFactory, ParentTransactionFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def guest_user(db):
    return GuestUserFactory()


@pytest.fixture
def authenticated_user(request, user, guest_user):
    param = request.param
    if param == "user":
        return user

    if param == "guest_user":
        return guest_user

    msg = f"authenticated_user fixture does not support '{param}'."
    raise ValueError(msg)


@pytest.fixture
def room(db, user, guest_user):
    room_instance = RoomFactory(created_by=user)
    room_instance.users.add(user, guest_user)
    return room_instance


@pytest.fixture
def superuser(db):
    return SuperuserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.defaults["HTTP_HX_REQUEST"] = "true"
    request = RequestFactory().get("/")
    assert client.login(request=request, email=user.email, password=DEFAULT_PASSWORD)
    return client


@pytest.fixture
def room_with_stale_activity(room, user):
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
