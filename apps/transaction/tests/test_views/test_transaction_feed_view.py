import http

import pytest
from django.urls import reverse

from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


def test_transaction_feed_displays_no_matches_message(client, room, user, guest_user):
    create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(guest_user,),
    )
    client.force_login(user)

    response = client.get(
        reverse("transaction:feed", kwargs={"room_slug": room.slug}),
        data={"q": "missing"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    assert 'No transactions match "missing".' in content
