import csv
from pathlib import Path

import pytest

from cal2xl.convert import (
    FIELDS,
    convert,
    ics_to_records,
    ics_to_rows,
    records_to_csv_bytes,
    write_csv,
)

# Invented events, so nothing anyone's real calendar contains ends up in the repo. The
# file is built to carry the things that actually break converters: a UTF-8 BOM, CRLF
# line endings, a folded description, a U+2019 smart quote, commas inside fields, an
# event with no LOCATION, and a timed event alongside the all-day ones.
SAMPLE_ICS = Path(__file__).parent / "fixtures" / "sample.ics"


@pytest.fixture
def rows() -> list[list[str]]:
    return ics_to_rows(SAMPLE_ICS)


def test_parses_every_event(rows):
    assert len(rows) == 4
    assert all(len(row) == len(FIELDS) for row in rows)


def test_first_event_fields(rows):
    start, end, location, summary, description = rows[0]
    assert start == "2026-07-26"
    assert end == "2026-07-27"
    assert location == "12 Elm Street, Springfield"
    assert summary == "Neighbourhood Potluck"
    assert description.startswith("Bring a dish to share.")


def test_folded_description_is_rejoined(rows):
    # The line is folded across three physical lines in the file; icalendar unfolds it.
    assert "anything that needs reheating is best avoided." in rows[0][4]
    assert "\r\n " not in rows[0][4]


def test_timed_event_keeps_its_time(rows):
    start, end, _, summary, _ = rows[2]
    assert summary == "Book Swap"
    assert start == "2026-09-15 18:00:00+00:00"
    assert end == "2026-09-15 20:00:00+00:00"


def test_missing_fields_become_empty_strings(rows):
    town_hall = next(row for row in rows if row[3] == "Town Hall on the New Bus Route")
    assert town_hall[2] == ""


def test_csv_round_trip(tmp_path, rows):
    output_path = tmp_path / "out.csv"
    assert write_csv(rows, output_path) == len(rows)

    with output_path.open(newline="", encoding="utf-8-sig") as fin:
        records = list(csv.reader(fin))

    assert records[0] == list(FIELDS)
    assert records[1:] == rows
    # No blank rows interleaved by a stray \r (the newline="" contract).
    assert all(record for record in records)


def test_commas_in_fields_are_quoted(tmp_path, rows):
    output_path = tmp_path / "out.csv"
    write_csv(rows, output_path)

    text = output_path.read_text(encoding="utf-8-sig")
    assert '"8 Bridge Road, Riverside, Ashford"' in text


def test_csv_is_utf8_with_bom(tmp_path, rows):
    output_path = tmp_path / "out.csv"
    write_csv(rows, output_path)

    raw = output_path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    # The first event's description contains a U+2019 right single quote, and the
    # fourth event's summary an é.
    assert "doesn’t".encode() in raw
    assert "Repair Café".encode() in raw


def test_parses_uploaded_bytes(rows):
    # The web app hands icalendar the raw upload. The fixture carries a UTF-8 BOM,
    # which parses from bytes but blows up if it is decoded to str first -- so this is
    # the test that keeps a well-meaning .decode() out of the upload path.
    records = ics_to_records(SAMPLE_ICS.read_bytes())
    assert [[record[field] for field in FIELDS] for record in records] == rows


def test_web_and_desktop_csv_are_byte_identical(tmp_path, rows):
    output_path = tmp_path / "out.csv"
    write_csv(rows, output_path)

    assert records_to_csv_bytes(ics_to_records(SAMPLE_ICS)) == output_path.read_bytes()


def test_renamed_column_survives_into_the_header():
    # The spreadsheet widget lets people rename a column, so the header comes from the
    # records rather than from FIELDS.
    renamed = [{"when": "2026-07-26", "what": "Potluck"}]
    header = records_to_csv_bytes(renamed)[3:].split(b"\r\n")[0]
    assert header == b"when,what"


def test_convert_defaults_output_next_to_input(tmp_path):
    input_path = tmp_path / "calendar.ics"
    input_path.write_bytes(SAMPLE_ICS.read_bytes())

    assert convert(input_path) == 4
    assert (tmp_path / "calendar.csv").is_file()
