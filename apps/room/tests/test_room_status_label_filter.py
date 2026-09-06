"""Tests for the room_status_label templatetag filter."""

from django.test import TestCase

from apps.room.models import Room
from apps.room.templatetags.room_tags import room_status_label


class RoomStatusLabelFilterTestCase(TestCase):
    """Test cases for the room_status_label filter."""

    def test_known_status_resolves_to_its_label(self):
        self.assertEqual(room_status_label(Room.StatusChoices.OPEN.value), Room.StatusChoices.OPEN.label)

    def test_unknown_status_degrades_to_an_empty_label(self):
        self.assertEqual(room_status_label(99), "")
