from decimal import Decimal

import pytest
from django.core import mail
from django.db import transaction as db_transaction

from apps.account.models import User
from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.core.event_loop.runner import handle_message
from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.importer.dataclasses import CategoryAssignment, PersonAssignment
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.services.import_service import ImportService
from apps.importer.tests.factories import build_file_like
from apps.news.models import News
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.messages.events.transaction import TransactionsImported
from apps.transaction.models import Category, ChildTransaction, ParentTransaction, RoomCategory

DEFAULT_ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
    "2026-09-05,Gesamtbilanz,,,EUR,47.77,-47.77",
]


@pytest.fixture
def currency(db):
    return Currency.objects.create(name="Euro", sign="€", code="EUR")


@pytest.fixture
def parsed():
    return SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))


def run_import(*, parsed, user, currency, person_assignments=None, category_assignments=None, fire_event=True):
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


class TestImportServiceCreatesRoom:
    def test_room_is_owned_by_the_importer(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert result.room.created_by == user
        assert result.room.preferred_currency == currency

    def test_importer_becomes_a_member(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert UserConnectionToRoom.objects.filter(room=result.room, user=user).exists()

    def test_room_created_news_is_written(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert News.objects.filter(room=result.room, type=News.TypeChoices.ROOM_CREATED).exists()

    def test_importer_receives_no_added_to_room_mail(self, db, user, currency, parsed):
        mail.outbox.clear()

        run_import(parsed=parsed, user=user, currency=currency)

        assert mail.outbox == []

    def test_a_failing_import_leaves_no_half_room(self, db, user, currency, parsed):
        broken_assignments = [
            PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
            PersonAssignment(column="Elisabeth", kind=PersonAssignment.EXISTING, user_id=-1),
        ]

        with pytest.raises(User.DoesNotExist):
            run_import(
                parsed=parsed,
                user=user,
                currency=currency,
                person_assignments=broken_assignments,
                fire_event=False,
            )

        assert Room.objects.count() == 0
        assert ParentTransaction.objects.count() == 0


class TestImportServiceCreatesTransactions:
    def test_every_importable_row_becomes_a_transaction(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert ParentTransaction.objects.filter(room=result.room).count() == 2
        assert result.skipped_count == 1

    def test_zero_share_creates_no_child_transaction(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        cambio = ParentTransaction.objects.get(room=result.room, description="Cambio")
        assert cambio.child_transactions.count() == 1
        assert cambio.value == Decimal("25.20")

    def test_transactions_are_attributed_to_the_importer(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert all(transaction.created_by == user for transaction in ParentTransaction.objects.filter(room=result.room))
        assert all(
            child.created_by == user for child in ChildTransaction.objects.filter(parent_transaction__room=result.room)
        )

    def test_paid_at_is_timezone_aware(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        transaction = ParentTransaction.objects.filter(room=result.room).first()
        assert transaction.paid_at.tzinfo is not None

    def test_import_writes_a_single_summary_news_entry(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        import_news = News.objects.filter(room=result.room, message__contains="imported")
        assert import_news.count() == 1


class TestImportServiceBalances:
    def test_open_debt_matches_the_export_balance(self, db, user, currency, parsed):
        # The sample rows net out to 47.77 in favour of Kilian, matching the Gesamtbilanz line.
        result = run_import(parsed=parsed, user=user, currency=currency)

        debt = Debt.objects.get(room=result.room, settled=False)
        assert debt.creditor == user
        assert debt.value == Decimal("47.77")

    def test_settlement_row_becomes_a_settled_debt(self, db, user, currency):
        parsed = SplitwiseCsvParser().parse(
            build_file_like(
                [
                    "2023-03-06,Ikea,Möbel,100.00,EUR,50.00,-50.00",
                    "2023-04-01,Zahlung,Zahlung,50.00,EUR,-50.00,50.00",
                ]
            )
        )

        result = run_import(parsed=parsed, user=user, currency=currency)

        settled = Debt.objects.get(room=result.room, settled=True)
        assert settled.creditor == user
        assert settled.value == Decimal("50.00")
        assert settled.settled_at.isoformat() == "2023-04-01"
        # The settlement cancels the expense, so nothing is left open.
        assert not Debt.objects.filter(room=result.room, settled=False).exists()


class TestImportServicePeople:
    def test_guest_is_created_for_a_guest_assignment(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        guest = User.objects.get(name="Elisabeth")
        assert guest.is_guest is True
        assert guest.created_by == user
        assert result.created_guest_count == 1

    def test_existing_person_is_reused_instead_of_duplicated(self, db, user, currency, parsed):
        existing = GuestUserFactory(name="Elisabeth")
        assignments = [
            PersonAssignment(column="Kilian Karaus", kind=PersonAssignment.ME),
            PersonAssignment(column="Elisabeth", kind=PersonAssignment.EXISTING, user_id=existing.pk),
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, person_assignments=assignments)

        assert User.objects.filter(name="Elisabeth").count() == 1
        assert result.created_guest_count == 0
        assert UserConnectionToRoom.objects.filter(room=result.room, user=existing).exists()

    def test_importer_is_never_created_as_a_guest(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert User.objects.filter(name=user.name).count() == 1
        assert ParentTransaction.objects.filter(room=result.room, paid_by=user).exists()

    def test_room_has_one_member_per_person_column(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert result.room.users.count() == len(parsed.people)


class TestImportServiceCategories:
    def test_new_room_receives_the_full_base_category_set(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert RoomCategory.objects.filter(room=result.room).count() >= 10

    def test_every_transaction_category_belongs_to_the_room(self, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        room_category_ids = set(RoomCategory.objects.filter(room=result.room).values_list("category_id", flat=True))
        transaction_category_ids = set(
            ParentTransaction.objects.filter(room=result.room).values_list("category_id", flat=True)
        )
        assert transaction_category_ids <= room_category_ids

    def test_mapping_only_creates_no_new_categories(self, db, user, currency, parsed):
        before = Category.objects.count()

        run_import(parsed=parsed, user=user, currency=currency)

        assert Category.objects.count() == before

    def test_new_category_is_created_when_requested(self, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label="Möbel", kind=CategoryAssignment.NEW, name="Möbel", emoji="🛋️"),
            CategoryAssignment(label="Allgemein", kind=CategoryAssignment.EXISTING, slug="misc"),
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        created = Category.objects.get(name="Möbel")
        assert created.emoji == "🛋️"
        assert RoomCategory.objects.filter(room=result.room, category=created).exists()
        assert ParentTransaction.objects.filter(room=result.room, category=created).count() == 1

    def test_new_category_is_invisible_in_another_room(self, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label="Möbel", kind=CategoryAssignment.NEW, name="Möbel", emoji="🛋️"),
            CategoryAssignment(label="Allgemein", kind=CategoryAssignment.EXISTING, slug="misc"),
        ]
        run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        second_result = run_import(parsed=second_parsed, user=user, currency=currency)

        created = Category.objects.get(name="Möbel")
        assert not RoomCategory.objects.filter(room=second_result.room, category=created).exists()

    def test_unknown_slug_falls_back_to_the_room_default(self, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label=entry.label, kind=CategoryAssignment.EXISTING, slug="does-not-exist")
            for entry in parsed.categories
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        assert ParentTransaction.objects.filter(room=result.room, category__isnull=True).count() == 0


class TestImportServiceCurrency:
    def test_duplicate_currency_codes_do_not_break_the_import(self, db, user, currency, parsed):
        # Currency.code has no unique constraint, so a .get() would raise MultipleObjectsReturned.
        Currency.objects.create(name="Euro (duplicate)", sign="€", code="EUR")

        result = run_import(parsed=parsed, user=user, currency=currency)

        assert ParentTransaction.objects.filter(room=result.room).count() == 2

    def test_unknown_currency_code_falls_back_to_the_room_currency(self, db, user, currency):
        parsed = SplitwiseCsvParser().parse(
            build_file_like(
                ["2023-03-06,Ikea,Möbel,10.00,EUR,5.00,-5.00"],
            )
        )
        Currency.objects.filter(code="EUR").delete()
        fallback = Currency.objects.create(name="Pound", sign="£", code="GBP")

        result = run_import(parsed=parsed, user=user, currency=fallback)

        assert ParentTransaction.objects.filter(room=result.room, currency=fallback).count() == 1


class TestImportServiceRepeatedImports:
    def test_second_import_creates_a_separate_room(self, db, user, currency, parsed):
        first = run_import(parsed=parsed, user=user, currency=currency)
        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        second = run_import(parsed=second_parsed, user=user, currency=currency)

        assert first.room.pk != second.room.pk
        assert ParentTransaction.objects.filter(room=first.room).count() == 2
        assert ParentTransaction.objects.filter(room=second.room).count() == 2

    def test_repeated_import_does_not_touch_the_first_room(self, db, user, currency, parsed):
        first = run_import(parsed=parsed, user=user, currency=currency)
        before = set(ParentTransaction.objects.filter(room=first.room).values_list("pk", flat=True))

        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        run_import(parsed=second_parsed, user=user, currency=currency)

        after = set(ParentTransaction.objects.filter(room=first.room).values_list("pk", flat=True))
        assert before == after


class TestPersonCandidateService:
    def test_guests_from_other_rooms_are_offered(self, db, user, room, guest_user):
        from apps.importer.services.person_candidate_service import PersonCandidateService

        candidates = PersonCandidateService(user=user).get_candidates()

        assert guest_user in candidates

    def test_the_importer_is_not_a_candidate(self, db, user, room):
        from apps.importer.services.person_candidate_service import PersonCandidateService

        assert user not in PersonCandidateService(user=user).get_candidates()

    def test_name_match_ignores_case_and_padding(self, db, user, room):
        from apps.importer.services.person_candidate_service import PersonCandidateService

        friend = UserFactory(name="Elisabeth")
        room.users.add(friend)
        service = PersonCandidateService(user=user)

        assert service.match_by_name("  elisabeth ") == friend

    def test_unknown_name_matches_nothing(self, db, user, room):
        from apps.importer.services.person_candidate_service import PersonCandidateService

        assert PersonCandidateService(user=user).match_by_name("Nobody") is None
