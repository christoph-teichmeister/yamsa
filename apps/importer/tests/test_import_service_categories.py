from apps.importer.dataclasses import CategoryAssignment
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import DEFAULT_ROWS, build_file_like
from apps.transaction.models import Category, ParentTransaction, RoomCategory


class TestImportServiceCategories:
    def test_new_room_receives_the_full_base_category_set(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert RoomCategory.objects.filter(room=result.room).count() >= 10

    def test_every_transaction_category_belongs_to_the_room(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        room_category_ids = set(RoomCategory.objects.filter(room=result.room).values_list("category_id", flat=True))
        transaction_category_ids = set(
            ParentTransaction.objects.filter(room=result.room).values_list("category_id", flat=True)
        )
        assert transaction_category_ids <= room_category_ids

    def test_mapping_only_creates_no_new_categories(self, run_import, db, user, currency, parsed):
        before = Category.objects.count()

        run_import(parsed=parsed, user=user, currency=currency)

        assert Category.objects.count() == before

    def test_new_category_is_created_when_requested(self, run_import, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label="Möbel", kind=CategoryAssignment.NEW, name="Möbel", emoji="🛋️"),
            CategoryAssignment(label="Allgemein", kind=CategoryAssignment.EXISTING, slug="misc"),
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        created = Category.objects.get(name="Möbel")
        assert created.emoji == "🛋️"
        assert RoomCategory.objects.filter(room=result.room, category=created).exists()
        assert ParentTransaction.objects.filter(room=result.room, category=created).count() == 1

    def test_new_category_is_invisible_in_another_room(self, run_import, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label="Möbel", kind=CategoryAssignment.NEW, name="Möbel", emoji="🛋️"),
            CategoryAssignment(label="Allgemein", kind=CategoryAssignment.EXISTING, slug="misc"),
        ]
        run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        second_result = run_import(parsed=second_parsed, user=user, currency=currency)

        created = Category.objects.get(name="Möbel")
        assert not RoomCategory.objects.filter(room=second_result.room, category=created).exists()

    def test_unknown_slug_falls_back_to_the_room_default(self, run_import, db, user, currency, parsed):
        assignments = [
            CategoryAssignment(label=entry.label, kind=CategoryAssignment.EXISTING, slug="does-not-exist")
            for entry in parsed.categories
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        assert ParentTransaction.objects.filter(room=result.room, category__isnull=True).count() == 0

    def test_two_labels_mapped_to_the_same_new_name_create_one_category(self, db, user, currency, run_import):
        parsed = SplitwiseCsvParser().parse(
            build_file_like(
                [
                    "2023-03-06,Sofa,Möbel,10.00,EUR,5.00,-5.00",
                    "2023-03-07,Lampe,Zuhause - Sonstiges,10.00,EUR,5.00,-5.00",
                ]
            )
        )
        assignments = [
            CategoryAssignment(label=entry.label, kind=CategoryAssignment.NEW, name="Wohnen", emoji="🛋️")
            for entry in parsed.categories
        ]

        result = run_import(parsed=parsed, user=user, currency=currency, category_assignments=assignments)

        assert Category.objects.filter(name="Wohnen").count() == 1
        assert RoomCategory.objects.filter(room=result.room, category__name="Wohnen").count() == 1
        assert result.created_category_count == 1
