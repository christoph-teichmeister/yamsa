import pytest

from apps.news.models import News
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestNewsModel:
    def test_heading_prefers_type_icon_and_room_initials(self):
        room = ParentTransactionFactory().room
        room.name = "Holiday"
        room.save(update_fields=["name"])

        news = News.objects.create(
            message="Test",
            room=room,
            type=News.TypeChoices.TRANSACTION_CREATED,
        )

        expected_icon = News.TYPE_ICONS[News.TypeChoices.TRANSACTION_CREATED]
        expected_label = news.get_type_display()
        expected_initials = room.capitalised_initials

        assert news.heading == f"{expected_icon} {expected_initials}: {expected_label}"

    def test_heading_falls_back_to_title_when_type_missing(self):
        room = ParentTransactionFactory().room
        room.name = "Atlas"
        room.save(update_fields=["name"])

        title = "Weekend plan"
        news = News.objects.create(message="Note", room=room, title=title)

        assert news.heading == f"{room.capitalised_initials}: {title}"

    def test_heading_uses_default_label_without_type_or_title(self):
        room = ParentTransactionFactory().room
        room.name = "Beacon"
        room.save(update_fields=["name"])

        news = News.objects.create(message="Note", room=room)

        assert news.heading == f"{room.capitalised_initials}: {News.DEFAULT_HEADING_LABEL}"

    def test_highlighted_flag_resets_other_records(self):
        room = ParentTransactionFactory().room
        existing = News.objects.create(message="Existing", room=room, highlighted=True)

        fresh = News(message="Fresh", room=room, highlighted=True)
        fresh.save()

        existing.refresh_from_db()

        assert not existing.highlighted
        assert fresh.highlighted
