"""Internationalization tests. Run: python -m unittest discover -s tests -v"""
import ast
import json
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers as H  # noqa: E402  (must come first: isolates config dir, picks pygame backend)

from systems import localization as loc  # noqa: E402
from systems.localization import Localization, Msg, placeholders  # noqa: E402
from systems.settings_manager import SettingsManager, DEFAULTS  # noqa: E402

LOCALES = os.path.join(H.ROOT, "locales")


def load(code):
    with open(os.path.join(LOCALES, code + ".json"), encoding="utf-8") as f:
        return json.load(f)


class TestFiles(unittest.TestCase):
    def test_1_all_json_load(self):                       # spec 1
        for code in H.LANGS:
            d = load(code)
            self.assertIn("strings", d); self.assertIn("meta", d)
        L = Localization()
        self.assertEqual(L.load_errors, {})
        for code in H.LANGS:
            self.assertIn(code, L.data)

    def test_2_required_keys_present_everywhere(self):    # spec 2
        ref = set(load("pt_BR")["strings"])
        for code in H.LANGS:
            self.assertEqual(ref - set(load(code)["strings"]), set(), code)
            self.assertEqual(set(load(code)["strings"]) - ref, set(), f"extra keys in {code}")

    def test_2b_placeholders_match(self):
        ref = load("pt_BR")["strings"]
        for code in H.LANGS:
            for k, v in load(code)["strings"].items():
                self.assertEqual(placeholders(v), placeholders(ref[k]), f"{code}:{k}")

    def test_3_no_empty_translations(self):               # spec 3
        for code in H.LANGS:
            for k, v in load(code)["strings"].items():
                self.assertTrue(isinstance(v, str) and v.strip(), f"{code}:{k}")

    def test_meta_complete(self):
        for code in H.LANGS:
            m = load(code)["meta"]
            self.assertEqual(len(m["months"]), 12); self.assertEqual(len(m["months_short"]), 12)
            for k in ("name", "flag", "number", "currency", "percent", "date", "million"):
                self.assertIn(k, m, f"{code}:{k}")

    def test_all_languages_offered(self):
        self.assertEqual(Localization().available_languages(), H.LANGS)

    def test_draft_language_is_hidden_and_incomplete_is_not_offered(self):
        with tempfile.TemporaryDirectory() as d:
            for code in ("pt_BR", "en_US"):
                with open(os.path.join(d, code + ".json"), "w", encoding="utf-8") as f:
                    json.dump(load(code), f, ensure_ascii=False)
            draft = load("en_US"); draft["meta"]["status"] = "draft"
            partial = load("en_US"); partial["strings"].pop("menu.quit")
            for name, obj in (("xx_XX", draft), ("yy_YY", partial)):
                with open(os.path.join(d, name + ".json"), "w", encoding="utf-8") as f:
                    json.dump(obj, f)
            with open(os.path.join(d, "zz_ZZ.json"), "w") as f:
                f.write("{not json")
            L = Localization(locales_dir=d)
            self.assertEqual(L.available_languages(), ["pt_BR", "en_US"])
            self.assertIn("zz_ZZ", L.load_errors)           # corrupt file ignored, no crash
            self.assertIn("menu.quit", L.missing_in("yy_YY"))


class TestCodeUsesKeys(unittest.TestCase):
    """Static guard: keys used in code exist; no hard-coded UI strings in the interface modules."""

    FILES = ["game.py", "modes/dashboard.py", "modes/office.py", "modes/ui.py", "core/company.py"]

    def _calls(self):
        for rel in self.FILES:
            tree = ast.parse(open(os.path.join(H.ROOT, rel), encoding="utf-8").read())
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    yield rel, n

    def test_translation_keys_used_in_code_exist(self):
        keys = set(load("pt_BR")["strings"])
        names = {"t", "tu", "tn", "Msg"}
        for rel, n in self._calls():
            f = n.func
            fname = f.id if isinstance(f, ast.Name) else None
            if fname in names and n.args:
                a = n.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    k = a.value
                    ok = k in keys or (fname == "tn" and f"{k}.one" in keys)
                    self.assertTrue(ok, f"{rel}:{n.lineno} unknown key {k!r}")

    def test_no_hardcoded_visible_text(self):
        allowed = {"STARTUP TYCOON", "-10", "-1", "+1", "+10", "->", ""}
        sinks = {"text", "button", "card", "toast", "draw_tooltip"}
        bad = []
        for rel, n in self._calls():
            f = n.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if name not in sinks:
                continue
            for a in n.args:
                for c in ast.walk(a):
                    if isinstance(c, ast.Call):          # string inside t()/L.x() call is fine
                        break
                else:
                    pass
                lits = [c for c in ast.walk(a) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
                # skip subtrees that are calls (t("key") etc.)
                if any(isinstance(c, ast.Call) for c in ast.walk(a)):
                    continue
                for c in lits:
                    v = c.value
                    if v in allowed or v in ("topleft", "center", "topright", "midtop", "midleft", "midright"):
                        continue
                    if any(ch.isalpha() for ch in v) and len(v) > 3 and "kind" not in v:
                        bad.append(f"{rel}:{n.lineno} {v!r}")
        # kind="primary" style kwargs are keywords, not args; only positional literals are checked
        self.assertEqual(bad, [], "hard-coded text found")

    def test_every_locale_key_is_used_somewhere(self):
        src = ""
        for rel in self.FILES + ["core/economy.py"]:
            src += open(os.path.join(H.ROOT, rel), encoding="utf-8").read()
        dynamic = ("role.", "role_short.", "role_desc.", "campaign.", "state.", "msg.meeting.", "hr.free_desks.",
                   "market.months.")
        unused = []
        for k in load("pt_BR")["strings"]:
            if f'"{k}"' in src or any(k.startswith(p) for p in dynamic):
                continue
            unused.append(k)
        self.assertEqual(unused, [], "locale keys never referenced by the code")


class TestSettings(unittest.TestCase):
    def test_4_default_language_is_pt_BR(self):           # spec 4
        self.assertEqual(loc.DEFAULT_LANGUAGE, "pt_BR")
        with tempfile.TemporaryDirectory() as d:
            sm = SettingsManager(path=os.path.join(d, "settings.json"))
            self.assertEqual(sm.language, "pt_BR")
            self.assertEqual(sm.data, DEFAULTS)
            self.assertEqual(Localization().language, "pt_BR")

    def test_file_created_corrupt_and_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "settings.json")
            sm = SettingsManager(path=p, valid_languages=lambda: H.LANGS)
            self.assertTrue(sm.save()); self.assertTrue(os.path.exists(p))
            open(p, "w").write("{{{ corrupt")
            sm = SettingsManager(path=p, valid_languages=lambda: H.LANGS)
            self.assertEqual(sm.language, "pt_BR"); self.assertTrue(sm.warnings)
            json.dump({"language": "klingon", "fullscreen": "yes", "volume": 999}, open(p, "w"))
            sm = SettingsManager(path=p, valid_languages=lambda: H.LANGS)
            self.assertEqual((sm.language, sm.fullscreen, sm.volume), ("pt_BR", False, 100))
            json.dump([1, 2], open(p, "w"))
            self.assertEqual(SettingsManager(path=p).language, "pt_BR")

    def test_unwritable_location_does_not_crash(self):
        sm = SettingsManager(path="/proc/definitely/not/writable/settings.json")
        self.assertFalse(sm.save())

    def test_6_persistence_across_restart(self):          # spec 6
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "settings.json")
            g = H.new_game(path=p)
            self.assertEqual(loc.L.language, "pt_BR")
            self.assertTrue(g.change_language("es_ES"))
            self.assertEqual(json.load(open(p, encoding="utf-8"))["language"], "es_ES")
            g2 = H.new_game(path=p)                         # "restart": brand-new Game reads the file
            self.assertEqual(loc.L.language, "es_ES")
            self.assertEqual(loc.t("menu.new_game"), "Nueva partida")
            g2.change_language("pt_BR")


class TestTranslationEngine(unittest.TestCase):
    def test_7_fallback_for_missing_keys(self):           # spec 7
        with tempfile.TemporaryDirectory() as d:
            pt = load("pt_BR"); en = load("en_US")
            es = load("en_US"); es["meta"]["name"] = "Partial"
            for code, data in (("pt_BR", pt), ("en_US", en), ("zz_ZZ", es)):
                with open(os.path.join(d, code + ".json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            L = Localization(locales_dir=d)
            L.language = "zz_ZZ"
            L.data["zz_ZZ"]["strings"].pop("menu.quit")
            self.assertEqual(L.t("menu.quit"), en["strings"]["menu.quit"])   # falls back to en_US
            self.assertIn(("zz_ZZ", "menu.quit"), L.missing_keys)             # and is reported
            self.assertEqual(L.t("does.not.exist"), "[does.not.exist]")      # visible, never crashes
            self.assertEqual(L.t("msg.hired"), L.data["en_US"]["strings"]["msg.hired"])  # missing params: no crash
            self.assertTrue(L.errors)

    def test_5_runtime_switch_keeps_game_and_updates_texts(self):   # spec 5
        g = H.new_game("pt_BR")
        H.click(g, (H.S.WIDTH // 2, 348))                  # New Game
        c = g.company; c.cash = 77_777
        seen = {}
        for lang in H.LANGS:
            g.change_language(lang)
            with H.Recorder() as r:
                H.frame(g, 2); g.ui.toasts.clear(); H.frame(g, 1)
            seen[lang] = {s for k, _, s in r.items}
            self.assertIs(g.company, c); self.assertEqual(c.cash, 77_777)   # same match, same numbers
            self.assertIn(loc.tu("nav.end_month"), seen[lang])
        self.assertEqual(len({frozenset(v) for v in seen.values()}), 5)    # screens really differ
        g.change_language("pt_BR")

    def test_ui_modules_do_not_hold_translated_text(self):
        g = H.new_game("pt_BR")
        g.ui.toast(Msg("msg.watered"), True)
        self.assertEqual(loc.tr(g.ui.toasts[0][0]), "Você regou a planta.")
        g.change_language("en_US")
        self.assertEqual(loc.tr(g.ui.toasts[0][0]), "You watered the plant.")   # re-translated live
        g.change_language("pt_BR")


class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.L = Localization()

    def at(self, code):
        self.L.language = code
        return self.L

    def test_8_money(self):                                # spec 8
        n = " "
        self.assertEqual(self.at("pt_BR").money(100000, 2), f"R${n}100.000,00")
        self.assertEqual(self.at("pt_BR").money(100000), f"R${n}100.000")
        self.assertEqual(self.at("pt_BR").money(-5500), f"-R${n}5.500")
        self.assertEqual(self.at("en_US").money(100000, 2), "$100,000.00")
        self.assertEqual(self.at("en_US").money(-5500), "-$5,500")
        self.assertEqual(self.at("es_ES").money(100000, 2), f"100.000,00{n}€")

    def test_9_numbers_dates_compact(self):                # spec 9
        self.assertEqual(self.at("pt_BR").number(1234567.891, 2), "1.234.567,89")
        self.assertEqual(self.at("en_US").number(1234567.891, 2), "1,234,567.89")
        self.assertEqual(self.at("pt_BR").date(3, 11, 2026), "03/11/2026")
        self.assertEqual(self.at("en_US").date(3, 11, 2026), "11/03/2026")
        self.assertEqual(self.at("de_DE").date(3, 11, 2026), "03.11.2026")
        self.assertEqual(self.at("pt_BR").compact_number(1_500_000), "1,5 milhão")      # spec example
        self.assertEqual(self.at("pt_BR").compact_number(2_500_000), "2,5 milhões")
        self.assertEqual(self.at("pt_BR").compact_number(1_000_000), "1 milhão")
        self.assertEqual(self.at("en_US").compact_number(1_500_000), "1.5 million")
        self.assertEqual(self.at("pt_BR").percent(12.34, 1), "12,3%")
        self.assertEqual(self.at("pt_BR").month_label(1), "Jan 2026")
        self.assertEqual(self.at("pt_BR").month_label(11), "Nov 2026")
        self.assertEqual(self.at("es_ES").month_label(13), self.L.meta()["months_short"][0] + " 2027")

    def test_formatting_never_changes_the_value(self):
        from core.company import Company
        c = Company(seed=1)
        before = (c.cash, c.net_worth)
        for code in H.LANGS:
            self.at(code).money(c.cash)
            self.assertIsInstance(c.cash, int)
        self.assertEqual((c.cash, c.net_worth), before)

    def test_economy_identical_in_every_language(self):
        from core.company import Company
        results = []
        for code in H.LANGS:
            loc.L.language = code
            c = Company(seed=1)
            for m in range(24):
                c.set_price(150); c.end_month()
            results.append((c.cash, c.customers, round(c.reputation, 6), c.status))
        loc.L.language = "pt_BR"
        self.assertEqual(len(set(results)), 1)


def _cmap(path):
    """Set of code points a TrueType font really has glyphs for (parses the 'cmap' table)."""
    b = open(path, "rb").read()
    n = struct.unpack(">H", b[4:6])[0]
    off = next(struct.unpack(">I", b[12 + 16 * i + 8:12 + 16 * i + 12])[0]
               for i in range(n) if b[12 + 16 * i:16 + 16 * i] == b"cmap")
    cps = set()
    for i in range(struct.unpack(">H", b[off + 2:off + 4])[0]):
        sub = off + struct.unpack(">I", b[off + 4 + 8 * i + 4:off + 4 + 8 * i + 8])[0]
        fmt = struct.unpack(">H", b[sub:sub + 2])[0]
        if fmt == 4:
            sc = struct.unpack(">H", b[sub + 6:sub + 8])[0] // 2
            ends = struct.unpack(f">{sc}H", b[sub + 14:sub + 14 + 2 * sc])
            starts = struct.unpack(f">{sc}H", b[sub + 16 + 2 * sc:sub + 16 + 4 * sc])
            for s, e in zip(starts, ends):
                if s != 0xFFFF:
                    cps.update(range(s, e + 1))
        elif fmt == 12:
            for g in range(struct.unpack(">I", b[sub + 12:sub + 16])[0]):
                s, e, _ = struct.unpack(">III", b[sub + 16 + 12 * g:sub + 28 + 12 * g])
                cps.update(range(s, e + 1))
    return cps


class TestSpecialCharacters(unittest.TestCase):
    def test_10_fonts_cover_every_character_of_every_language(self):   # spec 10 / 9
        for fname in ("DejaVuSansCondensed.ttf", "DejaVuSansCondensed-Bold.ttf"):
            have = _cmap(os.path.join(H.ROOT, "assets", "fonts", fname))
            for code in H.LANGS:
                d = load(code)
                text = "".join(d["strings"].values()) + json.dumps(d["meta"], ensure_ascii=False)
                text += "".join(d["meta"]["months"] + d["meta"]["months_short"])
                missing = {ch for ch in text if ord(ch) > 31 and ord(ch) not in have}
                self.assertEqual(missing, set(), f"{fname} lacks glyphs used by {code}")

    def test_10b_accents_survive_json_and_settings_roundtrip(self):
        self.assertEqual(load("pt_BR")["strings"]["menu.settings"], "Configurações")
        self.assertIn("ñ", "".join(load("es_ES")["strings"].values()))
        self.assertIn("ß", "".join(load("de_DE")["strings"].values()))
        self.assertIn("ç", "".join(load("fr_FR")["strings"].values()))
        with tempfile.TemporaryDirectory() as d:
            sm = SettingsManager(path=os.path.join(d, "s.json"))
            sm.set("note", "Patrimônio líquido – ção ñ ß €")
            raw = open(sm.path, encoding="utf-8").read()
            self.assertIn("Patrimônio", raw)                  # stored as UTF-8, not \\u escapes
            self.assertEqual(SettingsManager(path=sm.path).get("note"), "Patrimônio líquido – ção ñ ß €")


class TestDistributionPaths(unittest.TestCase):
    def test_frozen_layout_resolves_resources(self):
        """Simulates PyInstaller: resources under sys._MEIPASS, program started from another folder."""
        import shutil, subprocess
        with tempfile.TemporaryDirectory() as d:
            bundle = os.path.join(d, "bundle")
            os.makedirs(bundle)
            shutil.copytree(LOCALES, os.path.join(bundle, "locales"))
            shutil.copytree(os.path.join(H.ROOT, "assets"), os.path.join(bundle, "assets"))
            code = ("import sys; sys._MEIPASS=%r; sys.path.insert(0,%r); "
                    "from systems.localization import L; from modes import ui; "
                    "import os; print(sorted(L.available_languages())==sorted(%r), "
                    "os.path.exists(ui.resource_path('assets','fonts','DejaVuSansCondensed.ttf')))") % (bundle, H.ROOT, H.LANGS)
            env = dict(os.environ, SDL_VIDEODRIVER="dummy",
                       PYTHONPATH=os.path.join(H.ROOT, "tests", "support", "pygame_shim"))
            out = subprocess.run([sys.executable, "-c", code], cwd=d, env=env, capture_output=True, text=True)
            self.assertEqual(out.stdout.strip(), "True True", out.stderr)


if __name__ == "__main__":
    unittest.main()
