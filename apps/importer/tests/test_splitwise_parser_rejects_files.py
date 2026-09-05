import io

import pytest

from apps.importer.parsers.exceptions import ImportParseError
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserRejectsFiles:
    def test_empty_file_is_rejected(self):
        with pytest.raises(ImportParseError):
            SplitwiseCsvParser().parse(build_file_like([], header=""))

    def test_header_without_person_columns_is_rejected(self):
        with pytest.raises(ImportParseError, match="person columns"):
            parse(["2023-03-06,A,Allgemein,10.00,EUR"], header="Datum,Beschreibung,Kategorie,Kosten,Währung")

    def test_non_utf8_file_is_rejected(self):
        with pytest.raises(ImportParseError, match="UTF-8"):
            SplitwiseCsvParser().parse(io.BytesIO(b"\xff\xfe\x00invalid"))
