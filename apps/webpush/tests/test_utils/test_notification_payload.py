import json

from apps.webpush.dataclasses import Notification


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
