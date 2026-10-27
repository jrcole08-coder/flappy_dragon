"""Detailed towers and castle pieces (the game uses the stone keep, castle gatehouse and castle keep). build(style, h, banner, seed) -> (surface, ox, top)
surface is drawn so the 95px-wide body starts at x = ox and the body top (the old crenel line)
sits at y = top; roofs, turrets and flags go above / beside it."""
import math, random
import pygame

BW = 95
def _sh(c, f):
  return tuple(max(0, min(255, int(v * f))) for v in c[:3])

# ------------------------------------------------------------------ building blocks
def stones(s, x0, y0, w, h, base, rnd, bw=19, bh=11, cyl=True, mortar=None, vary=0.12, cracks=0):
  mortar = mortar or _sh(base, 0.5)
  pygame.draw.rect(s, mortar, (x0, y0, w, h))
  row = 0
  y = y0
  while y < y0 + h:
    off = (bw // 2) if row % 2 else 0
    x = x0 - off
    while x < x0 + w:
      bwid = bw + rnd.randint(-3, 3)
      bx0, bx1 = max(x0, x + 1), min(x0 + w - 1, x + bwid - 1)
      by0, by1 = y + 1, min(y0 + h - 1, y + bh - 1)
      if bx1 - bx0 >= 2 and by1 - by0 >= 2:
        t = ((bx0 + bx1) / 2.0 - x0) / w
        f = rnd.uniform(1 - vary, 1 + vary * 0.6)
        if cyl:
          f *= 0.52 + 0.62 * math.sin(math.pi * min(1.0, t * 0.92 + 0.06)) ** 0.8 * (1.08 - 0.25 * t)
        c = _sh(base, f)
        pygame.draw.rect(s, c, (bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1))
        pygame.draw.line(s, _sh(c, 1.22), (bx0, by0), (bx1 - 1, by0))
        pygame.draw.line(s, _sh(c, 1.12), (bx0, by0), (bx0, by1 - 1))
        pygame.draw.line(s, _sh(c, 0.72), (bx0 + 1, by1), (bx1, by1))
        pygame.draw.line(s, _sh(c, 0.8), (bx1, by0 + 1), (bx1, by1))
        for _ in range(2):
          if rnd.random() < 0.5:
            s.set_at((rnd.randint(bx0 + 1, max(bx0 + 1, bx1 - 1)), rnd.randint(by0 + 1, max(by0 + 1, by1 - 1))), _sh(c, rnd.choice((0.8, 1.15))))
      x += bwid
    y += bh
    row += 1
  for _ in range(cracks):
    cx, cy = rnd.randint(x0 + 8, x0 + w - 8), rnd.randint(y0 + 10, y0 + h - 10)
    pts = [(cx, cy)]
    for k in range(5):
      cx += rnd.randint(-3, 3); cy += rnd.randint(3, 6); pts.append((cx, cy))
    pygame.draw.lines(s, _sh(base, 0.3), False, pts, 1)

def crenels(s, x0, y, w, n, base, mh=14, gap_dark=True):
  mw = w / float(n * 2 - 1)
  for i in range(n):
    x, yy, ww = int(x0 + i * 2 * mw), int(y - mh), int(mw + 0.99)
    pygame.draw.rect(s, _sh(base, 0.5), (x + 1, yy + 1, ww, mh))
    pygame.draw.rect(s, base, (x, yy, ww, mh))
    pygame.draw.line(s, _sh(base, 1.3), (x, yy), (x + ww - 1, yy), 2)
    pygame.draw.line(s, _sh(base, 0.7), (x + ww - 1, yy), (x + ww - 1, yy + mh), 2)
    pygame.draw.line(s, _sh(base, 0.8), (x, yy + mh // 2), (x + ww - 1, yy + mh // 2))

def shade(s, rect, a=60):
  x, y, w, h = [int(v) for v in rect]
  g = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
  g.fill((0, 0, 0, a))
  s.blit(g, (x, y))

def corbels(s, x0, y, w, base, n=7):
  """stepped stone corbels holding up an overhanging parapet (machicolations)."""
  step = w / float(n)
  pygame.draw.rect(s, (18, 16, 20), (x0, y, w, 8))
  for i in range(n + 1):
    cx = int(x0 + i * step)
    pygame.draw.polygon(s, _sh(base, 0.85), [(cx - 3, y), (cx + 3, y), (cx + 2, y + 5), (cx, y + 9), (cx - 2, y + 5)])
    pygame.draw.line(s, _sh(base, 1.2), (cx - 3, y), (cx - 1, y + 7))

def band(s, x0, y, w, base, hgt=6):
  pygame.draw.rect(s, _sh(base, 0.5), (x0, y + 1, w, hgt))
  pygame.draw.rect(s, base, (x0, y, w, hgt))
  pygame.draw.line(s, _sh(base, 1.3), (x0, y), (x0 + w - 1, y), 2)
  pygame.draw.line(s, _sh(base, 0.6), (x0, y + hgt - 1), (x0 + w - 1, y + hgt - 1))

def cone(s, cx, by, hw, ht, col, shingle=True, finial=(200, 170, 80)):
  top = (cx, by - ht)
  pygame.draw.polygon(s, _sh(col, 0.45), [(cx - hw - 1, by + 2), top, (cx + hw + 1, by + 2)])
  pygame.draw.polygon(s, col, [(cx - hw, by), top, (cx + hw, by)])
  pygame.draw.polygon(s, _sh(col, 0.7), [(cx + hw * 0.25, by), top, (cx + hw, by)])
  pygame.draw.polygon(s, _sh(col, 1.18), [(cx - hw, by), top, (cx - hw * 0.45, by)])
  if shingle:
    rows = max(2, int(ht / 7))
    for k in range(1, rows):
      t = k / float(rows)
      yy = by - ht * (1 - t)
      half = hw * t
      n = max(2, int(half / 4))
      for j in range(-n, n + 1):
        xx = cx + j * half / float(n) + (2 if k % 2 else 0)
        if abs(xx - cx) < half - 1:
          pygame.draw.arc(s, _sh(col, 0.55), (xx - 3, yy - 2, 6, 5), math.pi, 2 * math.pi, 1)
  pygame.draw.line(s, (80, 64, 40), top, (cx, by - ht - 10), 2)
  pygame.draw.circle(s, finial, (cx, by - ht - 1), 2)

def window(s, x, y, w, h, lit, frame=(70, 66, 70), glow=(255, 186, 80)):
  pygame.draw.rect(s, _sh(frame, 0.5), (x - 3, y - 1, w + 6, h + 5))
  pygame.draw.ellipse(s, _sh(frame, 0.5), (x - 3, y - w // 2 - 3, w + 6, w + 4))
  pygame.draw.rect(s, frame, (x - 2, y, w + 4, h + 3))
  pygame.draw.ellipse(s, frame, (x - 2, y - w // 2 - 2, w + 4, w + 2))
  col = glow if lit else (22, 20, 30)
  pygame.draw.rect(s, col, (x, y, w, h))
  pygame.draw.ellipse(s, col, (x, y - w // 2, w, w))
  if lit:
    pygame.draw.rect(s, _sh(glow, 1.15), (x + 1, y + h // 2, w - 2, h // 2))
    pygame.draw.line(s, _sh(glow, 0.6), (x + w // 2, y - w // 2 + 1), (x + w // 2, y + h - 1))
    pygame.draw.line(s, _sh(glow, 0.6), (x, y + h // 3), (x + w - 1, y + h // 3))
  else:
    pygame.draw.line(s, (50, 48, 64), (x + 1, y - w // 3), (x + 2, y + h - 2))
  pygame.draw.rect(s, _sh(frame, 1.3), (x - 4, y + h + 2, w + 8, 3))          # sill
  pygame.draw.line(s, _sh(frame, 0.5), (x - 4, y + h + 5), (x + w + 3, y + h + 5))

def slit(s, cx, y, glow=False):
  c = (255, 160, 60) if glow else (16, 12, 14)
  pygame.draw.rect(s, (40, 36, 40), (cx - 3, y - 1, 6, 20))
  pygame.draw.rect(s, c, (cx - 1, y, 3, 18))
  pygame.draw.rect(s, c, (cx - 5, y + 7, 11, 3))

def hang_banner(s, cx, y, col, h=44, emblem=(240, 200, 60)):
  w = 22
  pygame.draw.rect(s, (90, 64, 30), (cx - w // 2 - 3, y - 2, w + 6, 4))
  for kx in (cx - w // 2 - 4, cx + w // 2 + 3):
    pygame.draw.circle(s, (220, 180, 70), (kx, y), 2)
  pts = [(cx - w // 2, y + 2), (cx + w // 2, y + 2), (cx + w // 2, y + h), (cx, y + h + 10), (cx - w // 2, y + h)]
  pygame.draw.polygon(s, _sh(col, 0.5), [(px + 1, py + 1) for px, py in pts])
  pygame.draw.polygon(s, col, pts)
  for k in (-6, 1, 7):                                        # folds
    pygame.draw.line(s, _sh(col, 0.72), (cx + k, y + 3), (cx + k, y + h + 3 - abs(k)))
    pygame.draw.line(s, _sh(col, 1.2), (cx + k - 2, y + 3), (cx + k - 2, y + h - abs(k)))
  pygame.draw.lines(s, emblem, True, pts, 1)
  ey = y + h // 2 - 2
  pygame.draw.polygon(s, _sh(emblem, 0.6), [(cx, ey - 8), (cx + 7, ey - 2), (cx + 4, ey + 8), (cx - 4, ey + 8), (cx - 7, ey - 2)])
  pygame.draw.polygon(s, emblem, [(cx, ey - 6), (cx + 5, ey - 1), (cx + 3, ey + 6), (cx - 3, ey + 6), (cx - 5, ey - 1)])
  pygame.draw.circle(s, _sh(col, 0.8), (cx, ey), 2)

def pennant(s, x, y, h, col, wave=0.0, tatter=False):
  pygame.draw.line(s, (70, 54, 36), (x, y), (x, y - h), 2)
  pygame.draw.circle(s, (220, 190, 90), (x, y - h), 2)
  top = y - h + 2
  pts = [(x + 1, top)]
  for k in range(1, 6):
    pts.append((x + k * 4, top + math.sin(k + wave) * 1.5 + k * 0.6))
  bot = [(px, py + 9 - k * 1.2) for k, (px, py) in enumerate(pts)]
  if tatter:
    bot = [(px, py + (2 if k % 2 else 0)) for k, (px, py) in enumerate(bot)]
  poly = pts + bot[::-1]
  pygame.draw.polygon(s, col, poly)
  pygame.draw.lines(s, _sh(col, 1.4), False, pts[:4], 1)
  pygame.draw.lines(s, _sh(col, 0.6), False, bot, 1)

def ivy(s, x, y, n, rnd):
  for k in range(n):
    o = rnd.randint(-5, 5)
    c = rnd.choice(((38, 86, 40), (58, 118, 50), (30, 66, 34), (74, 140, 60)))
    pygame.draw.ellipse(s, c, (x + o - 3, y - k * 6 - 3, 7, 6))
    if rnd.random() < 0.4:
      pygame.draw.line(s, (40, 60, 30), (x, y - k * 6), (x + o, y - k * 6 - 3))

def moss(s, x0, y, w, rnd):
  for _ in range(int(w / 3)):
    x = rnd.randint(x0, x0 + w - 3)
    pygame.draw.ellipse(s, rnd.choice(((60, 96, 46), (80, 118, 56), (46, 76, 40))), (x, y - rnd.randint(2, 7), rnd.randint(4, 8), 4))

def glow(s, cx, cy, r, col):
  g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
  for k in range(8, 0, -1):
    t = k / 8.0
    pygame.draw.circle(g, col + (int(70 * (1 - t) + 8),), (r, r), int(r * t))
  s.blit(g, (cx - r, cy - r))

def torch(s, x, y):
  glow(s, x, y - 6, 18, (255, 150, 40))
  pygame.draw.rect(s, (60, 46, 36), (x - 2, y - 2, 4, 10))
  pygame.draw.polygon(s, (255, 130, 30), [(x - 4, y - 2), (x, y - 13), (x + 4, y - 2)])
  pygame.draw.polygon(s, (255, 230, 120), [(x - 2, y - 2), (x, y - 8), (x + 2, y - 2)])

def door(s, cx, by, w, h, wood=(96, 62, 34), metal=(70, 70, 76)):
  pygame.draw.rect(s, (40, 36, 40), (cx - w // 2 - 3, by - h, w + 6, h))
  pygame.draw.ellipse(s, (40, 36, 40), (cx - w // 2 - 3, by - h - w // 2 - 3, w + 6, w + 6))
  pygame.draw.rect(s, wood, (cx - w // 2, by - h, w, h))
  pygame.draw.ellipse(s, wood, (cx - w // 2, by - h - w // 2, w, w))
  for k in range(1, 4):
    xx = cx - w // 2 + k * w // 4
    pygame.draw.line(s, _sh(wood, 0.6), (xx, by - h - w // 2 + 3), (xx, by - 1))
  for yy in (by - h + 4, by - 8):
    pygame.draw.rect(s, metal, (cx - w // 2, yy, w, 3))
    for k in range(4):
      pygame.draw.circle(s, _sh(metal, 1.5), (cx - w // 2 + 3 + k * (w - 6) // 3, yy + 1), 1)
  pygame.draw.circle(s, (200, 170, 80), (cx + w // 4, by - h // 2), 2)

def portcullis(s, cx, by, w, h):
  pygame.draw.rect(s, (26, 20, 22), (cx - w // 2, by - h, w, h))
  pygame.draw.ellipse(s, (26, 20, 22), (cx - w // 2, by - h - w // 2, w, w))
  glow(s, cx, by - h // 2, w // 2, (120, 70, 20))
  for k in range(5):
    xx = cx - w // 2 + 3 + k * (w - 6) // 4
    pygame.draw.line(s, (90, 92, 100), (xx, by - h - w // 3), (xx, by - 5), 2)
    pygame.draw.polygon(s, (150, 152, 160), [(xx - 2, by - 5), (xx + 2, by - 5), (xx, by - 1)])
  for yy in range(by - h - 4, by - 6, 8):
    pygame.draw.line(s, (80, 82, 90), (cx - w // 2 + 2, yy), (cx + w // 2 - 2, yy), 2)
  # stone arch voussoirs
  for k in range(9):
    a = math.pi + k * math.pi / 8
    x1, y1 = cx + math.cos(a) * (w / 2 + 1), by - h + math.sin(a) * (w / 2 + 1)
    x2, y2 = cx + math.cos(a) * (w / 2 + 6), by - h + math.sin(a) * (w / 2 + 6)
    pygame.draw.line(s, (150, 146, 150), (x1, y1), (x2, y2), 3)

def shield(s, cx, cy, col, emblem=(240, 200, 60)):
  pts = [(cx - 9, cy - 9), (cx + 9, cy - 9), (cx + 9, cy + 2), (cx, cy + 11), (cx - 9, cy + 2)]
  pygame.draw.polygon(s, (40, 36, 40), [(x + 1, y + 1) for x, y in pts])
  pygame.draw.polygon(s, (200, 170, 80), pts)
  inner = [(cx - 7, cy - 7), (cx + 7, cy - 7), (cx + 7, cy + 1), (cx, cy + 8), (cx - 7, cy + 1)]
  pygame.draw.polygon(s, col, inner)
  pygame.draw.polygon(s, emblem, [(cx, cy - 5), (cx + 3, cy), (cx, cy + 5), (cx - 3, cy)])

# ------------------------------------------------------------------ the towers
STONE = (128, 126, 132)
SAND = (166, 142, 108)
BASALT = (66, 60, 70)
SLATE = (54, 62, 96)
CLAY = (150, 60, 44)

def keep(h, banner, rnd, open_top=False):
  """1 Stone keep: round tower, corbelled parapet, slate cone roof (or open battlements)."""
  ox, top = 12, 82
  s = pygame.Surface((BW + 24, h + top), pygame.SRCALPHA)
  stones(s, ox, top, BW, h, STONE, rnd, cracks=1)
  band(s, ox - 3, top + h - 16, BW + 6, _sh(STONE, 0.75), 16)                   # plinth
  band(s, ox - 4, top + 60, BW + 8, _sh(STONE, 0.95), 5)
  par = top - 18
  corbels(s, ox - 4, top - 2, BW + 8, STONE)
  stones(s, ox - 6, par, BW + 12, 16, _sh(STONE, 1.05), rnd, bw=14, bh=8)
  if open_top:
    crenels(s, ox - 6, par, BW + 12, 5, _sh(STONE, 1.05))
  else:
    cone(s, ox + BW // 2, par + 2, BW // 2 + 10, 62, SLATE)
  for k in range(max(1, (h - 60) // 95)):
    window(s, ox + BW // 2 - 7, top + 34 + k * 92, 14, 22, rnd.random() < 0.75)
  if h > 200:
    slit(s, ox + 20, top + 110); slit(s, ox + BW - 20, top + 150)
  hang_banner(s, ox + 26, top + 72, banner)
  moss(s, ox, top + h - 16, BW, rnd)
  for _ in range(3):
    ivy(s, ox + rnd.randint(8, BW - 8), top + h - 14, rnd.randint(4, 9), rnd)
  return s, ox, top

def gatehouse(h, banner, rnd, open_top=True):
  """2 Castle gatehouse: square tower, corner bartizans, portcullis gate, torches, crest."""
  ox, top = 14, 64
  s = pygame.Surface((BW + 28, h + top), pygame.SRCALPHA)
  stones(s, ox, top, BW, h, (138, 134, 128), rnd, bw=22, bh=12, cyl=False)
  for yy in range(top, top + h, 24):                                          # corner quoins
    pygame.draw.rect(s, (176, 170, 160), (ox, yy, 10, 11)); pygame.draw.rect(s, (110, 106, 100), (ox + BW - 10, yy + 12, 10, 11))
  shade(s, (ox + BW - 14, top, 14, h), 60)
  band(s, ox - 4, top - 4, BW + 8, (150, 146, 140), 6)
  crenels(s, ox - 4, top - 4, BW + 8, 5, (150, 146, 140))
  for bx in (ox - 6, ox + BW - 12):                                           # bartizans
    pygame.draw.polygon(s, (110, 106, 100), [(bx, top + 22), (bx + 18, top + 22), (bx + 9, top + 36)])
    stones(s, bx, top - 6, 18, 28, (150, 146, 140), rnd, bw=9, bh=7)
    cone(s, bx + 9, top - 6, 11, 26, SLATE)
    slit(s, bx + 9, top + 2)
  portcullis(s, ox + BW // 2, top + h - 2, 34, 34)
  torch(s, ox + 18, top + h - 44); torch(s, ox + BW - 18, top + h - 44)
  shield(s, ox + BW // 2, top + h - 92, banner)
  for k in range(max(0, (h - 150) // 80)):
    window(s, ox + BW // 2 - 6, top + 26 + k * 78, 12, 18, rnd.random() < 0.7)
  if h > 220:
    hang_banner(s, ox + 22, top + 20, banner, 50); hang_banner(s, ox + BW - 22, top + 20, banner, 50)
  moss(s, ox, top + h, BW, rnd)
  return s, ox, top

def _gable(s, ox, top, banner):
  pygame.draw.polygon(s, _sh(CLAY, 0.6), [(ox + 14, top - 12), (ox + BW // 2, top - 50), (ox + BW - 14, top - 12)])
  pygame.draw.polygon(s, CLAY, [(ox + 16, top - 12), (ox + BW // 2, top - 48), (ox + BW // 2, top - 12)])
  for k in range(5):
    yy = top - 16 - k * 7
    pygame.draw.line(s, _sh(CLAY, 0.7), (ox + 16 + k * 6, yy), (ox + BW - 16 - k * 6, yy))
  pennant(s, ox + BW // 2, top - 50, 20, banner, 0.4)

def castle(h, banner, rnd, open_top=False):
  """3 Castle keep: square keep with two slender round turrets rising beside it."""
  ox, top = 20, 110
  s = pygame.Surface((BW + 40, h + top), pygame.SRCALPHA)
  stones(s, ox + 10, top, BW - 20, h, (140, 136, 140), rnd, bw=18, bh=11, cyl=False)
  shade(s, (ox + BW - 26, top, 16, h), 50)
  band(s, ox + 6, top - 4, BW - 12, (156, 152, 156), 6)
  crenels(s, ox + 6, top - 4, BW - 12, 4, (156, 152, 156))
  # central gable roof behind the crenels (left off when the top is a fighting platform)
  if not open_top:
    _gable(s, ox, top, banner)
  # turrets
  for tx, extra, side in ((ox - 6, 46, 0), (ox + BW - 22, 26, 1)):
    tw = 28
    stones(s, tx, top - extra, tw, h + extra, (150, 146, 150), rnd, bw=10, bh=9)
    band(s, tx - 3, top - extra - 4, tw + 6, (160, 156, 160), 5)
    cone(s, tx + tw // 2, top - extra - 4, tw // 2 + 4, 40, SLATE)
    pennant(s, tx + tw // 2, top - extra - 52, 14, banner, side * 1.3)
    for k in range(max(1, (h + extra - 60) // 70)):
      slit(s, tx + tw // 2, top - extra + 16 + k * 66, glow=rnd.random() < 0.3)
  for k in range(max(1, (h - 50) // 80)):
    window(s, ox + BW // 2 - 7, top + 22 + k * 78, 14, 22, rnd.random() < 0.8)
  hang_banner(s, ox + BW // 2, top + 60, banner, 46) if h > 200 else None
  door(s, ox + BW // 2, top + h, 22, 26)
  moss(s, ox - 6, top + h, BW + 12, rnd)
  for _ in range(2):
    ivy(s, ox + rnd.randint(14, BW - 14), top + h - 4, rnd.randint(4, 8), rnd)
  return s, ox, top

def watch(h, banner, rnd, open_top=False):
  """4 Fortified watchtower: sandstone, timber hoarding with shingles, braziers."""
  ox, top = 16, 72
  s = pygame.Surface((BW + 32, h + top), pygame.SRCALPHA)
  stones(s, ox, top, BW, h, SAND, rnd, bw=24, bh=12, cyl=False, vary=0.1)
  for yy in range(top, top + h, 24):
    pygame.draw.rect(s, _sh(SAND, 1.18), (ox, yy, 12, 11)); pygame.draw.rect(s, _sh(SAND, 0.72), (ox + BW - 12, yy + 12, 12, 11))
  hy = top - 32
  wood = (104, 68, 38)
  pygame.draw.rect(s, _sh(wood, 0.5), (ox - 9, hy + 1, BW + 18, 36))
  pygame.draw.rect(s, wood, (ox - 10, hy, BW + 20, 34))
  for x in range(ox - 10, ox + BW + 10, 6):
    pygame.draw.line(s, _sh(wood, 0.7), (x, hy), (x, hy + 33))
    pygame.draw.line(s, _sh(wood, 1.15), (x + 1, hy), (x + 1, hy + 33))
  for yy in (hy + 2, hy + 30):
    pygame.draw.rect(s, _sh(wood, 0.6), (ox - 10, yy, BW + 20, 3))
  for x in (ox + 6, ox + 34, ox + 62):                                         # shutters
    pygame.draw.rect(s, (20, 14, 10), (x, hy + 9, 12, 13))
    pygame.draw.rect(s, _sh(wood, 1.3), (x - 1, hy + 8, 14, 2))
  for k in range(7):                                                            # support struts
    x = ox - 6 + k * (BW + 12) // 6
    pygame.draw.line(s, _sh(wood, 0.8), (x, hy + 34), (x + (6 if k < 3 else -6), top + 14), 3)
  if open_top:
    for x in (ox - 6, ox + BW + 6):
      pygame.draw.rect(s, (50, 42, 36), (x - 4, hy - 8, 8, 8))
      glow(s, x, hy - 14, 18, (255, 140, 30))
      pygame.draw.polygon(s, (255, 130, 30), [(x - 6, hy - 8), (x, hy - 24), (x + 6, hy - 8)])
      pygame.draw.polygon(s, (255, 230, 120), [(x - 3, hy - 8), (x, hy - 16), (x + 3, hy - 8)])
    pennant(s, ox + BW - 2, hy, 24, banner, 0.8)
  else:
    pygame.draw.polygon(s, _sh(CLAY, 0.5), [(ox - 18, hy + 3), (ox + BW // 2, hy - 34), (ox + BW + 18, hy + 3)])
    pygame.draw.polygon(s, CLAY, [(ox - 16, hy + 1), (ox + BW // 2, hy - 32), (ox + BW + 16, hy + 1)])
    for k in range(5):
      yy = hy - k * 7
      half = (BW // 2 + 16) * (1 - k / 5.0)
      for j in range(int(-half), int(half), 6):
        pygame.draw.arc(s, _sh(CLAY, 0.6), (ox + BW // 2 + j - 3 + (3 if k % 2 else 0), yy - 3, 7, 6), math.pi, 2 * math.pi, 1)
    pennant(s, ox + BW // 2, hy - 32, 20, banner, 0.3)
  for k in range(max(1, (h - 40) // 66)):
    slit(s, ox + BW // 2, top + 22 + k * 62, glow=k % 2 == 1)
  door(s, ox + BW // 2, top + h, 24, 30)
  torch(s, ox + BW // 2 - 22, top + h - 34)
  moss(s, ox, top + h, BW, rnd)
  return s, ox, top

def fortress(h, banner, rnd, open_top=True):
  """5 Dark fortress tower: basalt blocks, red-lit windows, iron spikes, chains, skulls."""
  ox, top = 12, 60
  s = pygame.Surface((BW + 24, h + top), pygame.SRCALPHA)
  stones(s, ox, top, BW, h, BASALT, rnd, bw=17, bh=12, cracks=3, vary=0.18)
  band(s, ox - 5, top - 6, BW + 10, (80, 74, 86), 8)
  crenels(s, ox - 5, top - 6, BW + 10, 5, (80, 74, 86), 16)
  for k in range(5):                                                          # iron spikes on merlons
    x = ox - 5 + k * 2 * (BW + 10) / 9.0 + (BW + 10) / 18.0
    pygame.draw.polygon(s, (150, 150, 158), [(x - 3, top - 22), (x, top - 34), (x + 3, top - 22)])
    pygame.draw.line(s, (220, 220, 230), (x - 1, top - 23), (x, top - 32))
  for k in range(max(1, (h - 50) // 85)):
    y = top + 30 + k * 82
    window(s, ox + BW // 2 - 7, y, 14, 22, True, frame=(50, 44, 54), glow=(230, 50, 30))
    glow(s, ox + BW // 2, y + 8, 22, (200, 30, 20))
  for cx in (ox + 14, ox + BW - 14):                                          # hanging chains
    for k in range(8):
      pygame.draw.ellipse(s, (110, 110, 118), (cx - 2, top + 6 + k * 6, 5, 7), 1)
  for sx, sy in ((ox + 14, top + 56), (ox + BW - 14, top + 56)):              # skulls
    pygame.draw.circle(s, (226, 218, 196), (sx, sy), 5)
    pygame.draw.rect(s, (226, 218, 196), (sx - 3, sy + 3, 7, 4))
    pygame.draw.circle(s, (30, 10, 10), (sx - 2, sy), 1); pygame.draw.circle(s, (30, 10, 10), (sx + 2, sy), 1)
  hang_banner(s, ox + BW // 2, top + 8, (40, 30, 34), 40, emblem=(200, 30, 30)) if h > 180 else None
  pennant(s, ox + BW - 6, top - 22, 22, (190, 30, 30), 1.0, tatter=True)
  portcullis(s, ox + BW // 2, top + h - 2, 30, 28)
  return s, ox, top

def spire(h, banner, rnd, open_top=False):
  """6 Sorcerer spire: tapered dark stone, rune bands, spiked crown, floating crystal."""
  ox, top = 10, 96
  s = pygame.Surface((BW + 20, h + top), pygame.SRCALPHA)
  body = pygame.Surface((BW, h), pygame.SRCALPHA)
  stones(body, 0, 0, BW, h, (70, 64, 92), rnd, bw=15, bh=10)
  mask = pygame.Surface((BW, h), pygame.SRCALPHA)
  pygame.draw.polygon(mask, (255, 255, 255, 255), [(9, 0), (BW - 9, 0), (BW - 1, h), (0, h)])
  try:
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
  except Exception:
    pass
  s.blit(body, (ox, top))
  gl = {(170, 40, 40): (255, 110, 90), (40, 80, 180): (110, 200, 255)}.get(tuple(banner), (190, 120, 255))
  for k in range(0, h - 20, 52):
    y = top + 24 + k
    for x in range(ox + 14, ox + BW - 14, 10):
      pygame.draw.lines(s, gl, False, [(x, y), (x + 3, y - 4), (x + 6, y), (x + 9, y - 4)], 1)
  for k in range(max(1, (h - 40) // 90)):
    y = top + 44 + k * 88
    glow(s, ox + BW // 2, y + 6, 16, gl)
    pygame.draw.polygon(s, gl, [(ox + BW // 2 - 7, y + 18), (ox + BW // 2, y), (ox + BW // 2 + 7, y + 18)])
    pygame.draw.polygon(s, (255, 255, 255), [(ox + BW // 2 - 3, y + 18), (ox + BW // 2, y + 7), (ox + BW // 2 + 3, y + 18)])
  for i in range(6):
    x = ox + 6 + i * 17
    pygame.draw.polygon(s, (52, 46, 70), [(x, top + 2), (x + 8, top - 20 - (i % 2) * 10), (x + 16, top + 2)])
    pygame.draw.line(s, (96, 88, 126), (x + 1, top + 1), (x + 8, top - 18 - (i % 2) * 10))
  pygame.draw.polygon(s, (40, 36, 56), [(ox + BW // 2 - 14, top - 4), (ox + BW // 2, top - 70), (ox + BW // 2 + 14, top - 4)])
  pygame.draw.line(s, gl, (ox + BW // 2, top - 68), (ox + BW // 2, top - 6))
  cy = top - 84
  glow(s, ox + BW // 2, cy, 22, gl)
  pygame.draw.polygon(s, gl, [(ox + BW // 2, cy - 12), (ox + BW // 2 + 7, cy), (ox + BW // 2, cy + 12), (ox + BW // 2 - 7, cy)])
  pygame.draw.polygon(s, (255, 255, 255), [(ox + BW // 2, cy - 12), (ox + BW // 2 + 7, cy), (ox + BW // 2, cy)])
  return s, ox, top

STYLES = [keep, gatehouse, castle, watch, fortress, spire]
NAMES = ["Stone keep", "Castle gatehouse", "Castle keep", "Fortified watchtower", "Dark fortress", "Sorcerer spire"]
OPEN_TOP = {0: True, 1: True, 3: True, 4: True}       # styles with a fighting platform an archer can stand on

def build(style, h, banner, seed=0, open_top=None):
  rnd = random.Random(seed)
  fn = STYLES[style]
  if open_top is None:
    open_top = rnd.random() < 0.5 if style in (0, 3) else style in (1, 4)
  return fn(h, banner, rnd, open_top)


GAME_STYLES = (0, 1, 2)                 # stone keep, castle gatehouse, castle keep
PERCH = {0: 18, 1: 4, 2: 4}             # how far above the body top a unit stands on an open top

def _harden(img):
  """fully opaque / fully clear pixels only (the game turns towers into colorkey sprites)."""
  try:
    solid = img.copy()
    solid.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
    m = pygame.mask.from_surface(img, 100)
    return m.to_surface(setsurface=solid, unsetcolor=(0, 0, 0, 0))
  except Exception:
    return img

def tower_art(h, banner):
  """random tower for a level: {'surf', 'ox', 'top', 'perch'} (perch = None if it has a roof)."""
  style = random.choice(GAME_STYLES)
  rnd = random.Random(random.randrange(1 << 30))
  open_top = True if style == 1 else rnd.random() < 0.6
  surf, ox, top = STYLES[style](h, banner, rnd, open_top)
  return {'surf': _harden(surf), 'ox': ox, 'top': top, 'perch': PERCH[style] if open_top else None, 'style': style}
