"""Renders every screen in every language and checks for clipped / overlapping text,
missing translations and state preservation. Run: python -m unittest discover -s tests -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers as H  # noqa: E402

from helpers import S, click, frame  # noqa: E402
from systems.localization import L  # noqa: E402

SHOTS = os.environ.get("ST_SHOTS")      # optional: folder to save screenshots


def shot(g, lang, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        H.pygame.image.save(g.screen, os.path.join(SHOTS, f"{lang}_{name}.png"))


def tour(g, lang):
    """Yield (name) after drawing each distinct screen; caller checks the recorded frame."""
    # menu / settings
    g.state = "menu"; yield "menu"
    g.state = "settings"; yield "settings"
    g.new_game(); c = g.company
    c.cash = 400_000
    for _ in range(2):
        c.hire("Marketing Specialist")
    c.toggle_campaign("social"); c.toggle_campaign("influencer")
    c.invest_dev(0)
    for i, name in enumerate(["overview", "hr", "products", "marketing", "financials"]):
        g.dashboard.tab = i; yield f"dash_{name}"
    # with history (table, chart) and a loss-making month
    for _ in range(3):
        g.end_month(); g.report = None
    c.cash = 20_000
    g.end_month(); yield "report_modal"; g.report = None
    g.dashboard.tab = 4; yield "dash_financials_history"
    g.dashboard.tab = 0; yield "dash_overview_history"
    g.dashboard.tab = 1; g.dashboard.pending_dismiss = (c.employees[0].id, 10 ** 12); yield "hr_confirm"
    g.dashboard.pending_dismiss = None
    c.cash = 500_000; c.expand_office(); c.hire("Manager")
    g.mode = "office"
    frame(g, 30)
    for sel in [("emp", c.employees[0].id), ("desk", 7), ("meeting",), ("cooler",), ("plant", 0), ("board",), None]:
        g.office.sel = sel; yield f"office_{sel[0] if sel else 'none'}"
    g.office.send_all("meeting", 5); frame(g, 40); g.office.sel = ("emp", c.employees[1].id); yield "office_walking"
    g.mode = "dashboard"
    c.cash = 1_200_000; g.end_month(); yield "report_victory"; g.close_report(); yield "end_victory"
    g.new_game(); g.company.cash = 50; g.end_month(); yield "report_bankrupt"; g.close_report(); yield "end_bankrupt"


class TestEveryScreenEveryLanguage(unittest.TestCase):
    def test_layout_and_translation(self):
        problems = []
        for lang in H.LANGS:
            g = H.new_game(lang)
            L.missing_keys.clear(); L.errors.clear()
            for name in tour(g, lang):
                g.ui.toasts.clear()
                with H.Recorder() as r:
                    frame(g, 1)
                problems += r.problems(f"[{lang}/{name}]")
                texts = [s for k, _, s in r.items if k == "text"]
                bad = [s for s in texts if s.startswith("[") and s.endswith("]") and "." in s]
                if bad:
                    problems.append(f"[{lang}/{name}] untranslated placeholders {bad}")
                self.assertGreater(len(texts), 3, f"{lang}/{name} drew almost nothing")
                shot(g, lang, name)
            mk = {k for k in L.missing_keys if k[0] == lang}
            self.assertEqual(mk, set(), f"{lang}: keys looked up but missing")
            self.assertEqual(L.errors, [], f"{lang}: formatting errors")
        self.assertEqual(problems, [], "\n".join(problems[:40]))

    def test_toasts_fit_window_in_every_language(self):
        from systems.localization import Msg
        msgs = [Msg("msg.hired", {"name": "Guilherme", "role": "Marketing Specialist", "salary": 12345678, "fee": 6172839}),
                Msg("msg.confirm_dismiss", {"name": "Guilherme", "sev": 1234567}),
                Msg("msg.campaign_launched", {"camp": "influencer", "cost": 15000})]
        for lang in H.LANGS:
            g = H.new_game(lang)
            for m in msgs:
                g.ui.toasts.clear(); g.ui.toast(m, True)
                with H.Recorder() as r:
                    frame(g, 1)
                # toasts float over the UI on purpose; only require that they stay inside the window
                self.assertEqual([x for x in r.problems(f"[{lang}]") if "outside window" in x], [])


class TestSettingsScreenFlow(unittest.TestCase):
    def test_language_picker_by_real_clicks_midgame_and_persists(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "settings.json")
            g = H.new_game(path=p)
            frame(g, 2)
            click(g, (S.WIDTH // 2, 348)); self.assertEqual(g.state, "play")
            c = g.company; c.cash = 55_555
            g.state = "menu"; frame(g, 2)
            # menu with a running game: Continue, New Game, Settings
            click(g, (S.WIDTH // 2, 320 + 72 * 2 + 28)); self.assertEqual(g.state, "settings")
            panel_y = 120
            for code in H.LANGS[1:] + H.LANGS[:1]:             # click each language row (pt_BR last: it is the start)
                i = H.LANGS.index(code)
                click(g, (S.WIDTH // 2, panel_y + 52 + i * 52 + 22))
                self.assertEqual(L.language, code)
                self.assertEqual(json.load(open(p, encoding="utf-8"))["language"], code)
            click(g, (S.WIDTH // 2, panel_y + 52 + 2 * 52 + 22))  # es_ES
            self.assertEqual(L.language, "es_ES")
            g.on_key(H.pygame.K_ESCAPE); self.assertEqual(g.state, "menu")
            click(g, (S.WIDTH // 2, 348))                         # Continue (first button)
            self.assertEqual(g.state, "play"); self.assertIs(g.company, c); self.assertEqual(c.cash, 55_555)
            frame(g, 1)
            # restart -> still Spanish
            g2 = H.new_game(path=p)
            self.assertEqual(L.language, "es_ES")
            g2.change_language("pt_BR")

    def test_fullscreen_toggle_persists(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "settings.json")
            g = H.new_game(path=p)
            g.toggle_fullscreen()
            self.assertTrue(json.load(open(p))["fullscreen"])
            g.toggle_fullscreen()
            self.assertFalse(json.load(open(p))["fullscreen"])


if __name__ == "__main__":
    unittest.main()
