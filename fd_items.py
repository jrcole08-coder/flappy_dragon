"""Detailed coin, power-up and nest art. Everything is drawn big with pygame primitives,
then smooth-scaled down once and cached, so the small sprites get soft, detailed edges."""
import math, random
import pygame
from fd_core import grayscale

_C = {}
def _sh(c, f):
  return tuple(max(0, min(255, int(v * f))) for v in c[:3])
def _mix(a, b, t):
  return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def _down(s, w, h):
  return pygame.transform.smoothscale(s, (w, h))
def _disc(s, cx, cy, r, inner, outer, light=(-0.35, -0.4)):
  """shaded sphere-ish disc: concentric circles shifting toward the light."""
  n = max(4, int(r))
  for k in range(n, 0, -1):
    t = k / n
    ox = cx + light[0] * r * (1 - t); oy = cy + light[1] * r * (1 - t)
    pygame.draw.circle(s, _mix(inner, outer, t), (int(ox), int(oy)), max(1, int(r * t)))

# ------------------------------------------------------------------ coins
GOLD_D, GOLD_M, GOLD_L, GOLD_W = (120, 70, 8), (214, 150, 26), (255, 214, 90), (255, 248, 200)
def _coin_face(style, R=48):
  S = R * 2
  s = pygame.Surface((S, S), pygame.SRCALPHA)
  c = (R, R)
  if style == 2:   # ancient rune coin: worn bronze-gold
    d, m, l = (90, 52, 18), (176, 118, 46), (236, 190, 110)
  else:
    d, m, l = GOLD_D, GOLD_M, GOLD_L
  pygame.draw.circle(s, d, c, R)
  _disc(s, R, R, R - 3, l, m)
  if style == 0:                      # dragon crest: beaded rim + dragon head relief
    pygame.draw.circle(s, d, c, R - 9, 3)
    for k in range(28):
      a = k * math.tau / 28
      pygame.draw.circle(s, l, (int(R + math.cos(a) * (R - 5)), int(R + math.sin(a) * (R - 5))), 2)
    pygame.draw.circle(s, _sh(m, 0.92), c, R - 12)
    _disc(s, R, R, R - 13, _sh(l, 1.02), _sh(m, 0.9))
    head = [(-20, 6), (-14, -4), (-8, -10), (-2, -22), (2, -12), (10, -14), (22, -6), (24, 0), (14, 2), (20, 8), (8, 8), (2, 16), (-6, 20), (-12, 14)]
    pts = [(R + x, R + y) for x, y in head]
    pygame.draw.polygon(s, d, [(x + 2, y + 2) for x, y in pts])
    pygame.draw.polygon(s, _sh(m, 1.05), pts)
    pygame.draw.lines(s, GOLD_W, False, pts[:6], 2)
    pygame.draw.circle(s, d, (R + 8, R - 6), 3)                      # eye
    pygame.draw.line(s, d, (R + 12, R + 3), (R + 20, R + 6), 2)      # mouth
  elif style == 1:                    # ruby set coin: reeded edge + faceted ruby
    for k in range(48):
      a = k * math.tau / 48
      pygame.draw.line(s, d, (R + math.cos(a) * (R - 1), R + math.sin(a) * (R - 1)), (R + math.cos(a) * (R - 7), R + math.sin(a) * (R - 7)), 2)
    pygame.draw.circle(s, d, c, R - 10, 2)
    pygame.draw.circle(s, l, c, R - 13, 1)
    for k in range(8):                                           # little laurel marks
      a = k * math.tau / 8 + 0.2
      x, y = R + math.cos(a) * (R - 17), R + math.sin(a) * (R - 17)
      pygame.draw.ellipse(s, _sh(m, 0.75), (x - 4, y - 2, 8, 5))
    pygame.draw.circle(s, d, c, 20)                              # bezel
    pygame.draw.circle(s, GOLD_L, c, 18)
    gem = [(R + math.cos(k * math.tau / 8 + math.pi / 8) * 15, R + math.sin(k * math.tau / 8 + math.pi / 8) * 15) for k in range(8)]
    pygame.draw.polygon(s, (120, 0, 20), gem)
    tab = [(R + math.cos(k * math.tau / 8 + math.pi / 8) * 8, R + math.sin(k * math.tau / 8 + math.pi / 8) * 8) for k in range(8)]
    cols = [(255, 70, 90), (230, 30, 50), (190, 10, 34), (150, 0, 24), (130, 0, 20), (160, 0, 26), (200, 16, 40), (240, 50, 70)]
    for k in range(8):
      pygame.draw.polygon(s, cols[k], [gem[k], gem[(k + 1) % 8], tab[(k + 1) % 8], tab[k]])
    pygame.draw.polygon(s, (220, 30, 54), tab)
    pygame.draw.polygon(s, (255, 150, 160), [tab[5], tab[6], (R - 1, R - 1)])
    pygame.draw.circle(s, (255, 235, 240), (R - 6, R - 7), 3)
  else:                               # rune coin: square hole, rune ring, worn edges
    pygame.draw.circle(s, d, c, R - 8, 2)
    pygame.draw.circle(s, d, c, R - 24, 2)
    rnd = random.Random(4)
    for k in range(12):
      a = k * math.tau / 12
      ca, sa = math.cos(a), math.sin(a)
      px, py = R + ca * (R - 16), R + sa * (R - 16)
      g = rnd.choice(((0, -5, 0, 5, 3, -1), (-3, -5, 3, 5, -3, 5), (0, -5, 0, 5, -3, -2), (-3, -5, 0, 0, 3, -5)))
      pygame.draw.line(s, (250, 220, 150), (px + g[0], py + g[1]), (px + g[2], py + g[3]), 2)
      pygame.draw.line(s, (250, 220, 150), (px + g[2] * 0.3, py), (px + g[4], py + g[5]), 2)
    pygame.draw.rect(s, d, (R - 10, R - 10, 20, 20))
    pygame.draw.rect(s, (0, 0, 0, 0), (R - 7, R - 7, 14, 14))
    pygame.draw.line(s, l, (R - 10, R + 10), (R + 10, R + 10), 2)
    pygame.draw.line(s, l, (R + 10, R - 10), (R + 10, R + 10), 2)
    for k in range(7):                                          # nicks and wear
      a = rnd.random() * math.tau
      pygame.draw.circle(s, (0, 0, 0, 0), (int(R + math.cos(a) * R), int(R + math.sin(a) * R)), rnd.randint(2, 4))
  # shine arc
  pygame.draw.arc(s, GOLD_W, (8, 8, S - 16, S - 16), math.radians(100), math.radians(160), 3)
  return s

def coin_frames(style=0, size=24, n=10):
  k = ('coin', style, size)
  if k not in _C:
    face = _coin_face(style)
    S = face.get_width()
    out = []
    for i in range(n):
      a = i * math.tau / n
      w = max(4, int(abs(math.cos(a)) * S))
      fr = pygame.Surface((S + 12, S), pygame.SRCALPHA)
      edge = max(2, int(abs(math.sin(a)) * 9))
      thin = pygame.transform.scale(face, (w, S))
      dark = pygame.Surface((w, S), pygame.SRCALPHA)
      pygame.draw.ellipse(dark, GOLD_D, (0, 0, w, S))
      x0 = (S + 12 - w - edge) // 2
      for e in range(edge):
        fr.blit(dark, (x0 + e + 1, 0))
      fr.blit(thin if math.cos(a) >= 0 else pygame.transform.flip(thin, True, False), (x0, 0))
      out.append(_down(fr, size + 2, size))
    _C[k] = out
  return _C[k]

# ------------------------------------------------------------------ power-ups
def _star(s, x, y, r, col):
  pygame.draw.polygon(s, col, [(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])

def _glow(s, cx, cy, r, col, a=90):
  for k in range(10, 0, -1):
    t = k / 10
    pygame.draw.circle(s, col + (int(a * (1 - t) ** 1.5 + 6),), (int(cx), int(cy)), int(r * t))

def _power_big(style, ph):
  S = 160
  s = pygame.Surface((S, S), pygame.SRCALPHA)
  c = S // 2
  pulse = 0.5 + 0.5 * math.sin(ph)
  if style == 0:                       # fire crystal on a gold clasp
    _glow(s, c, c - 4, 74 + pulse * 6, (255, 120, 20), 120)
    top, mid, bot = (c, 14), c - 4, (c, 138)
    L, Rr = c - 30, c + 30
    facets = [
      ([top, (L, mid - 20), (c - 8, mid)], (255, 210, 120)),
      ([top, (c - 8, mid), (c + 6, mid - 4)], (255, 240, 190)),
      ([top, (c + 6, mid - 4), (Rr, mid - 20)], (255, 150, 40)),
      ([(L, mid - 20), (c - 8, mid), (c - 6, 112)], (250, 120, 20)),
      ([(c - 8, mid), (c + 6, mid - 4), (c + 4, 116), (c - 6, 112)], (255, 170, 50)),
      ([(c + 6, mid - 4), (Rr, mid - 20), (c + 4, 116)], (210, 60, 10)),
      ([(L, mid - 20), (c - 6, 112), bot], (220, 80, 14)),
      ([(c - 6, 112), (c + 4, 116), bot], (190, 50, 8)),
      ([(c + 4, 116), (Rr, mid - 20), bot], (150, 30, 6)),
    ]
    for pts, col in facets:
      pygame.draw.polygon(s, col, pts)
    pygame.draw.lines(s, (120, 20, 0), True, [top, (Rr, mid - 20), bot, (L, mid - 20)], 2)
    # inner flame
    fl = int(pulse * 6)
    pygame.draw.polygon(s, (255, 250, 210), [(c - 2, 58 - fl), (c + 9, 84), (c, 96), (c - 9, 84)])
    for k in range(3):                   # orbiting shards
      a = ph + k * math.tau / 3
      x, y = c + math.cos(a) * 58, c - 6 + math.sin(a) * 18
      pygame.draw.polygon(s, (255, 190, 80), [(x, y - 8), (x + 4, y), (x, y + 8), (x - 4, y)])
    _star(s, c - 14, 34, 7 + pulse * 3, (255, 255, 230))
  elif style == 1:                     # dragon-heart gem with a turning rune ring
    _glow(s, c, c, 76, (255, 40, 60), 110)
    ring = c - 8
    pygame.draw.circle(s, GOLD_D, (c, c), 64, 7)
    pygame.draw.circle(s, GOLD_M, (c, c), 63, 4)
    pygame.draw.circle(s, GOLD_L, (c, c), 66, 1)
    for k in range(10):
      a = ph * 0.5 + k * math.tau / 10
      x, y = c + math.cos(a) * 63, c + math.sin(a) * 63
      pygame.draw.circle(s, GOLD_D, (int(x), int(y)), 7)
      pygame.draw.circle(s, (255, 230, 150), (int(x), int(y)), 5)
      pygame.draw.line(s, (150, 60, 10), (x - 2, y - 3), (x + 2, y + 3), 2)
    # heart gem
    hp = []
    for k in range(40):
      t = k / 40 * math.tau
      x = 16 * math.sin(t) ** 3
      y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
      hp.append((c + x * 2.7, c + 4 + y * 2.7))
    pygame.draw.polygon(s, (100, 0, 16), hp)
    inner = [(c + (x - c) * 0.55, c + 4 + (y - c - 4) * 0.55 - 4) for x, y in hp]
    cols = [(255, 80, 100), (230, 30, 56), (180, 10, 36), (140, 0, 24)]
    for k in range(40):
      t = (math.cos(k / 40 * math.tau + 2.3) + 1) / 2
      col = _mix(cols[3], cols[0], t)
      pygame.draw.polygon(s, col, [hp[k], hp[(k + 1) % 40], inner[(k + 1) % 40], inner[k]])
    pygame.draw.polygon(s, (230 + int(pulse * 25), 40, 70), inner)
    pygame.draw.polygon(s, (255, 170, 180), [inner[30], inner[33], (c - 4, c)])
    # dragon eye slit inside the heart
    pygame.draw.ellipse(s, (255, 200, 60), (c - 9, c - 8, 18, 22))
    pygame.draw.ellipse(s, (30, 0, 0), (c - 2 - int(pulse), c - 6, 4 + int(pulse) * 2, 18))
    _star(s, c - 22, c - 22, 6 + pulse * 3, (255, 255, 240))
  else:                                # phoenix feather orb in a gold cage
    _glow(s, c, c + 4, 74, (255, 160, 40), 100)
    _disc(s, c, c + 6, 54, (255, 236, 200), (190, 80, 30))
    pygame.draw.circle(s, (120, 40, 10), (c, c + 6), 54, 2)
    # feather
    sw = math.sin(ph) * 4
    fx, fy = c + sw, c + 6
    vane = [(fx, fy - 40), (fx + 14, fy - 20), (fx + 16, fy + 4), (fx + 8, fy + 26), (fx, fy + 34), (fx - 8, fy + 26), (fx - 16, fy + 4), (fx - 14, fy - 20)]
    pygame.draw.polygon(s, (220, 50, 10), vane)
    pygame.draw.polygon(s, (255, 140, 20), [(fx, fy - 34), (fx + 10, fy - 16), (fx + 10, fy + 6), (fx, fy + 22), (fx - 10, fy + 6), (fx - 10, fy - 16)])
    pygame.draw.polygon(s, (255, 230, 90), [(fx, fy - 24), (fx + 5, fy - 10), (fx, fy + 6), (fx - 5, fy - 10)])
    for k in range(6):
      yy = fy - 26 + k * 9
      pygame.draw.line(s, (170, 30, 0), (fx, yy), (fx + 13, yy - 6), 1)
      pygame.draw.line(s, (170, 30, 0), (fx, yy), (fx - 13, yy - 6), 1)
    pygame.draw.line(s, (255, 240, 200), (fx, fy - 40), (fx, fy + 44), 2)
    # glass shine
    pygame.draw.arc(s, (255, 255, 255), (c - 44, c - 40, 88, 92), math.radians(110), math.radians(165), 4)
    pygame.draw.circle(s, (255, 255, 255), (c - 30, c - 20), 4)
    # gold cage
    for wx in (30, 54):
      pygame.draw.ellipse(s, GOLD_D, (c - wx // 2 - 1, c - 48, wx + 2, 110), 4)
      pygame.draw.ellipse(s, GOLD_L, (c - wx // 2, c - 48, wx, 110), 2)
    pygame.draw.ellipse(s, GOLD_D, (c - 56, c - 2, 112, 20), 4)
    pygame.draw.ellipse(s, GOLD_L, (c - 55, c - 1, 110, 18), 2)
    pygame.draw.rect(s, GOLD_D, (c - 14, 14, 28, 12))
    pygame.draw.rect(s, GOLD_M, (c - 12, 15, 24, 9))
    pygame.draw.circle(s, GOLD_L, (c, 10), 7, 3)
    pygame.draw.polygon(s, GOLD_D, [(c - 22, 136), (c + 22, 136), (c + 14, 148), (c - 14, 148)])
    pygame.draw.polygon(s, GOLD_M, [(c - 18, 137), (c + 18, 137), (c + 12, 146), (c - 12, 146)])
    for k in range(4):                    # rising sparks
      yy = 130 - ((ph * 30 + k * 32) % 120)
      pygame.draw.circle(s, (255, 220, 120), (int(c + math.sin(yy * 0.1 + k) * 30), int(yy)), 2)
  return s

def power_frames(style=0, size=40, n=12):
  k = ('pow', style, size)
  if k not in _C:
    _C[k] = [_down(_power_big(style, i * math.tau / n), size, size) for i in range(n)]
  return _C[k]

# ------------------------------------------------------------------ in-game helpers
def coin_img(fr=0, size=24):
  """ruby-set gold coin, spinning frame fr."""
  fs = coin_frames(1, size)
  return fs[fr % len(fs)]

def crystal_img(fr=0, size=40):
  """fire crystal power-up, pulsing frame fr."""
  fs = power_frames(0, size)
  return fs[fr % len(fs)]

def life_heart(full, fr=0, size=40):
  """dragon-heart life icon; empty hearts are greyed and darkened."""
  k = ('life', full, size)
  if k not in _C:
    fs = power_frames(1, size)
    if not full:
      out = []
      for f in fs:
        g = grayscale(f)                              # (works on the phone app's older pygame too)
        g.fill((96, 90, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
        out.append(g)
      fs = out
    _C[k] = fs
  fs = _C[k]
  return fs[fr % len(fs)]

# ------------------------------------------------------------------ treasure-hoard nest
_GEMS = ((228, 28, 52), (40, 116, 255), (36, 196, 96), (176, 60, 232), (255, 200, 40), (240, 240, 255))

def _coin_flat(s, x, y, r, f, tilt=0.5):
  """a coin lying in the pile: rim edge, face, engraved ring and a glint. f = depth light."""
  ry = r * tilt
  pygame.draw.ellipse(s, _sh(GOLD_D, f * 0.75), (x - r, y - ry + 2.5, r * 2, ry * 2))
  pygame.draw.ellipse(s, _sh(GOLD_D, f), (x - r, y - ry + 1.2, r * 2, ry * 2))
  pygame.draw.ellipse(s, _sh(GOLD_M, f), (x - r, y - ry, r * 2, ry * 2))
  pygame.draw.ellipse(s, _sh(GOLD_L, f), (x - r * 0.78, y - ry * 0.85, r * 1.5, ry * 1.5))
  pygame.draw.ellipse(s, _sh(GOLD_D, f * 1.1), (x - r * 0.62, y - ry * 0.62, r * 1.24, ry * 1.24), 1)
  pygame.draw.line(s, _sh(GOLD_W, min(1.0, f + 0.1)), (x - r * 0.5, y - ry * 0.55), (x + r * 0.1, y - ry * 0.75), 1)

def _coin_edge(s, x, y, r, f, ang):
  """a coin standing on its edge / leaning in the pile."""
  w = r * 0.55
  pts = []
  for k in range(16):
    a = k / 16 * math.tau
    px, py = math.cos(a) * w, math.sin(a) * r
    pts.append((x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)))
  pygame.draw.polygon(s, _sh(GOLD_D, f), [(px + 2, py) for px, py in pts])
  pygame.draw.polygon(s, _sh(GOLD_M, f), pts)
  inner = [(x + (px - x) * 0.7, y + (py - y) * 0.7) for px, py in pts]
  pygame.draw.polygon(s, _sh(GOLD_L, f), inner)
  pygame.draw.polygon(s, _sh(GOLD_D, f), inner, 1)

def _gem(s, x, y, r, col, f=1.0):
  pts = [(x, y - r), (x + r, y - r * 0.25), (x + r * 0.62, y + r * 0.8), (x - r * 0.62, y + r * 0.8), (x - r, y - r * 0.25)]
  tab = [(x, y - r * 0.5), (x + r * 0.5, y - r * 0.1), (x + r * 0.3, y + r * 0.35), (x - r * 0.3, y + r * 0.35), (x - r * 0.5, y - r * 0.1)]
  pygame.draw.polygon(s, (20, 10, 10), [(px + 1.5, py + 2) for px, py in pts])
  shades = (1.35, 1.0, 0.62, 0.48, 0.85)
  for k in range(5):
    pygame.draw.polygon(s, _sh(col, shades[k] * f), [pts[k], pts[(k + 1) % 5], tab[(k + 1) % 5], tab[k]])
  pygame.draw.polygon(s, _sh(col, 1.15 * f), tab)
  pygame.draw.polygon(s, (255, 255, 255), [tab[4], tab[0], (x - r * 0.1, y - r * 0.1)])

def _sparkle(s, x, y, r):
  _star(s, x, y, r, (255, 252, 225))
  pygame.draw.circle(s, (255, 255, 255), (int(x), int(y)), max(1, int(r * 0.22)))

def _pearls(s, pts, r):
  for x, y in pts:
    pygame.draw.circle(s, (120, 110, 120), (int(x + 1), int(y + 1.5)), int(r))
    pygame.draw.circle(s, (236, 230, 226), (int(x), int(y)), int(r))
    pygame.draw.circle(s, (255, 255, 255), (int(x - r * 0.35), int(y - r * 0.35)), max(1, int(r * 0.35)))

def _crown(s, x, y, w, f=1.0):
  h = w * 0.55
  base = [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h * 0.35), (x - w / 2, y - h * 0.35)]
  spikes = [(x - w / 2, y - h * 0.3), (x - w / 2, y - h), (x - w / 4, y - h * 0.55), (x, y - h * 1.1), (x + w / 4, y - h * 0.55), (x + w / 2, y - h), (x + w / 2, y - h * 0.3)]
  pygame.draw.polygon(s, _sh(GOLD_D, f), [(px + 2, py + 2) for px, py in spikes])
  pygame.draw.polygon(s, _sh(GOLD_M, f), spikes)
  pygame.draw.polygon(s, _sh(GOLD_L, f), [(x - w / 2 + 3, y - h * 0.32), (x - w / 2 + 3, y - h * 0.85), (x - w / 4, y - h * 0.5)])
  pygame.draw.polygon(s, _sh(GOLD_D, f), base)
  pygame.draw.polygon(s, _sh(GOLD_L, f), [(x - w / 2, y - h * 0.32), (x + w / 2, y - h * 0.32), (x + w / 2, y - h * 0.2), (x - w / 2, y - h * 0.2)])
  for k, gx in enumerate((-w / 3, 0, w / 3)):
    _gem(s, x + gx, y - h * 0.15, w * 0.07, _GEMS[k], f)
  for px, py in (spikes[1], spikes[3], spikes[5]):
    pygame.draw.circle(s, (240, 236, 230), (int(px), int(py)), max(2, int(w * 0.045)))

def _goblet(s, x, y, h, f=1.0):
  w = h * 0.62
  cup = [(x - w / 2, y - h), (x + w / 2, y - h), (x + w * 0.34, y - h * 0.5), (x + w * 0.1, y - h * 0.38), (x - w * 0.1, y - h * 0.38), (x - w * 0.34, y - h * 0.5)]
  pygame.draw.polygon(s, _sh(GOLD_D, f), [(px + 2, py + 2) for px, py in cup])
  pygame.draw.polygon(s, _sh(GOLD_M, f), cup)
  pygame.draw.polygon(s, _sh(GOLD_L, f), [(x - w / 2 + 3, y - h + 2), (x - w * 0.1, y - h + 2), (x - w * 0.12, y - h * 0.45), (x - w * 0.3, y - h * 0.52)])
  pygame.draw.ellipse(s, _sh(GOLD_D, f * 0.8), (x - w / 2, y - h - w * 0.12, w, w * 0.24))
  pygame.draw.ellipse(s, (60, 20, 30), (x - w / 2 + 3, y - h - w * 0.08, w - 6, w * 0.16))
  pygame.draw.rect(s, _sh(GOLD_D, f), (x - w * 0.07, y - h * 0.4, w * 0.14, h * 0.32))
  pygame.draw.circle(s, _sh(GOLD_L, f), (int(x), int(y - h * 0.24)), max(2, int(w * 0.1)))
  pygame.draw.ellipse(s, _sh(GOLD_D, f), (x - w * 0.36, y - h * 0.12, w * 0.72, h * 0.16))
  pygame.draw.ellipse(s, _sh(GOLD_M, f), (x - w * 0.34, y - h * 0.14, w * 0.68, h * 0.12))
  _gem(s, x, y - h * 0.72, w * 0.16, _GEMS[0], f)
  _gem(s, x - w * 0.3, y - h * 0.76, w * 0.08, _GEMS[1], f)
  _gem(s, x + w * 0.3, y - h * 0.76, w * 0.08, _GEMS[2], f)

def _sword(s, x, y, ln, ang, f=1.0):
  ca, sa = math.cos(ang), math.sin(ang)
  def P(a, b):
    return (x + ca * a - sa * b, y + sa * a + ca * b)
  bw = ln * 0.06
  blade = [P(0, -bw), P(ln * 0.8, -bw * 0.8), P(ln, 0), P(ln * 0.8, bw * 0.8), P(0, bw)]
  pygame.draw.polygon(s, _sh((150, 156, 170), f), blade)
  pygame.draw.polygon(s, _sh((230, 236, 245), f), [P(0, -bw), P(ln * 0.8, -bw * 0.8), P(ln, 0), P(0, 0)])
  pygame.draw.line(s, _sh((90, 96, 110), f), P(0, 0), P(ln * 0.9, 0), 1)
  guard = [P(-2, -bw * 4), P(4, -bw * 4), P(4, bw * 4), P(-2, bw * 4)]
  pygame.draw.polygon(s, _sh(GOLD_D, f), guard)
  pygame.draw.polygon(s, _sh(GOLD_L, f), [P(-1, -bw * 3.6), P(3, -bw * 3.6), P(3, 0), P(-1, 0)])
  grip = [P(-ln * 0.22, -bw * 0.9), P(-2, -bw * 0.9), P(-2, bw * 0.9), P(-ln * 0.22, bw * 0.9)]
  pygame.draw.polygon(s, (70, 30, 20), grip)
  for k in range(4):
    a = -ln * 0.04 - k * ln * 0.045
    pygame.draw.line(s, (130, 70, 40), P(a, -bw * 0.9), P(a - ln * 0.02, bw * 0.9), 1)
  pygame.draw.circle(s, _sh(GOLD_M, f), [int(v) for v in P(-ln * 0.25, 0)], max(2, int(bw * 1.6)))
  _gem(s, *P(-ln * 0.25, 0), bw * 1.1, _GEMS[3], f)

NEST_RAISE = 12            # the hoard is taller than the old twig nest: extra rows (x scale) above it

def _hoard(W, H):
  """back and front of a heaped dragon hoard. The egg sits in a hollow on top of the mound."""
  back = pygame.Surface((W, H), pygame.SRCALPHA)
  front = pygame.Surface((W, H), pygame.SRCALPHA)
  rnd = random.Random(23)
  cx = W / 2.0
  R = W / 52.0 * 2.0                     # base coin radius, scales with the nest size
  def U(x):
    return (x - cx) / (W / 2.0)
  def back_top(x):                       # tall mound behind the egg
    u = min(1.0, abs(U(x)))
    return H * (0.97 - 0.80 * (1 - u * u) ** 0.7)
  def front_top(x):                      # front mound with a hollow scooped out for the egg
    u = min(1.0, abs(U(x)))
    m = H * (0.97 - 0.62 * (1 - u * u) ** 0.6)
    return m + H * 0.18 * math.exp(-(U(x) / 0.30) ** 2)
  def gnd(x):
    u = min(1.0, abs(U(x)))
    return H * (0.86 + 0.11 * math.sqrt(1 - u * u))
  ground = H * 0.97

  def pile(surf, top, n, lo, f_top, f_bot, extra):
    pts = [(x, min(top(x) + R * 0.6, gnd(x) - R * 0.3)) for x in range(0, int(W) + 1, 3)]
    pygame.draw.polygon(surf, _sh((150, 96, 16), f_bot), pts + [(x, gnd(x) - R * 0.3) for x in range(int(W), -1, -3)])
    items = []
    for _ in range(n):
      x = rnd.uniform(R * 0.6, W - R * 0.6)
      t0 = top(x)
      if t0 > gnd(x) - R * 0.5:
        continue
      y = rnd.uniform(t0, gnd(x) - R * 0.2)
      items.append((y, x))
    items.sort()
    for y, x in items:
      depth = (y - top(x)) / max(1.0, gnd(x) - top(x))
      f = f_top - (f_top - f_bot) * depth
      r = R * rnd.uniform(0.78, 1.18)
      roll = rnd.random()
      if roll < extra:
        _gem(surf, x, y, r * rnd.uniform(0.7, 1.0), rnd.choice(_GEMS), f)
      elif roll < extra + 0.08:
        _coin_edge(surf, x, y, r, f, rnd.uniform(-0.7, 0.7))
      else:
        _coin_flat(surf, x, y, r, f, rnd.uniform(0.38, 0.56))

  # ---------------- back heap
  _sword(back, W * 0.70, back_top(W * 0.70) + R * 2, W * 0.34, -2.2, 0.9)
  pile(back, back_top, int(W * H / (R * R) * 0.45), 0, 0.98, 0.62, 0.05)
  _crown(back, W * 0.27, back_top(W * 0.27) + R * 1.6, W * 0.18, 0.96)
  for _ in range(6):
    x = rnd.uniform(W * 0.12, W * 0.88)
    _sparkle(back, x, back_top(x) + rnd.uniform(0, R * 3), R * rnd.uniform(0.5, 0.9))
  dip = pygame.Surface((W, H), pygame.SRCALPHA)           # warm shadow in the hollow
  for k in range(8, 0, -1):
    t = k / 8.0
    hy = front_top(cx)
    pygame.draw.ellipse(dip, (50, 24, 2, int(120 * (1 - t) + 40)), (cx - W * 0.22 * t, hy - H * 0.10 * t - H * 0.04, W * 0.44 * t, H * 0.16 * t))
  back.blit(dip, (0, 0))

  # ---------------- front heap
  pile(front, front_top, int(W * H / (R * R) * 0.55), 0, 1.12, 0.58, 0.06)
  for k in range(int(W / R * 0.9)):                       # loose coins spilled on the ground
    x = rnd.uniform(0, W)
    if abs(U(x)) < 0.6:
      continue
    _coin_flat(front, x, gnd(x) - rnd.uniform(-R * 0.3, R * 1.2), R * rnd.uniform(0.8, 1.1), 0.8, 0.42)
  pts = []                                                 # pearl necklace draped over the lip
  for k in range(28):
    t = k / 27.0
    x = W * 0.14 + t * W * 0.46
    pts.append((x, front_top(x) + R * 1.4 + math.sin(t * math.pi) * H * 0.10))
  _pearls(front, pts, R * 0.42)
  _gem(front, pts[14][0], pts[14][1] + R * 0.9, R * 1.0, _GEMS[1])
  for k in range(15):                                      # gold chain on the other side
    t = k / 14.0
    x = W * 0.56 + t * W * 0.30
    y = front_top(x) + R * 1.2 + math.sin(t * math.pi) * H * 0.08
    pygame.draw.ellipse(front, GOLD_D, (x - R * 0.55, y - R * 0.35, R * 1.1, R * 0.7), 2)
    pygame.draw.ellipse(front, GOLD_L, (x - R * 0.45, y - R * 0.36, R * 0.9, R * 0.56), 1)
  _goblet(front, W * 0.84, front_top(W * 0.84) + H * 0.12, H * 0.26)
  for gx, gc in ((0.16, 0), (0.33, 2), (0.66, 3), (0.42, 4)):        # big hero gems on the lip
    _gem(front, W * gx, front_top(W * gx) + R * 0.7, R * 1.35, _GEMS[gc])
  for x in (W * 0.25, W * 0.38, W * 0.60, W * 0.72):
    _coin_flat(front, x, front_top(x) + R * 0.3, R * 1.25, 1.14, 0.5)
  for _ in range(7):
    x = rnd.uniform(W * 0.1, W * 0.9)
    _sparkle(front, x, front_top(x) + rnd.uniform(R, H * 0.25), R * rnd.uniform(0.45, 0.8))
  return back, front

def nest_sprites(scale=3):
  """(back, front) of the treasure-hoard nest: blit back, then the egg/baby, then front.
  The sprites are NEST_RAISE*scale px taller than the old nest, so blit them that much higher."""
  k = ('nest', scale)
  if k not in _C:
    W, H = 52 * scale, (22 + NEST_RAISE) * scale
    b, f = _hoard(W * 2, H * 2)
    _C[k] = (_down(b, W, H), _down(f, W, H))
  return _C[k]
