# cal2xl

Convert an iCalendar `.ics` export into a spreadsheet-friendly `.csv`.

Open a calendar file, review and edit the events in a built-in spreadsheet, then save
the CSV wherever you want. Columns are `start`, `end`, `location`, `summary`,
`description`.

It comes in two shapes over one conversion library:

| | Front end | Best for |
| --- | --- | --- |
| **Web app** | a marimo notebook, exported to WebAssembly | handing to other people — a link, nothing to install |
| **Desktop app** | tkinter + tksheet, bundled with PyInstaller | working offline, or on files you would rather not upload |

The web app runs entirely in the visitor's browser: the calendar file never leaves
their machine, and there is no server to keep running.

## Install

Download the build for your platform from the
[latest release](../../releases/latest). No Python installation required.

| Platform | Asset | First run |
| --- | --- | --- |
| Windows | `cal2xl-windows.exe` | Double-click. See the SmartScreen note below. |
| macOS (Apple Silicon) | `cal2xl-mac-apple-silicon.zip` | Unzip, then **right-click → Open**. |
| macOS (Intel) | `cal2xl-mac-intel.zip` | Unzip, then **right-click → Open**. |
| Linux | `cal2xl-linux.tar.gz` | Extract, then right-click → **Run as a Program**. |

The builds are unsigned, so each OS warns on first launch:

- **Windows** shows *"Windows protected your PC"*. Click **More info → Run anyway**.
  PyInstaller executables also draw the occasional antivirus false positive; only a
  code-signing certificate removes that for good.
- **macOS** refuses a plain double-click because the app is not notarized. Right-click
  the app and choose **Open**, then **Open** again — once per machine. Alternatively:
  `xattr -dr com.apple.quarantine cal2xl.app`. Removing the prompt entirely requires an
  Apple Developer ID ($99/yr) and notarization.
- **Linux** needs the executable bit, which the `tar.gz` preserves. The released binary
  is built on Ubuntu 22.04 and needs glibc 2.17+ plus the usual X11 client libraries
  (`libX11`, `libXft`, `libfontconfig`), which every desktop install already has.

## Usage

Launch it with no arguments for the GUI:

1. **Open .ics…** and pick a calendar file.
2. The events appear in an editable grid — click any cell to change it, right-click for
   row insert/delete, `Ctrl+Z` to undo.
3. **Save CSV…** writes what is currently in the grid.

The same executable also converts on the command line:

```
cal2xl                                    # GUI, empty
cal2xl calendar.ics                       # GUI, pre-loaded with that file
cal2xl calendar.ics --no-gui              # writes calendar.csv next to the input
cal2xl calendar.ics -o out.csv --no-gui   # writes to a chosen path
```

The CSV is UTF-8 with a BOM and CRLF line endings, so Excel opens it with accents and
smart quotes intact.

## The web app

`src/app.py` is a [marimo](https://marimo.io) notebook: upload an `.ics`, edit the
events in a grid, download the `.csv`. Same three steps as the desktop app, same
`convert.py` underneath.

The grid does more than edit cells. **New row** / **Delete row** sit under it, and
hovering a column header reveals a `▾` menu with **Rename column**, **Add column to the
left/right**, and **Delete column**. Whatever the grid ends up holding is what gets
written — the CSV header is taken from the columns as they stand, not from the five
`icalendar` fields, so a column you added for your own notes comes out in the file.

```bash
uv sync --group web
uv run --group web marimo edit src/app.py   # develop, with the code visible
uv run --group web marimo run src/app.py    # app mode, code hidden
./build-web.sh                              # -> site/, a static WASM bundle
uv run python -m http.server -d site 8000   # preview at localhost:8000
```

### Deploying it

[`.github/workflows/deploy-web.yml`](.github/workflows/deploy-web.yml) runs the tests,
exports the bundle and publishes it to GitHub Pages on every push to `main`/`master`.
It needs one manual step first, once per repository:

**Settings → Pages → Build and deployment → Source → GitHub Actions.**

Without that the workflow fails at the deploy step. After the first successful run the
app is at `https://<user>.github.io/<repo>/`. All of the bundle's asset paths are
relative, so serving from a repository subpath needs no extra configuration.

`site/` is also portable by hand: drop it on Cloudflare, Netlify, or any static host and
the link is all anyone needs. Two things to know about it:

- **It has to be served over HTTP.** Opening `site/index.html` from the file system
  does not work; Pyodide fetches its own assets.
- **First load pulls down ~25 MB** of Python runtime and caches it. Later visits are
  fast.

The notebook lives at `src/app.py` rather than the repo root on purpose. To build the
bundle, marimo resolves the notebook's local imports with `ruff analyze graph` rooted at
the notebook's *own directory*, then packages what it finds into a wheel it injects into
the file's PEP 723 metadata. From `src/`, `from cal2xl.convert import …` resolves and
`site/public/wheels/cal2xl-*.whl` is produced; from the repo root it would not, and the
export would quietly ship a notebook that cannot import its own conversion code.

One display quirk worth knowing: a column with no value shows as `null` in the grid. The
downloaded CSV has a properly empty field — it is only how marimo's editor draws a blank.

## Development

```bash
uv sync --group build --group dev --group web
uv run pytest                  # tests (the marimo ones skip without --group web)
uv run cal2xl                  # run the desktop GUI from source
uv run pyinstaller cal2xl.spec # build dist/cal2xl for this machine
```

`marimo` and `anywidget` sit in the `web` dependency group rather than in
`dependencies`, so the desktop install and the PyInstaller build environment stay small.

### Building a Linux binary for other people

`uv run pyinstaller` bundles the build machine's system libraries, so a binary built on
a current distro inherits that distro's glibc floor — on Fedora 44 the result needs
glibc 2.43 and runs almost nowhere else. Build inside an old-glibc container instead:

```bash
./build-linux.sh                # -> dist-linux/cal2xl-linux.tar.gz
```

That runs the build in Ubuntu 22.04 via podman (or docker), giving a binary that needs
only glibc 2.17. Use the plain `pyinstaller` command for local testing, and this script
for anything you hand to someone else.

PyInstaller cannot cross-compile, so the Windows and macOS executables must be built on
their own machines; [`.github/workflows/build.yml`](.github/workflows/build.yml) does all
four on GitHub runners. Pushing a `v*` tag attaches them to a GitHub release.
