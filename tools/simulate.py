"""Balance check: plays many games with simple bot strategies (no UI, no pygame).

    python tools/simulate.py            # summary table
"""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings as S                    # noqa: E402
from core import economy                # noqa: E402
from core.company import Company        # noqa: E402

MAX_MONTHS = 240


def fair_price(c):
    return int(economy.reference_price(c.product.quality) * 0.95)


def idle(c):
    pass


def passive_price(c):
    c.set_price(fair_price(c))


def campaigns_first(*ids, hire_marketing=False):
    """Fair price + run the given campaigns as soon as there is a cash cushion for them."""
    def strategy(c):
        c.set_price(fair_price(c))
        for k in ids:
            if k not in c.active_campaigns and c.cash > economy.CAMPAIGN_BY_ID[k]["cost"] * 4:
                c.toggle_campaign(k)
        if hire_marketing and not any(e.role == "Marketing Specialist" for e in c.employees) and c.cash > 30_000:
            c.hire("Marketing Specialist")
        if c.cash > 60_000:
            c.invest_dev(0)
    return strategy


def overstaffed(c):
    """Common beginner mistake: hire everyone, never market."""
    c.set_price(fair_price(c))
    for role in ("Developer", "Designer", "Manager", "Developer"):
        if len(c.employees) < c.office_capacity and c.cash > 20_000:
            c.hire(role)


STRATEGIES = {
    "idle": idle,
    "fair price only": passive_price,
    "overstaffed": overstaffed,
    "social only": campaigns_first("social"),
    "social + ads": campaigns_first("social", "ads"),
    "all campaigns": campaigns_first("social", "ads", "influencer", "media", hire_marketing=True),
}


def play(strategy, seed):
    c = Company(seed=seed)
    for _ in range(MAX_MONTHS):
        strategy(c)
        c.end_month()
        if c.status != "running":
            break
    return c


def main():
    print(f"{'strategy':<18}{'win%':>6}{'bankrupt%':>11}{'unfinished%':>13}{'median months':>15}")
    for name, strat in STRATEGIES.items():
        res = [play(strat, seed) for seed in range(200)]
        win = sum(r.status == "victory" for r in res)
        bust = sum(r.status == "bankrupt" for r in res)
        left = len(res) - win - bust
        med = statistics.median(r.month - 1 for r in res)
        print(f"{name:<18}{win / 2:>6.0f}{bust / 2:>11.0f}{left / 2:>13.0f}{med:>15.0f}")


if __name__ == "__main__":
    main()
