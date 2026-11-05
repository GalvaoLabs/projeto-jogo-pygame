"""Where bundled resources and per-user data live, and which platform we are running on.

* Development / source checkout: resources sit next to the code.
* PyInstaller bundle (Windows / macOS / Linux): resources are unpacked under ``sys._MEIPASS``.
* Android (python-for-android / buildozer): resources are next to the code, user data goes to
  the app's private folder (``ANDROID_PRIVATE``).
* Web (Pygbag / Emscripten): resources are packaged next to ``main.py``; user data goes to the
  browser's ``localStorage`` (see ``systems.storage``) with a virtual-filesystem fallback.
"""
import os
import sys

APP_DIR_NAME = "StartupTycoon"
CONFIG_ENV_VAR = "STARTUP_TYCOON_CONFIG_DIR"   # lets tests and portable installs override the location


def is_web() -> bool:
    return sys.platform == "emscripten"


def is_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ


def is_mobile() -> bool:
    """Touch-first platforms (the phone browser is detected later by the page itself)."""
    return is_android()


def platform_name() -> str:
    if is_web():
        return "web"
    if is_android():
        return "android"
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def base_dir() -> str:
    """Folder that contains ``locales/`` and ``assets/``."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts: str) -> str:
    return os.path.join(base_dir(), *parts)


def user_config_dir() -> str:
    """Per-user, writable folder for settings and saves (not created here)."""
    override = os.environ.get(CONFIG_ENV_VAR)
    if override:
        return override
    if is_web():
        return "/data/data/startup_tycoon"      # Pygbag virtual filesystem (fallback only)
    if is_android():
        return os.environ.get("ANDROID_PRIVATE") or os.path.join(os.path.expanduser("~"), ".startup_tycoon")
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming"), APP_DIR_NAME)
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", APP_DIR_NAME)
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config"), APP_DIR_NAME)
