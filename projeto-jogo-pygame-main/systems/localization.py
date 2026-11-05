"""Internationalization (i18n) and regional formatting (l10n).

Usage::

    from systems.localization import t, money
    t("menu.new_game")                      # -> "Novo Jogo"
    t("msg.hired", name="Ana", role="Developer", salary=5500, fee=2750)
    money(100000)                           # -> "R$ 100.000"

Design rules
------------
* Every language is one JSON file in ``locales/`` (``{"meta": {...}, "strings": {...}}``).
  Adding a language = dropping a new file there; no code changes.
* Translation strings may contain placeholders such as ``{fee:money}``. The *value* stays a
  plain number everywhere in the simulation; only this module turns it into text.
* Lookup order: current language -> FALLBACK_LANGUAGE -> DEFAULT_LANGUAGE -> ``[key]``.
  Missing keys and formatting errors are recorded (``missing_keys`` / ``errors``) instead of
  crashing the game.
* A language is only offered to the player when it contains every key of the reference
  language and none is empty (``is_complete``).
"""
import json
import os
import string
from typing import NamedTuple

from systems.paths import resource_path

DEFAULT_LANGUAGE = "pt_BR"       # shown on first run; also the reference for completeness
FALLBACK_LANGUAGE = "en_US"      # used for keys missing in the selected language
REFERENCE_LANGUAGE = DEFAULT_LANGUAGE
HIDDEN_STATUSES = ("draft", "hidden")   # meta.status values that keep a language out of the picker


class Msg(NamedTuple):
    """A translatable message produced by the simulation: a key plus raw (numeric) params."""
    key: str
    params: dict = {}


def placeholders(template: str) -> set:
    """Names of the ``{fields}`` used in a template."""
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


class _Fmt(string.Formatter):
    """str.format with game-specific format specs (money, n1, pct0, role, ...)."""

    def __init__(self, loc):
        super().__init__()
        self.loc = loc

    def format_field(self, value, spec):
        L = self.loc
        if spec == "money":
            return L.money(value)
        if spec == "compact":
            return L.money_compact(value)
        if spec == "int":
            return L.integer(value)
        if spec == "sint":
            return ("+" if value > 0 else "") + L.integer(value)
        if len(spec) == 2 and spec[0] == "n" and spec[1].isdigit():
            return L.number(value, int(spec[1]))
        if spec.startswith("pct") and spec[3:].isdigit():
            return L.percent(value, int(spec[3:]))
        if spec == "role":
            return L.t("role." + str(value))
        if spec == "campaign":
            return L.t(f"campaign.{value}.name")
        if spec == "monthlabel":
            return L.month_label(int(value))
        return super().format_field(value, spec)


class Localization:
    def __init__(self, locales_dir=None, language=DEFAULT_LANGUAGE):
        self.locales_dir = locales_dir or resource_path("locales")
        self.data = {}               # code -> {"meta": {...}, "strings": {...}}
        self.load_errors = {}        # code -> reason the file was ignored
        self.missing_keys = set()    # (language, key) looked up but absent
        self.errors = []             # formatting problems (never raised)
        self._fmt = _Fmt(self)
        self.language = language
        self.load_all()
        if language not in self.data:
            self.language = DEFAULT_LANGUAGE

    # ------------------------------------------------------------ loading
    def load_all(self):
        self.data.clear()
        self.load_errors.clear()
        try:
            names = sorted(os.listdir(self.locales_dir))
        except OSError as exc:
            self.load_errors["*"] = f"cannot read {self.locales_dir}: {exc}"
            return
        for fname in names:
            if not fname.endswith(".json"):
                continue
            code = fname[:-5]
            try:
                with open(os.path.join(self.locales_dir, fname), encoding="utf-8") as f:
                    raw = json.load(f)
                if not isinstance(raw.get("strings"), dict) or not isinstance(raw.get("meta"), dict):
                    raise ValueError("expected an object with 'meta' and 'strings'")
                self.data[code] = {"meta": raw["meta"], "strings": raw["strings"]}
            except (OSError, ValueError) as exc:     # JSONDecodeError is a ValueError
                self.load_errors[code] = str(exc)

    # ------------------------------------------------------------ languages
    def meta(self, code=None) -> dict:
        return self.data.get(code or self.language, {}).get("meta", {})

    def missing_in(self, code) -> list:
        """Keys of the reference language that ``code`` lacks or leaves empty/non-text."""
        ref = self.data.get(REFERENCE_LANGUAGE, {}).get("strings", {})
        cur = self.data.get(code, {}).get("strings", {})
        return sorted(k for k in ref if not isinstance(cur.get(k), str) or not cur[k].strip())

    def is_complete(self, code) -> bool:
        return code in self.data and REFERENCE_LANGUAGE in self.data and not self.missing_in(code)

    def available_languages(self) -> list:
        """Codes the player may choose (complete, not draft/hidden), ordered by ``meta.order``."""
        codes = [c for c in self.data
                 if self.is_complete(c) and self.data[c]["meta"].get("status") not in HIDDEN_STATUSES]
        return sorted(codes, key=lambda c: (self.data[c]["meta"].get("order", 99), c))

    def set_language(self, code) -> bool:
        if code in self.available_languages():
            self.language = code
            return True
        return False

    # ------------------------------------------------------------ translation
    def _lookup(self, key):
        for code in (self.language, FALLBACK_LANGUAGE, DEFAULT_LANGUAGE):
            s = self.data.get(code, {}).get("strings", {}).get(key)
            if isinstance(s, str) and s:
                return code, s
            self.missing_keys.add((code, key))
        return None, None

    def t(self, key, **params) -> str:
        code, template = self._lookup(key)
        if template is None:
            return f"[{key}]"
        if not params and "{" not in template:
            return template
        try:
            return self._fmt.vformat(template, (), params)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            self.errors.append((self.language, key, repr(exc)))
            return template

    def tu(self, key, **params) -> str:
        return self.t(key, **params).upper()

    def tn(self, key, count, **params) -> str:
        """Plural helper: uses ``key.one`` when count == 1, otherwise ``key.other``."""
        suffix = "one" if count == 1 else "other"
        return self.t(f"{key}.{suffix}", n=count, **params)

    def tr(self, msg) -> str:
        """Translate a Msg (or pass a plain str through)."""
        if isinstance(msg, Msg):
            return self.t(msg.key, **msg.params)
        return str(msg)

    # ------------------------------------------------------------ regional formatting
    def _num(self):
        return self.meta().get("number", {})

    @staticmethod
    def _group(digits: str, group: str, min_group: int) -> str:
        if len(digits) < 3 + min_group:
            return digits
        parts = []
        while len(digits) > 3:
            parts.insert(0, digits[-3:])
            digits = digits[:-3]
        parts.insert(0, digits)
        return group.join(parts)

    def number(self, value, decimals=0) -> str:
        n = self._num()
        dec, grp, mg = n.get("decimal", "."), n.get("group", ","), n.get("min_group", 1)
        neg = round(value, decimals) < 0
        body = f"{abs(value):.{decimals}f}"
        whole, _, frac = body.partition(".")
        out = self._group(whole, grp, mg) + (dec + frac if decimals else "")
        return ("-" if neg else "") + out

    def integer(self, value) -> str:
        return self.number(round(value), 0)

    def percent(self, value, decimals=0) -> str:
        return self.meta().get("percent", "{}%").format(self.number(value, decimals))

    def money(self, value, decimals=0) -> str:
        """Presentation only: the numeric value is never converted (no exchange rate)."""
        cur = self.meta().get("currency", {})
        neg = round(value, decimals) < 0
        return cur.get("pattern", "{sign}{symbol}{amount}").format(
            sign="-" if neg else "", symbol=cur.get("symbol", "$"), amount=self.number(abs(value), decimals))

    def compact_number(self, value) -> str:
        """1_500_000 -> '1,5 milhão' / '1.5 million'. Below one million: plain number."""
        if abs(value) < 1_000_000:
            return self.number(value, 0)
        x = value / 1_000_000
        shown = self.number(x, 0 if abs(x - round(x)) < 0.05 else 1)
        m = self.meta().get("million", {"one": "million", "other": "million", "rule": "same"})
        if m.get("rule") == "lt2":
            word = m["one"] if abs(x) < 2 else m["other"]
        elif m.get("rule") == "eq1":
            word = m["one"] if abs(round(x, 1)) == 1 else m["other"]
        else:
            word = m["one"]
        return f"{shown} {word}"

    def money_compact(self, value) -> str:
        if abs(value) < 1_000_000:
            return self.money(value)
        cur = self.meta().get("currency", {})
        return cur.get("compact_pattern", "{sign}{symbol}{amount}").format(
            sign="-" if value < 0 else "", symbol=cur.get("symbol", "$"),
            amount=self.compact_number(abs(value)))

    def date(self, day, month, year) -> str:
        return self.meta().get("date", "{year}-{month:02d}-{day:02d}").format(day=day, month=month, year=year)

    def month_label(self, month_counter: int, short=True) -> str:
        """Game month counter (1 = first month) -> 'Jan 2026' in the current language."""
        from systems.time_system import month_parts   # local import: time_system imports us lazily too
        year, m = month_parts(month_counter)
        names = self.meta().get("months_short" if short else "months")
        return f"{names[m - 1]} {year}" if names else f"{m:02d}/{year}"

    def month_name(self, month_counter: int) -> str:
        from systems.time_system import month_parts
        _, m = month_parts(month_counter)
        names = self.meta().get("months_short")
        return names[m - 1] if names else str(m)


# ---------------------------------------------------------------- module-level singleton
L = Localization()


def t(key, **params):
    return L.t(key, **params)


def tu(key, **params):
    return L.tu(key, **params)


def tn(key, count, **params):
    return L.tn(key, count, **params)


def tr(msg):
    return L.tr(msg)


def money(value, decimals=0):
    return L.money(value, decimals)


def set_language(code):
    return L.set_language(code)
