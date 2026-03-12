import csv
import io


class CsvExportMixin:
    """Encapsulate shared CSV metadata + buffering logic."""

    _FORMULA_TRIGGERS = frozenset("=+-@\t\r")

    def _iter_rows(self, room, queryset, timestamp):
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        yield from self._write_metadata(writer, buffer, room, timestamp)
        yield from self._write_rows(writer, buffer, queryset, timestamp)

    def _write_metadata(self, writer, buffer, room, timestamp):
        metadata = [
            ["Room Slug", room.slug],
            ["Room Name", room.name],
            ["Export Timestamp", timestamp.isoformat()],
        ]

        for row in metadata:
            writer.writerow(row)
            yield self._pop_buffer(buffer)

        writer.writerow([])
        yield self._pop_buffer(buffer)

        writer.writerow(self.HEADER)
        yield self._pop_buffer(buffer)

    def _write_rows(self, writer, buffer, queryset, timestamp):
        raise NotImplementedError

    def _pop_buffer(self, buffer):
        value = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return value

    def _safe(self, value):
        if value is None:
            return ""
        string_value = str(value)
        if string_value and string_value[0] in self._FORMULA_TRIGGERS:
            return f"'{string_value}"
        return string_value
