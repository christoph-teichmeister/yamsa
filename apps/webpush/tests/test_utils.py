import json

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.webpush.dataclasses import Notification
from apps.webpush.utils import get_templatetag_context


@pytest.mark.django_db
class TestWebPushTemplateTagContext:
    def test_webpush_save_url_is_current(self, user):
        request = RequestFactory().get("/")
        request.user = user
        context = {"request": request, "webpush": {"group": "alerts"}}

        data = get_templatetag_context(context)

        assert data["webpush_save_url"] == reverse("webpush:save")
        assert data["group"] == "alerts"
        assert data["user"] == user


class TestNotificationPayload:
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

        assert first["data"]["actionClickUrls"][0]["url"] == action["url"]
        assert second["data"]["actionClickUrls"][0]["url"] == action["url"]
        assert payload.actions[0]["url"] == action["url"]
