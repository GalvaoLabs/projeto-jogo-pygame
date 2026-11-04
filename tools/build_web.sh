#!/usr/bin/env bash
# Cross-platform implementation lives in Python so Windows and CI use the same steps.
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python tools/build_web.py
