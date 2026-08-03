import argparse
import sys
from pathlib import Path

from cal2xl.convert import merge_ics, records_to_csv_bytes

# Several calendars merge into one table, so the result is no longer named after any
# single input.
MERGED_OUTPUT_NAME = "calendars.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cal2xl",
        description="Convert iCalendar (.ics) files to a spreadsheet-friendly CSV. "
        "Several calendars are merged into one table in date order. "
        "Opens a GUI by default.",
    )
    parser.add_argument(
        "input",
        nargs="*",
        type=Path,
        help="Calendar files to convert. Pre-loads the GUI unless --no-gui is given.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Where to write the CSV (default: the input path with a .csv suffix, or "
        f"{MERGED_OUTPUT_NAME} when merging several).",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Convert on the command line without opening a window.",
    )
    args = parser.parse_args(argv)

    if args.no_gui and not args.input:
        parser.error("--no-gui requires at least one input .ics file")
    if args.output is not None and not args.no_gui:
        parser.error("--output only applies with --no-gui; the GUI asks where to save")

    return args


def default_output(inputs: list[Path]) -> Path:
    if len(inputs) == 1:
        return inputs[0].with_suffix(".csv")
    return inputs[0].parent / MERGED_OUTPUT_NAME


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.no_gui:
        missing = [path for path in args.input if not path.is_file()]
        if missing:
            for path in missing:
                print(f"cal2xl: no such file: {path}", file=sys.stderr)
            return 1

        records = merge_ics([(path.name, path) for path in args.input])
        output_path = args.output or default_output(args.input)
        output_path.write_bytes(records_to_csv_bytes(records))
        print(f"Wrote {len(records)} events to {output_path}")
        return 0

    # Imported lazily so --no-gui still works where tkinter is unavailable.
    from cal2xl.gui import run

    run(args.input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
