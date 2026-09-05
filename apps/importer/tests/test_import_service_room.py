import pytest
from django.core import mail

from apps.account.models import User
from apps.importer.dataclasses import PersonAssignment
from apps.news.models import News
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.models import ParentTransaction


class TestImportServiceCreatesRoom:
    def test_room_is_owned_by_the_importer(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert result.room.created_by == user
        assert result.room.preferred_currency == currency

    def test_importer_becomes_a_member(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert UserConnectionToRoom.objects.filter(room=result.room, user=user).exists()

    def test_room_created_news_is_written(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert News.objects.filter(room=result.room, type=News.TypeChoices.ROOM_CREATED).exists()

    def test_importer_receives_no_added_to_room_mail(self, run_import, db, user, currency, parsed):
        mail.outbox.clear()

        run_import(parsed=parsed, user=user, currency=currency)

        assert mail.outbox == []

    def test_a_failing_import_leaves_no_half_room(self, run_import, db, user, currency, parsed):
        broken_assignments = [
            PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
            PersonAssignment(column="Elisabeth", kind=PersonAssignment.EXISTING, user_id=-1),
        ]

        with pytest.raises(User.DoesNotExist):
            run_import(
                parsed=parsed,
                user=user,
                currency=currency,
                person_assignments=broken_assignments,
                fire_event=False,
            )

        assert Room.objects.count() == 0
        assert ParentTransaction.objects.count() == 0
