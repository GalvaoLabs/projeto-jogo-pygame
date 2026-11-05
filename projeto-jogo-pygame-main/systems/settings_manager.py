"""Persistent user settings (language, fullscreen, volume) stored as JSON.

* Missing file  -> created with defaults on first save.
* Corrupt file / wrong types / unknown language -> defaults for the bad fields; never raises.
* Unknown extra keys are preserved so newer versions' settings survive a downgrade.
"""
import json
import os

from systems.paths import user_config_dir

DEFAULTS = {"language": "pt_BR", "fullscreen": False, "volume": 80}
FILE_NAME = "settings.json"


class SettingsManager:
    def __init__(self, path=None, valid_languages=None):
        """``valid_languages``: optional callable returning the codes a user may select."""
        self.path = path or os.path.join(user_config_dir(), FILE_NAME)
        self._valid_languages = valid_languages
        self.data = dict(DEFAULTS)
        self.warnings = []
        self.load()

    # ------------------------------------------------------------ io
    def load(self):
        self.data = dict(DEFAULTS)
        self.warnings = []
        raw = None
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
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
        if not isinstance(d.get("fullscreen"), bool):
            d["fullscreen"] = DEFAULTS["fullscreen"]
        vol = d.get("volume")
        if isinstance(vol, bool) or not isinstance(vol, (int, float)):
            d["volume"] = DEFAULTS["volume"]
        else:
            d["volume"] = int(max(0, min(100, vol)))

    def save(self) -> bool:
        """Atomic write. Returns False (never raises) if the location is not writable."""
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.replace(tmp, self.path)
            return True
        except OSError as exc:
            self.warnings.append(f"could not save settings: {exc}")
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
    def volume(self):
        return self.data["volume"]
