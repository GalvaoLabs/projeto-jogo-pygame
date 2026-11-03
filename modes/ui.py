"""Tiny immediate-mode UI toolkit shared by every screen."""
import pygame

import settings as S

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("segoeui,arial,helvetica,dejavusans", size, bold=bold)
    return _fonts[key]


def text(surf, s, pos, size=16, color=S.TEXT, bold=False, anchor="topleft"):
    img = font(size, bold).render(str(s), True, color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def wrap(s, size, width, bold=False):
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
    return lines


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

    def begin(self, clicked):
        self.mouse = pygame.mouse.get_pos()
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
        text(surf, label, rect.center, size, tcol, bold=True, anchor="center")
        if hovered and enabled and self.clicked:
            self.clicked = False
            return True
        if hovered and not enabled and self.clicked:
            self.clicked = False  # swallow clicks on disabled buttons
        return False

    def card(self, surf, rect, title=None, color=S.CARD):
        rect = pygame.Rect(rect)
        pygame.draw.rect(surf, color, rect, border_radius=12)
        pygame.draw.rect(surf, S.BORDER, rect, 1, border_radius=12)
        if title:
            text(surf, title, (rect.x + 16, rect.y + 12), 15, S.MUTED, bold=True)
        return rect

    def bar(self, surf, rect, value, maxv=100, color=S.BLUE):
        rect = pygame.Rect(rect)
        pygame.draw.rect(surf, (20, 24, 38), rect, border_radius=6)
        frac = 0 if maxv <= 0 else max(0.0, min(1.0, value / maxv))
        if frac > 0:
            fill = pygame.Rect(rect.x, rect.y, max(6, int(rect.w * frac)), rect.h)
            pygame.draw.rect(surf, color, fill, border_radius=6)

    def toast(self, msg, ok=True):
        self.toasts.append([msg, ok, 3.2])
        self.toasts = self.toasts[-3:]

    def draw_toasts(self, surf, dt):
        y = S.HEIGHT - 20
        for t in reversed(self.toasts):
            t[2] -= dt
            img = font(16, True).render(t[0], True, S.WHITE)
            w, h = img.get_size()
            r = pygame.Rect(0, 0, w + 32, h + 18)
            r.midbottom = (S.WIDTH // 2, y)
            col = (30, 120, 75) if t[1] else (160, 50, 44)
            pygame.draw.rect(surf, col, r, border_radius=10)
            pygame.draw.rect(surf, lighten(col, 40), r, 1, border_radius=10)
            surf.blit(img, (r.x + 16, r.y + 9))
            y = r.y - 8
        self.toasts = [t for t in self.toasts if t[2] > 0]
