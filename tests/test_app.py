"""Guards for the marimo web app.

Skipped wherever marimo is not installed -- the executable build environment does not
need it. Run these with `uv run --group web pytest`.
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("marimo")

import marimo as mo  # noqa: E402

from cal2xl.convert import FIELDS, ics_to_records, records_to_csv_bytes  # noqa: E402

SAMPLE_ICS = Path(__file__).parent / "fixtures" / "sample.ics"

# Importing the notebook applies its module-level patches; it lives beside the package
# rather than in it, because marimo resolves a notebook's local imports against the
# notebook's own directory when it builds the WASM bundle.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import app  # noqa: E402, F401


def test_app_runs_with_no_upload():
    outputs, defs = app.app.run()

    assert defs["records"] == []
    assert defs["uploads"] == []
    assert defs["error"] is None
    # mo.stop held back the grid, and with it the download button.
    assert "editor" not in defs


def test_every_grid_column_is_pinned_to_text():
    # Without this the browser infers column types itself and renders a start of
    # "2026-07-26" as a local-timezone JavaScript Date, showing the event a day early
    # west of UTC. If a marimo upgrade moves the hook src/app.py patches, this fails
    # here rather than silently in front of a user.
    editor = mo.ui.data_editor(ics_to_records(SAMPLE_ICS))

    assert editor._component_args["field-types"] == [
        (field, ("string", "str")) for field in FIELDS
    ]


def test_added_column_reaches_the_csv():
    # "Add column to the right" in the grid's header menu sends a column insert. The
    # header comes from the records' own keys, so a column nobody planned for still
    # lands in the file -- with an empty value on every row left untouched.
    editor = mo.ui.data_editor(ics_to_records(SAMPLE_ICS))

    edited = editor._convert_value(
        {
            "edits": [
                {"columnIdx": len(FIELDS), "newName": "notes", "type": "insert"},
                {"rowIdx": 0, "columnId": "notes", "value": "carpool confirmed"},
            ]
        }
    )
    lines = records_to_csv_bytes(edited)[3:].decode().split("\r\n")

    assert lines[0] == ",".join([*FIELDS, "notes"])
    assert lines[1].endswith(",carpool confirmed")
    assert lines[2].endswith(",")


def test_grid_edits_reach_the_saved_rows():
    editor = mo.ui.data_editor(ics_to_records(SAMPLE_ICS))

    edited = editor._convert_value(
        {"edits": [{"rowIdx": 0, "columnId": "summary", "value": "Renamed"}]}
    )

    assert edited[0]["summary"] == "Renamed"
    assert edited[0]["start"] == "2026-07-26"
