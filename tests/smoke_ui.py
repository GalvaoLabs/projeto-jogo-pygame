"""Headless smoke test: drives the real Game object with fake clicks.

    python tests/smoke_ui.py [screenshot_dir]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import settings as S  # noqa: E402
from game import Game  # noqa: E402

shots = sys.argv[1] if len(sys.argv) > 1 else None
g = Game()
g.ui.begin = lambda clicked: None   # we drive mouse state by hand


def frame(n=1, pos=None, click=False):
    for i in range(n):
        if pos is not None:
            g.ui.mouse = pos
        g.ui.clicked = click and i == 0
        g.frame(1 / 60)


def click(pos):
    frame(1, pos, True)
    frame(1, (0, 0), False)


def shot(name):
    if shots:
        os.makedirs(shots, exist_ok=True)
        pygame.image.save(g.screen, os.path.join(shots, name + ".png"))


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        global failures
        failures += 1


failures = 0

# ---- menu -> new game
frame(3)
shot("01_menu")
click((S.WIDTH // 2, 348))                       # New Game (first button)
check(g.state == "play" and g.company is not None, "New Game starts a company")
c = g.company
check(c.cash == 100_000 and len(c.employees) == 2 and c.customers == 10 and c.reputation == 10
      and c.office_capacity == 4, "initial conditions correct")

# ---- dashboard tabs via real clicks
for i, name in enumerate(["overview", "hr", "products", "marketing", "financials"]):
    click((100, S.NAV_H + 20 + i * 52 + 20))
    check(g.dashboard.tab == i, f"sidebar tab {i} opens")
    frame(2)
    shot(f"02_dash_{name}")

# ---- HR: hire through the real button (Developer button), dismiss through button
click((100, S.NAV_H + 20 + 1 * 52 + 20))
frame(2)
before = len(c.employees)
click((230 + 616 + 100, 104 + 62 + 20))           # first hire button (Developer)
check(len(c.employees) == before + 1, "Hire button adds an employee")
check(c.cash < 100_000, "hiring fee is charged")
click((230 + 616 + 100, 104 + 62 + 65 * 1 + 20))  # Designer
click((230 + 616 + 100, 104 + 62 + 65 * 2 + 20))  # Marketing -> office now full (4)
check(len(c.employees) == 4, "four employees hired")
click((230 + 616 + 100, 104 + 62 + 65 * 3 + 20))  # Manager -> must fail (office full)
check(len(c.employees) == 4, "office capacity is respected")
frame(2)
shot("03_hr_full")

# ---- marketing + products via direct calls (logic) then render
check(c.toggle_campaign("social")[0], "campaign can be launched")
check(c.marketing_investment == 2000, "marketing investment tracked")
cash_before = c.cash
c.cash = 10_000
check(not c.toggle_campaign("media")[0], "campaign beyond available funds is refused")
c.cash = cash_before
c.set_price(150)
check(c.product.price == 150, "price change works")
ok, _ = c.invest_dev(0)
check(ok and c.product.progress >= 8, "development investment adds progress")

# ---- office mode via nav button
click((230, 28))                                  # OFFICE nav button
check(g.mode == "office", "OFFICE button switches mode")
frame(120)
shot("04_office_L1")
check(len(g.office.sprites) == len(c.employees), "office shows one sprite per employee")
check(c.cash < 100_000 and len(c.employees) == 4, "state preserved after switching modes")

# ---- expand office (insufficient funds then enough funds)
c.cash = 5_000
ok, _ = c.expand_office()
check(not ok and c.office_level == 0, "expansion refused without funds")
c.cash = 200_000
click((1000 + 14 + 100, S.NAV_H + 12 + 40 + 48 + 20))   # expand button in the panel
check(c.office_level == 1 and c.office_capacity == 8, "Expand button works")
frame(60)
shot("05_office_L2")
g.office.sel = ("emp", c.employees[0].id)
frame(2)
shot("06_office_selected")
ok, _ = c.hire("Developer")
frame(30)
check(len(g.office.sprites) == len(c.employees), "hire in dashboard logic shows up in office")
victim = c.employees[2].id
c.dismiss(victim)
frame(5)
check(victim not in g.office.sprites, "dismissal removes the character")

# ---- team meeting animation
for sp in g.office.sprites.values():
    sp.break_timer = 1e9          # no random breaks during this check
g.office.send_all("meeting", 3)
frame(180)
shot("07_office_meeting")
check(any(sp.state != "sit" for sp in g.office.sprites.values()), "team meeting moves employees away from desks")
frame(2400)
check(all(sp.state == "sit" for sp in g.office.sprites.values()), "employees return to their desks")

# ---- max office
c.cash = 1_000_000
c.expand_office(); c.expand_office()
check(c.office_level == 3 and not c.expand_office()[0], "office tops out at max level")
for _ in range(11):
    c.hire("Developer")
frame(60)
shot("08_office_L4_full")

# ---- end month via real button
g.mode = "dashboard"
frame(2)
click((1118 + 75, 28))
check(g.report is not None and c.month == 2, "END MONTH shows a report and advances")
frame(2)
shot("09_report")
click((S.WIDTH // 2, S.HEIGHT // 2 + 300 - 78 + 25))
check(g.report is None, "report closes")
check(c.last_report is not None and c.last_report.cash_end == int(c.cash), "report matches company cash")

# ---- bankruptcy
g.new_game()
c = g.company
c.cash = 100
g.end_month()
check(c.status == "bankrupt", "bankruptcy triggers when cash < 0")
g.close_report()
check(g.state == "end", "bankruptcy screen shown")
frame(2)
shot("10_bankrupt")
click((S.WIDTH // 2 - 130, 580 + 27))              # Play Again
check(g.state == "play" and g.company is not c and g.company.cash == 100_000, "restart creates a new company")

# ---- victory
c = g.company
c.cash = 1_050_000
g.end_month()
g.close_report()
check(c.status == "victory" and g.state == "end", "victory triggers at R$ 1.000.000 net worth")
frame(2)
shot("11_victory")

print("\nFAILURES:", failures)
sys.exit(1 if failures else 0)
