from collections.abc import Iterable, Sequence
from pathlib import Path
import csv
import io

import icalendar

FIELDS = ("start", "end", "location", "summary", "description")

# A calendar source is anything icalendar itself knows how to read: a path, the raw
# bytes of an upload, or already-decoded text. Bytes are the safe currency -- an .ics
# exported with a UTF-8 BOM parses from bytes but fails if decoded naively first.
Source = Path | bytes | str


def ics_to_records(source: Source) -> list[dict[str, str]]:
    """Parse a calendar into one dict per event, keyed by FIELDS."""
    cal = icalendar.Calendar.from_ical(source)
    return [
        {
            field: "" if (value := getattr(event, field, None)) is None else str(value)
            for field in FIELDS
        }
        for event in cal.events
    ]


def ics_to_rows(source: Source) -> list[list[str]]:
    """Parse a calendar into a list of row-lists, each ordered like FIELDS."""
    return [[record[field] for field in FIELDS] for record in ics_to_records(source)]


def csv_bytes(header: Sequence[str], rows: Iterable[Sequence[str]]) -> bytes:
    """Encode a header and rows the one way every front end should write CSV.

    newline="" is the csv module's contract, so rows end in a single CRLF; utf-8-sig
    makes Excel read the file as UTF-8 rather than the local ANSI codepage.
    """
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def records_to_csv_bytes(records: Sequence[dict[str, str]]) -> bytes:
    """Encode records to CSV, taking the header from the records' own keys.

    Reading the keys rather than assuming FIELDS means columns the user renamed or
    added in a spreadsheet view survive into the file.
    """
    fields = list(dict.fromkeys(key for record in records for key in record))
    fields = fields or list(FIELDS)
    return csv_bytes(fields, [[record.get(field, "") for field in fields] for record in records])


def write_csv(rows: Iterable[Sequence[str]], output_path: Path) -> int:
    """Write rows under a FIELDS header. Returns the number of data rows written."""
    rows = list(rows)
    output_path.write_bytes(csv_bytes(FIELDS, rows))
    return len(rows)


def convert(input_path: Path, output_path: Path | None = None) -> int:
    """Convert an .ics straight to a .csv, defaulting to a sibling file."""
    output_path = output_path if output_path is not None else input_path.with_suffix(".csv")
    return write_csv(ics_to_rows(input_path), output_path)
