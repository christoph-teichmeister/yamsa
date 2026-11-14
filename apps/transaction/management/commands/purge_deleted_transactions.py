from django.core.management.base import BaseCommand

from apps.transaction.services.transaction_deletion_service import TransactionDeletionService


class Command(BaseCommand):
    help = "Delete transactions whose undo window has passed and notify their rooms. Meant for a frequent cron."

    def handle(self, *args: object, **options: object) -> None:
        count = TransactionDeletionService.finalise_expired()
        self.stdout.write(f"Deleted {count} transactions for good.")
