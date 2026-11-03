"""Economic model. Pure calculations: nothing here touches the UI.

calculate_month(company) returns a MonthReport *without* mutating the
company, so the same function powers the real month-end and the
"projected next month" previews shown in the interfaces.
"""
from dataclasses import dataclass

import settings as S
from systems.time_system import month_label

CAMPAIGNS = [
    {"id": "social", "name": "Social Media Push", "cost": 2_000, "per_k": 6.0, "rep": 0.4,
     "desc": "Organic posts and small paid boosts."},
    {"id": "ads", "name": "Online Ads", "cost": 6_000, "per_k": 5.0, "rep": 0.6,
     "desc": "Search and display ads with sharp targeting."},
    {"id": "influencer", "name": "Influencer Partnerships", "cost": 15_000, "per_k": 4.5, "rep": 1.5,
     "desc": "Tech creators review and recommend the product."},
    {"id": "media", "name": "TV & Media Blitz", "cost": 40_000, "per_k": 4.0, "rep": 3.0,
     "desc": "Prime-time spots and press coverage."},
]
CAMPAIGN_BY_ID = {c["id"]: c for c in CAMPAIGNS}


@dataclass
class MonthReport:
    month: int
    label: str
    revenue: int
    salaries: int
    marketing: int
    office: int
    other: int
    one_time: int          # hiring fees, severance, development investments
    expenses: int
    profit: int
    customers_start: int
    organic: int
    referral: int
    from_marketing: int
    churned: int
    customers_end: int
    rep_start: float
    rep_end: float
    progress_gain: float
    progress_end: float
    releases: int
    quality_start: float
    quality_end: float
    version_end: int
    capex: int = 0         # office expansions paid this month (not in P&L)
    cash_end: int = 0
    net_worth: int = 0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ------------------------------------------------------------ staff helpers
def staff_sums(company) -> dict:
    sums = {r: 0.0 for r in S.ROLES}
    for e in company.employees:
        sums[e.role] += e.productivity
    return sums


def manager_multiplier(company) -> float:
    return 1.0 + min(0.30, 0.10 * staff_sums(company)["Manager"])


def marketing_multiplier(company) -> float:
    sums = staff_sums(company)
    return (1.0 + 0.20 * sums["Marketing Specialist"]) * manager_multiplier(company)


def quality_per_release(company) -> float:
    return S.RELEASE_BASE_QUALITY + S.RELEASE_PER_DESIGNER * staff_sums(company)["Designer"]


# ------------------------------------------------------------ market model
def market_appeal(company) -> float:
    return 0.6 * company.product.quality / 100 + 0.4 * company.reputation / 100


def reference_price(quality: float) -> float:
    """Price the market considers fair for a given quality."""
    return 100 + 2 * quality


def price_factor(company) -> float:
    p = company.product
    return clamp(reference_price(p.quality) / p.price, 0.4, 1.5)


def churn_rate(company) -> float:
    p = company.product
    r = S.CHURN_BASE - S.CHURN_QUALITY * p.quality / 100
    ref = reference_price(p.quality)
    if p.price > ref:
        r += min(0.10, (p.price / ref - 1) * 0.25)
    return clamp(r, 0.01, 0.25)


def saturation(customers: int) -> float:
    return max(0.1, 1 - customers / S.MARKET_SIZE)


def organic_customers(company) -> float:
    base = S.ORGANIC_BASE + S.ORGANIC_APPEAL * market_appeal(company)
    return base * price_factor(company) * saturation(company.customers)


def referral_customers(company) -> float:
    return (company.customers * S.REFERRAL_RATE * market_appeal(company)
            * price_factor(company) * saturation(company.customers))


def campaign_customers(company, camp) -> float:
    raw = camp["cost"] / 1000 * camp["per_k"]
    return (raw * (0.5 + market_appeal(company)) * marketing_multiplier(company)
            * saturation(company.customers))


def marketing_budget(company) -> int:
    return sum(CAMPAIGN_BY_ID[c]["cost"] for c in company.active_campaigns)


def expected_marketing_customers(company) -> float:
    return sum(campaign_customers(company, CAMPAIGN_BY_ID[c])
               for c in company.active_campaigns)


def marketing_reputation(company) -> float:
    return sum(CAMPAIGN_BY_ID[c]["rep"] for c in company.active_campaigns)


def office_cost(capacity: int) -> int:
    return S.OFFICE_BASE_COST + S.OFFICE_COST_PER_DESK * capacity


def reputation_change(company) -> float:
    p = company.product
    ref = reference_price(p.quality)
    d = (p.quality - 40) / 40 * 0.8
    d += marketing_reputation(company)
    if p.price > ref:
        d -= min(1.0, (p.price / ref - 1) * 3)
    else:
        d += min(0.3, (1 - p.price / ref) * 0.5)
    if company.reputation > 70:
        d -= 0.15
    return d


# ------------------------------------------------------------ month
def calculate_month(company) -> MonthReport:
    p = company.product
    sums = staff_sums(company)

    revenue = int(round(company.customers * p.price))
    salaries = company.monthly_payroll
    marketing = marketing_budget(company)
    office = office_cost(company.office_capacity)
    other = S.OTHER_BASE + S.OTHER_PER_CUSTOMER * company.customers
    one_time = company.one_time_costs
    expenses = salaries + marketing + office + other + one_time

    organic = int(round(organic_customers(company)))
    referral = int(round(referral_customers(company)))
    from_mkt = int(round(expected_marketing_customers(company)))
    churned = int(round(company.customers * churn_rate(company)))
    customers_end = max(0, company.customers + organic + referral + from_mkt - churned)

    rep_end = clamp(company.reputation + reputation_change(company), 0, 100)

    gain = sums["Developer"] * S.DEV_PROGRESS_PER_DEV * manager_multiplier(company)
    total = p.progress + gain
    releases = int(total // 100)
    progress_end = total - releases * 100
    polish = S.DESIGN_POLISH * sums["Designer"]
    quality_end = min(100.0, p.quality + releases * quality_per_release(company) + polish)

    return MonthReport(
        month=company.time.month, label=company.time.label,
        revenue=revenue, salaries=salaries, marketing=marketing, office=office,
        other=other, one_time=one_time, expenses=expenses, profit=revenue - expenses,
        customers_start=company.customers, organic=organic, referral=referral,
        from_marketing=from_mkt, churned=churned, customers_end=customers_end,
        rep_start=company.reputation, rep_end=rep_end,
        progress_gain=gain, progress_end=progress_end, releases=releases,
        quality_start=p.quality, quality_end=quality_end,
        version_end=p.version + releases, capex=company.capex_this_month,
    )
