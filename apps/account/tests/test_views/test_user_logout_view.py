import http

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.account.views import LogInUserView

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("authenticated_user", ("user", "guest_user"), indirect=True)
def test_get_regular_as_user_and_guest_user(hx_client, authenticated_user):
    client = hx_client(authenticated_user)

    response = client.get(reverse("account:logout"), follow=True)

    assert response.status_code == http.HTTPStatus.OK
    assert response.templates[0].name == LogInUserView.template_name
    assert isinstance(response.wsgi_request.user, AnonymousUser)

    content = response.content.decode()
    assert "Login" in content
    assert "Forgot password?" in content
    assert "Create an account" in content

    client.logout()
