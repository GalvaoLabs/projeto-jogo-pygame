"""A minimal in-memory stand-in for ``pygame``.

Only used by the test-suite when real pygame is not installed (e.g. in a sandbox), so the whole
UI code path can still be executed headlessly: every screen is drawn, every button can be
clicked, and typos / bad arithmetic / missing names show up as exceptions. Nothing is rendered.
When the real pygame is available the tests use it (with SDL's dummy drivers) instead.
"""
import sys
import types


class error(Exception):
    pass


class Rect:
    def __init__(self, *a):
        if len(a) == 1:
            a = tuple(a[0]) if not isinstance(a[0], Rect) else a[0].as_tuple()
        if len(a) == 2:
            (x, y), (w, h) = a
        else:
            x, y, w, h = a
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    def as_tuple(self):
        return (self.x, self.y, self.w, self.h)

    def __iter__(self):
        return iter(self.as_tuple())

    def __repr__(self):
        return f"Rect{self.as_tuple()}"

    width = property(lambda s: s.w, lambda s, v: setattr(s, "w", int(v)))
    height = property(lambda s: s.h, lambda s, v: setattr(s, "h", int(v)))
    left = property(lambda s: s.x, lambda s, v: setattr(s, "x", int(v)))
    top = property(lambda s: s.y, lambda s, v: setattr(s, "y", int(v)))
    right = property(lambda s: s.x + s.w, lambda s, v: setattr(s, "x", int(v) - s.w))
    bottom = property(lambda s: s.y + s.h, lambda s, v: setattr(s, "y", int(v) - s.h))
    centerx = property(lambda s: s.x + s.w // 2, lambda s, v: setattr(s, "x", int(v) - s.w // 2))
    centery = property(lambda s: s.y + s.h // 2, lambda s, v: setattr(s, "y", int(v) - s.h // 2))

    def _set(self, ax, ay, pos):
        px, py = pos
        if ax == "l":
            self.x = int(px)
        elif ax == "c":
            self.x = int(px) - self.w // 2
        else:
            self.x = int(px) - self.w
        if ay == "t":
            self.y = int(py)
        elif ay == "m":
            self.y = int(py) - self.h // 2
        else:
            self.y = int(py) - self.h

    center = property(lambda s: (s.centerx, s.centery), lambda s, v: s._set("c", "m", v))
    topleft = property(lambda s: (s.x, s.y), lambda s, v: s._set("l", "t", v))
    topright = property(lambda s: (s.right, s.y), lambda s, v: s._set("r", "t", v))
    midtop = property(lambda s: (s.centerx, s.y), lambda s, v: s._set("c", "t", v))
    midleft = property(lambda s: (s.x, s.centery), lambda s, v: s._set("l", "m", v))
    midright = property(lambda s: (s.right, s.centery), lambda s, v: s._set("r", "m", v))
    bottomleft = property(lambda s: (s.x, s.bottom), lambda s, v: s._set("l", "b", v))
    bottomright = property(lambda s: (s.right, s.bottom), lambda s, v: s._set("r", "b", v))
    midbottom = property(lambda s: (s.centerx, s.bottom), lambda s, v: s._set("c", "b", v))
    size = property(lambda s: (s.w, s.h))

    def collidepoint(self, *p):
        px, py = p[0] if len(p) == 1 else p
        return self.x <= px < self.right and self.y <= py < self.bottom

    def inflate(self, dx, dy):
        return Rect(self.x - dx // 2, self.y - dy // 2, self.w + dx, self.h + dy)

    def copy(self):
        return Rect(*self.as_tuple())


class Surface:
    def __init__(self, size=(1, 1), flags=0):
        self._size = (int(size[0]), int(size[1]))

    def fill(self, *a, **k):
        return None

    def blit(self, *a, **k):
        return None

    def get_size(self):
        return self._size

    def get_width(self):
        return self._size[0]

    def get_height(self):
        return self._size[1]

    def get_rect(self, **kw):
        r = Rect(0, 0, *self._size)
        for k, v in kw.items():
            setattr(r, k, v)
        return r


class Font:
    def __init__(self, path=None, size=12):
        self.size_px = size

    def size(self, s):
        return (int(len(str(s)) * self.size_px * 0.5), int(self.size_px * 1.2))

    def render(self, s, aa, color, bg=None):
        return Surface(self.size(s))


class Clock:
    def tick(self, fps=0):
        return 16

    def get_fps(self):
        return 60.0


class Sound:
    def __init__(self, buffer=None):
        self.buffer = buffer

    def set_volume(self, v):
        pass

    def play(self):
        pass


class Event:
    def __init__(self, type, **kw):
        self.type = type
        self.__dict__.update(kw)


def install(width_height=(1280, 720)):
    """Create and register a fake ``pygame`` module; returns it."""
    m = types.ModuleType("pygame")
    m.error = error
    m.Rect, m.Surface = Rect, Surface
    consts = dict(QUIT=256, KEYDOWN=768, MOUSEBUTTONDOWN=1025, MOUSEMOTION=1024,
                  APP_WILLENTERBACKGROUND=259, SCALED=0x200, FULLSCREEN=0x80000000, RESIZABLE=0x10,
                  SRCALPHA=0x10000, KMOD_ALT=0x300,
                  K_ESCAPE=27, K_TAB=9, K_RETURN=13, K_KP_ENTER=1073741912, K_SPACE=32, K_F11=1073741892,
                  K_m=109, K_o=111, K_e=101, K_AC_BACK=1073742094,
                  K_1=49, K_2=50, K_3=51, K_4=52, K_5=53)
    for k, v in consts.items():
        setattr(m, k, v)
    state = {"pos": (0, 0), "queue": [], "ticks": 0}
    m._state = state

    m.init = lambda: (6, 0)
    m.quit = lambda: None
    m.display = types.SimpleNamespace(
        init=lambda: None, flip=lambda: None, set_caption=lambda *a: None, set_icon=lambda *a: None,
        set_mode=lambda size, flags=0: Surface(size))
    m.font = types.SimpleNamespace(init=lambda: None, Font=Font, SysFont=lambda name, size, bold=False: Font(None, size))

    def get_ticks():
        state["ticks"] += 16
        return state["ticks"]

    m.time = types.SimpleNamespace(Clock=Clock, get_ticks=get_ticks)
    m.mouse = types.SimpleNamespace(get_pos=lambda: state["pos"])

    def ev_get():
        q, state["queue"] = state["queue"], []
        return q

    m.event = types.SimpleNamespace(get=ev_get, post=lambda e: state["queue"].append(e), Event=Event)
    m.Event = Event
    m.image = types.SimpleNamespace(load=lambda p: Surface((96, 96)))
    m.transform = types.SimpleNamespace(scale=lambda s, size: Surface(size))
    nop = lambda *a, **k: None
    m.draw = types.SimpleNamespace(rect=nop, line=nop, circle=nop, polygon=nop, lines=nop, ellipse=nop)
    m.mixer = types.SimpleNamespace(get_init=lambda: (22050, -16, 1), init=nop, Sound=Sound)
    sys.modules["pygame"] = m
    return m
