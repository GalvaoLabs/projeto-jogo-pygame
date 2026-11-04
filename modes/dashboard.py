"""V1 - Executive Dashboard. Reads and changes the shared Company only."""
import pygame

import settings as S
from core import economy
from modes import ui as uikit
from modes.ui import text, wrap
from systems.localization import L, Msg, t, tu, tn, money

TABS = ["tab.overview", "tab.hr", "tab.products", "tab.marketing", "tab.reports"]   # locale keys
CX, CW = 230, 1030          # content area
CY = 104


def signed(v):
    return ("+" if v > 0 else "") + money(v)


class Dashboard:
    def __init__(self, company, ui):
        self.c = company
        self.ui = ui
        self.tab = 0
        self.pending_dismiss = None  # (employee id, expiry ms)

    # ------------------------------------------------------------ helpers
    def act(self, result):
        ok, msg = result
        self.ui.toast(msg, ok)
        return ok

    def stat_card(self, surf, rect, title, value, sub="", color=S.TEXT):
        self.ui.card(surf, rect, title)
        text(surf, value, (rect.x + 16, rect.y + 38), 28, color, bold=True, max_w=rect.w - 32)
        if sub:
            text(surf, sub, (rect.x + 16, rect.y + rect.h - 28), 14, S.MUTED, max_w=rect.w - 32)

    def row(self, surf, x, y, w, label, value, color=S.TEXT, size=16, bold=False):
        uikit.row(surf, x, y, w, label, value, color, size, bold)

    # ------------------------------------------------------------ main
    def draw(self, surf):
        ui = self.ui
        pygame.draw.rect(surf, S.SIDEBAR, (0, S.NAV_H, 210, S.HEIGHT - S.NAV_H))
        pygame.draw.line(surf, S.BORDER, (210, S.NAV_H), (210, S.HEIGHT))
        for i, key in enumerate(TABS):
            r = pygame.Rect(14, S.NAV_H + 20 + i * 52, 182, 42)
            if ui.button(surf, r, t(key), kind="primary" if i == self.tab else "ghost",
                         size=15, active=(i == self.tab)):
                self.tab = i
        text(surf, t(TABS[self.tab]), (CX, S.NAV_H + 8), 26, S.TEXT, bold=True, max_w=CW)
        [self.overview, self.hr, self.products, self.marketing, self.financials][self.tab](surf)

    # ------------------------------------------------------------ overview
    def overview(self, surf):
        c = self.c
        p = c.preview()
        last = c.last_report
        ref = last or p
        tag = t("ov.tag_last") if last else t("ov.tag_projected")
        w, gap = 245, 16

        def xs(i):
            return CX + i * (w + gap)

        profit_color = S.GREEN if ref.profit >= 0 else S.RED
        self.stat_card(surf, pygame.Rect(xs(0), CY + 8, w, 104), tu("fin.cash_balance"), money(c.cash),
                       t("ov.net_worth_sub", v=c.net_worth), S.GREEN if c.cash >= 0 else S.RED)
        self.stat_card(surf, pygame.Rect(xs(1), CY + 8, w, 104), tu("ov.monthly_revenue"), money(ref.revenue),
                       tag, S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(2), CY + 8, w, 104), tu("ov.monthly_expenses"), money(ref.expenses),
                       tag, S.PURPLE)
        self.stat_card(surf, pygame.Rect(xs(3), CY + 8, w, 104), tu("ov.net_profit"), signed(ref.profit),
                       tag, profit_color)

        self.stat_card(surf, pygame.Rect(xs(0), CY + 128, w, 104), tu("biz.employees"),
                       f"{len(c.employees)} / {c.office_capacity}", t("common.payroll", v=c.monthly_payroll), S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(1), CY + 128, w, 104), tu("biz.customers"), L.integer(c.customers),
                       t("ov.price_sub", v=c.product.price), S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(2), CY + 128, w, 104), tu("biz.reputation"), t("ov.reputation_value", v=c.reputation),
                       t("ov.quality_sub", v=c.product.quality), S.PURPLE)
        self.stat_card(surf, pygame.Rect(xs(3), CY + 128, w, 104), tu("ov.valuation"), money(c.valuation),
                       t("ov.valuation_sub", mult=S.VALUATION_REVENUE_MULT), S.PURPLE)

        goal = pygame.Rect(CX, CY + 248, CW, 92)
        self.ui.card(surf, goal, tu("ov.goal_title", goal=S.GOAL_NET_WORTH))
        self.ui.bar(surf, (goal.x + 16, goal.y + 40, CW - 32, 18), c.net_worth, S.GOAL_NET_WORTH, S.GREEN)
        pct = max(0, c.net_worth) / S.GOAL_NET_WORTH * 100
        text(surf, f"{money(c.net_worth)}  ({L.percent(pct, 1)})", (goal.x + 16, goal.y + 64), 15, S.TEXT, max_w=CW - 32)

        box = pygame.Rect(CX, CY + 356, CW, 228)
        self.ui.card(surf, box, tu("ov.projection_title", when=p.month))
        lx, ly, lw = box.x + 20, box.y + 42, 440
        self.row(surf, lx, ly, lw, t("fin.revenue"), money(p.revenue), S.GREEN)
        self.row(surf, lx, ly + 26, lw, t("fin.salaries"), money(-p.salaries))
        self.row(surf, lx, ly + 52, lw, t("fin.marketing"), money(-p.marketing))
        self.row(surf, lx, ly + 78, lw, t("fin.office"), money(-p.office))
        self.row(surf, lx, ly + 104, lw, t("fin.other"), money(-p.other))
        self.row(surf, lx, ly + 130, lw, t("fin.one_time_month"), money(-p.one_time))
        pygame.draw.line(surf, S.BORDER, (lx, ly + 158), (lx + lw, ly + 158))
        self.row(surf, lx, ly + 166, lw, t("fin.projected_profit"), signed(p.profit),
                 S.GREEN if p.profit >= 0 else S.RED, 18, True)

        rx = box.x + 520
        net_cust = p.customers_end - p.customers_start
        self.row(surf, rx, ly, 480, t("biz.customers"),
                 f"{L.integer(p.customers_start)} -> {L.integer(p.customers_end)} ({'+' if net_cust > 0 else ''}{L.number(net_cust)})",
                 S.GREEN if net_cust >= 0 else S.RED)
        self.row(surf, rx, ly + 26, 480, t("biz.reputation"), f"{L.number(p.rep_start, 1)} -> {L.number(p.rep_end, 1)}")
        self.row(surf, rx, ly + 52, 480, t("biz.quality"), f"{L.number(p.quality_start, 1)} -> {L.number(p.quality_end, 1)}")
        self.row(surf, rx, ly + 78, 480, t("biz.dev_progress"),
                 f"{L.percent(c.product.progress)} -> {L.percent(p.progress_end)}")
        if p.profit < 0:
            runway = c.cash / -p.profit if p.profit else 99
            tip = t("ov.runway_tip", m=runway)
            col = S.RED if runway < 3 else S.ORANGE
        else:
            tip = t("ov.profitable_tip")
            col = S.GREEN
        for i, line in enumerate(wrap(tip, 15, 480)):
            text(surf, line, (rx, ly + 120 + i * 20), 15, col, bold=True)

    # ------------------------------------------------------------ HR
    def hr(self, surf):
        c, ui = self.c, self.ui
        left = pygame.Rect(CX, CY, 600, 592)
        ui.card(surf, left, tu("hr.team"))
        text(surf, t("hr.desks", used=len(c.employees), cap=c.office_capacity), (left.right - 16, left.y + 12), 15,
             S.MUTED, bold=True, anchor="topright", max_w=300)
        hy = left.y + 40
        for key, dx, mw in (("hr.col_name", 16, 108), ("hr.col_role", 130, 164), ("hr.col_salary", 300, 86),
                            ("hr.col_productivity", 392, 100)):
            text(surf, t(key), (left.x + dx, hy), 13, S.MUTED, bold=True, max_w=mw)
        pygame.draw.line(surf, S.BORDER, (left.x + 12, hy + 22), (left.right - 12, hy + 22))
        now = pygame.time.get_ticks()
        if self.pending_dismiss and now > self.pending_dismiss[1]:
            self.pending_dismiss = None
        for i, e in enumerate(c.employees):
            ry = hy + 30 + i * 32
            if i % 2 == 0:
                pygame.draw.rect(surf, S.CARD_HI, (left.x + 8, ry - 3, left.w - 16, 30), border_radius=6)
            pygame.draw.rect(surf, e.color, (left.x + 14, ry + 5, 8, 14), border_radius=3)
            text(surf, e.name, (left.x + 30, ry), 15, S.TEXT, bold=True, max_w=96)
            text(surf, t(f"role_short.{e.role}"), (left.x + 130, ry), 15, e.color, max_w=164)
            text(surf, money(e.salary), (left.x + 300, ry), 15, max_w=86)
            ui.bar(surf, (left.x + 392, ry + 6, 70, 10), e.productivity, 1.3, S.BLUE)
            text(surf, L.number(e.productivity, 2), (left.x + 470, ry), 14, S.MUTED)
            confirming = self.pending_dismiss and self.pending_dismiss[0] == e.id
            if ui.button(surf, (left.right - 96, ry - 1, 84, 26), t("hr.sure") if confirming else t("hr.dismiss"),
                         kind="danger", size=13):
                if confirming:
                    self.act(c.dismiss(e.id))
                    self.pending_dismiss = None
                else:
                    self.pending_dismiss = (e.id, now + 2500)
                    ui.toast(Msg("msg.confirm_dismiss", {"name": e.name, "sev": e.severance}), True)
                break

        right = pygame.Rect(CX + 616, CY, 414, 330)
        ui.card(surf, right, tu("hr.hire_title"))
        full = len(c.employees) >= c.office_capacity
        sub = t("hr.office_full") if full else tn("hr.free_desks", c.office_capacity - len(c.employees))
        text(surf, sub, (right.x + 16, right.y + 34), 14, S.ORANGE if full else S.MUTED, max_w=382)
        for i, role in enumerate(S.ROLE_ORDER):
            info = S.ROLES[role]
            r = pygame.Rect(right.x + 16, right.y + 62 + i * 65, 382, 58)
            fee = int(info["salary"] * S.HIRE_FEE_RATE)
            if ui.button(surf, r, "", enabled=not full, kind="ghost"):
                self.act(c.hire(role))
            pygame.draw.rect(surf, info["color"], (r.x, r.y, 8, r.h), border_top_left_radius=8,
                             border_bottom_left_radius=8)
            # three short lines (title / pay / description) so long translations never collide
            text(surf, t("hr.hire_role", role=role), (r.x + 20, r.y + 4), 15, S.WHITE if not full else S.MUTED,
                 bold=True, max_w=r.w - 32)
            text(surf, t("hr.salary_fee", salary=info["salary"], fee=fee), (r.x + 20, r.y + 22), 12, S.TEXT,
                 max_w=r.w - 32)
            text(surf, t(f"role_desc.{role}"), (r.x + 20, r.y + 39), 12, S.MUTED, max_w=r.w - 32, min_size=10)

        pay = pygame.Rect(CX + 616, CY + 346, 414, 246)
        ui.card(surf, pay, tu("hr.payroll_title"))
        self.row(surf, pay.x + 16, pay.y + 42, 382, t("hr.monthly_payroll"), money(c.monthly_payroll), S.PURPLE, 16, True)
        counts = {r: 0 for r in S.ROLES}
        for e in c.employees:
            counts[e.role] += 1
        for i, role in enumerate(S.ROLE_ORDER):
            self.row(surf, pay.x + 16, pay.y + 76 + i * 26, 382, t(f"role.{role}"), str(counts[role]), S.ROLES[role]["color"])
        avg = sum(e.productivity for e in c.employees) / max(1, len(c.employees))
        self.row(surf, pay.x + 16, pay.y + 186, 382, t("hr.avg_productivity"), L.number(avg, 2))
        text(surf, t("hr.dismissal_cost", pct=int(S.SEVERANCE_RATE * 100)), (pay.x + 16, pay.y + 214), 13, S.MUTED,
             max_w=382)

    # ------------------------------------------------------------ products
    def products(self, surf):
        c, ui, p = self.c, self.ui, self.c.product
        left = pygame.Rect(CX, CY, 600, 360)
        ui.card(surf, left, tu("prod.title"))
        text(surf, p.name, (left.x + 16, left.y + 36), 30, S.TEXT, bold=True, max_w=300)
        text(surf, t("prod.version", v=p.version), (left.right - 16, left.y + 46), 16, S.PURPLE, bold=True,
             anchor="topright", max_w=220)
        text(surf, t("prod.dev_progress", v=p.version + 1), (left.x + 16, left.y + 88), 14, S.MUTED, max_w=480)
        ui.bar(surf, (left.x + 16, left.y + 110, 568, 16), p.progress, 100, S.BLUE)
        text(surf, L.percent(p.progress), (left.right - 16, left.y + 88), 14, S.TEXT, anchor="topright")
        text(surf, t("biz.quality"), (left.x + 16, left.y + 144), 14, S.MUTED, max_w=400)
        ui.bar(surf, (left.x + 16, left.y + 166, 568, 16), p.quality, 100, S.GREEN)
        text(surf, f"{L.number(p.quality, 1)} / 100", (left.right - 16, left.y + 144), 14, S.TEXT, anchor="topright")
        text(surf, t("prod.price_label"), (left.x + 16, left.y + 206), 14, S.MUTED, max_w=568)
        text(surf, money(p.price), (left.x + 16, left.y + 228), 30, S.TEXT, bold=True)
        for i, (lab, d) in enumerate((("-10", -10), ("-1", -1), ("+1", 1), ("+10", 10))):
            if ui.button(surf, (left.x + 250 + i * 80, left.y + 230, 72, 38), lab, kind="ghost"):
                self.act(c.set_price(p.price + d))
        ref = economy.reference_price(p.quality)
        col = S.GREEN if p.price <= ref else S.ORANGE
        text(surf, t("prod.fair_price", v=ref), (left.x + 16, left.y + 284), 15, col, max_w=568)
        text(surf, t("prod.price_hint"), (left.x + 16, left.y + 308), 13, S.MUTED, max_w=568)
        text(surf, t("prod.total_invested", v=p.dev_investment), (left.x + 16, left.y + 332), 14, S.MUTED, max_w=568)

        right = pygame.Rect(CX + 616, CY, 414, 360)
        ui.card(surf, right, tu("prod.invest_title"))
        for i, (cost, pts) in enumerate(S.DEV_INVESTMENTS):
            r = pygame.Rect(right.x + 16, right.y + 44 + i * 86, 382, 74)
            if ui.button(surf, r, "", enabled=c.cash >= cost, kind="primary" if i == 0 else "purple"):
                self.act(c.invest_dev(i))
            text(surf, t("prod.invest_line", name=t("prod.sprint" if i == 0 else "prod.overhaul"), cost=cost),
                 (r.x + 16, r.y + 12), 17, S.WHITE if c.cash >= cost else S.MUTED, bold=True, max_w=r.w - 32)
            text(surf, t("prod.invest_points", pts=pts), (r.x + 16, r.y + 40), 14, S.MUTED, max_w=r.w - 32)
        qpr = economy.quality_per_release(c)
        for i, line in enumerate(wrap(t("prod.release_note", q=qpr), 14, 382, max_lines=6)):
            text(surf, line, (right.x + 16, right.y + 226 + i * 20), 14, S.MUTED)

        bot = pygame.Rect(CX, CY + 376, CW, 216)
        ui.card(surf, bot, tu("prod.market_title"))
        self.row(surf, bot.x + 20, bot.y + 42, 440, t("market.appeal"), L.percent(economy.market_appeal(c) * 100), S.BLUE)
        self.row(surf, bot.x + 20, bot.y + 70, 440, t("market.churn"), L.percent(economy.churn_rate(c) * 100, 1),
                 S.RED if economy.churn_rate(c) > 0.07 else S.GREEN)
        self.row(surf, bot.x + 20, bot.y + 98, 440, t("market.organic"), "+" + L.number(economy.organic_customers(c), 1))
        self.row(surf, bot.x + 20, bot.y + 126, 440, t("market.referrals"), "+" + L.number(economy.referral_customers(c), 1))
        self.row(surf, bot.x + 20, bot.y + 154, 440, t("market.saturation"),
                 L.percent((1 - economy.saturation(c.customers)) * 100))
        pr = c.preview()
        months = None if pr.progress_gain <= 0 else max(1, int((100 - p.progress) / pr.progress_gain + 0.99))
        self.row(surf, bot.x + 540, bot.y + 42, 460, t("biz.customers"), L.integer(c.customers))
        self.row(surf, bot.x + 540, bot.y + 70, 460, t("market.revenue_now"), money(pr.revenue), S.GREEN)
        self.row(surf, bot.x + 540, bot.y + 98, 460, t("market.revenue_per_customer"), money(p.price))
        self.row(surf, bot.x + 540, bot.y + 126, 460, t("market.next_release"),
                 t("market.never") if months is None else tn("market.months", months))

    # ------------------------------------------------------------ marketing
    def marketing(self, surf):
        c, ui = self.c, self.ui
        box = pygame.Rect(CX, CY, CW, 452)
        ui.card(surf, box, tu("mkt.campaigns_title"))
        for i, camp in enumerate(economy.CAMPAIGNS):
            ry = box.y + 42 + i * 100
            active = camp["id"] in c.active_campaigns
            row = pygame.Rect(box.x + 12, ry, box.w - 24, 90)
            pygame.draw.rect(surf, S.CARD_HI, row, border_radius=10)
            if active:
                pygame.draw.rect(surf, S.GREEN, row, 2, border_radius=10)
            text(surf, t(f"campaign.{camp['id']}.name"), (row.x + 16, row.y + 10), 18, S.TEXT, bold=True, max_w=440)
            text(surf, t(f"campaign.{camp['id']}.desc"), (row.x + 16, row.y + 38), 14, S.MUTED, max_w=450)
            exp = economy.campaign_customers(c, camp)
            text(surf, t("mkt.investment", v=camp["cost"]), (row.x + 16, row.y + 62), 14, S.PURPLE, bold=True, max_w=440)
            text(surf, t("mkt.expected", n=exp), (row.x + 480, row.y + 20), 15, S.GREEN, bold=True, max_w=370)
            text(surf, t("mkt.rep_impact", v=camp["rep"]), (row.x + 480, row.y + 50), 15, S.BLUE, bold=True, max_w=370)
            label = t("mkt.stop") if active else t("mkt.launch")
            if ui.button(surf, (row.right - 140, row.y + 22, 124, 44), label,
                         kind="danger" if active else "success"):
                self.act(c.toggle_campaign(camp["id"]))
        sm = pygame.Rect(CX, CY + 468, CW, 124)
        ui.card(surf, sm, tu("mkt.summary_title"))
        self.row(surf, sm.x + 20, sm.y + 40, 440, t("mkt.monthly_investment"), money(c.marketing_investment), S.PURPLE, 16, True)
        self.row(surf, sm.x + 20, sm.y + 68, 440, t("mkt.expected_total"),
                 "+" + L.number(economy.expected_marketing_customers(c), 0), S.GREEN)
        self.row(surf, sm.x + 20, sm.y + 94, 440, t("mkt.rep_total"),
                 t("mkt.rep_total_value", v=economy.marketing_reputation(c)), S.BLUE)
        mm = economy.marketing_multiplier(c)
        self.row(surf, sm.x + 540, sm.y + 40, 460, t("mkt.team_multiplier"), "x" + L.number(mm, 2), S.BLUE)
        self.row(surf, sm.x + 540, sm.y + 68, 460, t("mkt.campaign_effect"),
                 "x" + L.number(0.5 + economy.market_appeal(c), 2))
        text(surf, t("mkt.hire_tip"), (sm.x + 540, sm.y + 94), 14, S.MUTED, max_w=460)

    # ------------------------------------------------------------ financials
    def financials(self, surf):
        c, ui = self.c, self.ui
        h = c.history
        last = h[-1] if h else None
        w = 245
        vals = [(tu("rep.revenue_last"), money(last.revenue) if last else "-", S.BLUE),
                (tu("rep.expenses_last"), money(last.expenses) if last else "-", S.PURPLE),
                (tu("rep.profit_last"), signed(last.profit) if last else "-",
                 (S.GREEN if last.profit >= 0 else S.RED) if last else S.MUTED),
                (tu("fin.cash_balance"), money(c.cash), S.GREEN if c.cash >= 0 else S.RED)]
        for i, (title, v, col) in enumerate(vals):
            r = pygame.Rect(CX + i * (w + 16), CY + 8, w, 84)
            ui.card(surf, r, title)
            text(surf, v, (r.x + 16, r.y + 40), 22, col, bold=True, max_w=w - 32)

        perf = pygame.Rect(CX, CY + 104, CW, 56)
        ui.card(surf, perf)
        if not last:
            rating, col, note = t("perf.none"), S.MUTED, t("perf.note_none")
        else:
            if last.profit >= 0:
                rating, col, note = t("perf.healthy"), S.GREEN, t("perf.note_healthy")
            else:
                runway = c.cash / -last.profit
                if runway < 3:
                    rating, col = t("perf.critical"), S.RED
                else:
                    rating, col = t("perf.at_risk"), S.ORANGE
                note = t("perf.note_burn", burn=-last.profit, m=runway)
        text(surf, tu("rep.performance"), (perf.x + 16, perf.y + 8), 13, S.MUTED, bold=True, max_w=230)
        text(surf, rating, (perf.x + 16, perf.y + 26), 20, col, bold=True, max_w=230)
        text(surf, note, (perf.x + 260, perf.y + 20), 16, S.TEXT, max_w=CW - 260 - 16)

        ch = pygame.Rect(CX, CY + 172, CW, 210)
        ui.card(surf, ch, tu("rep.chart_title"))
        recent = h[-12:]
        area = pygame.Rect(ch.x + 24, ch.y + 44, ch.w - 48, 140)
        if not recent:
            text(surf, t("rep.no_history"), area.center, 16, S.MUTED, anchor="center")
        else:
            mx = max(1, max(abs(r.profit) for r in recent))
            zero = area.y + area.h // 2
            pygame.draw.line(surf, S.BORDER, (area.x, zero), (area.right, zero))
            slot = area.w / 12
            for i, r in enumerate(recent):
                bh = int(abs(r.profit) / mx * (area.h // 2 - 14))
                bx = int(area.x + i * slot + slot * 0.2)
                bw = int(slot * 0.6)
                if r.profit >= 0:
                    pygame.draw.rect(surf, S.GREEN, (bx, zero - bh, bw, max(2, bh)), border_radius=3)
                else:
                    pygame.draw.rect(surf, S.RED, (bx, zero, bw, max(2, bh)), border_radius=3)
                text(surf, L.month_name(r.month), (bx + bw // 2, area.bottom + 2), 11, S.MUTED, anchor="midtop")

        tb = pygame.Rect(CX, CY + 394, CW, 198)
        ui.card(surf, tb, tu("rep.table_title"))
        cols = [("rep.col_month", 16), ("rep.col_revenue", 170), ("rep.col_expenses", 340), ("rep.col_profit", 510),
                ("rep.col_cash", 680), ("biz.customers", 860)]
        for key, dx in cols:
            text(surf, t(key), (tb.x + dx, tb.y + 34), 13, S.MUTED, bold=True, max_w=150)
        for i, r in enumerate(reversed(h[-6:])):
            y = tb.y + 56 + i * 22
            text(surf, L.month_label(r.month), (tb.x + 16, y), 14, max_w=150)
            text(surf, money(r.revenue), (tb.x + 170, y), 14, S.BLUE, max_w=160)
            text(surf, money(r.expenses), (tb.x + 340, y), 14, S.PURPLE, max_w=160)
            text(surf, signed(r.profit), (tb.x + 510, y), 14, S.GREEN if r.profit >= 0 else S.RED, max_w=160)
            text(surf, money(r.cash_end), (tb.x + 680, y), 14, max_w=170)
            text(surf, L.integer(r.customers_end), (tb.x + 860, y), 14)
        if not h:
            text(surf, t("rep.nothing_yet", btn=tu("nav.end_month")), (tb.x + 16, tb.y + 60), 15, S.MUTED,
                 max_w=CW - 32)
