import argparse
import sys
from pathlib import Path

from cal2xl.convert import convert


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cal2xl",
        description="Convert an iCalendar (.ics) file to a spreadsheet-friendly CSV. "
        "Opens a GUI by default.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="Calendar file to convert. Pre-loads the GUI unless --no-gui is given.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Where to write the CSV (default: the input path with a .csv suffix).",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Convert on the command line without opening a window.",
    )
    args = parser.parse_args(argv)

    if args.no_gui and args.input is None:
        parser.error("--no-gui requires an input .ics file")
    if args.output is not None and not args.no_gui:
        parser.error("--output only applies with --no-gui; the GUI asks where to save")

    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.no_gui:
        if not args.input.is_file():
            print(f"cal2xl: no such file: {args.input}", file=sys.stderr)
            return 1
        count = convert(args.input, args.output)
        output_path = args.output or args.input.with_suffix(".csv")
        print(f"Wrote {count} events to {output_path}")
        return 0

    # Imported lazily so --no-gui still works where tkinter is unavailable.
    from cal2xl.gui import run

    run(args.input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
