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

with app.setup(hide_code=True):
    from pathlib import Path

    import marimo as mo
    from marimo._plugins.ui._impl.tables.default_table import DefaultTableManager

    from cal2xl.convert import merge_ics, records_to_csv_bytes

    # For plain Python data mo.ui.data_editor reports no column types at all, so the
    # browser guesses them -- and reads a start of "2026-07-26" as a JavaScript Date in
    # the viewer's own timezone, displaying the event a day early anywhere west of UTC.
    # Everything icalendar hands us is already text, so pin every column to text.
    # tests/test_app.py fails loudly if a marimo upgrade moves this hook.
    DefaultTableManager.get_field_types = lambda self: [
        (str(name), ("string", "str")) for name in self.get_column_names()
    ]


@app.cell(hide_code=True)
def _():
    mo.md("""
    # Calender (.ics) to Spreadsheet Converter

    Turn calendar exports into a spreadsheet. Pick one `.ics` file or several — several
    are merged into a single table, in date order — check the events over, edit anything
    you like, then download the `.csv` and open it in Excel, Numbers or Google Sheets.
    """)
    return


@app.cell
def _():
    upload = mo.ui.file(
        filetypes=[".ics"],
        multiple=True,
        kind="area",
        label="Drop .ics calendar files here, or click to browse",
    )
    upload
    return (upload,)


@app.cell
def _(upload):
    # icalendar reads the uploaded bytes itself. Decoding first would break any file
    # exported with a UTF-8 BOM, which is most of them.
    uploads = list(upload.value) if upload.value else []

    error = None
    records = []
    if uploads:
        try:
            records = merge_ics([(item.name, item.contents) for item in uploads])
        except Exception as exc:  # a bad file is a message, not a traceback
            error = str(exc)
    return error, records, uploads


@app.cell(hide_code=True)
def _(error, records, uploads):
    if len(uploads) == 1:
        source = f"`{uploads[0].name}`"
    else:
        source = f"{len(uploads)} calendars"

    if error is not None:
        status = mo.callout(
            mo.md(f"**Could not read a calendar**\n\n```\n{error}\n```"),
            kind="danger",
        )
    elif not uploads:
        status = mo.md("*Waiting for calendar files.*")
    elif not records:
        status = mo.callout(mo.md(f"No events found in {source}."), kind="warn")
    else:
        plural = "" if len(records) == 1 else "s"
        status = mo.md(
            f"**{len(records)} event{plural}** from {source} — "
            "edit any cell, then download below."
        )
    status
    return


@app.cell
def _(records):
    # Stopping here leaves `editor` undefined, which also holds back the download
    # button until there is something to download.
    mo.stop(not records)

    editor = mo.ui.data_editor(records)
    editor
    return (editor,)


@app.cell
def _(editor, uploads):
    # One calendar keeps its own name; a merge of several gets a neutral one.
    if len(uploads) == 1:
        download_name = Path(uploads[0].name).with_suffix(".csv").name
    else:
        download_name = "calendars.csv"

    # Lazy so the file is built at click time, from the latest edits.
    mo.download(
        data=lambda: records_to_csv_bytes(editor.value),
        filename=download_name,
        mimetype="text/csv",
        label="Download CSV",
    )
    return


if __name__ == "__main__":
    app.run()
