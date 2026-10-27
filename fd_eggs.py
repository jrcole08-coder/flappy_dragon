"""Dragon egg art: scaly, egg-shaped shells painted large and smooth-scaled down. The nest lives in fd_items."""
import math
import random
import pygame

# rarity -> (name, shell ramp dark..light, pattern colour, glow colour)
EGG_STYLE = {
  'common': ("Common", ((46, 70, 30), (78, 112, 46), (120, 156, 70), (170, 200, 112), (220, 236, 170)), (96, 66, 34), (60, 90, 30)),
  'uncommon': ("Uncommon", ((24, 54, 104), (40, 92, 160), (70, 140, 210), (130, 190, 240), (210, 240, 255)), (235, 248, 255), (30, 70, 130)),
  'rare': ("Rare", ((48, 18, 80), (84, 34, 130), (128, 64, 186), (176, 118, 226), (226, 196, 255)), (255, 150, 255), (90, 30, 130)),
  'epic': ("Epic", ((110, 50, 8), (170, 90, 14), (220, 146, 30), (250, 200, 70), (255, 244, 170)), (255, 90, 30), (150, 80, 10)),
  'legendary': ("Legendary", ((10, 10, 34), (26, 22, 70), (46, 40, 118), (80, 74, 170), (150, 150, 230)), (255, 255, 255), (90, 60, 160)),
}
RARITY_ORDER = ['common', 'uncommon', 'rare', 'epic', 'legendary']
RARITY_COL = {'common': (150, 210, 110), 'uncommon': (110, 190, 255), 'rare': (210, 140, 255), 'epic': (255, 190, 60), 'legendary': (255, 120, 220)}
_CACHE = {}
EW, EH = 22, 28


HD = 6                      # eggs are painted at 6x then smooth-scaled, so the scales stay sharp


def _egg_half(t):
  """half-width (0..1) of the egg at height t (0 = top, 1 = bottom): pointed top, round bottom."""
  c = 0.58
  v = (t - c) / c if t < c else (t - c) / (1 - c)
  return math.sqrt(max(0.0, 1 - v * v)) * (0.84 + 0.16 * min(1.0, t / c))


def _egg_outline(w, h, ox=0, oy=0, n=72):
  pts = []
  for k in range(n + 1):
    t = k / float(n)
    pts.append((ox + w / 2.0 + _egg_half(t) * w / 2.0, oy + t * h))
  for k in range(n, -1, -1):
    t = k / float(n)
    pts.append((ox + w / 2.0 - _egg_half(t) * w / 2.0, oy + t * h))
  return pts


def _ramp(ramp, l):
  l = max(0.0, min(0.999, l)) * (len(ramp) - 1)
  i = int(l)
  f = l - i
  a, b = ramp[i], ramp[i + 1]
  return tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3))


def _light(nx, ny):
  nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
  l = -0.42 * nx - 0.52 * ny + 0.74 * nz
  return max(0.0, l) ** 0.9


def egg_hd(rarity, fr):
  """big scaled dragon egg (rarity colours) with a shimmer that moves with fr (0-7)."""
  k = ('egg_hd', rarity, fr)
  s = _CACHE.get(k)
  if s is not None:
    return s
  name, ramp, pat, glow = EGG_STYLE[rarity]
  W, H = EW * HD, EH * HD
  P = HD                                            # outline padding
  egg = pygame.Surface((W + 2 * P, H + 2 * P), pygame.SRCALPHA)
  cx, cy = P + W / 2.0, P + H * 0.58
  rnd = random.Random(RARITY_ORDER.index(rarity) * 31 + 7)
  outline = _egg_outline(W, H, P, P)
  pygame.draw.polygon(egg, ramp[0], outline)
  # --- overlapping dragon scales, row by row from the top (lower rows overlap upper ones)
  rs = W * 0.085
  rows = int(H / (rs * 0.95)) + 2
  for row in range(rows):
    yy = P - rs + row * rs * 0.95
    t = (yy - P) / H
    half = _egg_half(min(1.0, max(0.0, t))) * W / 2.0
    if half < 2:
      continue
    n = max(3, int(math.pi * half / (rs * 1.05)))
    for i in range(n + 1):
      th = -math.pi / 2 + (i + (0.5 if row % 2 else 0.0)) * math.pi / n
      if th > math.pi / 2 + 0.01:
        continue
      sx = cx + math.sin(th) * half
      sw = rs * (0.35 + 0.65 * math.cos(th))           # scales squash toward the sides
      nx, ny = math.sin(th) * (half / (W / 2.0)), (yy - cy) / (H * 0.62)
      l = _light(nx, max(-1.0, min(1.0, ny)))
      base = _ramp(ramp, 0.15 + l * 0.85)
      dark = _ramp(ramp, max(0.0, l * 0.55 - 0.05))
      hi = _ramp(ramp, min(1.0, l * 1.05 + 0.18))
      r = pygame.Rect(0, 0, int(sw * 2.1), int(rs * 2.0))
      r.center = (int(sx), int(yy + rs * 0.55))
      pygame.draw.ellipse(egg, dark, r)                           # scale edge / shadow
      pygame.draw.ellipse(egg, base, r.inflate(-max(2, int(sw * 0.28)), -max(2, int(rs * 0.34))).move(0, -int(rs * 0.08)))
      hr = pygame.Rect(0, 0, max(2, int(sw * 0.9)), max(2, int(rs * 0.6)))
      hr.center = (int(sx - sw * 0.2), int(yy + rs * 0.25))
      pygame.draw.ellipse(egg, hi, hr)                            # glossy highlight
      pygame.draw.line(egg, dark, (sx, yy + rs * 0.2), (sx, yy + rs * 1.2), 1)  # centre ridge
  # --- rarity markings painted over the scales
  def inside(x, y):
    t = (y - P) / H
    return 0 <= t <= 1 and abs(x - cx) <= _egg_half(t) * W / 2.0 - 3
  if rarity == 'common':                               # earthy speckles
    for _ in range(46):
      x, y = rnd.uniform(P, P + W), rnd.uniform(P + H * 0.1, P + H)
      if inside(x, y):
        rr = rnd.uniform(2, 5)
        pygame.draw.ellipse(egg, pat, (x - rr, y - rr * 0.7, rr * 2, rr * 1.4))
  elif rarity == 'uncommon':                           # frosty zig-zag bands
    for by in (0.40, 0.66):
      pts = []
      for k in range(25):
        x = P + k * W / 24.0
        y = P + H * by + (8 if k % 2 else -8)
        pts.append((x, y))
      pts = [p for p in pts if inside(*p)]
      if len(pts) > 1:
        pygame.draw.lines(egg, (30, 70, 130), False, [(x, y + 3) for x, y in pts], 6)
        pygame.draw.lines(egg, pat, False, pts, 5)
  elif rarity == 'rare':                               # glowing runes
    for gx, gy in ((0.32, 0.36), (0.62, 0.30), (0.46, 0.55), (0.28, 0.70), (0.68, 0.66)):
      x, y = P + W * gx, P + H * gy
      if inside(x, y):
        g = rnd.choice(((0, -12, 0, 12, 8, -4), (-8, -12, 8, 12, -8, 12), (0, -12, 0, 12, -8, -6), (-8, -12, 0, 0, 8, -12)))
        for wd, c in ((7, (120, 40, 160)), (3, pat)):
          pygame.draw.line(egg, c, (x + g[0], y + g[1]), (x + g[2], y + g[3]), wd)
          pygame.draw.line(egg, c, (x, y), (x + g[4], y + g[5]), wd)
  elif rarity == 'epic':                               # flame streaks rising from the base
    for k in range(7):
      x0 = P + W * (0.12 + k * 0.126)
      pts = [(x0 + math.sin(j * 0.8 + k) * 6, P + H - j * H * 0.06) for j in range(9 if k % 2 else 6)]
      pts = [p for p in pts if inside(*p)]
      if len(pts) > 1:
        pygame.draw.lines(egg, pat, False, pts, 6)
        pygame.draw.lines(egg, (255, 200, 90), False, pts, 2)
  else:                                                # legendary: starfield + glowing crack
    for _ in range(26):
      x, y = rnd.uniform(P, P + W), rnd.uniform(P, P + H)
      if inside(x, y):
        rr = rnd.choice((1, 1, 2, 3))
        pygame.draw.circle(egg, (255, 255, 255), (int(x), int(y)), rr)
    pts = [(cx + dx * W, P + dy * H) for dx, dy in ((0.0, 0.18), (-0.06, 0.28), (0.05, 0.38), (-0.03, 0.48), (0.07, 0.58), (0.01, 0.68), (0.09, 0.78))]
    pts = [p for p in pts if inside(*p)]
    pygame.draw.lines(egg, (150, 40, 130), False, pts, 7)
    pygame.draw.lines(egg, (255, 170, 240), False, pts, 3)
  # --- soft sheen + moving shimmer band (blended on a separate layer)
  fx = pygame.Surface(egg.get_size(), pygame.SRCALPHA)
  pygame.draw.ellipse(fx, (255, 255, 255, 70), (cx - W * 0.30, P + H * 0.12, W * 0.26, H * 0.30))
  pygame.draw.ellipse(fx, (255, 255, 255, 110), (cx - W * 0.25, P + H * 0.16, W * 0.12, H * 0.14))
  band = (fr / 8.0) * (W + H) * 1.1 - H * 0.4
  pygame.draw.polygon(fx, (255, 255, 255, 55), [(P + band, P), (P + band + W * 0.16, P), (P + band + W * 0.16 - H * 0.6, P + H), (P + band - H * 0.6, P + H)])
  egg.blit(fx, (0, 0))
  # --- cut to the egg shape, then a dark outline and shaded rim
  mask = pygame.Surface(egg.get_size(), pygame.SRCALPHA)
  pygame.draw.polygon(mask, (255, 255, 255, 255), outline)
  egg.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
  pygame.draw.polygon(egg, _ramp(ramp, 0.0), outline, max(3, HD // 2 + 1))
  pygame.draw.lines(egg, (14, 10, 18), True, outline, 2)
  _CACHE[k] = egg
  return egg


def egg_base(rarity, fr):
  """kept for old callers: the egg at 1x (with a 1px outline border)."""
  return egg_sprite(rarity, 1, fr)


def egg_sprite(rarity, scale, fr, tilt=0):
  """Scaled egg; tilt (degrees, rounded to 3) wobbles it."""
  tilt = int(round(tilt / 3.0)) * 3
  k = ('egg_s', rarity, scale, fr % 8, tilt)
  s = _CACHE.get(k)
  if s is None:
    b = egg_hd(rarity, fr % 8)
    s = pygame.transform.smoothscale(b, ((EW + 2) * scale, (EH + 2) * scale))
    if tilt:
      s = pygame.transform.rotate(s, tilt)
    if len(_CACHE) > 600:
      for kk in [q for q in _CACHE if q[0] == 'egg_s']:
        del _CACHE[kk]
    _CACHE[k] = s
  return s


from fd_items import nest_sprites   # treasure-hoard nest
