import pytest
from django.test import override_settings
from django.urls import reverse

from apps.core.pwa_constants import ANONYMOUS_SCOPE, SCOPE_HEADER_NAME
from apps.core.services.pwa_scope_service import resolve_scope

pytestmark = pytest.mark.django_db


def test_html_response_names_the_signed_in_account(authenticated_client, user):
    response = authenticated_client.get(reverse("core:welcome"))

    assert response[SCOPE_HEADER_NAME] == resolve_scope(user)


def test_html_response_of_a_visitor_names_the_anonymous_scope(client):
    response = client.get(reverse("account:login"))

    assert response[SCOPE_HEADER_NAME] == ANONYMOUS_SCOPE


def test_two_accounts_never_share_a_scope(user, guest_user):
    assert resolve_scope(user) != resolve_scope(guest_user)


def test_the_scope_cannot_be_derived_without_the_secret_key(user):
    """It becomes part of a cache name, and any script on the origin can list those."""
    scope = resolve_scope(user)

    assert scope != str(user.pk)
    assert user.email not in scope

    with override_settings(SECRET_KEY="a-different-secret-key-entirely"):
        assert resolve_scope(user) != scope


def test_a_non_html_response_carries_no_scope(client):
    """The worker only ever stores documents, so a scope on anything else would only mislead."""
    response = client.get(reverse("core:serviceworker"))

    assert SCOPE_HEADER_NAME not in response
