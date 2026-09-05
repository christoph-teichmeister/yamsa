import io

from django.core.files.uploadedfile import SimpleUploadedFile

SPLITWISE_HEADER = "Datum,Beschreibung,Kategorie,Kosten,Währung,Kilian Karaus,Elisabeth"


def build_csv(rows: list[str], header: str = SPLITWISE_HEADER) -> str:
    return "\n".join([header, *rows]) + "\n"


def build_upload(rows: list[str], header: str = SPLITWISE_HEADER, name: str = "export.csv") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, build_csv(rows, header).encode("utf-8"), content_type="text/csv")


def build_file_like(rows: list[str], header: str = SPLITWISE_HEADER) -> io.BytesIO:
    return io.BytesIO(build_csv(rows, header).encode("utf-8"))
