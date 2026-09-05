import http

import pytest
from django.urls import reverse

from apps.news.constants import NEWS_FEED_PAGE_SIZE
from apps.news.models import News
from apps.room.tests.factories import RoomFactory

pytestmark = pytest.mark.django_db


def create_news(*, room, message, highlighted=False):
    return News.objects.create(room=room, message=message, highlighted=highlighted)


class TestNewsListView:
    def test_anonymous_user_is_redirected_to_the_login(self, client):
        response = client.get(reverse("news:list"))

        assert response.status_code == http.HTTPStatus.FOUND
        assert reverse("account:login") in response.url

    def test_highlighted_news_and_the_first_batch_are_rendered(self, authenticated_client, room):
        create_news(room=room, message="Highlighted update", highlighted=True)
        create_news(room=room, message="Regular update")

        response = authenticated_client.get(reverse("news:list"))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["news_initial_render"] is True
        assert response.context_data["highlighted_news"].message == "Highlighted update"
        content = response.content.decode()
        assert "Highlighted update" in content
        assert "Regular update" in content

    def test_news_of_rooms_the_user_does_not_belong_to_are_hidden(self, authenticated_client, user):
        foreign_room = RoomFactory()
        create_news(room=foreign_room, message="Not for you")

        response = authenticated_client.get(reverse("news:list"))

        assert list(response.context_data["news"]) == []

    def test_a_full_batch_exposes_a_cursor(self, authenticated_client, room):
        for index in range(NEWS_FEED_PAGE_SIZE + 1):
            create_news(room=room, message=f"Update {index}")

        response = authenticated_client.get(reverse("news:list"))

        assert len(response.context_data["news"]) == NEWS_FEED_PAGE_SIZE
        assert response.context_data["news_next_cursor"] is not None


class TestNewsFeedChunkView:
    def test_cursor_returns_only_the_older_news(self, authenticated_client, room):
        older_news = create_news(room=room, message="Older update")
        newer_news = create_news(room=room, message="Newer update")

        response = authenticated_client.get(reverse("news:feed"), {"cursor": newer_news.id})

        assert response.status_code == http.HTTPStatus.OK
        returned_ids = [news.id for news in response.context_data["news"]]
        assert older_news.id in returned_ids
        assert newer_news.id not in returned_ids
        assert response.context_data["news_initial_render"] is False
