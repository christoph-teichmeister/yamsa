from django.core.management.base import BaseCommand

from apps.debt.services.payment_reminder_service import PaymentReminderService
from apps.room.services.room_closure_reminder_service import RoomClosureReminderService


class Command(BaseCommand):
    help = "Send reminder emails for rooms with stale activity."

    def handle(self, *args, **options):
        payment_service = PaymentReminderService()
        payment_candidates = payment_service.run()

        closure_service = RoomClosureReminderService()
        closure_candidates = closure_service.run()

        self.stdout.write(f"Sent {len(payment_candidates)} payment reminders ({payment_service.REMINDER_TYPE}).")
        self.stdout.write(f"Sent {len(closure_candidates)} room reminders ({closure_service.REMINDER_TYPE}).")
