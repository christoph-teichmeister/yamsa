"""What a background request that only fills the offline cache must not set in motion.

The client warms a room's pages by re-requesting them, so any GET that changes state once would
run again per warm-up - on a page nobody is looking at.
"""

from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
from apps.core.pwa_constants import PREFETCH_HEADER_NAME
from apps.importer.constants import IMPORT_SHARE_HINT_SESSION_KEY

pytestmark = pytest.mark.django_db

PREFETCH_HEADERS = {PREFETCH_HEADER_NAME.lower(): "1"}


def test_warming_the_transaction_list_keeps_the_import_hint_unspent(authenticated_client, room):
    session = authenticated_client.session
    session[IMPORT_SHARE_HINT_SESSION_KEY] = str(room.slug)
    session.save()

    url = reverse("transaction:list", kwargs={"room_slug": room.slug})
    prefetched = authenticated_client.get(url, headers=PREFETCH_HEADERS)

    assert prefetched.context["show_import_share_hint"] is False
    assert authenticated_client.session[IMPORT_SHARE_HINT_SESSION_KEY] == str(room.slug)

    assert authenticated_client.get(url).context["show_import_share_hint"] is True


@mock.patch("apps.room.services.room_closure_reminder_service.RoomClosureReminderService.run_if_due")
@mock.patch("apps.debt.services.payment_reminder_service.PaymentReminderService.run_if_due")
def test_warming_the_dashboard_does_not_run_the_reminder_services(
    payment_reminder, closure_reminder, authenticated_client, room
):
    url = reverse("room:dashboard", kwargs={"room_slug": room.slug})
    authenticated_client.get(url, headers=PREFETCH_HEADERS)

    payment_reminder.assert_not_called()
    closure_reminder.assert_not_called()

    authenticated_client.get(url)

    payment_reminder.assert_called_once()
    closure_reminder.assert_called_once()


def test_warming_a_page_does_not_keep_the_session_alive(authenticated_client, room):
    """Otherwise a session never expires while the app is open, and every warmed page writes it."""
    session = authenticated_client.session
    session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
    session.set_expiry(30)
    session.save()
    authenticated_client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    url = reverse("transaction:list", kwargs={"room_slug": room.slug})
    authenticated_client.get(url, headers=PREFETCH_HEADERS)

    assert authenticated_client.session.get_expiry_age() <= 30

    authenticated_client.get(url)

    assert authenticated_client.session.get_expiry_age() > 30
