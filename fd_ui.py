"""Menu look: stone plaques and panels in the style of the main title, fire-lettered screen titles,
the icon tab bar along the bottom, and the themed backdrops for each menu screen."""
import math
import random
import pygame
from fd_core import *
import fd_core
import fd_env as ENV

_C = {}
GOLD, GOLD_L, GOLD_D = (212, 160, 44), (255, 230, 140), (110, 74, 16)


def _cache(key, fn):
  s = _C.get(key)
  if s is None:
    s = _C[key] = fn()
  return s


# ---------------------------------------------------------------- stone panels (the main title's crest)
def _bricks(s, x0, y0, w, h, rng, base=(34, 32, 44), bh=16):
  y, row = y0, 0
  while y < y0 + h:
    x = x0 - (row % 2) * 20
    hh = min(bh, y0 + h - y)
    while x < x0 + w:
      bw = rng.randint(34, 52)
      xa, xb = max(x0, x + 1), min(x0 + w, x + bw - 1)
      if xb - xa > 2 and hh > 2:
        v = rng.randint(-8, 10)
        c = (base[0] + v, base[1] + v, base[2] + v)
        pygame.draw.rect(s, c, (xa, y + 1, xb - xa, hh - 2))
        pygame.draw.line(s, (c[0] + 14, c[1] + 14, c[2] + 14), (xa, y + 1), (xb - 1, y + 1))
        pygame.draw.line(s, (8, 8, 12), (xa, y + hh - 1), (xb - 1, y + hh - 1))
      x += bw
    y += bh
    row += 1


def stone_surface(w, h, accent=None, base=(34, 32, 44)):
  """stone-brick panel with the main title's gold frame and corner studs"""
  w, h = max(24, int(w)), max(24, int(h))
  def build():
    rng = random.Random(w * 7 + h * 13)
    r = 14 if min(w, h) > 60 else 8
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (14, 12, 20), (0, 0, w, h), border_radius=r)
    _bricks(s, 6, 6, w - 12, h - 12, rng, base)
    for _ in range(w * h // 260):
      s.set_at((rng.randint(8, w - 9), rng.randint(8, h - 9)), rng.choice(((20, 18, 26), (58, 56, 70), (28, 26, 36))))
    edge = min(16, min(w, h) // 5)
    for i in range(edge):                         # inner shadow
      a = int(150 * (1 - i / float(edge)))
      sh = pygame.Surface((w - 2 * i, 2), pygame.SRCALPHA)
      sh.fill((0, 0, 0, a))
      s.blit(sh, (i, i))
      s.blit(sh, (i, h - i - 2))
      sv = pygame.Surface((2, h - 2 * i), pygame.SRCALPHA)
      sv.fill((0, 0, 0, a // 2))
      s.blit(sv, (i, i))
      s.blit(sv, (w - i - 2, i))
    pygame.draw.rect(s, GOLD_D, (0, 0, w, h), 6, border_radius=r)
    pygame.draw.rect(s, GOLD, (1, 1, w - 2, h - 2), 3, border_radius=r - 1)
    pygame.draw.rect(s, GOLD_L, (3, 3, w - 6, h - 6), 1, border_radius=max(2, r - 3))
    if min(w, h) > 70:
      pygame.draw.rect(s, GOLD_D, (11, 11, w - 22, h - 22), 2, border_radius=max(2, r - 6))
      pygame.draw.rect(s, GOLD, (12, 12, w - 24, h - 24), 1, border_radius=max(2, r - 6))
    if accent:
      pygame.draw.rect(s, accent, (7, 7, w - 14, h - 14), 2, border_radius=max(2, r - 5))
    if min(w, h) > 44:
      for cx, cy in ((12, 12), (w - 12, 12), (12, h - 12), (w - 12, h - 12)):
        pygame.draw.circle(s, GOLD_D, (cx, cy), 7)
        pygame.draw.circle(s, GOLD, (cx, cy), 5)
        pygame.draw.circle(s, GOLD_L, (cx - 2, cy - 2), 2)
    return s.convert_alpha()
  return _cache(('stone', w, h, accent, base), build)


STONE_FILLS = (PANEL_DARK, (50, 15, 15), (30, 20, 16), (30, 28, 40), IRON_GRAY)


def stone_panel(surf, rect, fill, alpha, border, bw, radius):
  """the hook fd_core.panel() calls on menu screens"""
  if fill not in STONE_FILLS or rect.w < 40 or rect.h < 30:
    return False
  accent = None if border in (GOLD_BORDER, STONE_LIGHT, STONE_DARK, BANNER_GOLD) else border
  surf.blit(stone_surface(rect.w, rect.h, accent), rect.topleft)
  return True


fd_core.UI['stone_fn'] = stone_panel


# ---------------------------------------------------------------- fire-lettered titles on a stone plaque
def small_fire(label, size, stops=None):
  """small fire-lettered text (same colours as the main title, but a tighter outline and shadow)"""
  def build():
    f = pygame.font.SysFont("serif", size, bold=True)
    im = f.render(label, True, (255, 255, 255))
    w, h = im.get_width() + 8, im.get_height() + 8
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    def stamp(col, offs):
      tint = pygame.Surface(im.get_size(), pygame.SRCALPHA)
      tint.fill(col + (255,))
      tint.blit(im, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
      for ox, oy in offs:
        out.blit(tint, (3 + ox, 3 + oy))
    stamp((12, 5, 3), [(2, 3)])
    stamp((24, 10, 6), [(dx, dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) if dx * dx + dy * dy <= 5])
    stamp((206, 146, 36), [(-1, 0), (1, 0), (0, -1), (0, 1)])
    fill = pygame.Surface(im.get_size(), pygame.SRCALPHA)
    st = stops or ENV.FIRE_TEXT
    hh = im.get_height()
    for y in range(hh):
      u = y / float(max(1, hh - 1)) * (len(st) - 1)
      i = min(len(st) - 2, int(u))
      fr = u - i
      c = tuple(int(st[i][k] + (st[i + 1][k] - st[i][k]) * fr) for k in range(3))
      pygame.draw.line(fill, c + (255,), (0, y), (im.get_width(), y))
    fill.blit(im, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    out.blit(fill, (3, 3))
    return out.convert_alpha()
  return _cache(('sfire', label, size), build)


def title_plaque(label, size=38):
  def build():
    t = ENV.fire_text(label, size)
    w, h = t.get_width() + 96, t.get_height() + 18
    s = stone_surface(w, h).copy()
    ly = h - 9
    pygame.draw.line(s, GOLD, (28, ly), (w // 2 - 16, ly), 1)
    pygame.draw.line(s, GOLD, (w // 2 + 16, ly), (w - 28, ly), 1)
    pygame.draw.polygon(s, GOLD_L, [(w // 2, ly - 5), (w // 2 + 6, ly), (w // 2, ly + 5), (w // 2 - 6, ly)])
    for side in (-1, 1):                             # little gold diamonds at the ends
      cx = w // 2 + side * (w // 2 - 22)
      pygame.draw.polygon(s, GOLD, [(cx, h // 2 - 7), (cx + 6, h // 2), (cx, h // 2 + 7), (cx - 6, h // 2)])
      pygame.draw.polygon(s, GOLD_L, [(cx, h // 2 - 3), (cx + 3, h // 2), (cx, h // 2 + 3), (cx - 3, h // 2)])
    s.blit(t, t.get_rect(center=(w // 2, h // 2 - 3)))
    return s
  return _cache(('plaque', label, size), build)


def torch(surf, x, y, anim, ph=0.0, big=1.0):
  fl = 3 * math.sin(anim * 9 + ph)
  pygame.draw.rect(surf, (60, 34, 16), (x - 3, y, 6, int(30 * big)))
  pygame.draw.rect(surf, (90, 56, 24), (x - 4, y - 2, 8, 5))
  add_glow(surf, x, y - 6, int(40 * big), (130, 60, 8))
  pygame.draw.polygon(surf, (255, 120, 20), [(x - 7 * big, y + 2), (x, y - (20 + fl) * big), (x + 7 * big, y + 2)])
  pygame.draw.polygon(surf, FIRE_CORE, [(x - 3 * big, y + 2), (x, y - (9 + fl) * big), (x + 3 * big, y + 2)])


def draw_title(surf, label, cy, anim, torches=True):
  p = title_plaque(label)
  r = p.get_rect(center=(WIDTH // 2, cy))
  add_glow(surf, WIDTH // 2, cy, max(80, r.w // 2), (40, 16, 6))
  if torches:
    torch(surf, r.left - 18, cy - 6, anim, 0.0)
    torch(surf, r.right + 18, cy - 6, anim, 2.0)
  surf.blit(p, r)
  k = (math.sin(anim * 3) + 1) / 2                   # twinkles, like the main title
  for sx, ph in ((-0.36, 0.0), (0.3, 1.7)):
    rr = int(2 + 4 * ((math.sin(anim * 3 + ph) + 1) / 2))
    cx, cy2 = int(r.centerx + sx * r.w), r.top + 10
    pygame.draw.line(surf, (255, 244, 190), (cx - rr, cy2), (cx + rr, cy2), 1)
    pygame.draw.line(surf, (255, 244, 190), (cx, cy2 - rr), (cx, cy2 + rr), 1)
  return r


# ---------------------------------------------------------------- icon tab bar
TABS = [('home', 'Home'), ('lair', 'Den'), ('roster', 'Roster'), ('hoard', 'Hoard'), ('quests', 'Quests'),
        ('enemies', 'Bestiary'), ('eggs', 'Eggs'), ('hatchlings', 'Babies'), ('options', 'Options')]
TAB_OF_STATE = {'LAIR': 'lair', 'SELECT': 'roster', 'RARE_SELECT': 'roster', 'HOARD': 'hoard', 'QUESTS': 'quests',
                'ENEMIES': 'enemies', 'EGGS': 'eggs', 'ROOSTS': 'eggs', 'HATCHLINGS': 'hatchlings', 'OPTIONS': 'options'}
TAB_W, TAB_H = 74, 56
TAB_BAR = pygame.Rect(WIDTH // 2 - (len(TABS) * TAB_W + 24) // 2, HEIGHT - TAB_H - 2, len(TABS) * TAB_W + 24, TAB_H)


def tab_rects():
  return [(k, lab, pygame.Rect(TAB_BAR.x + 12 + i * TAB_W, TAB_BAR.y, TAB_W, TAB_H)) for i, (k, lab) in enumerate(TABS)]


def tab_bar_shown(game):
  st = game.state
  if st not in TAB_OF_STATE or getattr(game, 'pending', None):
    return False
  if st == 'OPTIONS' and getattr(game, 'opt_from', 'MENU') == 'PAUSED':
    return False
  return True


def _icon(name, col):
  def build():
    s = pygame.Surface((34, 34), pygame.SRCALPHA)
    c, d = col, tuple(int(v * 0.45) for v in col)
    if name == 'home':                               # castle
      pygame.draw.rect(s, c, (7, 14, 20, 14))
      for x in (7, 13, 19, 25):
        pygame.draw.rect(s, c, (x - 1, 10, 4, 5))
      pygame.draw.rect(s, d, (14, 20, 6, 8))
      pygame.draw.polygon(s, c, [(17, 2), (22, 9), (12, 9)])
    elif name == 'lair':                             # cave + fire
      pygame.draw.polygon(s, c, [(2, 30), (6, 12), (17, 4), (28, 12), (32, 30)])
      pygame.draw.polygon(s, (20, 14, 10), [(9, 30), (11, 18), (17, 12), (23, 18), (25, 30)])
      pygame.draw.polygon(s, (255, 140, 30), [(13, 30), (17, 19), (21, 30)])
      pygame.draw.polygon(s, (255, 230, 120), [(15, 30), (17, 24), (19, 30)])
    elif name == 'roster':                           # dragon head
      pygame.draw.polygon(s, c, [(4, 22), (12, 12), (24, 10), (31, 16), (26, 20), (31, 25), (20, 26), (12, 30)])
      pygame.draw.polygon(s, c, [(12, 12), (9, 3), (16, 10)])
      pygame.draw.polygon(s, c, [(18, 10), (19, 2), (22, 10)])
      pygame.draw.circle(s, (255, 80, 40), (21, 15), 2)
    elif name == 'hoard':                            # anvil + hammer
      pygame.draw.polygon(s, c, [(3, 14), (27, 14), (31, 11), (31, 18), (24, 20), (22, 25), (12, 25), (10, 20), (3, 18)])
      pygame.draw.rect(s, c, (9, 25, 16, 5))
      pygame.draw.line(s, d, (8, 4), (20, 12), 3)
      pygame.draw.rect(s, c, (4, 1, 8, 6))
    elif name == 'quests':                           # scroll
      pygame.draw.rect(s, c, (7, 6, 20, 22))
      pygame.draw.ellipse(s, d, (4, 3, 26, 7))
      pygame.draw.ellipse(s, d, (4, 25, 26, 7))
      for y in (12, 16, 20):
        pygame.draw.line(s, d, (11, y), (23, y), 1)
    elif name == 'enemies':                          # book
      pygame.draw.rect(s, c, (5, 6, 24, 23), border_radius=2)
      pygame.draw.rect(s, d, (5, 6, 5, 23))
      pygame.draw.circle(s, d, (19, 15), 4)
      pygame.draw.line(s, d, (13, 23), (25, 23), 2)
    elif name == 'eggs':                             # egg
      pygame.draw.ellipse(s, c, (8, 3, 18, 27))
      pygame.draw.ellipse(s, (255, 255, 240), (12, 8, 5, 7))
      for x, y in ((18, 18), (14, 22), (20, 12)):
        pygame.draw.circle(s, d, (x, y), 1)
    elif name == 'hatchlings':                       # paw
      pygame.draw.ellipse(s, c, (9, 15, 16, 14))
      for x, y in ((7, 10), (13, 5), (21, 5), (27, 10)):
        pygame.draw.ellipse(s, c, (x - 3, y - 3, 7, 8))
    elif name == 'options':                          # gear
      for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(s, c, (17, 17), (int(17 + math.cos(a) * 14), int(17 + math.sin(a) * 14)), 5)
      pygame.draw.circle(s, c, (17, 17), 10)
      pygame.draw.circle(s, d, (17, 17), 4)
    return s
  return _cache(('icon', name, col), build)


def draw_tab_bar(surf, active, anim, mouse, badges=()):
  if art_ok():
    return draw_art_tab_bar(surf, active, anim, mouse, badges)
  surf.blit(stone_surface(TAB_BAR.w, TAB_BAR.h), TAB_BAR.topleft)
  f = _small_label_font()
  for k, lab, r in tab_rects():
    on = k == active
    hov = r.collidepoint(mouse)
    cx = r.centerx
    cy = r.top + 19 - (4 if on else 0) - (1 if hov and not on else 0)
    if on:
      pulse = (math.sin(anim * 4) + 1) / 2
      add_glow(surf, cx, cy, 30 + int(pulse * 6), (90, 60, 10))
    pygame.draw.circle(surf, (10, 8, 12), (cx + 1, cy + 2), 19)
    pygame.draw.circle(surf, (44, 40, 52) if not on else (70, 40, 20), (cx, cy), 18)
    pygame.draw.circle(surf, GOLD_L if (on or hov) else GOLD, (cx, cy), 18, 2)
    pygame.draw.circle(surf, GOLD_D, (cx, cy), 15, 1)
    ic = _icon(k, (255, 220, 120) if on else ((240, 232, 210) if hov else (190, 180, 160)))
    surf.blit(ic, ic.get_rect(center=(cx, cy)))
    img = text(f, lab, BANNER_GOLD if on else (200, 190, 170))
    surf.blit(img, img.get_rect(center=(cx, r.bottom - 12)))
    if k in badges:
      draw_badge(surf, cx + 14, cy - 15, anim)


def _small_label_font():
  f = _C.get('lblfont')
  if f is None:
    f = _C['lblfont'] = pygame.font.SysFont("serif", 13, bold=True)
  return f


def draw_badge(surf, x, y, anim):
  r = 8 + int(abs(math.sin(anim * 5)) * 2)
  pygame.draw.circle(surf, (120, 10, 10), (x, y), r + 2)
  pygame.draw.circle(surf, (230, 40, 30), (x, y), r)
  pygame.draw.rect(surf, (255, 255, 255), (x - 1, y - 5, 3, 6))
  pygame.draw.rect(surf, (255, 255, 255), (x - 1, y + 3, 3, 2))


# ---------------------------------------------------------------- the Den: a dragon's cave
def _rock_blob(s, rng, x, y, r, col):
  pts = []
  n = rng.randint(7, 11)
  for i in range(n):
    a = i * math.tau / n
    rr = r * rng.uniform(0.7, 1.15)
    pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.8))
  pygame.draw.polygon(s, col, pts)
  hi = tuple(min(255, v + 14) for v in col)
  pygame.draw.lines(s, hi, False, pts[n // 2 + 1:] + pts[:1], 2)


def cave_backdrop():
  def build():
    rng = random.Random(77)
    s = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):                           # warm dark rock, lit from the fire below
      t = y / float(HEIGHT)
      s.fill((int(22 + 30 * t), int(16 + 18 * t), int(16 + 10 * t)), (0, y, WIDTH, 1))
    for _ in range(140):                              # boulders in the walls
      x, y = rng.randint(-40, WIDTH + 40), rng.randint(-20, HEIGHT)
      v = rng.randint(-6, 10)
      _rock_blob(s, rng, x, y, rng.randint(20, 70), (36 + v, 28 + v, 26 + v))
    for _ in range(900):                              # grit
      v = rng.randint(30, 70)
      s.set_at((rng.randint(0, WIDTH - 1), rng.randint(0, HEIGHT - 1)), (v, v - 8, v - 12))
    # arched cave opening framing the room
    arch = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pts = [(0, 0), (WIDTH, 0), (WIDTH, HEIGHT)]
    for k in range(41):
      a = math.pi * k / 40.0
      pts.append((WIDTH / 2 + math.cos(a) * WIDTH * 0.56, HEIGHT + 30 - math.sin(a) * (HEIGHT * 1.02) + rng.uniform(-10, 10)))
    pts += [(0, HEIGHT)]
    pygame.draw.polygon(arch, (14, 10, 10, 255), pts)
    s.blit(arch, (0, 0))
    for _ in range(46):                               # stalactites along the ceiling
      x = rng.randint(0, WIDTH)
      top = 0
      ln = rng.randint(18, 70)
      w = rng.randint(8, 20)
      c = rng.randint(24, 40)
      pygame.draw.polygon(s, (c, c - 6, c - 8), [(x - w, top), (x + w, top), (x + rng.randint(-3, 3), top + ln)])
      pygame.draw.line(s, (c + 18, c + 10, c + 6), (x - w // 2, top), (x, top + ln - 4), 1)
    # floor
    fy = HEIGHT - 90
    pygame.draw.rect(s, (30, 22, 18), (0, fy, WIDTH, 90))
    for _ in range(60):
      _rock_blob(s, rng, rng.randint(0, WIDTH), rng.randint(fy, HEIGHT), rng.randint(8, 26), (40 + rng.randint(-6, 6), 30, 24))
    # the hoard: a mound of gold in the middle
    cx, gy = WIDTH // 2, HEIGHT - 185
    for k in range(9):
      rw, rh = 300 - k * 26, 120 - k * 11
      col = (150 + k * 9, 104 + k * 9, 20 + k * 4)
      pygame.draw.ellipse(s, col, (cx - rw // 2, gy - rh // 2 + 40 - k * 5, rw, rh))
    for _ in range(420):                              # coins
      a, r = rng.uniform(0, math.tau), rng.random() ** 0.6
      x, y = int(cx + math.cos(a) * r * 140), int(gy + 30 + math.sin(a) * r * 50 - (1 - r) * 40)
      c = rng.choice(((255, 214, 80), (230, 170, 40), (200, 140, 30), (255, 236, 150)))
      pygame.draw.ellipse(s, (120, 80, 14), (x - 4, y - 2, 9, 5))
      pygame.draw.ellipse(s, c, (x - 4, y - 3, 8, 4))
    for _ in range(26):                               # gems and goblets
      a, r = rng.uniform(0, math.tau), rng.random() ** 0.7
      x, y = int(cx + math.cos(a) * r * 130), int(gy + 26 + math.sin(a) * r * 44 - (1 - r) * 36)
      c = rng.choice(((220, 40, 60), (60, 150, 255), (60, 220, 120), (200, 90, 255)))
      pygame.draw.polygon(s, c, [(x, y - 5), (x + 4, y), (x, y + 4), (x - 4, y)])
      s.set_at((x - 1, y - 2), (255, 255, 255))
    for gx in (cx - 100, cx + 92):
      pygame.draw.polygon(s, (230, 180, 60), [(gx - 8, gy + 10), (gx + 8, gy + 10), (gx + 4, gy + 24), (gx - 4, gy + 24)])
      pygame.draw.rect(s, (200, 150, 40), (gx - 2, gy + 24, 4, 8))
      pygame.draw.rect(s, (230, 180, 60), (gx - 7, gy + 32, 14, 3))
    # a wooden beam across the cave that the signs hang from
    pygame.draw.rect(s, (52, 32, 16), (0, 104, WIDTH, 14))
    pygame.draw.rect(s, (82, 52, 26), (0, 104, WIDTH, 4))
    for x in range(0, WIDTH, 90):
      pygame.draw.circle(s, (40, 28, 20), (x + 20, 111), 3)
    return s.convert()
  return _cache(('cave', WIDTH, HEIGHT), build)


def _sign(label, w, h, hover):
  def build():
    rng = random.Random(len(label) * 31 + w)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    base = (118, 74, 36) if not hover else (140, 90, 44)
    pygame.draw.rect(s, (40, 22, 10), (0, 0, w, h), border_radius=8)
    for i in range(3):                                # three planks
      y0 = 4 + i * (h - 8) // 3
      ph = (h - 8) // 3 - 1
      v = rng.randint(-10, 10)
      c = (base[0] + v, base[1] + v, base[2] + v // 2)
      pygame.draw.rect(s, c, (4, y0, w - 8, ph), border_radius=3)
      for _ in range(5):                              # grain
        yy = y0 + rng.randint(2, max(3, ph - 3))
        pygame.draw.line(s, (c[0] - 22, c[1] - 16, c[2] - 8), (8 + rng.randint(0, 20), yy), (w - 8 - rng.randint(0, 30), yy), 1)
    for cx, cy in ((10, 10), (w - 10, 10), (10, h - 10), (w - 10, h - 10)):    # iron nails
      pygame.draw.circle(s, (40, 40, 44), (cx, cy), 4)
      pygame.draw.circle(s, (150, 150, 160), (cx - 1, cy - 1), 1)
    pygame.draw.rect(s, GOLD if hover else (70, 44, 20), (0, 0, w, h), 2, border_radius=8)
    for sz in (24, 22, 20, 18, 16):
      t = small_fire(label, sz)
      if t.get_width() <= w - 66:
        break
    s.blit(t, t.get_rect(center=(w // 2 + 16, h // 2 - 2)))
    return s
  return _cache(('sign', label, w, h, hover), build)


LAIR_ICONS = {'roster': 'roster', 'hoard': 'hoard', 'quests': 'quests', 'enemies': 'enemies', 'eggs': 'eggs', 'hatchlings': 'hatchlings'}
LAIR_LABELS = {'roster': 'DRAGON ROSTER', 'hoard': 'THE HOARD', 'quests': 'QUESTS', 'enemies': 'BESTIARY', 'eggs': 'THE HATCHERY', 'hatchlings': 'HATCHLINGS'}


def draw_den(surf, game, anim):
  surf.blit(cave_backdrop(), (0, 0))
  cx, gy = WIDTH // 2, HEIGHT - 185
  t = anim
  # wall torches
  for i, tx in enumerate((70, WIDTH - 70)):
    torch(surf, tx, 210, t, i * 2.3, 1.3)
  # warm light from the fire pit
  fx, fy = cx - 250, HEIGHT - 76
  fl = (math.sin(t * 11) + math.sin(t * 7.3)) * 0.5
  add_glow(surf, fx, fy - 30, 260 + int(fl * 12), (70, 34, 8))
  add_glow(surf, cx, gy, 170, (80, 56, 10))
  # the selected dragon, asleep on the gold
  from fd_art import draw_any_dragon
  bob = int(math.sin(t * 1.6) * 2)
  draw_any_dragon(surf, game.selected, cx - 32, gy - 40 + bob, 0, 0.0, False)
  for k in range(3):                                  # z z z
    ph = (t * 0.45 + k / 3.0) % 1.0
    zx, zy = cx + 54 + int(ph * 40) + int(math.sin(ph * 6) * 6), gy - 60 - int(ph * 70)
    z = text(_z_font(10 + k * 4 + int(ph * 6)), "z", (230, 220, 255))
    z.set_alpha(int(255 * (1 - ph)))
    surf.blit(z, (zx, zy))
  # gold glints
  for k in range(5):
    ph = (t * 0.8 + k * 0.37) % 1.0
    if ph < 0.25:
      sx, sy = cx - 120 + k * 58, gy + 10 + (k % 2) * 22
      rr = int(1 + 5 * math.sin(ph / 0.25 * math.pi))
      pygame.draw.line(surf, (255, 250, 210), (sx - rr, sy), (sx + rr, sy), 1)
      pygame.draw.line(surf, (255, 250, 210), (sx, sy - rr), (sx, sy + rr), 1)
  # crackling fire pit beside the hoard
  campfire(surf, fx, fy, t)
  for k in range(9):                                  # embers
    ph = (t * 0.6 + k * 0.113) % 1.0
    ex = fx + math.sin(k * 2.1 + ph * 5) * (20 + 30 * ph)
    ey = fy - 40 - ph * 150
    pygame.draw.circle(surf, (255, int(200 - 120 * ph), 60), (int(ex), int(ey)), 2 if ph < 0.5 else 1)
  # hanging signs on chains
  for k, label, col, bg, border in LAIR_ITEMS:
    r = LAIR_RECTS[k]
    hov = r.collidepoint(game.mouse)
    sway = math.sin(t * 1.3 + r.y * 0.05 + r.x * 0.01) * 3
    sx = r.x + int(sway)
    for ax in (r.x + 30, r.right - 30):              # chains up to the beam (or to the sign above)
      top = 116 if r.y < 200 else r.y - 50
      for yy in range(top, r.y + 2, 8):
        u = (yy - top) / float(max(1, r.y - top))
        xx = int(ax + sway * u)
        pygame.draw.ellipse(surf, (110, 104, 96), (xx - 2, yy, 5, 8), 1)
    if hov:
      add_glow(surf, r.centerx, r.centery, r.w // 2 + 10, (90, 50, 10))
    surf.blit(_sign(LAIR_LABELS.get(k, label), r.w, r.h, hov), (sx, r.y))
    ic = _icon(LAIR_ICONS.get(k, 'roster'), (255, 226, 150))
    surf.blit(ic, ic.get_rect(center=(sx + 28, r.centery)))
    if k == 'eggs' and game.eggs_ready():
      draw_badge(surf, sx + r.w - 8, r.y + 6, t)
  # hanging lanterns between the signs
  for lx in (WIDTH // 2 - 165, WIDTH // 2 + 165):
    ly = 236 + int(math.sin(t * 1.1 + lx) * 3)
    pygame.draw.line(surf, (90, 84, 76), (lx, 118), (lx, ly - 14), 2)
    add_glow(surf, lx, ly, 46 + int(fl * 4), (110, 70, 14))
    pygame.draw.rect(surf, (40, 30, 20), (lx - 9, ly - 14, 18, 4))
    pygame.draw.rect(surf, (255, 200, 90), (lx - 7, ly - 10, 14, 20), border_radius=3)
    pygame.draw.rect(surf, (60, 40, 20), (lx - 7, ly - 10, 14, 20), 2, border_radius=3)
    pygame.draw.rect(surf, (40, 30, 20), (lx - 9, ly + 10, 18, 4))


def campfire(surf, fx, fy, t, sc=1.0, stones=True):
  """logs in a ring of stones with flickering tongues of flame (stones=False: just the flames, for painted fire pits)"""
  if stones:
    pygame.draw.ellipse(surf, (20, 14, 12), (fx - 64 * sc, fy - 6, 128 * sc, 26))
    for k in range(8):
      a = k / 8.0 * math.tau
      pygame.draw.ellipse(surf, (74, 70, 74), (fx + math.cos(a) * 56 * sc - 11, fy + 6 + math.sin(a) * 9 - 6, 22, 13))
      pygame.draw.ellipse(surf, (110, 106, 110), (fx + math.cos(a) * 56 * sc - 7, fy + 4 + math.sin(a) * 9 - 6, 10, 5))
    pygame.draw.line(surf, (70, 40, 20), (fx - 38 * sc, fy + 8), (fx + 34 * sc, fy - 2), int(9 * sc))
    pygame.draw.line(surf, (96, 56, 26), (fx - 34 * sc, fy - 3), (fx + 38 * sc, fy + 8), int(9 * sc))
  add_glow(surf, fx, fy - 26, int(90 * sc), (120, 50, 6))
  for layer, (col, hs, ws) in enumerate((((200, 50, 14), 1.0, 1.0), ((255, 128, 24), 0.74, 0.8), ((255, 226, 110), 0.45, 0.55))):
    for j in range(5):                                # separate tongues of flame
      u = (j - 2) / 2.0
      bx = fx + u * 26 * sc * ws
      h = (70 - abs(u) * 22 + 16 * math.sin(t * 10 + j * 1.9 + layer)) * hs * sc
      sway = math.sin(t * 6 + j) * 6 * sc
      wb = 15 * sc * ws
      pygame.draw.polygon(surf, col, [(bx - wb, fy + 4), (bx - wb * 0.5 + sway * 0.4, fy - h * 0.55), (bx + sway, fy - h),
                                      (bx + wb * 0.5 + sway * 0.4, fy - h * 0.55), (bx + wb, fy + 4)])


def fire_flames(surf, fx, fy, t, sc=1.0):
  """a full, flickering fire: layered tongues from deep red to a white-hot core, with sparks"""
  add_glow(surf, fx, fy - int(30 * sc), int(110 * sc), (120, 50, 6))
  add_glow(surf, fx, fy - int(20 * sc), int(50 * sc), (120, 80, 20))
  layers = (((170, 30, 10), 1.0, 1.0, 9), ((235, 80, 16), 0.86, 0.85, 8), ((255, 150, 30), 0.68, 0.68, 7),
            ((255, 210, 80), 0.48, 0.5, 6), ((255, 246, 200), 0.26, 0.3, 4))
  for li, (col, hs, ws, n) in enumerate(layers):
    for j in range(n):
      u = (j - (n - 1) / 2.0) / max(1.0, (n - 1) / 2.0)
      bx = fx + u * 40 * sc * ws
      h = (92 - abs(u) * 44 + 18 * math.sin(t * 9.5 + j * 1.7 + li * 0.9) + 8 * math.sin(t * 17 + j)) * hs * sc
      sway = (math.sin(t * 5.5 + j * 1.3) * 7 + math.sin(t * 11 + li) * 2) * sc
      wb = (15 - abs(u) * 4) * sc * ws
      pts = [(bx - wb, fy + 6), (bx - wb * 0.8 + sway * 0.2, fy - h * 0.3), (bx - wb * 0.45 + sway * 0.55, fy - h * 0.62),
             (bx + sway, fy - h), (bx + wb * 0.45 + sway * 0.6, fy - h * 0.6), (bx + wb * 0.8 + sway * 0.25, fy - h * 0.28), (bx + wb, fy + 6)]
      pygame.draw.polygon(surf, col, pts)
  for j in range(6):                                  # sparks flicking up out of the flames
    ph = (t * 1.3 + j * 0.17) % 1.0
    sx = fx + math.sin(j * 3.1 + t * 2) * 24 * sc + (ph - 0.5) * 10
    sy = fy - (40 + ph * 120) * sc
    pygame.draw.circle(surf, (255, int(240 - 140 * ph), int(140 - 100 * ph)), (int(sx), int(sy)), 2 if ph < 0.4 else 1)


def _z_font(n):
  k = ('zf', n)
  f = _C.get(k)
  if f is None:
    f = _C[k] = pygame.font.SysFont("serif", n, bold=True)
  return f


# ---------------------------------------------------------------- the Hatchery: stone hearths and iron cradles
def hatchery_backdrop():
  def build():
    rng = random.Random(41)
    s = pygame.Surface((WIDTH, HEIGHT))
    s.fill((26, 16, 12))
    _bricks(s, 0, 0, WIDTH, HEIGHT - 70, rng, (70, 38, 28), 20)          # warm brick walls
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
      a = int(150 * (1 - y / float(HEIGHT)) ** 1.5)
      shade.fill((10, 4, 2, a), (0, y, WIDTH, 1))
    s.blit(shade, (0, 0))
    fy = HEIGHT - 70
    for i in range(0, WIDTH, 48):                    # plank floor
      v = rng.randint(-8, 8)
      pygame.draw.rect(s, (74 + v, 46 + v, 24), (i, fy, 47, 70))
      pygame.draw.line(s, (40, 24, 12), (i, fy), (i, HEIGHT))
    pygame.draw.rect(s, (40, 24, 12), (0, fy, WIDTH, 4))
    for x in range(40, WIDTH, 260):                  # copper pipes along the wall
      pygame.draw.rect(s, (120, 70, 36), (x, 0, 10, fy))
      pygame.draw.rect(s, (170, 110, 60), (x + 2, 0, 3, fy))
      for y in range(60, fy, 140):
        pygame.draw.rect(s, (90, 50, 26), (x - 3, y, 16, 8))
    return s.convert()
  return _cache(('hatchery', WIDTH, HEIGHT), build)


def hearth_surface(w, h, lit=True):
  """a stone fireplace with an arched opening"""
  def build():
    rng = random.Random(w + h * 3)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 16, 16), (0, 0, w, h), border_radius=10)
    _bricks(s, 4, 4, w - 8, h - 8, rng, (74, 68, 70), 18)
    ox0, ox1 = 22, w - 22
    oy0, oy1 = 46, h - 12
    rad = (ox1 - ox0) // 2
    pts = [(ox0, oy1)]
    for k in range(21):
      a = math.pi * k / 20.0
      pts.append((w // 2 - math.cos(a) * rad, oy0 + rad - math.sin(a) * rad))
    pts.append((ox1, oy1))
    pygame.draw.polygon(s, (14, 8, 6), pts)                                   # opening
    pygame.draw.lines(s, (120, 112, 112), False, pts[1:-1], 4)                 # arch stones
    for k in range(0, 21, 3):
      a = math.pi * k / 20.0
      x0, y0 = w // 2 - math.cos(a) * rad, oy0 + rad - math.sin(a) * rad
      x1, y1 = w // 2 - math.cos(a) * (rad + 12), oy0 + rad - math.sin(a) * (rad + 12)
      pygame.draw.line(s, (40, 34, 34), (x0, y0), (x1, y1), 2)
    pygame.draw.rect(s, (96, 88, 90), (0, oy1 - 2, w, 14), border_radius=3)    # hearthstone
    pygame.draw.rect(s, (130, 122, 124), (0, oy1 - 2, w, 3))
    if lit:
      for _ in range(18):                                                      # coals
        x, y = rng.randint(ox0 + 8, ox1 - 8), rng.randint(oy1 - 16, oy1 - 4)
        pygame.draw.circle(s, rng.choice(((200, 60, 10), (255, 120, 20), (120, 30, 10))), (x, y), rng.randint(2, 4))
    pygame.draw.rect(s, GOLD_D, (0, 0, w, h), 3, border_radius=10)
    return s.convert_alpha()
  return _cache(('hearth', w, h, lit), build)


def hearth_fire(surf, cx, by, t, w):
  add_glow(surf, cx, by - 20, w // 2 + 10, (110, 46, 6))
  for layer, (col, hs) in enumerate((((210, 60, 14), 1.0), ((255, 140, 30), 0.7), ((255, 230, 120), 0.4))):
    for j in range(4):
      u = (j - 1.5) / 1.5
      bx = cx + u * w * 0.26
      hh = (30 - abs(u) * 8 + 8 * math.sin(t * 11 + j * 2.1 + layer)) * hs
      sway = math.sin(t * 7 + j) * 3
      pygame.draw.polygon(surf, col, [(bx - 9, by), (bx + sway, by - hh), (bx + 9, by)])


def cradle(surf, cx, cy, w=70, front=False):
  """iron basket the egg sits in: draw the back (rim and legs), then the egg, then the front"""
  hw = w // 2
  if not front:
    for lx in (-hw + 8, hw - 8):                       # legs
      pygame.draw.line(surf, (30, 30, 34), (cx + lx, cy + 10), (cx + lx * 1.25, cy + 36), 4)
    pygame.draw.line(surf, (30, 30, 34), (cx, cy + 16), (cx, cy + 38), 4)
    pygame.draw.ellipse(surf, (34, 34, 40), (cx - hw, cy - 6, w, 14), 3)       # back of the rim
    return
  bowl = pygame.Rect(cx - hw, cy - 18, w, 40)
  pygame.draw.arc(surf, (24, 24, 28), bowl, math.pi, 2 * math.pi, 5)         # bottom of the basket
  pygame.draw.arc(surf, (120, 120, 132), bowl.move(0, -1), math.pi * 1.1, math.pi * 1.9, 1)
  for k in range(1, 6):                                # vertical bars
    x = cx - hw + k * w / 6.0
    u = (x - cx) / float(hw)
    yb = cy + 2 + int(18 * math.sqrt(max(0.0, 1 - u * u)))
    pygame.draw.line(surf, (44, 44, 50), (x, cy + 1), (x, yb), 3)
    pygame.draw.line(surf, (110, 110, 122), (x - 1, cy + 2), (x - 1, yb - 2), 1)
  pygame.draw.ellipse(surf, (40, 40, 46), (cx - hw - 2, cy - 4, w + 4, 10), 3)  # front of the rim
  pygame.draw.arc(surf, (150, 150, 160), (cx - hw - 2, cy - 4, w + 4, 10), math.pi * 1.1, math.pi * 1.9, 1)


def steam(surf, cx, cy, t, n=4, spread=18):
  for k in range(n):
    ph = (t * 0.5 + k / float(n)) % 1.0
    x = cx + math.sin(ph * 6 + k * 2) * spread * ph
    y = cy - ph * 70
    r = int(4 + ph * 10)
    a = int(110 * (1 - ph))
    key = ('steam', r)
    s = _C.get(key)
    if s is None:
      s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
      pygame.draw.circle(s, (235, 235, 240, 255), (r + 1, r + 1), r)
      _C[key] = s
    s2 = s.copy()
    s2.set_alpha(a)
    surf.blit(s2, (int(x) - r, int(y) - r))


def brass_plate(w, h):
  def build():
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
      t = y / float(max(1, h - 1))
      c = (int(196 - 70 * t), int(150 - 60 * t), int(60 - 30 * t))
      pygame.draw.line(s, c, (2, y), (w - 3, y))
    pygame.draw.rect(s, (90, 60, 20), (0, 0, w, h), 2, border_radius=6)
    pygame.draw.rect(s, (255, 230, 150), (3, 3, w - 6, h - 6), 1, border_radius=4)
    for cx in (8, w - 8):
      pygame.draw.circle(s, (110, 76, 24), (cx, h // 2), 3)
      pygame.draw.circle(s, (250, 220, 140), (cx - 1, h // 2 - 1), 1)
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(m, (255, 255, 255, 255), (0, 0, w, h), border_radius=6)
    s.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return s.convert_alpha()
  return _cache(('brass', w, h), build)


# ---------------------------------------------------------------- the Hoard: a blacksmith's forge
def forge_backdrop():
  def build():
    rng = random.Random(9)
    s = pygame.Surface((WIDTH, HEIGHT))
    s.fill((16, 14, 16))
    _bricks(s, 0, 0, WIDTH, HEIGHT - 80, rng, (46, 42, 46), 22)
    fy = HEIGHT - 80
    for i in range(0, WIDTH, 64):                    # flagstone floor
      v = rng.randint(-6, 6)
      pygame.draw.rect(s, (52 + v, 48 + v, 50 + v), (i + 1, fy + 1, 62, 78))
    pygame.draw.rect(s, (20, 18, 20), (0, fy, WIDTH, 3))
    cx = WIDTH // 2                                  # the great forge at the back
    hood = [(cx - 150, 120), (cx - 70, 30), (cx + 70, 30), (cx + 150, 120)]
    pygame.draw.polygon(s, (60, 56, 60), hood)
    pygame.draw.polygon(s, (90, 86, 90), hood, 3)
    pygame.draw.rect(s, (70, 66, 70), (cx - 170, 120, 340, 200), border_radius=8)
    _bricks(s, cx - 166, 124, 332, 192, rng, (78, 72, 76), 18)
    pygame.draw.rect(s, (12, 8, 8), (cx - 120, 180, 240, 110), border_radius=40)
    pygame.draw.rect(s, (110, 100, 104), (cx - 124, 176, 248, 118), 4, border_radius=42)
    for x in range(cx - 110, cx + 110, 8):           # glowing coal bed
      for y in range(256, 288, 7):
        c = rng.choice(((200, 60, 10), (255, 120, 20), (120, 30, 10), (255, 180, 60)))
        pygame.draw.circle(s, c, (x + rng.randint(-2, 2), y), rng.randint(2, 4))
    for tx, kind in ((70, 'hammer'), (130, 'tongs'), (WIDTH - 130, 'hammer'), (WIDTH - 70, 'tongs')):   # tools on the wall
      pygame.draw.circle(s, (30, 26, 26), (tx, 120), 4)
      if kind == 'hammer':
        pygame.draw.line(s, (70, 46, 24), (tx, 124), (tx, 200), 6)
        pygame.draw.rect(s, (90, 90, 98), (tx - 16, 196, 32, 16))
      else:
        pygame.draw.line(s, (80, 80, 88), (tx - 4, 124), (tx - 10, 210), 4)
        pygame.draw.line(s, (80, 80, 88), (tx + 4, 124), (tx + 10, 210), 4)
    return s.convert()
  return _cache(('forge', WIDTH, HEIGHT), build)


def forge_fire(surf, t):
  cx = WIDTH // 2
  fl = (math.sin(t * 9) + math.sin(t * 13.7)) * 0.5
  add_glow(surf, cx, 250, 200 + int(fl * 14), (120, 50, 6))
  hearth_fire(surf, cx, 280, t, 230)
  for k in range(12):                                # sparks drifting up out of the forge
    ph = (t * 0.7 + k * 0.083) % 1.0
    x = cx + math.sin(k * 1.7 + ph * 4) * (40 + 70 * ph)
    y = 260 - ph * 230
    pygame.draw.circle(surf, (255, int(220 - 150 * ph), 60), (int(x), int(y)), 2 if ph < 0.4 else 1)


def anvil(surf, cx, top):
  """an anvil whose flat face is at y = top"""
  pts = [(cx - 72, top), (cx + 52, top), (cx + 74, top - 6), (cx + 74, top + 6), (cx + 44, top + 16), (cx + 30, top + 28),
         (cx - 30, top + 28), (cx - 44, top + 16), (cx - 72, top + 12)]
  pygame.draw.polygon(surf, (40, 40, 46), pts)
  pygame.draw.polygon(surf, (90, 92, 104), [(cx - 72, top), (cx + 52, top), (cx + 74, top - 6), (cx + 74, top - 1), (cx + 52, top + 4), (cx - 72, top + 4)])
  pygame.draw.lines(surf, (140, 142, 156), False, [(cx - 72, top), (cx + 52, top), (cx + 74, top - 6)], 2)
  pygame.draw.rect(surf, (34, 34, 40), (cx - 26, top + 28, 52, 24))
  pygame.draw.polygon(surf, (40, 40, 46), [(cx - 44, top + 62), (cx + 44, top + 62), (cx + 30, top + 50), (cx - 30, top + 50)])
  pygame.draw.rect(surf, (60, 40, 22), (cx - 50, top + 62, 100, 14))        # wooden block
  pygame.draw.rect(surf, (90, 60, 32), (cx - 50, top + 62, 100, 4))


def ingot(surf, x, y, lit):
  c1, c2 = ((255, 214, 80), (190, 130, 30)) if lit else ((70, 64, 60), (44, 40, 38))
  pygame.draw.polygon(surf, c2, [(x - 14, y + 7), (x + 14, y + 7), (x + 10, y - 5), (x - 10, y - 5)])
  pygame.draw.polygon(surf, c1, [(x - 10, y - 5), (x + 10, y - 5), (x + 8, y - 1), (x - 8, y - 1)])
  if lit:
    add_glow(surf, x, y, 14, (90, 60, 10))


def metal_sign(w, h, label):
  def build():
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (30, 30, 36), (0, 0, w, h), border_radius=6)
    pygame.draw.rect(s, (70, 72, 82), (3, 3, w - 6, h - 6), border_radius=4)
    pygame.draw.rect(s, (110, 112, 124), (3, 3, w - 6, 3))
    for cx in (9, w - 9):
      pygame.draw.circle(s, (40, 40, 46), (cx, h // 2), 4)
      pygame.draw.circle(s, (160, 160, 170), (cx - 1, h // 2 - 1), 1)
    for sz in (22, 20, 18, 16):
      t = small_fire(label, sz)
      if t.get_width() <= w - 26:
        break
    s.blit(t, t.get_rect(center=(w // 2, h // 2 - 1)))
    return s.convert_alpha()
  return _cache(('msign', w, h, label), build)


def update_sparks(game):
  out = []
  for p in getattr(game, 'forge_sparks', ()):
    p[0] += p[2]; p[1] += p[3]; p[3] += 0.35; p[4] -= 1
    if p[4] > 0:
      out.append(p)
  game.forge_sparks = out


def spark_burst(game, x, y, n=40):
  sp = getattr(game, 'forge_sparks', [])
  for _ in range(n):
    a = random.uniform(math.pi * 1.05, math.pi * 1.95)
    v = random.uniform(3, 9)
    sp.append([float(x), float(y), math.cos(a) * v, math.sin(a) * v, random.randint(14, 30)])
  game.forge_sparks = sp


def draw_sparks(surf, game):
  for x, y, vx, vy, life in getattr(game, 'forge_sparks', ()):
    c = (255, 240, 160) if life > 18 else ((255, 170, 50) if life > 8 else (200, 80, 20))
    pygame.draw.line(surf, c, (int(x), int(y)), (int(x - vx), int(y - vy)), 2)


# ---------------------------------------------------------------- Quests: a tavern notice board
def tavern_backdrop():
  def build():
    rng = random.Random(5)
    s = pygame.Surface((WIDTH, HEIGHT))
    for x in range(0, WIDTH, 38):                    # plank wall
      v = rng.randint(-10, 10)
      c = (88 + v, 56 + v, 30 + v // 2)
      pygame.draw.rect(s, c, (x, 0, 37, HEIGHT))
      pygame.draw.line(s, (40, 24, 12), (x, 0), (x, HEIGHT), 2)
      for _ in range(6):
        y = rng.randint(0, HEIGHT)
        pygame.draw.line(s, (c[0] - 18, c[1] - 12, c[2] - 6), (x + rng.randint(4, 30), y), (x + rng.randint(4, 30), y + rng.randint(20, 60)), 1)
      for y in (40, HEIGHT - 120):
        pygame.draw.circle(s, (40, 30, 24), (x + 18, y), 2)
    pygame.draw.rect(s, (50, 30, 16), (0, HEIGHT - 70, WIDTH, 70))   # wainscot
    pygame.draw.rect(s, (70, 44, 22), (0, HEIGHT - 72, WIDTH, 6))
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
      shade.fill((12, 6, 2, int(120 * abs(y / float(HEIGHT) - 0.45))), (0, y, WIDTH, 1))
    s.blit(shade, (0, 0))
    for bx in (70, WIDTH - 130):                     # barrels
      pygame.draw.ellipse(s, (70, 42, 20), (bx, HEIGHT - 150, 70, 100))
      for yy in (HEIGHT - 128, HEIGHT - 76):
        pygame.draw.line(s, (40, 40, 44), (bx + 4, yy), (bx + 66, yy), 4)
    return s.convert()
  return _cache(('tavern', WIDTH, HEIGHT), build)


BOARD = pygame.Rect(WIDTH // 2 - 320, 96, 640, 430)


def cork_board():
  def build():
    rng = random.Random(3)
    w, h = BOARD.size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (60, 36, 18), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(s, (96, 62, 30), (4, 4, w - 8, h - 8), border_radius=6)
    pygame.draw.rect(s, (150, 104, 60), (18, 18, w - 36, h - 36))
    for _ in range(2600):                            # cork speckle
      c = rng.choice(((170, 120, 70), (130, 88, 48), (186, 140, 86), (118, 78, 40)))
      s.set_at((rng.randint(18, w - 19), rng.randint(18, h - 19)), c)
    for _ in range(18):                              # old pin holes and torn paper corners
      x, y = rng.randint(30, w - 30), rng.randint(30, h - 30)
      pygame.draw.circle(s, (80, 54, 30), (x, y), 2)
    pygame.draw.rect(s, (40, 22, 10), (18, 18, w - 36, h - 36), 3)
    for cx, cy in ((10, 10), (w - 10, 10), (10, h - 10), (w - 10, h - 10)):
      pygame.draw.circle(s, (40, 40, 44), (cx, cy), 5)
      pygame.draw.circle(s, (140, 140, 150), (cx - 1, cy - 1), 2)
    return s.convert_alpha()
  return _cache(('cork',), build)


def _ink_font(n):
  k = ('ink', n)
  f = _C.get(k)
  if f is None:
    f = _C[k] = pygame.font.SysFont("serif", n, bold=True)
  return f


def _wrap(f, txt, width):
  words, lines, cur = txt.split(), [], ''
  for w in words:
    test = (cur + ' ' + w).strip()
    if f.size(test)[0] > width and cur:
      lines.append(cur)
      cur = w
    else:
      cur = test
  if cur:
    lines.append(cur)
  return lines


def parchment(w, h, seed=1):
  rng = random.Random(seed)
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  pts = []
  for x in range(0, w + 1, 10):
    pts.append((x, rng.randint(0, 5)))
  for y in range(0, h + 1, 10):
    pts.append((w - rng.randint(0, 5), y))
  for x in range(w, -1, -10):
    pts.append((x, h - rng.randint(0, 5)))
  for y in range(h, -1, -10):
    pts.append((rng.randint(0, 5), y))
  pygame.draw.polygon(s, (226, 206, 160), pts)
  for _ in range(w * h // 40):
    c = rng.choice(((214, 192, 144), (236, 220, 178), (200, 176, 128)))
    s.set_at((rng.randint(6, w - 7), rng.randint(6, h - 7)), c)
  for k in range(10):                                # browned edges
    pygame.draw.lines(s, (196 - k * 2, 164 - k * 3, 110 - k * 3), True, [(px + (k if px < w / 2 else -k), py + (k if py < h / 2 else -k)) for px, py in pts[::3]], 1)
  return s


def quest_poster(q, gold, w, h, header, small=False):
  key = ('poster', q['desc'], q['progress'], q.get('done'), w, h, header)
  def build():
    s = parchment(w, h, len(q['desc']) + w)
    ink, red = (52, 30, 14), (150, 30, 20)
    f1, f2, f3 = _ink_font(16 if small else 20), _ink_font(18 if small else 24), _ink_font(14 if small else 17)
    hd = f1.render(header, True, red)
    s.blit(hd, hd.get_rect(center=(w // 2, 30)))
    pygame.draw.line(s, red, (30, 44), (w - 30, 44), 2)
    y = 58
    for ln in _wrap(f2, q['desc'], w - (70 if small else 40))[:3]:
      im = f2.render(ln, True, ink)
      s.blit(im, im.get_rect(midtop=(w // 2, y)))
      y += f2.get_height() + 2
    rw = f3.render("Reward: %d gold" % gold, True, (120, 76, 10))
    s.blit(rw, rw.get_rect(midtop=(w // 2, y + 6)))
    if not small:                                    # progress as an inked bar with notches
      bar = pygame.Rect(30, h - 62, w - 60, 18)
      pygame.draw.rect(s, (200, 178, 130), bar)
      frac = min(1.0, q['progress'] / float(max(1, q['target'])))
      if frac > 0:
        pygame.draw.rect(s, (60, 120, 40) if q.get('done') else (150, 40, 24), (bar.x, bar.y, int(bar.w * frac), bar.h))
      pygame.draw.rect(s, ink, bar, 2)
      for k in range(1, 10):
        x = bar.x + bar.w * k // 10
        pygame.draw.line(s, ink, (x, bar.bottom - 5), (x, bar.bottom), 1)
      pt = f3.render("{:,} / {:,}".format(min(q['progress'], q['target']), q['target']), True, ink)
      s.blit(pt, pt.get_rect(midtop=(w // 2, bar.bottom + 4)))
    if q.get('done'):                                # COMPLETE stamp
      st = pygame.Surface((220, 64), pygame.SRCALPHA)
      pygame.draw.rect(st, (190, 30, 20, 200), (0, 0, 220, 64), 5, border_radius=8)
      im = _ink_font(36).render("COMPLETE", True, (190, 30, 20))
      im.set_alpha(220)
      st.blit(im, im.get_rect(center=(110, 32)))
      st = pygame.transform.rotate(st, 14)
      s.blit(st, st.get_rect(center=(w // 2, h // 2 + 10)))
    return s
  return _cache(key, build)


def pin(surf, x, y, col=(190, 30, 30)):
  pygame.draw.circle(surf, (30, 10, 10), (x + 1, y + 2), 7)
  pygame.draw.circle(surf, col, (x, y), 7)
  pygame.draw.circle(surf, (255, 200, 200), (x - 2, y - 2), 2)


def wax_seal(surf, x, y):
  pygame.draw.circle(surf, (120, 16, 16), (x, y), 15)
  for k in range(10):
    a = k * math.tau / 10
    pygame.draw.circle(surf, (150, 24, 20), (int(x + math.cos(a) * 14), int(y + math.sin(a) * 14)), 4)
  pygame.draw.circle(surf, (170, 30, 24), (x, y), 11)
  pygame.draw.polygon(surf, (110, 14, 14), [(x, y - 7), (x + 6, y + 5), (x - 6, y + 5)], 2)


def draw_notice_board(surf, game, anim):
  surf.blit(tavern_backdrop(), (0, 0))
  for lx in (BOARD.left - 60, BOARD.right + 60):     # lanterns either side
    ly = 200 + int(math.sin(anim * 1.2 + lx) * 2)
    add_glow(surf, lx, ly, 70, (110, 70, 14))
    pygame.draw.line(surf, (40, 30, 20), (lx, 120), (lx, ly - 16), 2)
    pygame.draw.rect(surf, (40, 30, 20), (lx - 11, ly - 16, 22, 5))
    pygame.draw.rect(surf, (255, 206, 100), (lx - 9, ly - 11, 18, 24), border_radius=3)
    pygame.draw.rect(surf, (60, 40, 20), (lx - 9, ly - 11, 18, 24), 2, border_radius=3)
    fl = math.sin(anim * 9 + lx) * 2
    pygame.draw.polygon(surf, (255, 140, 30), [(lx - 3, ly + 8), (lx, ly - 4 - fl), (lx + 3, ly + 8)])
  surf.blit(cork_board(), BOARD.topleft)
  d = game.data
  q = d['active_quest']
  nq = d.get('next_quest')
  if nq:                                             # next quest: a smaller poster tucked behind
    p2 = quest_poster(nq, quest_gold(nq), 250, 200, "UP NEXT", True)
    r2 = pygame.transform.rotate(p2, -5)
    rr = r2.get_rect(center=(BOARD.right - 150, BOARD.top + 262))
    surf.blit(r2, rr)
    pin(surf, rr.centerx + 6, rr.top + 14, (40, 90, 160))
  p1 = quest_poster(q, quest_gold(q), 340, 290, "BOUNTY WANTED")
  r1 = pygame.transform.rotate(p1, 2)
  rr = r1.get_rect(center=(BOARD.centerx - 100, BOARD.top + 226))
  surf.blit(r1, rr)
  wax_seal(surf, rr.centerx, rr.top + 14)
  # chalk slate with the tally of completed quests
  sl = pygame.Rect(BOARD.left + 30, BOARD.top + 28, 150, 62)
  pygame.draw.rect(surf, (90, 60, 30), sl, border_radius=4)
  pygame.draw.rect(surf, (34, 40, 38), sl.inflate(-10, -10), border_radius=3)
  im = text(_ink_font(14), "QUESTS DONE", (220, 224, 220))
  surf.blit(im, im.get_rect(center=(sl.centerx, sl.top + 18)))
  im = text(_ink_font(24), str(d['completed_quests']), (240, 240, 236))
  surf.blit(im, im.get_rect(center=(sl.centerx, sl.top + 42)))
  pin(surf, sl.centerx, sl.top + 3, (200, 170, 40))
  if q['type'] in ('distance', 'score') and not q.get('done'):
    im = text(_ink_font(14), "your best single run counts", (250, 236, 200))
    surf.blit(im, im.get_rect(center=(BOARD.centerx - 100, BOARD.bottom - 20)))


# ---------------------------------------------------------------- Roster: the stables
def stable_backdrop():
  def build():
    rng = random.Random(12)
    s = pygame.Surface((WIDTH, HEIGHT))
    for x in range(0, WIDTH, 44):
      v = rng.randint(-8, 8)
      c = (70 + v, 44 + v, 24 + v // 2)
      pygame.draw.rect(s, c, (x, 0, 43, HEIGHT))
      pygame.draw.line(s, (34, 20, 10), (x, 0), (x, HEIGHT), 2)
    for y in (88, 300):                              # cross beams
      pygame.draw.rect(s, (46, 28, 14), (0, y, WIDTH, 18))
      pygame.draw.rect(s, (90, 58, 30), (0, y, WIDTH, 4))
    fy = HEIGHT - 76
    pygame.draw.rect(s, (120, 96, 40), (0, fy, WIDTH, 76))
    for _ in range(900):                             # hay
      x, y = rng.randint(0, WIDTH), rng.randint(fy - 6, HEIGHT)
      a = rng.uniform(-0.8, 0.8)
      c = rng.choice(((210, 180, 80), (180, 150, 60), (230, 200, 110), (150, 120, 50)))
      pygame.draw.line(s, c, (x, y), (x + int(math.cos(a) * 9), y + int(math.sin(a) * 4)), 1)
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
      shade.fill((8, 4, 2, int(110 * (1 - y / float(HEIGHT)) ** 2)), (0, y, WIDTH, 1))
    s.blit(shade, (0, 0))
    return s.convert()
  return _cache(('stable', WIDTH, HEIGHT), build)


def stall_surface(w, h):
  """an arched wooden stall with hay on the floor"""
  def build():
    rng = random.Random(w * 5 + h)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (22, 14, 10), (8, 20, w - 16, h - 28))
    rad = (w - 16) // 2
    pygame.draw.ellipse(s, (22, 14, 10), (8, 4, w - 16, rad * 2 // 2 + 30))
    for _ in range(160):                             # hay inside
      x, y = rng.randint(14, w - 14), rng.randint(h - 46, h - 10)
      c = rng.choice(((200, 170, 70), (170, 140, 56), (220, 190, 100)))
      pygame.draw.line(s, c, (x, y), (x + rng.randint(-6, 6), y + rng.randint(-2, 2)), 1)
    beam, beam_l = (90, 56, 28), (130, 86, 44)
    pygame.draw.rect(s, beam, (0, 18, 10, h - 18))
    pygame.draw.rect(s, beam, (w - 10, 18, 10, h - 18))
    pygame.draw.arc(s, beam, (0, 0, w, 70), 0, math.pi, 10)
    pygame.draw.arc(s, beam_l, (2, 2, w - 4, 66), 0.1, math.pi - 0.1, 2)
    pygame.draw.line(s, beam_l, (2, 22), (2, h), 2)
    pygame.draw.rect(s, (60, 36, 18), (0, h - 8, w, 8))                  # threshold
    for y in (40, h - 40):                                                 # iron hinges
      pygame.draw.rect(s, (50, 50, 56), (1, y, 12, 6))
      pygame.draw.rect(s, (50, 50, 56), (w - 13, y, 12, 6))
    return s.convert_alpha()
  return _cache(('stall', w, h), build)


def stall_bars(w, h):
  def build():
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(20, w - 10, 18):
      pygame.draw.line(s, (30, 30, 34), (x, 26), (x, h - 10), 5)
      pygame.draw.line(s, (110, 110, 120), (x - 1, 26), (x - 1, h - 10), 1)
    pygame.draw.line(s, (30, 30, 34), (12, 60), (w - 12, 60), 5)
    pygame.draw.line(s, (30, 30, 34), (12, h - 30), (w - 12, h - 30), 5)
    pygame.draw.rect(s, (60, 60, 66), (w // 2 - 9, h // 2 - 4, 18, 16), border_radius=3)   # padlock
    pygame.draw.arc(s, (60, 60, 66), (w // 2 - 7, h // 2 - 14, 14, 16), 0, math.pi, 3)
    pygame.draw.circle(s, (20, 20, 24), (w // 2, h // 2 + 3), 2)
    return s.convert_alpha()
  return _cache(('bars', w, h), build)


def dragon_silhouette(key):
  def build():
    from fd_art import draw_any_dragon
    import fd_pixart as PX
    s = pygame.Surface((168, 128), pygame.SRCALPHA)
    draw_any_dragon(s, key, PX.OX, PX.OY, 0, 0.0, False)
    s.fill((14, 12, 20, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return s
  return _cache(('sil', key), build)


def plaque(w, h, lines, cols):
  key = ('plq', w, h, tuple(lines), tuple(cols))
  def build():
    s = brass_plate(w, h).copy()
    n = len(lines)
    for i, (ln, c) in enumerate(zip(lines, cols)):
      sz = 14 if i == 0 else 12
      f = _ink_font(sz)
      while f.size(ln)[0] > w - 16 and sz > 9:
        sz -= 1
        f = _ink_font(sz)
      im = f.render(ln, True, c)
      s.blit(im, im.get_rect(center=(w // 2, h * (i + 1) // (n + 1) + (1 if n > 1 else 0))))
    return s
  return _cache(key, build)


# ---------------------------------------------------------------- Bestiary: the Monster Manual
BOOK = pygame.Rect(WIDTH // 2 - 400, 92, 800, 410)          # open book (both pages + leather rim)
PAGE_W, PAGE_H = 376, 386


def page_rects():
  if art_ok('bestiary'):
    return art_page_rects()
  l = pygame.Rect(BOOK.centerx - PAGE_W - 4, BOOK.top + 12, PAGE_W, PAGE_H)
  r = pygame.Rect(BOOK.centerx + 4, BOOK.top + 12, PAGE_W, PAGE_H)
  return l, r


def book_arrows():
  """corner tabs that turn the page back / forward"""
  if art_ok('bestiary'):
    return art_corner_rects()
  return (pygame.Rect(BOOK.left - 6, BOOK.bottom - 58, 56, 56), pygame.Rect(BOOK.right - 50, BOOK.bottom - 58, 56, 56))


def book_rect():
  """the whole open book (swipes start here)"""
  if art_ok('bestiary'):
    l, r = art_page_rects()
    return l.union(r).inflate(60, 30)
  return BOOK


def library_backdrop():
  def build():
    rng = random.Random(21)
    s = pygame.Surface((WIDTH, HEIGHT))
    s.fill((26, 22, 30))
    _bricks(s, 0, 0, WIDTH, HEIGHT - 150, rng, (36, 32, 42), 22)
    for sx in (40, WIDTH - 250):                      # bookshelves either side
      pygame.draw.rect(s, (52, 32, 18), (sx, 30, 210, HEIGHT - 170))
      for sy in range(46, HEIGHT - 150, 74):
        x = sx + 10
        while x < sx + 196:
          bw = rng.randint(9, 18)
          bh = rng.randint(44, 62)
          c = rng.choice(((110, 30, 26), (40, 70, 44), (40, 50, 96), (120, 90, 40), (80, 40, 90), (70, 50, 30)))
          pygame.draw.rect(s, c, (x, sy + 62 - bh, bw - 1, bh))
          pygame.draw.line(s, (min(255, c[0] + 50), min(255, c[1] + 40), min(255, c[2] + 30)), (x + 2, sy + 66 - bh), (x + 2, sy + 58), 1)
          pygame.draw.line(s, GOLD_D, (x + 1, sy + 70 - bh), (x + bw - 2, sy + 70 - bh), 1)
          x += bw
        pygame.draw.rect(s, (74, 46, 24), (sx, sy + 62, 210, 8))
      pygame.draw.rect(s, (36, 20, 10), (sx, 30, 210, HEIGHT - 170), 4)
    pygame.draw.rect(s, (66, 40, 20), (0, HEIGHT - 150, WIDTH, 150))   # reading table
    for _ in range(60):
      y = rng.randint(HEIGHT - 146, HEIGHT - 4)
      x = rng.randint(0, WIDTH)
      pygame.draw.line(s, (56, 32, 16), (x, y), (x + rng.randint(40, 160), y), 1)
    pygame.draw.rect(s, (92, 58, 30), (0, HEIGHT - 152, WIDTH, 5))
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
      shade.fill((8, 4, 2, int(150 * abs(y / float(HEIGHT) - 0.5))), (0, y, WIDTH, 1))
    s.blit(shade, (0, 0))
    return s.convert()
  return _cache(('library', WIDTH, HEIGHT), build)


def book_cover():
  def build():
    w, h = BOOK.w + 24, BOOK.h + 20
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 90), (8, 12, w - 8, h - 12), border_radius=16)
    pygame.draw.rect(s, (92, 40, 22), (0, 0, w - 8, h - 12), border_radius=16)
    pygame.draw.rect(s, (120, 56, 30), (4, 4, w - 16, h - 20), 3, border_radius=14)
    rng = random.Random(4)
    for _ in range(500):                              # grain of the leather
      x, y = rng.randint(6, w - 14), rng.randint(6, h - 18)
      s.set_at((x, y), (78, 32, 18) if rng.random() < 0.6 else (108, 50, 28))
    for cx, cy in ((10, 10), (w - 18, 10), (10, h - 22), (w - 18, h - 22)):   # brass corners
      pygame.draw.polygon(s, GOLD, [(cx - 4, cy - 4), (cx + 26 if cx < w / 2 else cx - 26, cy - 4), (cx - 4, cy + 26 if cy < h / 2 else cy - 26)] if cx < w / 2 else
                          [(cx + 4, cy - 4), (cx - 26, cy - 4), (cx + 4, cy + 26 if cy < h / 2 else cy - 26)])
    m = (w - 8) // 2
    pygame.draw.rect(s, (60, 24, 12), (m - 10, 0, 20, h - 12))         # spine
    return s
  return _cache(('bookcover',), build)


def page_paper(side):
  """blank page, shaded toward the spine ('L' or 'R')"""
  def build():
    w, h = PAGE_W, PAGE_H
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((232, 214, 170))
    rng = random.Random(7 if side == 'L' else 8)
    for _ in range(w * h // 50):
      s.set_at((rng.randint(0, w - 1), rng.randint(0, h - 1)), rng.choice(((220, 200, 152), (240, 226, 186), (212, 190, 140))))
    for i in range(26):                                # gutter shadow
      a = int(70 * (1 - i / 26.0) ** 2)
      x = w - 1 - i if side == 'L' else i
      pygame.draw.line(s, (120, 90, 50, a), (x, 0), (x, h))
    for i in range(6):                                 # outer page edges
      a = 60 - i * 10
      x = i if side == 'L' else w - 1 - i
      pygame.draw.line(s, (150, 120, 70, a), (x, 0), (x, h))
    return s
  return _cache(('pagepaper', side), build)


def ink_star(s, x, y, full, r=7):
  pts = []
  for i in range(10):
    a = -math.pi / 2 + i * math.pi / 5
    rr = r if i % 2 == 0 else r * 0.45
    pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
  if full:
    pygame.draw.polygon(s, (150, 30, 20), pts)
  pygame.draw.polygon(s, (52, 30, 14), pts, 1)


SKETCH = pygame.Rect(30, 62, PAGE_W - 60, 132)         # where the creature is drawn on a page


def bestiary_page(info, side, num):
  """the printed (static) part of one Monster Manual page"""
  key, name, kind, desc, stars, attack, weak, appears, pts = info
  def build():
    s = page_paper(side).copy()
    ink, red, faint = (52, 30, 14), (150, 30, 20), (120, 96, 60)
    w = PAGE_W
    sz = 26
    f1 = _ink_font(sz)
    while f1.size(name)[0] > w - 60 and sz > 14:
      sz -= 2
      f1 = _ink_font(sz)
    im = f1.render(name, True, red if kind == "BOSS" else ink)
    s.blit(im, im.get_rect(center=(w // 2, 26)))
    im = _ink_font(13).render("~ %s ~" % (kind if kind == "BOSS" else kind.title()), True, red if kind == "BOSS" else faint)
    s.blit(im, im.get_rect(center=(w // 2, 48)))
    sk = SKETCH
    pygame.draw.rect(s, (170, 140, 92), sk, 1)
    pygame.draw.rect(s, (190, 160, 110), sk.inflate(6, 6), 1)
    for cx, cy in ((sk.left, sk.top), (sk.right, sk.top), (sk.left, sk.bottom), (sk.right, sk.bottom)):
      pygame.draw.circle(s, (170, 140, 92), (cx, cy), 3, 1)
    pygame.draw.ellipse(s, (210, 188, 140), (sk.centerx - 90, sk.bottom - 20, 180, 14))
    for fs_ in (13, 12, 11):
      f3 = _ink_font(fs_)
      dl = _wrap(f3, desc, w - 56)
      if len(dl) <= 3:
        break
    if len(dl) > 3:
      dl = dl[:3]
      dl[2] = dl[2].rstrip('.,') + '...'
    y = sk.bottom + 8
    for ln in dl:
      s.blit(f3.render(ln, True, ink), (28, y))
      y += 16
    y = sk.bottom + 60
    pygame.draw.line(s, faint, (30, y), (w - 30, y), 1)
    f4 = _ink_font(13)
    for i, (lab, v) in enumerate(zip(("Danger", "Toughness", "Speed"), stars)):
      cx = 30 + (w - 60) * (2 * i + 1) // 6
      im = f4.render(lab, True, ink)
      s.blit(im, im.get_rect(center=(cx, y + 14)))
      for k in range(5):
        ink_star(s, cx - 28 + k * 14, y + 32, k < v, 6)
    y += 48
    pygame.draw.line(s, faint, (30, y), (w - 30, y), 1)
    f5 = _ink_font(13)
    for i, (lab, val) in enumerate((("Attack", attack), ("Weak to", weak), ("Appears", appears), ("Bounty", pts + " pts"))):
      yy = y + 14 + i * 18
      s.blit(f5.render(lab + ":", True, red), (30, yy - 8))
      v_ = val
      while f5.size(v_)[0] > w - 140 and len(v_) > 4:
        v_ = v_[:-2].rstrip() + "."
      s.blit(f5.render(v_, True, ink), (106, yy - 8))
    im = _ink_font(11).render(str(num), True, faint)
    s.blit(im, im.get_rect(center=(22 if side == 'L' else w - 22, PAGE_H - 12)))
    return s
  return _cache(('bpage', key, side, num), build)


def end_page(side):
  def build():
    s = page_paper(side).copy()
    ink = (120, 96, 60)
    f = _ink_font(18)
    for i, ln in enumerate(("More beasts await", "beyond the mountains...")):
      im = f.render(ln, True, ink)
      s.blit(im, im.get_rect(center=(PAGE_W // 2, PAGE_H // 2 - 14 + i * 26)))
    pygame.draw.line(s, ink, (PAGE_W // 2 - 60, PAGE_H // 2 + 40), (PAGE_W // 2 + 60, PAGE_H // 2 + 40), 1)
    return s
  return _cache(('endpage', side), build)


def ink_sketch(frames):
  """sepia ink-drawing versions of a creature's animation frames"""
  out = []
  for f in frames:
    g = grayscale(f)
    g.fill((36, 36, 36), special_flags=pygame.BLEND_RGB_ADD)
    g.fill((206, 160, 112), special_flags=pygame.BLEND_RGB_MULT)
    out.append(g)
  return out


def corner_tab(surf, r, dir_, hov, anim):
  pts = [(r.left, r.bottom), (r.right, r.bottom), (r.right, r.top)] if dir_ > 0 else [(r.left, r.top), (r.left, r.bottom), (r.right, r.bottom)]
  pygame.draw.polygon(surf, (200, 176, 128) if not hov else (240, 220, 170), pts)
  pygame.draw.polygon(surf, (120, 90, 50), pts, 2)
  bob = int(math.sin(anim * 4) * 2)
  cx, cy = (r.right - 16 + bob, r.bottom - 16) if dir_ > 0 else (r.left + 16 - bob, r.bottom - 16)
  a = [(cx - 6 * dir_, cy - 7), (cx + 5 * dir_, cy), (cx - 6 * dir_, cy + 7)]
  pygame.draw.polygon(surf, (150, 30, 20), a)


def candle(surf, x, y, anim, ph=0.0):
  pygame.draw.rect(surf, (230, 220, 190), (x - 6, y, 12, 40))
  pygame.draw.ellipse(surf, (240, 232, 205), (x - 6, y - 3, 12, 6))
  pygame.draw.rect(surf, (60, 40, 20), (x - 14, y + 38, 28, 6), border_radius=3)
  fl = math.sin(anim * 11 + ph) * 1.5 + math.sin(anim * 23 + ph) * 0.8
  g = pygame.Surface((90, 90))
  pygame.draw.circle(g, (34, 22, 6), (45, 45), 42)
  pygame.draw.circle(g, (60, 40, 12), (45, 45), 22)
  surf.blit(g, (x - 45, y - 56), special_flags=pygame.BLEND_RGB_ADD)
  pygame.draw.ellipse(surf, (255, 150, 40), (x - 4 + fl * 0.5, y - 18, 8, 16))
  pygame.draw.ellipse(surf, (255, 240, 180), (x - 2 + fl * 0.5, y - 12, 4, 9))


def draw_book(surf, game, anim, sketch_fn):
  """the open Monster Manual: two creatures per spread, flick or tap the corners to turn"""
  surf.blit(library_backdrop(), (0, 0))
  candle(surf, BOOK.left - 60, HEIGHT - 150, anim)
  candle(surf, BOOK.right + 60, HEIGHT - 150, anim, 2.0)
  surf.blit(book_cover(), (BOOK.left - 12, BOOK.top - 8))
  info = ENEMY_INFO
  n_spreads = (len(info) + 1) // 2
  lr, rr = page_rects()

  def page(i, side):
    if 0 <= i < len(info):
      s = bestiary_page(info[i], side, i + 1).copy()
      spr = sketch_fn(info[i][0], anim + i * 0.37, SKETCH.w - 20, SKETCH.h - 18)
      s.blit(spr, (SKETCH.centerx - spr.get_width() // 2, SKETCH.bottom - 8 - spr.get_height()))
      return s
    return end_page(side)

  cur = game.en_page
  fl = getattr(game, 'en_flip', None)
  p = None
  if fl:
    p = (pygame.time.get_ticks() - fl[1]) / 340.0
    if p >= 1.0:
      game.en_flip, p = None, None
  if p is None:
    surf.blit(page(cur * 2, 'L'), lr)
    surf.blit(page(cur * 2 + 1, 'R'), rr)
  else:
    d, old = fl[0], cur - fl[0]
    e = p * p * (3 - 2 * p)
    if d > 0:                                          # next: right page lifts and falls to the left
      surf.blit(page(old * 2, 'L'), lr)
      surf.blit(page(cur * 2 + 1, 'R'), rr)
      if e < 0.5:
        w = max(1, int(PAGE_W * (1 - 2 * e)))
        surf.blit(pygame.transform.scale(page(old * 2 + 1, 'R'), (w, PAGE_H)), (rr.left, rr.top))
      else:
        w = max(1, int(PAGE_W * (2 * e - 1)))
        surf.blit(pygame.transform.scale(page(cur * 2, 'L'), (w, PAGE_H)), (lr.right - w, lr.top))
    else:                                              # back: left page lifts and falls to the right
      surf.blit(page(cur * 2, 'L'), lr)
      surf.blit(page(old * 2 + 1, 'R'), rr)
      if e < 0.5:
        w = max(1, int(PAGE_W * (1 - 2 * e)))
        surf.blit(pygame.transform.scale(page(old * 2, 'L'), (w, PAGE_H)), (lr.right - w, lr.top))
      else:
        w = max(1, int(PAGE_W * (2 * e - 1)))
        surf.blit(pygame.transform.scale(page(cur * 2 + 1, 'R'), (w, PAGE_H)), (rr.left, rr.top))
    sh = pygame.Surface((14, PAGE_H), pygame.SRCALPHA)
    sh.fill((40, 20, 10, int(120 * math.sin(e * math.pi))))
    surf.blit(sh, (BOOK.centerx - 7, lr.top))
  pygame.draw.line(surf, (90, 60, 30), (BOOK.centerx, lr.top), (BOOK.centerx, lr.bottom), 2)
  # ribbon bookmark
  rx = BOOK.centerx - 7
  pygame.draw.polygon(surf, (150, 26, 30), [(rx, BOOK.bottom - 10), (rx + 14, BOOK.bottom - 10), (rx + 14, BOOK.bottom + 8), (rx + 7, BOOK.bottom + 2), (rx, BOOK.bottom + 8)])
  pa, na = book_arrows()
  m = getattr(game, 'mouse', (-1, -1))
  if cur > 0:
    corner_tab(surf, pa, -1, pa.collidepoint(m), anim)
  if cur < n_spreads - 1:
    corner_tab(surf, na, 1, na.collidepoint(m), anim)
  f = _small_label_font()
  im = f.render("Swipe or tap the corners to turn  -  tap a beast for its full entry", True, (210, 190, 150))
  surf.blit(im, im.get_rect(center=(WIDTH // 2, BOOK.bottom + 20)))


# ---------------------------------------------------------------- Options: the wizard's study
OPT_SHEET = pygame.Rect(WIDTH // 2 - 348, 88, 696, 418)        # the hanging parchment
INK, INK_RED, INK_GREEN = (44, 26, 12), (150, 32, 22), (34, 112, 30)


def _wood_planks(s, x0, y0, w, h, rng, base=(46, 28, 18), pw=40):
  for x in range(x0, x0 + w, pw):
    v = rng.randint(-7, 7)
    c = (base[0] + v, base[1] + v, base[2] + v // 2)
    pygame.draw.rect(s, c, (x, y0, pw - 1, h))
    pygame.draw.line(s, (22, 12, 6), (x, y0), (x, y0 + h), 2)
    for _ in range(h // 40):
      y = rng.randint(y0, y0 + h)
      pygame.draw.line(s, (c[0] - 10, c[1] - 7, c[2] - 4), (x + rng.randint(4, pw - 6), y), (x + rng.randint(4, pw - 6), y + rng.randint(20, 70)), 1)


def _book(s, x, y, w, h, col, rng):
  """a book lying flat, spine toward us"""
  dk = tuple(max(0, c - 40) for c in col)
  pygame.draw.rect(s, (230, 214, 176), (x + 4, y + 3, w - 6, h - 4))                 # page edges
  for k in range(3):
    pygame.draw.line(s, (200, 180, 140), (x + 6, y + 5 + k * (h - 8) // 3), (x + w - 4, y + 5 + k * (h - 8) // 3), 1)
  pygame.draw.rect(s, col, (x, y, w, h), border_radius=4)
  pygame.draw.rect(s, dk, (x, y, w, h), 2, border_radius=4)
  pygame.draw.line(s, tuple(min(255, c + 40) for c in col), (x + 4, y + 3), (x + w - 5, y + 3), 1)
  for bx in (x + 14, x + w - 22):                                                  # gold bands on the spine
    pygame.draw.rect(s, GOLD_D, (bx, y + 2, 8, h - 4))
    pygame.draw.line(s, GOLD, (bx + 1, y + 2), (bx + 1, y + h - 3), 1)
  cx, cy = x + w // 2, y + h // 2                                                  # tooled ornament
  pygame.draw.polygon(s, GOLD_D, [(cx, cy - h // 3), (cx + 10, cy), (cx, cy + h // 3), (cx - 10, cy)], 1)
  pygame.draw.circle(s, GOLD, (cx, cy), 2)


def _flask(s, cx, cy, r, col, tag):
  """a round potion flask with a cork and a paper tag"""
  pygame.draw.ellipse(s, (0, 0, 0, 80), (cx - r, cy + r - 6, r * 2, 14))
  glass = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
  c0 = r + 2
  pygame.draw.circle(glass, (200, 220, 230, 70), (c0, c0), r)
  liquid = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
  pygame.draw.circle(liquid, col + (235,), (c0, c0), r - 3)
  liquid.fill((0, 0, 0, 0), (0, 0, r * 2 + 4, int(c0 - r * 0.25)))
  glass.blit(liquid, (0, 0))
  pygame.draw.ellipse(glass, tuple(min(255, v + 70) for v in col) + (200,), (c0 - r + 6, int(c0 - r * 0.25) - 3, (r - 6) * 2, 7))
  pygame.draw.circle(glass, (230, 240, 250, 150), (c0, c0), r, 2)
  pygame.draw.ellipse(glass, (255, 255, 255, 170), (c0 - r // 2 - 4, c0 - r // 2 - 2, r // 3, r // 2))
  s.blit(glass, (cx - c0, cy - c0))
  nw = max(8, r // 3)
  pygame.draw.rect(s, (200, 220, 230), (cx - nw // 2, cy - r - 20, nw, 24))
  pygame.draw.rect(s, (150, 170, 180), (cx - nw // 2, cy - r - 20, nw, 24), 1)
  pygame.draw.rect(s, (150, 104, 60), (cx - nw // 2 - 2, cy - r - 32, nw + 4, 14), border_radius=3)
  pygame.draw.line(s, (190, 140, 90), (cx - nw // 2, cy - r - 28), (cx + nw // 2, cy - r - 28), 1)
  pygame.draw.line(s, (90, 60, 30), (cx - nw // 2, cy - r - 12), (cx - r * 0.75, cy - r * 0.2), 1)   # tag string
  tx, ty = int(cx - r * 0.95), int(cy - r * 0.25)
  pts = [(tx - 14, ty - 2), (tx + 4, ty - 10), (tx + 16, ty + 10), (tx - 2, ty + 18)]
  pygame.draw.polygon(s, (232, 214, 172), pts)
  pygame.draw.polygon(s, (150, 120, 80), pts, 1)
  if tag == 'heart':
    hx, hy = tx + 1, ty + 4
    pygame.draw.circle(s, (180, 30, 36), (hx - 3, hy - 2), 3)
    pygame.draw.circle(s, (180, 30, 36), (hx + 3, hy - 2), 3)
    pygame.draw.polygon(s, (180, 30, 36), [(hx - 6, hy - 1), (hx + 6, hy - 1), (hx, hy + 6)])
  else:
    for k in range(5):
      a = -math.pi / 2 + k * 2 * math.pi / 5
      pygame.draw.line(s, (90, 70, 110), (tx + 1, ty + 4), (int(tx + 1 + math.cos(a) * 6), int(ty + 4 + math.sin(a) * 6)), 2)


def _diamond(s, cx, cy, rx, ry, fill, rim=None, w=0):
  pts = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
  pygame.draw.polygon(s, fill, pts, w)
  if rim:
    pygame.draw.polygon(s, rim, pts, 1)


def blue_gem(s, cx, cy, r):
  _diamond(s, cx, cy, r + 3, r + 4, (40, 24, 10))
  _diamond(s, cx, cy, r + 1, r + 2, GOLD)
  _diamond(s, cx, cy, r - 1, r, (30, 70, 190))
  pygame.draw.polygon(s, (90, 150, 255), [(cx, cy - r), (cx + r - 1, cy), (cx, cy)])
  pygame.draw.polygon(s, (20, 40, 120), [(cx, cy + r), (cx - r + 1, cy), (cx, cy)])
  pygame.draw.line(s, (230, 245, 255), (cx - 2, cy - r // 2), (cx, cy - r + 2), 1)


def study_backdrop():
  """the wizard's study behind the options: lattice window, dragon banner, books, potions, map and compass"""
  def build():
    rng = random.Random(77)
    s = pygame.Surface((WIDTH, HEIGHT))
    C = WIDTH // 2
    _wood_planks(s, 0, 0, WIDTH, HEIGHT, rng)
    for side in (-1, 1):                                            # roof beams
      x0, x1 = C + side * 330, C + side * 640
      pygame.draw.polygon(s, (30, 18, 10), [(x0 - 20, -10), (x0 + 20, -10), (x1 + 20 * side, 220), (x1 - 20 * side, 220)])
      pygame.draw.line(s, (72, 46, 26), (x0 - 18 * side, -10), (x1 - 22 * side, 220), 3)
    pygame.draw.rect(s, (32, 20, 12), (0, 0, WIDTH, 12))
    # lattice window, top left
    wr = pygame.Rect(0, 0, 150, 226)
    for y in range(wr.h):
      t = y / float(wr.h)
      pygame.draw.line(s, (int(20 + 18 * t), int(40 + 30 * t), int(90 + 40 * t)), (0, y), (wr.w, y))
    for _ in range(14):
      s.set_at((rng.randint(4, wr.w - 4), rng.randint(4, wr.h - 4)), (220, 230, 255))
    for k in range(-8, 10):                                         # diamond leading
      pygame.draw.line(s, (20, 14, 10), (k * 30, 0), (k * 30 + wr.h, wr.h), 3)
      pygame.draw.line(s, (20, 14, 10), (k * 30, wr.h), (k * 30 + wr.h, 0), 3)
    pygame.draw.rect(s, (54, 32, 18), (wr.right - 10, 0, 14, wr.h + 10))
    pygame.draw.rect(s, (54, 32, 18), (0, wr.bottom - 4, wr.w + 4, 14))
    pygame.draw.line(s, (88, 58, 32), (wr.right - 8, 0), (wr.right - 8, wr.h), 2)
    for _ in range(26):                                             # ivy
      x, y = rng.randint(0, 170), rng.choice((rng.randint(0, 40), rng.randint(0, 200)))
      if x > 60 and y > 50:
        continue
      c = rng.choice(((40, 90, 30), (60, 120, 40), (30, 70, 24), (80, 140, 50)))
      pygame.draw.ellipse(s, c, (x, y, rng.randint(10, 18), rng.randint(7, 11)))
    # dragon banner, top right
    bx, bw, bh = WIDTH - 182, 140, 150
    pygame.draw.rect(s, (60, 40, 20), (bx - 12, 4, bw + 24, 8), border_radius=3)
    pygame.draw.circle(s, GOLD, (bx - 12, 8), 6)
    pygame.draw.circle(s, GOLD, (bx + bw + 12, 8), 6)
    pts = [(bx, 10), (bx + bw, 10), (bx + bw, bh), (bx + bw // 2, bh + 34), (bx, bh)]
    pygame.draw.polygon(s, (120, 22, 28), pts)
    for k in range(5):
      fx = bx + 12 + k * 28
      pygame.draw.line(s, (96, 14, 20), (fx, 14), (fx + 4, bh - 6), 3)
    pygame.draw.polygon(s, GOLD, pts, 3)
    pygame.draw.polygon(s, GOLD_D, [(bx + 8, 16), (bx + bw - 8, 16), (bx + bw - 8, bh - 4), (bx + bw // 2, bh + 24), (bx + 8, bh - 4)], 1)
    for k in range(13):                                             # fringe
      t = k / 12.0
      x = bx + bw * t
      y = bh + 34 * (1 - abs(t - 0.5) * 2)
      pygame.draw.line(s, GOLD_D, (int(x), int(y)), (int(x), int(y) + 7), 2)
    ex, ey = bx + bw // 2 + 4, 76                                   # dragon head emblem (facing left)
    head = [(ex - 36, ey - 2), (ex - 24, ey - 11), (ex - 10, ey - 15), (ex - 2, ey - 20), (ex + 24, ey - 44), (ex + 10, ey - 16),
            (ex + 20, ey - 10), (ex + 28, ey + 8), (ex + 26, ey + 30), (ex + 34, ey + 46), (ex + 8, ey + 40), (ex + 4, ey + 18),
            (ex - 6, ey + 10), (ex - 22, ey + 8), (ex - 14, ey + 3), (ex - 34, ey + 4)]
    pygame.draw.polygon(s, (226, 172, 60), head)
    pygame.draw.polygon(s, (226, 172, 60), [(ex + 2, ey - 16), (ex + 34, ey - 30), (ex + 16, ey - 10)])   # second horn
    for k in range(4):                                              # frill down the back of the neck
      y = ey - 4 + k * 11
      pygame.draw.polygon(s, (226, 172, 60), [(ex + 22 + k, y), (ex + 36 + k * 2, y + 3), (ex + 25 + k, y + 8)])
    pygame.draw.polygon(s, (130, 80, 20), head, 2)
    pygame.draw.circle(s, (120, 22, 28), (ex - 9, ey - 7), 3)
    pygame.draw.line(s, (130, 80, 20), (ex - 33, ey + 1), (ex - 16, ey + 2), 2)
    pygame.draw.circle(s, (130, 80, 20), (ex - 30, ey - 6), 1)
    # table top
    ty = HEIGHT - 176
    pygame.draw.rect(s, (52, 30, 16), (0, ty, WIDTH, HEIGHT - ty))
    pygame.draw.rect(s, (82, 50, 26), (0, ty, WIDTH, 5))
    for _ in range(30):
      y = rng.randint(ty + 8, HEIGHT - 4)
      x = rng.randint(0, WIDTH)
      pygame.draw.line(s, (42, 24, 12), (x, y), (x + rng.randint(40, 150), y), 1)
    # red velvet cloth spilling over the table either side
    for side in (-1, 1):
      x0 = C + side * 300
      cl = [(x0, ty - 10), (x0 + side * 170, ty - 30), (x0 + side * 220, HEIGHT), (x0 - side * 40, HEIGHT)]
      pygame.draw.polygon(s, (110, 18, 26), cl)
      for k in range(4):
        fx = x0 + side * (30 + k * 40)
        pygame.draw.line(s, (80, 10, 18), (fx, ty - 14), (fx + side * 18, HEIGHT), 3)
      pygame.draw.line(s, GOLD_D, cl[0], cl[3], 3)
      pygame.draw.line(s, GOLD, cl[0], cl[3], 1)
    # left: star map, inkwell + quill, brass compass, books
    mp = parchment(270, 240, 21)
    pygame.draw.circle(mp, (130, 100, 64), (135, 120), 92, 1)
    pygame.draw.circle(mp, (130, 100, 64), (135, 120), 64, 1)
    pygame.draw.circle(mp, (130, 100, 64), (135, 120), 30, 1)
    for k in range(16):
      a = k * math.pi / 8
      L = 96 if k % 2 == 0 else 60
      pygame.draw.line(mp, (140, 110, 70), (135, 120), (int(135 + math.cos(a) * L), int(120 + math.sin(a) * L)), 1)
    for k in range(4):                                              # compass rose
      a = k * math.pi / 2
      tip = (135 + math.cos(a) * 52, 120 + math.sin(a) * 52)
      l = (135 + math.cos(a + 1.3) * 10, 120 + math.sin(a + 1.3) * 10)
      r = (135 + math.cos(a - 1.3) * 10, 120 + math.sin(a - 1.3) * 10)
      pygame.draw.polygon(mp, (110, 80, 46), [tip, l, (135, 120)])
      pygame.draw.polygon(mp, (170, 140, 96), [tip, r, (135, 120)])
    for _ in range(40):
      pygame.draw.circle(mp, (110, 84, 54), (rng.randint(20, 250), rng.randint(20, 220)), 1)
    mp = pygame.transform.rotate(mp, 8)
    s.blit(mp, (60, 150))
    pygame.draw.rect(s, (200, 178, 130), (40, ty - 46, 230, 30), border_radius=14)   # rolled scroll
    pygame.draw.rect(s, (150, 124, 84), (40, ty - 46, 230, 30), 2, border_radius=14)
    pygame.draw.ellipse(s, (170, 146, 100), (32, ty - 46, 22, 30))
    for i, (col, w_, h_) in enumerate((((90, 30, 26), 220, 40), ((40, 46, 80), 200, 36), ((96, 60, 28), 230, 42))):   # book pile
      _book(s, -20 + i * 8, HEIGHT - 60 - i * 44 - h_ + 40, w_, h_, col, rng)
    iw = (98, 290)                                                  # inkwell
    pygame.draw.ellipse(s, (0, 0, 0), (iw[0] - 44, iw[1] + 34, 88, 16))
    pygame.draw.ellipse(s, (22, 22, 40), (iw[0] - 38, iw[1] - 20, 76, 62))
    pygame.draw.ellipse(s, (52, 52, 90), (iw[0] - 30, iw[1] - 12, 22, 30))
    pygame.draw.rect(s, (22, 22, 40), (iw[0] - 18, iw[1] - 38, 36, 22))
    pygame.draw.ellipse(s, GOLD, (iw[0] - 22, iw[1] - 44, 44, 12))
    pygame.draw.ellipse(s, (10, 10, 18), (iw[0] - 16, iw[1] - 42, 32, 8))
    pygame.draw.arc(s, GOLD, (iw[0] - 30, iw[1] - 6, 60, 40), 0.3, 2.8, 2)
    pygame.draw.circle(s, GOLD, (iw[0], iw[1] + 14), 4, 1)
    qx, qy = iw[0] + 4, iw[1] - 40                                  # quill
    tip = (qx + 96, qy - 150)
    vane = [(qx, qy), (qx + 40, qy - 70), tip, (qx + 70, qy - 60), (qx + 18, qy - 20)]
    pygame.draw.polygon(s, (236, 234, 226), vane)
    pygame.draw.polygon(s, (170, 168, 160), vane, 1)
    pygame.draw.line(s, (200, 196, 186), (qx, qy), tip, 2)
    for k in range(1, 12):
      t = k / 12.0
      px, py = qx + (tip[0] - qx) * t, qy + (tip[1] - qy) * t
      pygame.draw.line(s, (190, 188, 180), (int(px), int(py)), (int(px - 14 + t * 6), int(py - 6)), 1)
    cx_, cy_ = 70, 345                                              # brass compass
    pygame.draw.ellipse(s, (0, 0, 0), (cx_ - 66, cy_ - 30, 132, 76))
    pygame.draw.ellipse(s, (150, 104, 30), (cx_ - 64, cy_ - 42, 128, 84))
    pygame.draw.ellipse(s, (220, 170, 70), (cx_ - 64, cy_ - 42, 128, 84), 4)
    pygame.draw.ellipse(s, (40, 26, 16), (cx_ - 50, cy_ - 32, 100, 64))
    for k in range(24):
      a = k * math.pi / 12
      pygame.draw.line(s, (200, 160, 80), (int(cx_ + math.cos(a) * 44), int(cy_ + math.sin(a) * 28)), (int(cx_ + math.cos(a) * 48), int(cy_ + math.sin(a) * 31)), 1)
    pygame.draw.polygon(s, (200, 40, 30), [(cx_ + 30, cy_ - 14), (cx_ + 4, cy_ + 4), (cx_ - 4, cy_ - 4)])
    pygame.draw.polygon(s, (230, 224, 210), [(cx_ - 30, cy_ + 14), (cx_ - 4, cy_ - 4), (cx_ + 4, cy_ + 4)])
    pygame.draw.circle(s, GOLD, (cx_, cy_), 4)
    pygame.draw.rect(s, (90, 60, 30), (64, HEIGHT - 50, 82, 22), border_radius=6)    # candle holder (the flame is animated)
    pygame.draw.ellipse(s, (120, 80, 40), (56, HEIGHT - 64, 98, 26))
    pygame.draw.ellipse(s, (70, 46, 24), (66, HEIGHT - 60, 78, 16))
    pygame.draw.rect(s, (236, 226, 196), (82, HEIGHT - 150, 46, 98))
    pygame.draw.rect(s, (250, 244, 224), (86, HEIGHT - 150, 12, 96))
    for dxp, dl in ((84, 30), (104, 46), (122, 22)):
      pygame.draw.rect(s, (246, 238, 214), (dxp, HEIGHT - 152, 7, dl), border_radius=3)
    pygame.draw.ellipse(s, (246, 238, 214), (80, HEIGHT - 158, 50, 14))
    pygame.draw.line(s, (40, 30, 20), (105, HEIGHT - 156), (105, HEIGHT - 164), 2)
    # right: big book stacks, two potions and a sealed letter
    rx = WIDTH - 210
    for i, (col, h_) in enumerate((((70, 40, 60), 54), ((40, 30, 50), 60), ((84, 46, 24), 52), ((50, 30, 46), 58), ((70, 40, 24), 50), ((44, 30, 60), 56))):
      y = 180 + sum(54 for _ in range(i)) + (i // 3) * 20
      _book(s, rx + (i % 2) * 14 - 10, y, 240, h_, col, rng)
    lt = parchment(176, 196, 31)                                    # sealed letter
    for k in range(8):
      y = 24 + k * 18
      x = 18
      while x < 150:
        L = rng.randint(10, 26)
        pygame.draw.line(lt, (70, 50, 40), (x, y + rng.randint(-1, 1)), (min(156, x + L), y + rng.randint(-2, 2)), 1)
        x += L + rng.randint(4, 8)
    pygame.draw.circle(lt, (130, 16, 22), (120, 164), 17)
    pygame.draw.circle(lt, (170, 30, 36), (120, 164), 12)
    pygame.draw.circle(lt, (110, 10, 18), (120, 164), 6, 2)
    lt = pygame.transform.rotate(lt, -12)
    s.blit(lt, (WIDTH - 334, 318))
    _flask(s, WIDTH - 218, 300, 40, (190, 20, 30), 'heart')
    _flask(s, WIDTH - 108, 444, 34, (40, 110, 220), 'star')
    # the parchment itself, hung from rods with red cloth draped behind its sides
    sh = OPT_SHEET
    for side in (-1, 1):
      ex_ = sh.left + 8 if side < 0 else sh.right - 8
      cl = [(ex_ - side * 4, sh.top - 6), (ex_ + side * 26, sh.top - 6), (ex_ + side * 34, sh.top + 140), (ex_ + side * 16, sh.top + 300), (ex_ - side * 10, sh.top + 330)]
      pygame.draw.polygon(s, (118, 20, 28), cl)
      for k in range(3):
        pygame.draw.line(s, (86, 12, 20), (ex_ + side * (4 + k * 8), sh.top), (ex_ + side * (8 + k * 6), sh.top + 280 - k * 40), 2)
      pygame.draw.line(s, GOLD_D, cl[1], cl[2], 2)
      pygame.draw.line(s, GOLD_D, cl[2], cl[3], 2)
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)        # vignette
    for x in range(0, WIDTH, 4):
      d = abs(x / float(WIDTH) - 0.5) * 2
      shade.fill((8, 4, 0, int(120 * max(0.0, d - 0.35) ** 1.3)), (x, 0, 4, HEIGHT))
    s.blit(shade, (0, 0))
    s.blit(_parchment_sheet(), sh)                                  # (the sheet sits above the vignette)
    for side in (-1, 1):
      x0 = sh.left - 18 if side < 0 else sh.right - 52
      pygame.draw.rect(s, (30, 16, 8), (x0, sh.top - 14, 70, 14), border_radius=7)
      pygame.draw.rect(s, (110, 66, 30), (x0 + 2, sh.top - 13, 66, 10), border_radius=5)
      kx = x0 if side < 0 else x0 + 70
      pygame.draw.circle(s, GOLD_D, (kx, sh.top - 7), 9)
      pygame.draw.circle(s, GOLD, (kx, sh.top - 7), 9, 2)
      pygame.draw.circle(s, GOLD_L, (kx - 2, sh.top - 10), 2)
      pygame.draw.arc(s, GOLD, (kx - 14 + side * 4, sh.top - 30, 28, 30), 0.2 if side > 0 else 1.6, 2.6 if side > 0 else 3.9, 3)
    return s.convert()
  return _cache(('study', WIDTH, HEIGHT), build)


def _parchment_sheet():
  def build():
    sh = OPT_SHEET
    s = parchment(sh.w, sh.h, 12).copy()
    ink = (120, 84, 50)
    for cx, cy, sx, sy in ((26, 22, 1, 1), (sh.w - 26, 22, -1, 1), (26, sh.h - 22, 1, -1), (sh.w - 26, sh.h - 22, -1, -1)):   # corner flourishes
      pygame.draw.line(s, ink, (cx, cy), (cx + sx * 40, cy), 1)
      pygame.draw.line(s, ink, (cx, cy), (cx, cy + sy * 30), 1)
      pygame.draw.arc(s, ink, (cx + (0 if sx > 0 else -16), cy + (0 if sy > 0 else -16), 16, 16), 0, 6.28, 1)
      _diamond(s, cx + sx * 46, cy, 4, 3, ink)
    y = sh.h - 52                                                   # footer rule
    pygame.draw.line(s, ink, (120, y), (sh.w // 2 - 14, y), 1)
    pygame.draw.line(s, ink, (sh.w // 2 + 14, y), (sh.w - 120, y), 1)
    _diamond(s, sh.w // 2, y, 7, 4, ink)
    fy = sh.h - 30
    for sx in (-1, 1):                                              # little flourishes either side of the footer text
      fx = sh.w // 2 + sx * 250
      pygame.draw.line(s, ink, (fx - 16, fy), (fx + 16, fy), 1)
      _diamond(s, fx, fy, 5, 3, ink)
      pygame.draw.arc(s, ink, (fx + sx * 10 - 6, fy - 6, 12, 12), 0, 6.28, 1)
    return s
  return _cache(('optsheet2', WIDTH), build)


def opt_icon(kind):
  """diamond badge with a cream glyph for an options row"""
  def build():
    S = 52
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    c = S // 2
    _diamond(s, c, c, 25, 25, (24, 14, 8))
    _diamond(s, c, c, 23, 23, GOLD)
    _diamond(s, c, c, 20, 20, (40, 30, 24))
    _diamond(s, c, c, 17, 17, (58, 44, 34), (30, 20, 14))
    g = (238, 224, 192)
    o = c - 22
    if kind == 'music':
      pygame.draw.circle(s, g, (o + 17, o + 29), 5)
      pygame.draw.line(s, g, (o + 21, o + 29), (o + 21, o + 12), 3)
      pygame.draw.polygon(s, g, [(o + 21, o + 11), (o + 30, o + 15), (o + 30, o + 20), (o + 21, o + 16)])
    elif kind == 'sfx':
      pygame.draw.rect(s, g, (o + 11, o + 18, 6, 9))
      pygame.draw.polygon(s, g, [(o + 17, o + 18), (o + 24, o + 12), (o + 24, o + 33), (o + 17, o + 27)])
      pygame.draw.arc(s, g, (o + 22, o + 16, 10, 13), -0.9, 0.9, 2)
      pygame.draw.arc(s, g, (o + 22, o + 11, 16, 23), -0.9, 0.9, 2)
    elif kind == 'display':
      pygame.draw.rect(s, g, (o + 10, o + 12, 25, 17), 2)
      pygame.draw.rect(s, (140, 170, 190), (o + 13, o + 15, 19, 11))
      pygame.draw.line(s, g, (o + 22, o + 29), (o + 22, o + 33), 3)
      pygame.draw.line(s, g, (o + 16, o + 33), (o + 28, o + 33), 3)
    elif kind == 'weather':
      pygame.draw.circle(s, (255, 214, 120), (o + 18, o + 19), 6)
      for k in range(8):
        a = k * math.pi / 4
        pygame.draw.line(s, (255, 214, 120), (int(o + 18 + math.cos(a) * 8), int(o + 19 + math.sin(a) * 8)), (int(o + 18 + math.cos(a) * 11), int(o + 19 + math.sin(a) * 11)), 2)
      for cx, cy, r in ((22, 28, 5), (28, 25, 7), (34, 29, 4)):
        pygame.draw.circle(s, g, (o + cx, o + cy), r)
      pygame.draw.rect(s, g, (o + 17, o + 28, 21, 6))
    elif kind == 'difficulty':
      pygame.draw.polygon(s, g, [(o + 8, o + 33), (o + 19, o + 13), (o + 26, o + 25), (o + 30, o + 19), (o + 37, o + 33)])
      pygame.draw.polygon(s, (58, 44, 34), [(o + 19, o + 13), (o + 15, o + 21), (o + 19, o + 19), (o + 23, o + 21)])
      pygame.draw.polygon(s, (255, 255, 255), [(o + 19, o + 14), (o + 16, o + 20), (o + 19, o + 18), (o + 22, o + 20)])
    elif kind == 'shake':
      pygame.draw.rect(s, g, (o + 9, o + 16, 27, 17), border_radius=3)
      pygame.draw.rect(s, g, (o + 15, o + 12, 9, 5))
      pygame.draw.circle(s, (40, 30, 24), (o + 22, o + 24), 6)
      pygame.draw.circle(s, g, (o + 22, o + 24), 4, 2)
    elif kind == 'vibrate':
      pygame.draw.rect(s, g, (o + 16, o + 10, 13, 24), 2, border_radius=3)
      pygame.draw.line(s, g, (o + 20, o + 30), (o + 25, o + 30), 1)
      for sx in (-1, 1):
        x = o + 22 + sx * 11
        pygame.draw.line(s, g, (x, o + 15), (x, o + 29), 2)
        pygame.draw.line(s, g, (x + sx * 4, o + 18), (x + sx * 4, o + 26), 2)
    return s
  return _cache(('opticon', kind), build)


def ornate_plaque(label):
  """the gold-framed wooden title plaque with blue gems"""
  def build():
    t = ENV.fire_text(label, 44)
    w, h = max(330, t.get_width() + 150), 86
    s = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
    ox, oy = 12, 12
    pts = [(ox + 22, oy), (ox + w - 22, oy), (ox + w, oy + h // 2), (ox + w - 22, oy + h), (ox + 22, oy + h), (ox, oy + h // 2)]   # pointed side ends
    pygame.draw.polygon(s, (16, 8, 4), [(x + 3, y + 4) for x, y in pts])
    pygame.draw.polygon(s, (52, 30, 18), pts)
    for k in range(5):                                              # wood grain
      y = oy + 12 + k * 15
      pygame.draw.line(s, (40, 22, 12), (ox + 26, y), (ox + w - 26, y + (k % 2)), 1)
    pygame.draw.polygon(s, GOLD_D, pts, 6)
    pygame.draw.polygon(s, GOLD, pts, 3)
    inner = [(ox + 30, oy + 9), (ox + w - 30, oy + 9), (ox + w - 12, oy + h // 2), (ox + w - 30, oy + h - 9), (ox + 30, oy + h - 9), (ox + 12, oy + h // 2)]
    pygame.draw.polygon(s, GOLD_D, inner, 1)
    for cx, sy in ((ox + 34, 1), (ox + w - 34, 1), (ox + 34, -1), (ox + w - 34, -1)):   # corner scrolls
      cy = oy + 12 if sy > 0 else oy + h - 12
      pygame.draw.arc(s, GOLD, (cx - 8, cy - 8, 16, 16), 0, 6.28, 2)
      pygame.draw.circle(s, GOLD_L, (cx, cy), 2)
    s.blit(t, t.get_rect(center=(ox + w // 2, oy + h // 2 - 1)))
    blue_gem(s, ox + 34, oy + h // 2, 7)
    blue_gem(s, ox + w - 34, oy + h // 2, 7)
    blue_gem(s, ox + w // 2, oy + 2, 6)
    blue_gem(s, ox + w // 2, oy + h - 2, 6)
    return s
  return _cache(('oplaque', label), build)


def sconce_candle(surf, x, y, anim, ph=0.0):
  """a candle in a little gold wall sconce (x, y = top of the wax)"""
  pygame.draw.rect(surf, (70, 44, 20), (x - 2, y + 30, 4, 18))
  pygame.draw.polygon(surf, GOLD_D, [(x - 20, y + 30), (x + 20, y + 30), (x + 12, y + 40), (x - 12, y + 40)])
  pygame.draw.line(surf, GOLD, (x - 20, y + 30), (x + 20, y + 30), 2)
  pygame.draw.rect(surf, (236, 226, 196), (x - 9, y, 18, 31))
  pygame.draw.rect(surf, (250, 246, 228), (x - 6, y + 1, 5, 28))
  flame(surf, x, y - 2, anim, ph, 1.0)


def flame(surf, x, y, anim, ph=0.0, sc=1.0):
  fl = math.sin(anim * 10 + ph) * 1.6 + math.sin(anim * 23 + ph * 2) * 0.8
  add_glow(surf, int(x), int(y - 8 * sc), int(46 * sc), (70, 44, 10))
  pygame.draw.ellipse(surf, (255, 140, 30), (int(x - 6 * sc + fl * 0.4), int(y - 22 * sc), int(12 * sc), int(24 * sc)))
  pygame.draw.ellipse(surf, (255, 214, 90), (int(x - 4 * sc + fl * 0.4), int(y - 17 * sc), int(8 * sc), int(17 * sc)))
  pygame.draw.ellipse(surf, (255, 250, 220), (int(x - 2 * sc + fl * 0.3), int(y - 11 * sc), int(4 * sc), int(9 * sc)))


def draw_study_title(surf, label, cy, anim):
  p = ornate_plaque(label)
  r = p.get_rect(center=(WIDTH // 2, cy))
  sconce_candle(surf, r.left - 26, cy - 22, anim, 0.0)
  sconce_candle(surf, r.right + 26, cy - 22, anim, 2.3)
  surf.blit(p, r)
  return r


def gold_slider(surf, x0, x1, y, v, col, hot):
  """dark track with gold caps, a coloured fill and a gold handle"""
  fx = x0 + int((x1 - x0) * v / 100.0)
  pygame.draw.rect(surf, (16, 10, 6), (x0 - 5, y - 9, x1 - x0 + 10, 18), border_radius=9)
  pygame.draw.rect(surf, (30, 24, 22), (x0 - 3, y - 7, x1 - x0 + 6, 14), border_radius=7)
  if fx > x0:
    pygame.draw.rect(surf, tuple(max(0, c - 50) for c in col), (x0 - 2, y - 5, fx - x0 + 4, 11), border_radius=5)
    pygame.draw.rect(surf, col, (x0 - 2, y - 5, fx - x0 + 4, 8), border_radius=4)
    pygame.draw.line(surf, tuple(min(255, c + 90) for c in col), (x0 + 2, y - 3), (fx - 2, y - 3), 1)
  pygame.draw.rect(surf, GOLD, (x0 - 5, y - 9, x1 - x0 + 10, 18), 2, border_radius=9)
  for cx, sx in ((x0 - 12, -1), (x1 + 12, 1)):                     # gold arrow caps
    _diamond(surf, cx, y, 9, 10, (30, 16, 8))
    _diamond(surf, cx, y, 7, 8, GOLD)
    _diamond(surf, cx, y, 3, 4, (30, 70, 190))
  if hot:
    add_glow(surf, fx, y, 26, (60, 46, 10))
  pygame.draw.rect(surf, (30, 16, 6), (fx - 9, y - 16, 18, 32), border_radius=5)
  pygame.draw.rect(surf, GOLD, (fx - 8, y - 15, 16, 30), border_radius=4)
  pygame.draw.rect(surf, GOLD_L, (fx - 6, y - 13, 5, 26), border_radius=2)
  pygame.draw.line(surf, GOLD_D, (fx + 2, y - 11), (fx + 2, y + 11), 2)
  _diamond(surf, fx, y, 3, 5, (30, 16, 8))


def toggle_switch(surf, x, y, pos, on, hot):
  """pill switch: the knob sits right (green) when on, left (red) when off; pos 0..1 animates it"""
  w, h = 58, 28
  r = pygame.Rect(x, y - h // 2, w, h)
  pygame.draw.rect(surf, (14, 8, 4), r.inflate(4, 4), border_radius=16)
  pygame.draw.rect(surf, (36, 26, 20), r, border_radius=14)
  pygame.draw.rect(surf, GOLD_D if not hot else GOLD, r, 2, border_radius=14)
  kx = int(r.left + 14 + (w - 28) * pos)
  base = (40, 160, 50) if on else (170, 50, 40)
  pygame.draw.circle(surf, (10, 6, 2), (kx, y + 1), 13)
  pygame.draw.circle(surf, tuple(max(0, c - 40) for c in base), (kx, y), 12)
  pygame.draw.circle(surf, base, (kx, y - 1), 10)
  pygame.draw.circle(surf, tuple(min(255, c + 80) for c in base), (kx - 1, y - 3), 6)
  pygame.draw.circle(surf, (255, 255, 255), (kx - 4, y - 5), 2)


ROW_ICONS = {'music': 'music', 'sfx': 'sfx', 'display': 'display', 'weather': 'weather', 'difficulty': 'difficulty', 'shake': 'shake', 'vibrate': 'vibrate'}
LIQUID = {'music': (140, 50, 210), 'sfx': (50, 180, 50)}


def draw_study(surf, game, anim, rows, sliders, track):
  """the options screen: the wizard's study with the settings written on a hanging parchment"""
  surf.blit(study_backdrop(), (0, 0))
  flame(surf, 105, HEIGHT - 160, anim, 1.1, 1.5)                    # the big desk candle
  fl, fv = _ink_font(22), _ink_font(19)
  m = getattr(game, 'mouse', (-1, -1))
  knobs = game.__dict__.setdefault('opt_knob', {})
  for i, (k, (name, val, on, r)) in enumerate(rows.items()):
    hot = r.collidepoint(m) or getattr(game, 'opt_drag', None) == k
    if hot:
      hl = _cache(('opthl', r.w, r.h), lambda: _hl_surf(r.w + 16, r.h))
      surf.blit(hl, (r.x - 8, r.y))
    surf.blit(opt_icon(ROW_ICONS.get(k, 'music')), (r.left - 4, r.centery - 26))
    im = fl.render(name, True, INK)
    surf.blit(im, im.get_rect(midleft=(r.left + 56, r.centery)))
    sep_y = r.bottom + 4                                            # ruled line under the row
    pygame.draw.line(surf, (150, 116, 76), (r.left + 40, sep_y), (r.right, sep_y), 1)
    _diamond(surf, r.left + 40, sep_y, 4, 3, (150, 116, 76))
    if k in sliders:
      x0, x1, y = track(r)
      gold_slider(surf, x0, x1, y, on, LIQUID.get(k, (200, 80, 80)), hot)
      im = fv.render(str(on), True, INK_GREEN if on else INK_RED)
      surf.blit(im, im.get_rect(midright=(r.right - 2, r.centery)))
    else:
      p = knobs.get(k, 1.0 if on else 0.0)
      p += ((1.0 if on else 0.0) - p) * 0.35                         # knob slides across
      knobs[k] = p
      toggle_switch(surf, r.right - 60, r.centery, p, on, hot)
      im = fv.render(val, True, INK_GREEN if on else INK_RED)
      surf.blit(im, im.get_rect(midright=(r.right - 78, r.centery)))


def _hl_surf(w, h):
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  s.fill((170, 120, 50, 38))
  return s


# ---------------------------------------------------------------- your painted options art (fd_optart), with the drawn look as a fallback
try:
  import fd_optart as OA
except Exception:                                  # (missing file: fall back to the drawn version)
  OA = None
try:
  import fd_lairart as LA
except Exception:
  LA = None
try:
  import fd_forgeart as FA
except Exception:
  FA = None
try:
  import fd_bestart as BA
except Exception:
  BA = None
try:
  import fd_questart as QA
except Exception:
  QA = None
try:
  import fd_stableart as SA
except Exception:
  SA = None
try:
  import fd_eggart as EA
except Exception:
  EA = None
try:
  import fd_babyart as YA
except Exception:
  YA = None
try:
  import fd_hearthart as HA
except Exception:
  HA = None
try:
  import fd_reportart as RA
except Exception:
  RA = None
try:
  import fd_infoart as IA
except Exception:
  IA = None
try:
  import fd_menuart as MA
except Exception:
  MA = None
ART_MODS = [m for m in (OA, LA, FA, BA, QA, SA, EA, YA, HA, RA, IA, MA) if m is not None]


class _Art:
  """looks a piece up in whichever art module holds it"""
  @staticmethod
  def _m(name):
    for m in ART_MODS:
      if m.has(name):
        return m
    raise KeyError(name)

  def img(self, name):
    return self._m(name).img(name)

  def scaled(self, name, w, h):
    return self._m(name).scaled(name, w, h)

  def has(self, name):
    return any(m.has(name) for m in ART_MODS)


ART = _Art()
SCROLL_ART = pygame.Rect(WIDTH // 2 - 360, 88, 720, 412)     # where the painted scroll goes (banners included)


_ART_OK = {}


def art_ok(screen='options'):
  """True when your painted art for that screen loads; otherwise the drawn version is used"""
  r = _ART_OK.get(screen)
  if r is None:
    need = {'options': ('tab_home', 'background', 'scroll'), 'lair': ('lair_bg', 'sign', 'chain', 'lair_plaque'),
            'bestiary': ('best_bg', 'frame_ruins', 'frame_forest', 'frame_boss', 'star_on', 'star_off', 'tab_left', 'tab_right', 'ink_divider', 'ink_flourish', 'title_plaque', 'coin'),
            'report': ('report_bg', 'coin'),
            'menu': ('menu_bg', 'menu_title', 'menu_record', 'cloud_a', 'cloud_d', 'red_button', 'coin_box'),
            'info': ('info_bg', 'red_button', 'gstar_on', 'gstar_off', 'pedestal', 'gold_divider', 'egg_common'),
            'hearths': ('hearth_bg', 'egg_common', 'egg_legendary', 'quest_bar', 'wood_button', 'coin'),
            'babies': ('baby_bg', 'brass_long', 'wood_button', 'egg_frame', 'egg_frame_gold', 'lair_plaque'),
            'eggs': ('hatch_bg', 'egg_frame', 'egg_frame_gold', 'egg_cradle', 'egg_common', 'egg_legendary', 'wood_button', 'lair_plaque'),
            'stables': ('stable_bg', 'stall', 'stall_gold', 'stall_bars', 'brass_long', 'wood_button', 'lair_plaque'),
            'quests': ('quest_bg', 'quest_bar', 'stamp', 'quest_tag', 'lair_plaque', 'coin'),
            'hoard': ('forge_bg', 'forge_sign', 'forge_label', 'price_plaque', 'icon_upg_thick_scales', 'chain', 'coin', 'lair_plaque')}.get(screen, ())
    try:
      for n in need:
        ART.img(n)
      r = True
    except Exception:
      r = False
    _ART_OK[screen] = r
  return r


def nine_slice(name, w, h, corner, k=0.5):
  """stretch a framed piece to (w, h) keeping its corners un-squashed"""
  key = ('9s', name, w, h, corner, k)
  def build():
    src = ART.img(name)
    sw, sh = src.get_size()
    c = corner
    cc = max(2, int(c * k))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    xs = [(0, c, 0, cc), (c, sw - c, cc, w - cc), (sw - c, sw, w - cc, w)]
    ys = [(0, c, 0, cc), (c, sh - c, cc, h - cc), (sh - c, sh, h - cc, h)]
    for sx0, sx1, dx0, dx1 in xs:
      for sy0, sy1, dy0, dy1 in ys:
        if dx1 - dx0 < 1 or dy1 - dy0 < 1 or sx1 - sx0 < 1 or sy1 - sy0 < 1:
          continue
        piece = src.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
        out.blit(pygame.transform.smoothscale(piece, (dx1 - dx0, dy1 - dy0)), (dx0, dy0))
    return out
  return _cache(key, build)


def three_slice(name, w, h, end):
  """stretch a bar to (w, h): its two ends keep their shape, the middle stretches"""
  key = ('3s', name, w, h, end)
  def build():
    src = ART.img(name)
    sw, sh = src.get_size()
    k = h / float(sh)
    e = max(1, int(end * k))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.blit(pygame.transform.smoothscale(src.subsurface((0, 0, end, sh)), (e, h)), (0, 0))
    out.blit(pygame.transform.smoothscale(src.subsurface((end, 0, sw - 2 * end, sh)), (max(1, w - 2 * e), h)), (e, 0))
    out.blit(pygame.transform.smoothscale(src.subsurface((sw - end, 0, end, sh)), (e, h)), (w - e, 0))
    return out
  return _cache(key, build)


def scroll_art(w, h):
  """your scroll, widened: banner corners kept as painted, the parchment between them tiled (mirrored) to fill"""
  def build():
    src = ART.img('scroll')
    sw, sh = src.get_size()
    k = h / float(sh)
    a, b = OA.SCROLL_SLICE
    left = pygame.transform.smoothscale(src.subsurface((0, 0, a, sh)), (int(a * k), h))
    right = pygame.transform.smoothscale(src.subsurface((b, 0, sw - b, sh)), (int((sw - b) * k), h))
    mid = pygame.transform.smoothscale(src.subsurface((a, 0, b - a, sh)), (max(1, int((b - a) * k)), h))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    x, flip = left.get_width(), False
    end = w - right.get_width()
    while x < end:
      t = pygame.transform.flip(mid, True, False) if flip else mid
      out.blit(t, (x, 0), (0, 0, min(t.get_width(), end - x), h))
      x += t.get_width()
      flip = not flip
    out.blit(left, (0, 0))
    out.blit(right, (end, 0))
    return out
  return _cache(('scrollart', w, h), build)


def _bg_fit():
  src = ART.img('background')
  sw, sh = src.get_size()
  k = max(WIDTH / float(sw), HEIGHT / float(sh))
  w, h = int(sw * k + 0.5), int(sh * k + 0.5)
  return k, (WIDTH - w) // 2, (HEIGHT - h) // 2, w, h


def art_study_backdrop():
  def build():
    k, ox, oy, w, h = _bg_fit()
    s = pygame.Surface((WIDTH, HEIGHT))
    s.blit(pygame.transform.smoothscale(ART.img('background'), (w, h)), (ox, oy))
    r = SCROLL_ART
    s.blit(scroll_art(r.w, r.h), r.topleft)
    return s.convert()
  return _cache(('artstudy', WIDTH, HEIGHT), build)


def art_candles(surf, anim):
  """the candles painted into the background flicker"""
  k, ox, oy, _w, _h = _bg_fit()
  for i, (x, y) in enumerate(OA.CANDLES):
    f = 0.75 + 0.25 * math.sin(anim * (9 + i) + i * 2.1) + 0.1 * math.sin(anim * 23 + i)
    add_glow(surf, int(ox + x * k), int(oy + y * k), int((30 if i < 2 else 40) * (0.85 + 0.25 * f)), (int(60 * f), int(36 * f), 8))


def art_title(surf, label, cy, anim):
  w = 430
  pl = ART.img('title_plaque')
  h = int(pl.get_height() * w / float(pl.get_width()))
  p = ART.scaled('title_plaque', w, h)
  r = p.get_rect(center=(WIDTH // 2, cy))
  surf.blit(p, r)
  t = ENV.fire_text(label, 44)
  surf.blit(t, t.get_rect(center=(WIDTH // 2, cy - 1)))
  return r


def art_slider(surf, x0, x1, y, v, col, hot):
  """your slider: the bar, a coloured fill in its well and the gold handle"""
  L, T, R, B = OA.TRACK_IN
  tw0, th0 = ART.img('slider_track').get_size()
  k = (x1 - x0) / float(R - L)
  tw, th = int(tw0 * k), max(10, int(th0 * k))
  tx, ty = int(x0 - L * k), int(y - th / 2)
  surf.blit(ART.scaled('slider_track', tw, th), (tx, ty))
  fx = x0 + int((x1 - x0) * v / 100.0)
  top, bot = int(ty + T * k) + 1, int(ty + B * k) - 1
  if fx > x0 + 1:
    hgt = max(2, bot - top)
    pygame.draw.rect(surf, tuple(max(0, c - 60) for c in col), (x0 + 1, top, fx - x0 - 1, hgt), border_radius=max(1, hgt // 2))
    pygame.draw.rect(surf, col, (x0 + 1, top, fx - x0 - 1, max(1, hgt - 2)), border_radius=max(1, hgt // 2))
    pygame.draw.line(surf, tuple(min(255, c + 90) for c in col), (x0 + 3, top + 1), (fx - 3, top + 1), 1)
  hw0, hh0 = ART.img('slider_handle').get_size()
  hh = int(th * 1.35)
  hw = max(6, int(hw0 * hh / float(hh0)))
  if hot:
    add_glow(surf, fx, y, 24, (60, 46, 10))
  surf.blit(ART.scaled('slider_handle', hw, hh), (fx - hw // 2, int(y - hh / 2)))


def art_toggle(surf, x, y, pos, on, hot):
  w, h = 58, 29
  surf.blit(ART.scaled('toggle_track', w, h), (x, y - h // 2))
  L, T, R, B = OA.TOGGLE_IN
  k = w / float(ART.img('toggle_track').get_width())
  d = int(h * 0.86)
  kx = int(x + L * k + d / 2 + (((R - L) * k) - d) * pos)
  if hot:
    add_glow(surf, kx, y, 20, (30, 50, 20) if on else (60, 20, 14))
  surf.blit(ART.scaled('knob_on' if on else 'knob_off', d, d), (kx - d // 2, y - d // 2))


def draw_art_study(surf, game, anim, rows, sliders, track):
  surf.blit(art_study_backdrop(), (0, 0))
  art_candles(surf, anim)
  fl, fv = _ink_font(21), _ink_font(19)
  m = getattr(game, 'mouse', (-1, -1))
  knobs = game.__dict__.setdefault('opt_knob', {})
  for k, (name, val, on, r) in rows.items():
    hot = r.collidepoint(m) or getattr(game, 'opt_drag', None) == k
    if hot:
      surf.blit(_cache(('opthl', r.w, r.h), lambda: _hl_surf(r.w + 16, r.h)), (r.x - 8, r.y))
    ic = ART.scaled(ART_ICONS.get(k, 'icon_music'), 42, 42)
    surf.blit(ic, (r.left + 1, r.centery - 21))
    im = fl.render(name, True, INK)
    surf.blit(im, im.get_rect(midleft=(r.left + 52, r.centery)))
    surf.blit(three_slice('divider', r.w - 30, 12, 24), (r.left + 30, r.bottom - 1))
    if k in sliders:
      x0, x1, y = track(r)
      art_slider(surf, x0, x1, y, on, ART_FILL.get(k, (200, 60, 50)), hot)
      im = fv.render(str(on), True, INK_GREEN if on else INK_RED)
      surf.blit(im, im.get_rect(midright=(r.right - 4, r.centery)))
    else:
      p = knobs.get(k, 1.0 if on else 0.0)
      p += ((1.0 if on else 0.0) - p) * 0.35
      knobs[k] = p
      art_toggle(surf, r.right - 60, r.centery, p, on, hot)
      im = fv.render(val, True, INK_GREEN if on else INK_RED)
      surf.blit(im, im.get_rect(midright=(r.right - 70, r.centery)))


def art_footer(surf, txt):
  y = SCROLL_ART.bottom - 34
  im = _ink_font(16).render(txt, True, (70, 44, 20))
  r = im.get_rect(center=(WIDTH // 2, y))
  surf.blit(im, r)
  orn = ART.scaled('footer_ornament', 60, 20)
  surf.blit(orn, (r.left - 72, y - 10))
  surf.blit(pygame.transform.flip(orn, True, False), (r.right + 12, y - 10))


ART_ICONS = {'music': 'icon_music', 'sfx': 'icon_sound', 'display': 'icon_display', 'weather': 'icon_weather',
             'difficulty': 'icon_difficulty', 'shake': 'icon_camera', 'vibrate': 'icon_vibration'}
ART_FILL = {'music': (200, 34, 30), 'sfx': (50, 180, 50)}
ART_TABS = {'home': 'tab_home', 'lair': 'tab_den', 'roster': 'tab_roster', 'hoard': 'tab_hoard', 'quests': 'tab_quests',
            'enemies': 'tab_bestiary', 'eggs': 'tab_eggs', 'hatchlings': 'tab_babies', 'options': 'tab_options'}


def draw_art_tab_bar(surf, active, anim, mouse, badges=()):
  bar = TAB_BAR.inflate(60, 8)
  surf.blit(three_slice('tabbar', bar.w, bar.h, 52), bar.topleft)
  f = _small_label_font()
  for k, lab, r in tab_rects():
    on = k == active
    hov = r.collidepoint(mouse)
    cx = r.centerx
    if on:
      pulse = (math.sin(anim * 4) + 1) / 2
      add_glow(surf, cx, r.centery, 30 + int(pulse * 6), (70, 40, 8))
      surf.blit(nine_slice('tab_selected', r.w + 4, r.h + 4, 30, 0.34), (r.x - 2, r.y - 2))
    ic0 = ART.img(ART_TABS[k])
    ih = 36 if not on else 38
    iw = int(ic0.get_width() * ih / float(ic0.get_height()))
    cy = r.top + 19 - (2 if on else 0) - (1 if hov and not on else 0)
    surf.blit(ART.scaled(ART_TABS[k], iw, ih), (cx - iw // 2, cy - ih // 2))
    ly = r.bottom - 11
    if on:                                         # bright label with a dark outline so it reads on the red frame
      dk = f.render(lab, True, (30, 12, 4))
      for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        surf.blit(dk, dk.get_rect(center=(cx + dx, ly + dy)))
      img = f.render(lab, True, (255, 226, 120))
    else:
      img = text(f, lab, (236, 226, 206))
    surf.blit(img, img.get_rect(center=(cx, ly)))
    if k in badges:
      draw_badge(surf, cx + 14, cy - 15, anim)


# ---------------------------------------------------------------- the Den / Lair from your painted cave art
LAIR_ART_ICONS = {'roster': 'icon_lair_roster', 'hoard': 'icon_lair_hoard', 'quests': 'icon_lair_quests',
                  'enemies': 'icon_lair_enemies', 'eggs': 'icon_lair_eggs', 'hatchlings': 'icon_lair_hatchlings'}


COVER_KEEP = {'best_bg': (285, 1590), 'quest_bg': (560, 1310)}   # parts that must stay fully on screen (x range in the art)


def _cover(name):
  """scale factor and offset that make a background fill the whole screen
  (shrunk on narrow screens so the part in COVER_KEEP still fits)"""
  sw, sh = ART.img(name).get_size()
  k = max(WIDTH / float(sw), HEIGHT / float(sh))
  keep = COVER_KEEP.get(name)
  if keep and (keep[1] - keep[0]) * k > WIDTH - 8:
    k = (WIDTH - 8) / float(keep[1] - keep[0])
    w, h = int(sw * k + 0.5), int(sh * k + 0.5)
    return k, int(WIDTH / 2.0 - (keep[0] + keep[1]) / 2.0 * k), (HEIGHT - h) // 2, w, h
  w, h = int(sw * k + 0.5), int(sh * k + 0.5)
  return k, (WIDTH - w) // 2, (HEIGHT - h) // 2, w, h


def _cover_surf(name):
  def build():
    k, ox, oy, w, h = _cover(name)
    s = pygame.Surface((WIDTH, HEIGHT))
    if h < HEIGHT or w < WIDTH:                       # (narrow screen: a dimmed full-cover copy fills the gaps)
      kk = max(WIDTH / float(ART.img(name).get_width()), HEIGHT / float(ART.img(name).get_height()))
      big = pygame.transform.smoothscale(ART.img(name), (int(ART.img(name).get_width() * kk + 0.5), int(ART.img(name).get_height() * kk + 0.5)))
      s.blit(big, ((WIDTH - big.get_width()) // 2, (HEIGHT - big.get_height()) // 2))
      s.fill((70, 62, 58), special_flags=pygame.BLEND_RGB_MULT)
    s.blit(pygame.transform.smoothscale(ART.img(name), (w, h)), (ox, oy))
    return s.convert()
  return _cache(('cover', name, WIDTH, HEIGHT), build)


def art_sign(label, k, w, h, hover):
  def build():
    s = three_slice('sign', w, h, 60).copy()
    ic0 = ART.img(LAIR_ART_ICONS[k])
    ih = int(h * 0.74)
    iw = int(ic0.get_width() * ih / float(ic0.get_height()))
    s.blit(ART.scaled(LAIR_ART_ICONS[k], iw, ih), (int(h * 0.42), (h - ih) // 2))
    room = w - (int(h * 0.42) + iw + 14) - 20
    for sz in (26, 24, 22, 20, 18, 16):
      t = small_fire(label, sz)
      if t.get_width() <= room:
        break
    x0 = int(h * 0.42) + iw + 10
    s.blit(t, t.get_rect(center=(x0 + (w - x0 - 16) // 2, h // 2 - 1)))
    if hover:
      s.fill((26, 20, 8), special_flags=pygame.BLEND_RGB_ADD)
    return s
  return _cache(('artsign', label, k, w, h, hover), build)


def art_chain(surf, x, y0, y1):
  """your chain tiled from y0 down to y1, centred on x"""
  c0 = ART.img('chain')
  cw = 12
  ch = int(c0.get_height() * cw / float(c0.get_width()))
  tile = ART.scaled('chain', cw, ch)
  y = y0
  while y < y1:
    surf.blit(tile, (x - cw // 2, y), (0, 0, cw, min(ch, y1 - y)))
    y += ch - 2


def art_coin_panel(surf, coins, y=12):
  r = pygame.Rect(WIDTH - 184, y, 170, 46)
  surf.blit(ART.scaled('coin_box', r.w, r.h), r.topleft)
  c = ART.scaled('coin', 30, 31)
  surf.blit(c, (r.left + 14, r.centery - 15))
  f = _C.get('coinfont')
  if f is None:
    f = _C['coinfont'] = pygame.font.SysFont("serif", 26, bold=True)
  t = f.render(str(coins), True, (244, 236, 214))
  surf.blit(t, t.get_rect(midleft=(r.left + 52, r.centery + 1)))


def art_stone_title(surf, label, cy, anim):
  w, h = 470, 112
  p = ART.scaled('lair_plaque', w, h)
  r = p.get_rect(center=(WIDTH // 2, cy))
  surf.blit(p, r)
  t = ENV.fire_text(label, 46)
  surf.blit(t, t.get_rect(center=(WIDTH // 2, cy - 1)))
  return r


def art_lights(surf, name, lights, anim):
  k, ox, oy, _w, _h = _cover(name)
  for i, (x, y, rad) in enumerate(lights):
    f = 0.75 + 0.2 * math.sin(anim * (8 + i * 0.7) + i * 1.9) + 0.1 * math.sin(anim * 21 + i)
    add_glow(surf, int(ox + x * k), int(oy + y * k), int(rad * k * (0.9 + 0.2 * f)), (int(54 * f), int(32 * f), 6))


def draw_art_den(surf, game, anim):
  """the Lair: your painted cave, your dragon asleep on the hoard, a live fire and your signs on chains"""
  t = anim
  surf.blit(_cover_surf('lair_bg'), (0, 0))
  art_lights(surf, 'lair_bg', LA.LIGHTS, t)
  k, ox, oy, _w, _h = _cover('lair_bg')
  fx, fy = int(ox + LA.FIRE_PIT[0] * k), int(oy + LA.FIRE_PIT[1] * k)
  fl = (math.sin(t * 11) + math.sin(t * 7.3)) * 0.5
  add_glow(surf, fx, fy - 40, 200 + int(fl * 12), (70, 34, 8))
  hx, hy = int(ox + LA.HOARD_TOP[0] * k), int(oy + LA.HOARD_TOP[1] * k)
  add_glow(surf, hx, hy, 150, (70, 50, 10))
  from fd_art import draw_any_dragon                 # the selected dragon, asleep on the gold (drawn big)
  import fd_pixart as _PX
  tmp = _C.get('dragtmp')
  if tmp is None:
    tmp = _C['dragtmp'] = pygame.Surface((168, 128), pygame.SRCALPHA)
  tmp.fill((0, 0, 0, 0))
  draw_any_dragon(tmp, game.selected, _PX.OX, _PX.OY, 0, 0.0, False)
  dk = 1.275                                          # (25% smaller than before)
  big = pygame.transform.scale(tmp, (int(168 * dk), int(128 * dk)))
  bob = int(math.sin(t * 1.6) * 2)
  surf.blit(big, (hx - int(84 * dk), hy - int(104 * dk) + 22 + bob))
  for j in range(3):                                  # z z z
    ph = (t * 0.45 + j / 3.0) % 1.0
    zx, zy = hx + 72 + int(ph * 44) + int(math.sin(ph * 6) * 6), hy - 110 - int(ph * 80)
    z = text(_z_font(12 + j * 5 + int(ph * 7)), "z", (230, 220, 255))
    z.set_alpha(int(255 * (1 - ph)))
    surf.blit(z, (zx, zy))
  for j in range(6):                                  # gold glints
    ph = (t * 0.8 + j * 0.37) % 1.0
    if ph < 0.25:
      sx, sy = hx - 180 + j * 70, hy + 40 + (j % 2) * 30
      rr = int(1 + 5 * math.sin(ph / 0.25 * math.pi))
      pygame.draw.line(surf, (255, 250, 210), (sx - rr, sy), (sx + rr, sy), 1)
      pygame.draw.line(surf, (255, 250, 210), (sx, sy - rr), (sx, sy + rr), 1)
  fire_flames(surf, fx, fy, t, 1.0)                   # flames in your painted fire pit
  for j in range(9):                                  # embers
    ph = (t * 0.6 + j * 0.113) % 1.0
    ex = fx + math.sin(j * 2.1 + ph * 5) * (20 + 30 * ph)
    ey = fy - 40 - ph * 150
    pygame.draw.circle(surf, (255, int(200 - 120 * ph), 60), (int(ex), int(ey)), 2 if ph < 0.5 else 1)
  for kk, label, col, bg, border in LAIR_ITEMS:        # your signs on chains
    r = LAIR_RECTS[kk]
    hov = r.collidepoint(game.mouse)
    top = 0 if r.y < 200 else r.y - 44
    for ax in (r.x + 34, r.right - 34):
      art_chain(surf, ax, top, r.y + 8)
    if hov:
      add_glow(surf, r.centerx, r.centery, r.w // 2 + 10, (90, 50, 10))
    surf.blit(art_sign(LAIR_LABELS.get(kk, label), kk, r.w, r.h, hov), r.topleft)
    if kk == 'eggs' and game.eggs_ready():
      draw_badge(surf, r.right - 10, r.y + 8, t)


# ---------------------------------------------------------------- the Hoard / Dragon's Forge from your painted forge art
UPG_GLOW = {'thick_scales': (20, 50, 110), 'deep_lungs': (110, 50, 10), 'coin_magnet': (100, 24, 24)}


def _tint(name, w, h, mode):
  """a greyed-out (can't afford) or brightened (hover) copy of a stretched piece"""
  def build():
    s = three_slice(name, w, h, 60).copy()
    if mode == 'grey':
      s.fill((120, 116, 112), special_flags=pygame.BLEND_RGB_MULT)
    else:
      s.fill((34, 26, 10), special_flags=pygame.BLEND_RGB_ADD)
    return s
  return _cache(('tint', name, w, h, mode), build)


def art_wide_title(surf, label, cy, anim, size=44, minw=470):
  """the stone title plaque, stretched to fit a long name"""
  t = ENV.fire_text(label, size)
  w = max(minw, t.get_width() + 150)
  surf.blit(three_slice('lair_plaque', w, 112, 260), (WIDTH // 2 - w // 2, cy - 56))
  surf.blit(t, t.get_rect(center=(WIDTH // 2, cy - 1)))


def draw_art_forge(surf, game, anim):
  t = anim
  surf.blit(_cover_surf('forge_bg'), (0, 0))
  art_lights(surf, 'forge_bg', FA.LIGHTS, t)
  k, ox, oy, _w, _h = _cover('forge_bg')
  cx0, cy0, hw = FA.COALS
  pulse = 0.7 + 0.3 * math.sin(t * 2.3) + 0.1 * math.sin(t * 7.1)
  add_glow(surf, int(ox + cx0 * k), int(oy + cy0 * k), int(hw * k * (1.0 + 0.1 * pulse)), (int(80 * pulse), int(34 * pulse), 4))
  for j in range(10):                                  # embers drifting up from the coals
    ph = (t * 0.5 + j * 0.1) % 1.0
    ex = ox + (cx0 + math.sin(j * 2.7 + ph * 4) * hw * 0.8) * k
    ey = oy + (cy0 - ph * 150) * k
    pygame.draw.circle(surf, (255, int(210 - 130 * ph), 60), (int(ex), int(ey)), 2 if ph < 0.5 else 1)
  coins = game.data['coins']
  fn = _ink_font(15)
  ff = pygame.font.SysFont("serif", 24, bold=True) if 'pricefont' not in _C else _C['pricefont']
  _C['pricefont'] = ff
  ay = int(oy + FA.ANVILS[0][1] * k)
  for i, (key, title, desc, rect) in enumerate(UPGRADES):
    lvl = game.data['upgrades'][key]
    cx = rect.centerx
    for ax in (cx - 86, cx + 86):                      # chains up to the beams
      art_chain(surf, ax, 0, 182)
    surf.blit(three_slice('forge_sign', 240, 50, 40), (cx - 120, 175))
    for sz in (24, 22, 20, 18):
      tt = small_fire(title.upper(), sz)
      if tt.get_width() <= 200:
        break
    surf.blit(tt, tt.get_rect(center=(cx, 199)))
    surf.blit(three_slice('forge_label', 220, 30, 30), (cx - 110, 229))
    im = fn.render(desc, True, (60, 34, 12))
    surf.blit(im, im.get_rect(center=(cx, 244)))
    name = 'icon_upg_' + key                           # the upgrade glowing on its anvil
    ic0 = ART.img(name)
    ih = 76
    iw = int(ic0.get_width() * ih / float(ic0.get_height()))
    bob = int(math.sin(t * 2 + i * 1.3) * 3)
    add_glow(surf, cx, ay - 36 + bob, 54 + int(4 * math.sin(t * 3 + i)), (40, 90, 30) if lvl >= 3 else UPG_GLOW.get(key, (90, 54, 10)))
    surf.blit(ART.scaled(name, iw, ih), (cx - iw // 2, ay - ih + 2 + bob))
    btn = upgrade_btn(rect)                            # price plaque on the pedestal
    if lvl < 3:
      cost = UPGRADE_COSTS[lvl]
      ok = coins >= cost
      hov = ok and btn.collidepoint(game.mouse)
      if hov:
        add_glow(surf, btn.centerx, btn.centery, 80, (90, 50, 10))
      pl = _tint('price_plaque', btn.w, btn.h, 'grey') if not ok else (_tint('price_plaque', btn.w, btn.h, 'hot') if hov else three_slice('price_plaque', btn.w, btn.h, 60))
      surf.blit(pl, btn.topleft)
      c = ART.scaled('coin', 28, 29)
      if not ok:
        c = c.copy()
        c.fill((130, 126, 120), special_flags=pygame.BLEND_RGB_MULT)
      surf.blit(c, (btn.centerx - 54, btn.centery - 14))
      im = ff.render(str(cost), True, (250, 240, 220) if ok else (200, 170, 160))
      surf.blit(im, im.get_rect(midleft=(btn.centerx - 18, btn.centery + 1)))
    else:                                              # maxed: the star medal
      surf.blit(three_slice('price_plaque', btn.w, btn.h, 60), btn.topleft)
      md = ART.scaled('star_medal', 36, 35)
      surf.blit(md, (btn.centerx - 70, btn.centery - 17))
      tt = small_fire("MASTERED", 18)
      surf.blit(tt, tt.get_rect(center=(btn.centerx + 18, btn.centery)))
    for j in range(3):                                 # level ingots under the plaque
      nm = 'ingot_on' if j < lvl else 'ingot_off'
      g0 = ART.img(nm)
      gh = 20
      gw = int(g0.get_width() * gh / float(g0.get_height()))
      surf.blit(ART.scaled(nm, gw, gh), (cx - 36 + j * 36 - gw // 2, 510))


# ---------------------------------------------------------------- the Bestiary from your painted library art
def _bg_rect(name, box):
  k, ox, oy, _w, _h = _cover(name)
  l, t, r, b = box
  return pygame.Rect(int(ox + l * k), int(oy + t * k), int((r - l) * k), int((b - t) * k))


def art_page_rects():
  l = _bg_rect('best_bg', BA.PAGE_L)
  r = _bg_rect('best_bg', BA.PAGE_R)
  top, bot = max(l.top, r.top), min(l.bottom, r.bottom)
  return pygame.Rect(l.x, top, l.w, bot - top), pygame.Rect(r.x, top, r.w, bot - top)


def art_corner_rects():
  return _bg_rect('best_bg', BA.CORNER_L), _bg_rect('best_bg', BA.CORNER_R)


def crop_frame(name, w, h):
  """your picture frame at (w, h): the scene is cropped to fit (never squashed) and the frame edges rebuilt around it"""
  def build():
    src = ART.img(name)
    sw, sh = src.get_size()
    k = h / float(sh)
    ws = min(sw, int(w / k))
    e = BA.FRAME_EDGE.get(name, 12)
    x0 = (sw - ws) // 2
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    ek = max(1, int(e * k))
    out.blit(pygame.transform.smoothscale(src.subsurface((0, 0, e, sh)), (ek, h)), (0, 0))
    out.blit(pygame.transform.smoothscale(src.subsurface((sw - e, 0, e, sh)), (ek, h)), (w - ek, 0))
    mid = src.subsurface((x0 + e, 0, ws - 2 * e, sh))
    out.blit(pygame.transform.smoothscale(mid, (w - 2 * ek, h)), (ek, 0))
    return out
  return _cache(('cropframe', name, w, h), build)


def _blank_page(side):
  l, r = art_page_rects()
  pr = l if side == 'L' else r
  return _cache(('blankpage', side, WIDTH), lambda: _cover_surf('best_bg').subsurface(tuple(pr.clip(pygame.Rect(0, 0, WIDTH, HEIGHT)))).copy())


def art_best_page(info, side, num):
  """the printed part of one Bestiary page (everything but the moving creature)"""
  key, name, kind, desc, stars, attack, weak, appears, pts = info
  def build():
    s = _blank_page(side).copy()
    w, h = s.get_size()
    ink, red, faint = (52, 30, 14), (150, 30, 20), (120, 96, 60)
    boss = kind == "BOSS"
    sz = 26
    f1 = _ink_font(sz)
    while f1.size(name)[0] > w - 70 and sz > 14:
      sz -= 2
      f1 = _ink_font(sz)
    im = f1.render(name, True, red if boss else ink)
    s.blit(im, im.get_rect(center=(w // 2, 24)))
    sub = _ink_font(14).render("~ %s ~" % ("Boss" if boss else kind.title()), True, red if boss else faint)
    sr = sub.get_rect(center=(w // 2, 48))
    s.blit(sub, sr)
    fl = ART.scaled('ink_flourish', 66, 14)
    s.blit(fl, (sr.left - 72, sr.centery - 7))
    s.blit(pygame.transform.flip(fl, True, False), (sr.right + 6, sr.centery - 7))
    fr = pygame.Rect(18, 62, w - 36, 104)
    fname = 'frame_boss' if boss else ('frame_forest' if kind == "FLYING" else 'frame_ruins')
    s.blit(crop_frame(fname, fr.w, fr.h), fr.topleft)
    for fs_ in (13, 12, 11):
      f3 = _ink_font(fs_)
      dl = _wrap(f3, desc, w - 56)
      if len(dl) <= 3:
        break
    if len(dl) > 3:
      dl = dl[:3]
      dl[2] = dl[2].rstrip('.,') + '...'
    y = fr.bottom + 6
    for ln in dl:
      s.blit(f3.render(ln, True, ink), (28, y))
      y += 15
    s.blit(three_slice('ink_divider', w - 50, 12, 30), (25, 222))
    f4 = _ink_font(13)
    sn, sf = ART.scaled('star_on', 15, 14), ART.scaled('star_off', 15, 14)
    for i, (lab, v) in enumerate(zip(("Danger", "Toughness", "Speed"), stars)):
      cx = 30 + (w - 60) * (2 * i + 1) // 6
      im = f4.render(lab, True, ink)
      s.blit(im, im.get_rect(center=(cx, 240)))
      for j in range(5):
        s.blit(sn if j < v else sf, (cx - 40 + j * 16, 249))
    s.blit(three_slice('ink_divider', w - 50, 12, 30), (25, 266))
    f5 = _ink_font(13)
    coin = ART.scaled('coin', 13, 13)
    for i, (lab, val) in enumerate((("Attack", attack), ("Weak to", weak), ("Appears", appears), ("Bounty", pts + " pts"))):
      yy = 288 + i * 17
      s.blit(f5.render(lab + ":", True, red), (52, yy - 8))
      vx = 128
      if lab == "Bounty":
        s.blit(coin, (vx, yy - 7))
        vx += 17
      v_ = val
      while f5.size(v_)[0] > w - vx - 30 and len(v_) > 4:
        v_ = v_[:-2].rstrip() + "."
      s.blit(f5.render(v_, True, ink), (vx, yy - 8))
    return s
  return _cache(('artbpage', key, side, num, WIDTH), build)


def draw_art_book(surf, game, anim, art_fn):
  """the open book on your library desk: two beasts per spread, flick or tap the gold corners to turn"""
  surf.blit(_cover_surf('best_bg'), (0, 0))
  art_lights(surf, 'best_bg', BA.LIGHTS, anim)
  info = ENEMY_INFO
  n_spreads = (len(info) + 1) // 2
  lr, rr = art_page_rects()

  def page(i, side):
    if 0 <= i < len(info):
      s = art_best_page(info[i], side, i + 1).copy()
      w = s.get_width()
      spr = art_fn(info[i][0], anim + i * 0.37, w - 70, 92)
      s.blit(spr, (w // 2 - spr.get_width() // 2, 62 + 104 - 8 - spr.get_height()))
      return s
    return _blank_page(side)

  cur = game.en_page
  fl = getattr(game, 'en_flip', None)
  p = None
  if fl:
    p = (pygame.time.get_ticks() - fl[1]) / 340.0
    if p >= 1.0:
      game.en_flip, p = None, None
  if p is None:
    surf.blit(page(cur * 2, 'L'), lr)
    surf.blit(page(cur * 2 + 1, 'R'), rr)
  else:
    d, old = fl[0], cur - fl[0]
    e = p * p * (3 - 2 * p)
    W = lr.w
    if d > 0:                                          # next: the right page lifts and falls to the left
      surf.blit(page(old * 2, 'L'), lr)
      surf.blit(page(cur * 2 + 1, 'R'), rr)
      if e < 0.5:
        w = max(1, int(rr.w * (1 - 2 * e)))
        surf.blit(pygame.transform.scale(page(old * 2 + 1, 'R'), (w, rr.h)), (rr.left, rr.top))
      else:
        w = max(1, int(W * (2 * e - 1)))
        surf.blit(pygame.transform.scale(page(cur * 2, 'L'), (w, lr.h)), (lr.right - w, lr.top))
    else:                                              # back: the left page lifts and falls to the right
      surf.blit(page(cur * 2, 'L'), lr)
      surf.blit(page(old * 2 + 1, 'R'), rr)
      if e < 0.5:
        w = max(1, int(W * (1 - 2 * e)))
        surf.blit(pygame.transform.scale(page(old * 2, 'L'), (w, lr.h)), (lr.right - w, lr.top))
      else:
        w = max(1, int(rr.w * (2 * e - 1)))
        surf.blit(pygame.transform.scale(page(cur * 2 + 1, 'R'), (w, rr.h)), (rr.left, rr.top))
    sh = pygame.Surface((14, lr.h), pygame.SRCALPHA)
    sh.fill((40, 20, 10, int(110 * math.sin(e * math.pi))))
    surf.blit(sh, ((lr.right + rr.left) // 2 - 7, lr.top))
  ca, cb = art_corner_rects()                          # your gold page-turn tabs
  m = getattr(game, 'mouse', (-1, -1))
  bob = int(math.sin(anim * 4) * 1.5)
  for rect, nm, show in ((ca, 'tab_left', cur > 0), (cb, 'tab_right', cur < n_spreads - 1)):
    if show:
      if rect.collidepoint(m):
        add_glow(surf, rect.centerx, rect.centery, 40, (90, 60, 10))
      surf.blit(ART.scaled(nm, rect.w, rect.h), (rect.x, rect.y + bob))


# ---------------------------------------------------------------- Realm Quests from your painted notice board
def _outlined(font, txt, col, dark=(30, 14, 4)):
  im = font.render(txt, True, col)
  dk = font.render(txt, True, dark)
  out = pygame.Surface((im.get_width() + 2, im.get_height() + 2), pygame.SRCALPHA)
  for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2), (2, 2)):
    out.blit(dk, (dx, dy))
  out.blit(im, (1, 1))
  return out


def art_quest_bar(surf, x, y, w, frac, done):
  """your progress bar with the fill in its groove"""
  b0 = ART.img('quest_bar')
  h = max(12, int(b0.get_height() * w / float(b0.get_width())))
  surf.blit(three_slice('quest_bar', w, h, 90), (x, y))
  L, T, R, B = QA.BAR_IN
  k = w / float(b0.get_width())
  gx0, gx1 = x + int(L * k) + 1, x + int(R * k) - 1
  gy0, gy1 = y + int(T * k) + 1, y + int(B * k) - 1
  fx = gx0 + int((gx1 - gx0) * max(0.0, min(1.0, frac)))
  if fx > gx0 + 1:
    col = (70, 170, 50) if done else (200, 50, 30)
    pygame.draw.rect(surf, tuple(max(0, c - 60) for c in col), (gx0, gy0, fx - gx0, gy1 - gy0), border_radius=3)
    pygame.draw.rect(surf, col, (gx0, gy0, fx - gx0, max(1, gy1 - gy0 - 2)), border_radius=3)
    pygame.draw.line(surf, tuple(min(255, c + 90) for c in col), (gx0 + 2, gy0 + 1), (fx - 2, gy0 + 1), 1)
  return pygame.Rect(x, y, w, h)


def art_stamp(surf, cx, cy, w, scale=1.0):
  """the red COMPLETE stamp: your stamp border with the word inked inside, at the same tilt"""
  def build():
    st0 = ART.img('stamp')
    h = int(st0.get_height() * w / float(st0.get_width()))
    base = ART.scaled('stamp', w, h).copy()
    sz = max(12, int(w * 0.15))
    f = _ink_font(sz)
    while f.size("COMPLETE")[0] > w * 0.62 and sz > 10:
      sz -= 1
      f = _ink_font(sz)
    word = f.render("COMPLETE", True, (196, 28, 22))
    word = pygame.transform.rotate(word, QA.STAMP_TILT)
    word.set_alpha(225)
    base.blit(word, word.get_rect(center=(w // 2, h // 2)))
    return base
  st = _cache(('artstamp', w), build)
  if scale != 1.0:
    st = pygame.transform.smoothscale(st, (int(st.get_width() * scale), int(st.get_height() * scale)))
  surf.blit(st, st.get_rect(center=(cx, cy)))


def draw_art_quests(surf, game, anim):
  t = anim
  surf.blit(_cover_surf('quest_bg'), (0, 0))
  art_lights(surf, 'quest_bg', QA.LIGHTS, t)
  d = game.data
  q = d['active_quest']
  nq = d.get('next_quest')
  ink, red, gold = (52, 30, 14), (150, 30, 20), (120, 76, 10)
  coin = ART.scaled('coin', 18, 18)
  big = _bg_rect('quest_bg', QA.POSTER)                # the current quest on the big poster
  f1, f2, f3 = _ink_font(20), _ink_font(18), _ink_font(16)
  hd = f1.render("BOUNTY WANTED", True, red)
  surf.blit(hd, hd.get_rect(center=(big.centerx, big.top + 38)))
  pygame.draw.line(surf, red, (big.left + 30, big.top + 52), (big.right - 30, big.top + 52), 2)
  y = big.top + 62
  for ln in _wrap(f2, q['desc'], big.w - 44)[:3]:
    im = f2.render(ln, True, ink)
    surf.blit(im, im.get_rect(midtop=(big.centerx, y)))
    y += f2.get_height() + 1
  rw = f3.render("Reward: %d gold" % quest_gold(q), True, gold)
  rr = rw.get_rect(midtop=(big.centerx + 11, y + 6))
  surf.blit(coin, (rr.left - 22, rr.top))
  surf.blit(rw, rr)
  frac = min(1.0, q['progress'] / float(max(1, q['target'])))
  br = art_quest_bar(surf, big.left + 22, big.bottom - 58, big.w - 44, frac, q.get('done'))
  pt = _outlined(_ink_font(15), "{:,} / {:,}".format(min(q['progress'], q['target']), q['target']), (252, 240, 214))
  surf.blit(pt, pt.get_rect(center=br.center))
  if q.get('done'):                                    # the stamp slams down when the quest is done
    seen = game.__dict__.setdefault('stamp_seen', {})
    t0 = seen.setdefault(q['desc'], pygame.time.get_ticks())
    u = min(1.0, (pygame.time.get_ticks() - t0) / 260.0)
    art_stamp(surf, big.centerx, big.centery + 6, int(big.w * 0.78), 1.0 + 0.7 * (1 - u) ** 2)
  if nq:                                               # the next quest on the small poster
    sm = _bg_rect('quest_bg', QA.POSTER2)
    f4, f5, f6 = _ink_font(16), _ink_font(14), _ink_font(13)
    hd = f4.render("UP NEXT", True, red)
    surf.blit(hd, hd.get_rect(center=(sm.centerx, sm.top + 32)))
    pygame.draw.line(surf, red, (sm.left + 26, sm.top + 44), (sm.right - 26, sm.top + 44), 1)
    y = sm.top + 54
    for ln in _wrap(f5, nq['desc'], sm.w - 36)[:3]:
      im = f5.render(ln, True, ink)
      surf.blit(im, im.get_rect(midtop=(sm.centerx, y)))
      y += f5.get_height() + 1
    rw = f6.render("Reward: %d gold" % quest_gold(nq), True, gold)
    rr = rw.get_rect(midtop=(sm.centerx + 9, y + 6))
    surf.blit(ART.scaled('coin', 15, 15), (rr.left - 18, rr.top))
    surf.blit(rw, rr)
  k, ox, oy, _w, _h = _cover('quest_bg')               # your pinned tag: how many quests are done
  tx, ty = int(ox + QA.TAG_AT[0] * k), int(oy + QA.TAG_AT[1] * k)
  tg = ART.scaled('quest_tag', 62, 90)
  surf.blit(tg, (tx - 4, ty - 6))
  im = _ink_font(11).render("QUESTS", True, ink)
  surf.blit(im, im.get_rect(center=(tx + 27, ty + 28)))
  im = _ink_font(11).render("DONE", True, ink)
  surf.blit(im, im.get_rect(center=(tx + 27, ty + 41)))
  im = _ink_font(22).render(str(d['completed_quests']), True, red)
  surf.blit(im, im.get_rect(center=(tx + 27, ty + 62)))
  if q['type'] in ('distance', 'score') and not q.get('done'):
    im = _outlined(_ink_font(14), "your best single run counts", (250, 236, 200))
    surf.blit(im, im.get_rect(center=(big.centerx, int(oy + QA.BOARD_BOTTOM * k) + 14)))


# ---------------------------------------------------------------- Roster / Mythical stables from your painted barn
def _frac_rect(r, f):
  return pygame.Rect(r.x + int(r.w * f[0]), r.y + int(r.h * f[1]), int(r.w * (f[2] - f[0])), int(r.h * (f[3] - f[1])))


def _fit_text(label, maxw, size, col, fire=False):
  sz = size
  while True:
    im = small_fire(label, sz) if fire else _ink_font(sz).render(label, True, col)
    if im.get_width() <= maxw or sz <= 9:
      return im
    sz -= 1


def _stall_dragon(key, box, sil):
  """the dragon (or its dark shape) scaled to stand in a stall opening"""
  from fd_art import draw_any_dragon
  import fd_pixart as _PX
  if sil:
    src = dragon_silhouette(key)
  else:
    src = _C.get('stalltmp')
    if src is None:
      src = _C['stalltmp'] = pygame.Surface((168, 128), pygame.SRCALPHA)
    src.fill((0, 0, 0, 0))
    draw_any_dragon(src, key, _PX.OX, _PX.OY, 0, pygame.time.get_ticks() / 140.0 + box.x * 0.01, False)
  k = min(box.w / 168.0, box.h / 128.0) * 1.25
  im = pygame.transform.scale(src, (int(168 * k), int(128 * k)))
  return im


def draw_art_stables(surf, game, boxes, rare, pal_of, anim):
  surf.blit(_cover_surf('stable_bg'), (0, 0))
  art_lights(surf, 'stable_bg', SA.LIGHTS, anim)
  m = getattr(game, 'mouse', (-1, -1))
  hovered = game.selected if game.selected in [b[0] for b in boxes] else boxes[0][0]
  for key, rect in boxes:
    if rect.collidepoint(m) and not game.pending:
      hovered = key
    unlocked = key in game.data['unlocked']
    sel = game.selected == key
    hov = rect.collidepoint(m) and not game.pending
    if sel:
      add_glow(surf, rect.centerx, rect.centery, rect.w // 2 + 30, (90, 64, 10))
    sh = 'stall_gold' if sel else 'stall'
    surf.blit(ART.scaled(sh, rect.w, rect.h), rect.topleft)
    op = _frac_rect(rect, SA.OPENING)
    im = _stall_dragon(key, op, not unlocked)
    clip = surf.get_clip()
    surf.set_clip(op)
    surf.blit(im, (op.centerx - im.get_width() // 2, op.bottom - im.get_height() + int(op.h * 0.08)))
    surf.set_clip(clip)
    if not unlocked:                                   # your bars and padlock over locked dragons
      surf.blit(ART.scaled('stall_bars', op.w, op.h), op.topleft)
    elif hov and not sel:
      add_glow(surf, op.centerx, op.centery, op.w // 2, (40, 30, 10))
    pr = _frac_rect(rect, SA.PLATE)
    pal = pal_of(key)
    t1 = _fit_text(pal['title'], pr.w - 22, 16, (40, 20, 4))
    status = "RIDING" if sel else ("IN THE STABLE" if unlocked else "%d COINS" % pal['cost'])
    t2 = _fit_text(status, pr.w - 22, 12, (20, 90, 20) if sel else ((70, 40, 10) if unlocked else (150, 20, 20)))
    surf.blit(t1, t1.get_rect(center=(pr.centerx, pr.centery - 8)))
    surf.blit(t2, t2.get_rect(center=(pr.centerx, pr.centery + 9)))
  return hovered


def art_desc_plate(surf, rect, desc):
  surf.blit(three_slice('brass_long', rect.w, rect.h, 40), rect.topleft)
  lines = _wrap(_ink_font(14), desc, rect.w - 50)
  if len(lines) > 2:
    lines = _wrap(_ink_font(12), desc, rect.w - 50)[:2]
    f = _ink_font(12)
  else:
    f = _ink_font(14)
  n = len(lines)
  for i, ln in enumerate(lines):
    im = f.render(ln, True, (50, 24, 6))
    surf.blit(im, im.get_rect(center=(rect.centerx, rect.centery + (i - (n - 1) / 2.0) * (f.get_height() - 1))))


def art_wood_button(surf, rect, label, hov):
  b = three_slice('wood_button', rect.w, rect.h, 40)
  if hov:
    b = b.copy()
    b.fill((30, 22, 8), special_flags=pygame.BLEND_RGB_ADD)
    add_glow(surf, rect.centerx, rect.centery, rect.w // 2, (70, 44, 8))
  surf.blit(b, rect.topleft)
  t = _fit_text(label, rect.w - 50, 20, None, True)
  surf.blit(t, t.get_rect(center=(rect.centerx, rect.centery)))


# ---------------------------------------------------------------- The Hatchery from your painted egg room
def art_egg(rar, h, wobble=0.0):
  e0 = ART.img('egg_' + rar)
  w = int(e0.get_width() * h / float(e0.get_height()))
  im = ART.scaled('egg_' + rar, w, h)
  if abs(wobble) > 0.4:
    im = pygame.transform.rotate(im, wobble)
  return im


def egg_in_cradle(surf, cx, rim_y, cw, egg, back=True):
  """an egg sitting IN your iron cradle: the back of the cradle, the egg resting in the bowl,
  then the front rim and bars over its lower half. rim_y is the top of the rim."""
  c0 = ART.img('egg_cradle')
  ch = int(c0.get_height() * cw / float(c0.get_width()))
  cr = ART.scaled('egg_cradle', cw, ch)
  x0 = cx - cw // 2
  if back:
    surf.blit(cr, (x0, rim_y))
  ex = cx - egg.get_width() // 2
  ey = rim_y + int(ch * 0.6) - egg.get_height()       # its bottom rests in the bowl
  surf.blit(egg, (ex, ey))
  fy = int(ch * 0.2)                                   # the front rim and bars, drawn over the egg
  surf.blit(cr, (x0, rim_y + fy), (0, fy, cw, ch - fy))
  return ex, ey


def draw_art_egg_card(surf, r, rar, n, hov, t, i, egg_glow):
  """one egg on your frame: the egg in its iron cradle over a little fire, the rarity on the brass plate"""
  sh = 'egg_frame_gold' if hov else 'egg_frame'
  surf.blit(ART.scaled(sh, r.w, r.h), r.topleft)
  pr = _frac_rect(r, EA.PLATE)
  cx = r.centerx
  cw = int(r.w * 0.56)
  c0 = ART.img('egg_cradle')
  ch = int(c0.get_height() * cw / float(c0.get_width()))
  rim_y = pr.top - ch + 4                              # the cradle stands on the brass plate
  fire_flames(surf, cx, rim_y + int(ch * 0.78), t * 1.1 + i, 0.3)
  add_glow(surf, cx, rim_y, 50, egg_glow)
  eh = int(r.h * 0.42)
  if n > 1:                                            # a little pile behind the front egg
    for k in range(min(2, n - 1)):
      b = art_egg(rar, int(eh * 0.78))
      surf.blit(b, (cx + (-1 if k == 0 else 1) * int(r.w * 0.2) - b.get_width() // 2, rim_y + int(ch * 0.45) - b.get_height()))
  e = art_egg(rar, eh, math.sin(t * 2.4 + i) * 4)
  egg_in_cradle(surf, cx, rim_y, cw, e)
  label = "%s  x%d" % (RARITY_NAME.get(rar, rar.title()), n) if n > 1 else RARITY_NAME.get(rar, rar.title())
  tt = _fit_text(label, pr.w - 18, 15, (60, 28, 6))
  surf.blit(tt, tt.get_rect(center=pr.center))


RARITY_NAME = {'common': 'Common', 'uncommon': 'Uncommon', 'rare': 'Rare', 'epic': 'Epic', 'legendary': 'Legendary'}


# ---------------------------------------------------------------- Hatching Hearths from your painted hearth room
def hearth_backdrop():
  """your hearth room drawn from the top of the screen (so its title shows); a dimmed copy fills any gap at the sides"""
  def build():
    s = pygame.Surface((WIDTH, HEIGHT))
    s.blit(_cover_surf('hearth_bg'), (0, 0))
    s.fill((90, 80, 76), special_flags=pygame.BLEND_RGB_MULT)
    k = HEARTH_K
    s.blit(pygame.transform.smoothscale(ART.img('hearth_bg'), (int(HA.ART_W * k), int(HA.ART_H * k))), (HEARTH_OX, 0))
    return s.convert()
  return _cache(('hearthbg', WIDTH, HEIGHT), build)


def hearth_pt(x, y):
  return int(HEARTH_OX + x * HEARTH_K), int(y * HEARTH_K)


def hearth_lights(surf, anim):
  for i, (x, y, rad) in enumerate(HA.LIGHTS):
    f = 0.75 + 0.2 * math.sin(anim * (8 + i * 0.7) + i * 1.9) + 0.1 * math.sin(anim * 21 + i)
    px, py = hearth_pt(x, y)
    add_glow(surf, px, py, int(rad * HEARTH_K * (0.9 + 0.2 * f)), (int(54 * f), int(32 * f), 6))


# ---------------------------------------------------------------- Aftermath Report from your painted war room
def report_backdrop():
  def build():
    s = pygame.Surface((WIDTH, HEIGHT))
    s.blit(_cover_surf('report_bg'), (0, 0))
    s.fill((90, 80, 76), special_flags=pygame.BLEND_RGB_MULT)
    k = REPORT_K
    s.blit(pygame.transform.smoothscale(ART.img('report_bg'), (int(RA.ART_W * k), int(RA.ART_H * k))), (REPORT_OX, REPORT_OY))
    return s.convert()
  return _cache(('reportbg', WIDTH, HEIGHT), build)


def report_pt(x, y):
  return int(REPORT_OX + x * REPORT_K), int(REPORT_OY + y * REPORT_K)


# ---------------------------------------------------------------- detail pages from your painted trophy room
def info_backdrop():
  def build():
    s = pygame.Surface((WIDTH, HEIGHT))
    s.fill((20, 12, 8))
    k = INFO_K
    s.blit(pygame.transform.smoothscale(ART.img('info_bg'), (int(IA.ART_W * k), int(IA.ART_H * k))), (INFO_OX, INFO_OY))
    return s.convert()
  return _cache(('infobg', WIDTH, HEIGHT), build)


def info_title(surf, label):
  tr = info_rect(IA.TITLE)
  for sz in (44, 40, 36, 32, 28, 24):
    t = ENV.fire_text(label, sz)
    if t.get_width() <= tr.w - 50:
      break
  surf.blit(t, t.get_rect(center=tr.center))


def red_button(surf, rect, label, hov, off=False):
  b = three_slice('red_button', rect.w, rect.h, 70)
  if off:
    b = b.copy()
    b.fill((130, 120, 116), special_flags=pygame.BLEND_RGB_MULT)
  elif hov:
    b = b.copy()
    b.fill((34, 16, 6), special_flags=pygame.BLEND_RGB_ADD)
    add_glow(surf, rect.centerx, rect.centery, rect.w // 2, (80, 30, 8))
  surf.blit(b, rect.topleft)
  t = _fit_text(label, rect.w - 70, 20, None, True)
  if off:
    t = t.copy()
    t.fill((150, 140, 130), special_flags=pygame.BLEND_RGB_MULT)
  surf.blit(t, t.get_rect(center=(rect.centerx, rect.centery + (1 if hov else 0))))


def gold_star(surf, x, y, on, size=19):
  surf.blit(ART.scaled('gstar_on' if on else 'gstar_off', size, size), (int(x) - size // 2, int(y) - size // 2))


def gold_divider(surf, x0, x1, y):
  w = x1 - x0
  surf.blit(three_slice('gold_divider', w, 12, 40), (x0, y - 6))


def pedestal(surf, cx, bottom, w):
  p0 = ART.img('pedestal')
  h = int(p0.get_height() * w / float(p0.get_width()))
  surf.blit(ART.scaled('pedestal', w, h), (cx - w // 2, bottom - h))


# ---------------------------------------------------------------- the live main menu from your painted night battlement
CLOUDS = (('cloud_a', 0.0, 34, 0.55, 230), ('cloud_b', 0.37, 92, 0.35, 190), ('cloud_c', 0.66, 18, 0.8, 210), ('cloud_d', 0.18, 130, 0.25, 160))


def _cloud_surf(name, w, alpha):
  def build():
    c0 = ART.img(name)
    h = int(c0.get_height() * w / float(c0.get_width()))
    s = ART.scaled(name, w, h).copy()
    s.set_alpha(alpha)
    return s
  return _cache(('cloudsurf', name, w, alpha), build)


def draw_live_menu_bg(surf, anim):
  """your scene, brought to life: drifting clouds, twinkling stars, flickering windows, a rippling moonlit lake, burning braziers"""
  t = anim
  surf.blit(_cover_surf('menu_bg'), (0, 0))
  k, ox, oy, _w, _h = _cover('menu_bg')
  P = lambda x, y: (int(ox + x * k), int(oy + y * k))
  for i, (x, y) in enumerate(MA.STARS):                # stars twinkle
    tw = math.sin(t * (1.6 + (i % 5) * 0.37) + i * 2.3)
    if tw > 0.55:
      px, py = P(x, y)
      rr = 1 + int((tw - 0.55) * 7)
      c = (255, 255, 230)
      pygame.draw.line(surf, c, (px - rr, py), (px + rr, py), 1)
      pygame.draw.line(surf, c, (px, py - rr), (px, py + rr), 1)
  mx, my, mr = MA.MOON                                 # the moon breathes a soft halo
  px, py = P(mx, my)
  add_glow(surf, px, py, int(mr * k * (1.9 + 0.08 * math.sin(t * 0.8))), (22, 22, 34))
  for name, ph, y, spd, al in CLOUDS:                  # clouds drift slowly across the sky
    c = _cloud_surf(name, int(ART.img(name).get_width() * 0.62), al)
    span = WIDTH + c.get_width()
    cx = int(((t * spd * 12 + ph * span) % span) - c.get_width())
    surf.blit(c, (cx, int(y * k * 0.9)))
  for i, (x, y, n) in enumerate(MA.WINDOWS):           # windows and lamps flicker
    f = 0.55 + 0.25 * math.sin(t * (3.1 + (i % 7) * 0.53) + i * 1.7) + 0.2 * math.sin(t * 11.3 + i * 0.9)
    px, py = P(x, y)
    rad = 6 + min(14, int(n ** 0.5 * 1.4))
    add_glow(surf, px, py, rad, (int(70 * f), int(38 * f), 6))
  l, tp, r, bt = MA.LAKE                               # the lake ripples, with the moon on it
  x0, y0 = P(l, tp)
  x1, y1 = P(r, bt)
  mrx = P(mx, my)[0]
  for j in range(16):
    yy = y0 + 3 + (j * (y1 - y0 - 6)) // 16
    u = (j + 1) / 17.0
    for q in range(3):
      sx = x0 + int(((t * (14 + j * 3) + q * 310 + j * 97) % (x1 - x0)))
      ln = 10 + (j % 4) * 6
      pygame.draw.line(surf, (70, 90, 150), (sx, yy), (min(x1, sx + ln), yy), 1)
    wob = int(math.sin(t * 2.2 + j * 0.9) * (3 + u * 6))
    w_ = int((10 + u * 30) * (0.8 + 0.2 * math.sin(t * 3 + j)))
    pygame.draw.line(surf, (236, 232, 200), (mrx - w_ // 2 + wob, yy), (mrx + w_ // 2 + wob, yy), 1)
  for i, (x, y) in enumerate(MA.BRAZIERS):             # the braziers burn
    px, py = P(x, y)
    fire_flames(surf, px, py + 4, t * 1.05 + i * 1.7, 0.62)
    add_glow(surf, px, py - 40, 120, (60, 26, 4))
    for j in range(7):                                 # embers floating up
      ph = (t * 0.45 + j * 0.143 + i * 0.5) % 1.0
      ex = px + math.sin(j * 2.3 + ph * 6 + i) * (10 + 26 * ph)
      ey = py - 30 - ph * 170
      pygame.draw.circle(surf, (255, int(210 - 130 * ph), 60), (int(ex), int(ey)), 2 if ph < 0.4 else 1)
  for x in (ox + int(60 * k), ox + int(1806 * k)):     # banners catch the firelight
    add_glow(surf, x, int(oy + 330 * k), 60, (int(34 + 14 * math.sin(t * 6 + x)), 12, 2))


def draw_menu_title(surf, anim, y):
  w = 560
  t0 = ART.img('menu_title')
  h = int(t0.get_height() * w / float(t0.get_width()))
  r = pygame.Rect(WIDTH // 2 - w // 2, y, w, h)
  add_glow(surf, r.centerx, r.centery, 170, (40, 18, 6))
  surf.blit(ART.scaled('menu_title', w, h), r.topleft)
  for sx, sy, ph in ((-0.33, 0.28, 0.0), (0.2, 0.22, 1.7), (0.36, 0.62, 3.1)):     # glints on the gold
    rr = int(2 + 6 * ((math.sin(anim * 3 + ph) + 1) / 2))
    cx, cy = int(r.left + (0.5 + sx) * w), int(r.top + sy * h)
    pygame.draw.line(surf, (255, 244, 190), (cx - rr, cy), (cx + rr, cy), 1)
    pygame.draw.line(surf, (255, 244, 190), (cx, cy - rr), (cx, cy + rr), 1)
  return r


def draw_menu_record(surf, rect, score):
  surf.blit(three_slice('menu_record', rect.w, rect.h, 90), rect.topleft)
  t = _fit_text("REALM RECORD: %d" % score, rect.w - 110, 18, (244, 232, 206))
  surf.blit(t, t.get_rect(center=rect.center))


# ---------------------------------------------------------------- Aftermath report: the war tent
def tent_backdrop():
  def build():
    rng = random.Random(44)
    s = pygame.Surface((WIDTH, HEIGHT))
    s.fill((60, 44, 30))
    cx = WIDTH // 2
    n = 14
    for i in range(n):                                 # canvas panels fanning down from the peak
      x0 = int(-WIDTH * 0.3 + i * WIDTH * 1.6 / n)
      x1 = int(-WIDTH * 0.3 + (i + 1) * WIDTH * 1.6 / n)
      c = (150, 120, 80) if i % 2 else (124, 40, 34)
      v = rng.randint(-8, 8)
      c = (c[0] + v, c[1] + v, c[2] + v)
      pygame.draw.polygon(s, c, [(cx, -40), (x0, HEIGHT), (x1, HEIGHT)])
      pygame.draw.line(s, (40, 28, 18), (cx, -40), (x0, HEIGHT), 2)
    pygame.draw.rect(s, (58, 40, 22), (cx - 8, 0, 16, HEIGHT))     # centre pole
    pygame.draw.line(s, (90, 62, 34), (cx - 4, 0), (cx - 4, HEIGHT), 2)
    pygame.draw.rect(s, (54, 40, 26), (0, HEIGHT - 90, WIDTH, 90))  # trampled dirt floor
    for _ in range(300):
      pygame.draw.circle(s, rng.choice(((70, 52, 32), (44, 32, 20), (80, 60, 36))), (rng.randint(0, WIDTH), rng.randint(HEIGHT - 88, HEIGHT)), rng.randint(1, 3))
    for bx, flip in ((60, False), (WIDTH - 150, True)):      # weapon rack
      pygame.draw.rect(s, (70, 46, 24), (bx, HEIGHT - 260, 90, 10))
      pygame.draw.rect(s, (70, 46, 24), (bx, HEIGHT - 120, 90, 10))
      for k in range(3):
        x = bx + 15 + k * 30
        pygame.draw.line(s, (90, 60, 30), (x, HEIGHT - 300), (x, HEIGHT - 95), 4)
        pygame.draw.polygon(s, (170, 170, 180), [(x, HEIGHT - 330), (x - 7, HEIGHT - 298), (x + 7, HEIGHT - 298)])
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
      shade.fill((10, 4, 0, int(160 * abs(y / float(HEIGHT) - 0.45))), (0, y, WIDTH, 1))
    s.blit(shade, (0, 0))
    return s.convert()
  return _cache(('tent', WIDTH, HEIGHT), build)


def scroll_sheet(w, h, seed):
  """parchment scroll with wooden rollers top and bottom"""
  def build():
    s = pygame.Surface((w + 24, h + 30), pygame.SRCALPHA)
    s.blit(parchment(w, h, seed), (12, 15))
    for y in (2, h + 16):
      pygame.draw.rect(s, (20, 12, 6), (2, y + 3, w + 22, 14), border_radius=7)
      pygame.draw.rect(s, (110, 70, 34), (0, y, w + 24, 14), border_radius=7)
      pygame.draw.line(s, (160, 110, 60), (6, y + 3), (w + 18, y + 3), 2)
      for x in (0, w + 16):
        pygame.draw.rect(s, GOLD_D, (x, y - 2, 8, 18), border_radius=3)
        pygame.draw.rect(s, GOLD, (x, y - 2, 8, 18), 1, border_radius=3)
    return s
  return _cache(('scroll', w, h, seed), build)


def lantern(surf, x, y, anim):
  pygame.draw.line(surf, (40, 30, 20), (x, 0), (x, y - 20), 2)
  g = pygame.Surface((160, 160))
  f = 0.85 + 0.15 * math.sin(anim * 9)
  pygame.draw.circle(g, (int(36 * f), int(24 * f), 6), (80, 80), 78)
  pygame.draw.circle(g, (int(56 * f), int(40 * f), 12), (80, 80), 40)
  surf.blit(g, (x - 80, y - 70), special_flags=pygame.BLEND_RGB_ADD)
  pygame.draw.rect(surf, (40, 34, 30), (x - 12, y - 20, 24, 34), border_radius=3)
  pygame.draw.rect(surf, (255, 190, 80), (x - 8, y - 14, 16, 22))
  pygame.draw.ellipse(surf, (255, 240, 180), (x - 3, y - 8, 6, 12))
  for k in (-8, 0, 8):
    pygame.draw.line(surf, (40, 34, 30), (x + k, y - 14), (x + k, y + 8), 2)
  pygame.draw.polygon(surf, (40, 34, 30), [(x - 14, y - 20), (x + 14, y - 20), (x, y - 30)])


def tally(surf, x, y, n, col=(52, 30, 14)):
  """hand-scratched tally marks (groups of five); returns the width used"""
  gx = x
  for g in range(n // 5):
    for k in range(4):
      pygame.draw.line(surf, col, (gx + k * 5, y - 8), (gx + k * 5 + 1, y + 8), 2)
    pygame.draw.line(surf, (150, 30, 20), (gx - 3, y + 6), (gx + 19, y - 6), 2)
    gx += 28
  for k in range(n % 5):
    pygame.draw.line(surf, col, (gx + k * 5, y - 8), (gx + k * 5 + 1, y + 8), 2)
  return gx + (n % 5) * 5 - x
