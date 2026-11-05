"""Build the browser version for itch.io (or any static web host).

    python tools/build_web.py                # -> dist/startup-tycoon-itch.zip  (+ dist/web/ to test)

No Pygbag installation is needed: the game is packed exactly like ``pygbag --archive`` does
(an ``.apk`` zip with everything under ``assets/``) and the Python/WebAssembly runtime is
downloaded by the player's browser from the Pygbag CDN when the game starts.

To test locally:   cd dist/web && python -m http.server 8000     then open http://localhost:8000
(The first load needs internet access: it downloads the runtime from pygame-web.github.io.)
"""
import os
import py_compile
import shutil
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
APK_NAME = "web_src.apk"                  # must match `bundle = "web_src"` in web/index.template.html
ZIP_NAME = "startup-tycoon-itch.zip"

GAME_FILES = ["main.py", "settings.py", "game.py"]
GAME_DIRS = ["core", "modes", "systems", "locales", "assets"]
SKIP_FILES = {"icon.ico", "icon.icns", "favicon.png"}        # desktop-only icons: not needed in the browser
FIXED_DATE = (2026, 1, 1, 0, 0, 0)          # reproducible archives


def game_files():
    """Yield (absolute path, path inside the game folder) for everything the game needs at runtime."""
    for name in GAME_FILES:
        yield os.path.join(ROOT, name), name
    for folder in GAME_DIRS:
        for base, dirs, files in os.walk(os.path.join(ROOT, folder)):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for f in sorted(files):
                if f.endswith((".pyc", ".pyo", ".tmp")) or f in SKIP_FILES:
                    continue
                full = os.path.join(base, f)
                yield full, os.path.relpath(full, ROOT).replace(os.sep, "/")


def check_sources():
    """Fail early on syntax errors: a broken file would only show up as a black screen online."""
    with tempfile.TemporaryDirectory() as tmp:
        for full, rel in game_files():
            if rel.endswith(".py"):
                py_compile.compile(full, cfile=os.path.join(tmp, "x.pyc"), doraise=True)


def write_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arcname, data in entries:
            info = zipfile.ZipInfo(arcname, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)


def read(path):
    with open(path, "rb") as f:
        return f.read()


def main():
    check_sources()
    os.makedirs(DIST, exist_ok=True)

    # 1) web_src.apk  (zip; every file lives under assets/ like in a Pygbag archive)
    apk_entries = [("assets/" + rel, read(full)) for full, rel in game_files()]
    apk_path = os.path.join(DIST, APK_NAME)
    write_zip(apk_path, apk_entries)

    # 2) index.html + favicon
    index = read(os.path.join(ROOT, "web", "index.template.html"))
    index = index.replace(b"\r\n", b"\n")
    favicon = read(os.path.join(ROOT, "assets", "favicon.png"))

    # 3) the zip to upload to itch.io: index.html MUST be at the root of the zip
    zip_path = os.path.join(DIST, ZIP_NAME)
    write_zip(zip_path, [("index.html", index), ("favicon.png", favicon), (APK_NAME, read(apk_path))])

    # 4) loose copy for local testing
    web_dir = os.path.join(DIST, "web")
    shutil.rmtree(web_dir, ignore_errors=True)
    os.makedirs(web_dir)
    for name, data in (("index.html", index), ("favicon.png", favicon), (APK_NAME, read(apk_path))):
        with open(os.path.join(web_dir, name), "wb") as f:
            f.write(data)
    os.remove(apk_path)

    verify(zip_path)
    print(f"OK  {zip_path}  ({os.path.getsize(zip_path) / 1024:.0f} KB)")


def verify(zip_path):
    """The same rules itch.io applies to an HTML5 upload, plus the layout the runtime expects."""
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None, "corrupt zip"
        names = z.namelist()
        assert "index.html" in names, "index.html must be at the root of the zip"
        assert all("\\" not in n and not n.startswith("/") for n in names), "bad entry names"
        assert len(names) < 1000, "itch.io accepts at most 1000 files"
        html = z.read("index.html").decode("utf-8")
        assert "\r" not in html and "cookiecutter.comment" not in html
        assert 'data-python="python3.12"' in html and 'bundle = "web_src"' in html
        with z.open(APK_NAME) as f, zipfile.ZipFile(f) as apk:
            inner = set(apk.namelist())
            for need in ("assets/main.py", "assets/game.py", "assets/locales/pt_BR.json",
                         "assets/assets/fonts/DejaVuSansCondensed.ttf", "assets/assets/icon.png"):
                assert need in inner, f"missing in {APK_NAME}: {need}"
            assert apk.testzip() is None


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, py_compile.PyCompileError, OSError) as exc:
        sys.exit(f"build failed: {exc}")
