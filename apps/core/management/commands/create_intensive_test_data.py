import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.utils.timezone import now

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.models import Category, ChildTransaction, ParentTransaction, RoomCategory
from apps.transaction.models.constants import BASE_CATEGORY_SLUGS, DEFAULT_CATEGORY_SLUG

_CATEGORY_DATA = {
    "accommodation": ("Accommodation", "🏠", "#4A90D9", 0),
    "groceries": ("Groceries", "🛒", "#5CB85C", 1),
    "restaurants-and-bars": ("Restaurants & Bars", "🍴", "#F0AD4E", 2),
    "transport": ("Transport", "🚗", "#337AB7", 3),
    "activities": ("Activities", "🎯", "#9B59B6", 4),
    "household": ("Household", "🏡", "#1ABC9C", 5),
    "shopping": ("Shopping", "🛍️", "#E74C3C", 6),
    "health": ("Health", "❤️", "#E91E63", 7),
    "celebrations": ("Celebrations", "🎉", "#FF9800", 8),
    DEFAULT_CATEGORY_SLUG: ("Miscellaneous", "🌀", "#ADB5BD", 9),
}

_TRANSACTION_SCENARIOS = [
    ("Hotel check-in", "accommodation", 0, [0, 1, 2, 3], Decimal("480.00")),
    ("Supermarket run", "groceries", 1, [0, 1, 2], Decimal("87.50")),
    ("Restaurant dinner", "restaurants-and-bars", 0, [0, 1, 2, 3], Decimal("156.80")),
    ("Train tickets", "transport", 2, [0, 1, 2], Decimal("63.00")),
    ("Museum entry", "activities", 1, [0, 1, 2, 3], Decimal("44.00")),
    ("Groceries day 2", "groceries", 3, [0, 1, 2, 3], Decimal("112.30")),
    ("Lunch café", "restaurants-and-bars", 0, [0, 1], Decimal("38.90")),
    ("Bus tour", "activities", 2, [0, 1, 2, 3], Decimal("96.00")),
    ("Pharmacy", "health", 1, [1], Decimal("23.45")),
    ("Souvenir shopping", "shopping", 0, [0, 1, 2], Decimal("75.00")),
    ("Gas station", "transport", 3, [0, 1, 2, 3], Decimal("88.20")),
    ("Airbnb booking", "accommodation", 2, [0, 1, 2, 3], Decimal("620.00")),
    ("Bar night out", "restaurants-and-bars", 1, [0, 1, 2, 3], Decimal("203.50")),
    ("Grocery store", "groceries", 0, [0, 1, 2], Decimal("94.70")),
    ("Taxi ride", "transport", 3, [0, 1, 2, 3], Decimal("35.00")),
    ("Concert tickets", "celebrations", 2, [0, 1, 2, 3], Decimal("280.00")),
    ("Bakery breakfast", "restaurants-and-bars", 0, [0, 1], Decimal("24.60")),
    ("Parking fee", "transport", 1, [0, 1, 2], Decimal("18.00")),
    ("Sunscreen & supplies", "shopping", 3, [0, 1, 2, 3], Decimal("47.80")),
    ("Medication", "health", 2, [2], Decimal("31.20")),
    ("Electricity bill", "household", 0, [0, 1, 2], Decimal("145.00")),
    ("Internet subscription", "household", 1, [0, 1, 2, 3], Decimal("39.99")),
    ("Cleaning supplies", "household", 2, [0, 1, 2], Decimal("28.60")),
    ("Birthday dinner", "celebrations", 3, [0, 1, 2, 3], Decimal("312.00")),
    ("Hiking gear rental", "activities", 0, [0, 1, 2], Decimal("66.00")),
]


class Command(BaseCommand):
    """Command for creating an intensive set of test data"""

    help = "Creates an intensive set of test data (same users as restore_test_data, many more rooms/transactions/debts)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation of intensive test data even in production environments',
        )

    def handle(self, *args, **options):
        # Check if we're in a safe environment
        if not settings.DEBUG and not options.get('force'):
            raise CommandError(
                "This command can only be run in development/test environments (DEBUG=True) "
                "or with the --force flag. Use --force to override this safety check."
            )
        self.create_intensive_test_data()

    @staticmethod
    def _create_users():
        # Hashed password "Admin123$"
        default_password = (
            "argon2$argon2id$v=19$m=102400,t=2,p=8$ZE1LcE9TYmpDZTNmR1I3aVdHc"
            "jc4MQ$4JN0SLWYv/lI9oPPDY06UouiWdOpgR8BI65O+SeXsuE"
        )

        superuser, created = User.objects.get_or_create(
            email="admin@yamsa.local",
            defaults={
                "name": "yamsa-admin",
                "password": default_password,
                "is_superuser": True,
                "is_staff": True,
                "is_guest": False,
            },
        )
        print(f'User ID: {superuser.id}, Name: "{superuser.name}" {"created" if created else "found"}')

        registered_users = []
        for i in range(1, 6):
            registered_user, created = User.objects.get_or_create(
                email=f"registered_user_{i}@yamsa.local",
                defaults={
                    "name": f"registered_user_{i}",
                    "password": default_password,
                    "is_superuser": False,
                    "is_staff": False,
                    "is_guest": False,
                },
            )
            registered_users.append(registered_user)
            print(f'User ID: {registered_user.id}, Name: "{registered_user.name}" {"created" if created else "found"}')

        guest_users = []
        for i in range(1, 6):
            guest_user, created = User.objects.get_or_create(
                name=f"guest_{i}",
                is_guest=True,
                defaults={
                    "password": make_password(f"guest_{i}"),
                    "is_superuser": False,
                    "is_staff": False,
                },
            )
            guest_users.append(guest_user)
            print(f'User ID: {guest_user.id}, Name: "{guest_user.name}" {"created" if created else "found"}')

        return {
            "admin": superuser,
            "registered_users": registered_users,
            "guest_users": guest_users,
        }

    @staticmethod
    def _create_categories():
        categories = {}
        for slug in BASE_CATEGORY_SLUGS:
            name, emoji, color, order_index = _CATEGORY_DATA[slug]
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "emoji": emoji,
                    "color": color,
                    "order_index": order_index,
                    "is_default": slug == DEFAULT_CATEGORY_SLUG,
                },
            )
            categories[slug] = category
            print(f'Category: "{category.name}" ({slug}) created')
        return categories

    @staticmethod
    def _create_currencies():
        eur, _ = Currency.objects.get_or_create(code="EUR", defaults={"name": "Euro", "sign": "€"})
        gbp, _ = Currency.objects.get_or_create(code="GBP", defaults={"name": "Pound Sterling", "sign": "£"})
        usd, _ = Currency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "sign": "$"})
        chf, _ = Currency.objects.get_or_create(code="CHF", defaults={"name": "Swiss Franc", "sign": "CHF"})
        print("Currencies ensured: EUR, GBP, USD, CHF")
        return {"EUR": eur, "GBP": gbp, "USD": usd, "CHF": chf}

    @staticmethod
    def _create_rooms(currencies, categories, users_dict):
        registered_users = users_dict["registered_users"]
        guest_users = users_dict["guest_users"]
        admin = users_dict["admin"]

        room_configs = [
            {
                "name": "Summer Trip 2024",
                "description": "Our amazing summer vacation",
                "currency": currencies["EUR"],
                "members": registered_users[:4] + guest_users[:2],
                "creator": registered_users[0],
            },
            {
                "name": "Shared Apartment",
                "description": "Monthly shared household expenses",
                "currency": currencies["EUR"],
                "members": registered_users[:3] + guest_users[:1],
                "creator": registered_users[1],
            },
            {
                "name": "London Weekend",
                "description": "Weekend trip to London",
                "currency": currencies["GBP"],
                "members": registered_users[1:5] + guest_users[1:3],
                "creator": registered_users[2],
            },
            {
                "name": "Office Lunch Group",
                "description": "Weekly office lunch expenses",
                "currency": currencies["EUR"],
                "members": registered_users + guest_users[:3],
                "creator": registered_users[3],
            },
            {
                "name": "New York Business Trip",
                "description": "Business trip expenses",
                "currency": currencies["USD"],
                "members": [admin, *registered_users[:3]],
                "creator": admin,
            },
            {
                "name": "Ski Weekend",
                "description": "Annual ski trip in the Alps",
                "currency": currencies["CHF"],
                "members": registered_users[2:] + guest_users[2:],
                "creator": registered_users[4],
            },
        ]

        rooms = []
        for config in room_configs:
            room = Room.objects.create(
                name=config["name"],
                slug=uuid.uuid4(),
                description=config["description"],
                preferred_currency=config["currency"],
                created_by_id=config["creator"].id,
            )

            for user in config["members"]:
                UserConnectionToRoom.objects.create(
                    user=user,
                    room=room,
                    created_by_id=config["creator"].id,
                )

            for order_index, slug in enumerate(BASE_CATEGORY_SLUGS):
                RoomCategory.objects.create(
                    room=room,
                    category=categories[slug],
                    order_index=order_index,
                    is_default=(slug == DEFAULT_CATEGORY_SLUG),
                    created_by_id=config["creator"].id,
                )

            member_count = len(config["members"])
            print(f'Room ID: {room.id}, Name: "{room.name}" created with {member_count} members')
            rooms.append((room, config))

        return rooms

    @staticmethod
    def _create_transactions(rooms, categories):
        base_date = now() - timedelta(days=90)

        for room, config in rooms:
            # Use member_ids from config to ensure deterministic ordering
            member_ids = [user.id for user in config["members"]]
            if len(member_ids) < 2:
                continue

            currency = config["currency"]
            creator = config["creator"]

            for day_offset, (desc, cat_slug, payer_idx, split_idxs, total_amount) in enumerate(_TRANSACTION_SCENARIOS):
                payer_id = member_ids[payer_idx % len(member_ids)]

                seen = set()
                unique_split_ids = []
                for i in split_idxs:
                    uid = member_ids[i % len(member_ids)]
                    if uid not in seen:
                        seen.add(uid)
                        unique_split_ids.append(uid)

                category = categories.get(cat_slug, categories[DEFAULT_CATEGORY_SLUG])

                parent = ParentTransaction.objects.create(
                    description=desc,
                    paid_by_id=payer_id,
                    room=room,
                    currency=currency,
                    category=category,
                    paid_at=base_date + timedelta(days=day_offset),
                    created_by_id=creator.id,
                )

                # Convert to cents to avoid rounding issues
                total_cents = int(total_amount * 100)
                num_split = len(unique_split_ids)
                base_share_cents, remainder_cents = divmod(total_cents, num_split)

                for idx, uid in enumerate(unique_split_ids):
                    # Add one extra cent to the first 'remainder_cents' children
                    share_cents = base_share_cents + (1 if idx < remainder_cents else 0)
                    share_value = Decimal(share_cents) / Decimal(100)

                    ChildTransaction.objects.create(
                        parent_transaction=parent,
                        paid_for_id=uid,
                        value=share_value,
                        created_by_id=creator.id,
                    )

            print(f'Transactions created for room "{room.name}": {len(_TRANSACTION_SCENARIOS)} parent transactions')

    @staticmethod
    def _create_debts(rooms):
        for room, config in rooms:
            # Use member_ids from config to ensure deterministic ordering
            member_ids = [user.id for user in config["members"]]
            if len(member_ids) < 2:
                continue

            currency = config["currency"]
            creator = config["creator"]

            for i in range(len(member_ids) - 1):
                debitor_id = member_ids[i]
                creditor_id = member_ids[(i + 1) % len(member_ids)]
                if debitor_id == creditor_id:
                    continue

                settled = i % 3 == 0
                Debt.objects.create(
                    debitor_id=debitor_id,
                    creditor_id=creditor_id,
                    room=room,
                    value=Decimal(f"{(i + 1) * 15}.{(i * 7) % 100:02d}"),
                    currency=currency,
                    settled=settled,
                    settled_at=now().date() if settled else None,
                    created_by_id=creator.id,
                )

            print(f'Debts created for room "{room.name}": {len(member_ids) - 1} debts')

    @staticmethod
    @transaction.atomic
    def create_intensive_test_data():
        self = Command

        categories = self._create_categories()
        users_dict = self._create_users()
        currencies = self._create_currencies()
        rooms = self._create_rooms(currencies, categories, users_dict)
        self._create_transactions(rooms, categories)
        self._create_debts(rooms)
