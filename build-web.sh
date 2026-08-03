#!/usr/bin/env bash
# Export the marimo notebook as a self-contained WASM site.
#
# The output runs entirely in the visitor's browser via Pyodide -- no server-side
# Python, no install, no OS security warning. It does have to be served over HTTP
# though; opening index.html from the file system does not work.
#
# The export builds a wheel from src/cal2xl and injects it into the notebook's PEP 723
# metadata, which is why src/app.py lives beside the package rather than at the repo
# root: marimo resolves local imports against the notebook's own directory.
#
# Usage: ./build-web.sh [output-dir]      (default: ./site)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$REPO/site}"

uv run --group web marimo export html-wasm "$REPO/src/app.py" \
    --output "$OUT" \
    --mode run \
    --no-sandbox \
    --force

echo
echo "Built:   $OUT"
echo "Preview: uv run python -m http.server -d $OUT 8000"
echo "Deploy:  upload the contents of $OUT to any static host"
