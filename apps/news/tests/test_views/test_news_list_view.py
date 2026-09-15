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
    def test_highlighted_news_and_the_first_batch_are_rendered(self, authenticated_client, room):
        create_news(room=room, message="Highlighted update", highlighted=True)
        create_news(room=room, message="Regular update")

        response = authenticated_client.get(reverse("news:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["news_initial_render"] is True
        assert response.context_data["highlighted_news"].message == "Highlighted update"
        content = response.content.decode()
        assert "Highlighted update" in content
        assert "Regular update" in content

    def test_news_of_other_rooms_are_hidden(self, authenticated_client, room, user):
        other_room = RoomFactory()
        other_room.users.add(user)
        create_news(room=other_room, message="Not for this room")

        response = authenticated_client.get(reverse("news:list", kwargs={"room_slug": room.slug}))

        messages = [news.message for news in response.context_data["news"]]
        assert "Not for this room" not in messages

    def test_a_full_batch_exposes_a_cursor(self, authenticated_client, room):
        for index in range(NEWS_FEED_PAGE_SIZE + 1):
            create_news(room=room, message=f"Update {index}")

        response = authenticated_client.get(reverse("news:list", kwargs={"room_slug": room.slug}))

        assert len(response.context_data["news"]) == NEWS_FEED_PAGE_SIZE
        assert response.context_data["news_next_cursor"] is not None
