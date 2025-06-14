import uuid

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, call_command
from django.db import transaction

from apps.account.models import User
from apps.currency.models import Currency
from apps.room.models import Room, UserConnectionToRoom


class Command(BaseCommand):
    """Command for restoring test data for the system"""

    help = "Creates some test data"

    def handle(self, *args, **options):
        call_command("flush", "--noinput")

        call_command("migrate")

        self.restore_test_data()

    @staticmethod
    def _create_users():
        # Hashed password "Admin123$"
        default_password = (
            "argon2$argon2id$v=19$m=102400,t=2,p=8$ZE1LcE9TYmpDZTNmR1I3aVdHc"
            "jc4MQ$4JN0SLWYv/lI9oPPDY06UouiWdOpgR8BI65O+SeXsuE"
        )

        superuser = User.objects.create(
            name="yamsa-admin",
            password=default_password,
            email="admin@yamsa.local",
            is_superuser=True,
            is_staff=True,
            is_guest=False,
        )

        print(f'User ID: {superuser.id}, Name: "{superuser.name}" created')

        # --------------- REGISTERED USERS ---------------

        # Creates five registered users
        for i in range(1, 6):
            registered_user = User.objects.create(
                name=f"registered_user_{i}",
                password=default_password,
                email=f"registered_user_{i}@yamsa.local",
                is_superuser=False,
                is_staff=False,
                is_guest=False,
            )

            print(f'User ID: {registered_user.id}, Name: "{registered_user.name}" created')

        # --------------- GUEST USERS ---------------

        # Creates five guest users
        for i in range(1, 6):
            guest_user = User.objects.create(
                name=f"guest_{i}",
                password=make_password(f"guest_{i}"),
                is_superuser=False,
                is_staff=False,
                is_guest=True,
            )

            print(f'User ID: {guest_user.id}, Name: "{guest_user.name}" created')

    @staticmethod
    def _create_currencies():
        Currency.objects.create(name="Euro", sign="€", code="EUR")
        Currency.objects.create(name="Pound Sterling", sign="£", code="GBP")

        print("Euro and Pound Sterling created")

    @staticmethod
    def _create_rooms():
        all_users_id_list = User.objects.values_list("id", flat=True)

        for i in range(1, 4):
            room = Room.objects.create(
                name=f"Room {i}",
                slug=uuid.uuid4(),
                description=f"Description for Room {i}",
                preferred_currency=Currency.objects.get(sign="€"),
                created_by_id=all_users_id_list[i],
            )

            for user_id in all_users_id_list:
                if user_id % i == 0:
                    UserConnectionToRoom.objects.create(user_id=user_id, room=room, created_by_id=room.created_by_id)

            print(f'Room ID: {room.id}, Name: "{room.name}" created')

    @staticmethod
    @transaction.atomic
    def restore_test_data():
        """
        Creates / "Finds" test data.

        Will create a superuser, a few guest_users, rooms and transactions
        """

        # Fake self for this method
        self = Command

        self._create_users()

        self._create_currencies()

        self._create_rooms()
