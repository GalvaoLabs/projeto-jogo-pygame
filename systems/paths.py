"""Where bundled resources and per-user data live.

* Development / source checkout: resources sit next to the code.
* PyInstaller bundle: resources are unpacked under ``sys._MEIPASS``.
* Web (Pygbag / Emscripten): resources are packaged next to ``main.py``.
"""
import os
import sys

APP_DIR_NAME = "StartupTycoon"
CONFIG_ENV_VAR = "STARTUP_TYCOON_CONFIG_DIR"   # lets tests and portable installs override the location


def is_web() -> bool:
    return sys.platform == "emscripten"


def base_dir() -> str:
    """Folder that contains ``locales/`` and ``assets/``."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts: str) -> str:
    return os.path.join(base_dir(), *parts)


def user_config_dir() -> str:
    """Per-user, writable folder for settings.json (not created here)."""
    override = os.environ.get(CONFIG_ENV_VAR)
    if override:
        return override
    if is_web():
        return "/data/data/startup_tycoon"      # Pygbag persistent mount (IndexedDB-backed)
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming"), APP_DIR_NAME)
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", APP_DIR_NAME)
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config"), APP_DIR_NAME)
