from collections.abc import Sequence
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tksheet import Sheet

from cal2xl.convert import FIELDS, csv_bytes, merge_ics

ICS_FILETYPES = [("Calendar files", "*.ics"), ("All files", "*.*")]
CSV_FILETYPES = [("CSV files", "*.csv"), ("All files", "*.*")]

# Cap how wide a single column may grow when fitting to content, so the long
# description column cannot push everything else off screen.
MAX_COLUMN_WIDTH = 400


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=8)
        self.pack(fill="both", expand=True)

        self.input_paths: list[Path] = []
        # Merging several calendars adds a source column, so the header is not fixed.
        self.headers = list(FIELDS)

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Button(top, text="Open .ics…", command=self.open_ics).pack(side="left")
        self.path_label = ttk.Label(top, text="No file loaded", foreground="grey")
        self.path_label.pack(side="left", padx=8)

        self.sheet = Sheet(self, headers=list(FIELDS), data=[])
        self.sheet.enable_bindings()
        self.sheet.pack(fill="both", expand=True)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(8, 0))
        self.status_label = ttk.Label(bottom, text="Open an .ics file to begin.")
        self.status_label.pack(side="left")
        self.save_button = ttk.Button(
            bottom, text="Save CSV…", command=self.save_csv, state="disabled"
        )
        self.save_button.pack(side="right")

    def load(self, paths: Path | Sequence[Path]) -> None:
        """Parse paths and populate the grid. Reports failures in a dialog.

        Several calendars are merged into one table in date order, tagged with the file
        each event came from.
        """
        paths = [paths] if isinstance(paths, Path) else list(paths)
        if not paths:
            return

        try:
            records = merge_ics([(path.name, path) for path in paths])
        except Exception as exc:
            messagebox.showerror("Could not read calendar", str(exc))
            return

        headers = list(records[0]) if records else list(FIELDS)
        rows = [[record.get(field, "") for field in headers] for record in records]

        self.input_paths = paths
        self.headers = headers
        self.sheet.headers(headers)
        self.sheet.set_sheet_data(rows)
        self.sheet.set_all_cell_sizes_to_text(width=MAX_COLUMN_WIDTH)
        self.path_label.config(text=self.describe_input(), foreground="")
        self.save_button.config(state="normal")

        if rows:
            self.set_status(f"{len(rows)} events loaded — edit cells, then save.")
        else:
            self.set_status("No events found.")

    def describe_input(self) -> str:
        if len(self.input_paths) == 1:
            return str(self.input_paths[0])
        return f"{len(self.input_paths)} calendars merged"

    def open_ics(self) -> None:
        initial_dir = str(self.input_paths[0].parent) if self.input_paths else "."
        filenames = filedialog.askopenfilenames(
            title="Open calendar files",
            filetypes=ICS_FILETYPES,
            initialdir=initial_dir,
        )
        if filenames:
            self.load([Path(name) for name in filenames])

    def save_csv(self) -> None:
        assert self.input_paths  # the button is disabled until a file loads
        if len(self.input_paths) == 1:
            default = self.input_paths[0].with_suffix(".csv")
        else:
            default = self.input_paths[0].parent / "calendars.csv"
        filename = filedialog.asksaveasfilename(
            title="Save CSV as",
            filetypes=CSV_FILETYPES,
            defaultextension=".csv",
            initialfile=default.name,
            initialdir=str(default.parent),
        )
        if not filename:
            return

        output_path = Path(filename)
        rows = [[str(cell) for cell in row] for row in self.sheet.get_sheet_data()]
        try:
            output_path.write_bytes(csv_bytes(self.headers, rows))
        except Exception as exc:
            messagebox.showerror("Could not save CSV", f"{output_path.name}\n\n{exc}")
            return

        self.set_status(f"✓ Wrote {len(rows)} events to {output_path.name}")

    def set_status(self, text: str) -> None:
        self.status_label.config(text=text)


def run(input_paths: Sequence[Path] | None = None) -> None:
    """Open the main window, optionally pre-loaded with input_paths."""
    root = tk.Tk()
    root.title("cal2xl")
    root.geometry("1000x600")
    root.minsize(600, 300)

    app = App(root)
    if input_paths:
        app.load(input_paths)

    root.mainloop()
