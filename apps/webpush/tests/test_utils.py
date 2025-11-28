import json

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from apps.core.tests.setup import BaseTestSetUp
from apps.webpush.dataclasses import Notification
from apps.webpush.utils import get_templatetag_context


class WebPushTemplateTagContextTestCase(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get("/")
        self.request.user = self.user

    def test_webpush_save_url_is_current(self):
        context = {"request": self.request, "webpush": {"group": "alerts"}}

        data = get_templatetag_context(context)

        self.assertEqual(data["webpush_save_url"], reverse("webpush:save"))
        self.assertEqual(data["group"], "alerts")
        self.assertEqual(data["user"], self.user)


class NotificationPayloadTestCase(SimpleTestCase):
    def test_action_urls_are_preserved(self):
        action = {"action": "open", "title": "Open", "url": "https://example.com"}
        payload = Notification.Payload(
            head="Test Headline",
            body="Body text",
            click_url="https://example.com/click",
            actions=[action.copy()],
        )

        first = json.loads(payload.format_for_webpush())
        second = json.loads(payload.format_for_webpush())

        self.assertEqual(first["data"]["actionClickUrls"][0]["url"], action["url"])
        self.assertEqual(second["data"]["actionClickUrls"][0]["url"], action["url"])
        self.assertEqual(payload.actions[0]["url"], action["url"])
