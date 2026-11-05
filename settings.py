"""Global constants: window, colors, starting conditions and balance numbers."""

# ---------------------------------------------------------------- window
WIDTH, HEIGHT = 1280, 720
FPS = 60
VERSION = "1.1.0"
TITLE = "Startup Tycoon"            # brand only; the localized window title is app.window_title
NAV_H = 56

# ---------------------------------------------------------------- colors
BG = (15, 18, 28)
NAV = (18, 21, 34)
SIDEBAR = (20, 24, 38)
CARD = (30, 35, 52)
CARD_HI = (42, 49, 74)
BORDER = (54, 62, 90)
TEXT = (232, 236, 245)
MUTED = (140, 150, 175)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (77, 140, 255)
PURPLE = (155, 110, 240)
YELLOW = (241, 196, 15)
ORANGE = (243, 156, 18)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- start
START_CASH = 100_000
START_EMPLOYEES = 2
START_REPUTATION = 10.0
START_CUSTOMERS = 10
START_PRICE = 129
START_QUALITY = 30.0
PRODUCT_NAME = "TaskFlow"
GOAL_NET_WORTH = 1_000_000

# ---------------------------------------------------------------- roles
ROLES = {
    "Developer": {
        "salary": 5500,
        "color": (66, 135, 245),
    },
    "Designer": {
        "salary": 4500,
        "color": (170, 110, 235),
    },
    "Marketing Specialist": {
        "salary": 4800,
        "color": (240, 150, 50),
    },
    "Manager": {
        "salary": 8000,
        "color": (60, 190, 120),
    },
}
ROLE_ORDER = ["Developer", "Designer", "Marketing Specialist", "Manager"]
HIRE_FEE_RATE = 0.5       # one-time recruitment fee = 50% of monthly salary
SEVERANCE_RATE = 0.25     # severance = 25% of monthly salary

# ---------------------------------------------------------------- office
# cols x rows desks, room size in 16px tiles, cost to reach this level
OFFICE_LEVELS = [
    {"cols": 2, "rows": 2, "w": 18, "h": 12, "capacity": 4, "cost": 0},
    {"cols": 4, "rows": 2, "w": 28, "h": 12, "capacity": 8, "cost": 20_000},
    {"cols": 4, "rows": 3, "w": 28, "h": 16, "capacity": 12, "cost": 45_000},
    {"cols": 4, "rows": 4, "w": 28, "h": 20, "capacity": 16, "cost": 80_000},
]
OFFICE_BASE_COST = 1000
OFFICE_COST_PER_DESK = 400

# ---------------------------------------------------------------- economy
OTHER_BASE = 800
OTHER_PER_CUSTOMER = 14
MARKET_SIZE = 3000
ORGANIC_BASE = 1.5
ORGANIC_APPEAL = 8.0
REFERRAL_RATE = 0.012
CHURN_BASE = 0.09
CHURN_QUALITY = 0.06
DEV_PROGRESS_PER_DEV = 4.0
DESIGN_POLISH = 0.4
RELEASE_BASE_QUALITY = 6.0
RELEASE_PER_DESIGNER = 3.0
PRICE_MIN, PRICE_MAX = 20, 500
DEV_INVESTMENTS = [(5_000, 8.0), (15_000, 28.0)]   # (cost, progress points)
ASSET_RATE = 0.5          # office/product investments count 50% in net worth
VALUATION_REVENUE_MULT = 6
