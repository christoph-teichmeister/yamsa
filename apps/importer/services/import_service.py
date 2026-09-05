from datetime import datetime, time

from django.utils import timezone

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.importer.dataclasses import (
    CategoryAssignment,
    ImportResult,
    ParsedImport,
    PersonAssignment,
)
from apps.importer.session import resolve_currencies_by_code
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService


class ImportService:
    """
    Writes a ParsedImport into a brand-new room.

    Must run inside the caller's transaction.atomic(); the debt recalculation is deliberately
    left to the TransactionsImported event so it happens once, after the block exits.
    """

    def __init__(self, *, parsed: ParsedImport, user: User):
        self.parsed = parsed
        self.user = user

    def process(
        self,
        *,
        room_name: str,
        room_description: str,
        currency: Currency,
        person_assignments: list[PersonAssignment],
        category_assignments: list[CategoryAssignment],
    ) -> ImportResult:
        room = self._create_room(name=room_name, description=room_description, currency=currency)
        users_by_column, created_guest_count, deferred_connections = self._resolve_people(
            room=room, assignments=person_assignments
        )
        categories_by_label, created_category_count = self._resolve_categories(
            room=room, assignments=category_assignments
        )
        currencies_by_code = self._resolve_currencies(fallback=currency)

        self._create_transactions(
            room=room,
            users_by_column=users_by_column,
            categories_by_label=categories_by_label,
            currencies_by_code=currencies_by_code,
        )
        self._create_settlements(
            room=room,
            users_by_column=users_by_column,
            currencies_by_code=currencies_by_code,
        )

        return ImportResult(
            room=room,
            transaction_count=len(self.parsed.transactions),
            settlement_count=len(self.parsed.settlements),
            skipped_count=len(self.parsed.skipped_rows),
            created_category_count=created_category_count,
            created_guest_count=created_guest_count,
            deferred_connections=deferred_connections,
        )

    def _create_room(self, *, name: str, description: str, currency: Currency) -> Room:
        room = Room(name=name, description=description, preferred_currency=currency)
        # create_news_on_room_created reads room.created_by.name, so this must be set before save().
        room.created_by = self.user
        room.save()

        # created_by must match the user, otherwise the "you were added to a room" mail fires for the importer.
        connection = UserConnectionToRoom(user=self.user, room=room, user_has_seen_this_room=True)
        connection.created_by = self.user
        connection.save()

        return room

    def _resolve_people(
        self, *, room: Room, assignments: list[PersonAssignment]
    ) -> tuple[dict[str, User], int, list[User]]:
        users_by_column: dict[str, User] = {}
        created_guest_count = 0
        deferred: list[User] = []

        for assignment in assignments:
            if assignment.kind == PersonAssignment.ME:
                users_by_column[assignment.column] = self.user
                continue

            if assignment.kind == PersonAssignment.EXISTING:
                existing = User.objects.get(pk=assignment.user_id)
                users_by_column[assignment.column] = existing
                # Connecting an existing non-guest emits webpush and email from inside Model.save().
                # Doing that here would run HTTP and SMTP inside the caller's atomic block (#333), so
                # the caller connects them once the transaction has committed.
                deferred.append(existing)
                continue

            guest = User(name=assignment.guest_name or assignment.column, is_guest=True)
            guest.created_by = self.user
            guest.save()
            created_guest_count += 1
            users_by_column[assignment.column] = guest
            # Guest connections are safe here: both handlers return early for guests.
            self.connect(user=guest, room=room)

        return users_by_column, created_guest_count, deferred

    def connect(self, *, user: User, room: Room) -> None:
        connection = UserConnectionToRoom(user=user, room=room)
        connection.created_by = self.user
        connection.save()

    def _resolve_categories(self, *, room: Room, assignments: list[CategoryAssignment]) -> tuple[dict, int]:
        service = RoomCategoryService(room=room)
        # ParentTransaction.save() only triggers _ensure_defaults when no category is set, and the
        # import always sets one — so the room's RoomCategory rows have to be created explicitly here.
        room_categories = list(service.get_category_queryset())
        categories_by_slug = {category.slug: category for category in room_categories}

        categories_by_label: dict[str, Category] = {}
        created_category_count = 0
        # Two source labels can ask for the same new category name; creating it twice would leave
        # the room with two categories a user cannot tell apart.
        created_by_name: dict[str, Category] = {}

        for assignment in assignments:
            if assignment.kind == CategoryAssignment.NEW:
                key = assignment.name.strip().casefold()
                category = created_by_name.get(key)
                if category is None:
                    category = service.create_room_category(name=assignment.name, emoji=assignment.emoji).category
                    created_by_name[key] = category
                    created_category_count += 1
                categories_by_label[assignment.label] = category
                continue

            category = categories_by_slug.get(assignment.slug)
            if category is None:
                category = service.get_default_category()
            categories_by_label[assignment.label] = category

        return categories_by_label, created_category_count

    def _resolve_currencies(self, *, fallback: Currency) -> dict[str, Currency]:
        matches = resolve_currencies_by_code(self.parsed.currency_codes)
        return {code: match or fallback for code, match in matches.items()}

    def _create_transactions(
        self,
        *,
        room: Room,
        users_by_column: dict[str, User],
        categories_by_label: dict,
        currencies_by_code: dict[str, Currency],
    ) -> None:
        for parsed_transaction in self.parsed.transactions:
            parent = ParentTransaction(
                description=parsed_transaction.description,
                further_notes=parsed_transaction.further_notes or None,
                paid_by=users_by_column[parsed_transaction.payer],
                paid_at=self._as_aware(parsed_transaction.paid_at),
                room=room,
                currency=currencies_by_code[parsed_transaction.currency_code],
                category=categories_by_label[parsed_transaction.category_label],
            )
            parent.created_by = self.user
            # bulk_create would skip FullCleanOnSaveMixin, which enforces the 50 character description cap.
            parent.save()

            for share in parsed_transaction.shares:
                child = ChildTransaction(
                    parent_transaction=parent,
                    paid_for=users_by_column[share.person],
                    value=share.value,
                )
                child.created_by = self.user
                child.save()

    def _create_settlements(
        self,
        *,
        room: Room,
        users_by_column: dict[str, User],
        currencies_by_code: dict[str, Currency],
    ) -> None:
        for parsed_settlement in self.parsed.settlements:
            debt = Debt(
                debitor=users_by_column[parsed_settlement.debitor],
                creditor=users_by_column[parsed_settlement.creditor],
                room=room,
                value=parsed_settlement.value,
                currency=currencies_by_code[parsed_settlement.currency_code],
                settled=True,
                settled_at=parsed_settlement.settled_at,
            )
            debt.created_by = self.user
            debt.save()

    @staticmethod
    def _as_aware(value) -> datetime:
        # USE_TZ is on, so a naive datetime would warn and store the wrong instant. Midday rather
        # than midnight because some zones move their DST boundary through 00:00, where make_aware
        # raises NonExistentTimeError.
        return timezone.make_aware(datetime.combine(value, time(hour=12)), timezone.get_current_timezone())
