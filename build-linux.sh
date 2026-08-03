#!/usr/bin/env bash
# Build a widely-distributable Linux binary.
#
# A PyInstaller build bundles the host's system libraries, so it inherits that host's
# glibc floor -- building on Fedora 44 produces a binary that only runs on glibc 2.43+.
# Building inside Ubuntu 22.04 drops the floor to glibc 2.35, which covers Ubuntu 22.04+,
# Debian 12+, Fedora 36+, and RHEL 9+.
#
# Usage: ./build-linux.sh [output-dir]      (default: ./dist-linux)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$(realpath "${1:-$REPO/dist-linux}")"
IMAGE="docker.io/library/ubuntu:22.04"
ENGINE="$(command -v podman || command -v docker)"

mkdir -p "$OUT"

"$ENGINE" run --rm \
    --security-opt label=disable \
    -v "$REPO":/src:ro \
    -v "$OUT":/out \
    -w /src \
    -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
    -e UV_CACHE_DIR=/tmp/uvcache \
    "$IMAGE" bash -euo pipefail -c '
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        # binutils: PyInstaller shells out to objdump to trace library dependencies.
        # The X libraries: Tk links against them, and PyInstaller can only bundle
        # what it can resolve on the build machine.
        apt-get install -y -qq --no-install-recommends \
            curl ca-certificates binutils \
            libx11-6 libxft2 libxrender1 libxext6 libfontconfig1

        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="/root/.local/bin:$PATH"

        uv sync --frozen --group build
        uv run pyinstaller cal2xl.spec --noconfirm \
            --distpath /out --workpath /tmp/build
    '

tar -C "$OUT" -czf "$OUT/cal2xl-linux.tar.gz" cal2xl
echo
echo "Built: $OUT/cal2xl"
echo "Ship:  $OUT/cal2xl-linux.tar.gz"
