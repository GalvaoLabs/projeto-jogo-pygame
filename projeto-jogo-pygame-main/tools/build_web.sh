#!/usr/bin/env bash
# Packages ONLY the runtime files (no tests / shim / docs) and builds the Pygbag web bundle.
# Usage (project root):  bash tools/build_web.sh        -> build/web/  (+ build/web.zip)
# STATUS: not yet run in a real browser - see docs/WEB.md before publishing.
set -euo pipefail
OUT=build/web_src
rm -rf "$OUT" build/web && mkdir -p "$OUT"
cp main.py game.py settings.py "$OUT"/
cp -r core modes systems locales assets "$OUT"/
find "$OUT" -name __pycache__ -prune -exec rm -rf {} +
pip install pygbag
python -m pygbag --build "$OUT"           # writes $OUT/build/web
mkdir -p build && rm -rf build/web && mv "$OUT/build/web" build/web
(cd build/web && zip -qr ../web.zip .)
echo "Test locally with:  python -m pygbag $OUT   then open http://localhost:8000"
