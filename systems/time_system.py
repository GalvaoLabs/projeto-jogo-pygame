"""Monthly calendar used by the simulation."""

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
START_YEAR = 2026


def month_label(month: int) -> str:
    """Label for a 1-based month counter, e.g. 1 -> 'Jan 2026'."""
    idx = month - 1
    return f"{MONTH_NAMES[idx % 12]} {START_YEAR + idx // 12}"


class TimeSystem:
    def __init__(self):
        self.month = 1

    def advance(self):
        self.month += 1

    @property
    def label(self) -> str:
        return month_label(self.month)
