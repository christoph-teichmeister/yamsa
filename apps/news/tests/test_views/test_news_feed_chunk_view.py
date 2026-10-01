import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.news.models import News
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def create_news(*, room: Room, message: str) -> News:
    return News.objects.create(room=room, message=message)


class TestNewsFeedChunkView:
    def test_cursor_returns_only_the_older_news(self, authenticated_client: Client, room: Room) -> None:
        older_news = create_news(room=room, message="Older update")
        newer_news = create_news(room=room, message="Newer update")

        response = authenticated_client.get(
            reverse("news:feed", kwargs={"room_slug": room.slug}), {"cursor": newer_news.id}
        )

        assert response.status_code == http.HTTPStatus.OK
        returned_ids = [news.id for news in response.context_data["news"]]
        assert older_news.id in returned_ids
        assert newer_news.id not in returned_ids
        assert response.context_data["news_initial_render"] is False
