"""Central company state. Every economic action goes through this class."""
import random
from dataclasses import asdict, fields

import settings as S
from core import economy
from core.economy import MonthReport
from core.employee import Employee, NAMES
from core.product import Product
from systems.localization import Msg
from systems.time_system import TimeSystem

SAVE_VERSION = 1

# Actions return ``(ok, Msg)``: a translation key plus raw numeric parameters. The UI translates
# and formats them at display time, so the economy never builds text and a language change
# also re-translates messages that are still on screen.


class Company:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.time = TimeSystem()
        self.cash = S.START_CASH
        self.total_revenue = 0
        self.total_expenses = 0
        self.net_profit = 0              # cumulative profit
        self.customers = S.START_CUSTOMERS
        self.reputation = S.START_REPUTATION
        self.product = Product()
        self.employees = []
        self._next_id = 1
        self.active_campaigns = set()   # recurring monthly campaigns
        self.office_level = 0
        self.expansion_spent = 0
        self.one_time_costs = 0         # paid this month, reported at month end
        self.capex_this_month = 0
        self.history = []
        self.last_report = None
        self.status = "running"         # running | victory | bankrupt
        for role in ("Developer", "Designer"):
            self._create_employee(role, productivity=1.0)

    # ------------------------------------------------------------ properties
    @property
    def month(self) -> int:
        return self.time.month

    @property
    def office_capacity(self) -> int:
        return S.OFFICE_LEVELS[self.office_level]["capacity"]

    @property
    def monthly_payroll(self) -> int:
        return sum(e.salary for e in self.employees)

    @property
    def marketing_investment(self) -> int:
        return economy.marketing_budget(self)

    @property
    def office_asset_value(self) -> int:
        return int(self.expansion_spent * S.ASSET_RATE)

    @property
    def product_asset_value(self) -> int:
        return int(self.product.dev_investment * S.ASSET_RATE)

    @property
    def net_worth(self) -> int:
        return int(self.cash + self.office_asset_value + self.product_asset_value)

    @property
    def valuation(self) -> int:
        last = self.last_report.revenue if self.last_report else int(self.customers * self.product.price)
        return self.net_worth + S.VALUATION_REVENUE_MULT * last

    @property
    def next_office_cost(self):
        if self.office_level + 1 >= len(S.OFFICE_LEVELS):
            return None
        return S.OFFICE_LEVELS[self.office_level + 1]["cost"]

    def preview(self):
        return economy.calculate_month(self)

    # ------------------------------------------------------------ employees
    def _roll_employee(self, role, productivity=None):
        """Build (but do not add) a new employee; the id is only consumed by ``_add_employee``."""
        used = {e.name for e in self.employees}
        free = [n for n in NAMES if n not in used] or NAMES
        name = self.rng.choice(free) if self.employees else free[0]
        if productivity is None:
            productivity = round(self.rng.uniform(0.8, 1.25), 2)
        salary = int(round(S.ROLES[role]["salary"] * productivity / 100.0)) * 100
        return Employee(self._next_id, name, role, salary, productivity, self.month)

    def _add_employee(self, emp):
        self._next_id += 1
        self.employees.append(emp)
        return emp

    def _create_employee(self, role, productivity=None):
        return self._add_employee(self._roll_employee(role, productivity))

    def hire(self, role):
        if role not in S.ROLES:
            return False, Msg("msg.unknown_role")
        if len(self.employees) >= self.office_capacity:
            return False, Msg("msg.office_full")
        emp = self._roll_employee(role)
        if self.cash < emp.fee:
            return False, Msg("msg.hire_no_cash", {"fee": emp.fee})
        self._add_employee(emp)
        self.cash -= emp.fee
        self.one_time_costs += emp.fee
        return True, Msg("msg.hired", {"name": emp.name, "role": role, "salary": emp.salary, "fee": emp.fee})

    def dismiss(self, emp_id):
        emp = next((e for e in self.employees if e.id == emp_id), None)
        if emp is None:
            return False, Msg("msg.emp_not_found")
        if len(self.employees) <= 1:
            return False, Msg("msg.keep_one")
        if self.cash < emp.severance:
            return False, Msg("msg.sev_no_cash", {"sev": emp.severance})
        self.cash -= emp.severance
        self.one_time_costs += emp.severance
        self.employees.remove(emp)
        return True, Msg("msg.dismissed", {"name": emp.name, "sev": emp.severance})

    # ------------------------------------------------------------ office
    def expand_office(self):
        cost = self.next_office_cost
        if cost is None:
            return False, Msg("msg.office_max")
        if self.cash < cost:
            return False, Msg("msg.expand_no_cash", {"cost": cost})
        self.cash -= cost
        self.capex_this_month += cost
        self.expansion_spent += cost
        self.office_level += 1
        return True, Msg("msg.expanded", {"cap": self.office_capacity})

    # ------------------------------------------------------------ product
    def set_price(self, price):
        self.product.price = int(economy.clamp(price, S.PRICE_MIN, S.PRICE_MAX))
        return True, Msg("msg.price_set", {"price": self.product.price})

    def invest_dev(self, tier):
        cost, points = S.DEV_INVESTMENTS[tier]
        if self.cash < cost:
            return False, Msg("msg.dev_no_cash", {"cost": cost})
        self.cash -= cost
        self.one_time_costs += cost
        self.product.dev_investment += cost
        releases = self.product.add_progress(points, economy.quality_per_release(self))
        if releases:
            return True, Msg("msg.invested_release", {"cost": cost, "pts": points, "version": self.product.version})
        return True, Msg("msg.invested", {"cost": cost, "pts": points})

    # ------------------------------------------------------------ marketing
    def toggle_campaign(self, camp_id):
        camp = economy.CAMPAIGN_BY_ID.get(camp_id)
        if camp is None:
            return False, Msg("msg.unknown_campaign")
        if camp_id in self.active_campaigns:
            self.active_campaigns.discard(camp_id)
            return True, Msg("msg.campaign_stopped", {"camp": camp_id})
        if self.cash < self.marketing_investment + camp["cost"]:
            return False, Msg("msg.campaign_no_cash")
        self.active_campaigns.add(camp_id)
        return True, Msg("msg.campaign_launched", {"camp": camp_id, "cost": camp["cost"]})

    # ------------------------------------------------------------ month
    def end_month(self):
        """Run the monthly simulation. Returns the MonthReport (or None)."""
        if self.status != "running":
            return None
        r = economy.calculate_month(self)
        recurring = r.salaries + r.marketing + r.office + r.other
        self.cash += r.revenue - recurring   # one-time costs were paid already
        self.total_revenue += r.revenue
        self.total_expenses += r.expenses
        self.net_profit += r.profit
        self.customers = r.customers_end
        self.reputation = r.rep_end
        self.product.progress = r.progress_end
        self.product.quality = r.quality_end
        self.product.version = r.version_end
        self.one_time_costs = 0
        self.capex_this_month = 0
        self.time.advance()
        r.cash_end = int(self.cash)
        r.net_worth = self.net_worth
        self.history.append(r)
        self.last_report = r
        if self.cash < 0:
            self.status = "bankrupt"
        elif self.net_worth >= S.GOAL_NET_WORTH:
            self.status = "victory"
        return r

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        """JSON-friendly snapshot of the whole run (see ``from_dict``)."""
        version, internal, gauss = self.rng.getstate()
        return {
            "version": SAVE_VERSION,
            "rng": [version, list(internal), gauss],
            "month": self.time.month,
            "cash": self.cash,
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "net_profit": self.net_profit,
            "customers": self.customers,
            "reputation": self.reputation,
            "product": asdict(self.product),
            "employees": [asdict(e) for e in self.employees],
            "next_id": self._next_id,
            "campaigns": sorted(self.active_campaigns),
            "office_level": self.office_level,
            "expansion_spent": self.expansion_spent,
            "one_time_costs": self.one_time_costs,
            "capex_this_month": self.capex_this_month,
            "history": [asdict(r) for r in self.history],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Company":
        """Rebuild a company from ``to_dict`` output. Raises ValueError/TypeError/KeyError on
        data that cannot be trusted; callers discard such a save instead of crashing."""
        if not isinstance(d, dict) or d.get("version") != SAVE_VERSION:
            raise ValueError("unsupported save version")

        def num(key, lo, hi, as_int=True, src=d):
            v = src[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(f"{key} is not a number")
            v = max(lo, min(hi, v))
            return int(v) if as_int else float(v)

        c = cls()
        try:
            st = d["rng"]
            c.rng.setstate((int(st[0]), tuple(int(x) for x in st[1]), st[2]))
        except (KeyError, TypeError, ValueError, IndexError):
            pass                                  # the run is still valid, only the dice differ
        c.time.month = num("month", 1, 100_000)
        c.cash = num("cash", -10**12, 10**12)
        c.total_revenue = num("total_revenue", 0, 10**13)
        c.total_expenses = num("total_expenses", 0, 10**13)
        c.net_profit = num("net_profit", -10**13, 10**13)
        c.customers = num("customers", 0, 10**7)
        c.reputation = num("reputation", 0, 100, as_int=False)

        p = d["product"]
        c.product.version = num("version", 1, 100_000, src=p)
        c.product.progress = num("progress", 0, 99.999, as_int=False, src=p)
        c.product.quality = num("quality", 0, 100, as_int=False, src=p)
        c.product.price = num("price", S.PRICE_MIN, S.PRICE_MAX, src=p)
        c.product.dev_investment = num("dev_investment", 0, 10**12, src=p)

        c.employees = []
        for e in d["employees"]:
            role = e["role"]
            if role not in S.ROLES:
                raise ValueError(f"unknown role {role!r}")
            c.employees.append(Employee(
                id=num("id", 1, 10**9, src=e), name=str(e["name"])[:24], role=role,
                salary=num("salary", 0, 10**7, src=e), productivity=num("productivity", 0.1, 3.0, as_int=False, src=e),
                hired_month=num("hired_month", 1, 100_000, src=e)))
        if not c.employees:
            raise ValueError("a company needs at least one employee")
        c._next_id = max(num("next_id", 1, 10**9), max(e.id for e in c.employees) + 1)

        c.active_campaigns = {k for k in d["campaigns"] if k in economy.CAMPAIGN_BY_ID}
        c.office_level = num("office_level", 0, len(S.OFFICE_LEVELS) - 1)
        c.expansion_spent = num("expansion_spent", 0, 10**12)
        c.one_time_costs = num("one_time_costs", 0, 10**12)
        c.capex_this_month = num("capex_this_month", 0, 10**12)

        known = {f.name for f in fields(MonthReport)}
        c.history = [MonthReport(**{k: v for k, v in r.items() if k in known}) for r in d["history"]]
        c.last_report = c.history[-1] if c.history else None
        status = d.get("status", "running")
        c.status = status if status in ("running", "victory", "bankrupt") else "running"
        return c
