import pytest

from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserCategories:
    @pytest.mark.parametrize(
        ("label", "expected_slug"),
        [
            ("Allgemein", "misc"),
            ("Lebensmittel", "groceries"),
            ("Restaurant", "restaurants-and-bars"),
            ("Treibstoff", "transport"),
            ("Möbel", "household"),
            ("Zuhause - Sonstiges", "household"),
            ("Kino", "activities"),
            ("Voellig Unbekannt", "misc"),
        ],
    )
    def test_category_label_maps_to_slug(self, label, expected_slug):
        assert SplitwiseCsvParser.map_category_slug(label) == expected_slug

    def test_unknown_label_gets_the_fallback_emoji(self):
        assert SplitwiseCsvParser.suggest_emoji("Voellig Unbekannt") == "🏷️"

    def test_known_label_gets_a_specific_emoji(self):
        assert SplitwiseCsvParser.suggest_emoji("Treibstoff") == "⛽"

    def test_categories_are_counted_and_sorted_by_frequency(self):
        result = parse(
            [
                "2023-03-06,A,Restaurant,10.00,EUR,5.00,-5.00",
                "2023-03-07,B,Möbel,10.00,EUR,5.00,-5.00",
                "2023-03-08,C,Restaurant,10.00,EUR,5.00,-5.00",
            ]
        )

        assert [(entry.label, entry.transaction_count) for entry in result.categories] == [
            ("Restaurant", 2),
            ("Möbel", 1),
        ]
