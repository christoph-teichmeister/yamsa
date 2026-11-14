from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone, translation
from pytest_django.fixtures import Settings

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.models import Category, ChildTransaction, ParentTransaction, Receipt, TransactionChange
from apps.transaction.services import change_history
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db

Kind = TransactionChange.Kind


@pytest.fixture(autouse=True)
def enforce_media_root(tmp_path: Path, settings: Settings) -> Path:
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def parent(room: Room, user: User, guest_user: User) -> ParentTransaction:
    parent_transaction, _children = create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(user, guest_user),
        parent_transaction_kwargs={
            "description": "Dinner",
            "category": RoomCategoryService(room=room).get_default_category(),
            "currency": room.preferred_currency,
            "paid_at": datetime(2026, 1, 2, 3, 4, tzinfo=UTC),
        },
    )
    return parent_transaction


def _edit_payload(parent: ParentTransaction, **overrides: object) -> dict:
    children = list(parent.child_transactions.order_by("id"))
    payload = {
        "description": parent.description,
        "paid_by": parent.paid_by_id,
        "paid_at": timezone.localtime(parent.paid_at).strftime("%Y-%m-%d %H:%M:%S"),
        "currency": parent.currency_id,
        "category": parent.category_id,
        "paid_for": [c.paid_for_id for c in children],
        "value": [str(c.value) for c in children],
        "child_transaction_id": [c.id for c in children],
        "total_value": str(parent.value),
    }
    payload.update(overrides)
    return payload


def _edit(client: Client, room: Room, parent: ParentTransaction, **overrides: object) -> None:
    response = client.post(
        reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent.id}),
        _edit_payload(parent, **overrides),
    )
    assert response.status_code == HTTPStatus.FOUND


def test_create_view_records_the_creator(authenticated_client: Client, room: Room, user: User) -> None:
    members = list(room.users.all())
    response = authenticated_client.post(
        reverse("transaction:create", kwargs={"room_slug": room.slug}),
        data={
            "category": Category.objects.get(slug="groceries").id,
            "description": "Pizza",
            "currency": room.preferred_currency.id,
            "paid_at": datetime(2026, 4, 4, 4, 20, tzinfo=UTC),
            "paid_by": user.id,
            "room": room.id,
            "room_slug": room.slug,
            "paid_for": [str(m.id) for m in members],
            "total_value": 10,
            "value": ["0.00"] * len(members),
            "reference_total_value": "0.00",
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    change = TransactionChange.objects.get(parent_transaction__description="Pizza")
    assert (change.kind, change.user, change.changes) == (Kind.CREATED, user, [])


def test_edit_records_field_level_old_and_new(
    authenticated_client: Client, room: Room, user: User, guest_user: User, parent: ParentTransaction
) -> None:
    _edit(
        authenticated_client,
        room,
        parent,
        description="Renamed",
        paid_by=guest_user.id,
        total_value="40.00",
        paid_at="2026-02-03 04:05:00",
    )

    change = TransactionChange.objects.get(parent_transaction=parent)
    assert change.kind == Kind.EDITED
    assert change.user == user
    by_field = {entry["field"]: entry for entry in change.changes if entry["field"] != "split"}
    assert (by_field["description"]["old"], by_field["description"]["new"]) == (parent.description, "Renamed")
    assert by_field["payer"]["old"] == user.name
    assert by_field["payer"]["new"] == guest_user.name
    assert (by_field["amount"]["old"], by_field["amount"]["new"]) == ("26.00", "40.00")
    assert "date" in by_field
    assert {e["who"] for e in change.changes if e["field"] == "split"} == {user.name, guest_user.name}


def test_edit_records_a_removed_participant(
    authenticated_client: Client, room: Room, user: User, guest_user: User, parent: ParentTransaction
) -> None:
    children = list(parent.child_transactions.order_by("id"))
    # A share set to zero is how a debtor leaves; the total stays so the shares are not re-split.
    shares = ["26.00" if c.paid_for_id == user.id else "0.00" for c in children]

    _edit(authenticated_client, room, parent, value=shares, total_value="26.00")

    change = TransactionChange.objects.get(parent_transaction=parent)
    removed = [e for e in change.changes if e["field"] == "split" and e["new"] is None]
    assert [(e["who"], e["old"]) for e in removed] == [(guest_user.name, "13.00")]


def test_edit_without_changes_records_nothing(
    authenticated_client: Client, room: Room, parent: ParentTransaction
) -> None:
    _edit(authenticated_client, room, parent)

    assert not TransactionChange.objects.filter(parent_transaction=parent).exists()


def test_receipt_upload_and_delete_are_recorded(
    authenticated_client: Client, room: Room, user: User, parent: ParentTransaction
) -> None:
    authenticated_client.post(
        reverse("transaction:receipt-upload", kwargs={"room_slug": room.slug, "transaction_pk": parent.id}),
        data={"receipt": SimpleUploadedFile("bill.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")},
    )
    receipt = Receipt.objects.get(parent_transaction=parent)
    authenticated_client.post(
        reverse("transaction:receipt-delete", kwargs={"room_slug": room.slug, "receipt_pk": receipt.id})
    )

    entries = list(TransactionChange.objects.filter(parent_transaction=parent).order_by("id"))
    assert [(e.kind, e.detail, e.user) for e in entries] == [
        (Kind.RECEIPT_ADDED, "bill.pdf", user),
        (Kind.RECEIPT_REMOVED, "bill.pdf", user),
    ]


def test_history_survives_the_user_being_deleted(user: User, guest_user: User, parent: ParentTransaction) -> None:
    change_history.record(parent, guest_user, Kind.CREATED)
    ChildTransaction.objects.filter(paid_for=guest_user).delete()
    guest_user.delete()

    change = TransactionChange.objects.get(parent_transaction=parent)
    assert change.user is None
    assert "Someone" in change_history.describe_headline(change)


def test_detail_renders_history_in_locale_with_formatted_amounts(
    authenticated_client: Client, room: Room, user: User, parent: ParentTransaction
) -> None:
    _edit(authenticated_client, room, parent, total_value="1234.50")

    with translation.override("de"):
        response = authenticated_client.get(
            reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent.id}), HTTP_ACCEPT_LANGUAGE="de"
        )

    soup = BeautifulSoup(response.content.decode(), "html.parser")
    section = soup.select_one("details#transaction-history > summary")
    assert section is not None
    text = soup.select_one("details#transaction-history").get_text(" ", strip=True)
    assert "hat diese Ausgabe bearbeitet" in text
    assert "Betrag: 26,00" in text
    assert "1.234,50" in text


def test_detail_shows_empty_state_for_legacy_transactions(
    authenticated_client: Client, room: Room, parent: ParentTransaction
) -> None:
    response = authenticated_client.get(
        reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent.id}), HTTP_ACCEPT_LANGUAGE="en"
    )

    soup = BeautifulSoup(response.content.decode(), "html.parser")
    details = soup.select_one("details#transaction-history")
    assert details is not None
    assert "open" not in details.attrs
    assert "No history was recorded for this expense." in details.get_text()


def test_history_is_hidden_from_non_members(client: Client, parent: ParentTransaction, room: Room) -> None:
    from apps.account.tests.factories import UserFactory

    client.force_login(UserFactory())

    response = client.get(reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent.id}))

    assert response.status_code != HTTPStatus.OK
    assert b"transaction-history" not in response.content


def test_describe_amounts_use_the_active_locale() -> None:
    entry = {"field": "amount", "old": "1000.00", "new": "1234.50", "sign": "€"}
    with translation.override("en"):
        assert change_history._describe_entry(entry) == "Amount: 1,000.00€ → 1,234.50€"
    with translation.override("de"):
        assert change_history._describe_entry(entry) == "Betrag: 1.000,00€ → 1.234,50€"
