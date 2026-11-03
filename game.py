"""Game loop, screens (menu / play / report / end) and navigation."""
import math
import sys

import pygame

import settings as S
from core.company import Company, money
from modes.dashboard import Dashboard
from modes.office import OfficeMode
from modes.ui import UI, text, wrap, font


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.state = "menu"        # menu | play | end
        self.mode = "dashboard"    # dashboard | office
        self.company = None
        self.dashboard = None
        self.office = None
        self.report = None         # month report shown in a modal
        self.t = 0.0
        self.running = True

    # ------------------------------------------------------------ lifecycle
    def new_game(self):
        self.company = Company()
        self.dashboard = Dashboard(self.company, self.ui)
        self.office = OfficeMode(self.company, self.ui, self.goto_dashboard_tab)
        self.mode = "dashboard"
        self.report = None
        self.state = "play"
        self.ui.toasts.clear()

    def goto_dashboard_tab(self, tab):
        self.mode = "dashboard"
        self.dashboard.tab = tab

    def end_month(self):
        r = self.company.end_month()
        if r:
            self.report = r

    def close_report(self):
        self.report = None
        if self.company.status != "running":
            self.state = "end"

    def can_continue(self):
        return self.company is not None and self.company.status == "running"

    # ------------------------------------------------------------ main loop
    def run(self):
        while self.running:
            dt = min(self.clock.tick(S.FPS) / 1000.0, 0.1)
            self.t += dt
            clicked = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    clicked = True
                elif ev.type == pygame.KEYDOWN:
                    self.on_key(ev.key)
            self.ui.begin(clicked)
            self.frame(dt)
            pygame.display.flip()
        pygame.quit()

    def on_key(self, key):
        if self.state == "play":
            if self.report is not None:
                if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.close_report()
            elif key == pygame.K_TAB:
                self.mode = "office" if self.mode == "dashboard" else "dashboard"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
        elif self.state == "menu" and key == pygame.K_ESCAPE and self.can_continue():
            self.state = "play"

    def frame(self, dt):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "play":
            self.draw_play(dt)
        elif self.state == "end":
            self.draw_end()
        self.ui.draw_toasts(self.screen, dt)

    # ------------------------------------------------------------ menu
    def draw_menu(self):
        s, ui = self.screen, self.ui
        s.fill(S.BG)
        for i in range(24):  # floating pixel squares
            x = (i * 137 + self.t * (10 + i % 5 * 4)) % (S.WIDTH + 40) - 20
            y = (i * 71) % S.HEIGHT
            col = S.BLUE if i % 3 == 0 else (S.PURPLE if i % 3 == 1 else (40, 60, 100))
            pygame.draw.rect(s, tuple(v // 3 for v in col), (x, y + math.sin(self.t + i) * 8, 14, 14))
        text(s, "STARTUP TYCOON", (S.WIDTH // 2, 150), 76, S.TEXT, bold=True, anchor="center")
        text(s, "BUILD AN EMPIRE", (S.WIDTH // 2, 218), 34, S.BLUE, bold=True, anchor="center")
        bw, bh, y = 320, 56, 320
        if self.can_continue():
            if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), "Continue", kind="primary", size=22):
                self.state = "play"
            y += 72
        if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), "New Game", kind="success", size=22):
            self.new_game()
        y += 72
        if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), "Quit", kind="danger", size=22):
            self.running = False
        text(s, f"Goal: reach {money(S.GOAL_NET_WORTH)} in net worth. Do not go bankrupt.",
             (S.WIDTH // 2, 620), 16, S.MUTED, anchor="center")
        text(s, "TAB switches Dashboard / Office   |   ESC opens this menu", (S.WIDTH // 2, 648), 14, S.MUTED,
             anchor="center")

    # ------------------------------------------------------------ play
    def draw_play(self, dt):
        s, ui, c = self.screen, self.ui, self.company
        s.fill(S.BG)
        ui.locked = self.report is not None
        if self.mode == "dashboard":
            self.dashboard.draw(s)
        else:
            self.office.update(dt)
            self.office.draw(s)
        self.draw_nav()
        if self.report is not None:
            ui.locked = False
            self.draw_report()

    def draw_nav(self):
        s, ui, c = self.screen, self.ui, self.company
        pygame.draw.rect(s, S.NAV, (0, 0, S.WIDTH, S.NAV_H))
        pygame.draw.line(s, S.BORDER, (0, S.NAV_H - 1), (S.WIDTH, S.NAV_H - 1))
        if ui.button(s, (12, 8, 150, 40), "DASHBOARD", kind="primary" if self.mode == "dashboard" else "ghost",
                     size=15, active=self.mode == "dashboard"):
            self.mode = "dashboard"
        if ui.button(s, (170, 8, 130, 40), "OFFICE", kind="primary" if self.mode == "office" else "ghost",
                     size=15, active=self.mode == "office"):
            self.mode = "office"
        text(s, f"Month {c.month}  |  {c.time.label}", (330, 8), 15, S.TEXT, bold=True)
        text(s, f"Cash {money(c.cash)}", (330, 30), 14, S.GREEN if c.cash >= 0 else S.RED, bold=True)
        text(s, f"Net worth {money(c.net_worth)} / {money(S.GOAL_NET_WORTH)}", (560, 19), 15, S.TEXT)
        if ui.button(s, (1040, 8, 70, 40), "MENU", kind="ghost", size=14):
            self.state = "menu"
        if ui.button(s, (1118, 8, 150, 40), "END MONTH", kind="success", size=16):
            self.end_month()

    # ------------------------------------------------------------ report modal
    def draw_report(self):
        s, ui, r = self.screen, self.ui, self.report
        dim = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        s.blit(dim, (0, 0))
        box = pygame.Rect(0, 0, 700, 600)
        box.center = (S.WIDTH // 2, S.HEIGHT // 2)
        pygame.draw.rect(s, S.CARD, box, border_radius=16)
        pygame.draw.rect(s, S.BORDER, box, 2, border_radius=16)
        text(s, f"Monthly Report - {r.label}", (box.x + 28, box.y + 22), 26, S.TEXT, bold=True)

        def row(y, label, val, col=S.TEXT, bold=False, x=box.x + 28, w=300):
            text(s, label, (x, y), 16, S.MUTED)
            text(s, val, (x + w, y), 16, col, bold=bold, anchor="topright")

        y = box.y + 72
        text(s, "FINANCES", (box.x + 28, y), 13, S.BLUE, bold=True)
        row(y + 26, "Product revenue", money(r.revenue), S.GREEN)
        row(y + 52, "Salaries", "-" + money(r.salaries))
        row(y + 78, "Marketing", "-" + money(r.marketing))
        row(y + 104, "Office maintenance", "-" + money(r.office))
        row(y + 130, "Other operating costs", "-" + money(r.other))
        row(y + 156, "One-time costs", "-" + money(r.one_time))
        pygame.draw.line(s, S.BORDER, (box.x + 28, y + 186), (box.x + 328, y + 186))
        row(y + 196, "Profit / loss", ("+" if r.profit > 0 else "") + money(r.profit),
            S.GREEN if r.profit >= 0 else S.RED, True)
        row(y + 230, "Cash balance", money(r.cash_end), S.GREEN if r.cash_end >= 0 else S.RED, True)
        row(y + 256, "Net worth", money(r.net_worth), S.PURPLE, True)
        if r.capex:
            row(y + 282, "Office expansion (capex)", "-" + money(r.capex))

        x2 = box.x + 372
        text(s, "BUSINESS", (x2, y), 13, S.BLUE, bold=True)
        row(y + 26, "Customers at start", str(r.customers_start), x=x2, w=300)
        row(y + 52, "New: organic", f"+{r.organic}", S.GREEN, x=x2, w=300)
        row(y + 78, "New: referrals", f"+{r.referral}", S.GREEN, x=x2, w=300)
        row(y + 104, "New: marketing", f"+{r.from_marketing}", S.GREEN, x=x2, w=300)
        row(y + 130, "Churned", f"-{r.churned}", S.RED, x=x2, w=300)
        row(y + 156, "Customers now", str(r.customers_end), S.TEXT, True, x=x2, w=300)
        row(y + 196, "Reputation", f"{r.rep_start:.1f} -> {r.rep_end:.1f}", x=x2, w=300)
        row(y + 222, "Product quality", f"{r.quality_start:.1f} -> {r.quality_end:.1f}", x=x2, w=300)
        row(y + 248, "Development", f"+{r.progress_gain:.0f}% (now {r.progress_end:.0f}%)", x=x2, w=300)
        if r.releases:
            text(s, f"Version {r.version_end} released!", (x2, y + 282), 16, S.YELLOW, bold=True)

        status = self.company.status
        if status == "bankrupt":
            text(s, "The company ran out of cash.", (box.x + 28, box.bottom - 120), 18, S.RED, bold=True)
        elif status == "victory":
            text(s, "You reached the goal!", (box.x + 28, box.bottom - 120), 18, S.GREEN, bold=True)
        label = "Continue" if status == "running" else "See result"
        if ui.button(s, (box.centerx - 110, box.bottom - 78, 220, 50), label, kind="success", size=18):
            self.close_report()

    # ------------------------------------------------------------ end screens
    def draw_end(self):
        s, ui, c = self.screen, self.ui, self.company
        s.fill(S.BG)
        won = c.status == "victory"
        col = S.GREEN if won else S.RED
        pygame.draw.rect(s, tuple(v // 6 for v in col), (0, 0, S.WIDTH, 260))
        text(s, "VICTORY!" if won else "BANKRUPT", (S.WIDTH // 2, 100), 84, col, bold=True, anchor="center")
        sub = ("Your startup is worth a million. You built an empire!" if won
               else "Your startup ran out of money and had to close its doors.")
        text(s, sub, (S.WIDTH // 2, 190), 22, S.TEXT, anchor="center")
        box = pygame.Rect(0, 0, 520, 250)
        box.center = (S.WIDTH // 2, 410)
        ui.card(s, box, "FINAL RESULTS")
        rows = [("Months played", str(c.month - 1)), ("Final cash", money(c.cash)),
                ("Net worth", money(c.net_worth)), ("Total revenue", money(c.total_revenue)),
                ("Customers", str(c.customers)), ("Employees", str(len(c.employees)))]
        for i, (a, b) in enumerate(rows):
            text(s, a, (box.x + 24, box.y + 44 + i * 30), 17, S.MUTED)
            text(s, b, (box.right - 24, box.y + 44 + i * 30), 17, S.TEXT, bold=True, anchor="topright")
        if ui.button(s, (S.WIDTH // 2 - 250, 580, 240, 54), "Play Again", kind="success", size=20):
            self.new_game()
        if ui.button(s, (S.WIDTH // 2 + 10, 580, 240, 54), "Main Menu", kind="ghost", size=20):
            self.state = "menu"
