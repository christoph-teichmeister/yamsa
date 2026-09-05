import io

from django.core.files.uploadedfile import SimpleUploadedFile

SPLITWISE_HEADER = "Datum,Beschreibung,Kategorie,Kosten,Währung,Kilian Karaus,Elisabeth"

# Two importable rows plus the balance summary row every Splitwise export ends with.
DEFAULT_ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
    "2026-09-05,Gesamtbilanz,,,EUR,47.77,-47.77",
]


def build_csv(rows: list[str], header: str = SPLITWISE_HEADER) -> str:
    return "\n".join([header, *rows]) + "\n"


def build_upload(rows: list[str], header: str = SPLITWISE_HEADER, name: str = "export.csv") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, build_csv(rows, header).encode("utf-8"), content_type="text/csv")


def build_file_like(rows: list[str], header: str = SPLITWISE_HEADER) -> io.BytesIO:
    return io.BytesIO(build_csv(rows, header).encode("utf-8"))
