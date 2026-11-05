"""Tiny immediate-mode UI toolkit shared by every screen."""
import os

import pygame

import settings as S
from systems.localization import tr
from systems.paths import resource_path

_fonts = {}
FONT_FILES = {False: "DejaVuSansCondensed.ttf", True: "DejaVuSansCondensed-Bold.ttf"}

# Test hook: when set, called as hook(kind, rect, label) for every text / button drawn.
LAYOUT_HOOK = None
ELLIPSIS = "\u2026"


def font(size, bold=False):
    """Bundled DejaVu Sans Condensed: covers accents, cedilla, sharp s, euro sign, etc., and
    looks the same on Windows, Linux and in the browser (no dependency on installed fonts)."""
    key = (size, bold)
    if key not in _fonts:
        path = resource_path("assets", "fonts", FONT_FILES[bold])
        if os.path.exists(path):
            _fonts[key] = pygame.font.Font(path, size)
        else:                                   # keeps the game running if the file is missing
            _fonts[key] = pygame.font.SysFont("dejavusans,arial,helvetica", size, bold=bold)
    return _fonts[key]


_width_cache = {}


def text_width(s, size=16, bold=False):
    key = (s, size, bold)
    w = _width_cache.get(key)
    if w is None:
        if len(_width_cache) >= 6000:
            _width_cache.clear()
        w = _width_cache[key] = font(size, bold).size(str(s))[0]
    return w


def fit_text(s, size, max_w, bold=False, min_size=None):
    """Return ``(text, size)`` that fits ``max_w``: first shrink the font a little, then cut
    with an ellipsis. Never changes the meaning of short strings."""
    s = str(s)
    if max_w is None or text_width(s, size, bold) <= max_w:
        return s, size
    floor = max(9, size - 3) if min_size is None else min_size
    for sz in range(size - 1, floor - 1, -1):
        if text_width(s, sz, bold) <= max_w:
            return s, sz
    sz = floor
    while s and text_width(s + ELLIPSIS, sz, bold) > max_w:
        s = s[:-1]
    return s.rstrip() + ELLIPSIS, sz


_text_cache = {}
_TEXT_CACHE_MAX = 1500


def render_text(s, size, color, bold=False):
    """Rendered text surface, cached: rendering glyphs every frame is the main CPU cost of an
    immediate-mode UI, especially on phones and in the browser."""
    key = (s, size, bold, tuple(color))
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) >= _TEXT_CACHE_MAX:
            _text_cache.clear()
        img = _text_cache[key] = font(size, bold).render(s, True, color)
    return img


def text(surf, s, pos, size=16, color=S.TEXT, bold=False, anchor="topleft", max_w=None, min_size=None):
    """Draw text. With ``max_w`` the text is shrunk / ellipsized to fit that width."""
    s, size = fit_text(s, size, max_w, bold, min_size)
    img = render_text(s, size, color, bold)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    if LAYOUT_HOOK and s:
        LAYOUT_HOOK("text", rect, s)
    return rect


def wrap(s, size, width, bold=False, max_lines=None):
    """Greedy word wrap. With ``max_lines`` the last line is ellipsized instead of overflowing."""
    f = font(size, bold)
    lines, line = [], ""
    for word in str(s).split():
        trial = f"{line} {word}".strip()
        if f.size(trial)[0] <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        rest = " ".join(lines[max_lines - 1:])
        lines = lines[:max_lines - 1] + [fit_text(rest, size, width, bold, min_size=size)[0]]
    return lines


def row(surf, x, y, w, label, value, color=S.TEXT, size=16, bold=False, label_color=S.MUTED):
    """Label on the left, value right-aligned at ``x + w``. The label shrinks / ellipsizes so a
    long translation never runs into the value."""
    value = str(value)
    vw = text_width(value, size, bold)
    text(surf, label, (x, y), size, label_color, max_w=max(20, w - vw - 14))
    text(surf, value, (x + w, y), size, color, bold=bold, anchor="topright")


def draw_flag(surf, rect, code):
    """Small simplified flag (DejaVu has no emoji flags, and emoji would break on other fonts)."""
    r = pygame.Rect(rect)
    x, y, w, h = r.x, r.y, r.w, r.h
    if code == "BR":
        pygame.draw.rect(surf, (0, 156, 59), r)
        pygame.draw.polygon(surf, (255, 223, 0), [(x + w // 2, y + 3), (x + w - 4, y + h // 2),
                                                 (x + w // 2, y + h - 3), (x + 4, y + h // 2)])
        pygame.draw.circle(surf, (0, 39, 118), (x + w // 2, y + h // 2), max(3, h // 4))
    elif code == "US":
        stripe = h / 7
        for i in range(7):
            col = (191, 10, 48) if i % 2 == 0 else (255, 255, 255)
            pygame.draw.rect(surf, col, (x, int(y + i * stripe), w, int(stripe) + 1))
        pygame.draw.rect(surf, (10, 49, 97), (x, y, int(w * 0.45), int(stripe * 4)))
        for i in range(3):
            for j in range(2):
                pygame.draw.rect(surf, (255, 255, 255), (x + 3 + i * 5, y + 3 + j * 5, 2, 2))
    elif code == "ES":
        pygame.draw.rect(surf, (170, 21, 27), r)
        pygame.draw.rect(surf, (241, 191, 0), (x, y + h // 4, w, h // 2))
    elif code == "FR":
        for i, col in enumerate(((0, 85, 164), (255, 255, 255), (239, 65, 53))):
            pygame.draw.rect(surf, col, (x + i * w // 3, y, w // 3 + 1, h))
    elif code == "DE":
        for i, col in enumerate(((0, 0, 0), (221, 0, 0), (255, 206, 0))):
            pygame.draw.rect(surf, col, (x, y + i * h // 3, w, h // 3 + 1))
    else:
        pygame.draw.rect(surf, S.CARD_HI, r)
    pygame.draw.rect(surf, (10, 12, 20), r, 1)


def lighten(c, amt=22):
    return tuple(min(255, v + amt) for v in c)


def darken(c, amt=30):
    return tuple(max(0, v - amt) for v in c)


BUTTON_KINDS = {
    "primary": S.BLUE,
    "success": (36, 160, 92),
    "danger": (200, 62, 52),
    "ghost": (44, 51, 76),
    "purple": (120, 85, 205),
}


class UI:
    def __init__(self):
        self.mouse = (0, 0)
        self.clicked = False
        self.locked = False
        self.toasts = []  # [text, ok, time_left]
        self.sfx = lambda name: None      # the game plugs its sound player in here

    def begin(self, clicked, pos=None):
        """``pos``: where the click/tap happened (touch screens do not move a cursor first)."""
        self.mouse = pos if pos is not None else pygame.mouse.get_pos()
        self.clicked = clicked

    def hover(self, rect):
        return (not self.locked) and rect.collidepoint(self.mouse)

    def button(self, surf, rect, label, enabled=True, kind="primary", size=16, active=False):
        rect = pygame.Rect(rect)
        base = BUTTON_KINDS.get(kind, S.BLUE)
        hovered = self.hover(rect)
        if not enabled:
            col, tcol = (38, 43, 62), (100, 108, 130)
        else:
            col = lighten(base, 28) if hovered else base
            if active:
                col = lighten(base, 14)
            tcol = S.WHITE
        pygame.draw.rect(surf, col, rect, border_radius=8)
        if active and enabled:
            pygame.draw.rect(surf, S.WHITE, rect, 2, border_radius=8)
        text(surf, label, rect.center, size, tcol, bold=True, anchor="center", max_w=rect.w - 16)
        if LAYOUT_HOOK:
            LAYOUT_HOOK("button", rect, label)
        if hovered and enabled and self.clicked:
            self.clicked = False
            self.sfx("click")
            return True
        if hovered and not enabled and self.clicked:
            self.clicked = False  # swallow clicks on disabled buttons
            self.sfx("error")
        return False

    def card(self, surf, rect, title=None, color=S.CARD):
        rect = pygame.Rect(rect)
        pygame.draw.rect(surf, color, rect, border_radius=12)
        pygame.draw.rect(surf, S.BORDER, rect, 1, border_radius=12)
        if title:
            text(surf, title, (rect.x + 16, rect.y + 12), 15, S.MUTED, bold=True, max_w=rect.w - 32)
        return rect

    def bar(self, surf, rect, value, maxv=100, color=S.BLUE):
        rect = pygame.Rect(rect)
        pygame.draw.rect(surf, (20, 24, 38), rect, border_radius=6)
        frac = 0 if maxv <= 0 else max(0.0, min(1.0, value / maxv))
        if frac > 0:
            fill = pygame.Rect(rect.x, rect.y, max(6, int(rect.w * frac)), rect.h)
            pygame.draw.rect(surf, color, fill, border_radius=6)

    def slider(self, surf, rect, value, maxv=100, color=S.BLUE, step=10):
        """Click/tap bar. Returns the new value (rounded to ``step``) when the player picks one."""
        rect = pygame.Rect(rect)
        self.bar(surf, rect, value, maxv, color)
        frac = 0 if maxv <= 0 else max(0.0, min(1.0, value / maxv))
        pygame.draw.circle(surf, S.WHITE, (rect.x + int(rect.w * frac), rect.centery), rect.h // 2 + 3)
        if self.hover(rect.inflate(16, 24)) and self.clicked:
            self.clicked = False
            f = max(0.0, min(1.0, (self.mouse[0] - rect.x) / max(1, rect.w)))
            return int(round(f * maxv / step) * step)
        return None

    def toast(self, msg, ok=True):
        """``msg`` may be a ``Msg`` (translated every frame, so a language change applies at once)
        or a plain string."""
        self.toasts.append([msg, ok, 3.2])
        self.toasts = self.toasts[-3:]
        if not ok:
            self.sfx("error")

    def draw_toasts(self, surf, dt):
        y = S.HEIGHT - 20
        for t in reversed(self.toasts):
            t[2] -= dt
            label, sz = fit_text(tr(t[0]), 16, S.WIDTH - 80, True)
            img = font(sz, True).render(label, True, S.WHITE)
            w, h = img.get_size()
            r = pygame.Rect(0, 0, w + 32, h + 18)
            r.midbottom = (S.WIDTH // 2, y)
            col = (30, 120, 75) if t[1] else (160, 50, 44)
            pygame.draw.rect(surf, col, r, border_radius=10)
            pygame.draw.rect(surf, lighten(col, 40), r, 1, border_radius=10)
            surf.blit(img, (r.x + 16, r.y + 9))
            if LAYOUT_HOOK:
                LAYOUT_HOOK("text", pygame.Rect(r.x + 16, r.y + 9, w, h), label)
            y = r.y - 8
        self.toasts = [t for t in self.toasts if t[2] > 0]
