"""Detailed siege engines (catapult, trebuchet, ballista) in three styles each.
Each is painted 4x larger with shading and smooth-scaled down, using the same footprint,
pivot points and poses as before, so the game logic is unchanged."""
import math, random
import pygame

K = 4
def _sh(c, f):
  return tuple(max(0, min(255, int(v * f))) for v in c[:3])

# style palettes: wood, dark wood, metal, metal light, cloth, cloth 2, trim
STYLES = {
  0: dict(name="Oak", wood=(156, 104, 56), metal=(110, 112, 122), trim=(110, 112, 122), cloth=(196, 40, 40), cloth2=(240, 200, 60), rope=(196, 166, 110)),
  1: dict(name="War", wood=(98, 66, 44), metal=(70, 66, 70), trim=(150, 40, 30), cloth=(40, 30, 34), cloth2=(190, 30, 30), rope=(150, 120, 80)),
  2: dict(name="Royal", wood=(178, 124, 72), metal=(208, 160, 50), trim=(36, 70, 150), cloth=(40, 80, 180), cloth2=(240, 200, 70), rope=(210, 180, 120)),
}

def _harden(img):
  """make edge pixels fully opaque or fully clear (the game turns these sprites into colorkey
  sprites, and half-transparent edges would pick up the pink key colour)."""
  try:
    solid = img.copy()
    solid.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
    m = pygame.mask.from_surface(img, 110)
    return m.to_surface(setsurface=solid, unsetcolor=(0, 0, 0, 0))
  except Exception:
    return img

class _P:
  """painter: native game coords -> big canvas coords."""
  def __init__(self, bx0, by0, bw, bh):
    self.bx0, self.by0, self.bw, self.bh = bx0, by0, bw, bh
    self.s = pygame.Surface((bw * K, bh * K), pygame.SRCALPHA)
  def T(self, p):
    return ((p[0] - self.bx0) * K, (p[1] - self.by0) * K)
  def poly(self, col, pts, w=0):
    pygame.draw.polygon(self.s, col, [self.T(p) for p in pts], w)
  def line(self, col, a, b, w=1):
    pygame.draw.line(self.s, col, self.T(a), self.T(b), max(1, int(w * K)))
  def lines(self, col, pts, w=1, closed=False):
    pygame.draw.lines(self.s, col, closed, [self.T(p) for p in pts], max(1, int(w * K)))
  def circle(self, col, c, r, w=0):
    pygame.draw.circle(self.s, col, [int(v) for v in self.T(c)], max(1, int(r * K)), int(w * K) if w else 0)
  def ellipse(self, col, rect, w=0):
    x, y, ww, hh = rect
    X, Y = self.T((x, y))
    pygame.draw.ellipse(self.s, col, (X, Y, ww * K, hh * K), int(w * K) if w else 0)
  def out(self, surface, x, y):
    img = pygame.transform.smoothscale(self.s, (self.bw, self.bh))
    img = _harden(img)
    surface.blit(img, (x + self.bx0, y + self.by0))


  # ---- building blocks
  def beam(self, a, b, w, col, grain=True, bands=(), band_col=None, rivet=None):
    """a thick shaded timber from a to b (w = thickness)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2.0, dx / L * w / 2.0
    if ny > 0:                                # make n point "up" for the highlight
      nx, ny = -nx, -ny
    pts = [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]
    self.poly(_sh(col, 0.55), [(p[0] + 0.6, p[1] + 0.9) for p in pts])          # drop shadow
    self.poly(col, pts)
    self.poly(_sh(col, 0.78), [((a[0] + b[0]) * 0 + a[0], a[1]), b, (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
    self.line(_sh(col, 1.28), pts[0], pts[1], 0.5)
    self.line(_sh(col, 0.45), pts[3], pts[2], 0.5)
    if grain and L > 6:
      rnd = random.Random(int(a[0] * 7 + a[1] * 13 + b[0]))
      for k in range(int(L / 7) + 1):
        t0 = rnd.uniform(0.05, 0.7); t1 = min(0.97, t0 + rnd.uniform(0.15, 0.35))
        o = rnd.uniform(-0.3, 0.3)
        p0 = (a[0] + dx * t0 + nx * o * 2, a[1] + dy * t0 + ny * o * 2)
        p1 = (a[0] + dx * t1 + nx * o * 2, a[1] + dy * t1 + ny * o * 2)
        self.line(_sh(col, 0.66), p0, p1, 0.25)
    bc = band_col or (96, 98, 108)
    for t in bands:
      c = (a[0] + dx * t, a[1] + dy * t)
      ux, uy = dx / L * 1.1, dy / L * 1.1
      q = [(c[0] - ux + nx * 1.15, c[1] - uy + ny * 1.15), (c[0] + ux + nx * 1.15, c[1] + uy + ny * 1.15), (c[0] + ux - nx * 1.15, c[1] + uy - ny * 1.15), (c[0] - ux - nx * 1.15, c[1] - uy - ny * 1.15)]
      self.poly(_sh(bc, 0.6), q)
      self.poly(bc, [q[0], q[1], ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2), ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)])
      self.line(_sh(bc, 1.4), q[0], q[1], 0.25)
      if rivet:
        self.circle(rivet, (c[0] + nx * 0.5, c[1] + ny * 0.5), 0.35)
  def plank_box(self, x0, y0, x1, y1, col, n=4, band_col=None, rivets=None):
    """a plank-built box (chassis, crates)."""
    self.poly(_sh(col, 0.5), [(x0 + 0.8, y0 + 1), (x1 + 0.8, y0 + 1), (x1 + 0.8, y1 + 1), (x0 + 0.8, y1 + 1)])
    h = (y1 - y0) / float(n)
    for k in range(n):
      f = 1.08 - 0.1 * k
      self.poly(_sh(col, f), [(x0, y0 + k * h), (x1, y0 + k * h), (x1, y0 + (k + 1) * h), (x0, y0 + (k + 1) * h)])
      self.line(_sh(col, 1.25 * f), (x0, y0 + k * h + 0.2), (x1, y0 + k * h + 0.2), 0.25)
      self.line(_sh(col, 0.5), (x0, y0 + (k + 1) * h), (x1, y0 + (k + 1) * h), 0.3)
    rnd = random.Random(int(x0 * 3 + y0))
    for k in range(int((x1 - x0) / 5)):
      yy = rnd.uniform(y0, y1)
      xx = rnd.uniform(x0, x1 - 4)
      self.line(_sh(col, 0.7), (xx, yy), (xx + rnd.uniform(2, 5), yy), 0.25)
    if band_col:
      for bx in (x0 + 1.5, x1 - 3):
        self.poly(_sh(band_col, 0.7), [(bx, y0 - 0.3), (bx + 1.6, y0 - 0.3), (bx + 1.6, y1 + 0.3), (bx, y1 + 0.3)])
        self.line(_sh(band_col, 1.3), (bx, y0), (bx, y1), 0.35)
        for yy in (y0 + 1.2, y1 - 1.2):
          self.circle(rivets or _sh(band_col, 1.4), (bx + 0.8, yy), 0.45)
  def wheel(self, c, r, wood, metal, spokes=8, spiked=False, hub=None):
    cx, cy = c
    if spiked:
      for k in range(10):
        a = k * math.tau / 10 + 0.2
        self.poly(_sh(metal, 1.1), [(cx + math.cos(a - 0.12) * r, cy + math.sin(a - 0.12) * r), (cx + math.cos(a) * (r + 3), cy + math.sin(a) * (r + 3)), (cx + math.cos(a + 0.12) * r, cy + math.sin(a + 0.12) * r)])
    self.circle(_sh(metal, 0.45), (cx + 0.6, cy + 0.8), r)
    self.circle(_sh(metal, 0.85), c, r)                       # iron tyre
    self.circle(_sh(wood, 0.55), c, r - 1.4)
    self.circle(_sh(wood, 0.95), c, r - 2.0, 0)
    self.circle(_sh(wood, 0.55), c, r - 3.6)                  # hollow between spokes
    for k in range(spokes):
      a = k * math.tau / spokes
      self.line(_sh(wood, 0.5), (cx + 0.3, cy + 0.4), (cx + math.cos(a) * (r - 2.2) + 0.3, cy + math.sin(a) * (r - 2.2) + 0.4), 1.4)
      self.line(_sh(wood, 1.05), c, (cx + math.cos(a) * (r - 2.2), cy + math.sin(a) * (r - 2.2)), 1.1)
    for k in range(8):                                        # tyre rivets
      a = k * math.tau / 8 + 0.4
      self.circle(_sh(metal, 1.45), (cx + math.cos(a) * (r - 0.7), cy + math.sin(a) * (r - 0.7)), 0.35)
    pygame.draw.arc(self.s, _sh(metal, 1.5), (self.T((cx - r, cy - r))[0], self.T((cx - r, cy - r))[1], 2 * r * K, 2 * r * K), math.radians(100), math.radians(170), max(1, K // 2))
    self.circle(_sh(hub or metal, 0.6), c, r * 0.3)
    self.circle(hub or metal, c, r * 0.24)
    self.circle(_sh(hub or metal, 1.5), (cx - r * 0.07, cy - r * 0.08), r * 0.09)
  def boulder(self, c, r, fire=False):
    cx, cy = c
    if fire:
      for k in range(6):
        a = -math.pi / 2 + (k - 2.5) * 0.35
        self.poly((255, 120 + k * 12, 20), [(cx + math.cos(a - 0.4) * r, cy + math.sin(a - 0.4) * r), (cx + math.cos(a) * r * 2.1, cy + math.sin(a) * r * 2.1), (cx + math.cos(a + 0.4) * r, cy + math.sin(a + 0.4) * r)])
    n = 14
    rnd = random.Random(int(r * 10))
    pts = [(cx + math.cos(k * math.tau / n) * r * rnd.uniform(0.86, 1.05), cy + math.sin(k * math.tau / n) * r * rnd.uniform(0.86, 1.05)) for k in range(n)]
    self.poly((52, 48, 50), [(p[0] + 0.5, p[1] + 0.6) for p in pts])
    self.poly((112, 106, 104), pts)
    self.poly((150, 144, 140), [(cx + (p[0] - cx) * 0.7 - r * 0.18, cy + (p[1] - cy) * 0.7 - r * 0.2) for p in pts])
    self.poly((190, 184, 178), [(cx + (p[0] - cx) * 0.3 - r * 0.35, cy + (p[1] - cy) * 0.3 - r * 0.38) for p in pts])
    self.line((70, 64, 66), (cx - r * 0.1, cy - r * 0.2), (cx + r * 0.4, cy + r * 0.3), 0.3)
    self.line((70, 64, 66), (cx + r * 0.4, cy + r * 0.3), (cx + r * 0.2, cy + r * 0.7), 0.3)
  def rope_coil(self, c, rx, ry, col):
    cx, cy = c
    self.ellipse(_sh(col, 0.5), (cx - rx + 0.4, cy - ry + 0.5, rx * 2, ry * 2))
    self.ellipse(col, (cx - rx, cy - ry, rx * 2, ry * 2))
    for k in range(7):
      t = -1 + k / 3.0
      x = cx + t * rx * 0.85
      hh = ry * math.sqrt(max(0.0, 1 - (t * 0.85) ** 2))
      self.line(_sh(col, 0.6), (x - 0.5, cy - hh), (x + 0.5, cy + hh), 0.3)
    self.line(_sh(col, 1.3), (cx - rx * 0.6, cy - ry * 0.8), (cx + rx * 0.4, cy - ry * 0.9), 0.3)
  def flag(self, base, h, col, col2, wave=0.0, tattered=False, crest=None):
    bx, by = base
    self.line((70, 50, 30), (bx, by), (bx, by - h), 0.9)
    self.circle((220, 190, 90), (bx, by - h), 0.7)
    top = by - h + 1
    pts = []
    for k in range(7):
      t = k / 6.0
      pts.append((bx + t * 13, top + math.sin(t * 3 + wave) * 1.2))
    bot = [(x, y + 6 - (t * 1.5)) for (x, y), t in zip(pts, [k / 6.0 for k in range(7)])]
    if tattered:
      bot = [(x, y + (1.8 if k % 2 else 0)) for k, (x, y) in enumerate(bot)]
      tip = [(pts[-1][0] - 2, pts[-1][1] + 1.5), (pts[-1][0] + 1, pts[-1][1] + 3), (pts[-1][0] - 2, pts[-1][1] + 4.5)]
    else:
      tip = [(pts[-1][0] + 2, (pts[-1][1] + bot[-1][1]) / 2)]
    shape = pts + tip + bot[::-1]
    self.poly(_sh(col, 0.6), [(x + 0.4, y + 0.5) for x, y in shape])
    self.poly(col, shape)
    self.lines(_sh(col, 1.35), pts[:4], 0.3)
    self.line(col2, (bx + 1, top + 1.2), (bx + 10, top + 1.2 + math.sin(2 + wave)), 0.4)
    if crest:
      self.circle(crest, (bx + 5.5, top + 3.2), 1.3)

# ------------------------------------------------------------------ catapult
SIEGE_STYLE = 1          # 0 Oak, 1 War, 2 Royal (War chosen)
_LAYERS = {}


def _native(p):
  """the painter's canvas smooth-scaled to game size (not yet hardened)."""
  return pygame.transform.smoothscale(p.s, (p.bw, p.bh))


def _rot_about(img, deg, piv):
  """rotate img (smoothly) by deg (pygame: counter-clockwise) about pixel piv; returns (surf, top-left offset)."""
  r = pygame.transform.rotozoom(img, deg, 1.0)
  w, h = img.get_size()
  vx, vy = piv[0] - w / 2.0, piv[1] - h / 2.0
  a = math.radians(deg)
  nx = vx * math.cos(a) + vy * math.sin(a)
  ny = -vx * math.sin(a) + vy * math.cos(a)
  cx, cy = r.get_width() / 2.0 + nx, r.get_height() / 2.0 + ny
  return r, (piv[0] - cx, piv[1] - cy)


def _finish(surface):
  """harden the finished sprite in place (it becomes a colorkey sprite in the game)."""
  try:
    hard = _harden(surface)
    if hard is surface:
      return
    surface.fill((0, 0, 0, 0))
    surface.blit(hard, (0, 0))
  except Exception:
    pass


def _boulder_img(r, fire):
  k = ('boulder', r, fire)
  if k not in _LAYERS:
    p = _P(-12, -16, 24, 28)
    p.boulder((0, 0), r, fire=fire)
    _LAYERS[k] = _native(p)
  return _LAYERS[k]


def _cat_layers(style):
  """built once: back (frame), arm (pointing right, angle 0) and front (hub, wheels, extras)."""
  k = ('cat', style)
  if k in _LAYERS:
    return _LAYERS[k]
  st = STYLES[style]
  W, M, R = st['wood'], st['metal'], st['rope']
  px, py = 30, 20
  b = _P(-26, -34, 112, 92)
  b.plank_box(-2, 22, 62, 32, W, 3, band_col=M if style != 1 else (60, 56, 60))
  b.beam((-4, 27), (66, 27), 2.0, _sh(W, 0.9))
  b.beam((19, 23), (30, 15), 4.0, W, bands=(0.75,), band_col=M)
  b.beam((43, 23), (31, 15), 4.0, _sh(W, 0.92), bands=(0.75,), band_col=M)
  b.beam((22, 19), (40, 19), 2.0, _sh(W, 0.85))
  b.beam((6, 23), (12, 2), 3.0, _sh(W, 0.9))
  b.beam((2, 3), (16, 0), 3.2, _sh(W, 1.05), bands=(0.5,), band_col=M)
  b.rope_coil((9, 1.5), 3.2, 2.2, (120, 50, 40) if style == 1 else R)
  b.wheel((52, 18), 4.2, W, M, 6)
  b.rope_coil((px, py), 5.0, 4.2, R)
  # arm at angle 0 (pointing right) on the same canvas, so it can be rotated about the pivot
  a = _P(-26, -34, 112, 92)
  ex, ey = px + 38, py
  a.beam((px, py), (ex, ey), 3.2, _sh(W, 1.08), bands=(0.35, 0.7), band_col=M, rivet=_sh(M, 1.5))
  ux, uy, nx, ny = 1.0, 0.0, 0.0, -1.0
  cx_, cy_ = ex + nx * 3.2, ey + ny * 3.2
  bowl = []
  for kk in range(13):
    t = math.pi * kk / 12
    bowl.append((cx_ + ux * math.cos(t) * 5.4 - nx * math.sin(t) * 5.4, cy_ + uy * math.cos(t) * 5.4 - ny * math.sin(t) * 5.4))
  a.poly(_sh(M, 0.5), [(q[0] + 0.5, q[1] + 0.6) for q in bowl])
  a.poly(_sh(W, 0.8), bowl)
  inner = [(cx_ + (q[0] - cx_) * 0.72, cy_ + (q[1] - cy_) * 0.72) for q in bowl]
  a.poly(_sh(W, 0.45), inner)
  a.lines(M, bowl, 0.7)
  a.line(_sh(M, 1.4), bowl[0], bowl[-1], 0.5)
  f = _P(-26, -34, 112, 92)
  f.circle(_sh(M, 0.6), (px, py), 2.6)
  f.circle(M, (px, py), 2.0)
  f.circle(_sh(M, 1.6), (px - 0.6, py - 0.6), 0.7)
  for wx in (13, 47):
    f.wheel((wx, 36), 11.5, W, M, 8, spiked=(style == 1), hub=(st['metal'] if style == 2 else None))
  if style == 0:
    f.flag((58, 16), 20, st['cloth'], st['cloth2'], 0.5)
    for kk in range(3):
      f.boulder((60 + kk * 0.3 - 4 + kk * 3.2, 19.5 - (kk % 2) * 1.2), 2.0)
  elif style == 1:
    f.flag((58, 16), 22, st['cloth'], st['cloth2'], 1.2, tattered=True, crest=(220, 210, 190))
    for kk in range(4):
      f.poly((180, 176, 170), [(-2, 23 + kk * 2.6), (-8, 24.2 + kk * 2.6), (-2, 25.4 + kk * 2.6)])
    f.circle((50, 44, 40), (5.2, 18.6), 3.2)
    f.circle((226, 218, 196), (5, 18), 3.0)
    f.poly((226, 218, 196), [(3.4, 20), (6.6, 20), (6.2, 22.2), (3.8, 22.2)])
    f.circle((30, 20, 20), (4.0, 17.8), 0.8); f.circle((30, 20, 20), (6.1, 17.8), 0.8)
  else:
    f.flag((58, 16), 22, st['cloth'], st['cloth2'], 0.4, crest=st['cloth2'])
    sh = [(-1, 13), (8, 13), (8, 20), (3.5, 24), (-1, 20)]
    f.poly(_sh(st['metal'], 0.6), [(a_ + 0.4, b_ + 0.5) for a_, b_ in sh])
    f.poly(st['metal'], sh)
    f.poly(st['trim'], [(0, 14), (7, 14), (7, 19.6), (3.5, 22.8), (0, 19.6)])
    f.poly(st['cloth2'], [(3.5, 15), (5.2, 17.6), (3.5, 21), (1.8, 17.6)])
    f.line(st['metal'], (-2, 22), (62, 22), 0.6)
    f.line(st['metal'], (-2, 32), (62, 32), 0.6)
  L = _LAYERS[k] = {'back': _native(b), 'arm': _native(a), 'front': _native(f), 'org': (-26, -34), 'piv': (px + 26, py + 34)}
  return L


def draw_catapult(surface, x, y, ang=225.0, loaded=True, style=None):
  """cheap per pose: the detailed layers are painted once and the arm is just rotated."""
  style = SIEGE_STYLE if style is None else style
  st = STYLES[style]
  L = _cat_layers(style)
  ox, oy = x + L['org'][0], y + L['org'][1]
  px, py = 30, 20
  a = math.radians(ang)
  ex, ey = px + math.cos(a) * 38, py + math.sin(a) * 38
  surface.blit(L['back'], (ox, oy))
  if math.cos(a) > 0.2:                               # winch rope pulls the arm down
    pygame.draw.line(surface, _sh(st['rope'], 0.7), (x + 52, y + 18), (x + ex, y + ey), 2)
  arm, off = _rot_about(L['arm'], -ang, L['piv'])
  surface.blit(arm, (ox + off[0], oy + off[1]))
  if loaded:                                          # stone sits in the bucket (flames stay upright)
    bx, by = 38.0, -2.6
    wx = px + bx * math.cos(a) - by * math.sin(a)
    wy = py + bx * math.sin(a) + by * math.cos(a)
    bimg = _boulder_img(4.2, style == 1)
    surface.blit(bimg, (x + wx - 12, y + wy - 16))
  surface.blit(L['front'], (ox, oy))
  _finish(surface)

# ------------------------------------------------------------------ trebuchet
def _treb_layers(style):
  k = ('treb', style)
  if k in _LAYERS:
    return _LAYERS[k]
  st = STYLES[style]
  W, M, R = st['wood'], st['metal'], st['rope']
  px, py = 35, 5
  b = _P(-40, -50, 150, 112)
  b.plank_box(-2, 42, 72, 52, W, 3, band_col=M)
  b.beam((-4, 47), (76, 47), 2.0, _sh(W, 0.88))
  for lx0, f_ in ((6, 0.86), (64, 0.95)):
    b.beam((lx0, 43), (px, py + 1), 4.2, _sh(W, f_), bands=(0.25, 0.8), band_col=M, rivet=_sh(M, 1.5))
  b.beam((16, 30), (54, 30), 2.6, _sh(W, 0.92), bands=(0.5,), band_col=M)
  b.beam((24, 18), (46, 18), 2.2, _sh(W, 0.88))
  b.beam((16, 30), (35, 43), 2.0, _sh(W, 0.8))
  b.beam((54, 30), (35, 43), 2.0, _sh(W, 0.8))
  b.beam((-14, 41), (6, 41), 2.0, _sh(W, 0.75))
  a = _P(-40, -50, 150, 112)                          # arm at angle 0: long end to the right
  a.beam((px - 22, py), (px + 50, py), 3.6, _sh(W, 1.1), bands=(0.12, 0.32, 0.55, 0.8), band_col=M, rivet=_sh(M, 1.5))
  a.circle(_sh(M, 0.6), (px + 50, py), 1.5)
  a.circle(M, (px + 50, py), 1.1)
  c = _P(-12, -2, 24, 26)                             # counterweight, hangs from (0, 0)
  cwx, cwy = 0, 3
  c.line(_sh(M, 0.8), (-3, 0), (cwx - 5, cwy + 3), 0.6)
  c.line(_sh(M, 0.8), (3, 0), (cwx + 5, cwy + 3), 0.6)
  if style == 0:
    c.plank_box(cwx - 8, cwy + 3, cwx + 8, cwy + 17, _sh(W, 0.95), 3, band_col=M)
    for kk in range(4):
      c.boulder((cwx - 5.5 + kk * 3.7, cwy + 3.2 - (kk % 2)), 2.2)
  elif style == 1:
    cage = (cwx - 8, cwy + 3, cwx + 8, cwy + 18)
    for kk in range(7):
      c.boulder((cwx - 5 + (kk % 3) * 5, cwy + 6 + (kk // 3) * 4.5), 2.8)
    for kk in range(5):
      xx = cage[0] + kk * 4
      c.line(_sh(M, 1.1), (xx, cage[1]), (xx, cage[3]), 0.6)
    c.line(_sh(M, 1.2), (cage[0], cage[1]), (cage[2], cage[1]), 0.9)
    c.line(_sh(M, 1.2), (cage[0], cage[3]), (cage[2], cage[3]), 0.9)
    for kk in range(3):
      c.poly((190, 186, 180), [(cage[0] + 3 + kk * 5, cage[3]), (cage[0] + 4.2 + kk * 5, cage[3] + 3.4), (cage[0] + 5.4 + kk * 5, cage[3])])
  else:
    c.poly(_sh((120, 124, 136), 0.5), [(cwx - 7.6, cwy + 3.6), (cwx + 8.6, cwy + 3.6), (cwx + 8.6, cwy + 17.6), (cwx - 7.6, cwy + 17.6)])
    c.poly((128, 132, 146), [(cwx - 8, cwy + 3), (cwx + 8, cwy + 3), (cwx + 8, cwy + 17), (cwx - 8, cwy + 17)])
    c.poly((156, 160, 176), [(cwx - 8, cwy + 3), (cwx + 8, cwy + 3), (cwx + 8, cwy + 6), (cwx - 8, cwy + 6)])
    c.poly(st['trim'], [(cwx - 4, cwy + 7.5), (cwx + 4, cwy + 7.5), (cwx + 4, cwy + 12), (cwx, cwy + 15), (cwx - 4, cwy + 12)])
    c.poly(st['cloth2'], [(cwx, cwy + 8.4), (cwx + 1.6, cwy + 11), (cwx, cwy + 13.6), (cwx - 1.6, cwy + 11)])
    for xx in (cwx - 6.8, cwx + 6.8):
      for yy in (cwy + 4.4, cwy + 15.8):
        c.circle(M, (xx, yy), 0.55)
    c.line(M, (cwx - 8, cwy + 17), (cwx + 8, cwy + 17), 0.6)
  f = _P(-40, -50, 150, 112)
  f.circle(_sh(M, 0.55), (px, py), 3.4)
  f.circle(M, (px, py), 2.7)
  f.circle(_sh(M, 1.6), (px - 0.8, py - 0.8), 0.9)
  for wx in (10, 60):
    f.wheel((wx, 52), 5.5, W, M, 6, spiked=(style == 1))
  if style == 0:
    f.flag((70, 42), 18, st['cloth'], st['cloth2'], 0.2)
  elif style == 1:
    f.flag((70, 42), 20, st['cloth'], st['cloth2'], 1.0, tattered=True, crest=(220, 210, 190))
    f.circle((226, 218, 196), (35, 24), 2.6)
    f.circle((30, 20, 20), (34.1, 23.7), 0.7); f.circle((30, 20, 20), (35.9, 23.7), 0.7)
  else:
    f.flag((70, 42), 20, st['cloth'], st['cloth2'], 0.4, crest=st['cloth2'])
    f.line(st['metal'], (-2, 42), (72, 42), 0.6)
  L = _LAYERS[k] = {'back': _native(b), 'arm': _native(a), 'cw': _native(c), 'front': _native(f), 'org': (-40, -50), 'piv': (px + 40, py + 50)}
  return L


def draw_trebuchet(surface, x, y, ang=146.0, loaded=True, style=None):
  style = SIEGE_STYLE if style is None else style
  st = STYLES[style]
  L = _treb_layers(style)
  ox, oy = x + L['org'][0], y + L['org'][1]
  px, py = 35, 5
  a = math.radians(ang)
  ca, sa = math.cos(a), math.sin(a)
  lx, ly = px + ca * 50, py + sa * 50
  sx, sy = px - ca * 22, py - sa * 22
  surface.blit(L['back'], (ox, oy))
  arm, off = _rot_about(L['arm'], -ang, L['piv'])
  surface.blit(arm, (ox + off[0], oy + off[1]))
  surface.blit(L['cw'], (x + sx - 12, y + sy - 2))    # the counterweight always hangs straight down
  if loaded:
    if ca < 0 and sa > 0:
      slx, sly = lx - 6, ly + 8
    else:
      slx, sly = lx + 2, ly + 8
    rope = _sh(st['rope'], 0.75)
    pygame.draw.line(surface, rope, (x + lx, y + ly), (x + slx - 2, y + sly - 2), 2)
    pygame.draw.line(surface, rope, (x + lx, y + ly), (x + slx + 2, y + sly - 2), 2)
    surface.blit(_boulder_img(4.2, style == 1), (x + slx - 12, y + sly - 16))
  surface.blit(L['front'], (ox, oy))
  _finish(surface)

# ------------------------------------------------------------------ ballista
def draw_ballista(surface, x, y, mode, style=None):
  style = SIEGE_STYLE if style is None else style
  st = STYLES[style]
  W, M, R = st['wood'], st['metal'], st['rope']
  p = _P(-30, -40, 100, 96)
  aiming = mode == 'aiming'
  # carriage
  p.plank_box(-2, 22, 42, 34, W, 3, band_col=M)
  # pedestal + swivel
  p.beam((14, 24), (19, 3), 4.0, _sh(W, 0.9), bands=(0.6,), band_col=M)
  p.beam((27, 24), (21, 3), 4.0, _sh(W, 0.82), bands=(0.6,), band_col=M)
  p.ellipse(_sh(M, 0.6), (13, 0.2, 14, 4.4))
  p.ellipse(M, (13, -0.4, 14, 4))
  # stock (pointing left, slightly up)
  tilt = -0.05
  s0, s1 = (-10, -8.5), (36, -8.5 - 46 * tilt * -1)
  s1 = (36, -6.2)
  # bow arms (seen from the side they sweep up and down from the front of the stock)
  fx, fy = 0, -8
  if style == 2:
    armc = (176, 182, 196)
  else:
    armc = _sh(W, 1.05)
  tips = [(6, -25), (6, 9)]
  for tx, ty in tips:
    mid = ((fx + tx) / 2 - 3, (fy + ty) / 2)
    p.beam((fx, fy), mid, 3.0 if style != 2 else 2.4, armc, grain=(style != 2), bands=(0.4,), band_col=M)
    p.beam(mid, (tx, ty), 2.2 if style != 2 else 1.8, armc, grain=(style != 2))
    p.circle(_sh(M, 0.7), (tx, ty), 1.2)
    p.circle(M, (tx, ty), 0.8)
  # torsion springs at the front
  p.rope_coil((fx, fy - 2.8), 2.2, 2.6, R)
  p.rope_coil((fx, fy + 2.8), 2.2, 2.6, R)
  # the stock itself
  p.beam(s0, s1, 3.4, _sh(W, 1.08), bands=(0.15, 0.55, 0.9), band_col=M, rivet=_sh(M, 1.5))
  # string: pulled back to the claw when aiming, straight when fired
  claw = (30, -8.0)
  if aiming:
    p.line((230, 226, 210), tips[0], claw, 0.45)
    p.line((230, 226, 210), tips[1], claw, 0.45)
    # bolt
    p.beam((-22, -10.5), (30, -10.5), 1.4, (150, 100, 52), grain=False)
    for k in range(3):                                          # fletching
      p.poly((200, 40, 40) if style != 2 else (240, 240, 245), [(24 + k * 2, -10.6), (27 + k * 2, -13.4), (27.6 + k * 2, -10.6)])
    p.poly((90, 92, 100), [(-22, -12.4), (-30, -10.5), (-22, -8.6)])
    p.poly((200, 204, 214), [(-22, -12.4), (-30, -10.5), (-22, -10.5)])
  else:
    p.line((230, 226, 210), tips[0], (5, -8), 0.45)
    p.line((230, 226, 210), tips[1], (5, -8), 0.45)
  p.poly(_sh(M, 0.6), [(28, -10), (32, -10), (32, -5.6), (28, -5.6)])   # trigger claw
  p.poly(M, [(28.4, -9.6), (31.6, -9.6), (31.6, -7), (28.4, -7)])
  # winch crank at the back
  p.wheel((37, -5), 3.0, W, M, 4)
  p.line(_sh(M, 0.8), (37, -5), (40, -9), 0.6)
  # wheels
  for wx in (8, 32):
    p.wheel((wx, 37), 9.5, W, M, 8, spiked=(style == 1))
  # style extras
  if style == 0:
    p.flag((40, 22), 16, st['cloth'], st['cloth2'], 0.7)
  elif style == 1:
    # repeating magazine of bolts on top + iron spikes
    p.plank_box(10, -20, 28, -12.5, (70, 50, 36), 2, band_col=M)
    for k in range(4):
      p.line((150, 100, 52), (12 + k * 4, -19.5), (12 + k * 4, -13), 0.8)
      p.poly((190, 190, 200), [(11.2 + k * 4, -19.5), (12 + k * 4, -22.5), (12.8 + k * 4, -19.5)])
    for k in range(3):
      p.poly((180, 176, 170), [(-2, 24 + k * 3), (-8, 25.3 + k * 3), (-2, 26.6 + k * 3)])
    p.flag((40, 22), 18, st['cloth'], st['cloth2'], 1.2, tattered=True, crest=(220, 210, 190))
  else:
    # steel mantlet shield with the royal crest
    sh = [(-6, 12), (6, 12), (6, 22), (0, 27), (-6, 22)]
    p.poly(_sh((150, 156, 170), 0.5), [(a_ + 0.5, b_ + 0.6) for a_, b_ in sh])
    p.poly((170, 176, 192), sh)
    p.poly(st['trim'], [(-4.6, 13.4), (4.6, 13.4), (4.6, 21.4), (0, 25.4), (-4.6, 21.4)])
    p.poly(st['cloth2'], [(0, 14.6), (2.2, 18.6), (0, 23), (-2.2, 18.6)])
    p.line(st['metal'], (-2, 22), (42, 22), 0.6)
    p.flag((40, 22), 18, st['cloth'], st['cloth2'], 0.3, crest=st['cloth2'])
  p.out(surface, x, y)


def prewarm_siege():
  """paint the siege layers and ballista poses up front (called when a run starts)."""
  try:
    _cat_layers(SIEGE_STYLE)
    _treb_layers(SIEGE_STYLE)
    _boulder_img(4.2, SIEGE_STYLE == 1)
  except Exception:
    pass
