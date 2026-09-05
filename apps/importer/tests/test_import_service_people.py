from apps.account.models import User
from apps.account.tests.factories import GuestUserFactory
from apps.importer.dataclasses import PersonAssignment
from apps.room.models import UserConnectionToRoom
from apps.transaction.models import ParentTransaction


class TestImportServicePeople:
    def test_guest_is_created_for_a_guest_assignment(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        guest = User.objects.get(name="Elisabeth")
        assert guest.is_guest is True
        assert guest.created_by == user
        assert result.created_guest_count == 1

    def test_existing_person_is_reused_instead_of_duplicated(self, run_import, db, user, currency, parsed):
        existing = GuestUserFactory(name="Elisabeth")
        assignments = [
            PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
            PersonAssignment(column="Elisabeth", kind=PersonAssignment.EXISTING, user_id=existing.pk),
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, person_assignments=assignments)

        assert User.objects.filter(name="Elisabeth").count() == 1
        assert result.created_guest_count == 0
        assert UserConnectionToRoom.objects.filter(room=result.room, user=existing).exists()

    def test_importer_is_never_created_as_a_guest(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert User.objects.filter(name=user.name).count() == 1
        assert ParentTransaction.objects.filter(room=result.room, paid_by=user).exists()

    def test_room_has_one_member_per_person_column(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert result.room.users.count() == len(parsed.people)
