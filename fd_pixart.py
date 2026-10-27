"""Pixel-art dragons. Each dragon is drawn on a tiny canvas (84x64), outlined, then scaled up 2x
with no smoothing so the pixels stay crisp. fd_art caches the results."""
import math
import pygame

S = 2                      # pixel scale
CW, CH = 84, 64            # canvas size in art pixels
AX, AY = 20, 20            # art-pixel position of the 65x38 hitbox's top-left corner
OX, OY = AX * S, AY * S    # blit offset (game pixels) from the hitbox corner to the sprite corner
BONE = (236, 224, 192)
CLAW = (244, 236, 210)
VARIANTS = {'BLUE': 'ice', 'GREEN': 'acid', 'YELLOW': 'storm', 'SILVER': 'wind', 'CHRONO': 'time'}


def shade(c, f):
  return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))), max(0, min(255, int(c[2] * f))))


def lite(c, n):
  return (min(255, c[0] + n), min(255, c[1] + n), min(255, c[2] + n))


def blend(a, b, t):
  return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t), int(a[2] * (1 - t) + b[2] * t))


def frame_index(wing):
  """0 = wings up, 1 = half up, 3 = half down, 2 = down."""
  f = math.sin(wing)
  if f > 0.5:
    return 0
  if f > 0:
    return 1
  if f > -0.5:
    return 3
  return 2


# wing tips (relative to the shoulder) for each flap frame: outer, middle, inner finger
WING_SCALE = {0: 1.0, 1: 1.0, 3: 1.0, 2: 1.0}
WING_TIPS = {0: ((-34, -14), (-18, -21), (0, -20)), 1: ((-34, -4), (-20, -11), (-4, -12)),
             3: ((-33, 5), (-20, 0), (-5, -2)), 2: ((-30, 10), (-18, 10), (-4, 8))}


def _poly(s, col, pts):
  pygame.draw.polygon(s, col, [(int(x), int(y)) for x, y in pts])


def _ell(s, col, x, y, w, h):
  pygame.draw.ellipse(s, col, (int(x), int(y), max(1, int(w)), max(1, int(h))))


def _line(s, col, a, b, w=1):
  pygame.draw.line(s, col, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), w)


def _path(s, col, pts, radii):
  """A thick tube: circles along a polyline."""
  for i in range(len(pts) - 1):
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    r0, r1 = radii[i], radii[i + 1]
    for k in range(4):
      t = k / 4.0
      pygame.draw.circle(s, col, (int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)), max(1, int(r0 + (r1 - r0) * t)))
  pygame.draw.circle(s, col, (int(pts[-1][0]), int(pts[-1][1])), max(1, int(radii[-1])))


def _wing(s, shoulder, tips, membrane, bone, hi, scale=1.0, off=(0, 0)):
  sx, sy = shoulder[0] + off[0], shoulder[1] + off[1]
  t = [(sx + dx * scale, sy + dy * scale) for dx, dy in tips]
  elbow = ((sx + t[0][0]) / 2.0, (sy + t[0][1]) / 2.0 - 3)

  def scallop(a, b):
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    return (mx + (sx - mx) * 0.2, my + (sy - my) * 0.2)

  pts = [(sx, sy), elbow, t[0], scallop(t[0], t[1]), t[1], scallop(t[1], t[2]), t[2]]
  _poly(s, membrane, pts)
  for tp in t:
    _line(s, hi, (sx, sy), ((sx + tp[0]) / 2.0 + 1, (sy + tp[1]) / 2.0 + 2), 1)
  _line(s, bone, (sx, sy), elbow, 2)
  _line(s, bone, elbow, t[0], 2)
  _line(s, bone, (sx, sy), t[1], 1)
  _line(s, bone, (sx, sy), t[2], 1)
  _poly(s, BONE, [(t[0][0], t[0][1]), (t[0][0] - 2, t[0][1] + 3), (t[0][0] + 2, t[0][1] + 2)])


def _outline(surf, col):
  try:
    m = pygame.mask.from_surface(surf)
    sil = m.to_surface(setcolor=col + (255,), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
      out.blit(sil, (dx, dy))
    out.blit(surf, (0, 0))
    return out
  except Exception:
    return surf


def _finish(s, pal, flip):
  s = _outline(s, shade(pal['dark'], 0.32))
  s = pygame.transform.scale(s, (CW * S, CH * S))
  if flip:
    s = pygame.transform.flip(s, True, False)
  return s


def _head_and_neck(s, pal, hd, fire, ring, variant, horn):
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh = shade(m, 0.72)
  deep = shade(d, 0.7)
  hi = lite(m, 38)
  hy = 17 + hd
  pts = [(44, 27), (48, 23), (52, 20 + hd // 2), (55, hy + 1)]
  _path(s, sh, pts, [6, 5, 5, 5])
  _path(s, m, [(p[0], p[1] - 1) for p in pts], [5, 4, 4, 4])
  for p in pts[:-1]:
    pygame.draw.circle(s, b, (p[0] + 2, p[1] + 3), 2)
  # horns, cheek spike
  _poly(s, horn, [(52, hy - 4), (55, hy - 4), (47, hy - 13), (46, hy - 11)])
  _poly(s, shade(horn, 0.8), [(56, hy - 4), (59, hy - 4), (54, hy - 12), (52, hy - 11)])
  _poly(s, deep, [(51, hy), (46, hy + 4), (52, hy + 4)])
  # skull + snout
  _ell(s, sh, 50, hy - 5, 13, 11)
  _ell(s, m, 50, hy - 6, 13, 10)
  _ell(s, hi, 53, hy - 5, 6, 2)
  _poly(s, m, [(58, hy - 3), (67, hy - 1), (67, hy + 4), (58, hy + 4)])
  _poly(s, hi, [(59, hy - 3), (66, hy - 1), (66, hy), (59, hy - 1)])
  pygame.draw.rect(s, sh, (62, hy + 2, 5, 2))
  pygame.draw.rect(s, deep, (65, hy, 1, 1))       # nostril
  if fire:
    _poly(s, (70, 14, 8), [(58, hy + 3), (67, hy + 3), (66, hy + 8), (58, hy + 7)])
    _poly(s, ring, [(60, hy + 4), (66, hy + 4), (65, hy + 6), (60, hy + 6)])
    _poly(s, shade(m, 0.7), [(57, hy + 5), (67, hy + 8), (66, hy + 10), (56, hy + 8)])
    for px, py in ((60, hy + 3), (64, hy + 3), (62, hy + 6)):
      s.set_at((px, py), CLAW)
    for k in range(3):
      pygame.draw.circle(s, ring, (68 + k * 2, hy + 3 + k * 2 - (k % 2) * 4), 1)
  else:
    pygame.draw.rect(s, shade(m, 0.6), (59, hy + 3, 8, 1))
    s.set_at((61, hy + 4), CLAW)
    s.set_at((65, hy + 4), CLAW)
  # eye
  ex = 57
  pygame.draw.rect(s, (18, 10, 10), (ex - 1, hy - 3, 4, 3))
  pygame.draw.rect(s, pal['eye'], (ex, hy - 3, 2, 2))
  s.set_at((ex, hy - 3), (255, 255, 255))
  if variant == 'acid':
    for dx in (60, 64):
      s.set_at((dx, hy + 5 if not fire else hy + 11), (150, 255, 60))
  if variant == 'storm':
    _line(s, (255, 255, 160), (49, hy - 6), (52, hy - 3), 1)


def draw_dragon_px(pal, variant, fidx, hd, fire, ring):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh = shade(m, 0.72)
  deep = shade(d, 0.7)
  hi = lite(m, 38)
  membrane = blend(b, m, 0.28)
  membrane_far = blend(m, d, 0.55)
  bone = shade(d, 0.9)
  horn = BONE
  spine = d
  if variant == 'ice':
    horn, spine = (205, 240, 255), (190, 235, 255)
  elif variant == 'acid':
    spine = (140, 235, 60)
  elif variant == 'time':
    horn = (240, 210, 110)
  elif variant == 'storm':
    spine = (255, 235, 110)
  shoulder = (38, 24)
  tips = WING_TIPS[fidx]
  # far wing + far legs
  _wing(s, shoulder, tips, membrane_far, deep, shade(membrane_far, 1.15), WING_SCALE[fidx] * 0.9, (7, -2))
  for lx in (50, 31):
    _line(s, deep, (lx, 36), (lx + 1, 43), 3)
    _ell(s, deep, lx - 3, 43, 8, 3)
  # tail
  tail = [(26, 31), (19, 35), (13, 38), (8, 40), (5, 38), (4, 34), (5, 31)]
  _path(s, sh, tail, [5, 4, 4, 3, 2, 2, 1])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 3, 3, 2, 1, 1, 1])
  for x, y in ((18, 33), (12, 36), (7, 36)):
    _poly(s, spine, [(x - 2, y), (x, y - 4), (x + 2, y)])
  _poly(s, spine, [(4, 33), (7, 29), (6, 34)])
  # torso
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, hi, 28, 23, 15, 3)
  _ell(s, b, 34, 33, 16, 8)
  for xx in (38, 42, 46):
    pygame.draw.line(s, shade(b, 0.74), (xx, 35), (xx, 39), 1)
  for sx_, sy_ in ((27, 27), (31, 25), (36, 27), (41, 26), (26, 31)):
    s.set_at((sx_, sy_), sh)
  for i in range(6):
    x = 26 + i * 4
    _poly(s, spine, [(x, 24 - (1 if i > 3 else 0)), (x + 2, 18 - (i % 2)), (x + 4, 24)])
  # hind + front near legs
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  _line(s, sh, (28, 38), (26, 45), 3)
  _ell(s, sh, 22, 45, 9, 3)
  for k in range(3):
    s.set_at((21 + k * 3, 48), CLAW)
    s.set_at((21 + k * 3, 47), CLAW)
  _line(s, sh, (42, 37), (45, 44), 3)
  _ell(s, sh, 42, 44, 8, 3)
  for k in range(3):
    s.set_at((47 + k * 2, 47), CLAW)
    s.set_at((47 + k * 2, 46), CLAW)
  if variant == 'time':
    pygame.draw.circle(s, (240, 210, 110), (41, 28), 5, 1)
    pygame.draw.circle(s, (15, 70, 95), (41, 28), 4)
    _line(s, (240, 210, 110), (41, 28), (41, 25), 1)
    _line(s, (240, 210, 110), (41, 28), (43, 29), 1)
  # near wing in front of the body
  _wing(s, shoulder, tips, membrane, bone, lite(membrane, 28), WING_SCALE[fidx], (0, 0))
  if variant == 'storm':
    sx, sy = shoulder
    t0 = tips[0]
    pts = [(sx + t0[0] * 0.8, sy + t0[1] * 0.8), (sx + t0[0] * 0.55 + 3, sy + t0[1] * 0.55 + 1), (sx + t0[0] * 0.5, sy + t0[1] * 0.5 + 4), (sx + t0[0] * 0.25, sy + t0[1] * 0.25 + 3)]
    for i in range(len(pts) - 1):
      _line(s, (255, 240, 120), pts[i], pts[i + 1], 1)
  _head_and_neck(s, pal, hd, fire, ring, variant, horn)
  return _finish(s, pal, False)


def draw_skeleton_px(pal, fidx, hd, fire, ring):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  bone, dk = pal['main'], pal['dark']
  sh = shade(bone, 0.7)
  soul = (30, 255, 90)
  hy = 17 + hd
  shoulder = (38, 24)
  tips = WING_TIPS[fidx]
  _wing(s, shoulder, tips, (46, 54, 48), sh, (70, 80, 72), 0.86, (7, -2))
  # near wing: tattered membrane and bone fingers
  sx, sy = shoulder
  t = [(sx + dx, sy + dy) for dx, dy in tips]
  mid1 = ((t[0][0] + t[1][0]) / 2.0, (t[0][1] + t[1][1]) / 2.0 + 5)
  mid2 = ((t[1][0] + t[2][0]) / 2.0, (t[1][1] + t[2][1]) / 2.0 + 5)
  _poly(s, (52, 60, 54), [(sx, sy), t[0], mid1, t[1], mid2, t[2]])
  for tp in t:
    _line(s, sh, (sx, sy), tp, 2)
    _line(s, bone, (sx, sy), tp, 1)
    pygame.draw.circle(s, bone, (int(tp[0]), int(tp[1])), 1)
  # tail + spine vertebrae
  pts = [(44, 27), (40, 24), (34, 24), (28, 25), (22, 28), (17, 32), (12, 36), (8, 39), (5, 37), (4, 33)]
  for i, (x, y) in enumerate(pts):
    r = 2 if i < 6 else 1
    pygame.draw.circle(s, sh, (x, y), r + 1)
    pygame.draw.circle(s, bone, (x, y), r)
  _poly(s, bone, [(5, 32), (3, 27), (7, 31)])
  # ribs
  for i in range(5):
    x = 26 + i * 4
    _line(s, sh, (x, 25), (x - 2, 31), 2)
    _line(s, sh, (x - 2, 31), (x - 4, 38 - i // 2), 2)
    _line(s, bone, (x, 25), (x - 2, 31), 1)
    _line(s, bone, (x - 2, 31), (x - 4, 38 - i // 2), 1)
  pr = 3 + (fidx % 2)
  pygame.draw.circle(s, (8, 90, 34), (33, 31), pr + 2)
  pygame.draw.circle(s, soul, (33, 31), pr)
  pygame.draw.circle(s, (220, 255, 230), (33, 31), 1)
  # legs (bones)
  for lx, fx in ((26, 22), (42, 46)):
    _line(s, sh, (lx, 33), (lx - 3, 40), 3)
    _line(s, sh, (lx - 3, 40), (fx, 46), 3)
    _line(s, bone, (lx, 33), (lx - 3, 40), 1)
    _line(s, bone, (lx - 3, 40), (fx, 46), 1)
    pygame.draw.circle(s, bone, (lx - 3, 40), 2)
    for k in range(3):
      s.set_at((fx - 2 + k * 2, 48), CLAW)
      s.set_at((fx - 2 + k * 2, 47), CLAW)
  # skull
  hx = 56
  pts2 = [(46, 28), (50, 24), (hx - 2, hy + 3)]
  for i, (x, y) in enumerate(pts2):
    pygame.draw.circle(s, sh, (x, y), 4)
    pygame.draw.circle(s, bone, (x, y), 3)
  _poly(s, bone, [(52, hy - 3), (55, hy - 3), (47, hy - 13), (46, hy - 11)])
  _poly(s, bone, [(56, hy - 3), (59, hy - 3), (54, hy - 12), (52, hy - 11)])
  _ell(s, sh, 50, hy - 5, 13, 11)
  _ell(s, bone, 50, hy - 6, 13, 10)
  _poly(s, bone, [(58, hy - 3), (67, hy - 1), (67, hy + 3), (58, hy + 4)])
  pygame.draw.rect(s, (12, 12, 12), (55, hy - 3, 5, 4))
  pygame.draw.rect(s, pal['eye'], (57, hy - 2, 2, 2))
  jaw_y = hy + 7 if fire else hy + 4
  _poly(s, sh, [(57, hy + 3), (67, jaw_y), (66, jaw_y + 2), (56, hy + 6)])
  for k in range(4):
    s.set_at((59 + k * 2, hy + 3), CLAW)
    s.set_at((59 + k * 2, jaw_y - 1 + (k // 2)), CLAW)
  if fire:
    _poly(s, soul, [(60, hy + 4), (66, hy + 5), (63, hy + 7)])
    for k in range(3):
      pygame.draw.circle(s, ring, (68 + k * 2, hy + 3 + k * 2 - (k % 2) * 4), 1)
  return _finish(s, pal, False)


def draw_serpent_px(pal, fidx, fire, ring):
  """The Celestial dragon: a long, coiling Eastern dragon with a gold mane, whiskers and antlers."""
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh = shade(m, 0.7)
  gold, orange = (244, 204, 70), (255, 140, 40)
  ph = fidx * math.pi / 2
  pts, rad = [], []
  for i in range(34):
    t = i / 33.0
    pts.append((6 + t * 52, 31 + math.sin(ph + t * 7.0) * 5 * (0.55 + 0.45 * (1 - t))))
    rad.append(2.2 + 4.2 * t ** 0.9)
  tx, ty = pts[0]
  for k, c in ((0, orange), (1, gold)):
    _poly(s, c, [(tx + 2, ty), (tx - 8 + k * 3, ty - 6 + k * 2), (tx - 4 + k * 2, ty), (tx - 8 + k * 3, ty + 6 - k * 2)])
  _path(s, shade(m, 0.55), pts, [r + 1 for r in rad])
  _path(s, sh, pts, rad)
  _path(s, m, [(x, y - 1) for x, y in pts], [max(1, r - 1.3) for r in rad])
  for i in range(2, 34, 2):
    x, y = pts[i]
    pygame.draw.circle(s, b, (int(x + 1), int(y + rad[i] * 0.55)), max(1, int(rad[i] * 0.4)))
  for i in range(33, 1, -3):
    x, y = pts[i]
    r = rad[i]
    _poly(s, orange, [(x - 3, y - r + 1), (x, y - r - 5), (x + 2, y - r + 1)])
    _poly(s, gold, [(x - 1, y - r + 1), (x, y - r - 2), (x + 1, y - r + 1)])
  for i in (11, 22):
    x, y = pts[i]
    r = rad[i]
    _line(s, m, (x - 1, y + r - 1), (x - 4, y + r + 6), 2)
    for k in range(3):
      s.set_at((int(x - 7 + k * 2), int(y + r + 7)), CLAW)
  hx, hy = int(pts[-1][0]) + 3, int(pts[-1][1]) - 3
  for sgn in (0, 1):
    wp = [(hx + 12, hy + 7 + sgn * 2)]
    for k in range(1, 5):
      wp.append((hx + 12 + k * 4, int(hy + 7 + sgn * 2 + k * 2 + math.sin(ph * 2 + k + sgn) * 3)))
    pygame.draw.lines(s, gold, False, wp, 1)
  _line(s, gold, (hx + 2, hy - 2), (hx - 3, hy - 11), 2)
  _line(s, gold, (hx - 3, hy - 11), (hx - 7, hy - 14), 1)
  _line(s, gold, (hx, hy - 6), (hx + 5, hy - 11), 1)
  _poly(s, gold, [(hx + 6, hy + 11), (hx + 9, hy + 17), (hx + 12, hy + 11)])
  _ell(s, sh, hx - 1, hy - 3, 16, 12)
  _ell(s, m, hx, hy - 3, 15, 11)
  _poly(s, m, [(hx + 9, hy), (hx + 19, hy + 1), (hx + 19, hy + 7), (hx + 9, hy + 8)])
  _poly(s, b, [(hx + 8, hy + 7), (hx + 19, hy + 7), (hx + 16, hy + 12), (hx + 9, hy + 11)] if not fire else [(hx + 8, hy + 8), (hx + 19, hy + 11), (hx + 16, hy + 14), (hx + 8, hy + 11)])
  for k in range(3):
    s.set_at((hx + 11 + k * 3, hy + 7), CLAW)
  pygame.draw.rect(s, (12, 12, 12), (hx + 6, hy + 1, 4, 3))
  pygame.draw.rect(s, pal['eye'], (hx + 7, hy + 1, 2, 2))
  pygame.draw.circle(s, (255, 220, 100), (hx + 28, hy - 2), 3)
  pygame.draw.circle(s, (215, 250, 255), (hx + 28, hy - 2), 1)
  if fire:
    for k in range(3):
      pygame.draw.circle(s, ring, (hx + 22 + k * 2, hy + 3 + k * 2 - (k % 2) * 4), 1)
  return _finish(s, pal, False)

MAGMA_PAL = {'main': (62, 48, 54), 'dark': (26, 18, 22), 'belly': (255, 150, 40), 'eye': (255, 235, 70)}
GLOW, GLOW2, GLOW3 = (255, 176, 44), (255, 96, 20), (255, 236, 110)


def _magma_wing(s, shoulder, tips, scale=1.0, off=(0, 0), dim=False):
  sx, sy = shoulder[0] + off[0], shoulder[1] + off[1]
  t = [(sx + dx * scale, sy + dy * scale) for dx, dy in tips]
  elbow = ((sx + t[0][0]) / 2.0, (sy + t[0][1]) / 2.0 - 3)

  def scallop(a, b):
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    return (mx + (sx - mx) * 0.2, my + (sy - my) * 0.2)

  mem = (92, 34, 24) if not dim else (58, 24, 22)
  edge = [t[0], scallop(t[0], t[1]), t[1], scallop(t[1], t[2]), t[2]]
  _poly(s, mem, [(sx, sy), elbow] + edge)
  if not dim:
    for tp in t:                                   # glowing veins
      _line(s, GLOW2, (sx, sy), ((sx + tp[0]) / 2.0, (sy + tp[1]) / 2.0), 1)
      _line(s, GLOW, ((sx + tp[0]) / 2.0, (sy + tp[1]) / 2.0), ((sx * 0.3 + tp[0] * 0.7), (sy * 0.3 + tp[1] * 0.7)), 1)
    for i in range(len(edge) - 1):                 # molten trailing edge
      _line(s, GLOW2, (int(edge[i][0]), int(edge[i][1])), (int(edge[i + 1][0]), int(edge[i + 1][1])), 1)
  bone = (36, 26, 30)
  _line(s, bone, (sx, sy), elbow, 2)
  _line(s, bone, elbow, t[0], 2)
  _line(s, bone, (sx, sy), t[1], 1)
  _line(s, bone, (sx, sy), t[2], 1)
  _poly(s, GLOW3 if not dim else bone, [(t[0][0], t[0][1]), (t[0][0] - 2, t[0][1] + 3), (t[0][0] + 2, t[0][1] + 2)])


MAGMA_LEG = {2: 0, 3: 1, 1: 3, 0: 5}
MAGMA_TAIL = {2: 4, 3: 2, 1: -1, 0: -4}


def draw_magma_px(fidx, hd, fire, ring=GLOW2, beat=0):
  """beat (0/1) makes the lava cracks pulse."""
  pal = MAGMA_PAL
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh, deep, hi = shade(m, 0.72), shade(d, 0.7), lite(m, 30)
  hot = GLOW if beat else GLOW2
  tips = WING_TIPS[fidx]
  shoulder = (38, 24)
  _magma_wing(s, shoulder, tips, 0.9, (7, -2), dim=True)
  lf = MAGMA_LEG[fidx]
  sway = MAGMA_TAIL[fidx]
  for lx in (50, 31):
    fy = 43 - lf
    fx = lx + 1 - lf // 2
    _line(s, deep, (lx, 36), (fx, fy), 3)
    _ell(s, deep, fx - 4, fy, 8, 3)
  tail0 = [(26, 31), (19, 35), (13, 38), (8, 40), (5, 38), (4, 34), (5, 31)]
  tail = [(x, y + int(round(sway * (i / 6.0) ** 1.3))) for i, (x, y) in enumerate(tail0)]
  tdy = tail[6][1] - tail0[6][1]
  _path(s, sh, tail, [5, 4, 4, 3, 2, 2, 1])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 3, 3, 2, 1, 1, 1])
  for ti, off in ((1, -2), (2, -2), (3, -4)):
    x, y = tail[ti][0] - 1, tail[ti][1] + off
    _poly(s, GLOW2, [(x - 2, y), (x, y - 4), (x + 2, y)])
  for k, (fx, fy) in enumerate(((5, 31 + tdy), (3, 27 + tdy), (7, 26 + tdy))):    # flame tuft on the tail tip
    _poly(s, GLOW2, [(fx - 2, fy + 3), (fx, fy - 5 - (beat + k) % 2), (fx + 2, fy + 3)])
    _poly(s, GLOW3, [(fx - 1, fy + 3), (fx, fy - 2), (fx + 1, fy + 3)])
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, hi, 28, 23, 15, 2)
  _ell(s, b, 34, 33, 16, 8)
  for xx in (38, 42, 46):
    pygame.draw.line(s, GLOW2, (xx, 35), (xx, 39), 1)
  for pts in (((26, 26), (30, 29), (29, 33), (34, 35)), ((38, 24), (41, 28), (46, 27), (48, 31)), ((14, 35), (19, 36), (23, 34)), ((44, 37), (46, 41))):
    for i in range(len(pts) - 1):
      _line(s, hot, pts[i], pts[i + 1], 2)
      _line(s, GLOW3, pts[i], pts[i + 1], 1)
  for i in range(7):                                         # flame mane along the back
    x = 25 + i * 3.5
    h = 7 + ((i + beat) % 3)
    _poly(s, GLOW2, [(x - 2, 24), (x + 1, 24 - h), (x + 4, 24)])
    _poly(s, GLOW, [(x - 1, 24), (x + 1, 24 - h + 3), (x + 3, 24)])
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  hx0, hy0 = 26 - lf // 2, 45 - lf
  _line(s, sh, (28, 38), (hx0, hy0), 3)
  _ell(s, sh, hx0 - 4, hy0, 9, 3)
  for k in range(3):
    s.set_at((hx0 - 5 + k * 3, hy0 + 3), GLOW)
    s.set_at((hx0 - 5 + k * 3, hy0 + 2), GLOW)
  fx0, fy0 = 45 - lf // 2, 44 - (lf * 3) // 4
  _line(s, sh, (42, 37), (fx0, fy0), 3)
  _ell(s, sh, fx0 - 3, fy0, 8, 3)
  for k in range(3):
    s.set_at((fx0 + 2 + k * 2, fy0 + 3), GLOW)
    s.set_at((fx0 + 2 + k * 2, fy0 + 2), GLOW)
  _magma_wing(s, shoulder, tips, 1.0)
  _head_and_neck(s, pal, hd, fire, GLOW, None, (230, 110, 40))
  hy = 17 + hd
  if fire:                                                    # molten throat + dripping lava
    pygame.draw.rect(s, GLOW3, (61, hy + 4, 5, 2))
    for dx in (60, 64, 67):
      s.set_at((dx, hy + 11 + (dx % 2)), GLOW)
  else:
    s.set_at((61, hy + 4), GLOW)
  return _finish(s, pal, False)


CRYS_L, CRYS_M, CRYS_D = (210, 248, 255), (150, 226, 246), (66, 140, 190)


def draw_crystal_px(pal, fidx, hd, fire, ring=CRYS_M, beat=0):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh, deep, hi = shade(m, 0.72), shade(d, 0.7), lite(m, 30)
  tips = WING_TIPS[fidx]
  shoulder = (38, 24)
  _wing(s, shoulder, tips, (96, 160, 196), deep, (150, 210, 235), 0.9, (7, -2))
  lf = MAGMA_LEG[fidx]
  sway = MAGMA_TAIL[fidx]
  for lx in (50, 31):
    fy = 43 - lf
    fx = lx + 1 - lf // 2
    _line(s, deep, (lx, 36), (fx, fy), 3)
    _ell(s, deep, fx - 4, fy, 8, 3)
  tail0 = [(26, 31), (19, 35), (13, 37), (9, 38)]
  tail = [(x, y + int(round(sway * (i / 3.0) ** 1.3))) for i, (x, y) in enumerate(tail0)]
  _path(s, sh, tail, [5, 4, 4, 3])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 3, 3, 2])
  for ti in (1, 2):
    x, y = tail[ti][0], tail[ti][1] - 2
    _poly(s, CRYS_D, [(x - 2, y), (x, y - 5), (x + 2, y)])
    _poly(s, CRYS_L, [(x - 1, y), (x, y - 4), (x + 2, y)])
  ex, ey = tail[3]
  for dx, dy, h, col in ((0, 0, 12, CRYS_L), (-4, -2, 9, CRYS_M), (3, -4, 8, CRYS_D), (-7, 3, 7, CRYS_M)):
    _poly(s, CRYS_D, [(ex + dx - 3, ey + dy), (ex + dx, ey + dy - h), (ex + dx + 3, ey + dy)])
    _poly(s, col, [(ex + dx - 1, ey + dy), (ex + dx, ey + dy - h + 2), (ex + dx + 3, ey + dy)])
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, b, 34, 33, 16, 8)
  for tri, col in (([(22, 24), (32, 18), (34, 29)], CRYS_L), ([(34, 29), (32, 18), (46, 23)], CRYS_M), ([(22, 24), (34, 29), (26, 34)], CRYS_D), ([(34, 29), (46, 23), (44, 34)], CRYS_D), ([(26, 34), (34, 29), (44, 34)], CRYS_M)):
    _poly(s, col, tri)
  for i in range(6):
    x, h = 24 + i * 4, 8 + (i % 2) * 3 + (beat + i) % 2
    _poly(s, CRYS_D, [(x, 24), (x + 2, 24 - h), (x + 4, 24)])
    _poly(s, CRYS_L, [(x + 2, 24), (x + 2, 24 - h), (x + 4, 24)])
  for px, py in ((28, 27), (36, 31), (41, 27)):
    s.set_at((px, py + beat), (255, 255, 255))
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  hx0, hy0 = 26 - lf // 2, 45 - lf
  _line(s, sh, (28, 38), (hx0, hy0), 3)
  _ell(s, sh, hx0 - 4, hy0, 9, 3)
  for k in range(3):
    s.set_at((hx0 - 5 + k * 3, hy0 + 3), CLAW)
    s.set_at((hx0 - 5 + k * 3, hy0 + 2), CLAW)
  fx0, fy0 = 45 - lf // 2, 44 - (lf * 3) // 4
  _line(s, sh, (42, 37), (fx0, fy0), 3)
  _ell(s, sh, fx0 - 3, fy0, 8, 3)
  for k in range(3):
    s.set_at((fx0 + 2 + k * 2, fy0 + 3), CLAW)
    s.set_at((fx0 + 2 + k * 2, fy0 + 2), CLAW)
  _wing(s, shoulder, tips, (160, 230, 248), (60, 128, 180), (255, 255, 255), 1.0)
  for tp in tips:
    _line(s, (235, 252, 255), (38 + tp[0] * 0.3, 24 + tp[1] * 0.3), (38 + tp[0] * 0.9, 24 + tp[1] * 0.9), 1)
  _head_and_neck(s, pal, hd, fire, ring, None, (215, 250, 255))
  hy = 17 + hd
  if fire:
    pygame.draw.rect(s, (235, 252, 255), (61, hy + 4, 5, 2))
  return _finish(s, pal, False)


DART_ORG, DART_YEL, DART_ORG_D = (255, 142, 34), (255, 230, 90), (214, 100, 24)
DART_TEAL_L, DART_LIME = (110, 236, 196), (176, 240, 70)


def _drips(s, pts, beat=0):
  for x, y, ln in pts:
    ln += beat
    _line(s, DART_LIME, (x, y), (x, y + ln), 1)
    s.set_at((x, y + ln + 1), DART_LIME)
    s.set_at((x, y + ln + 2), (250, 255, 200))


def draw_dart_px(pal, fidx, hd, fire, ring=DART_LIME, beat=0):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh, deep, hi = shade(m, 0.72), shade(d, 0.7), lite(m, 30)
  tips = WING_TIPS[fidx]
  shoulder = (38, 24)
  mem, mem_far = (255, 170, 50), (214, 120, 40)
  _wing(s, shoulder, tips, mem_far, deep, mem_far, 0.9, (7, -2))
  lf, sway = MAGMA_LEG[fidx], MAGMA_TAIL[fidx]
  for lx in (50, 31):
    fy, fx = 43 - lf, lx + 1 - lf // 2
    _line(s, deep, (lx, 36), (fx, fy), 3)
    _ell(s, deep, fx - 4, fy, 8, 3)
  tail0 = [(26, 31), (19, 35), (13, 37), (8, 36), (4, 33)]
  tail = [(x, y + int(round(sway * (i / 4.0) ** 1.3))) for i, (x, y) in enumerate(tail0)]
  _path(s, sh, tail, [5, 4, 4, 3, 2])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 3, 3, 2, 1])
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, hi, 28, 23, 15, 2)
  _ell(s, b, 34, 33, 16, 8)
  for xx in (38, 42, 46):
    pygame.draw.line(s, shade(b, 0.74), (xx, 35), (xx, 39), 1)
  for i in range(6):
    x, h = 24 + i * 4, 6 + (i % 2) * 2 + (beat + i) % 2
    _poly(s, DART_ORG_D, [(x, 24), (x + 2, 24 - h), (x + 4, 24)])
    _poly(s, DART_ORG, [(x + 1, 24), (x + 2, 24 - h + 2), (x + 4, 24)])
    s.set_at((x + 2, 24 - h + 3), DART_YEL)
  for x, y, r in ((28, 27, 2), (35, 26, 2), (41, 28, 2), (32, 31, 1), (46, 31, 1), (25, 32, 1)):
    pygame.draw.circle(s, DART_ORG, (x, y), r)
    s.set_at((x, y - (1 if r > 1 else 0)), DART_YEL)
  for x, y in tail[1:]:
    s.set_at((x, y - 2), DART_YEL)
    s.set_at((x + 1, y - 1), DART_ORG)
  for k in range(3):
    _line(s, DART_TEAL_L, (30 + k * 5, 23), (31 + k * 5, 27), 1)
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  hx0, hy0 = 26 - lf // 2, 45 - lf
  _line(s, sh, (28, 38), (hx0, hy0), 3)
  _ell(s, sh, hx0 - 4, hy0, 9, 3)
  fx0, fy0 = 45 - lf // 2, 44 - (lf * 3) // 4
  _line(s, sh, (42, 37), (fx0, fy0), 3)
  _ell(s, sh, fx0 - 3, fy0, 8, 3)
  for k in range(3):
    for bx, by in ((hx0 - 5, hy0 + 3), (fx0 + 2, fy0 + 3)):
      s.set_at((bx + k * 3, by), (255, 244, 170))
      s.set_at((bx + k * 3, by - 1), (255, 244, 170))
  _wing(s, shoulder, tips, mem, (22, 110, 104), DART_YEL, 1.0)
  for tp in tips:
    for a in (0.45, 0.75):
      x, y = int(38 + tp[0] * a), int(24 + tp[1] * a)
      pygame.draw.circle(s, DART_YEL, (x, y), 1)
      s.set_at((x - 1, y - 1), (255, 250, 200))
  _drips(s, ((30, 38, 4), (43, 39, 5)), beat)
  for k in range(3):
    s.set_at((26 + k * 3, 33), DART_TEAL_L)
  _head_and_neck(s, pal, hd, fire, ring, None, DART_YEL)
  if fire:
    hy = 17 + hd
    pygame.draw.rect(s, (230, 255, 130), (61, hy + 4, 5, 2))
    for dx in (60, 63, 66):
      s.set_at((dx, hy + 12 + (dx % 2)), DART_LIME)
  return _finish(s, pal, False)


VOLT_WH, VOLT_CY = (255, 255, 240), (120, 220, 255)


def _bolt(s, pts, col, core):
  for a, b in zip(pts, pts[1:]):
    _line(s, col, a, b, 2)
  for a, b in zip(pts, pts[1:]):
    _line(s, core, a, b, 1)


def draw_volt_px(pal, fidx, hd, fire, ring=VOLT_CY, beat=0):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, d, b = pal['main'], pal['dark'], pal['belly']
  sh, deep, hi = shade(m, 0.72), shade(d, 0.7), lite(m, 30)
  tips = WING_TIPS[fidx]
  shoulder = (38, 24)
  _wing(s, shoulder, tips, (214, 168, 48), deep, (214, 168, 48), 0.9, (7, -2))
  lf, sway = MAGMA_LEG[fidx], MAGMA_TAIL[fidx]
  for lx in (50, 31):
    fy, fx = 43 - lf, lx + 1 - lf // 2
    _line(s, deep, (lx, 36), (fx, fy), 3)
    _ell(s, deep, fx - 4, fy, 8, 3)
  tail0 = [(26, 31), (19, 35), (13, 37), (8, 36), (3, 32)]
  tail = [(x, y + int(round(sway * (i / 4.0) ** 1.3))) for i, (x, y) in enumerate(tail0)]
  _path(s, sh, tail, [5, 4, 4, 3, 2])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 3, 3, 2, 1])
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, hi, 28, 23, 15, 2)
  _ell(s, b, 34, 33, 16, 8)
  for xx in (38, 42, 46):
    pygame.draw.line(s, shade(b, 0.74), (xx, 35), (xx, 39), 1)
  for i in range(6):
    x, h = 24 + i * 4, 8 + (i % 2) * 3
    j = 1 if (beat + i) % 2 else 0
    _bolt(s, [(x, 24), (x + 3 - j, 24 - h // 2), (x + 1 + j, 24 - h // 2 - 1), (x + 4, 24 - h)], VOLT_CY, VOLT_WH)
  for pts in (((22, 30), (27, 28), (25, 32), (31, 31)), ((36, 26), (40, 30), (38, 30), (44, 33))):
    _bolt(s, pts, (255, 255, 255), (220, 245, 255))
  for x, y in tail[1:4]:
    _bolt(s, [(x, y - 2), (x + 2, y - 5), (x, y - 5), (x + 3, y - 8)], VOLT_CY, VOLT_WH)
  ex, ey = tail[-1]
  _poly(s, VOLT_CY, [(ex + 2, ey - 2), (ex - 3, ey - 3), (ex - 1, ey), (ex - 6, ey + 1), (ex - 2, ey + 3), (ex + 1, ey + 2)])
  _poly(s, VOLT_WH, [(ex + 1, ey - 1), (ex - 2, ey - 2), (ex - 1, ey), (ex - 4, ey + 1), (ex, ey + 1)])
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  hx0, hy0 = 26 - lf // 2, 45 - lf
  _line(s, sh, (28, 38), (hx0, hy0), 3)
  _ell(s, sh, hx0 - 4, hy0, 9, 3)
  fx0, fy0 = 45 - lf // 2, 44 - (lf * 3) // 4
  _line(s, sh, (42, 37), (fx0, fy0), 3)
  _ell(s, sh, fx0 - 3, fy0, 8, 3)
  for k in range(3):
    for bx, by in ((hx0 - 5, hy0 + 3), (fx0 + 2, fy0 + 3)):
      s.set_at((bx + k * 3, by), VOLT_WH)
      s.set_at((bx + k * 3, by - 1), VOLT_WH)
  _wing(s, shoulder, tips, (255, 232, 116), (176, 118, 30), VOLT_WH, 1.0)
  for tp in tips:
    a = (38 + tp[0] * 0.25, 24 + tp[1] * 0.25)
    _bolt(s, [a, (a[0] + tp[0] * 0.2, a[1] + tp[1] * 0.2 + 2), (a[0] + tp[0] * 0.3, a[1] + tp[1] * 0.3 - 1), (a[0] + tp[0] * 0.5, a[1] + tp[1] * 0.5 + 1)], VOLT_WH, VOLT_WH)
  for k in range(3):
    s.set_at((30 + k * 5, 33), VOLT_WH)
  _head_and_neck(s, pal, hd, fire, ring, None, VOLT_WH)
  if fire:
    hy = 17 + hd
    pygame.draw.rect(s, VOLT_WH, (61, hy + 4, 5, 2))
    for dx in (60, 63, 66):
      s.set_at((dx, hy + 12 + (dx % 2)), VOLT_CY)
  return _finish(s, pal, False)


OWL_CREAM, OWL_MAIN, OWL_LIGHT, OWL_DARK, OWL_EDGE = (238, 228, 214), (152, 140, 170), (180, 168, 200), (98, 86, 122), (58, 50, 78)


def _feather(s, x, y, ang, L, col, edge, w):
  ca, sa = math.cos(ang), math.sin(ang)

  def P(t, side):
    return (x + ca * L * t - sa * w * side, y + sa * L * t + ca * w * side)
  _poly(s, edge, [P(0, 0.35), P(0.35, 1.0), P(0.75, 0.95), P(0.97, 0.55), P(1.03, 0), P(0.97, -0.55), P(0.75, -0.95), P(0.35, -1.0)])
  _poly(s, col, [P(0.05, 0.2), P(0.36, 0.62), P(0.74, 0.62), P(0.93, 0.3), P(0.97, 0), P(0.93, -0.3), P(0.74, -0.62), P(0.36, -0.62), P(0.05, -0.2)])
  _line(s, edge, P(0.05, 0), P(0.92, 0), 1)


def _owl_wing(s, tips, far):
  ox, oy = (7, -2) if far else (0, 0)
  S = (38 + ox, 24 + oy)
  T = [(S[0] + t[0], S[1] + t[1]) for t in tips]
  Wr = (S[0] + tips[0][0] * 0.5, S[1] + tips[0][1] * 0.5 - 3)

  def c(col):
    return tuple(int(v * 0.72) for v in col) if far else col
  path = [T[0], T[1], T[2], (S[0] + tips[2][0] * 0.35, S[1] + tips[2][1] * 0.35 + 2)]

  def along(u):
    seg = u * (len(path) - 1)
    i = min(len(path) - 2, int(seg))
    f = seg - i
    return (path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f)
  _poly(s, c(OWL_EDGE), [S, Wr, T[0], T[1], T[2]])
  for i in range(8):
    p = along(i / 7.0 * 0.98)
    base = (S[0] + (p[0] - S[0]) * 0.5, S[1] + (p[1] - S[1]) * 0.5)
    ang = math.atan2(p[1] - S[1], p[0] - S[0])
    L = math.hypot(p[0] - base[0], p[1] - base[1]) + 2
    _feather(s, base[0], base[1], ang, L, c(OWL_DARK) if i < 4 else c(OWL_MAIN), c(OWL_EDGE), 3.4)
  _poly(s, c(OWL_LIGHT), [S, Wr, ((Wr[0] + T[1][0]) / 2.0, (Wr[1] + T[1][1]) / 2.0), ((S[0] + T[2][0]) / 2.0, (S[1] + T[2][1]) / 2.0)])
  _line(s, c(OWL_EDGE), S, Wr, 2)


def draw_owl_px(pal, fidx, hd, fire, ring=(206, 190, 240), beat=0):
  s = pygame.Surface((CW, CH), pygame.SRCALPHA)
  m, b = pal['main'], pal['belly']
  sh, deep, hi = shade(m, 0.72), shade(pal['dark'], 0.7), lite(m, 30)
  tips = WING_TIPS[fidx]
  _owl_wing(s, tips, True)
  lf, sway = MAGMA_LEG[fidx], MAGMA_TAIL[fidx]
  for lx in (50, 31):
    fy, fx = 43 - lf, lx + 1 - lf // 2
    _line(s, deep, (lx, 36), (fx, fy), 3)
    _ell(s, deep, fx - 4, fy, 8, 3)
  tail0 = [(26, 31), (19, 35), (13, 37), (8, 36)]
  tail = [(x, y + int(round(sway * (i / 3.0) ** 1.3))) for i, (x, y) in enumerate(tail0)]
  _path(s, sh, tail, [5, 5, 4, 3])
  _path(s, m, [(x, y - 1) for x, y in tail], [4, 4, 3, 2])
  _ell(s, deep, 21, 21, 31, 21)
  _ell(s, sh, 22, 22, 29, 19)
  _ell(s, m, 23, 22, 27, 14)
  _ell(s, hi, 28, 23, 15, 2)
  _ell(s, b, 34, 33, 16, 8)
  for r in range(4):
    for cc in range(7):
      x, y = 25 + cc * 4.2 + (r % 2) * 2, 24.5 + r * 3.6
      if ((x - 37) / 15.0) ** 2 + ((y - 30) / 9.5) ** 2 < 0.95:
        col = OWL_DARK if y < 33 else (176, 164, 150)
        _line(s, col, (x - 2, y), (x, y + 2), 1)
        _line(s, col, (x, y + 2), (x + 2, y), 1)
  e = tail[-1]
  for k in range(4):
    _feather(s, e[0] + 2, e[1], math.pi - 0.6 + k * 0.4, 13 - abs(k - 1.5) * 1.6, OWL_LIGHT if k % 2 else OWL_MAIN, OWL_EDGE, 2.8)
  _ell(s, sh, 23, 31, 11, 10)
  _ell(s, m, 24, 31, 9, 8)
  hx0, hy0 = 26 - lf // 2, 45 - lf
  _line(s, sh, (28, 38), (hx0, hy0), 3)
  _ell(s, sh, hx0 - 4, hy0, 9, 3)
  fx0, fy0 = 45 - lf // 2, 44 - (lf * 3) // 4
  _line(s, sh, (42, 37), (fx0, fy0), 3)
  _ell(s, sh, fx0 - 3, fy0, 8, 3)
  for k in range(3):
    for bx, by in ((hx0 - 5, hy0 + 3), (fx0 + 2, fy0 + 3)):
      s.set_at((bx + k * 3, by), OWL_CREAM)
      s.set_at((bx + k * 3, by - 1), OWL_CREAM)
  _owl_wing(s, tips, False)
  for (x, y) in ((27, 36), (44, 37)):
    for k in range(2):
      _feather(s, x + k * 3 - 1, y, 1.5, 6, OWL_CREAM if k else OWL_LIGHT, (160, 148, 138), 2.0)
  _head_and_neck(s, pal, hd, fire, ring, None, (206, 196, 222))
  for i, (x, y) in enumerate(((46, 27), (49, 25), (52, 23), (54, 21))):
    _feather(s, x, y + hd, 2.65, 6, OWL_CREAM if i % 2 else OWL_LIGHT, OWL_EDGE, 2.2)
  for d_ in (0, 5):
    _feather(s, 57 + d_, 15 + hd, -1.75 - d_ * 0.05, 10, OWL_LIGHT, OWL_EDGE, 2.4)
  if fire:
    hy = 17 + hd
    pygame.draw.rect(s, (250, 253, 255), (61, hy + 4, 5, 2))
    for dx in (60, 63, 66):
      s.set_at((dx, hy + 12 + (dx % 2)), ring)
  return _finish(s, pal, False)
