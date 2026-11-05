"""Headless run of the whole UI: every screen is drawn and a 'monkey' clicks / types at random."""
import os
import random
import tempfile
import unittest

import support
from support import click, key, pygame

import settings as S
from core.company import Company
from game import Game, SAVE_NAME
from systems.localization import L
from systems.storage import FileStorage


def make_game(folder):
    return Game(storage=FileStorage(folder))


def frames(g, n=2):
    for _ in range(n):
        g.tick()


class Smoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        L.set_language("pt_BR")

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_screen_in_every_language(self):
        for code in L.available_languages():
            g = make_game(self.tmp.name)
            g.change_language(code)
            frames(g)                                    # menu
            g.state = "settings"; frames(g)
            g.new_game()
            for tab in range(5):
                g.goto_dashboard_tab(tab); frames(g)
            g.mode = "office"; frames(g, 3)
            for sel in (("desk", 0), ("meeting",), ("cooler",), ("plant", 0), ("board",), ("emp", g.company.employees[0].id)):
                g.office.sel = sel; frames(g)
            g.mode = "dashboard"
            for _ in range(3):
                g.end_month(); frames(g)                 # report modal
                g.close_report()
            g.company.status = "victory"; g.state = "end"; frames(g)
            g.company.status = "bankrupt"; frames(g)
            self.assertEqual(L.errors, [], code)
            self.assertEqual(L.missing_keys, set(), code)
        L.set_language("pt_BR")

    def test_continue_after_restart(self):
        g = make_game(self.tmp.name)
        self.assertFalse(g.can_continue())
        g.new_game()
        g.company.hire("Developer")
        g.end_month(); g.close_report()
        cash, month = g.company.cash, g.company.month
        g.shutdown()
        g2 = make_game(self.tmp.name)
        self.assertTrue(g2.can_continue())
        self.assertEqual((g2.company.cash, g2.company.month), (cash, month))

    def test_corrupt_save_is_ignored(self):
        FileStorage(self.tmp.name).write(SAVE_NAME, '{"version": 1, "cash": ')
        g = make_game(self.tmp.name)
        self.assertFalse(g.can_continue())
        frames(g)

    def test_finished_run_deletes_save(self):
        g = make_game(self.tmp.name)
        g.new_game()
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, SAVE_NAME)))
        g.company.cash = -1
        g.end_month()
        self.assertEqual(g.company.status, "bankrupt")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, SAVE_NAME)))

    def test_menu_buttons_work_with_clicks(self):
        g = make_game(self.tmp.name)
        frames(g)
        click(640, 348); frames(g)                       # "Novo Jogo" (no Continue button yet)
        self.assertEqual(g.state, "play")
        key(pygame.K_ESCAPE); frames(g)
        self.assertEqual(g.state, "menu")
        key(pygame.K_ESCAPE); frames(g)
        self.assertEqual(g.state, "play")

    def test_shortcuts(self):
        g = make_game(self.tmp.name)
        g.new_game(); frames(g)
        key(pygame.K_3); frames(g)
        self.assertEqual((g.mode, g.dashboard.tab), ("dashboard", 2))
        key(pygame.K_o); frames(g)
        self.assertEqual(g.mode, "office")
        key(pygame.K_e); frames(g)
        self.assertIsNotNone(g.report)
        key(pygame.K_SPACE); frames(g)
        self.assertIsNone(g.report)
        sound = g.settings.sound
        key(pygame.K_m); frames(g)
        self.assertNotEqual(sound, g.settings.sound)

    def test_monkey(self):
        rng = random.Random(1234)
        g = make_game(self.tmp.name)
        keys = [pygame.K_TAB, pygame.K_e, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_1,
                pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_o, pygame.K_m]
        g.new_game()
        for step in range(4000):
            r = rng.random()
            if r < 0.85:
                click(rng.randrange(S.WIDTH), rng.randrange(S.HEIGHT))
            else:
                key(rng.choice(keys))
            g.tick()
            g.running = True                              # the monkey may hit "Quit"; keep going
            if g.state == "end" and rng.random() < 0.3:
                g.new_game()
            if g.state == "menu" and rng.random() < 0.05:
                g.state = "play" if g.can_continue() else "menu"
        self.assertEqual(L.missing_keys, set(), "a screen asked for a translation key that does not exist")
        self.assertEqual(L.errors, [], "a translation string failed to format")
        L.set_language("pt_BR")


if __name__ == "__main__":
    unittest.main()
