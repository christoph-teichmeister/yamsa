import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation


@pytest.mark.django_db
class TestMoneySpentOnRoomViewAvatars:
    def test_every_bar_shows_the_face_of_the_person_it_belongs_to(
        self, client, room, user, guest_user, attach_profile_picture
    ):
        attach_profile_picture(user)
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        client.force_login(user)

        response = client.get(reverse("debt:money-spent-on-room", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["room_member_avatars"] == {user.id: user.avatar_url, guest_user.id: None}

        page = BeautifulSoup(response.content.decode(), "html.parser")
        payer_avatar = page.select_one(".graph-label .avatar")
        assert payer_avatar.find("img")["src"] == user.avatar_url

        # The guest paid nothing and owes everything, so their bar is the open-debt one.
        debtor_avatar = page.select(".graph-label .avatar")[1]
        assert debtor_avatar.find("img") is None
        assert debtor_avatar.get_text(strip=True) == guest_user.name[:1].upper()
