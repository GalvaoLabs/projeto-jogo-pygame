"""Build a standalone desktop app (Windows / macOS / Linux) with PyInstaller.

    pip install -r requirements-dev.txt
    python tools/build_desktop.py

PyInstaller cannot cross-compile: run this on each target OS (the GitHub Actions workflow in
.github/workflows/build.yml does exactly that). Output goes to dist/:

    Windows -> StartupTycoon-windows-<arch>.zip      (StartupTycoon/StartupTycoon.exe)
    macOS   -> StartupTycoon-macos-<arch>.zip        (StartupTycoon.app)
    Linux   -> StartupTycoon-linux-<arch>.tar.gz     (StartupTycoon/StartupTycoon)
"""
import os
import platform
import shutil
import subprocess
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")
NAME = "StartupTycoon"
BUNDLE_ID = "com.startuptycoon.game"


def arch():
    m = platform.machine().lower()
    return {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(m, m)


def main():
    system = platform.system()
    sep = os.pathsep                       # PyInstaller's --add-data separator: ';' on Windows, ':' elsewhere
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
           "--name", NAME, "--distpath", os.path.join(BUILD, "pyi"), "--workpath", os.path.join(BUILD, "work"),
           "--specpath", BUILD,
           "--add-data", f"{os.path.join(ROOT, 'locales')}{sep}locales",
           "--add-data", f"{os.path.join(ROOT, 'assets')}{sep}assets",
           "--paths", ROOT,
           "--exclude-module", "tkinter", "--exclude-module", "numpy.testing"]
    if system == "Windows":
        cmd += ["--icon", os.path.join(ROOT, "assets", "icon.ico")]
    elif system == "Darwin":
        cmd += ["--icon", os.path.join(ROOT, "assets", "icon.icns"), "--osx-bundle-identifier", BUNDLE_ID]
    cmd.append(os.path.join(ROOT, "main.py"))
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    out = os.path.join(BUILD, "pyi")
    os.makedirs(DIST, exist_ok=True)
    tag = {"Windows": "windows", "Darwin": "macos"}.get(system, "linux") + "-" + arch()
    if system == "Darwin":
        target = os.path.join(DIST, f"{NAME}-{tag}.zip")
        if os.path.exists(target):
            os.remove(target)
        # ditto keeps the symlinks / permissions inside the .app (a plain zip would break them)
        subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(out, f"{NAME}.app"), target], check=True)
    elif system == "Windows":
        target = shutil.make_archive(os.path.join(DIST, f"{NAME}-{tag}"), "zip", out, NAME)
    else:
        target = os.path.join(DIST, f"{NAME}-{tag}.tar.gz")
        with tarfile.open(target, "w:gz") as tar:
            tar.add(os.path.join(out, NAME), arcname=NAME)
    print("OK ", target)


if __name__ == "__main__":
    main()
