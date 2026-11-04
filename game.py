"""Game loop, screens (menu / settings / play / report / end) and navigation."""
import math

import pygame

import settings as S
from core.company import Company
from modes.dashboard import Dashboard
from modes.office import OfficeMode
from modes import ui as uikit
from modes.ui import UI, text, row, draw_flag
from systems import paths
from systems.localization import L, Msg, t, tu, money
from systems.settings_manager import SettingsManager


class Game:
    def __init__(self, settings_path=None):
        pygame.init()
        # Settings first: the saved language must be active before the first frame is drawn.
        self.settings = SettingsManager(path=settings_path, valid_languages=L.available_languages)
        L.set_language(self.settings.language)
        self.screen = None
        self.apply_display()
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.state = "menu"        # menu | settings | play | end
        self.settings_from = "menu"
        self.mode = "dashboard"    # dashboard | office
        self.company = None
        self.dashboard = None
        self.office = None
        self.report = None         # month report shown in a modal
        self.t = 0.0
        self.running = True

    # ------------------------------------------------------------ display / settings
    def apply_display(self):
        """(Re)create the window. Fullscreen uses SCALED so the 1280x720 layout is stretched."""
        flags = 0
        if self.settings.fullscreen and not paths.is_web():
            flags = pygame.FULLSCREEN | pygame.SCALED
        self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT), flags)
        pygame.display.set_caption(t("app.window_title"))

    def change_language(self, code):
        """Switch language at runtime: no restart, the running company is untouched."""
        if code == L.language or not L.set_language(code):
            return False
        self.settings.set("language", code)          # persisted immediately
        pygame.display.set_caption(t("app.window_title"))
        self.ui.toast(Msg("settings.language_changed", {"name": L.meta().get("name", code)}), True)
        return True

    def toggle_fullscreen(self):
        self.settings.set("fullscreen", not self.settings.fullscreen)
        self.apply_display()

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
    def tick(self):
        """One frame: events, update, draw. Shared by the desktop loop and the web (async) loop."""
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

    def run(self):
        while self.running:
            self.tick()
        pygame.quit()

    async def run_async(self):
        """Same loop, but yields to the browser every frame (required by Pygbag / WebAssembly)."""
        import asyncio
        while self.running:
            self.tick()
            await asyncio.sleep(0)
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
        elif self.state == "settings" and key == pygame.K_ESCAPE:
            self.state = "menu"
        elif self.state == "menu" and key == pygame.K_ESCAPE and self.can_continue():
            self.state = "play"

    def frame(self, dt):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
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
        text(s, "STARTUP TYCOON", (S.WIDTH // 2, 150), 76, S.TEXT, bold=True, anchor="center")   # brand name
        text(s, tu("menu.tagline"), (S.WIDTH // 2, 218), 34, S.BLUE, bold=True, anchor="center", max_w=900)
        bw, bh, y = 320, 56, 320
        if self.can_continue():
            if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), t("menu.continue"), kind="primary", size=22):
                self.state = "play"
            y += 72
        if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), t("menu.new_game"), kind="success", size=22):
            self.new_game()
        y += 72
        if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), t("menu.settings"), kind="ghost", size=22):
            self.settings_from = "menu"
            self.state = "settings"
        y += 72
        if not paths.is_web():               # a browser tab cannot be "quit" by the game
            if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), t("menu.quit"), kind="danger", size=22):
                self.running = False
        text(s, t("menu.goal", goal=S.GOAL_NET_WORTH), (S.WIDTH // 2, 650), 16, S.MUTED, anchor="center", max_w=1100)
        text(s, t("menu.hint"), (S.WIDTH // 2, 678), 14, S.MUTED, anchor="center", max_w=1100)

    # ------------------------------------------------------------ settings
    def draw_settings(self):
        s, ui = self.screen, self.ui
        s.fill(S.BG)
        cx = S.WIDTH // 2
        text(s, tu("menu.settings"), (cx, 70), 44, S.TEXT, bold=True, anchor="center", max_w=900)

        langs = L.available_languages()
        panel_w = 520
        panel = pygame.Rect(cx - panel_w // 2, 120, panel_w, 74 + len(langs) * 52 + 76)
        ui.card(s, panel)
        text(s, t("settings.language_label"), (panel.x + 20, panel.y + 16), 18, S.TEXT, bold=True, max_w=panel_w - 40)
        for i, code in enumerate(langs):
            meta = L.meta(code)
            r = pygame.Rect(panel.x + 16, panel.y + 52 + i * 52, panel_w - 32, 44)
            active = code == L.language
            if ui.button(s, r, "", kind="primary" if active else "ghost", active=active):
                self.change_language(code)
            draw_flag(s, pygame.Rect(r.x + 12, r.y + 10, 36, 24), meta.get("flag", ""))
            tag = t("settings.beta") if meta.get("status") == "beta" else ""
            text(s, meta.get("name", code), (r.x + 62, r.centery), 18, S.WHITE, bold=True, anchor="midleft",
                 max_w=r.w - 62 - (90 if tag else 24))
            if tag:
                text(s, tag, (r.right - 14, r.centery), 13, S.YELLOW, bold=True, anchor="midright")
        y = panel.y + 52 + len(langs) * 52 + 8
        if any(L.meta(c).get("status") == "beta" for c in langs):
            text(s, t("settings.beta_note"), (panel.x + 20, y), 12, S.MUTED, max_w=panel_w - 40)

        by = panel.bottom + 16
        if not paths.is_web():
            state = t("settings.on") if self.settings.fullscreen else t("settings.off")
            if ui.button(s, (cx - panel_w // 2, by, panel_w, 48), t("settings.fullscreen") + ": " + state,
                         kind="success" if self.settings.fullscreen else "ghost", size=18):
                self.toggle_fullscreen()
            by += 60
        if ui.button(s, (cx - 140, by, 280, 52), t("settings.back"), kind="primary", size=20):
            self.state = "menu"

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
        if ui.button(s, (12, 8, 150, 40), tu("nav.dashboard"), kind="primary" if self.mode == "dashboard" else "ghost",
                     size=15, active=self.mode == "dashboard"):
            self.mode = "dashboard"
        if ui.button(s, (170, 8, 130, 40), tu("nav.office"), kind="primary" if self.mode == "office" else "ghost",
                     size=15, active=self.mode == "office"):
            self.mode = "office"
        text(s, t("nav.month", n=c.month, when=c.month), (330, 8), 15, S.TEXT, bold=True, max_w=220)
        text(s, t("common.cash", v=c.cash), (330, 30), 14, S.GREEN if c.cash >= 0 else S.RED, bold=True, max_w=220)
        text(s, t("nav.net_worth", v=c.net_worth, goal=S.GOAL_NET_WORTH), (560, 19), 15, S.TEXT, max_w=460)
        if ui.button(s, (1040, 8, 70, 40), tu("nav.menu"), kind="ghost", size=14):
            self.state = "menu"
        if ui.button(s, (1118, 8, 150, 40), tu("nav.end_month"), kind="success", size=16):
            self.end_month()

    # ------------------------------------------------------------ report modal
    def draw_report(self):
        s, ui, r = self.screen, self.ui, self.report
        dim = pygame.Surface((S.WIDTH, S.HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        s.blit(dim, (0, 0))
        if uikit.LAYOUT_HOOK:
            uikit.LAYOUT_HOOK("layer", pygame.Rect(0, 0, S.WIDTH, S.HEIGHT), "")   # everything before is now dimmed
        box = pygame.Rect(0, 0, 700, 600)
        box.center = (S.WIDTH // 2, S.HEIGHT // 2)
        pygame.draw.rect(s, S.CARD, box, border_radius=16)
        pygame.draw.rect(s, S.BORDER, box, 2, border_radius=16)
        text(s, t("report.title", when=r.month), (box.x + 28, box.y + 22), 26, S.TEXT, bold=True, max_w=box.w - 56)

        y = box.y + 72
        x1, w1 = box.x + 28, 300
        text(s, tu("report.finances"), (x1, y), 13, S.BLUE, bold=True)
        row(s, x1, y + 26, w1, t("fin.revenue"), money(r.revenue), S.GREEN)
        row(s, x1, y + 52, w1, t("fin.salaries"), money(-r.salaries))
        row(s, x1, y + 78, w1, t("fin.marketing"), money(-r.marketing))
        row(s, x1, y + 104, w1, t("fin.office"), money(-r.office))
        row(s, x1, y + 130, w1, t("fin.other"), money(-r.other))
        row(s, x1, y + 156, w1, t("fin.one_time"), money(-r.one_time))
        pygame.draw.line(s, S.BORDER, (x1, y + 186), (x1 + w1, y + 186))
        row(s, x1, y + 196, w1, t("fin.profit_loss"), ("+" if r.profit > 0 else "") + money(r.profit),
            S.GREEN if r.profit >= 0 else S.RED, bold=True)
        row(s, x1, y + 230, w1, t("fin.cash_balance"), money(r.cash_end), S.GREEN if r.cash_end >= 0 else S.RED, bold=True)
        row(s, x1, y + 256, w1, t("fin.net_worth"), money(r.net_worth), S.PURPLE, bold=True)
        if r.capex:
            row(s, x1, y + 282, w1, t("fin.capex"), money(-r.capex))

        x2, w2 = box.x + 372, 300
        text(s, tu("report.business"), (x2, y), 13, S.BLUE, bold=True)
        row(s, x2, y + 26, w2, t("report.customers_start"), str(r.customers_start))
        row(s, x2, y + 52, w2, t("report.new_organic"), f"+{r.organic}", S.GREEN)
        row(s, x2, y + 78, w2, t("report.new_referral"), f"+{r.referral}", S.GREEN)
        row(s, x2, y + 104, w2, t("report.new_marketing"), f"+{r.from_marketing}", S.GREEN)
        row(s, x2, y + 130, w2, t("report.churned"), f"-{r.churned}", S.RED)
        row(s, x2, y + 156, w2, t("report.customers_now"), str(r.customers_end), S.TEXT, bold=True)
        row(s, x2, y + 196, w2, t("biz.reputation"), f"{L.number(r.rep_start, 1)} -> {L.number(r.rep_end, 1)}")
        row(s, x2, y + 222, w2, t("biz.quality"), f"{L.number(r.quality_start, 1)} -> {L.number(r.quality_end, 1)}")
        row(s, x2, y + 248, w2, t("biz.development"), t("report.development_value", gain=r.progress_gain, now=r.progress_end))
        if r.releases:
            text(s, t("report.version_released", v=r.version_end), (x2, y + 282), 16, S.YELLOW, bold=True, max_w=w2)

        status = self.company.status
        if status == "bankrupt":
            text(s, t("report.bankrupt"), (box.x + 28, box.bottom - 120), 18, S.RED, bold=True, max_w=box.w - 56)
        elif status == "victory":
            text(s, t("report.victory"), (box.x + 28, box.bottom - 120), 18, S.GREEN, bold=True, max_w=box.w - 56)
        label = t("menu.continue") if status == "running" else t("report.see_result")
        if ui.button(s, (box.centerx - 110, box.bottom - 78, 220, 50), label, kind="success", size=18):
            self.close_report()

    # ------------------------------------------------------------ end screens
    def draw_end(self):
        s, ui, c = self.screen, self.ui, self.company
        s.fill(S.BG)
        won = c.status == "victory"
        col = S.GREEN if won else S.RED
        pygame.draw.rect(s, tuple(v // 6 for v in col), (0, 0, S.WIDTH, 260))
        text(s, tu("end.victory" if won else "end.bankrupt"), (S.WIDTH // 2, 100), 84, col, bold=True,
             anchor="center", max_w=1100)
        text(s, t("end.sub_victory" if won else "end.sub_bankrupt"), (S.WIDTH // 2, 190), 22, S.TEXT,
             anchor="center", max_w=1180)
        box = pygame.Rect(0, 0, 520, 250)
        box.center = (S.WIDTH // 2, 410)
        ui.card(s, box, tu("end.final_results"))
        rows = [(t("end.months_played"), str(c.month - 1)), (t("end.final_cash"), money(c.cash)),
                (t("fin.net_worth"), money(c.net_worth)), (t("end.total_revenue"), money(c.total_revenue)),
                (t("biz.customers"), str(c.customers)), (t("biz.employees"), str(len(c.employees)))]
        for i, (a, b) in enumerate(rows):
            row(s, box.x + 24, box.y + 44 + i * 30, box.w - 48, a, b, S.TEXT, 17, True)
        if ui.button(s, (S.WIDTH // 2 - 250, 580, 240, 54), t("end.play_again"), kind="success", size=20):
            self.new_game()
        if ui.button(s, (S.WIDTH // 2 + 10, 580, 240, 54), t("end.main_menu"), kind="ghost", size=20):
            self.state = "menu"

