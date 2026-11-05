import json
import os
import tempfile
import unittest

import support  # noqa: F401  (sets sys.path / pygame)

import settings as S
from core import economy
from core.company import Company, SAVE_VERSION
from systems.localization import L, placeholders
from systems.settings_manager import SettingsManager
from systems.storage import FileStorage


class Localization(unittest.TestCase):
    def test_all_shipped_languages_are_complete(self):
        self.assertEqual(sorted(L.available_languages()), sorted(L.data), L.load_errors)
        for code in L.data:
            self.assertEqual(L.missing_in(code), [], code)

    def test_placeholders_match_reference_language(self):
        ref = L.data["pt_BR"]["strings"]
        for code, data in L.data.items():
            for key, tpl in data["strings"].items():
                self.assertEqual(placeholders(tpl), placeholders(ref[key]), f"{code}:{key}")

    def test_number_and_money_formatting(self):
        L.set_language("pt_BR")
        self.assertEqual(L.money(100000), "R$\xa0100.000")
        L.set_language("en_US")
        self.assertTrue(L.money(100000).endswith("100,000"))
        L.set_language("pt_BR")


class Economy(unittest.TestCase):
    def test_start_state(self):
        c = Company(seed=1)
        self.assertEqual(c.cash, S.START_CASH)
        self.assertEqual(len(c.employees), S.START_EMPLOYEES)
        p = c.preview()
        self.assertEqual(p.month, 1)

    def test_preview_does_not_mutate(self):
        c = Company(seed=1)
        before = json.dumps(c.to_dict(), sort_keys=True)
        c.preview()
        self.assertEqual(before, json.dumps(c.to_dict(), sort_keys=True))

    def test_failed_hire_does_not_consume_ids_or_cash(self):
        c = Company(seed=2)
        c.cash = 10
        nid, n = c._next_id, len(c.employees)
        ok, _ = c.hire("Developer")
        self.assertFalse(ok)
        self.assertEqual((c._next_id, len(c.employees), c.cash), (nid, n, 10))

    def test_cannot_exceed_office_capacity(self):
        c = Company(seed=2)
        for _ in range(10):
            c.hire("Designer")
        self.assertLessEqual(len(c.employees), c.office_capacity)

    def test_bankruptcy_detected(self):
        c = Company(seed=3)
        c.cash = 0
        c.end_month()
        self.assertEqual(c.status, "bankrupt")


class SaveGame(unittest.TestCase):
    def play(self, months=8):
        c = Company(seed=5)
        c.hire("Marketing Specialist")
        c.toggle_campaign("social")
        c.invest_dev(0)
        for _ in range(months):
            c.end_month()
        return c

    def test_roundtrip(self):
        c = self.play()
        d = json.loads(json.dumps(c.to_dict()))
        c2 = Company.from_dict(d)
        self.assertEqual(json.dumps(c.to_dict(), sort_keys=True), json.dumps(c2.to_dict(), sort_keys=True))
        c.end_month()
        c2.end_month()
        self.assertEqual(c.cash, c2.cash)             # same dice after loading

    def test_bad_saves_are_rejected(self):
        good = self.play(2).to_dict()
        for mutate in (
            lambda d: d.update(version=SAVE_VERSION + 1),
            lambda d: d.pop("cash"),
            lambda d: d.update(cash="lots"),
            lambda d: d.update(employees=[]),
            lambda d: d["employees"][0].update(role="Wizard"),
            lambda d: d.update(product=None),
        ):
            d = json.loads(json.dumps(good))
            mutate(d)
            with self.assertRaises((ValueError, TypeError, KeyError)):
                Company.from_dict(d)
        with self.assertRaises(ValueError):
            Company.from_dict([])

    def test_values_are_clamped(self):
        d = json.loads(json.dumps(self.play(2).to_dict()))
        d["office_level"] = 99
        d["product"]["price"] = 10**9
        c = Company.from_dict(d)
        self.assertEqual(c.office_level, len(S.OFFICE_LEVELS) - 1)
        self.assertEqual(c.product.price, S.PRICE_MAX)


class Settings(unittest.TestCase):
    def test_defaults_corrupt_and_persist(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "settings.json")
            with open(path, "w") as f:
                f.write("{not json")
            sm = SettingsManager(path=path, valid_languages=L.available_languages)
            self.assertEqual(sm.language, "pt_BR")
            self.assertTrue(sm.warnings)
            sm.set("language", "en_US")
            sm.set("volume", 500)
            sm.set("sound", "yes")
            sm2 = SettingsManager(path=path, valid_languages=L.available_languages)
            self.assertEqual((sm2.language, sm2.volume, sm2.sound), ("en_US", 100, True))

    def test_unwritable_location_never_raises(self):
        sm = SettingsManager(path="/proc/nope/settings.json")
        self.assertFalse(sm.save())

    def test_file_storage(self):
        with tempfile.TemporaryDirectory() as d:
            st = FileStorage(os.path.join(d, "a", "b"))
            self.assertIsNone(st.read("x"))
            self.assertTrue(st.write("x", "olá"))
            self.assertEqual(st.read("x"), "olá")
            self.assertTrue(st.delete("x") and st.delete("x"))


if __name__ == "__main__":
    unittest.main()
