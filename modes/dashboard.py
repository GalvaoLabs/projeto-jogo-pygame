"""V1 - Executive Dashboard. Reads and changes the shared Company only."""
import pygame

import settings as S
from core import economy
from core.company import money
from modes.ui import text, wrap

TABS = ["Overview", "Human Resources", "Products", "Marketing", "Financial Reports"]
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
        text(surf, value, (rect.x + 16, rect.y + 38), 28, color, bold=True)
        if sub:
            text(surf, sub, (rect.x + 16, rect.y + rect.h - 28), 14, S.MUTED)

    def row(self, surf, x, y, w, label, value, color=S.TEXT, size=16, bold=False):
        text(surf, label, (x, y), size, S.MUTED)
        text(surf, value, (x + w, y), size, color, bold=bold, anchor="topright")

    # ------------------------------------------------------------ main
    def draw(self, surf):
        ui = self.ui
        pygame.draw.rect(surf, S.SIDEBAR, (0, S.NAV_H, 210, S.HEIGHT - S.NAV_H))
        pygame.draw.line(surf, S.BORDER, (210, S.NAV_H), (210, S.HEIGHT))
        for i, name in enumerate(TABS):
            r = pygame.Rect(14, S.NAV_H + 20 + i * 52, 182, 42)
            if ui.button(surf, r, name, kind="primary" if i == self.tab else "ghost",
                         size=15, active=(i == self.tab)):
                self.tab = i
        text(surf, TABS[self.tab], (CX, S.NAV_H + 8), 26, S.TEXT, bold=True)
        [self.overview, self.hr, self.products, self.marketing, self.financials][self.tab](surf)

    # ------------------------------------------------------------ overview
    def overview(self, surf):
        c = self.c
        p = c.preview()
        last = c.last_report
        ref = last or p
        tag = "last month" if last else "projected"
        w, gap = 245, 16

        def xs(i):
            return CX + i * (w + gap)

        profit_color = S.GREEN if ref.profit >= 0 else S.RED
        self.stat_card(surf, pygame.Rect(xs(0), CY + 8, w, 104), "CASH BALANCE", money(c.cash),
                       f"Net worth {money(c.net_worth)}", S.GREEN if c.cash >= 0 else S.RED)
        self.stat_card(surf, pygame.Rect(xs(1), CY + 8, w, 104), "MONTHLY REVENUE", money(ref.revenue),
                       tag, S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(2), CY + 8, w, 104), "MONTHLY EXPENSES", money(ref.expenses),
                       tag, S.PURPLE)
        self.stat_card(surf, pygame.Rect(xs(3), CY + 8, w, 104), "NET PROFIT", signed(ref.profit),
                       tag, profit_color)

        self.stat_card(surf, pygame.Rect(xs(0), CY + 128, w, 104), "EMPLOYEES",
                       f"{len(c.employees)} / {c.office_capacity}", f"Payroll {money(c.monthly_payroll)}/mo", S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(1), CY + 128, w, 104), "CUSTOMERS", f"{c.customers:,}".replace(",", "."),
                       f"Price {money(c.product.price)}/mo", S.BLUE)
        self.stat_card(surf, pygame.Rect(xs(2), CY + 128, w, 104), "REPUTATION", f"{c.reputation:.1f} / 100",
                       f"Product quality {c.product.quality:.0f}", S.PURPLE)
        self.stat_card(surf, pygame.Rect(xs(3), CY + 128, w, 104), "COMPANY VALUATION", money(c.valuation),
                       "Net worth + 6x monthly revenue", S.PURPLE)

        goal = pygame.Rect(CX, CY + 248, CW, 92)
        self.ui.card(surf, goal, f"GOAL: REACH {money(S.GOAL_NET_WORTH)} IN NET WORTH")
        self.ui.bar(surf, (goal.x + 16, goal.y + 40, CW - 32, 18), c.net_worth, S.GOAL_NET_WORTH, S.GREEN)
        pct = max(0, c.net_worth) / S.GOAL_NET_WORTH * 100
        text(surf, f"{money(c.net_worth)}  ({pct:.1f}%)", (goal.x + 16, goal.y + 64), 15, S.TEXT)

        box = pygame.Rect(CX, CY + 356, CW, 228)
        self.ui.card(surf, box, f"PROJECTION FOR {p.label.upper()} (if you end the month now)")
        lx, ly, lw = box.x + 20, box.y + 42, 440
        self.row(surf, lx, ly, lw, "Product revenue", money(p.revenue), S.GREEN)
        self.row(surf, lx, ly + 26, lw, "Salaries", "-" + money(p.salaries).replace("-", ""))
        self.row(surf, lx, ly + 52, lw, "Marketing", "-" + money(p.marketing).replace("-", ""))
        self.row(surf, lx, ly + 78, lw, "Office maintenance", "-" + money(p.office).replace("-", ""))
        self.row(surf, lx, ly + 104, lw, "Other operating costs", "-" + money(p.other).replace("-", ""))
        self.row(surf, lx, ly + 130, lw, "One-time costs this month", "-" + money(p.one_time).replace("-", ""))
        pygame.draw.line(surf, S.BORDER, (lx, ly + 158), (lx + lw, ly + 158))
        self.row(surf, lx, ly + 166, lw, "Projected profit", signed(p.profit),
                 S.GREEN if p.profit >= 0 else S.RED, 18, True)

        rx = box.x + 520
        net_cust = p.customers_end - p.customers_start
        self.row(surf, rx, ly, 480, "Customers", f"{p.customers_start} -> {p.customers_end} ({net_cust:+d})",
                 S.GREEN if net_cust >= 0 else S.RED)
        self.row(surf, rx, ly + 26, 480, "Reputation", f"{p.rep_start:.1f} -> {p.rep_end:.1f}")
        self.row(surf, rx, ly + 52, 480, "Product quality", f"{p.quality_start:.1f} -> {p.quality_end:.1f}")
        self.row(surf, rx, ly + 78, 480, "Development progress", f"{c.product.progress:.0f}% -> {p.progress_end:.0f}%")
        if p.profit < 0:
            runway = c.cash / -p.profit if p.profit else 99
            tip = f"At this pace your cash lasts about {runway:.1f} months."
            col = S.RED if runway < 3 else S.ORANGE
        else:
            tip = "You are profitable. Reinvest in marketing, product and people."
            col = S.GREEN
        for i, line in enumerate(wrap(tip, 15, 480)):
            text(surf, line, (rx, ly + 120 + i * 20), 15, col, bold=True)

    # ------------------------------------------------------------ HR
    def hr(self, surf):
        c, ui = self.c, self.ui
        left = pygame.Rect(CX, CY, 600, 592)
        ui.card(surf, left, "TEAM")
        text(surf, f"{len(c.employees)} / {c.office_capacity} desks", (left.right - 16, left.y + 12), 15,
             S.MUTED, bold=True, anchor="topright")
        hy = left.y + 40
        for label, dx in (("Name", 16), ("Role", 130), ("Salary", 300), ("Productivity", 392)):
            text(surf, label, (left.x + dx, hy), 13, S.MUTED, bold=True)
        pygame.draw.line(surf, S.BORDER, (left.x + 12, hy + 22), (left.right - 12, hy + 22))
        now = pygame.time.get_ticks()
        if self.pending_dismiss and now > self.pending_dismiss[1]:
            self.pending_dismiss = None
        for i, e in enumerate(c.employees):
            ry = hy + 30 + i * 32
            if i % 2 == 0:
                pygame.draw.rect(surf, S.CARD_HI, (left.x + 8, ry - 3, left.w - 16, 30), border_radius=6)
            pygame.draw.rect(surf, e.color, (left.x + 14, ry + 5, 8, 14), border_radius=3)
            text(surf, e.name, (left.x + 30, ry), 15, S.TEXT, bold=True)
            text(surf, e.role.replace("Marketing Specialist", "Marketing"), (left.x + 130, ry), 15, e.color)
            text(surf, money(e.salary), (left.x + 300, ry), 15)
            ui.bar(surf, (left.x + 392, ry + 6, 70, 10), e.productivity, 1.3, S.BLUE)
            text(surf, f"{e.productivity:.2f}", (left.x + 470, ry), 14, S.MUTED)
            confirming = self.pending_dismiss and self.pending_dismiss[0] == e.id
            if ui.button(surf, (left.right - 96, ry - 1, 84, 26), "Sure?" if confirming else "Dismiss",
                         kind="danger", size=13):
                if confirming:
                    self.act(c.dismiss(e.id))
                    self.pending_dismiss = None
                else:
                    self.pending_dismiss = (e.id, now + 2500)
                    ui.toast(f"Click again to dismiss {e.name} (severance {money(e.severance)}).", True)
                break

        right = pygame.Rect(CX + 616, CY, 414, 330)
        ui.card(surf, right, "HIRE EMPLOYEE")
        full = len(c.employees) >= c.office_capacity
        sub = "Office is full - expand it in Office mode." if full else f"{c.office_capacity - len(c.employees)} free desk(s)"
        text(surf, sub, (right.x + 16, right.y + 34), 14, S.ORANGE if full else S.MUTED)
        for i, role in enumerate(S.ROLE_ORDER):
            info = S.ROLES[role]
            r = pygame.Rect(right.x + 16, right.y + 62 + i * 65, 382, 58)
            fee = int(info["salary"] * S.HIRE_FEE_RATE)
            if ui.button(surf, r, "", enabled=not full, kind="ghost"):
                self.act(c.hire(role))
            pygame.draw.rect(surf, info["color"], (r.x, r.y, 8, r.h), border_top_left_radius=8,
                             border_bottom_left_radius=8)
            text(surf, f"Hire {role}", (r.x + 20, r.y + 7), 16, S.WHITE if not full else S.MUTED, bold=True)
            text(surf, f"~{money(info['salary'])}/mo  |  fee ~{money(fee)}", (r.right - 12, r.y + 8), 13,
                 S.MUTED, anchor="topright")
            text(surf, info["desc"][:58], (r.x + 20, r.y + 33), 13, S.MUTED)

        pay = pygame.Rect(CX + 616, CY + 346, 414, 246)
        ui.card(surf, pay, "PAYROLL SUMMARY")
        self.row(surf, pay.x + 16, pay.y + 42, 382, "Monthly payroll", money(c.monthly_payroll), S.PURPLE, 16, True)
        counts = {r: 0 for r in S.ROLES}
        for e in c.employees:
            counts[e.role] += 1
        for i, role in enumerate(S.ROLE_ORDER):
            self.row(surf, pay.x + 16, pay.y + 76 + i * 26, 382, role, str(counts[role]), S.ROLES[role]["color"])
        avg = sum(e.productivity for e in c.employees) / max(1, len(c.employees))
        self.row(surf, pay.x + 16, pay.y + 186, 382, "Average productivity", f"{avg:.2f}")
        text(surf, f"Dismissal costs {int(S.SEVERANCE_RATE * 100)}% of salary.", (pay.x + 16, pay.y + 214), 13, S.MUTED)

    # ------------------------------------------------------------ products
    def products(self, surf):
        c, ui, p = self.c, self.ui, self.c.product
        left = pygame.Rect(CX, CY, 600, 360)
        ui.card(surf, left, "PRODUCT")
        text(surf, p.name, (left.x + 16, left.y + 36), 30, S.TEXT, bold=True)
        text(surf, f"Version {p.version}", (left.right - 16, left.y + 46), 16, S.PURPLE, bold=True, anchor="topright")
        text(surf, f"Development progress to v{p.version + 1}", (left.x + 16, left.y + 88), 14, S.MUTED)
        ui.bar(surf, (left.x + 16, left.y + 110, 568, 16), p.progress, 100, S.BLUE)
        text(surf, f"{p.progress:.0f}%", (left.right - 16, left.y + 88), 14, S.TEXT, anchor="topright")
        text(surf, "Product quality", (left.x + 16, left.y + 144), 14, S.MUTED)
        ui.bar(surf, (left.x + 16, left.y + 166, 568, 16), p.quality, 100, S.GREEN)
        text(surf, f"{p.quality:.1f} / 100", (left.right - 16, left.y + 144), 14, S.TEXT, anchor="topright")
        text(surf, "Selling price (per customer / month)", (left.x + 16, left.y + 206), 14, S.MUTED)
        text(surf, money(p.price), (left.x + 16, left.y + 228), 30, S.TEXT, bold=True)
        for i, (lab, d) in enumerate((("-10", -10), ("-1", -1), ("+1", 1), ("+10", 10))):
            if ui.button(surf, (left.x + 250 + i * 80, left.y + 230, 72, 38), lab, kind="ghost"):
                self.act(c.set_price(p.price + d))
        ref = economy.reference_price(p.quality)
        col = S.GREEN if p.price <= ref else S.ORANGE
        text(surf, f"Fair market price for this quality: {money(ref)}", (left.x + 16, left.y + 284), 15, col)
        text(surf, "Above it: more churn and less reputation. Below it: more customers.",
             (left.x + 16, left.y + 308), 13, S.MUTED)
        text(surf, f"Total invested in development: {money(p.dev_investment)}", (left.x + 16, left.y + 332), 14, S.MUTED)

        right = pygame.Rect(CX + 616, CY, 414, 360)
        ui.card(surf, right, "INVEST IN DEVELOPMENT")
        for i, (cost, pts) in enumerate(S.DEV_INVESTMENTS):
            r = pygame.Rect(right.x + 16, right.y + 44 + i * 86, 382, 74)
            if ui.button(surf, r, "", enabled=c.cash >= cost, kind="primary" if i == 0 else "purple"):
                self.act(c.invest_dev(i))
            text(surf, f"{'Sprint' if i == 0 else 'Major overhaul'}: {money(cost)}", (r.x + 16, r.y + 12),
                 17, S.WHITE if c.cash >= cost else S.MUTED, bold=True)
            text(surf, f"+{pts:.0f} development progress now", (r.x + 16, r.y + 40), 14, S.MUTED)
        qpr = economy.quality_per_release(c)
        for i, line in enumerate(wrap(
                f"Each release adds about +{qpr:.1f} quality. Developers add progress every month and "
                f"designers add release impact and slow polish.", 14, 382)):
            text(surf, line, (right.x + 16, right.y + 226 + i * 20), 14, S.MUTED)

        bot = pygame.Rect(CX, CY + 376, CW, 216)
        ui.card(surf, bot, "MARKET INSIGHT")
        self.row(surf, bot.x + 20, bot.y + 42, 440, "Market appeal", f"{economy.market_appeal(c) * 100:.0f}%", S.BLUE)
        self.row(surf, bot.x + 20, bot.y + 70, 440, "Monthly churn rate", f"{economy.churn_rate(c) * 100:.1f}%",
                 S.RED if economy.churn_rate(c) > 0.07 else S.GREEN)
        self.row(surf, bot.x + 20, bot.y + 98, 440, "Expected organic customers", f"+{economy.organic_customers(c):.1f}")
        self.row(surf, bot.x + 20, bot.y + 126, 440, "Expected referrals", f"+{economy.referral_customers(c):.1f}")
        self.row(surf, bot.x + 20, bot.y + 154, 440, "Market saturation", f"{(1 - economy.saturation(c.customers)) * 100:.0f}%")
        pr = c.preview()
        self.row(surf, bot.x + 540, bot.y + 42, 460, "Customers", str(c.customers))
        self.row(surf, bot.x + 540, bot.y + 70, 460, "Monthly revenue now", money(pr.revenue), S.GREEN)
        self.row(surf, bot.x + 540, bot.y + 98, 460, "Revenue per customer", money(p.price))
        self.row(surf, bot.x + 540, bot.y + 126, 460, "Next release in about",
                 "never" if pr.progress_gain <= 0 else f"{max(1, int((100 - p.progress) / pr.progress_gain + 0.99))} month(s)")

    # ------------------------------------------------------------ marketing
    def marketing(self, surf):
        c, ui = self.c, self.ui
        box = pygame.Rect(CX, CY, CW, 452)
        ui.card(surf, box, "CAMPAIGNS (recurring monthly while active)")
        for i, camp in enumerate(economy.CAMPAIGNS):
            ry = box.y + 42 + i * 100
            active = camp["id"] in c.active_campaigns
            row = pygame.Rect(box.x + 12, ry, box.w - 24, 90)
            pygame.draw.rect(surf, S.CARD_HI, row, border_radius=10)
            if active:
                pygame.draw.rect(surf, S.GREEN, row, 2, border_radius=10)
            text(surf, camp["name"], (row.x + 16, row.y + 10), 18, S.TEXT, bold=True)
            text(surf, camp["desc"], (row.x + 16, row.y + 38), 14, S.MUTED)
            exp = economy.campaign_customers(c, camp)
            text(surf, f"Investment: {money(camp['cost'])}/month", (row.x + 16, row.y + 62), 14, S.PURPLE, bold=True)
            text(surf, f"Expected customers: +{exp:.0f}", (row.x + 480, row.y + 20), 15, S.GREEN, bold=True)
            text(surf, f"Reputation impact: +{camp['rep']:.1f}/month", (row.x + 480, row.y + 50), 15, S.BLUE, bold=True)
            label = "Stop" if active else "Launch"
            if ui.button(surf, (row.right - 140, row.y + 22, 124, 44), label,
                         kind="danger" if active else "success"):
                self.act(c.toggle_campaign(camp["id"]))
        sm = pygame.Rect(CX, CY + 468, CW, 124)
        ui.card(surf, sm, "MARKETING SUMMARY")
        self.row(surf, sm.x + 20, sm.y + 40, 440, "Monthly marketing investment", money(c.marketing_investment), S.PURPLE, 16, True)
        self.row(surf, sm.x + 20, sm.y + 68, 440, "Expected customers from campaigns",
                 f"+{economy.expected_marketing_customers(c):.0f}", S.GREEN)
        self.row(surf, sm.x + 20, sm.y + 94, 440, "Reputation impact", f"+{economy.marketing_reputation(c):.1f}/month", S.BLUE)
        mm = economy.marketing_multiplier(c)
        self.row(surf, sm.x + 540, sm.y + 40, 460, "Team marketing multiplier", f"x{mm:.2f}", S.BLUE)
        self.row(surf, sm.x + 540, sm.y + 68, 460, "Campaign effect (quality & reputation)",
                 f"x{0.5 + economy.market_appeal(c):.2f}")
        text(surf, "Hire Marketing Specialists to boost every campaign.", (sm.x + 540, sm.y + 94), 14, S.MUTED)

    # ------------------------------------------------------------ financials
    def financials(self, surf):
        c, ui = self.c, self.ui
        h = c.history
        last = h[-1] if h else None
        w = 245
        vals = [("REVENUE (LAST MONTH)", money(last.revenue) if last else "-", S.BLUE),
                ("EXPENSES (LAST MONTH)", money(last.expenses) if last else "-", S.PURPLE),
                ("NET PROFIT (LAST MONTH)", signed(last.profit) if last else "-",
                 (S.GREEN if last.profit >= 0 else S.RED) if last else S.MUTED),
                ("CASH BALANCE", money(c.cash), S.GREEN if c.cash >= 0 else S.RED)]
        for i, (t, v, col) in enumerate(vals):
            r = pygame.Rect(CX + i * (w + 16), CY + 8, w, 84)
            ui.card(surf, r, t)
            text(surf, v, (r.x + 16, r.y + 40), 22, col, bold=True)

        perf = pygame.Rect(CX, CY + 104, CW, 56)
        ui.card(surf, perf)
        if not last:
            rating, col, note = "No data yet", S.MUTED, "End your first month to see business performance."
        else:
            if last.profit >= 0:
                rating, col, note = "Healthy", S.GREEN, "Revenue covers all costs."
            else:
                runway = c.cash / -last.profit
                if runway < 3:
                    rating, col = "Critical", S.RED
                else:
                    rating, col = "At risk", S.ORANGE
                note = f"Burning {money(-last.profit)}/month - cash lasts about {runway:.1f} months."
        text(surf, "BUSINESS PERFORMANCE", (perf.x + 16, perf.y + 8), 13, S.MUTED, bold=True)
        text(surf, rating, (perf.x + 16, perf.y + 26), 20, col, bold=True)
        text(surf, note, (perf.x + 260, perf.y + 20), 16, S.TEXT)

        ch = pygame.Rect(CX, CY + 172, CW, 210)
        ui.card(surf, ch, "NET PROFIT PER MONTH (last 12)")
        recent = h[-12:]
        area = pygame.Rect(ch.x + 24, ch.y + 44, ch.w - 48, 140)
        if not recent:
            text(surf, "No history yet.", area.center, 16, S.MUTED, anchor="center")
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
                text(surf, r.label[:3], (bx + bw // 2, area.bottom + 2), 11, S.MUTED, anchor="midtop")

        tb = pygame.Rect(CX, CY + 394, CW, 198)
        ui.card(surf, tb, "MONTHLY REPORTS (latest first)")
        cols = [("Month", 16), ("Revenue", 170), ("Expenses", 340), ("Profit", 510), ("Cash", 680), ("Customers", 860)]
        for lab, dx in cols:
            text(surf, lab, (tb.x + dx, tb.y + 34), 13, S.MUTED, bold=True)
        for i, r in enumerate(reversed(h[-6:])):
            y = tb.y + 56 + i * 22
            text(surf, r.label, (tb.x + 16, y), 14)
            text(surf, money(r.revenue), (tb.x + 170, y), 14, S.BLUE)
            text(surf, money(r.expenses), (tb.x + 340, y), 14, S.PURPLE)
            text(surf, signed(r.profit), (tb.x + 510, y), 14, S.GREEN if r.profit >= 0 else S.RED)
            text(surf, money(r.cash_end), (tb.x + 680, y), 14)
            text(surf, str(r.customers_end), (tb.x + 860, y), 14)
        if not h:
            text(surf, "Nothing yet - click END MONTH.", (tb.x + 16, tb.y + 60), 15, S.MUTED)
