"""Shared test helpers: headless Game with an isolated settings file."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
os.environ["STARTUP_TYCOON_CONFIG_DIR"] = tempfile.mkdtemp(prefix="st_test_")

from use_pygame import ensure_pygame  # noqa: E402

BACKEND = ensure_pygame()

import pygame  # noqa: E402
import settings as S  # noqa: E402
from game import Game  # noqa: E402
from modes import ui as uikit  # noqa: E402
from systems.localization import L  # noqa: E402

LANGS = ["pt_BR", "en_US", "es_ES", "fr_FR", "de_DE"]


def new_game(lang=None, path=None):
    path = path or os.path.join(tempfile.mkdtemp(prefix="st_cfg_"), "settings.json")
    g = Game(settings_path=path)
    g.ui.begin = lambda clicked: None
    if lang:
        g.change_language(lang)
    g.ui.toasts.clear()
    return g


def frame(g, n=1, pos=(0, 0), click=False):
    for i in range(n):
        g.ui.mouse = pos
        g.ui.clicked = click and i == 0
        g.frame(1 / 60)


def click(g, pos):
    frame(g, 1, pos, True)
    frame(g, 1, (0, 0), False)


class Recorder:
    """Collects every text/button rect drawn in one frame."""
    def __enter__(self):
        self.items = []
        uikit.LAYOUT_HOOK = self._hook
        return self

    def _hook(self, kind, rect, label):
        if kind == "layer":            # a full-screen overlay was drawn: earlier items are covered
            self.items.clear()
        else:
            self.items.append((kind, pygame.Rect(rect), label))

    def __exit__(self, *a):
        uikit.LAYOUT_HOOK = None

    def problems(self, tag=""):
        out = []
        texts = [(r, s) for k, r, s in self.items if k == "text"]
        for r, s in texts:
            if r.x < 0 or r.y < 0 or r.right > S.WIDTH or r.bottom > S.HEIGHT:
                out.append(f"{tag} outside window: {s!r} {r}")
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                (a, sa), (b, sb) = texts[i], texts[j]
                ix = min(a.right, b.right) - max(a.x, b.x)
                iy = min(a.bottom, b.bottom) - max(a.y, b.y)
                if ix > 2 and iy > 4:
                    out.append(f"{tag} overlap: {sa!r} x {sb!r}")
        return out
