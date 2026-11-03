"""Ultimate attack animations: one full-screen show for every dragon's Ultimate.
draw(gs, game, fx) is called every frame while fx['t'] runs from 0 to LIFE; everything is drawn in code."""
import math
import random
import pygame
from fd_core import WIDTH, HEIGHT, GROUND_Y, add_glow

LIFE = 100                      # frames the show lasts


def _parts(fx, n, make):
  """particles made once per Ultimate (seeded, so they don't jump between frames)"""
  p = fx.get('parts')
  if p is None:
    rnd = random.Random(fx.get('seed', 1))
    p = fx['parts'] = [make(rnd, i) for i in range(n)]
  return p


def _fade(t, a=8, b=LIFE - 20):
  """0..1 envelope: fades in over a frames, holds, fades out after b"""
  if t < a:
    return t / float(a)
  if t > b:
    return max(0.0, (LIFE - t) / float(LIFE - b))
  return 1.0


def _tint(gs, col, k):
  if k > 0:
    gs.fill(tuple(int(c * k) for c in col), special_flags=pygame.BLEND_RGB_SUB)


def _add(gs, col, k):
  if k > 0:
    gs.fill(tuple(int(c * k) for c in col), special_flags=pygame.BLEND_RGB_ADD)


def _bolt(gs, x, rnd, y0=0, y1=GROUND_Y, col=(200, 210, 255)):
  pts, y, bx = [], y0, x
  while y < y1:
    pts.append((bx, y))
    bx += rnd.randint(-26, 26)
    y += rnd.randint(28, 56)
  pts.append((bx, y1))
  pygame.draw.lines(gs, col, False, pts, 7)
  pygame.draw.lines(gs, (255, 255, 255), False, pts, 3)
  return bx


def _boom(gs, x, y, u, col=(255, 150, 40), size=60):
  """an explosion u = 0..1 through its life"""
  if not 0 <= u <= 1:
    return
  r = int(8 + size * math.sqrt(u))
  add_glow(gs, int(x), int(y), int(r * 1.6), tuple(int(c * 0.45 * (1 - u)) for c in col))
  if u < 0.7:
    pygame.draw.circle(gs, (255, 240, 180), (int(x), int(y)), max(2, int(r * 0.55 * (1 - u))))
  pygame.draw.circle(gs, col, (int(x), int(y)), r, max(1, int(5 * (1 - u))))


# ---------------------------------------------------------------- the shows
def meteor_storm(gs, g, fx, t):                          # RED: flaming meteors rain down and burst on the ground
  _tint(gs, (10, 40, 60), 0.6 * _fade(t))
  ps = _parts(fx, 22, lambda r, i: (r.uniform(100, WIDTH + 300), r.randint(0, 60), r.uniform(15, 22), r.randint(10, 22)))
  for x0, d0, sp, rad in ps:
    k = t - d0
    if k < 0:
      continue
    x, y = x0 - k * sp * 0.55, -40 + k * sp
    if y < GROUND_Y - 10:
      for j in range(6):                                 # fire trail
        pygame.draw.circle(gs, (255, 120 + j * 20, 30), (int(x + j * 6), int(y - j * 11)), max(2, rad - j * 3))
      add_glow(gs, int(x), int(y), rad * 3, (90, 40, 6))
      pygame.draw.circle(gs, (90, 40, 24), (int(x), int(y)), rad)
      pygame.draw.circle(gs, (255, 200, 90), (int(x - 2), int(y - 2)), rad // 2)
    else:
      u = (k - (GROUND_Y - 10 + 40) / sp) / 18.0
      _boom(gs, x, GROUND_Y - 8, u, (255, 130, 30), 70)


def blizzard(gs, g, fx, t):                              # BLUE: a white-out of driving snow and falling ice spears
  f = _fade(t)
  _add(gs, (90, 110, 140), 0.9 * f)
  ps = _parts(fx, 150, lambda r, i: (r.uniform(0, WIDTH), r.uniform(0, HEIGHT), r.uniform(0.6, 1.4)))
  for x0, y0, s in ps:
    x = (x0 - t * 26 * s) % (WIDTH + 60) - 30
    y = (y0 + t * 9 * s) % HEIGHT
    pygame.draw.line(gs, (245, 250, 255), (int(x), int(y)), (int(x + 30 * s), int(y - 9 * s)), 3 if s > 1.1 else 2)
  sh = _parts_b(fx, 'ice', 18, lambda r, i: (r.uniform(80, WIDTH - 40), r.randint(5, 55)))
  for x, d0 in sh:
    k = t - d0
    if 0 <= k:
      y = min(GROUND_Y - 30, -60 + k * 24)
      pts = [(x, y + 70), (x - 14, y), (x, y - 20), (x + 14, y)]
      pygame.draw.polygon(gs, (170, 225, 255), pts)
      pygame.draw.polygon(gs, (255, 255, 255), pts, 2)
      if y >= GROUND_Y - 30:
        _boom(gs, x, GROUND_Y - 6, (k - (GROUND_Y + 30) / 24.0) / 14.0, (200, 240, 255), 40)
  if t < 10:
    _add(gs, (120, 140, 160), (10 - t) / 10.0)


def _parts_b(fx, key, n, make):
  p = fx.get(key)
  if p is None:
    rnd = random.Random(fx.get('seed', 1) * 7 + len(key))
    p = fx[key] = [make(rnd, i) for i in range(n)]
  return p


def acid_rain(gs, g, fx, t):                             # GREEN / ALIEN-ish: a sickly sky and sizzling green rain
  f = _fade(t)
  _tint(gs, (60, 10, 60), 0.6 * f)
  for k in range(7):                                     # boiling green cloud bank
    cx = (k * 230 + t * 3) % (WIDTH + 200) - 100
    pygame.draw.ellipse(gs, (60, 110, 40), (cx - 120, -50, 260, 110))
    pygame.draw.ellipse(gs, (90, 150, 50), (cx - 90, -40, 200, 80))
  ps = _parts(fx, 110, lambda r, i: (r.uniform(0, WIDTH), r.uniform(0, GROUND_Y), r.uniform(0.8, 1.3)))
  for x0, y0, s in ps:
    y = (y0 + t * 20 * s) % GROUND_Y
    x = x0 - y * 0.15
    pygame.draw.line(gs, (150, 255, 90), (int(x), int(y)), (int(x - 3), int(y + 13)), 2)
    if y > GROUND_Y - 22:
      pygame.draw.ellipse(gs, (170, 255, 110), (int(x) - 7, GROUND_Y - 6, 14, 5), 1)


def abduction(gs, g, fx, t):                             # ALIEN: flying saucers sweep their tractor beams over the land
  f = _fade(t)
  _tint(gs, (40, 20, 40), 0.7 * f)
  for k in range(3):
    cx = int(-160 + ((t * 9 + k * 470) % (WIDTH + 320)))
    cy = 70 + k * 20
    beam = pygame.Surface((180, GROUND_Y - cy), pygame.SRCALPHA)
    pygame.draw.polygon(beam, (140, 255, 120, int(90 * f)), [(70, 0), (110, 0), (180, GROUND_Y - cy), (0, GROUND_Y - cy)])
    gs.blit(beam, (cx - 90, cy + 10))
    for j in range(5):                                   # rings rising up the beam
      u = ((t * 0.03 + j / 5.0 + k * 0.3) % 1.0)
      yy = GROUND_Y - u * (GROUND_Y - cy - 20)
      w = int(170 * (1 - u) + 40 * u)
      pygame.draw.ellipse(gs, (190, 255, 160), (cx - w // 2, int(yy) - 5, w, 10), 2)
    add_glow(gs, cx, cy, 80, (30, 80, 30))
    pygame.draw.ellipse(gs, (150, 160, 175), (cx - 60, cy - 8, 120, 26))
    pygame.draw.ellipse(gs, (90, 100, 115), (cx - 60, cy + 4, 120, 14))
    pygame.draw.ellipse(gs, (150, 255, 140), (cx - 24, cy - 22, 48, 26))
    for j in range(5):
      on = (t // 4 + j) % 2
      pygame.draw.circle(gs, (255, 240, 90) if on else (255, 120, 60), (cx - 44 + j * 22, cy + 10), 4)


def thunderstorm(gs, g, fx, t):                          # YELLOW: the sky goes black and lightning strikes everywhere
  f = _fade(t)
  _tint(gs, (90, 90, 70), 0.75 * f)
  rnd = random.Random(fx.get('seed', 1) * 31 + t // 3)
  if t < LIFE - 15 and t % 3 == 0:
    fx['strikes'] = [rnd.randint(40, WIDTH - 40) for _ in range(rnd.randint(1, 3))]
  for x in fx.get('strikes', ()) if t < LIFE - 15 else ():
    bx = _bolt(gs, x, rnd)
    add_glow(gs, bx, GROUND_Y - 6, 70, (90, 90, 40))
  if t % 6 < 2 and t < LIFE - 15:
    _add(gs, (70, 70, 60), 1.0)


def hurricane(gs, g, fx, t):                             # SILVER: a vast spinning storm sweeps across the screen
  f = _fade(t)
  _tint(gs, (40, 34, 20), 0.5 * f)
  cx = int(-200 + t * (WIDTH + 400) / float(LIFE))
  cy = HEIGHT // 2 - 30
  for arm in range(5):
    pts = []
    for j in range(40):
      a = arm * 2 * math.pi / 5 + j * 0.16 - t * 0.35
      r = 12 + j * 9
      pts.append((cx + math.cos(a) * r * 1.3, cy + math.sin(a) * r * 0.75))
    pygame.draw.lines(gs, (230, 236, 245), False, pts, 5)
    pygame.draw.lines(gs, (170, 180, 200), False, pts[5:], 2)
  add_glow(gs, cx, cy, 120, (40, 46, 56))
  ps = _parts(fx, 40, lambda r, i: (r.uniform(0, 6.28), r.uniform(60, 330), r.uniform(0.5, 1.0)))
  for a0, rr, s in ps:                                   # debris whirling around the eye
    a = a0 - t * 0.2 * s * 2
    x, y = cx + math.cos(a) * rr * 1.3, cy + math.sin(a) * rr * 0.75
    pygame.draw.rect(gs, (120, 90, 60), (int(x), int(y), 6, 4))
  ws = _parts_b(fx, 'wind', 40, lambda r, i: (r.uniform(0, WIDTH), r.uniform(0, GROUND_Y), r.uniform(0.6, 1.4)))
  for x0, y0, s in ws:
    x = (x0 + t * 30 * s) % (WIDTH + 80) - 40
    pygame.draw.line(gs, (220, 228, 240), (int(x), int(y0)), (int(x - 50 * s), int(y0)), 1)


def overgrowth(gs, g, fx, t):                            # FOREST: giant thorny vines erupt out of the ground across the screen
  f = _fade(t)
  _add(gs, (10, 30, 0), 0.5 * f)
  vs = _parts(fx, 14, lambda r, i: (60 + i * (WIDTH - 120) / 13.0 + r.uniform(-20, 20), r.randint(0, 22), r.uniform(220, 420), r.uniform(0, 6.28)))
  for x0, d0, hmax, ph in vs:
    k = t - d0
    if k <= 0:
      continue
    hh = min(hmax, k * 18) * (1.0 if t < LIFE - 20 else max(0.0, (LIFE - t) / 20.0))
    pts = []
    for j in range(0, int(hh), 12):
      pts.append((x0 + math.sin(j * 0.03 + ph + t * 0.05) * 24, GROUND_Y - j))
    if len(pts) > 1:
      pygame.draw.lines(gs, (40, 90, 30), False, pts, 12)
      pygame.draw.lines(gs, (90, 160, 50), False, pts, 5)
      for j, (x, y) in enumerate(pts[2::3]):             # thorns and leaves
        sd = 1 if j % 2 else -1
        pygame.draw.polygon(gs, (190, 210, 120), [(x, y), (x + 14 * sd, y - 4), (x, y - 8)])
        pygame.draw.ellipse(gs, (110, 200, 60), (x - 6 + 12 * sd, y - 12, 14, 8))
      tx, ty = pts[-1]
      pygame.draw.circle(gs, (255, 120, 180), (int(tx), int(ty)), 7)
      pygame.draw.circle(gs, (255, 230, 120), (int(tx), int(ty)), 3)


def death_toll(gs, g, fx, t):                            # SKELETAL: the bell tolls; skulls of green soul-fire rise from the earth
  f = _fade(t)
  _tint(gs, (70, 90, 60), 0.7 * f)
  if t % 30 < 6:                                         # a ghostly toll ripples out
    r = (t % 30) * 60
    pygame.draw.circle(gs, (160, 255, 170), (WIDTH // 2, 120), r + 20, 3)
  ps = _parts(fx, 26, lambda r, i: (r.uniform(40, WIDTH - 40), r.randint(0, 50), r.uniform(2.5, 4.5)))
  for x0, d0, sp in ps:
    k = t - d0
    if k < 0:
      continue
    y = GROUND_Y - k * sp
    x = x0 + math.sin(k * 0.12 + x0) * 14
    if y < -40:
      continue
    add_glow(gs, int(x), int(y), 30, (20, 80, 30))
    for j in range(4):                                   # soul-fire tail
      pygame.draw.circle(gs, (110, 255, 140), (int(x + math.sin(k * 0.3 + j) * 4), int(y + 12 + j * 9)), 8 - j * 2)
    pygame.draw.circle(gs, (225, 240, 215), (int(x), int(y)), 12)
    pygame.draw.rect(gs, (225, 240, 215), (int(x) - 7, int(y) + 6, 14, 9))
    for ex in (-5, 5):
      pygame.draw.circle(gs, (20, 60, 30), (int(x) + ex, int(y) - 1), 3)
    pygame.draw.line(gs, (20, 60, 30), (int(x) - 4, int(y) + 10), (int(x) + 4, int(y) + 10), 1)


def supernova(gs, g, fx, t):                             # COSMIC: the dragon explodes into a star; a shockwave of light fills the screen
  d = g.dragon
  cx, cy = d.centerx, d.centery
  r = int(t * 22)
  if t < 50:
    add_glow(gs, cx, cy, 60 + t * 8, (120, 70, 160))
    for k, col in enumerate(((255, 255, 255), (220, 180, 255), (160, 110, 255))):
      pygame.draw.circle(gs, col, (cx, cy), max(1, r - k * 26), 10 - k * 3)
  for a in range(16):                                    # star rays
    ang = a * math.pi / 8 + t * 0.02
    ln = min(WIDTH, t * 30) * (0.6 + 0.4 * (a % 2))
    w = 4 if a % 2 == 0 else 2
    if t < 70:
      pygame.draw.line(gs, (240, 220, 255), (cx, cy), (int(cx + math.cos(ang) * ln), int(cy + math.sin(ang) * ln)), w)
  if t < 12:
    _add(gs, (255, 240, 255), (12 - t) / 12.0)
  ps = _parts(fx, 60, lambda r_, i: (r_.uniform(0, 6.28), r_.uniform(4, 16)))
  for a, sp in ps:                                       # stardust flung outward
    rr = t * sp
    x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
    pygame.draw.circle(gs, (255, 255, 220), (int(x), int(y)), 2)


def prism_burst(gs, g, fx, t):                           # UNICORN: rainbow beams sweep out across the whole sky
  d = g.dragon
  cx, cy = d.right + 10, d.centery
  cols = ((255, 60, 60), (255, 160, 40), (255, 240, 60), (80, 230, 80), (60, 160, 255), (150, 80, 255))
  f = _fade(t)
  for k, c in enumerate(cols):
    for s in (-1, 1):
      a = s * (0.12 + k * 0.12) * math.sin(t * 0.06 + k * 0.2)
      ln = WIDTH * 1.2
      ex, ey = cx + math.cos(a) * ln, cy + math.sin(a) * ln
      pygame.draw.line(gs, c, (cx, cy), (int(ex), int(ey)), int(10 * f) + 1)
  add_glow(gs, cx, cy, 70, (120, 90, 120))
  pygame.draw.circle(gs, (255, 255, 255), (cx, cy), 12)
  ps = _parts(fx, 50, lambda r, i: (r.uniform(0, WIDTH), r.uniform(0, GROUND_Y), r.randint(0, 5)))
  for x, y, c in ps:                                     # twinkling rainbow sparkles
    if (t + int(x)) % 10 < 5:
      q = 5
      pygame.draw.line(gs, cols[c], (int(x) - q, int(y)), (int(x) + q, int(y)), 2)
      pygame.draw.line(gs, cols[c], (int(x), int(y) - q), (int(x), int(y) + q), 2)


def soul_harvest(gs, g, fx, t):                          # WRAITH: ghostly souls stream in from every side to the wraith
  f = _fade(t)
  _tint(gs, (70, 50, 20), 0.6 * f)
  d = g.dragon
  ps = _parts(fx, 44, lambda r, i: (r.uniform(0, WIDTH), r.uniform(0, GROUND_Y), r.randint(0, 45)))
  for x0, y0, d0 in ps:
    u = (t - d0) / 40.0
    if not 0 <= u <= 1:
      continue
    e = u * u
    x = x0 + (d.centerx - x0) * e + math.sin(u * 9 + x0) * 30 * (1 - u)
    y = y0 + (d.centery - y0) * e
    sd = 1 if x0 > d.centerx else -1
    add_glow(gs, int(x), int(y), 34, (20, 70, 90))
    for j in range(6):                                   # a wailing ghost with a long wispy tail
      pygame.draw.circle(gs, (140, 240, 255), (int(x + j * 9 * sd), int(y + j * 3 + math.sin(t * 0.4 + j) * 3)), 15 - j * 2)
    pygame.draw.circle(gs, (235, 255, 255), (int(x), int(y)), 11)
    for ex in (-4, 4):
      pygame.draw.circle(gs, (20, 40, 70), (int(x) + ex, int(y) - 2), 3)
    pygame.draw.ellipse(gs, (20, 40, 70), (int(x) - 3, int(y) + 3, 6, 7))
  add_glow(gs, d.centerx, d.centery, 80 + int(20 * math.sin(t * 0.3)), (30, 90, 110))


def tidal_wave(gs, g, fx, t):                            # CHINESE (Lung): a towering wave rolls across the whole screen
  f = _fade(t, 4, LIFE - 10)
  front = -300 + t * (WIDTH + 500) / float(LIFE - 15)
  top = GROUND_Y - 330
  pts = [(front - 900, GROUND_Y + 40)]
  for k in range(0, 900, 30):
    x = front - 900 + k
    u = k / 900.0
    h = top + (1 - u) * 160 + math.sin(x * 0.03 + t * 0.4) * 14
    pts.append((x, h))
  pts += [(front + 40, top + 10), (front + 70, top + 60), (front + 30, top + 100), (front, GROUND_Y + 40)]
  pygame.draw.polygon(gs, (30, 90, 170), pts)
  pygame.draw.lines(gs, (120, 200, 255), False, pts[1:-1], 6)
  for k in range(0, 900, 40):                            # foam on the crest
    x = front - 900 + k
    pygame.draw.circle(gs, (235, 250, 255), (int(x), int(top + (1 - k / 900.0) * 160 + math.sin(x * 0.03 + t * 0.4) * 14)), 7)
  pygame.draw.circle(gs, (235, 250, 255), (int(front + 50), int(top + 30)), 22, 6)  # the curling lip
  ps = _parts(fx, 40, lambda r, i: (r.uniform(-60, 60), r.uniform(-200, 0), r.uniform(0.5, 1.5)))
  for dx, dy, s in ps:                                   # spray thrown ahead of the wave
    x, y = front + 60 + dx + (t % 12) * 4 * s, top + 40 + dy * 0.4 + (t % 12) * 6
    pygame.draw.circle(gs, (210, 240, 255), (int(x), int(y)), 3)


def carpet_bomb(gs, g, fx, t):                           # CLOCKWORK: a bomber's line of bombs falls left to right and explodes
  bs = _parts(fx, 16, lambda r, i: (60 + i * (WIDTH - 120) / 15.0, i * 4))
  pygame.draw.polygon(gs, (110, 90, 70), [(int(-100 + t * 18), 40), (int(-30 + t * 18), 48), (int(-100 + t * 18), 56)])
  for x, d0 in bs:
    k = t - d0
    if k < 0:
      continue
    y = 50 + k * k * 0.9
    if y < GROUND_Y - 10:
      pygame.draw.ellipse(gs, (60, 56, 50), (int(x) - 11, int(y) - 18, 22, 36))
      pygame.draw.ellipse(gs, (120, 116, 110), (int(x) - 6, int(y) - 12, 7, 14))
      pygame.draw.polygon(gs, (190, 150, 70), [(int(x) - 11, int(y) - 22), (int(x) + 11, int(y) - 22), (int(x), int(y) - 12)])
    else:
      kk = k - math.sqrt((GROUND_Y - 60) / 0.9)
      _boom(gs, x, GROUND_Y - 20, kk / 22.0, (255, 160, 50), 90)
      if 0 <= kk < 4:
        _add(gs, (40, 30, 10), 1.0)


def stone_gaze(gs, g, fx, t):                            # COCKATRICE: a grey wave of petrification spreads from its eyes
  d = g.dragon
  r = t * 26
  if t < LIFE - 20:                                      # everything inside the spreading circle turns to grey stone
    cx, cy = d.right, d.centery
    for y in range(max(0, int(cy - r)), min(HEIGHT, int(cy + r)), 8):
      dy = abs(y + 4 - cy)
      if dy >= r:
        continue
      hw = int(math.sqrt(r * r - dy * dy))
      x0, x1 = max(0, cx - hw), min(WIDTH, cx + hw)
      if x1 > x0:
        band = pygame.Rect(x0, y, x1 - x0, 8)
        gs.fill((105, 110, 118), band, special_flags=pygame.BLEND_RGB_SUB)
        gs.fill((70, 66, 60), band, special_flags=pygame.BLEND_RGB_ADD)
  pygame.draw.circle(gs, (230, 220, 160), (d.right, d.centery), int(r), 5)
  ps = _parts(fx, 30, lambda r_, i: (r_.uniform(0, WIDTH), r_.uniform(0, GROUND_Y), r_.uniform(0, 6.28)))
  for x, y, a in ps:                                     # cracks splitting the stone
    if math.hypot(x - d.right, y - d.centery) < r:
      for j in range(3):
        pygame.draw.line(gs, (70, 66, 60), (int(x), int(y)), (int(x + math.cos(a + j * 2.1) * 18), int(y + math.sin(a + j * 2.1) * 18)), 2)
  if t < 8:
    add_glow(gs, d.right, d.centery - 6, 60, (120, 110, 40))


def black_hole(gs, g, fx, t):                            # WHALE: a black hole opens mid-screen and drags everything in
  f = _fade(t)
  cx, cy = WIDTH // 2 + 120, HEIGHT // 2 - 40
  _tint(gs, (60, 60, 40), 0.6 * f)
  rr = int(70 * f)
  for k in range(4):                                     # glowing accretion disk
    pygame.draw.ellipse(gs, ((200, 140, 255), (160, 100, 255), (255, 200, 140), (120, 80, 220))[k],
                        (cx - rr * 3 + k * 12, cy - rr // 2 + k * 3, rr * 6 - k * 24, rr - k * 6), 3)
  add_glow(gs, cx, cy, rr * 3, (60, 30, 90))
  pygame.draw.circle(gs, (0, 0, 0), (cx, cy), max(1, rr))
  pygame.draw.circle(gs, (220, 180, 255), (cx, cy), max(1, rr), 2)
  ps = _parts(fx, 70, lambda r, i: (r.uniform(0, 6.28), r.uniform(200, 700), r.uniform(0.6, 1.4)))
  for a0, d0, s in ps:                                   # matter spiralling in
    u = ((t * 0.012 * s) + d0 / 700.0) % 1.0
    dist = d0 * (1 - u)
    a = a0 + u * 6
    x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.6
    pygame.draw.line(gs, (230, 210, 255), (int(x), int(y)), (int(x + math.cos(a + 1.6) * 8), int(y + math.sin(a + 1.6) * 5)), 2)


def wild_magic(gs, g, fx, t):                            # FEY: bursts of fairy magic pop all over the screen
  cols = ((255, 140, 230), (140, 230, 255), (255, 230, 120), (190, 150, 255), (150, 255, 190))
  ps = _parts(fx, 46, lambda r, i: (r.uniform(60, WIDTH - 60), r.uniform(40, GROUND_Y - 30), r.randint(0, 72), r.randint(0, 4)))
  for x, y, d0, c in ps:
    u = (t - d0) / 24.0
    if 0 <= u <= 1:
      col = cols[c]
      r = int(14 + 110 * u)
      if u < 0.25:
        pygame.draw.circle(gs, (255, 255, 255), (int(x), int(y)), int(22 * (1 - u * 4)) + 2)
      pygame.draw.circle(gs, col, (int(x), int(y)), r, max(2, int(8 * (1 - u))))
      for k in range(8):                                 # star sparks
        a = k * math.pi / 4 + u
        px, py = x + math.cos(a) * r * 1.1, y + math.sin(a) * r * 1.1
        q = int(10 * (1 - u)) + 2
        pygame.draw.line(gs, (255, 255, 255), (int(px) - q, int(py)), (int(px) + q, int(py)), 2)
        pygame.draw.line(gs, (255, 255, 255), (int(px), int(py) - q), (int(px), int(py) + q), 2)
      add_glow(gs, int(x), int(y), r, tuple(v // 4 for v in col))


def talon_storm(gs, g, fx, t):                           # EAGLE: giant talon slashes rake across the screen, feathers fly
  ps = _parts(fx, 12, lambda r, i: (r.uniform(150, WIDTH - 150), r.uniform(80, GROUND_Y - 60), i * 6, r.uniform(-0.8, 0.8)))
  for x, y, d0, a in ps:
    u = (t - d0) / 12.0
    if not 0 <= u <= 1.6:
      continue
    ln = 420
    for k in (-1, 0, 1):                                 # three claw marks
      ox, oy = -math.sin(a) * 34 * k, math.cos(a) * 34 * k
      p0 = (x - math.cos(a) * ln / 2 + ox, y - math.sin(a) * ln / 2 + oy)
      e = min(1.0, u)
      p1 = (p0[0] + math.cos(a) * ln * e, p0[1] + math.sin(a) * ln * e)
      w = max(2, int(16 * (1.6 - u) / 1.6))
      pygame.draw.line(gs, (200, 40, 30), (int(p0[0]), int(p0[1]) + 3), (int(p1[0]), int(p1[1]) + 3), w)
      pygame.draw.line(gs, (255, 230, 170), (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), w)
      pygame.draw.line(gs, (255, 255, 255), (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), max(1, w // 3))
  fs = _parts_b(fx, 'feathers', 45, lambda r, i: (r.uniform(0, WIDTH), r.uniform(-200, 0), r.uniform(0, 6.28)))
  for x0, y0, ph in fs:
    y = y0 + t * 5
    x = x0 + math.sin(t * 0.1 + ph) * 30
    if 0 < y < GROUND_Y:
      a = math.sin(t * 0.15 + ph)
      pygame.draw.ellipse(gs, (230, 200, 150), (int(x), int(y), 28, 9))
      pygame.draw.line(gs, (140, 100, 60), (int(x), int(y + 3)), (int(x + 18), int(y + 3 + a * 2)), 1)


def _bird(gs, x, y, s, flap, col):
  w = int(22 * s)
  dy = int(9 * s * flap)
  pygame.draw.polygon(gs, col, [(x - w, y - dy), (x - 4, y), (x, y + 3), (x + 4, y), (x + w, y - dy), (x + 3, y + 5), (x - 3, y + 5)])


def murder_of_crows(gs, g, fx, t):                       # RAVEN: a huge flock of crows sweeps across, darkening the sky
  f = _fade(t)
  _tint(gs, (50, 50, 40), 0.6 * f)
  ps = _parts(fx, 70, lambda r, i: (r.uniform(-900, 0), r.uniform(20, GROUND_Y - 30), r.uniform(0.6, 1.2), r.uniform(0, 6.28)))
  for x0, y0, s, ph in ps:
    x = x0 + t * 22 * s
    y = y0 + math.sin(t * 0.12 + ph) * 18
    if -40 < x < WIDTH + 40:
      _bird(gs, int(x), int(y), s * 1.3, math.sin(t * 0.6 + ph), (20, 14, 26))
      if s > 1.05:
        pygame.draw.circle(gs, (200, 60, 60), (int(x + 5 * s), int(y)), 1)


def _stag(gs, x, y, s, ph, col):
  """a charging ghost stag silhouette"""
  leg = math.sin(ph) * 10 * s
  body = pygame.Rect(int(x - 34 * s), int(y - 18 * s), int(68 * s), int(30 * s))
  pygame.draw.ellipse(gs, col, body)
  pygame.draw.polygon(gs, col, [(x + 26 * s, y - 10 * s), (x + 50 * s, y - 32 * s), (x + 62 * s, y - 26 * s), (x + 36 * s, y)])
  for k, lx in enumerate((-26, -14, 14, 26)):
    sw = leg if k % 2 else -leg
    pygame.draw.line(gs, col, (int(x + lx * s), int(y + 6 * s)), (int(x + lx * s + sw), int(y + 34 * s)), max(2, int(5 * s)))
  for k in (0, 1):                                       # antlers
    bx, by = x + (50 + k * 6) * s, y - 32 * s
    pygame.draw.line(gs, col, (int(bx), int(by)), (int(bx - 6 * s), int(by - 30 * s)), max(2, int(3 * s)))
    pygame.draw.line(gs, col, (int(bx - 4 * s), int(by - 16 * s)), (int(bx + 10 * s), int(by - 26 * s)), max(2, int(3 * s)))


def stampede(gs, g, fx, t):                              # PERYTON: a herd of blazing red spirit-stags charges across the land
  f = _fade(t)
  _tint(gs, (20, 50, 50), 0.5 * f)
  ps = _parts(fx, 12, lambda r, i: (-120 - i * 110 + r.uniform(-40, 40), GROUND_Y - 40 - r.uniform(0, 220), r.uniform(0.9, 1.4)))
  for x0, y, s in ps:
    x = x0 + t * 26
    if -120 < x < WIDTH + 120:
      for j in range(3):                                 # flame trail
        pygame.draw.ellipse(gs, (255, 90 + j * 40, 60), (int(x - 60 * s - j * 24), int(y - 12 * s), int(40 * s), int(20 * s)))
      add_glow(gs, int(x), int(y), int(70 * s), (90, 20, 20))
      _stag(gs, x, y, s, t * 0.7 + x0, (255, 110, 110))
      _stag(gs, x, y, s * 0.92, t * 0.7 + x0, (255, 200, 180))
  if t % 10 < 3 and t < LIFE - 20:
    g.shake_for(2, 3)


SHOWS = {'RED': meteor_storm, 'BLUE': blizzard, 'GREEN': acid_rain, 'ALIEN': abduction, 'YELLOW': thunderstorm, 'SILVER': hurricane,
         'FOREST': overgrowth, 'SKELETAL': death_toll, 'COSMIC': supernova, 'UNICORN': prism_burst, 'WRAITH': soul_harvest,
         'CHINESE': tidal_wave, 'CLOCKWORK': carpet_bomb, 'COCKATRICE': stone_gaze, 'WHALE': black_hole, 'FEY': wild_magic,
         'EAGLE': talon_storm, 'RAVEN': murder_of_crows, 'PERYTON': stampede}


def draw(gs, game, fx):
  fn = SHOWS.get(fx.get('k'))
  if fn is None or fx['t'] >= LIFE:
    return
  try:
    fn(gs, game, fx, fx['t'])
  except Exception:
    fx['k'] = None                                       # (never let a show crash the game)
