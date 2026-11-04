"""Monthly calendar used by the simulation (language-independent).

The simulation only stores an integer month counter. Turning it into text ("Jan 2026" /
"jan. 2026" ...) is the job of ``systems.localization``.
"""

START_YEAR = 2026


def month_parts(month: int):
    """1-based month counter -> (year, month_of_year 1..12)."""
    idx = month - 1
    return START_YEAR + idx // 12, idx % 12 + 1


def month_label(month: int) -> str:
    """Localized label for a month counter, e.g. 1 -> 'Jan 2026'."""
    from systems.localization import L          # lazy: localization imports month_parts from here
    return L.month_label(month)


class TimeSystem:
    def __init__(self):
        self.month = 1

    def advance(self):
        self.month += 1

    @property
    def label(self) -> str:
        return month_label(self.month)
