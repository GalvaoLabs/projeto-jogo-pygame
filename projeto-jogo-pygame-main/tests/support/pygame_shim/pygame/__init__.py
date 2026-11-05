"""DEV-ONLY pygame stand-in backed by Pillow.

It exists so the game code can be *executed* (and text measured with the real
DejaVu fonts) on machines where pygame cannot be installed. It is NOT pygame:
it only implements the small API surface Startup Tycoon uses, and renders
approximately. Never ship it, and never treat a pass here as a pygame pass.
"""
import os
import time as _time

from PIL import Image, ImageDraw, ImageFont

IS_SHIM = True
SRCALPHA, FULLSCREEN, SCALED = 0x10000, 0x80000000, 0x200
QUIT, KEYDOWN, MOUSEBUTTONDOWN = 256, 768, 1025
K_RETURN, K_SPACE, K_ESCAPE, K_TAB = 13, 32, 27, 9


class Rect:
    def __init__(self, *a):
        if len(a) == 1:
            a = tuple(a[0])
        if len(a) == 2:
            a = (a[0][0], a[0][1], a[1][0], a[1][1])
        self.x, self.y, self.w, self.h = (int(v) for v in a)

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))

    def __repr__(self):
        return f"Rect({self.x}, {self.y}, {self.w}, {self.h})"

    left = property(lambda s: s.x)
    top = property(lambda s: s.y)
    width = property(lambda s: s.w)
    height = property(lambda s: s.h)
    right = property(lambda s: s.x + s.w)
    bottom = property(lambda s: s.y + s.h)
    centerx = property(lambda s: s.x + s.w // 2)
    centery = property(lambda s: s.y + s.h // 2)
    center = property(lambda s: (s.x + s.w // 2, s.y + s.h // 2))
    midtop = property(lambda s: (s.x + s.w // 2, s.y))
    midbottom = property(lambda s: (s.x + s.w // 2, s.y + s.h))
    topleft = property(lambda s: (s.x, s.y))
    topright = property(lambda s: (s.x + s.w, s.y))
    bottomleft = property(lambda s: (s.x, s.y + s.h))
    bottomright = property(lambda s: (s.x + s.w, s.y + s.h))
    midleft = property(lambda s: (s.x, s.y + s.h // 2))
    midright = property(lambda s: (s.x + s.w, s.y + s.h // 2))
    size = property(lambda s: (s.w, s.h))

    def _set(self, ax, ay, v):
        # ax/ay in {0, .5, 1}: which point of the rect is being placed
        if ax is not None:
            self.x = int(v[0] - self.w * ax)
        if ay is not None:
            self.y = int(v[1] - self.h * ay)

    center = center.setter(lambda s, v: s._set(.5, .5, v))
    midbottom = midbottom.setter(lambda s, v: s._set(.5, 1, v))
    midtop = midtop.setter(lambda s, v: s._set(.5, 0, v))
    topleft = topleft.setter(lambda s, v: s._set(0, 0, v))
    topright = topright.setter(lambda s, v: s._set(1, 0, v))
    bottomleft = bottomleft.setter(lambda s, v: s._set(0, 1, v))
    bottomright = bottomright.setter(lambda s, v: s._set(1, 1, v))
    midleft = midleft.setter(lambda s, v: s._set(0, .5, v))
    midright = midright.setter(lambda s, v: s._set(1, .5, v))

    def inflate(self, dx, dy):
        return Rect(self.x - dx // 2, self.y - dy // 2, self.w + dx, self.h + dy)

    def collidepoint(self, *p):
        px, py = p[0] if len(p) == 1 else p
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

    def copy(self):
        return Rect(self.x, self.y, self.w, self.h)


class Surface:
    def __init__(self, size, flags=0):
        self.img = Image.new("RGBA", (int(size[0]), int(size[1])),
                             (0, 0, 0, 0) if flags & SRCALPHA else (0, 0, 0, 255))

    def get_size(self):
        return self.img.size

    def get_width(self):
        return self.img.size[0]

    def get_height(self):
        return self.img.size[1]

    def get_rect(self, **kw):
        r = Rect(0, 0, *self.img.size)
        for k, v in kw.items():
            setattr(r, k, v)
        return r

    def fill(self, color):
        c = tuple(color) + ((255,) if len(color) == 3 else ())
        self.img.paste(c, (0, 0) + self.img.size)

    def blit(self, src, dest):
        pos = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        self.img.paste(src.img, pos, src.img)


def _box(r):
    r = r if isinstance(r, Rect) else Rect(r)
    return r, [r.x, r.y, r.x + r.w - 1, r.y + r.h - 1]


class draw:
    @staticmethod
    def rect(surf, color, rect, width=0, border_radius=0, border_top_left_radius=-1,
             border_top_right_radius=-1, border_bottom_left_radius=-1, border_bottom_right_radius=-1):
        r, box = _box(rect)
        if r.w <= 0 or r.h <= 0:
            return
        d = ImageDraw.Draw(surf.img)
        radii = [border_top_left_radius, border_top_right_radius,
                 border_bottom_right_radius, border_bottom_left_radius]
        corners = tuple(x > 0 or (x < 0 and border_radius > 0) for x in radii)
        rad = max([x for x in radii] + [border_radius, 0])
        kw = dict(fill=tuple(color) if width == 0 else None,
                  outline=tuple(color) if width else None, width=max(1, width))
        if rad > 0:
            d.rounded_rectangle(box, radius=min(rad, r.h // 2, r.w // 2), corners=corners, **kw)
        else:
            d.rectangle(box, **kw)

    @staticmethod
    def line(surf, color, a, b, width=1):
        ImageDraw.Draw(surf.img).line([tuple(a), tuple(b)], fill=tuple(color), width=width)

    @staticmethod
    def circle(surf, color, center, radius, width=0):
        cx, cy = center
        ImageDraw.Draw(surf.img).ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=tuple(color))

    @staticmethod
    def polygon(surf, color, pts, width=0):
        ImageDraw.Draw(surf.img).polygon([tuple(p) for p in pts], fill=tuple(color))


_FONT_DIRS = ["/usr/share/fonts/truetype/dejavu"]


class Font:
    def __init__(self, path, size, bold=False):
        if path is None or not os.path.exists(str(path)):
            name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            path = os.path.join(_FONT_DIRS[0], name)
        self.f = ImageFont.truetype(path, int(size))
        self.px = int(size)

    def size(self, s):
        return (int(round(self.f.getlength(s))), int(self.px * 1.17))

    def render(self, s, aa, color, bg=None):
        w, h = self.size(s)
        surf = Surface((max(1, w), h), SRCALPHA)
        ImageDraw.Draw(surf.img).text((0, 0), s, font=self.f, fill=tuple(color) + (255,))
        return surf

    def get_linesize(self):
        return self.size("A")[1]


class font:
    Font = Font
    _inited = True

    @staticmethod
    def SysFont(name, size, bold=False, italic=False):
        return Font(None, size, bold)

    @staticmethod
    def init():
        pass


class transform:
    @staticmethod
    def scale(surf, size):
        out = Surface(size)
        out.img = surf.img.resize((int(size[0]), int(size[1])), Image.NEAREST)
        return out


class image:
    @staticmethod
    def save(surf, path):
        surf.img.convert("RGB").save(path)


class _Clock:
    def tick(self, fps=0):
        return 16


class time:
    Clock = _Clock

    @staticmethod
    def get_ticks():
        return int(_time.monotonic() * 1000)


class event:
    @staticmethod
    def get():
        return []


class mouse:
    @staticmethod
    def get_pos():
        return (0, 0)


class display:
    _surf = None

    @staticmethod
    def set_mode(size, flags=0, *a, **k):
        display._surf = Surface(size)
        return display._surf

    @staticmethod
    def set_caption(*a):
        pass

    @staticmethod
    def flip():
        pass

    @staticmethod
    def toggle_fullscreen():
        return 1


def init():
    return (6, 0)


def quit():
    pass
