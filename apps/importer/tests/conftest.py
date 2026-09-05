import pytest
from django.db import transaction as db_transaction

from apps.core.event_loop.runner import handle_message
from apps.currency.models import Currency
from apps.importer.dataclasses import CategoryAssignment, PersonAssignment
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.services.import_service import ImportService
from apps.importer.tests.factories import DEFAULT_ROWS, build_file_like
from apps.transaction.messages.events.transaction import TransactionsImported


@pytest.fixture
def currency(db):
    return Currency.objects.create(name="Euro", sign="€", code="EUR")


@pytest.fixture
def parsed():
    return SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))


@pytest.fixture
def run_import():
    """Drive ImportService the way the preview view does, including the follow-up event."""

    def _run_import(*, parsed, user, currency, person_assignments=None, category_assignments=None, fire_event=True):
        if person_assignments is None:
            person_assignments = [
                PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
                PersonAssignment(column="Elisabeth", kind=PersonAssignment.GUEST, guest_name="Elisabeth"),
            ]
        if category_assignments is None:
            category_assignments = [
                CategoryAssignment(label=entry.label, kind=CategoryAssignment.EXISTING, slug=entry.suggested_slug)
                for entry in parsed.categories
            ]

        service = ImportService(parsed=parsed, user=user)
        with db_transaction.atomic():
            result = service.process(
                room_name="Kilian & Elisabeth",
                room_description="Import aus Splitwise",
                currency=currency,
                person_assignments=person_assignments,
                category_assignments=category_assignments,
            )

        # The view connects existing users after the atomic block; mirror that here so tests
        # exercise the same end state.
        for deferred in result.deferred_connections:
            service.connect(user=deferred, room=result.room)

        if fire_event:
            handle_message(
                TransactionsImported(
                    context_data={
                        "room": result.room,
                        "imported_count": result.transaction_count,
                        "settled_count": result.settlement_count,
                        "source_label": "Splitwise (CSV)",
                        "triggered_by": user,
                    }
                )
            )
        return result

    return _run_import
