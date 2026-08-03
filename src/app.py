# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "icalendar>=7.2.2",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    from marimo._plugins.ui._impl.tables.default_table import DefaultTableManager

    from cal2xl.convert import ics_to_records, records_to_csv_bytes

    # For plain Python data mo.ui.data_editor reports no column types at all, so the
    # browser guesses them -- and reads a start of "2026-07-26" as a JavaScript Date in
    # the viewer's own timezone, displaying the event a day early anywhere west of UTC.
    # Everything icalendar hands us is already text, so pin every column to text.
    # tests/test_app.py fails loudly if a marimo upgrade moves this hook.
    DefaultTableManager.get_field_types = lambda self: [
        (str(name), ("string", "str")) for name in self.get_column_names()
    ]

    return Path, ics_to_records, mo, records_to_csv_bytes


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # cal2xl

    Turn a calendar export into a spreadsheet. Pick an `.ics` file, check the events
    over — every cell is editable — then download the `.csv` and open it in Excel,
    Numbers or Google Sheets.
    """)
    return


@app.cell
def _(mo):
    upload = mo.ui.file(
        filetypes=[".ics"],
        kind="area",
        label="Drop an .ics calendar file here, or click to browse",
    )
    upload
    return (upload,)


@app.cell
def _(ics_to_records, upload):
    # icalendar reads the uploaded bytes itself. Decoding first would break any file
    # exported with a UTF-8 BOM, which is most of them.
    uploaded = upload.value[0] if upload.value else None

    error = None
    records = []
    if uploaded is not None:
        try:
            records = ics_to_records(uploaded.contents)
        except Exception as exc:  # a bad file is a message, not a traceback
            error = str(exc)

    return error, records, uploaded


@app.cell(hide_code=True)
def _(error, mo, records, uploaded):
    if error is not None:
        status = mo.callout(
            mo.md(f"**Could not read `{uploaded.name}`**\n\n```\n{error}\n```"),
            kind="danger",
        )
    elif uploaded is None:
        status = mo.md("*Waiting for a calendar file.*")
    elif not records:
        status = mo.callout(
            mo.md(f"No events found in `{uploaded.name}`."), kind="warn"
        )
    else:
        plural = "" if len(records) == 1 else "s"
        status = mo.md(
            f"**{len(records)} event{plural}** from `{uploaded.name}` — "
            "edit any cell, then download below."
        )
    status
    return


@app.cell
def _(mo, records):
    # Stopping here leaves `editor` undefined, which also holds back the download
    # button until there is something to download.
    mo.stop(not records)

    editor = mo.ui.data_editor(records)
    editor
    return (editor,)


@app.cell
def _(Path, editor, mo, records_to_csv_bytes, uploaded):
    # Lazy so the file is built at click time, from the latest edits.
    mo.download(
        data=lambda: records_to_csv_bytes(editor.value),
        filename=Path(uploaded.name).with_suffix(".csv").name,
        mimetype="text/csv",
        label="Download CSV",
    )
    return


if __name__ == "__main__":
    app.run()
