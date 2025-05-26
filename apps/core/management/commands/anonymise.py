from django.core.management import BaseCommand
from django.db import transaction

from apps.account.models import User


class Command(BaseCommand):
    """Command for "anonymising" data"""

    help = '"Anonymises" Data'

    def handle(self, *args, **options):
        self.anonymise_data()

    @staticmethod
    def _anonymise_users():
        # Hashed password ""
        default_password = "Admin123$"

        for user in User.objects.all().order_by("id"):
            user.email = f"{user.id}@yamsa.local"
            user.set_password(default_password)
            user.save()

            print(f"Anonymised <{user.name} ({user.id})>")

    @staticmethod
    @transaction.atomic
    def anonymise_data():
        # Fake self for this method
        self = Command

        self._anonymise_users()
