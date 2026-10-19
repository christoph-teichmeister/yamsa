import factory
from factory import Faker, Sequence, post_generation

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    name = Faker("name")
    email = Sequence(lambda sequence: f"user-{sequence}@yamsa.local")
    is_guest = False
    is_staff = False
    is_superuser = False
    wants_to_receive_webpush_notifications = True
    wants_to_receive_payment_reminders = True
    wants_to_receive_room_reminders = True

    @post_generation
    def password(self, create: bool, extracted: str | None, **kwargs: object) -> None:
        self.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            self.save(update_fields=["password"])
