"""V2 - Top-down pixel-art Office. Characters come from the shared Company."""
import random

import pygame

import settings as S
<<<<<<< HEAD
from modes.ui import text, wrap, row as uikit_row
from systems.localization import L, Msg, t, tu, tn, money
=======
from core.company import money
from modes.ui import text, wrap
>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334

T = 16                      # logical tile size
SCALE = 2                   # canvas is drawn small and scaled up (pixel look)
CANVAS_W, CANVAS_H = 500, 332
VIEW_W = CANVAS_W * SCALE   # 1000
PANEL_X = VIEW_W

FLOOR_A, FLOOR_B = (74, 84, 112), (68, 78, 106)
WALL_DARK, WALL_FACE, WALL_EDGE = (36, 40, 58), (88, 96, 130), (52, 58, 82)
WOOD_TOP, WOOD, WOOD_DARK = (178, 128, 80), (150, 104, 62), (106, 70, 42)
SKINS = [(245, 205, 165), (222, 170, 125), (176, 120, 82), (120, 80, 55)]
HAIRS = [(40, 30, 25), (90, 55, 30), (200, 160, 70), (170, 60, 40), (60, 60, 70)]
WALK_SPEED = 38.0


# ---------------------------------------------------------------- layout
def make_layout(level):
    L = S.OFFICE_LEVELS[level]
    rw, rh = L["w"] * T, L["h"] * T
    ox, oy = (CANVAS_W - rw) // 2, (CANVAS_H - rh) // 2
    slots = []
    for i in range(L["cols"] * L["rows"]):
        col, row = i % L["cols"], i // L["cols"]
        x, y = ox + 32 + col * 80, oy + 48 + row * 64
        slots.append({"x": x, "y": y, "seat": (x + 24, y + 31),
                      "desk": pygame.Rect(x, y + 22, 48, 24), "aisle": y + 58})
    zx = ox + rw - 56
    table = pygame.Rect(zx - 32, oy + 48 + (rh - 48) // 2 - 20, 64, 40)
    return {
        "L": L, "rw": rw, "rh": rh, "ox": ox, "oy": oy, "slots": slots, "zx": zx,
        "table": table,
        "cooler": pygame.Rect(zx - 7, oy + 52, 14, 24),
        "board": pygame.Rect(zx - 24, oy + 8, 48, 26),
        "plants": [pygame.Rect(ox + 10, oy + rh - 26, 14, 20),
                   pygame.Rect(ox + rw - 26, oy + rh - 26, 14, 20)],
    }


def cooler_spot(lay, i):
    c = lay["cooler"]
    return (c.centerx + ((i % 3) - 1) * 12, c.bottom + 12 + (i // 3) * 8)


def table_spot(lay, i):
    t = lay["table"]
    k = i % 8
    x = t.x + 8 + (k % 4) * 16
    return (x, t.y - 6) if k < 4 else (x, t.bottom + 16)


def plant_spot(lay, i):
    p = lay["plants"][i]
    return (p.x + 24 if i == 0 else p.x - 10, p.y + 18)


# ---------------------------------------------------------------- drawing
def draw_char(s, cx, fy, emp, sitting, frame, typing=False, rnd=None):
    skin = SKINS[emp.id % len(SKINS)]
    hair = HAIRS[(emp.id * 3) % len(HAIRS)]
    shirt = emp.color
    dark = tuple(max(0, v - 45) for v in shirt)
    if not sitting:
        up = 1 if frame else 0
        pygame.draw.rect(s, (40, 44, 64), (cx - 4, fy - 6 + (1 - up), 3, 6 - (1 - up)))
        pygame.draw.rect(s, (40, 44, 64), (cx + 1, fy - 6 + up, 3, 6 - up))
    pygame.draw.rect(s, shirt, (cx - 5, fy - 13, 10, 7))
    if sitting:
        off = 1 if (typing and frame) else 0
        pygame.draw.rect(s, dark, (cx - 7, fy - 11, 2, 5 + off))
        pygame.draw.rect(s, dark, (cx + 5, fy - 11, 2, 6 - off))
        pygame.draw.rect(s, skin, (cx - 7, fy - 6 + off, 2, 2))
        pygame.draw.rect(s, skin, (cx + 5, fy - 5 - off, 2, 2))
    else:
        sw = 1 if frame else -1
        pygame.draw.rect(s, dark, (cx - 7, fy - 13 + max(0, sw), 2, 6))
        pygame.draw.rect(s, dark, (cx + 5, fy - 13 + max(0, -sw), 2, 6))
        pygame.draw.rect(s, skin, (cx - 7, fy - 7 + max(0, sw), 2, 2))
        pygame.draw.rect(s, skin, (cx + 5, fy - 7 + max(0, -sw), 2, 2))
    pygame.draw.rect(s, skin, (cx - 4, fy - 20, 8, 7))
    pygame.draw.rect(s, hair, (cx - 4, fy - 21, 8, 3))
    pygame.draw.rect(s, hair, (cx - 4, fy - 21, 1, 5))
    pygame.draw.rect(s, (25, 25, 35), (cx - 2, fy - 17, 1, 1))
    pygame.draw.rect(s, (25, 25, 35), (cx + 1, fy - 17, 1, 1))
    if emp.role == "Developer":      # headphones
        pygame.draw.rect(s, (30, 30, 40), (cx - 5, fy - 20, 1, 5))
        pygame.draw.rect(s, (30, 30, 40), (cx + 4, fy - 20, 1, 5))
        pygame.draw.rect(s, (30, 30, 40), (cx - 4, fy - 22, 8, 1))
    elif emp.role == "Designer":     # beret
        pygame.draw.rect(s, (205, 60, 95), (cx - 5, fy - 24, 9, 3))
        pygame.draw.rect(s, (205, 60, 95), (cx - 3, fy - 25, 5, 1))
    elif emp.role == "Marketing Specialist":   # headset + mic
        pygame.draw.rect(s, (245, 245, 245), (cx - 5, fy - 19, 1, 4))
        pygame.draw.rect(s, (245, 245, 245), (cx - 5, fy - 15, 3, 1))
    elif emp.role == "Manager":      # tie
        pygame.draw.rect(s, (245, 245, 245), (cx - 2, fy - 13, 4, 1))
        pygame.draw.rect(s, (200, 50, 50), (cx - 1, fy - 12, 2, 5))


def draw_plant(s, r, t, seed=0):
    sway = 1 if int(t * 1.5 + seed) % 2 else 0
    pygame.draw.rect(s, (150, 80, 55), (r.x + 3, r.y + 12, 8, 8))
    pygame.draw.rect(s, (110, 55, 38), (r.x + 3, r.y + 12, 8, 2))
    for dx, dy, w, h in ((1, 4, 5, 6), (7, 3, 6, 7), (4, 0, 6, 8)):
        pygame.draw.rect(s, (52, 160, 90), (r.x + dx + sway * (dx % 2), r.y + dy, w, h))
    pygame.draw.rect(s, (80, 200, 115), (r.x + 5, r.y + 2, 3, 4))


def dashed_rect(s, rect, color, dash=6):
    x0, y0, x1, y1 = rect.left, rect.top, rect.right - 1, rect.bottom - 1
    for x in range(x0, x1, dash * 2):
        pygame.draw.line(s, color, (x, y0), (min(x + dash, x1), y0))
        pygame.draw.line(s, color, (x, y1), (min(x + dash, x1), y1))
    for y in range(y0, y1, dash * 2):
        pygame.draw.line(s, color, (x0, y), (x0, min(y + dash, y1)))
        pygame.draw.line(s, color, (x1, y), (x1, min(y + dash, y1)))


# ---------------------------------------------------------------- sprites
class Sprite:
    def __init__(self, emp_id, seat):
        self.id = emp_id
        self.x, self.y = seat
        self.state = "sit"          # sit | walk_out | stay | walk_back
        self.path = []
        self.timer = 0.0
        self.break_timer = random.uniform(8, 22)
        self.anim = random.uniform(0, 5)
        self.activity = ""

    def walk_to(self, path):
        self.path = list(path)

    def step(self, dt):
        """Move along the path. Returns True when the path is finished."""
        if not self.path:
            return True
        tx, ty = self.path[0]
        dx, dy = tx - self.x, ty - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        move = WALK_SPEED * dt
        if dist <= move:
            self.x, self.y = tx, ty
            self.path.pop(0)
            return not self.path
        self.x += dx / dist * move
        self.y += dy / dist * move
        return False

    @property
    def walking(self):
        return self.state in ("walk_out", "walk_back")


class OfficeMode:
    def __init__(self, company, ui, goto_dashboard_tab):
        self.c = company
        self.ui = ui
        self.goto = goto_dashboard_tab
        self.t = 0.0
        self.level = company.office_level
        self.lay = make_layout(self.level)
        self.sprites = {}
        self.sel = None            # ("emp", id) | ("desk", i) | ("meeting",) | ("cooler",) | ("plant", i) | ("board",)
        self.sync()

    # ------------------------------------------------------------ sync/update
    def seat_of(self, index):
        slots = self.lay["slots"]
        return slots[min(index, len(slots) - 1)]

    def sync(self):
        c = self.c
        if c.office_level != self.level:       # expansion: rebuild room, everyone sits down
            self.level = c.office_level
            self.lay = make_layout(self.level)
            for sp in self.sprites.values():
                sp.state, sp.path = "sit", []
            self.sel = None
        ids = {e.id for e in c.employees}
        for eid in list(self.sprites):
            if eid not in ids:
                del self.sprites[eid]
                if self.sel == ("emp", eid):
                    self.sel = None
        for i, e in enumerate(c.employees):
            slot = self.seat_of(i)
            if e.id not in self.sprites:
                self.sprites[e.id] = Sprite(e.id, slot["seat"])
            sp = self.sprites[e.id]
            if sp.state == "sit":
                sp.x, sp.y = slot["seat"]
            elif sp.state == "walk_back" and sp.path:
                sp.path[-1] = slot["seat"]

    def update(self, dt):
        self.t += dt
        self.sync()
        lay = self.lay
        for i, e in enumerate(self.c.employees):
            sp = self.sprites[e.id]
            slot = self.seat_of(i)
            sp.anim += dt
            if sp.state == "sit":
                sp.break_timer -= dt
                if sp.break_timer <= 0:
                    sp.break_timer = random.uniform(14, 34)
                    self.send(sp, i, random.choice(["cooler", "meeting", "plant"]), random.uniform(3, 6))
            elif sp.state == "walk_out":
                if sp.step(dt):
                    sp.state = "stay"
            elif sp.state == "stay":
                sp.timer -= dt
                if sp.timer <= 0:
                    sp.state = "walk_back"
                    sp.walk_to(self.route((sp.x, sp.y), slot["seat"], slot["aisle"]))
            elif sp.state == "walk_back":
                if sp.step(dt):
                    sp.state = "sit"
                    sp.x, sp.y = slot["seat"]

    def route(self, pos, dest, aisle):
        pts = []
        if abs(pos[1] - aisle) > 1:
            pts.append((pos[0], aisle))
        if abs(pos[0] - dest[0]) > 1 or not pts:
            pts.append((dest[0], aisle))
        pts.append(dest)
        return pts

    def send(self, sp, index, where, stay):
        lay = self.lay
        slot = self.seat_of(index)
        if where == "cooler":
            spot = cooler_spot(lay, index)
        elif where == "meeting":
            spot = table_spot(lay, index)
        else:
            spot = plant_spot(lay, index % 2)
        sp.state = "walk_out"
        sp.timer = stay
        sp.activity = where
        sp.walk_to(self.route((sp.x, sp.y), spot, slot["aisle"]))

    def send_all(self, where, stay):
        n = 0
        for i, e in enumerate(self.c.employees):
            sp = self.sprites[e.id]
            if sp.state == "sit":
                self.send(sp, i, where, stay)
                n += 1
        return n

    # ------------------------------------------------------------ picking
    def sprite_rect(self, sp):
        return pygame.Rect(int(sp.x) - 7, int(sp.y) - 22, 14, 24 if sp.walking else 12)

    def pick(self, lx, ly):
        lay = self.lay
        for e in reversed(self.c.employees):
            sp = self.sprites[e.id]
            if self.sprite_rect(sp).collidepoint(lx, ly):
                return ("emp", e.id)
        for i, slot in enumerate(lay["slots"]):
            if pygame.Rect(slot["x"], slot["y"] + 8, 48, 40).collidepoint(lx, ly):
                if i < len(self.c.employees):
                    return ("emp", self.c.employees[i].id)
                return ("desk", i)
        if lay["table"].inflate(10, 10).collidepoint(lx, ly):
            return ("meeting",)
        if lay["cooler"].collidepoint(lx, ly):
            return ("cooler",)
        for i, p in enumerate(lay["plants"]):
            if p.inflate(6, 6).collidepoint(lx, ly):
                return ("plant", i)
        if lay["board"].collidepoint(lx, ly):
            return ("board",)
        return None

    # ------------------------------------------------------------ drawing
    def draw(self, surf):
        ui = self.ui
        canvas = pygame.Surface((CANVAS_W, CANVAS_H))
        self.draw_world(canvas)
        view = pygame.transform.scale(canvas, (VIEW_W, CANVAS_H * SCALE))
        surf.blit(view, (0, S.NAV_H))

        mx, my = ui.mouse
        in_view = (not ui.locked) and 0 <= mx < VIEW_W and my >= S.NAV_H
        hovered = None
        if in_view:
            lx, ly = mx / SCALE, (my - S.NAV_H) / SCALE
            hovered = self.pick(lx, ly)
            if ui.clicked:
                ui.clicked = False
                self.sel = hovered
<<<<<<< HEAD
        label = ""
        if hovered and hovered[0] == "emp":
            e = next((x for x in self.c.employees if x.id == hovered[1]), None)
            if e:
                label = f"{e.name} - {t('role.' + e.role)}"
        elif hovered:
            names = {"meeting": "obj.meeting", "cooler": "obj.cooler", "plant": "obj.plant_short",
                     "board": "obj.board", "desk": "obj.desk_empty"}
            label = t(names[hovered[0]]) if hovered[0] in names else ""
        if label:
            self.draw_tooltip(surf, label, (mx + 14, my - 8))
        self.draw_panel(surf)

    def draw_tooltip(self, surf, label, pos):
        """Small label next to the cursor, kept inside the window (translations can be long)."""
        from modes.ui import fit_text, font
        label, size = fit_text(label, 14, 360, True)
        w, h = font(size, True).size(label)
        x = min(pos[0], S.WIDTH - w - 24)
        bg = pygame.Rect(x - 7, pos[1] - 4, w + 14, h + 8)
        pygame.draw.rect(surf, (20, 24, 38), bg, border_radius=6)
        pygame.draw.rect(surf, S.BORDER, bg, 1, border_radius=6)
        text(surf, label, (x, pos[1]), size, S.WHITE, bold=True)

=======
        if hovered and hovered[0] == "emp":
            e = next((x for x in self.c.employees if x.id == hovered[1]), None)
            if e:
                label = f"{e.name} - {e.role}"
                r = text(surf, label, (mx + 14, my - 8), 14, S.WHITE, bold=True)
                bg = r.inflate(14, 8)
                pygame.draw.rect(surf, (20, 24, 38), bg, border_radius=6)
                pygame.draw.rect(surf, S.BORDER, bg, 1, border_radius=6)
                text(surf, label, (mx + 14, my - 8), 14, S.WHITE, bold=True)
        elif hovered:
            names = {"meeting": "Meeting table", "cooler": "Coffee machine", "plant": "Plant",
                     "board": "Whiteboard", "desk": "Empty desk"}
            label = names.get(hovered[0], "")
            r = text(surf, label, (mx + 14, my - 8), 14, S.WHITE, bold=True)
            bg = r.inflate(14, 8)
            pygame.draw.rect(surf, (20, 24, 38), bg, border_radius=6)
            pygame.draw.rect(surf, S.BORDER, bg, 1, border_radius=6)
            text(surf, label, (mx + 14, my - 8), 14, S.WHITE, bold=True)
        self.draw_panel(surf)

>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334
    def draw_world(self, s):
        lay, c, t = self.lay, self.c, self.t
        ox, oy, rw, rh = lay["ox"], lay["oy"], lay["rw"], lay["rh"]
        s.fill((14, 16, 24))
        # ghost outline of the next expansion
        if c.office_level + 1 < len(S.OFFICE_LEVELS):
            nl = make_layout(c.office_level + 1)
            dashed_rect(s, pygame.Rect(nl["ox"] - 5, nl["oy"] - 5, nl["rw"] + 10, nl["rh"] + 10), (60, 78, 125))
        pygame.draw.rect(s, WALL_EDGE, (ox - 4, oy - 4, rw + 8, rh + 8))
        # floor
        for ty in range(3, lay["L"]["h"]):
            for tx in range(lay["L"]["w"]):
                col = FLOOR_A if (tx + ty) % 2 == 0 else FLOOR_B
                pygame.draw.rect(s, col, (ox + tx * T, oy + ty * T, T, T))
        # top wall
        pygame.draw.rect(s, WALL_FACE, (ox, oy, rw, 48))
        pygame.draw.rect(s, WALL_DARK, (ox, oy, rw, 6))
        pygame.draw.rect(s, WALL_DARK, (ox, oy + 44, rw, 4))
        for x in range(ox + 20, ox + rw - 120, 52):
            pygame.draw.rect(s, (205, 210, 225), (x - 2, oy + 9, 36, 28))
            pygame.draw.rect(s, (110, 176, 232), (x, oy + 11, 32, 24))
            pygame.draw.rect(s, (160, 210, 245), (x, oy + 11, 32, 8))
            pygame.draw.rect(s, (205, 210, 225), (x + 15, oy + 11, 2, 24))
            pygame.draw.rect(s, (205, 210, 225), (x, oy + 22, 32, 2))
            pygame.draw.rect(s, (255, 240, 170), (x + 22, oy + 13, 5, 5))
        # whiteboard
        b = lay["board"]
        pygame.draw.rect(s, (200, 200, 210), (b.x - 2, b.y - 2, b.w + 4, b.h + 4))
        pygame.draw.rect(s, (245, 246, 250), b)
        frac = max(0.0, min(1.0, c.net_worth / S.GOAL_NET_WORTH))
        pygame.draw.rect(s, (200, 205, 220), (b.x + 4, b.y + 17, b.w - 8, 5))
        pygame.draw.rect(s, (60, 190, 110), (b.x + 4, b.y + 17, int((b.w - 8) * frac), 5))
        pygame.draw.line(s, (220, 70, 70), (b.x + 5, b.y + 5), (b.x + 22, b.y + 5))
        pygame.draw.line(s, (60, 100, 220), (b.x + 5, b.y + 10), (b.x + 32, b.y + 10))
        # rug + meeting table
        tb = lay["table"]
        pygame.draw.rect(s, (96, 70, 122), (tb.x - 12, tb.y - 18, tb.w + 24, tb.h + 36))
        pygame.draw.rect(s, (120, 92, 150), (tb.x - 12, tb.y - 18, tb.w + 24, tb.h + 36), 2)
        for k in range(4):
            cx = tb.x + 8 + k * 16
            pygame.draw.rect(s, (60, 64, 84), (cx - 5, tb.y - 10, 10, 8))
            pygame.draw.rect(s, (60, 64, 84), (cx - 5, tb.bottom + 2, 10, 8))
        pygame.draw.rect(s, WOOD_DARK, (tb.x, tb.y + 3, tb.w, tb.h))
        pygame.draw.rect(s, (196, 146, 92), tb)
        pygame.draw.rect(s, WOOD, (tb.x, tb.y, tb.w, tb.h), 1)
        pygame.draw.rect(s, (235, 235, 245), (tb.centerx - 6, tb.centery - 4, 12, 8))
        pygame.draw.rect(s, (90, 130, 220), (tb.centerx - 5, tb.centery - 3, 10, 1))
        # coffee machine
        cl = lay["cooler"]
        pygame.draw.rect(s, (70, 76, 96), cl)
        pygame.draw.rect(s, (130, 200, 255), (cl.x + 2, cl.y + 2, 10, 9))
        pygame.draw.rect(s, (225, 230, 240), (cl.x + 2, cl.y + 14, 10, 8))
        if int(t * 2) % 2:
            pygame.draw.rect(s, (255, 255, 255), (cl.x + 6, cl.y - 3, 2, 2))
        for i, p in enumerate(lay["plants"]):
            draw_plant(s, p, t, i)
        draw_plant(s, pygame.Rect(ox + rw - 24, oy + 50, 14, 20), t, 5)

        # desks with their occupants
        emps = c.employees
        for i, slot in enumerate(lay["slots"]):
            sx, sy = slot["seat"]
            x, y = slot["x"], slot["y"]
            pygame.draw.rect(s, (52, 56, 76), (sx - 6, y + 12, 12, 3))          # chair back
            pygame.draw.rect(s, (62, 66, 90), (sx - 6, y + 14, 12, 14))         # chair seat
            emp = emps[i] if i < len(emps) else None
            sp = self.sprites.get(emp.id) if emp else None
            if emp and sp and sp.state == "sit":
                draw_char(s, sx, sy, emp, True, int(sp.anim * 4) % 2, typing=True)
            d = slot["desk"]
            pygame.draw.rect(s, WOOD_DARK, (d.x, d.y + 3, d.w, d.h))
            pygame.draw.rect(s, WOOD_TOP, (d.x, d.y, d.w, d.h - 3))
            pygame.draw.rect(s, WOOD, (d.x, d.y, d.w, d.h - 3), 1)
            working = bool(emp and sp and sp.state == "sit")
            pygame.draw.rect(s, (36, 40, 52), (sx - 9, d.y + 2, 18, 12))        # monitor bezel
            if working:
                pygame.draw.rect(s, (30, 46, 84), (sx - 8, d.y + 3, 16, 9))
                for k in range(3):
                    wlen = 4 + (int(t * 3) + k * 5 + i * 3) % 9
                    pygame.draw.rect(s, (120, 205, 255) if k != 1 else (255, 205, 120),
                                     (sx - 7, d.y + 4 + k * 3, wlen, 1))
            else:
                pygame.draw.rect(s, (20, 22, 30), (sx - 8, d.y + 3, 16, 9))
            pygame.draw.rect(s, (36, 40, 52), (sx - 2, d.y + 14, 4, 2))
            pygame.draw.rect(s, (210, 214, 224), (sx - 7, d.y + 17, 14, 3))     # keyboard
            pygame.draw.rect(s, (240, 240, 245), (d.right - 9, d.y + 5, 4, 5))  # mug
            pygame.draw.rect(s, (200, 70, 70), (d.right - 9, d.y + 5, 4, 1))

        # walking employees on top
        walkers = [(self.sprites[e.id], e) for e in emps if self.sprites[e.id].state != "sit"]
        for sp, e in sorted(walkers, key=lambda p: p[0].y):
            moving = sp.walking
            draw_char(s, int(sp.x), int(sp.y), e, False, int(sp.anim * 6) % 2 if moving else 0)

        # selection marker
        self.draw_selection(s)

    def draw_selection(self, s):
        sel = self.sel
        if not sel:
            return
        lay, bob = self.lay, int(self.t * 4) % 2
        col = (255, 220, 70)
        if sel[0] == "emp":
            sp = self.sprites.get(sel[1])
            if sp:
                cx, top = int(sp.x), int(sp.y) - 30 + bob
                pygame.draw.polygon(s, col, [(cx - 4, top), (cx + 4, top), (cx, top + 5)])
        else:
            rect = None
            if sel[0] == "desk":
                rect = lay["slots"][sel[1]]["desk"]
            elif sel[0] == "meeting":
                rect = lay["table"]
            elif sel[0] == "cooler":
                rect = lay["cooler"]
            elif sel[0] == "plant":
                rect = lay["plants"][sel[1]]
            elif sel[0] == "board":
                rect = lay["board"]
            if rect:
                pygame.draw.rect(s, col, rect.inflate(4, 4), 1)

    # ------------------------------------------------------------ side panel
    def draw_panel(self, surf):
        c, ui, lay = self.c, self.ui, self.lay
        pygame.draw.rect(surf, S.SIDEBAR, (PANEL_X, S.NAV_H, S.WIDTH - PANEL_X, S.HEIGHT - S.NAV_H))
        pygame.draw.line(surf, S.BORDER, (PANEL_X, S.NAV_H), (PANEL_X, S.HEIGHT))
        x, w = PANEL_X + 14, S.WIDTH - PANEL_X - 28
        y = S.NAV_H + 12
<<<<<<< HEAD
        text(surf, tu("nav.office"), (x, y), 22, S.TEXT, bold=True, max_w=w - 110)
        text(surf, t("office.level", n=c.office_level + 1, max=len(S.OFFICE_LEVELS)), (x + w, y + 5), 14, S.PURPLE,
             bold=True, anchor="topright", max_w=105)
        y += 40
        text(surf, t("office.desks_used", used=len(c.employees), cap=c.office_capacity), (x, y), 15, S.MUTED, max_w=w)
=======
        text(surf, "OFFICE", (x, y), 22, S.TEXT, bold=True)
        text(surf, f"Level {c.office_level + 1} / {len(S.OFFICE_LEVELS)}", (x + w, y + 5), 14, S.PURPLE,
             bold=True, anchor="topright")
        y += 40
        text(surf, f"Desks used: {len(c.employees)} / {c.office_capacity}", (x, y), 15, S.MUTED)
>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334
        ui.bar(surf, (x, y + 24, w, 12), len(c.employees), c.office_capacity,
               S.ORANGE if len(c.employees) >= c.office_capacity else S.BLUE)
        y += 48
        cost = c.next_office_cost
        if cost is None:
<<<<<<< HEAD
            ui.button(surf, (x, y, w, 46), t("office.at_max"), enabled=False, size=15)
        else:
            kind = "success" if c.cash >= cost else "ghost"
            if ui.button(surf, (x, y, w, 46), t("office.expand", cost=cost), kind=kind, size=15):
                ok, msg = c.expand_office()
                ui.toast(msg, ok)
            nxt = S.OFFICE_LEVELS[c.office_level + 1]["capacity"] - c.office_capacity
            text(surf, t("office.expand_note", n=nxt), (x, y + 52), 12, S.MUTED, max_w=w)
        y += 80

        card = pygame.Rect(x - 4, y, w + 8, 330)
        ui.card(surf, card, tu("office.selected"))
        self.draw_selected(surf, card)

        by = card.bottom + 12
        text(surf, t("common.cash", v=c.cash), (x, by), 14, S.GREEN if c.cash >= 0 else S.RED, bold=True, max_w=w)
        text(surf, t("common.payroll", v=c.monthly_payroll), (x, by + 22), 14, S.MUTED, max_w=w)
=======
            ui.button(surf, (x, y, w, 46), "Office at maximum size", enabled=False, size=15)
        else:
            kind = "success" if c.cash >= cost else "ghost"
            if ui.button(surf, (x, y, w, 46), f"Expand office: {money(cost)}", kind=kind, size=15):
                ok, msg = c.expand_office()
                ui.toast(msg, ok)
            nxt = S.OFFICE_LEVELS[c.office_level + 1]["capacity"] - c.office_capacity
            text(surf, f"+{nxt} desks. Maintenance grows too.", (x, y + 52), 12, S.MUTED)
        y += 80

        card = pygame.Rect(x - 4, y, w + 8, 330)
        ui.card(surf, card, "SELECTED")
        self.draw_selected(surf, card)

        by = card.bottom + 12
        text(surf, f"Cash {money(c.cash)}", (x, by), 14, S.GREEN if c.cash >= 0 else S.RED, bold=True)
        text(surf, f"Payroll {money(c.monthly_payroll)}/mo", (x, by + 22), 14, S.MUTED)
>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334

    def draw_selected(self, surf, card):
        c, ui, sel = self.c, self.ui, self.sel
        x, y, w = card.x + 14, card.y + 36, card.w - 28
        if not sel:
<<<<<<< HEAD
            for i, line in enumerate(wrap(t("office.hint_select"), 14, w)):
=======
            for i, line in enumerate(wrap("Click an employee, a desk or an object in the office to inspect it.", 14, w)):
>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334
                text(surf, line, (x, y + i * 20), 14, S.MUTED)
            return
        kind = sel[0]
        if kind == "emp":
            idx = next((i for i, e in enumerate(c.employees) if e.id == sel[1]), None)
            if idx is None:
                self.sel = None
                return
            e = c.employees[idx]
            sp = self.sprites.get(e.id)
<<<<<<< HEAD
            text(surf, e.name, (x, y), 22, S.TEXT, bold=True, max_w=w)
            text(surf, t(f"role.{e.role}"), (x, y + 30), 16, e.color, bold=True, max_w=w)
            state = t("state." + (sp.state if sp else "sit"))
            text(surf, state, (x, y + 54), 14, S.MUTED, max_w=w)
            ui_rows = [(t("hr.col_salary"), t("emp.salary_value", v=e.salary)), (t("emp.fee_paid"), money(e.fee)),
                       (t("emp.desk"), t("emp.desk_value", n=idx + 1)), (t("emp.hired"), t("emp.hired_value", n=e.hired_month))]
            for i, (a, b) in enumerate(ui_rows):
                uikit_row(surf, x, y + 84 + i * 24, w, a, b, S.TEXT, 14)
            text(surf, t("emp.productivity", v=e.productivity), (x, y + 190), 14, S.MUTED, max_w=w)
            ui.bar(surf, (x, y + 212, w, 10), e.productivity, 1.3, S.BLUE)
            if ui.button(surf, (x, y + 240, w, 38), t("emp.manage_hr"), kind="primary", size=14):
                self.goto(1)
        elif kind == "desk":
            text(surf, t("desk.empty_title", n=sel[1] + 1), (x, y), 20, S.TEXT, bold=True, max_w=w)
            for i, line in enumerate(wrap(t("desk.empty_desc"), 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 110, w, 38), t("desk.go_hr"), kind="primary", size=14):
                self.goto(1)
        elif kind == "meeting":
            text(surf, t("obj.meeting"), (x, y), 20, S.TEXT, bold=True, max_w=w)
            for i, line in enumerate(wrap(t("meeting.desc"), 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 110, w, 38), t("meeting.call"), kind="purple", size=14):
                n = self.send_all("meeting", 7)
                ui.toast(Msg("msg.meeting." + ("one" if n == 1 else "other"), {"n": n}) if n else Msg("msg.all_away"), bool(n))
        elif kind == "cooler":
            text(surf, t("obj.cooler"), (x, y), 20, S.TEXT, bold=True, max_w=w)
            for i, line in enumerate(wrap(t("cooler.desc"), 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 90, w, 38), t("cooler.btn"), kind="purple", size=14):
                n = self.send_all("cooler", 5)
                ui.toast(Msg("msg.coffee") if n else Msg("msg.all_away"), bool(n))
        elif kind == "plant":
            text(surf, t("obj.plant"), (x, y), 20, S.TEXT, bold=True, max_w=w)
            text(surf, t("plant.desc"), (x, y + 34), 14, S.MUTED, max_w=w)
            if ui.button(surf, (x, y + 70, w, 38), t("plant.water"), kind="success", size=14):
                ui.toast(Msg("msg.watered"), True)
        elif kind == "board":
            text(surf, t("obj.board"), (x, y), 20, S.TEXT, bold=True, max_w=w)
            frac = max(0.0, c.net_worth / S.GOAL_NET_WORTH)
            text(surf, t("board.goal"), (x, y + 34), 14, S.MUTED, max_w=w)
            ui.bar(surf, (x, y + 58, w, 12), c.net_worth, S.GOAL_NET_WORTH, S.GREEN)
            text(surf, t("board.progress", a=c.net_worth, b=S.GOAL_NET_WORTH), (x, y + 78), 13, S.TEXT, max_w=w)
            text(surf, t("board.complete", p=frac * 100), (x, y + 98), 13, S.MUTED, max_w=w)
=======
            text(surf, e.name, (x, y), 22, S.TEXT, bold=True)
            text(surf, e.role, (x, y + 30), 16, e.color, bold=True)
            state = {"sit": "Working at desk", "walk_out": "Walking", "stay": "On a break",
                     "walk_back": "Heading back"}.get(sp.state if sp else "sit", "")
            text(surf, state, (x, y + 54), 14, S.MUTED)
            ui_rows = [("Salary", money(e.salary) + "/mo"), ("Hiring fee paid", money(e.fee)),
                       ("Desk", f"#{idx + 1}"), ("Hired", f"month {e.hired_month}")]
            for i, (a, b) in enumerate(ui_rows):
                text(surf, a, (x, y + 84 + i * 24), 14, S.MUTED)
                text(surf, b, (x + w, y + 84 + i * 24), 14, S.TEXT, anchor="topright")
            text(surf, f"Productivity {e.productivity:.2f}", (x, y + 190), 14, S.MUTED)
            ui.bar(surf, (x, y + 212, w, 10), e.productivity, 1.3, S.BLUE)
            if ui.button(surf, (x, y + 240, w, 38), "Manage in HR", kind="primary", size=14):
                self.goto(1)
        elif kind == "desk":
            text(surf, f"Empty desk #{sel[1] + 1}", (x, y), 20, S.TEXT, bold=True)
            for i, line in enumerate(wrap("Nobody sits here yet. Hire someone in Human Resources.", 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 110, w, 38), "Go to HR", kind="primary", size=14):
                self.goto(1)
        elif kind == "meeting":
            text(surf, "Meeting table", (x, y), 20, S.TEXT, bold=True)
            for i, line in enumerate(wrap("Gather the whole team around the table for a quick sync.", 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 110, w, 38), "Call team meeting", kind="purple", size=14):
                n = self.send_all("meeting", 7)
                ui.toast(f"Team meeting called: {n} people on the way." if n else "Everyone is already away from their desk.", bool(n))
        elif kind == "cooler":
            text(surf, "Coffee machine", (x, y), 20, S.TEXT, bold=True)
            for i, line in enumerate(wrap("A coffee break never hurt anybody.", 14, w)):
                text(surf, line, (x, y + 34 + i * 20), 14, S.MUTED)
            if ui.button(surf, (x, y + 90, w, 38), "Coffee break", kind="purple", size=14):
                n = self.send_all("cooler", 5)
                ui.toast("Coffee break!" if n else "Everyone is already away from their desk.", bool(n))
        elif kind == "plant":
            text(surf, "Office plant", (x, y), 20, S.TEXT, bold=True)
            text(surf, "It looks happy.", (x, y + 34), 14, S.MUTED)
            if ui.button(surf, (x, y + 70, w, 38), "Water plant", kind="success", size=14):
                ui.toast("You watered the plant.", True)
        elif kind == "board":
            text(surf, "Whiteboard", (x, y), 20, S.TEXT, bold=True)
            frac = max(0.0, c.net_worth / S.GOAL_NET_WORTH)
            text(surf, "Company goal", (x, y + 34), 14, S.MUTED)
            ui.bar(surf, (x, y + 58, w, 12), c.net_worth, S.GOAL_NET_WORTH, S.GREEN)
            text(surf, f"{money(c.net_worth)} of {money(S.GOAL_NET_WORTH)}", (x, y + 78), 13, S.TEXT)
            text(surf, f"{frac * 100:.1f}% complete", (x, y + 98), 13, S.MUTED)
>>>>>>> 440bc27087758b9f4bcd405fe6188ca6d129a334
