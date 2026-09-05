from django.core import mail
from django.db import transaction as db_transaction

from apps.account.tests.factories import UserFactory
from apps.importer.dataclasses import CategoryAssignment, PersonAssignment
from apps.importer.services.import_service import ImportService
from apps.room.models import UserConnectionToRoom


class TestImportServiceSideEffects:
    """
    Connecting an existing non-guest emits webpush and email from inside Model.save().
    Doing that inside the caller's atomic block is the #333 pattern, so the service must
    hand those users back instead of connecting them itself.
    """

    def _assignments(self, existing):
        return [
            PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
            PersonAssignment(column="Elisabeth", kind=PersonAssignment.EXISTING, user_id=existing.pk),
        ]

    def _run(self, *, parsed, user, currency, existing):
        service = ImportService(parsed=parsed, user=user)
        with db_transaction.atomic():
            result = service.process(
                room_name="Kilian & Elisabeth",
                room_description="Import aus Splitwise",
                currency=currency,
                person_assignments=self._assignments(existing),
                category_assignments=[
                    CategoryAssignment(label=entry.label, kind=CategoryAssignment.EXISTING, slug=entry.suggested_slug)
                    for entry in parsed.categories
                ],
            )
        return service, result

    def test_existing_user_is_not_connected_inside_the_atomic_block(self, db, user, currency, parsed):
        existing = UserFactory(name="Elisabeth")

        _service, result = self._run(parsed=parsed, user=user, currency=currency, existing=existing)

        assert result.deferred_connections == [existing]
        assert not UserConnectionToRoom.objects.filter(room=result.room, user=existing).exists()

    def test_no_mail_is_sent_while_the_transaction_is_open(self, db, user, currency, parsed):
        existing = UserFactory(name="Elisabeth")
        mail.outbox.clear()

        _service, _result = self._run(parsed=parsed, user=user, currency=currency, existing=existing)

        assert mail.outbox == []

    def test_connecting_afterwards_completes_the_membership(self, db, user, currency, parsed):
        existing = UserFactory(name="Elisabeth")

        service, result = self._run(parsed=parsed, user=user, currency=currency, existing=existing)
        for deferred in result.deferred_connections:
            service.connect(user=deferred, room=result.room)

        assert UserConnectionToRoom.objects.filter(room=result.room, user=existing).exists()
        assert result.room.users.count() == 2

    def test_guests_are_still_connected_inside_the_service(self, db, user, currency, parsed, run_import):
        # Both handlers return early for guests, so those connections are safe in the block.
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert result.deferred_connections == []
        assert result.room.users.count() == 2
