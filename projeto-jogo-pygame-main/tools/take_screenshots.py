"""Takes REAL screenshots (needs real pygame) of the main screens in pt_BR, en_US and es_ES.

    python tools/take_screenshots.py          ->  docs/screenshots/<lang>_<screen>.png
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import helpers as H  # noqa: E402

if H.BACKEND != "real":
    sys.exit("Real pygame is not installed (pip install pygame). The Pillow shim is not used for screenshots.")

import test_ui_languages as T  # noqa: E402

OUT = os.path.join(ROOT, "docs", "screenshots")
KEEP = {"menu", "settings", "dash_overview_history", "dash_hr", "dash_products", "dash_marketing",
        "dash_financials_history", "report_modal", "office_emp", "office_meeting", "end_victory"}
os.makedirs(OUT, exist_ok=True)
for lang in ("pt_BR", "en_US", "es_ES"):
    g = H.new_game(lang)
    for name in T.tour(g, lang):
        if name in KEEP or name == "office_walking":
            g.ui.toasts.clear()
            H.frame(g, 2)
            H.pygame.image.save(g.screen, os.path.join(OUT, f"{lang}_{name}.png"))
print("saved to", OUT)
