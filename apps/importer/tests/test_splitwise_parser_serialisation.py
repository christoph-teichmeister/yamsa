import json

from apps.importer.dataclasses import ParsedImport
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserSerialisation:
    def test_parsed_import_survives_a_json_round_trip(self):
        result = parse(
            [
                "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
                "2024-10-04,Zahlung,Zahlung,10.00,EUR,10.00,-10.00",
                "2026-09-05,Gesamtbilanz,,,EUR,5.00,-5.00",
            ]
        )

        restored = ParsedImport.from_payload(json.loads(json.dumps(result.as_payload())))

        assert restored == result
