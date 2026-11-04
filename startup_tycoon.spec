# PyInstaller spec - Windows (and Linux/macOS) one-folder build.
# Build:  pip install -r requirements-dev.txt  &&  pyinstaller startup_tycoon.spec --noconfirm
# Output: dist/StartupTycoon/StartupTycoon.exe   (zip the whole folder to distribute)
# STATUS: written but NOT yet run (no PyInstaller in the authoring environment) - see README.
block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    # (source, folder inside the bundle) - systems/paths.py reads them from sys._MEIPASS
    datas=[("locales", "locales"), ("assets", "assets")],
    hiddenimports=[],
    excludes=["tkinter", "PIL", "numpy", "unittest", "tests"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="StartupTycoon",
    console=False,          # no terminal window; crashes are written to crash.log (see main.py)
    icon=None,              # put assets/icon.ico here when you have one
)
coll = COLLECT(exe, a.binaries, a.datas, name="StartupTycoon")
