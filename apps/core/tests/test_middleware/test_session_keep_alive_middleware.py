import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY

pytestmark = pytest.mark.django_db


def test_refreshes_session_ttl_on_authenticated_requests(authenticated_client):
    client = authenticated_client
    session = client.session
    session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
    session.set_expiry(30)
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    client.get(reverse("core:welcome"))

    assert client.session.get_expiry_age() == settings.SESSION_COOKIE_AGE


def test_maintains_remember_me_ttl(authenticated_client):
    client = authenticated_client
    session = client.session
    session[SESSION_TTL_SESSION_KEY] = settings.DJANGO_REMEMBER_ME_SESSION_AGE
    session.set_expiry(30)
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    client.get(reverse("core:welcome"))

    assert client.session.get_expiry_age() == settings.DJANGO_REMEMBER_ME_SESSION_AGE


def test_skips_safe_htmx_fragments(authenticated_client):
    client = authenticated_client
    session = client.session
    session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
    session.set_expiry(30)
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    client.get(
        reverse("core:welcome"),
        HTTP_HX_REQUEST="true",
        HTTP_HX_TRIGGER="reminder-heartbeat",
    )

    assert client.session.get_expiry_age() == 30
    assert client.session[SESSION_TTL_SESSION_KEY] == settings.SESSION_COOKIE_AGE


@override_settings(SESSION_COOKIE_AGE=1)
def test_session_expiry_follows_idle_threshold(client):
    session = client.session
    session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
    session.set_expiry(settings.SESSION_COOKIE_AGE)
    session.save()

    session.set_expiry(-1)
    session.save()

    response = client.get(reverse("core:welcome"), follow=True)

    assert response.redirect_chain
    assert response.redirect_chain[-1][0] == reverse("account:login")
