# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for cal2xl. One spec, three platforms.

Build with:  uv run pyinstaller cal2xl.spec   ->   dist/cal2xl
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# Linux only: the CPython builds uv installs carry no RPATH on _tkinter.so, so the
# dynamic loader -- and therefore PyInstaller's dependency scan -- resolves
# libtcl9.0.so against the *system* Tcl rather than the self-contained one shipped
# beside the interpreter. The two are not interchangeable: distro Tcl delegates bignum
# work to libtommath and exports no TclBN_* symbols, while the bundled Tcl exports them
# itself, so a mixed bundle dies at startup with
#   ImportError: ... undefined symbol: TclBN_mp_to_ubin
# PyInstaller already collects the Tcl/Tk *script* library from the interpreter, so pin
# the shared objects to the same source. This also covers build machines with no system
# Tcl installed at all, where the scan would otherwise find nothing to bundle.
SYSTEM_TCL_LIBS = {"libtcl9.0.so", "libtcl9tk9.0.so", "libtommath.so.1"}


def interpreter_tcl_libs():
    if not sys.platform.startswith("linux"):
        return []
    libdir = Path(sys.base_prefix) / "lib"
    # a.binaries entries are (dest_name, src_path, typecode) triples.
    return [(lib.name, str(lib), "BINARY") for lib in sorted(libdir.glob("libtcl9*.so*"))]

# tzdata ships no importable code, only zoneinfo data files, so the module scanner
# cannot see it. icalendar needs it for timezone lookups on Windows, which has no
# system tz database of its own.
tzdata_datas, tzdata_binaries, tzdata_hiddenimports = collect_all("tzdata")

a = Analysis(
    ["src/cal2xl/__main__.py"],
    pathex=["src"],
    binaries=tzdata_binaries,
    datas=tzdata_datas,
    hiddenimports=tzdata_hiddenimports,
    excludes=[
        "numpy",
        "pandas",
        "PIL",
        "matplotlib",
        "IPython",
        "pytest",
        "setuptools",
        "pip",
    ],
    noarchive=False,
    optimize=0,
)

tcl_libs = interpreter_tcl_libs()
if tcl_libs:
    a.binaries = [b for b in a.binaries if os.path.basename(b[0]) not in SYSTEM_TCL_LIBS]
    a.binaries.extend(tcl_libs)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="cal2xl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX-packed binaries trip antivirus heuristics far more often
    runtime_tmpdir=None,
    console=False,  # no terminal window on Windows; a .app bundle on macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="cal2xl.app",
        icon=None,
        bundle_identifier="io.github.cal2xl",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
        },
    )
