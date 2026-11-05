"""Game loop, screens (menu / settings / play / report / end) and navigation."""
import json
import math
import os

import pygame

import settings as S
from core.company import Company
from modes.dashboard import Dashboard
from modes.office import OfficeMode
from modes import ui as uikit
from modes.ui import UI, text, row, draw_flag
from systems import paths
from systems.audio import Audio
from systems.localization import L, Msg, t, tu, money
from systems.settings_manager import SettingsManager
from systems.storage import FileStorage, default_storage


SAVE_NAME = "savegame.json"
AUTOSAVE_SECONDS = 20.0
# Events that mean "the OS may kill us now" (phones, tablets): save immediately.
BACKGROUND_EVENTS = tuple(getattr(pygame, n) for n in
                          ("APP_WILLENTERBACKGROUND", "APP_DIDENTERBACKGROUND", "APP_TERMINATING")
                          if hasattr(pygame, n))
BACK_KEYS = tuple(k for k in (pygame.K_ESCAPE, getattr(pygame, "K_AC_BACK", None)) if k is not None)
TAB_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5)


class Game:
    def __init__(self, settings_path=None, storage=None):
        if paths.is_web():
            # Pygbag: initialise only what we need; the mixer is opened lazily on the first sound,
            # after the player has clicked the page (browsers refuse audio before a gesture).
            pygame.display.init()
            pygame.font.init()
        else:
            pygame.init()
        if storage is None:
            storage = FileStorage(os.path.dirname(settings_path) or ".") if settings_path else default_storage()
        self.storage = storage
        # Settings first: the saved language must be active before the first frame is drawn.
        self.settings = SettingsManager(path=None, valid_languages=L.available_languages, storage=storage)
        L.set_language(self.settings.language)
        self.audio = Audio(self.settings.sound, self.settings.volume)
        self.screen = None
        self.set_window_icon()
        self.apply_display()
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.ui.sfx = self.audio.play
        self.state = "menu"        # menu | settings | play | end
        self.settings_from = "menu"
        self.mode = "dashboard"    # dashboard | office
        self.company = None
        self.dashboard = None
        self.office = None
        self.report = None         # month report shown in a modal
        self.t = 0.0
        self.since_save = 0.0
        self.running = True
        self.load_game()           # makes "Continue" available after a restart

    # ------------------------------------------------------------ display / settings
    def set_window_icon(self):
        if paths.is_web():
            return
        try:
            pygame.display.set_icon(pygame.image.load(paths.resource_path("assets", "icon.png")))
        except (pygame.error, OSError):
            pass

    def apply_display(self):
        """(Re)create the window. Desktop/Android use SCALED: the game always renders 1280x720 and
        SDL stretches it (letterboxed) to any window / screen size, mapping mouse and touch back."""
        flags = 0
        if not paths.is_web():
            flags = pygame.SCALED
            if paths.is_android() or self.settings.fullscreen:
                flags |= pygame.FULLSCREEN
            else:
                flags |= pygame.RESIZABLE
        try:
            self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
        pygame.display.set_caption(t("app.window_title"))

    def change_language(self, code):
        """Switch language at runtime: no restart, the running company is untouched."""
        if code == L.language or not L.set_language(code):
            return False
        self.settings.set("language", code)          # persisted immediately
        pygame.display.set_caption(t("app.window_title"))
        self.ui.toast(Msg("settings.language_changed", {"name": L.meta().get("name", code)}), True)
        return True

    @property
    def can_toggle_fullscreen(self):
        return not paths.is_web() and not paths.is_android()

    def toggle_fullscreen(self):
        if self.can_toggle_fullscreen:
            self.settings.set("fullscreen", not self.settings.fullscreen)
            self.apply_display()

    def toggle_sound(self):
        on = not self.settings.sound
        self.settings.set("sound", on)
        self.audio.set_enabled(on)
        self.audio.play("click")

    def set_volume(self, value):
        self.settings.set("volume", value)
        self.audio.set_volume(self.settings.volume)
        self.audio.play("click")

    # ------------------------------------------------------------ saving
    def save_game(self):
        """Autosave. A finished run (victory / bankrupt) removes the save instead."""
        self.since_save = 0.0
        c = self.company
        if c is None:
            return False
        if c.status != "running":
            return self.storage.delete(SAVE_NAME)
        try:
            data = json.dumps(c.to_dict(), separators=(",", ":"))
        except (TypeError, ValueError):
            return False
        return self.storage.write(SAVE_NAME, data)

    def load_game(self):
        raw = self.storage.read(SAVE_NAME)
        if not raw:
            return False
        try:
            c = Company.from_dict(json.loads(raw))
        except Exception:                      # corrupt / foreign / old save: start clean, never crash
            return False
        if c.status != "running":
            return False
        self.attach(c)
        return True

    # ------------------------------------------------------------ lifecycle
    def attach(self, company):
        self.company = company
        self.dashboard = Dashboard(company, self.ui)
        self.office = OfficeMode(company, self.ui, self.goto_dashboard_tab)
        self.mode = "dashboard"
        self.report = None

    def new_game(self):
        self.attach(Company())
        self.state = "play"
        self.ui.toasts.clear()
        self.save_game()

    def go_menu(self):
        self.state = "menu"
        self.save_game()

    def goto_dashboard_tab(self, tab):
        self.mode = "dashboard"
        self.dashboard.tab = tab

    def end_month(self):
        r = self.company.end_month()
        if r:
            self.report = r
            self.ui.sfx("release" if r.releases else "month")
            self.save_game()

    def close_report(self):
        self.report = None
        if self.company.status != "running":
            self.state = "end"
            self.ui.sfx("victory" if self.company.status == "victory" else "defeat")

    def can_continue(self):
        return self.company is not None and self.company.status == "running"

    # ------------------------------------------------------------ main loop
    def tick(self):
        """One frame: events, update, draw. Shared by the desktop loop and the web (async) loop."""
        dt = min(self.clock.tick(S.FPS) / 1000.0, 0.1)
        self.t += dt
        clicked, click_pos = False, None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                clicked, click_pos = True, ev.pos       # touch taps arrive as synthetic mouse clicks
            elif ev.type == pygame.KEYDOWN:
                self.on_key(ev.key, ev.mod)
            elif ev.type in BACKGROUND_EVENTS:
                self.save_game()
        self.ui.begin(clicked, click_pos)
        self.frame(dt)
        pygame.display.flip()
        self.since_save += dt
        if self.state == "play" and self.since_save >= AUTOSAVE_SECONDS:
            self.save_game()

    def shutdown(self):
        self.save_game()
        pygame.quit()

    def run(self):
        try:
            while self.running:
                self.tick()
        finally:
            self.shutdown()

    async def run_async(self):
        """Same loop, but yields to the browser every frame (required by Pygbag / WebAssembly)."""
        import asyncio
        try:
            while self.running:
                self.tick()
                await asyncio.sleep(0)
        finally:
            self.shutdown()

    def on_key(self, key, mod=0):
        if key == pygame.K_F11 or (key == pygame.K_RETURN and mod & pygame.KMOD_ALT):
            self.toggle_fullscreen()
            return
        if key == pygame.K_m:
            self.toggle_sound()
            return
        back = key in BACK_KEYS
        if self.state == "play":
            if self.report is not None:
                if back or key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.close_report()
            elif key == pygame.K_TAB:
                self.mode = "office" if self.mode == "dashboard" else "dashboard"
            elif key in TAB_KEYS:
                self.goto_dashboard_tab(TAB_KEYS.index(key))
            elif key == pygame.K_o:
                self.mode = "office"
            elif key == pygame.K_e:
                self.end_month()
            elif back:
                self.go_menu()
        elif self.state == "settings" and back:
            self.state = "menu"
        elif self.state == "menu" and back and self.can_continue():
            self.state = "play"
        elif self.state == "end" and key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.new_game()

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
        if self.can_toggle_fullscreen:       # a browser tab / an Android app is closed by the OS, not the game
            if ui.button(s, ((S.WIDTH - bw) // 2, y, bw, bh), t("menu.quit"), kind="danger", size=22):
                self.running = False
        text(s, t("menu.goal", goal=S.GOAL_NET_WORTH), (S.WIDTH // 2, 650), 16, S.MUTED, anchor="center", max_w=1100)
        text(s, t("menu.hint"), (S.WIDTH // 2, 678), 14, S.MUTED, anchor="center", max_w=1100)
        text(s, f"v{S.VERSION}", (S.WIDTH - 12, S.HEIGHT - 8), 12, S.MUTED, anchor="bottomright")

    # ------------------------------------------------------------ settings
    def draw_settings(self):
        s, ui = self.screen, self.ui
        s.fill(S.BG)
        cx = S.WIDTH // 2
        text(s, tu("menu.settings"), (cx, 62), 44, S.TEXT, bold=True, anchor="center", max_w=900)

        langs = L.available_languages()
        lw, ow, gap = 500, 420, 24
        x0 = cx - (lw + gap + ow) // 2
        top = 116
        lp = pygame.Rect(x0, top, lw, 52 + len(langs) * 52 + 40)
        ui.card(s, lp)
        text(s, t("settings.language_label"), (lp.x + 20, lp.y + 16), 18, S.TEXT, bold=True, max_w=lw - 40)
        for i, code in enumerate(langs):
            meta = L.meta(code)
            r = pygame.Rect(lp.x + 16, lp.y + 52 + i * 52, lw - 32, 44)
            active = code == L.language
            if ui.button(s, r, "", kind="primary" if active else "ghost", active=active):
                self.change_language(code)
            draw_flag(s, pygame.Rect(r.x + 12, r.y + 10, 36, 24), meta.get("flag", ""))
            tag = t("settings.beta") if meta.get("status") == "beta" else ""
            text(s, meta.get("name", code), (r.x + 62, r.centery), 18, S.WHITE, bold=True, anchor="midleft",
                 max_w=r.w - 62 - (90 if tag else 24))
            if tag:
                text(s, tag, (r.right - 14, r.centery), 13, S.YELLOW, bold=True, anchor="midright")
        if any(L.meta(c).get("status") == "beta" for c in langs):
            text(s, t("settings.beta_note"), (lp.x + 20, lp.y + 52 + len(langs) * 52 + 6), 12, S.MUTED, max_w=lw - 40)

        op = pygame.Rect(lp.right + gap, top, ow, lp.h)
        ui.card(s, op)
        text(s, t("settings.options"), (op.x + 20, op.y + 16), 18, S.TEXT, bold=True, max_w=ow - 40)
        y = op.y + 52
        if self.can_toggle_fullscreen:
            state = t("settings.on") if self.settings.fullscreen else t("settings.off")
            if ui.button(s, (op.x + 16, y, ow - 32, 48), t("settings.fullscreen") + ": " + state,
                         kind="success" if self.settings.fullscreen else "ghost", size=18):
                self.toggle_fullscreen()
            y += 64
        state = t("settings.on") if self.settings.sound else t("settings.off")
        if ui.button(s, (op.x + 16, y, ow - 32, 48), t("settings.sound") + ": " + state,
                     kind="success" if self.settings.sound else "ghost", size=18):
            self.toggle_sound()
        y += 64
        text(s, t("settings.volume") + f": {self.settings.volume}%", (op.x + 20, y), 16, S.MUTED, max_w=ow - 40)
        picked = ui.slider(s, (op.x + 28, y + 36, ow - 56, 14), self.settings.volume, 100,
                           S.BLUE if self.settings.sound else S.MUTED)
        if picked is not None:
            self.set_volume(picked)

        if ui.button(s, (cx - 140, lp.bottom + 28, 280, 52), t("settings.back"), kind="primary", size=20):
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
            self.go_menu()
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

