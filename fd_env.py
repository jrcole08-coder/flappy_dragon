"""Environment + menu art: pixel-art scenery and runners, textured ground, medieval title, stone crest, big play button."""
import math
import random
import pygame
from fd_core import *
import fd_pixart as PX
from fd_folk import folk_frame
from fd_pixart import _poly, _ell, _line, _outline, shade, lite

OUT_G = (12, 34, 18)


def _mk(w, h, fn, outline, flip=False):
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  fn(s)
  s = _outline(s, outline)
  s = pygame.transform.scale(s, (w * 2, h * 2))
  if flip:
    s = pygame.transform.flip(s, True, False)
  return s


def _put(key, surf, ox, oy):
  SPRITE_CACHE[key] = (ck(surf), ox, oy)


def _leafy(s, cx, cy, r, dark, base, light, rng, dots=10):
  pygame.draw.circle(s, dark, (cx, cy), r)
  pygame.draw.circle(s, base, (cx - r // 5, cy - r // 5), max(1, r - 2))
  pygame.draw.circle(s, light, (cx - r // 3, cy - r // 2), max(1, r // 2))
  for _ in range(dots):
    a, d = rng.uniform(0, 6.28), rng.uniform(0, r - 2)
    px, py = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)
    s.set_at((px, py), light if rng.random() < 0.5 else dark)


def draw_oak(s, seed=1):
  rng = random.Random(seed)
  W, H = s.get_size()
  cx = W // 2
  tr, tm, tl = (60, 38, 22), (92, 62, 36), (124, 88, 52)
  _poly(s, tr, [(cx - 7, H - 1), (cx - 4, H - 24), (cx + 4, H - 24), (cx + 8, H - 1)])
  _poly(s, tm, [(cx - 5, H - 1), (cx - 3, H - 24), (cx + 2, H - 24), (cx + 4, H - 1)])
  for k in range(4):
    s.set_at((cx - 2 + k % 2, H - 6 - k * 4), tr)
    s.set_at((cx + 1, H - 8 - k * 4), tl)
  _line(s, tr, (cx - 2, H - 20), (cx - 11, H - 30), 2)
  _line(s, tr, (cx + 2, H - 20), (cx + 11, H - 31), 2)
  D, B, L = (20, 76, 30), (38, 120, 46), (92, 170, 70)
  for (dx, dy, r) in ((-12, -26, 9), (11, -27, 9), (0, -34, 12), (-6, -20, 10), (8, -20, 10), (-15, -15, 7), (14, -15, 7)):
    _leafy(s, cx + dx, H + dy, r, D, B, L, rng, 8)
  for (dx, dy) in ((-8, -30), (4, -38), (10, -24)):
    pygame.draw.circle(s, (205, 50, 40), (cx + dx, H + dy), 1)
  for i in range(10):
    s.set_at((cx - 14 + i * 3, H - 9 + (i % 2)), D)


def draw_pine(s, seed=2):
  W, H = s.get_size()
  cx = W // 2
  _poly(s, (60, 38, 22), [(cx - 2, H - 1), (cx - 2, H - 12), (cx + 2, H - 12), (cx + 3, H - 1)])
  for i, (w, top, bot) in enumerate(((17, H - 32, H - 8), (14, H - 42, H - 20), (11, H - 50, H - 32), (7, H - 58, H - 42))):
    _poly(s, (16, 70, 40), [(cx - w, bot), (cx, top), (cx + w, bot)])
    _poly(s, (30, 104, 54), [(cx - w + 3, bot - 1), (cx, top + 2), (cx + 1, bot - 1)])
    _poly(s, (12, 52, 32), [(cx + 2, bot - 1), (cx + 1, top + 4), (cx + w - 1, bot - 1)])
    for k in range(3):
      s.set_at((cx - w + 4 + k * 5, bot - 2 - (k % 2)), (70, 150, 80))
    _line(s, (220, 232, 240), (cx - w + 2, bot - 1), (cx - w // 2, bot - 4), 1)


def draw_birch(s, seed=3):
  rng = random.Random(seed)
  W, H = s.get_size()
  cx = W // 2
  _poly(s, (212, 208, 196), [(cx - 3, H - 1), (cx - 2, H - 40), (cx + 2, H - 40), (cx + 3, H - 1)])
  _poly(s, (150, 146, 136), [(cx + 1, H - 1), (cx + 1, H - 40), (cx + 2, H - 40), (cx + 3, H - 1)])
  for k in range(7):
    _line(s, (30, 30, 34), (cx - 2, H - 6 - k * 5), (cx - 2 + (k % 2) + 1, H - 6 - k * 5), 1)
  _line(s, (190, 186, 176), (cx, H - 30), (cx - 9, H - 40), 1)
  _line(s, (190, 186, 176), (cx, H - 26), (cx + 9, H - 38), 1)
  D, B, L = (74, 128, 52), (122, 178, 70), (190, 222, 110)
  for (dx, dy, r) in ((-9, -38, 7), (9, -36, 7), (0, -46, 8), (-3, -32, 7), (5, -44, 6)):
    _leafy(s, cx + dx, H + dy, r, D, B, L, rng, 6)


def draw_bush(s, seed=4):
  rng = random.Random(seed)
  W, H = s.get_size()
  for (dx, dy, r) in ((-9, -7, 8), (8, -7, 8), (0, -11, 9)):
    _leafy(s, W // 2 + dx, H + dy, r, (18, 74, 28), (36, 112, 42), (84, 162, 66), rng, 7)
  for (dx, dy) in ((-8, -8), (3, -6), (9, -11), (-2, -14)):
    pygame.draw.circle(s, (200, 40, 60), (W // 2 + dx, H + dy), 1)
    s.set_at((W // 2 + dx - 1, H + dy - 1), (255, 150, 150))


def draw_grass(s, seed=5):
  rng = random.Random(seed)
  W, H = s.get_size()
  for i in range(7):
    x = 3 + i * 3
    h = rng.randint(7, 15)
    c = ((38, 120, 40), (62, 150, 56), (96, 184, 76))[i % 3]
    _line(s, c, (x, H - 1), (x + rng.randint(-3, 3), H - 1 - h), 1)
  for _ in range(2):
    s.set_at((rng.randint(2, W - 3), H - rng.randint(8, 14)), (250, 230, 120))


def draw_flowers(s, seed=6):
  rng = random.Random(seed)
  W, H = s.get_size()
  cols = ((235, 90, 110), (250, 215, 90), (170, 130, 235), (245, 245, 250))
  for i in range(6):
    x = 3 + i * 4 + rng.randint(-1, 1)
    h = rng.randint(6, 12)
    _line(s, (40, 120, 44), (x, H - 1), (x, H - 1 - h), 1)
    c = cols[(i + seed) % 4]
    pygame.draw.circle(s, c, (x, H - 1 - h), 2)
    s.set_at((x, H - 1 - h), (255, 240, 160))
  for i in range(5):
    _line(s, (70, 160, 60), (2 + i * 5, H - 1), (3 + i * 5 + (i % 2), H - 6), 1)


def draw_rock(s, seed=7):
  W, H = s.get_size()
  _poly(s, (84, 86, 96), [(1, H - 1), (3, H - 10), (10, H - 15), (19, H - 11), (22, H - 1)])
  _poly(s, (128, 130, 142), [(3, H - 10), (10, H - 15), (13, H - 9), (6, H - 5)])
  _poly(s, (58, 60, 70), [(13, H - 9), (19, H - 11), (22, H - 1), (11, H - 1)])
  for (x, y) in ((6, H - 3), (9, H - 5), (16, H - 4)):
    s.set_at((x, y), (70, 128, 60))
  _line(s, (60, 118, 52), (2, H - 3), (8, H - 7), 1)


SCENERY_ART = (("oak", 46, 54, draw_oak, OUT_G), ("pine", 40, 60, draw_pine, OUT_G), ("birch", 36, 56, draw_birch, (30, 50, 30)),
               ("bush", 34, 24, draw_bush, OUT_G), ("rock", 24, 17, draw_rock, (28, 28, 36)))


def _mix(c, f):
  return tuple(max(0, min(255, int(v * f))) for v in c)


def draw_peasant(s, var, fr):
  W, H = s.get_size()
  ph = fr * math.pi / 2.0
  sw = int(round(math.sin(ph) * 3))
  lift = 1 if math.cos(ph) > 0.3 else 0
  cloth = ((184, 52, 48), (52, 92, 176), (84, 132, 64))[var % 3]
  skin, hair = (236, 188, 148), ((84, 52, 28), (40, 30, 24), (190, 140, 60))[var % 3]
  bob = 1 if fr % 2 == 0 else 0
  by = H - 1
  _line(s, (60, 44, 34), (9 - sw, by - 8), (9 - sw - 1, by - lift * 2), 2)
  _line(s, (60, 44, 34), (9 + sw, by - 8), (9 + sw + 1, by - (1 - lift) * 2), 2)
  pygame.draw.rect(s, (40, 30, 26), (9 - sw - 2, by - lift * 2, 3, 1))
  pygame.draw.rect(s, (40, 30, 26), (9 + sw, by - (1 - lift) * 2, 3, 1))
  _poly(s, _mix(cloth, 0.75), [(5, by - 8 - bob), (14, by - 8 - bob), (15, by - 3 - bob), (4, by - 3 - bob)])
  _poly(s, cloth, [(5, by - 17 - bob), (13, by - 17 - bob), (14, by - 7 - bob), (5, by - 7 - bob)])
  _line(s, (60, 40, 24), (5, by - 9 - bob), (14, by - 9 - bob), 1)
  s.set_at((9, by - 9 - bob), (230, 200, 90))
  _line(s, skin, (8, by - 15 - bob), (8 + sw * 2, by - 10 - bob), 1)
  _line(s, _mix(cloth, 0.8), (8, by - 16 - bob), (8 + sw, by - 12 - bob), 2)
  pygame.draw.circle(s, skin, (9, by - 21 - bob), 4)
  pygame.draw.rect(s, hair, (5, by - 26 - bob, 8, 3))
  pygame.draw.rect(s, hair, (5, by - 24 - bob, 2, 4))
  s.set_at((12, by - 21 - bob), (30, 20, 20))
  if var % 3 == 1:
    _poly(s, (90, 60, 40), [(3, by - 26 - bob), (15, by - 26 - bob), (13, by - 29 - bob), (6, by - 29 - bob)])
  if var % 3 == 0:
    _line(s, (110, 80, 50), (15, by - 20 - bob), (18, by - 1), 1)
    for k in range(3):
      _line(s, (150, 150, 160), (14 + k * 2, by - 21 - bob), (14 + k * 2, by - 24 - bob), 1)
  elif var % 3 == 2:
    _ell(s, (140, 104, 60), 1, by - 15 - bob, 6, 7)
    s.set_at((3, by - 13 - bob), (190, 150, 90))


def draw_sheep(s, fr):
  W, H = s.get_size()
  ph = fr * math.pi / 2.0
  sw = int(round(math.sin(ph) * 2))
  by = H - 1
  for dx, o in ((5, 0), (7, 1), (14, 1), (16, 0)):
    k = sw if o == 0 else -sw
    _line(s, (46, 40, 44), (dx, by - 5), (dx + k, by - (1 if (k > 0) else 0)), 1)
  hop = 1 if fr % 2 else 0
  for (cx, cy, r, c) in ((8, by - 8 - hop, 5, (214, 210, 204)), (13, by - 9 - hop, 5, (230, 226, 220)), (10, by - 11 - hop, 4, (244, 240, 236)), (16, by - 7 - hop, 3, (214, 210, 204))):
    pygame.draw.circle(s, c, (cx, cy), r)
  _ell(s, (54, 48, 52), 17, by - 12 - hop, 6, 5)
  s.set_at((20, by - 10 - hop), (240, 240, 240))
  _poly(s, (54, 48, 52), [(17, by - 12 - hop), (15, by - 10 - hop), (18, by - 10 - hop)])


def draw_deer(s, fr):
  W, H = s.get_size()
  ph = fr * math.pi / 2.0
  sw = int(round(math.sin(ph) * 4))
  by = H - 1
  fur, dk, bl = (176, 122, 70), (118, 78, 44), (236, 220, 190)
  for dx, o in ((6, 0), (8, 1), (17, 1), (19, 0)):
    k = sw if o == 0 else -sw
    _line(s, dk, (dx, by - 9), (dx + k, by - (2 if k > 0 else 0)), 1)
    s.set_at((dx + k, by), (40, 30, 26))
  hop = 1 if fr % 2 == 0 else 0
  _ell(s, dk, 4, by - 17 - hop, 18, 9)
  _ell(s, fur, 4, by - 18 - hop, 18, 8)
  _ell(s, bl, 7, by - 12 - hop, 12, 3)
  for k in range(4):
    s.set_at((8 + k * 3, by - 15 - hop), (236, 200, 150))
  _line(s, fur, (20, by - 15 - hop), (24, by - 22 - hop), 3)
  _ell(s, fur, 22, by - 25 - hop, 6, 4)
  s.set_at((26, by - 24 - hop), (24, 18, 18))
  s.set_at((28, by - 24 - hop), (24, 18, 18))
  _line(s, (214, 196, 160), (23, by - 26 - hop), (21, by - 31 - hop), 1)
  _line(s, (214, 196, 160), (21, by - 31 - hop), (18, by - 33 - hop), 1)
  _line(s, (214, 196, 160), (22, by - 29 - hop), (25, by - 33 - hop), 1)
  _line(s, (214, 196, 160), (25, by - 26 - hop), (28, by - 31 - hop), 1)
  _poly(s, bl, [(3, by - 16 - hop), (0, by - 18 - hop), (4, by - 13 - hop)])


RUNNERS = {"peasant": (41, 59, 4), "sheep": (24, 18, 1), "deer": (32, 36, 1)}


def runner_sprite(kind, var, fr):
  """Run-cycle frame facing left. Returns a colorkey surface."""
  k = ("run", kind, var, fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    w, h, _n = RUNNERS[kind]
    if kind == "peasant":
      fn = lambda s: draw_peasant(s, var, fr)
    elif kind == "sheep":
      fn = lambda s: draw_sheep(s, fr)
    else:
      fn = lambda s: draw_deer(s, fr)
    if kind == "peasant":
      spr = SPRITE_CACHE[k] = ck(folk_frame(var, fr))
      return spr
    spr = SPRITE_CACHE[k] = ck(_mk(w, h, fn, (26, 20, 20), flip=True))
  return spr


def build_ground():
  w, h = WIDTH // 2, GROUND_H // 2
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  rng = random.Random(5)
  for y in range(h):
    t = y / float(h)
    c = (int(78 - 40 * t), int(56 - 30 * t), int(36 - 20 * t))
    pygame.draw.line(s, c, (0, y), (w, y))
  for _ in range(260):
    x, y = rng.randint(0, w - 1), rng.randint(5, h - 1)
    s.set_at((x, y), rng.choice(((100, 74, 48), (52, 36, 24), (118, 90, 60), (40, 28, 18))))
  for _ in range(14):
    x, y = rng.randint(0, w - 12), rng.randint(6, h - 4)
    rw, rh = rng.randint(4, 8), rng.randint(2, 3)
    pygame.draw.ellipse(s, (70, 70, 78), (x, y, rw, rh))
    pygame.draw.ellipse(s, (120, 120, 130), (x + 1, y, max(1, rw - 3), 1))
  for _ in range(8):
    x, y = rng.randint(0, w - 14), rng.randint(6, h - 3)
    _line(s, (46, 32, 20), (x, y), (x + rng.randint(5, 12), y + rng.randint(-1, 2)), 1)
  pygame.draw.rect(s, (34, 92, 40), (0, 0, w, 4))
  pygame.draw.rect(s, (58, 130, 56), (0, 0, w, 2))
  pygame.draw.rect(s, (22, 64, 30), (0, 3, w, 2))
  for x in range(0, w, 2):
    hh = rng.randint(1, 4)
    c = rng.choice(((58, 130, 56), (88, 168, 70), (34, 92, 40)))
    _line(s, c, (x, 2), (x + rng.randint(-1, 1), 2 - hh), 1)
  for _ in range(18):
    s.set_at((rng.randint(0, w - 1), rng.randint(0, 2)), rng.choice(((240, 220, 110), (230, 100, 120), (200, 180, 250))))
  s = pygame.transform.scale(s, (WIDTH, GROUND_H))
  out = pygame.Surface((WIDTH, GROUND_H))
  out.fill((20, 14, 10))
  out.blit(s, (0, 0))
  return out.convert()


def decorate_hills(s, ys):
  rng = random.Random(9)
  dark = shade(HILL_MID, 0.62)
  light = shade(HILL_MID, 0.82)
  x = 8
  while x < WIDTH - 8:
    y = int(ys[min(len(ys) - 1, x // 4)]) + 4
    h = rng.randint(12, 22)
    c = dark if rng.random() < 0.6 else light
    for t in range(3):
      _poly(s, c, [(x - 5 + t, y - t * 6), (x, y - h + 4 - t * 4), (x + 5 - t, y - t * 6)])
    x += rng.randint(14, 34)


def decorate_peaks(s, ys):
  snow, snow2 = (104, 112, 148), (70, 76, 106)
  for i in range(2, len(ys) - 2):
    if ys[i] < ys[i - 1] and ys[i] <= ys[i + 1] and ys[i] < 95:
      x, y = i * 4, int(ys[i])
      _poly(s, snow2, [(x, y + 1), (x + 18, y + 24), (x + 10, y + 19), (x + 4, y + 27), (x - 4, y + 19), (x - 14, y + 23)])
      _poly(s, snow, [(x, y + 1), (x - 5, y + 14), (x - 12, y + 20), (x - 3, y + 17), (x + 2, y + 22), (x + 3, y + 9)])


def build_fg_hill():
  W2, H2 = 100, 30
  s = pygame.Surface((W2, H2), pygame.SRCALPHA)
  rng = random.Random(3)
  pygame.draw.ellipse(s, (18, 40, 20), (0, 0, W2, H2 * 2))
  pygame.draw.ellipse(s, (30, 64, 32), (2, 1, W2 - 4, H2 * 2 - 3))
  pygame.draw.ellipse(s, (44, 88, 44), (8, 2, W2 - 20, 12))
  for _ in range(40):
    x = rng.randint(6, W2 - 7)
    y = int(H2 - 14 - 12 * math.sin(math.pi * x / W2)) if False else rng.randint(3, 12)
    s.set_at((x, y), rng.choice(((70, 130, 60), (28, 60, 30), (110, 170, 80))))
  for x in range(10, W2 - 10, 3):
    y = 2 + int(5 - 5 * math.sin(math.pi * (x - 10) / (W2 - 20)) * 0.0) + rng.randint(0, 1)
    _line(s, (70, 130, 60), (x, y + 2), (x + rng.randint(-1, 1), y - rng.randint(1, 3)), 1)
  for _ in range(5):
    s.set_at((rng.randint(14, W2 - 15), rng.randint(2, 5)), rng.choice(((240, 220, 110), (230, 100, 120))))
  return pygame.transform.scale(s, (W2 * 2, H2 * 2))


def build_all():
  for key, w, h, fn, outl in SCENERY_ART:
    _put(key, _mk(w, h, fn, outl), w, h * 2)
  for i in range(3):
    _put("grass%d" % i, _mk(22, 17, lambda s, i=i: draw_grass(s, i + 1), (16, 50, 24)), 22, 34)
  for i in range(2):
    _put("flowers%d" % i, _mk(26, 15, lambda s, i=i: draw_flowers(s, i + 2), (16, 50, 24)), 26, 30)
  SPRITE_CACHE["fg_hill"] = (ck(build_fg_hill()), 0, 0)


FIRE_TEXT = ((255, 238, 150), (255, 196, 70), (232, 128, 34), (170, 62, 22))


def _grad(w, h, stops, rng):
  g = pygame.Surface((w, h))
  n = len(stops) - 1
  for y in range(h):
    t = y / float(max(1, h - 1)) * n
    i = min(n - 1, int(t))
    f = t - i
    a, b = stops[i], stops[i + 1]
    pygame.draw.line(g, tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3)), (0, y), (w, y))
  for _ in range(w * h // 14):
    x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
    g.set_at((x, y), rng.choice(((255, 236, 170), (120, 56, 20), (214, 150, 50), (90, 36, 14))))
  for _ in range(14):
    x, y = rng.randint(0, w - 1), rng.randint(0, h - 8)
    _line(g, (96, 44, 16), (x, y), (x + rng.randint(-5, 5), y + rng.randint(4, 12)), 1)
  return g


def build_title(sizes=(96, 72), stops=FIRE_TEXT, words=None):
  """Medieval title: bigger drop-caps, gold rim, dark outline, bevel, textured metal fill, drop shadow."""
  rng = random.Random(11)
  big = pygame.font.SysFont("serif", sizes[0], bold=True)
  sml = pygame.font.SysFont("serif", sizes[1], bold=True)
  parts = ((words, sml),) if words else (("F", big), ("lappy", sml), (" ", sml), ("D", big), ("ragon", sml))
  imgs = []
  x = 0
  for t, f in parts:
    im = f.render(t, True, (255, 255, 255))
    imgs.append((im, x, f.get_ascent()))
    x += im.get_width() - 2
  pad = 12
  asc = max(a for _i, _x, a in imgs)
  hh = max(im.get_height() + asc - a for im, _x, a in imgs)
  W, H = x + 2 * pad, hh + 2 * pad + 6
  out = pygame.Surface((W, H), pygame.SRCALPHA)
  layers = (((16, 6, 4), 4, 3), ((200, 140, 34), 2, 0), ((255, 232, 150), 0, 0))
  def stamp(col, offs, dx0=0, dy0=0):
    for im, ix, a in imgs:
      tint = pygame.Surface(im.get_size(), pygame.SRCALPHA)
      tint.fill(col + (255,))
      tint.blit(im, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
      for ox, oy in offs:
        out.blit(tint, (pad + ix + ox + dx0, pad + asc - a + oy + dy0))
  ring = lambda r: [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if dx * dx + dy * dy <= r * r + 1]
  stamp((10, 4, 3), [(0, 0)], 6, 8)
  stamp((20, 8, 6), ring(4))
  stamp((206, 146, 36), ring(2))
  stamp((255, 236, 160), [(-1, -1)])
  stamp((96, 40, 14), [(1, 1)])
  for im, ix, a in imgs:
    fill = pygame.Surface(im.get_size(), pygame.SRCALPHA)
    fill.blit(im, (0, 0))
    gr = _grad(im.get_width(), im.get_height(), stops, rng)
    fill.blit(gr, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    out.blit(fill, (pad + ix, pad + asc - a))
  return out


def build_crest(w=600, h=140):
  rng = random.Random(21)
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  pygame.draw.rect(s, (14, 12, 20), (0, 0, w, h), border_radius=16)
  y = 6
  row = 0
  while y < h - 6:
    bh = 16
    x = 6 - (row % 2) * 20
    while x < w - 6:
      bw = min(rng.randint(34, 52), w - 6 - x)
      if bw < 6:
        break
      v = rng.randint(-8, 10)
      c = (34 + v, 32 + v, 44 + v)
      pygame.draw.rect(s, c, (max(6, x + 1), y + 1, bw - 2, bh - 2))
      _line(s, (c[0] + 14, c[1] + 14, c[2] + 14), (max(6, x + 1), y + 1), (max(6, x + 1) + bw - 3, y + 1), 1)
      _line(s, (8, 8, 12), (max(6, x + 1), y + bh - 1), (max(6, x + 1) + bw - 3, y + bh - 1), 1)
      x += bw
    y += bh
    row += 1
  for _ in range(240):
    s.set_at((rng.randint(8, w - 9), rng.randint(8, h - 9)), rng.choice(((20, 18, 26), (58, 56, 70), (28, 26, 36))))
  for i in range(18):
    a = int(150 * (1 - i / 18.0))
    d = pygame.Surface((w - 2 * i, 2), pygame.SRCALPHA)
    d.fill((0, 0, 0, a))
    s.blit(d, (i, i))
    s.blit(d, (i, h - i - 2))
  gold, gl, gd = (212, 160, 44), (255, 230, 140), (110, 74, 16)
  pygame.draw.rect(s, gd, (0, 0, w, h), 7, border_radius=16)
  pygame.draw.rect(s, gold, (1, 1, w - 2, h - 2), 4, border_radius=15)
  pygame.draw.rect(s, gl, (3, 3, w - 6, h - 6), 1, border_radius=13)
  pygame.draw.rect(s, gd, (12, 12, w - 24, h - 24), 2, border_radius=9)
  pygame.draw.rect(s, gold, (13, 13, w - 26, h - 26), 1, border_radius=9)
  for (cx, cy) in ((14, 14), (w - 14, 14), (14, h - 14), (w - 14, h - 14)):
    pygame.draw.circle(s, gd, (cx, cy), 8)
    pygame.draw.circle(s, gold, (cx, cy), 6)
    pygame.draw.circle(s, gl, (cx - 2, cy - 2), 2)
  ly = h - 16
  _line(s, gold, (60, ly), (w // 2 - 20, ly), 2)
  _line(s, gold, (w // 2 + 20, ly), (w - 60, ly), 2)
  _poly(s, gl, [(w // 2, ly - 7), (w // 2 + 8, ly), (w // 2, ly + 7), (w // 2 - 8, ly)])
  _poly(s, gold, [(w // 2, ly - 4), (w // 2 + 4, ly), (w // 2, ly + 4), (w // 2 - 4, ly)])
  for k in range(3):
    pygame.draw.circle(s, gold, (w // 2 - 36 - k * 12, ly), 2)
    pygame.draw.circle(s, gold, (w // 2 + 36 + k * 12, ly), 2)
  return s


def build_play_button(w=350, h=66, hover=False):
  rng = random.Random(31)
  s = pygame.Surface((w, h), pygame.SRCALPHA)
  top, bot = ((236, 66, 40), (150, 22, 16)) if hover else ((206, 48, 30), (116, 14, 12))
  for y in range(h):
    t = y / float(h)
    pygame.draw.line(s, tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3)), (0, y), (w, y))
  for _ in range(w * h // 40):
    s.set_at((rng.randint(6, w - 7), rng.randint(6, h - 7)), rng.choice(((250, 120, 70), (80, 8, 8), (170, 40, 28))))
  mask = pygame.Surface((w, h), pygame.SRCALPHA)
  pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=14)
  s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
  sheen = pygame.Surface((w - 16, h // 2 - 6), pygame.SRCALPHA)
  sheen.fill((255, 255, 255, 34))
  s.blit(sheen, (8, 6))
  gold, gl, gd = (232, 178, 52), (255, 238, 160), (110, 70, 12)
  pygame.draw.rect(s, gd, (0, 0, w, h), 6, border_radius=14)
  pygame.draw.rect(s, gold, (1, 1, w - 2, h - 2), 4, border_radius=13)
  pygame.draw.rect(s, gl, (3, 3, w - 6, h - 6), 1, border_radius=11)
  pygame.draw.rect(s, (60, 8, 6), (8, 8, w - 16, h - 16), 1, border_radius=8)
  for (cx, cy) in ((12, 12), (w - 12, 12), (12, h - 12), (w - 12, h - 12)):
    pygame.draw.circle(s, gd, (cx, cy), 5)
    pygame.draw.circle(s, gl, (cx - 1, cy - 1), 3)
  f = pygame.font.SysFont("serif", 40, bold=True)
  im = f.render("ENTER REALM", True, (255, 255, 255))
  gr = _grad(im.get_width(), im.get_height(), ((255, 250, 210), (255, 220, 120), (240, 170, 50)), rng)
  fill = pygame.Surface(im.get_size(), pygame.SRCALPHA)
  fill.blit(im, (0, 0))
  fill.blit(gr, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
  sh = f.render("ENTER REALM", True, (40, 4, 4))
  r = im.get_rect(center=(w // 2, h // 2 - 1))
  for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, 2), (2, -2), (-2, -2)):
    s.blit(sh, r.move(ox, oy))
  s.blit(sh, r.move(3, 4))
  s.blit(fill, r)
  return s.convert_alpha()


_MENU = {}


def menu_art():
  if not _MENU:
    try:
      for sizes in ((96, 72), (88, 66), (80, 60), (72, 54)):
        t = build_title(sizes)
        if t.get_width() <= 560:
          break
      _MENU['title'] = t.convert_alpha()
      _MENU['crest'] = build_crest().convert_alpha()
      _MENU['play'] = build_play_button(350, 66, False)
      _MENU['playh'] = build_play_button(350, 66, True)
    except Exception:
      _MENU['title'] = None
  return _MENU


_FIRE = {}


def fire_text(txt, size):
  k = (txt, size)
  if k not in _FIRE:
    try:
      _FIRE[k] = build_title((size, size), FIRE_TEXT, txt).convert_alpha()
    except Exception:
      f = pygame.font.SysFont("serif", size, bold=True)
      _FIRE[k] = f.render(txt, True, (255, 200, 80)).convert_alpha()
  return _FIRE[k]


_INTRO = {}


def intro_sky(day=False):
  k = 'sea_day' if day else 'sea_night'
  if k not in _INTRO:
    h = HEIGHT - 340
    s = pygame.Surface((WIDTH, h))
    for i in range(h):
      t = i / float(h)
      col = (int(60 - 25 * t), int(130 - 45 * t), int(185 - 55 * t)) if day else (int(22 - 12 * t), int(40 - 18 * t), int(84 - 30 * t))
      pygame.draw.line(s, col, (0, i), (WIDTH, i))
    _INTRO[k] = s
  if 'waves' not in _INTRO:
    rng = random.Random(5)
    _INTRO['waves'] = [[rng.uniform(0, WIDTH), rng.uniform(348, HEIGHT - 4), rng.uniform(0.4, 1.6), rng.randint(10, 36)] for _ in range(70)]
  return _INTRO[k], _INTRO['waves']
