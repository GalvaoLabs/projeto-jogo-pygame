"""Tiny text key/value storage used for settings and the saved game.

* Desktop / Android: one file per key inside the user's data folder (atomic writes).
* Web: the browser's ``localStorage`` (survives reloads, unlike the Pygbag virtual filesystem),
  falling back to files if the browser blocks it (private mode, third-party iframe rules...).

Every method swallows I/O errors and reports them through the return value / ``None``:
losing a save must never crash the game.
"""
import os

from systems import paths


class FileStorage:
    def __init__(self, folder):
        self.folder = folder

    def _path(self, name):
        return os.path.join(self.folder, name)

    def read(self, name):
        try:
            with open(self._path(name), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError):
            return None

    def write(self, name, data) -> bool:
        try:
            os.makedirs(self.folder or ".", exist_ok=True)
            tmp = self._path(name) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(data)
            os.replace(tmp, self._path(name))
            return True
        except OSError:
            return False

    def delete(self, name) -> bool:
        try:
            os.remove(self._path(name))
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False


class WebStorage:
    """``window.localStorage`` through Pygbag's ``platform`` bridge."""

    PREFIX = "startup_tycoon:"

    def __init__(self):
        import platform                       # Pygbag's platform module exposes ``window``
        self._ls = platform.window.localStorage
        probe = self.PREFIX + "__probe__"
        self._ls.setItem(probe, "1")          # raises if storage is blocked
        self._ls.removeItem(probe)

    def read(self, name):
        try:
            value = self._ls.getItem(self.PREFIX + name)
        except Exception:
            return None
        if value is None:
            return None
        value = str(value)
        return None if value in ("null", "undefined") else value

    def write(self, name, data) -> bool:
        try:
            self._ls.setItem(self.PREFIX + name, data)
            return True
        except Exception:
            return False

    def delete(self, name) -> bool:
        try:
            self._ls.removeItem(self.PREFIX + name)
            return True
        except Exception:
            return False


def default_storage():
    if paths.is_web() and not os.environ.get(paths.CONFIG_ENV_VAR):
        try:
            return WebStorage()
        except Exception:
            pass
    return FileStorage(paths.user_config_dir())
