"""Persistent user settings (language, fullscreen, sound, volume) stored as JSON.

* Missing file  -> created with defaults on first save.
* Corrupt file / wrong types / unknown language -> defaults for the bad fields; never raises.
* Unknown extra keys are preserved so newer versions' settings survive a downgrade.
"""
import json
import os

from systems.storage import FileStorage, default_storage

DEFAULTS = {"language": "pt_BR", "fullscreen": False, "sound": True, "volume": 80}
FILE_NAME = "settings.json"


class SettingsManager:
    def __init__(self, path=None, valid_languages=None, storage=None):
        """``path``: explicit settings file (tests, portable installs). Without it the platform's
        default storage is used. ``valid_languages``: callable returning the selectable codes."""
        if storage is not None:
            self.store, self.name = storage, FILE_NAME
        elif path:
            self.store, self.name = FileStorage(os.path.dirname(path) or "."), os.path.basename(path)
        else:
            self.store, self.name = default_storage(), FILE_NAME
        self._valid_languages = valid_languages
        self.data = dict(DEFAULTS)
        self.warnings = []
        self.load()

    # ------------------------------------------------------------ io
    def load(self):
        self.data = dict(DEFAULTS)
        self.warnings = []
        raw = None
        text = self.store.read(self.name)
        if text is not None:
            try:
                raw = json.loads(text)
            except ValueError as exc:
                self.warnings.append(f"settings unreadable ({exc}); using defaults")
        if raw is not None and not isinstance(raw, dict):
            self.warnings.append("settings file is not a JSON object; using defaults")
            raw = None
        for k, v in (raw or {}).items():
            self.data[k] = v
        self._sanitize()
        return self.data

    def _sanitize(self):
        d = self.data
        lang = d.get("language")
        valid = self._valid_languages() if self._valid_languages else None
        if not isinstance(lang, str) or (valid is not None and lang not in valid):
            if lang != DEFAULTS["language"]:
                self.warnings.append(f"invalid language {lang!r}; using {DEFAULTS['language']}")
            d["language"] = DEFAULTS["language"]
        for key in ("fullscreen", "sound"):
            if not isinstance(d.get(key), bool):
                d[key] = DEFAULTS[key]
        vol = d.get("volume")
        if isinstance(vol, bool) or not isinstance(vol, (int, float)):
            d["volume"] = DEFAULTS["volume"]
        else:
            d["volume"] = int(max(0, min(100, vol)))

    def save(self) -> bool:
        """Never raises. Returns False if the location is not writable."""
        text = json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"
        if self.store.write(self.name, text):
            return True
        self.warnings.append("could not save settings")
        return False

    # ------------------------------------------------------------ access
    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value, save=True):
        self.data[key] = value
        self._sanitize()
        if save:
            self.save()

    @property
    def language(self):
        return self.data["language"]

    @property
    def fullscreen(self):
        return self.data["fullscreen"]

    @property
    def sound(self):
        return self.data["sound"]

    @property
    def volume(self):
        return self.data["volume"]
