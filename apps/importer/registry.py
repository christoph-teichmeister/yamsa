from apps.importer.parsers.base import BaseImportParser
from apps.importer.parsers.splitwise import SplitwiseCsvParser

_PARSER_CLASSES: tuple[type[BaseImportParser], ...] = (SplitwiseCsvParser,)

PARSERS: dict[str, type[BaseImportParser]] = {parser.source_key: parser for parser in _PARSER_CLASSES}


def get_source_choices() -> list[tuple[str, str]]:
    return [(parser.source_key, parser.label) for parser in _PARSER_CLASSES]


def get_parser(source_key: str) -> BaseImportParser:
    parser_class = PARSERS.get(source_key)
    if parser_class is None:
        error_message = f"Unknown import source '{source_key}'"
        raise KeyError(error_message)
    return parser_class()
