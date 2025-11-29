from __future__ import annotations

import factory
from factory import Faker, PostGenerationMethodCall, Sequence

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    name = Faker("name")
    email = Sequence(lambda sequence: f"user-{sequence}@yamsa.local")
    is_guest = False
    is_staff = False
    is_superuser = False
    wants_to_receive_webpush_notifications = True
    wants_to_receive_payment_reminders = True
    wants_to_receive_room_reminders = True
    password = PostGenerationMethodCall("set_password", DEFAULT_PASSWORD)


class GuestUserFactory(UserFactory):
    is_guest = True
