"""Balance check: runs bot strategies against the economy (no window needed).

    python tests/simulate.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.company import Company  # noqa: E402
from systems.localization import money  # noqa: E402


def idle_bot(c, month):
    pass


def growth_bot(c, month):
    """A reasonable player: marketing, steady hiring, development, price tuning."""
    runway_ok = c.cash > 40_000
    if "social" not in c.active_campaigns and c.cash > 20_000:
        c.toggle_campaign("social")
    if "ads" not in c.active_campaigns and c.cash > 40_000:
        c.toggle_campaign("ads")
    if c.customers > 150 and "influencer" not in c.active_campaigns and c.cash > 60_000:
        c.toggle_campaign("influencer")
    roles = ["Marketing Specialist", "Developer", "Designer", "Manager"]
    if runway_ok and c.preview().profit > -5_000 and month % 3 == 0:
        if len(c.employees) >= c.office_capacity and c.next_office_cost and c.cash > c.next_office_cost + 40_000:
            c.expand_office()
        c.hire(roles[(len(c.employees) // 2) % 4])
    if c.cash > 50_000 and month % 4 == 0:
        c.invest_dev(0)
    # price follows the fair reference price
    from core import economy
    c.set_price(int(economy.reference_price(c.product.quality) * 1.0))


def run(bot, label, months=120):
    c = Company(seed=1)
    for m in range(1, months + 1):
        bot(c, m)
        c.end_month()
        if c.status != "running":
            break
    print(f"{label:12s} -> {c.status:9s} month {c.month - 1:3d} | cash {money(c.cash):>14s} | "
          f"net worth {money(c.net_worth):>14s} | customers {c.customers:5d} | "
          f"staff {len(c.employees):2d} | quality {c.product.quality:5.1f} | rep {c.reputation:5.1f}")
    return c


if __name__ == "__main__":
    run(idle_bot, "idle")
    run(growth_bot, "growth")
