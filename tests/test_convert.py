import csv
from pathlib import Path

import pytest

from cal2xl.convert import (
    FIELDS,
    SOURCE_FIELD,
    convert,
    ics_to_records,
    ics_to_rows,
    merge_ics,
    records_to_csv_bytes,
    write_csv,
)

# Invented events, so nothing anyone's real calendar contains ends up in the repo. The
# file is built to carry the things that actually break converters: a UTF-8 BOM, CRLF
# line endings, a folded description, a U+2019 smart quote, commas inside fields, an
# event with no LOCATION, and a timed event alongside the all-day ones.
SAMPLE_ICS = Path(__file__).parent / "fixtures" / "sample.ics"

# A second calendar whose events fall between sample.ics's, so a merge that failed to
# interleave would be visible rather than coincidentally correct.
OTHER_ICS = Path(__file__).parent / "fixtures" / "other.ics"


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


@pytest.fixture
def merged() -> list[dict[str, str]]:
    return merge_ics([("sample.ics", SAMPLE_ICS), ("other.ics", OTHER_ICS)])


def test_merge_interleaves_calendars_by_date(merged):
    assert len(merged) == 6
    assert [record["start"] for record in merged] == sorted(
        record["start"] for record in merged
    )
    # Second event comes from the other file, so the two are genuinely interleaved
    # rather than concatenated.
    assert merged[0]["summary"] == "Neighbourhood Potluck"
    assert merged[1]["summary"] == "Morning Litter Pick"


def test_merge_tags_each_event_with_its_calendar(merged):
    assert {record[SOURCE_FIELD] for record in merged} == {"sample.ics", "other.ics"}
    assert merged[1][SOURCE_FIELD] == "other.ics"


def test_single_calendar_gets_no_source_column():
    only_one = merge_ics([("sample.ics", SAMPLE_ICS)])

    assert all(SOURCE_FIELD not in record for record in only_one)
    assert list(only_one[0]) == list(FIELDS)


def test_merged_csv_carries_the_source_column(merged):
    lines = records_to_csv_bytes(merged)[3:].decode().split("\r\n")

    assert lines[0] == ",".join([*FIELDS, SOURCE_FIELD])
    assert lines[1].endswith(",sample.ics")
    assert len([line for line in lines if line.strip()]) == 7  # header + 6 events


def test_merge_names_the_calendar_that_failed(tmp_path):
    broken = tmp_path / "broken.ics"
    broken.write_bytes(b"this is not a calendar")

    with pytest.raises(ValueError, match="broken.ics"):
        merge_ics([("sample.ics", SAMPLE_ICS), ("broken.ics", broken)])


def test_events_without_a_start_sort_last():
    records = merge_ics(
        [("a", SAMPLE_ICS)], label_source=False
    ) + [dict.fromkeys(FIELDS, "")]
    records.sort(key=lambda record: (record["start"] == "", record["start"]))

    assert records[-1]["start"] == ""


def test_convert_defaults_output_next_to_input(tmp_path):
    input_path = tmp_path / "calendar.ics"
    input_path.write_bytes(SAMPLE_ICS.read_bytes())

    assert convert(input_path) == 4
    assert (tmp_path / "calendar.csv").is_file()
