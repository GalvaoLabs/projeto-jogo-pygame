"""Build the Pygbag web version and a ZIP ready to upload to itch.io."""
from __future__ import annotations

import shutil
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SOURCE = BUILD / "web_src"
WEB = BUILD / "web"
ITCH_ZIP = BUILD / "startup-tycoon-itch.zip"


def _remove_readonly(function, path, _error) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def main() -> None:
    for path in (SOURCE, WEB, ITCH_ZIP):
        if path.is_dir():
            shutil.rmtree(path, onerror=_remove_readonly)
        elif path.exists():
            path.unlink()
    SOURCE.mkdir(parents=True)

    for name in ("main.py", "game.py", "settings.py"):
        shutil.copy2(ROOT / name, SOURCE / name)
    for name in ("core", "modes", "systems", "locales", "assets"):
        shutil.copytree(ROOT / name, SOURCE / name, ignore=shutil.ignore_patterns("__pycache__"))

    subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", str(ROOT / "requirements.txt"), "pygbag>=0.9.3",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pygbag", "--build", str(SOURCE)],
        cwd=ROOT,
        check=True,
    )

    generated = SOURCE / "build" / "web"
    index = generated / "index.html"
    apk = generated / "web_src.apk"
    if not index.is_file() or not apk.is_file():
        raise FileNotFoundError("Pygbag did not produce index.html and web_src.apk")

    # Pygbag 0.9.3's template inserts an extra slash, causing BrowserFS to 404.
    html = index.read_text(encoding="utf-8")
    # BrowserFS was removed from Pygbag's CDN and this silent game does not need it.
    html = html.replace(
        '    <script src="https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js"></script>',
        "",
    )
    html = html.replace(
        "<title>web_src</title>",
        "<title>Startup Tycoon — Build an Empire</title>",
    )
    index.write_text(html, encoding="utf-8")

    (generated / ".nojekyll").touch()
    shutil.move(str(generated), str(WEB))

    # itch.io expects index.html at the archive root; Pygbag reads the APK on itch.zone.
    with zipfile.ZipFile(ITCH_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("index.html", "favicon.png", "web_src.apk"):
            archive.write(WEB / name, arcname=name)

    print(f"Web build: {WEB}")
    print(f"itch.io upload: {ITCH_ZIP}")


if __name__ == "__main__":
    main()

