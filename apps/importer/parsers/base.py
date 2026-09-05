from abc import ABC, abstractmethod

from apps.importer.dataclasses import ParsedImport

MAX_IMPORT_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_IMPORT_ROWS = 2000


class ImportParseError(Exception):
    """Raised when a file cannot be parsed at all — as opposed to single rows being skipped."""


class BaseImportParser(ABC):
    source_key: str
    label: str
    accepted_extensions: tuple[str, ...] = (".csv",)

    @abstractmethod
    def parse(self, uploaded_file) -> ParsedImport:
        """Turn an uploaded file into a ParsedImport without touching the database."""
