"""Tests for the room_last_used templatetag filter."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.room.templatetags.room_tags import room_last_used


class RoomLastUsedFilterTestCase(TestCase):
    """Test cases for the room_last_used filter."""

    def test_a_past_timestamp_is_rendered_in_one_unit(self) -> None:
        # naturaltime would answer "4 weeks, 2 days ago" here; the compact room row cannot
        # spare that width. days=29, not 30: Django's month chunk is exactly 30 days, and the
        # microseconds that pass between this line and timesince()'s own now() always push a
        # days=30 delta over that boundary, making "4 weeks ago" unreachable.
        assert room_last_used(timezone.now() - timedelta(days=29)) == "4\xa0weeks ago"

    def test_a_recent_timestamp_keeps_its_precision(self) -> None:
        assert room_last_used(timezone.now() - timedelta(minutes=5)) == "5\xa0minutes ago"

    def test_a_future_timestamp_reads_forwards(self) -> None:
        # paid_at is user-editable and accepts a future date - "in 3 hours" beats "0 minutes ago".
        assert room_last_used(timezone.now() + timedelta(hours=3, minutes=1)) == "3\xa0hours from now"

    def test_no_timestamp_renders_nothing(self) -> None:
        assert room_last_used(None) == ""

    def test_the_wording_is_translated(self) -> None:
        # "vor 2 Tage" rather than "Tagen": Django's German unit names are nominative and the
        # catalogue wraps them, the same way the news cards have always rendered this string.
        with override_settings(LANGUAGE_CODE="de"):
            assert room_last_used(timezone.now() - timedelta(days=2)) == "vor 2\xa0Tage"
