"""Flappy Dragon art: all drawing functions and pre-rendered backgrounds."""
from fd_core import *
import fd_core
import fd_pixart as PX
from fd_hd import hd_frame
import fd_env as ENV
from fd_items import coin_img, crystal_img
from fd_towers import tower_art
from fd_bone import bone_frame, fly_index
from fd_cosmic import void_frame, void_fly_index, void_mouth
from fd_sheet import has_sheet, sheet
from fd_enemy_anims import KINDS as EA_KINDS, anim_blit, anim_count, anim_frame, proj_frame, proj_count, prewarm_step
from fd_siege import draw_catapult, draw_trebuchet, draw_ballista, prewarm_siege   # War-style siege engines

TAU = 2 * math.pi

def darken(c, f):
  return (int(c[0] * f), int(c[1] * f), int(c[2] * f))

def _title_key(palette):
  for k, v in DRAGON_PALETTES.items():
    if v is palette:
      return k
  return None

def draw_dragon(surface, dx, dy, tilt, wing_angle, palette, fire_active=False):
  """(dx, dy) is the top-left of the dragon's 65x38 hitbox."""
  main_c, dark_c, belly_c, eye_c = palette['main'], palette['dark'], palette['belly'], palette['eye']
  hi_c = lighten(main_c, 45)
  deep_c = darken(dark_c, 0.6)
  plate_c = darken(belly_c, 0.78)
  ring_c = BREATH_BAR.get(_title_key(palette), (255, 150, 0))
  f_y = int(math.sin(wing_angle) * 22)
  S = (dx + 26, dy + 16)

  pygame.draw.polygon(surface, deep_c, [(dx + 34, dy + 14), (dx + 22, dy - 12 + f_y * 7 // 10), (dx + 40, dy - 20 + f_y * 7 // 10), (dx + 56, dy - 2 + f_y * 7 // 10)])

  tail = []
  for i in range(9):
    t = i / 8.0
    tail.append((int(dx + 16 - 44 * t), int(dy + 24 + 10 * t - tilt * t * 1.1 + math.sin(wing_angle * 0.8 + t * 3.0) * 3 * t), int(8 - 6 * t)))
  for px, py, rr in tail:
    pygame.draw.circle(surface, deep_c, (px, py), rr + 2)
  for px, py, rr in tail:
    pygame.draw.circle(surface, main_c, (px, py), rr)
  for px, py, rr in tail[1:7:2]:
    pygame.draw.polygon(surface, dark_c, [(px - 3, py - rr + 1), (px, py - rr - 6), (px + 3, py - rr + 1)])
  tx, ty, _r = tail[-1]
  pygame.draw.polygon(surface, dark_c, [(tx + 3, ty - 6), (tx - 14, ty), (tx + 3, ty + 6)])
  pygame.draw.polygon(surface, main_c, [(tx + 2, ty - 3), (tx - 8, ty), (tx + 2, ty + 3)])

  pygame.draw.ellipse(surface, deep_c, (dx + 12, dy + 22, 20, 20))
  pygame.draw.ellipse(surface, main_c, (dx + 14, dy + 23, 16, 17))
  pygame.draw.line(surface, dark_c, (dx + 22, dy + 36), (dx + 19, dy + 44), 5)
  pygame.draw.ellipse(surface, dark_c, (dx + 12, dy + 42, 14, 7))
  for k in range(3):
    pygame.draw.polygon(surface, BONE_WHITE, [(dx + 12 + k * 4, dy + 46), (dx + 14 + k * 4, dy + 51), (dx + 16 + k * 4, dy + 46)])

  for i in range(6):
    x0 = dx + 14 + i * 7
    h = 12 - abs(i - 2) * 2
    pygame.draw.polygon(surface, dark_c, [(x0, dy + 10), (x0 + 4, dy + 10 - h), (x0 + 8, dy + 9)])

  pygame.draw.ellipse(surface, deep_c, (dx + 10, dy + 4, 50, 36))
  pygame.draw.ellipse(surface, main_c, (dx + 12, dy + 6, 46, 32))
  pygame.draw.ellipse(surface, hi_c, (dx + 20, dy + 9, 26, 7))
  for sx, sy in ((18, 16), (26, 13), (34, 13), (42, 14), (22, 24), (31, 20), (40, 21), (49, 19)):
    pygame.draw.arc(surface, dark_c, (dx + sx - 4, dy + sy - 3, 8, 6), 0, math.pi, 1)
  pygame.draw.ellipse(surface, belly_c, (dx + 28, dy + 22, 24, 14))
  for i in range(4):
    pygame.draw.line(surface, plate_c, (dx + 32 + i * 5, dy + 24), (dx + 32 + i * 5, dy + 34), 1)
  pygame.draw.line(surface, lighten(belly_c, 25), (dx + 31, dy + 23), (dx + 48, dy + 23), 1)

  pygame.draw.ellipse(surface, deep_c, (dx + 35, dy + 25, 12, 16))
  pygame.draw.ellipse(surface, main_c, (dx + 36, dy + 26, 10, 13))
  pygame.draw.line(surface, dark_c, (dx + 42, dy + 36), (dx + 47, dy + 43), 4)
  for k in range(3):
    pygame.draw.polygon(surface, BONE_WHITE, [(dx + 43 + k * 3, dy + 42), (dx + 45 + k * 3, dy + 48), (dx + 47 + k * 3, dy + 42)])

  hx, hy = dx + 52, dy - 12 - tilt
  base, tip = (dx + 44, dy + 20), (hx + 6, hy + 14)
  segs = [(int(base[0] + (tip[0] - base[0]) * i / 4.0), int(base[1] + (tip[1] - base[1]) * i / 4.0)) for i in range(5)]
  for px, py in segs:
    pygame.draw.circle(surface, deep_c, (px, py), 9)
  for px, py in segs:
    pygame.draw.circle(surface, main_c, (px, py), 7)
  for px, py in segs[:-1]:
    pygame.draw.circle(surface, belly_c, (px + 1, py + 4), 3)

  pygame.draw.polygon(surface, deep_c, [(hx + 4, hy + 6), (hx - 12, hy - 15), (hx + 14, hy + 1)])
  pygame.draw.polygon(surface, dark_c, [(hx + 6, hy + 5), (hx - 8, hy - 11), (hx + 13, hy + 2)])
  pygame.draw.polygon(surface, dark_c, [(hx + 12, hy + 3), (hx + 6, hy - 12), (hx + 20, hy + 3)])
  for k in range(3):
    pygame.draw.polygon(surface, dark_c, [(hx - 2, hy + 8 + k * 5), (hx - 9, hy + 11 + k * 5), (hx, hy + 13 + k * 5)])
  pygame.draw.ellipse(surface, deep_c, (hx - 1, hy - 1, 30, 24))
  pygame.draw.ellipse(surface, main_c, (hx, hy, 28, 22))
  pygame.draw.rect(surface, main_c, (hx + 16, hy + 6, 18, 12), border_radius=4)
  pygame.draw.rect(surface, dark_c, (hx + 16, hy + 6, 18, 12), 1, border_radius=4)
  if fire_active:
    pygame.draw.polygon(surface, (60, 10, 5), [(hx + 14, hy + 16), (hx + 35, hy + 17), (hx + 32, hy + 29), (hx + 15, hy + 25)])
    pygame.draw.polygon(surface, ring_c, [(hx + 20, hy + 18), (hx + 33, hy + 18), (hx + 30, hy + 25), (hx + 21, hy + 23)])
    pygame.draw.polygon(surface, dark_c, [(hx + 14, hy + 24), (hx + 33, hy + 28), (hx + 32, hy + 31), (hx + 15, hy + 27)])
  else:
    pygame.draw.polygon(surface, dark_c, [(hx + 13, hy + 16), (hx + 34, hy + 16), (hx + 31, hy + 22), (hx + 15, hy + 23)])
    pygame.draw.line(surface, deep_c, (hx + 17, hy + 17), (hx + 33, hy + 17), 1)
  for k in range(3):
    pygame.draw.polygon(surface, BONE_WHITE, [(hx + 19 + k * 5, hy + 17), (hx + 21 + k * 5, hy + 21), (hx + 23 + k * 5, hy + 17)])
  pygame.draw.circle(surface, deep_c, (hx + 32, hy + 9), 2)
  pygame.draw.line(surface, deep_c, (hx + 13, hy + 4), (hx + 24, hy + 3), 3)
  pygame.draw.circle(surface, (20, 20, 20), (hx + 18, hy + 8), 4)
  pygame.draw.circle(surface, eye_c, (hx + 19, hy + 8), 3)
  pygame.draw.line(surface, (0, 0, 0), (hx + 19, hy + 6), (hx + 19, hy + 10), 1)
  pygame.draw.circle(surface, (255, 255, 255), (hx + 17, hy + 6), 1)
  if fire_active:
    pygame.draw.circle(surface, ring_c, (hx + 30, hy + 12), 35, 4)
    pygame.draw.circle(surface, lighten(ring_c, 60), (hx + 30, hy + 12), 26, 2)

  P1 = (dx + 8, dy - 18 + f_y)
  P2 = (dx + 26, dy - 26 + f_y)
  P3 = (dx + 46, dy - 10 + f_y)

  def scallop(a, b):
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    return (int(mx + (S[0] - mx) * 0.28), int(my + (S[1] - my) * 0.28))

  pts = [S, P1, scallop(P1, P2), P2, scallop(P2, P3), P3]
  cx = sum(p[0] for p in pts) / 6.0
  cy = sum(p[1] for p in pts) / 6.0
  inner = [(int(cx + (p[0] - cx) * 0.78), int(cy + (p[1] - cy) * 0.78)) for p in pts]
  pygame.draw.polygon(surface, dark_c, pts)
  pygame.draw.polygon(surface, main_c, inner)
  for P in (P1, P2, P3):
    pygame.draw.line(surface, BONE_WHITE, S, P, 2)
    pygame.draw.circle(surface, BONE_WHITE, P, 2)
  pygame.draw.polygon(surface, BONE_WHITE, [(P3[0], P3[1]), (P3[0] + 6, P3[1] + 4), (P3[0] + 2, P3[1] + 8)])

def draw_chinese_dragon(surface, dx, dy, tilt, wing_angle, palette, fire_active=False):
  main_c, belly_c, dark_c, eye_c = palette['main'], palette['belly'], palette['dark'], palette['eye']
  deep_c = darken(dark_c, 0.6)
  gold, orange = (240, 200, 60), (255, 130, 30)
  points = [(int(dx + 20 - i * 14), int(dy + 15 + math.sin(wing_angle + i * 0.8) * 12 - tilt * 0.4)) for i in range(8)]
  tx, ty = points[-1]
  pygame.draw.polygon(surface, orange, [(tx, ty), (tx - 24, ty - 15), (tx - 14, ty), (tx - 26, ty + 15)])
  pygame.draw.polygon(surface, gold, [(tx - 2, ty), (tx - 16, ty - 8), (tx - 10, ty), (tx - 17, ty + 8)])
  for i in range(len(points) - 1, -1, -1):
    px, py = points[i]
    size = 14 - i
    pygame.draw.polygon(surface, orange, [(px - 6, py - size), (px, py - size - 13), (px + 6, py - size)])
    pygame.draw.polygon(surface, gold, [(px - 3, py - size), (px, py - size - 8), (px + 3, py - size)])
    pygame.draw.circle(surface, deep_c, (px, py), size + 2)
    pygame.draw.circle(surface, main_c, (px, py), size)
    pygame.draw.circle(surface, belly_c, (px, py + int(size * 0.4)), int(size * 0.6))
    pygame.draw.arc(surface, dark_c, (px - size // 2, py - size + 2, size, size), 0.3, 2.8, 1)
    if i in (2, 5):
      lx, ly = px - 2, py + size
      pygame.draw.line(surface, main_c, (lx, ly - 2), (lx - 5, ly + 9), 4)
      for k in range(3):
        pygame.draw.line(surface, BONE_WHITE, (lx - 5, ly + 9), (lx - 9 + k * 4, ly + 14), 1)
  hx, hy = points[0][0] + 10, points[0][1] - 5
  for sgn in (0, 1):                                             # long whiskers
    wp = [(hx + 36, hy + 14 + sgn * 3)]
    for k in range(1, 6):
      wp.append((hx + 36 + k * 7, int(hy + 14 + sgn * 3 + k * 4 + math.sin(wing_angle * 2 + k + sgn) * 5)))
    pygame.draw.lines(surface, gold, False, wp, 2)
  pygame.draw.line(surface, gold, (hx + 12, hy + 2), (hx + 4, hy - 18), 3)      # antlers
  pygame.draw.line(surface, gold, (hx + 4, hy - 18), (hx - 4, hy - 24), 3)
  pygame.draw.line(surface, gold, (hx + 5, hy - 12), (hx + 14, hy - 20), 2)
  pygame.draw.polygon(surface, gold, [(hx + 16, hy + 24), (hx + 22, hy + 36), (hx + 28, hy + 24)])   # beard
  pygame.draw.ellipse(surface, deep_c, (hx - 1, hy - 1, 34, 24))
  pygame.draw.ellipse(surface, main_c, (hx, hy, 32, 22))
  pygame.draw.rect(surface, main_c, (hx + 16, hy + 8, 22, 12), border_radius=4)
  pygame.draw.polygon(surface, belly_c, [(hx + 14, hy + 18), (hx + 36, hy + 18), (hx + 30, hy + 26), (hx + 16, hy + 25)])
  for k in range(3):
    pygame.draw.polygon(surface, BONE_WHITE, [(hx + 20 + k * 5, hy + 18), (hx + 22 + k * 5, hy + 22), (hx + 24 + k * 5, hy + 18)])
  pygame.draw.circle(surface, deep_c, (hx + 36, hy + 12), 2)
  pygame.draw.line(surface, deep_c, (hx + 16, hy + 6), (hx + 28, hy + 5), 3)
  pygame.draw.circle(surface, (20, 20, 20), (hx + 21, hy + 10), 4)
  pygame.draw.circle(surface, eye_c, (hx + 22, hy + 10), 2)
  pygame.draw.circle(surface, (255, 215, 90), (hx + 54, hy - 4), 7)                # flaming pearl
  pygame.draw.circle(surface, (210, 250, 255), (hx + 54, hy - 4), 4)
  if fire_active:
    pygame.draw.circle(surface, (255, 150, 0), (hx + 42, hy + 12), 35, 4)

def draw_skeletal_dragon(surface, dx, dy, tilt, wing_angle, palette, fire_active=False):
  bone_c, dark_c, eye_c = palette['main'], palette['dark'], palette['eye']
  shade = darken(bone_c, 0.7)
  soul = (30, 255, 90)
  f_y = int(math.sin(wing_angle) * 22)
  spine_y = dy + 15 - tilt
  for i in range(12):                                                  # vertebrae
    t = i / 11.0
    vx = int(dx + 44 - 70 * t)
    vy = int(spine_y + math.sin(wing_angle * 0.8 + t * 3.0) * 3 * t)
    r = int(4 - 2 * t)
    pygame.draw.circle(surface, shade, (vx, vy), r + 1)
    pygame.draw.circle(surface, bone_c, (vx, vy), r)
  tipx, tipy = dx - 26, int(spine_y + math.sin(wing_angle * 0.8 + 3.0) * 3)
  blade = [(tipx + 4, tipy - 5), (tipx - 14, tipy), (tipx + 4, tipy + 5)]
  pygame.draw.polygon(surface, bone_c, blade)
  pygame.draw.polygon(surface, shade, blade, 1)
  for i in range(5):                                                   # ribs
    rx = dx + 8 + i * 7
    pygame.draw.arc(surface, shade, (rx, spine_y - 2, 11, 25 - i), math.pi, 2 * math.pi, 4)
    pygame.draw.arc(surface, bone_c, (rx, spine_y - 2, 11, 25 - i), math.pi, 2 * math.pi, 2)
  pr = 4 + int(2 * abs(math.sin(wing_angle * 1.5)))                    # soul fire in the ribcage
  pygame.draw.circle(surface, (10, 120, 40), (dx + 28, spine_y + 14), pr + 3)
  pygame.draw.circle(surface, soul, (dx + 28, spine_y + 14), pr)
  pygame.draw.circle(surface, (210, 255, 220), (dx + 28, spine_y + 14), 2)
  for lx, ly in ((dx + 14, spine_y), (dx + 38, spine_y + 2)):          # legs
    kx, ky = lx - 6, ly + 20
    fx, fy = lx + 3, ly + 31
    pygame.draw.line(surface, shade, (lx, ly), (kx, ky), 6)
    pygame.draw.line(surface, bone_c, (lx, ly), (kx, ky), 4)
    pygame.draw.line(surface, shade, (kx, ky), (fx, fy), 5)
    pygame.draw.line(surface, bone_c, (kx, ky), (fx, fy), 3)
    pygame.draw.circle(surface, bone_c, (kx, ky), 3)
    for k in range(3):
      pygame.draw.line(surface, (250, 250, 245), (fx, fy), (fx + 3 + k * 3, fy + 4 - k), 2)
  hx, hy = dx + 48, dy - 5 - tilt
  for i in range(4):                                                   # neck
    t = i / 3.0
    nx = int(dx + 44 + (hx + 4 - (dx + 44)) * t)
    ny = int(spine_y + (hy + 14 - spine_y) * t)
    pygame.draw.circle(surface, shade, (nx, ny), 5)
    pygame.draw.circle(surface, bone_c, (nx, ny), 4)
  pygame.draw.polygon(surface, bone_c, [(hx + 4, hy + 3), (hx - 10, hy - 12), (hx + 10, hy)])
  pygame.draw.polygon(surface, bone_c, [(hx + 12, hy), (hx + 8, hy - 14), (hx + 18, hy)])
  skull = [(hx, hy), (hx + 20, hy), (hx + 28, hy + 12), (hx + 18, hy + 22), (hx + 5, hy + 20)]
  pygame.draw.polygon(surface, bone_c, skull)
  pygame.draw.polygon(surface, shade, skull, 2)
  pygame.draw.rect(surface, bone_c, (hx + 20, hy + 11, 16, 9), border_radius=2)
  pygame.draw.rect(surface, shade, (hx + 20, hy + 11, 16, 9), 1, border_radius=2)
  if fire_active:
    pygame.draw.polygon(surface, bone_c, [(hx + 10, hy + 20), (hx + 34, hy + 22), (hx + 30, hy + 34), (hx + 12, hy + 28)])
    pygame.draw.polygon(surface, soul, [(hx + 16, hy + 22), (hx + 32, hy + 24), (hx + 29, hy + 30)])
  else:
    pygame.draw.polygon(surface, bone_c, [(hx + 10, hy + 20), (hx + 35, hy + 19), (hx + 30, hy + 26), (hx + 14, hy + 27)])
    pygame.draw.polygon(surface, shade, [(hx + 10, hy + 20), (hx + 35, hy + 19), (hx + 30, hy + 26), (hx + 14, hy + 27)], 1)
  for k in range(4):
    pygame.draw.polygon(surface, (250, 250, 245), [(hx + 21 + k * 4, hy + 20), (hx + 23 + k * 4, hy + 24), (hx + 25 + k * 4, hy + 20)])
  pygame.draw.circle(surface, (10, 10, 10), (hx + 17, hy + 9), 5)
  pygame.draw.circle(surface, eye_c, (hx + 18, hy + 9), 2)
  pygame.draw.line(surface, shade, (hx + 8, hy + 3), (hx + 13, hy + 9), 1)
  jx, jy = dx + 25, spine_y - 4                                         # wings: tattered membrane + finger bones
  tips = [(dx + 2, dy - 26 + f_y), (dx + 22, dy - 34 + f_y), (dx + 46, dy - 18 + f_y)]
  mid1 = ((tips[0][0] + tips[1][0]) // 2 + 1, (tips[0][1] + tips[1][1]) // 2 + 10)
  mid2 = ((tips[1][0] + tips[2][0]) // 2, (tips[1][1] + tips[2][1]) // 2 + 10)
  pygame.draw.polygon(surface, (44, 50, 46), [(jx, jy), tips[0], mid1, tips[1], mid2, tips[2]])
  for t in tips:
    pygame.draw.line(surface, shade, (jx, jy), t, 5)
    pygame.draw.line(surface, bone_c, (jx, jy), t, 3)
    pygame.draw.circle(surface, bone_c, t, 3)
  if fire_active:
    pygame.draw.circle(surface, (10, 255, 50), (hx + 40, hy + 15), 35, 4)

def draw_gear(surface, cx, cy, r, ang, col, dark):
  for i in range(6):
    a = ang + i * math.pi / 3
    pygame.draw.line(surface, col, (cx, cy), (int(cx + math.cos(a) * (r + 4)), int(cy + math.sin(a) * (r + 4))), 3)
  pygame.draw.circle(surface, col, (cx, cy), r)
  pygame.draw.circle(surface, dark, (cx, cy), r - 3)
  pygame.draw.circle(surface, col, (cx, cy), 2)

DRAGON_CANVAS = {"CHINESE": (224, 116, 106, 46), "SKELETAL": (180, 124, 46, 62)}
DRAGON_DEFAULT_CANVAS = (176, 120, 46, 58)
DRAGON_FRAMES = 14

def dragon_sprite(key, tq, wq, fire):
  ckey = ("dragon", key, tq, wq, fire)
  spr = SPRITE_CACHE.get(ckey)
  if spr is None:
    w, h, ox, oy = DRAGON_CANVAS.get(key, DRAGON_DEFAULT_CANVAS)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pal = DRAGON_PALETTES[key]
    wing = wq * (TAU / DRAGON_FRAMES)
    if key == "CHINESE":
      draw_chinese_dragon(s, ox, oy, tq, wing, pal, fire)
    elif key == "SKELETAL":
      draw_skeletal_dragon(s, ox, oy, tq, wing, pal, fire)
    else:
      draw_dragon(s, ox, oy, tq, wing, pal, fire)
      if key == "CHRONO":                                    # clockwork gears on the flank
        draw_gear(s, ox + 30, oy + 22, 8, wing * 0.5, (240, 210, 110), (15, 70, 95))
        draw_gear(s, ox + 44, oy + 28, 5, -wing * 0.8, (240, 210, 110), (15, 70, 95))
    spr = SPRITE_CACHE[ckey] = (ck(s), ox, oy)
  return spr

LAVA = ((255, 236, 110), (255, 176, 44), (255, 96, 20))

def _up(s):
  return ck(pygame.transform.scale(s, (s.get_width() * 2, s.get_height() * 2)))

def lava_stream_sprite(fr):
  k = ("lflame", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    from fd_extra import extra_frame
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(7 + fr)
    n = 10
    for i in range(n):
      t = i / (n - 1.0)
      b = extra_frame('fire', i * 3 + fr * 2)
      sc = 0.45 + 0.95 * t
      bw, bh = max(1, int(b.get_width() * sc)), max(1, int(b.get_height() * sc))
      img = pygame.transform.scale(b, (bw, bh))
      x = t * (W - bw - 4)
      y = H / 2.0 - bh / 2.0 + t * t * 5 + rnd.uniform(-1, 1) * (1 + 5 * t)
      s.blit(img, (int(x), int(y)))
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

DEATH_RAMP = ((10, 4, 16), (36, 14, 52), (72, 30, 104), (124, 70, 176), (196, 156, 240))
def _death_col(c):
  """fire colour -> death-smoke colour (by brightness)"""
  L = (c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11) / 255.0 * (len(DEATH_RAMP) - 1)
  j = min(len(DEATH_RAMP) - 2, int(L))
  f = L - j
  a, b = DEATH_RAMP[j], DEATH_RAMP[j + 1]
  return (int(a[0] + (b[0] - a[0]) * f), int(a[1] + (b[1] - a[1]) * f), int(a[2] + (b[2] - a[2]) * f))

def _death_puff(i):
  from fd_extra import extra_frame
  return extra_frame('fire', i, _death_col)

def death_stream_sprite(fr):
  """Bone Reaper's Death Cloud: drawn exactly like the magma stream, in death-smoke colours, with a few skulls"""
  k = ("dcloud", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(11 + fr)
    n = 10
    for i in range(n):
      t = i / (n - 1.0)
      b = _death_puff((i * 3 + fr * 2) % 8)
      sc = 0.5 + 1.0 * t
      bw, bh = max(1, int(b.get_width() * sc)), max(1, int(b.get_height() * sc))
      img = pygame.transform.scale(b, (bw, bh))
      x = t * (W - bw - 4)
      y = H / 2.0 - bh / 2.0 + t * t * 4 + rnd.uniform(-1, 1) * (1 + 6 * t)
      s.blit(img, (int(x), int(y)))
    for j in range(3):                                   # little skulls tumbling in the cloud
      x, y = 40 + j * 42 + rnd.randint(-6, 6), H // 2 + rnd.randint(-12, 12)
      pygame.draw.circle(s, (225, 205, 255), (x, y), 4)
      pygame.draw.rect(s, (225, 205, 255), (x - 3, y + 2, 6, 3))
      pygame.draw.rect(s, (40, 14, 54), (x - 2, y - 1, 1, 2))
      pygame.draw.rect(s, (40, 14, 54), (x + 1, y - 1, 1, 2))
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

WATER_RAMP = ((10, 40, 110), (24, 90, 180), (60, 160, 235), (150, 220, 255), (235, 250, 255))


def _water_col(c):
  v = (c[0] * 3 + c[1] * 6 + c[2]) / 2550.0
  return WATER_RAMP[min(4, int(v * 5))]


def _water_puff(i):
  from fd_extra import extra_frame
  return extra_frame('fire', i, _water_col)


def water_stream_sprite(fr):
  """Lung Dragon's Tidal Jet: drawn like the magma stream in water colours, with spray droplets"""
  k = ("wjet", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(23 + fr)
    n = 10
    for i in range(n):
      t = i / (n - 1.0)
      b = _water_puff((i * 3 + fr * 2) % 8)
      sc = 0.5 + 1.0 * t
      bw, bh = max(1, int(b.get_width() * sc)), max(1, int(b.get_height() * sc))
      img = pygame.transform.scale(b, (bw, bh))
      x = t * (W - bw - 4)
      y = H / 2.0 - bh / 2.0 + t * t * 4 + rnd.uniform(-1, 1) * (1 + 6 * t)
      s.blit(img, (int(x), int(y)))
    for j in range(14):                                  # spray droplets
      x, y = rnd.randint(20, W - 6), H // 2 + rnd.randint(-22, 22)
      pygame.draw.circle(s, (220, 245, 255), (x, y), rnd.choice((1, 1, 2)))
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

def frost_stream_sprite(fr):
  k = ("frost", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(5 + fr * 3)
    cy = H / 2.0
    for layer, (col, rad) in enumerate((((120, 170, 225), 1.0), ((170, 210, 245), 0.82), ((225, 244, 255), 0.55), ((255, 255, 255), 0.3))):
      for _ in range(60):
        t = rnd.random() * (1.0 if layer < 2 else 0.8)
        x = 2 + t * (W - 34)
        y = cy + t * t * 6 + rnd.uniform(-1, 1) * (2 + 16 * t) * rad
        rr = (2 + 9 * t ** 0.8) * rad * rnd.uniform(0.7, 1.2)
        pygame.draw.circle(s, col, (int(x), int(y)), max(1, int(rr)))
    for _ in range(14):
      t = rnd.uniform(0.2, 1.0)
      x = 2 + t * (W - 34)
      y = cy + rnd.uniform(-1, 1) * (5 + 20 * t)
      a = rnd.uniform(-0.5, 0.5)
      ln = rnd.uniform(6, 11)
      pygame.draw.polygon(s, (240, 252, 255), [(int(x), int(y)), (int(x + math.cos(a + 0.3) * ln * 0.4), int(y + math.sin(a + 0.3) * ln * 0.4 + 2)), (int(x + math.cos(a) * ln), int(y + math.sin(a) * ln)), (int(x + math.cos(a - 0.3) * ln * 0.4), int(y + math.sin(a - 0.3) * ln * 0.4 - 2))])
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

ACID_RAMP = ((30, 84, 44), (52, 128, 52), (92, 180, 56), (150, 224, 70), (204, 248, 120), (244, 255, 190))

def _acidify(c):
  lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
  for t, col in zip((95, 130, 160, 190, 222), ACID_RAMP):
    if lum < t:
      return col
  return ACID_RAMP[-1]

def acid_stream_sprite(fr):
  """Same flowing animation as the magma breath, in acid greens, with drips falling off it."""
  k = ("acidstream", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    from fd_extra import extra_frame
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(7 + fr)
    n = 10
    for i in range(n):
      t = i / (n - 1.0)
      b = extra_frame('fire', i * 3 + fr * 2, _acidify)
      sc = 0.45 + 0.95 * t
      bw, bh = max(1, int(b.get_width() * sc)), max(1, int(b.get_height() * sc))
      img = pygame.transform.scale(b, (bw, bh))
      x = t * (W - bw - 4)
      y = H / 2.0 - bh / 2.0 + t * t * 5 + rnd.uniform(-1, 1) * (1 + 5 * t)
      s.blit(img, (int(x), int(y)))
    for j in range(4):
      x = 30 + j * 34 + (fr * 5) % 11
      y = H // 2 + 8 + ((fr * 3 + j * 5) % 12)
      pygame.draw.ellipse(s, (170, 255, 90), (x, y, 3, 4))
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

TORNADO_COLS = ((70, 120, 190), (110, 170, 235), (170, 215, 255), (235, 248, 255))

def tornado_sprite(fr):
  """Sky-magic tornado (8-frame spin): stacked swirling rings, narrow at the ground, with sparkles."""
  fr %= 8
  k = ("tornado", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    h = 96
    s = pygame.Surface((100, h + 26), pygame.SRCALPHA)
    n = 12
    f = fr * 1.5
    for i in range(n):
      t = i / (n - 1.0)
      y = h - t * h + 14
      w = 8 + t * 34
      cx = 50 + math.sin(f * 0.7 + t * 5) * 6 * t
      hh = 4 + t * 5
      pygame.draw.ellipse(s, TORNADO_COLS[1] + (110,), (int(cx - w), int(y - hh), int(w * 2), int(hh * 2)))
      ph = f * 0.9 + i * 0.8
      for kk, c in enumerate(TORNADO_COLS):
        ww = w * (1 - kk * 0.2)
        a0 = math.radians((ph * 57 + kk * 40) % 360)
        pygame.draw.arc(s, c, (int(cx - ww), int(y - hh), max(2, int(ww * 2)), max(2, int(hh * 2))), a0, a0 + math.radians(220), 3 if kk < 2 else 2)
    for kk in range(9):
      a = f * 0.6 + kk * 0.7
      t = kk / 9.0
      y = h - t * h * 0.9 + 14
      w = 10 + t * 30
      pygame.draw.rect(s, (255, 255, 255), (int(50 + math.cos(a) * w) - 1, int(y + math.sin(a) * 3) - 1, 3, 3))
    pygame.draw.ellipse(s, TORNADO_COLS[0] + (120,), (30, h + 10, 40, 10))
    spr = SPRITE_CACHE[k] = pygame.transform.scale(s, (130, int((h + 26) * 1.3)))
  return spr

def blade_stream_sprite(fr):
  k = ("bladestream", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    W, H = 170, 64
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(7 + fr * 5)
    cy = H / 2.0
    for i in range(5):
      x = 16 + ((i * 28 + fr * 7) % 140)
      hh, w = 8 + i * 5, 10 + i * 2
      oy = (i - 2) * 3
      for t, col in ((6, (120, 190, 235)), (4, (200, 236, 255)), (2, (255, 255, 255))):
        pygame.draw.arc(s, col, (int(x - w), int(cy - hh + oy - 1), int(w * 2), int(hh * 2 + 2)), -1.13, 1.13, t)
    for _ in range(22):
      y = cy + rnd.uniform(-24, 24)
      x = rnd.uniform(10, W - 30)
      pygame.draw.line(s, (220, 244, 255), (int(x), int(y)), (int(x + rnd.uniform(8, 22)), int(y)), 1)
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

def acid_pool_sprite(fr):
  """Acid puddle: bubbles grow as they rise, then pop (16-frame loop)."""
  fr %= 16
  k = ("apool2", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (20, 70, 30), (0, 32, 40, 8))
    pygame.draw.ellipse(s, (60, 150, 50), (1, 32, 38, 7))
    pygame.draw.ellipse(s, (130, 225, 60), (3, 33, 34, 5))
    pygame.draw.ellipse(s, (190, 250, 110), (8, 34, 24, 3))
    for j in range(6):
      ph = (fr + j * 5) % 16
      x = 5 + j * 6 + int(math.sin((fr + j * 3) * 0.7) * 1.5)
      y = int(33 - ph * 1.9)
      r = int(round(1 + ph * 0.18))
      if ph < 14:
        pygame.draw.circle(s, (90, 190, 70), (x, y), r)
        pygame.draw.circle(s, (200, 255, 140), (x, y), r, 1)
        s.set_at((x - max(1, r // 2), y - max(1, r // 2)), (255, 255, 255))
      else:
        for a in range(0, 360, 60):
          s.set_at((int(x + math.cos(math.radians(a)) * 3), int(y + math.sin(math.radians(a)) * 3)), (220, 255, 170))
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

def lava_pool_sprite(fr):
  k = ("lpool", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((40, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (40, 22, 18), (0, 14, 40, 8))
    pygame.draw.ellipse(s, (150, 40, 14), (1, 14, 38, 7))
    pygame.draw.ellipse(s, LAVA[2], (3, 15, 34, 5))
    pygame.draw.ellipse(s, LAVA[1], (8, 16, 24, 3))
    for j in range(3):
      s.set_at((7 + j * 11 + fr * 2 % 5, 17), LAVA[0])
    for j in range(4):
      x, h = 6 + j * 9, 6 + ((j + fr) % 3) * 2
      pygame.draw.polygon(s, LAVA[2], [(x - 3, 17), (x, 17 - h), (x + 3, 17)])
      pygame.draw.polygon(s, LAVA[1], [(x - 2, 17), (x, 17 - h + 3), (x + 2, 17)])
      pygame.draw.polygon(s, LAVA[0], [(x - 1, 17), (x, 17 - h + 6), (x + 1, 17)])
    spr = SPRITE_CACHE[k] = _up(s)
  return spr

def dragon_sprite(key, fi, tb, fire):
  ckey = ("pdragon", key, fi, tb, fire)
  spr = SPRITE_CACHE.get(ckey)
  if spr is None:
    pal = DRAGON_PALETTES[key]
    ring = BREATH_BAR.get(key, (255, 150, 0))
    if has_sheet(key):
      sh = sheet(key)
      raw = sh.frame('breath', fi, tb) if fire else sh.frame('fly', fi * sh.count('fly') // 4, tb)
    elif key == "YELLOW":
      raw = hd_frame('YELLOW', fi, tb, fire) or PX.draw_volt_px(pal, fi, tb * 2, fire, beat=fi % 2)
    elif key == "GREEN":
      raw = hd_frame('GREEN', fi, tb, fire) or PX.draw_dart_px(pal, fi, tb * 2, fire, beat=fi % 2)
    elif key == "COSMIC":
      raw = void_frame('breath' if fire else 'fly', fi * 4, tb)
    elif key == "SILVER":
      raw = hd_frame('SILVER', fi, tb, fire) or PX.draw_owl_px(pal, fi, tb * 2, fire, beat=fi % 2)
    elif key == "BLUE":
      raw = hd_frame('BLUE', fi, tb, fire) or PX.draw_crystal_px(pal, fi, tb * 2, fire, beat=fi % 2)
    elif key == "RED":
      raw = hd_frame('RED', fi, tb, fire) or PX.draw_magma_px(fi, tb * 2, fire, beat=fi % 2)
    elif key == "CHINESE":
      raw = PX.draw_serpent_px(pal, fi, fire, ring)
    elif key == "SKELETAL":
      raw = bone_frame('breath' if fire else 'fly', fi * 4, tb)
    else:
      raw = PX.draw_dragon_px(pal, PX.VARIANTS.get(key), fi, tb * 2, fire, ring)
    spr = SPRITE_CACHE[ckey] = ck(raw)
  return spr


def prewarm_dragon(key):
  """Draw every frame of a dragon ahead of time so flying never hitches."""
  try:
    for fi in range(4):
      for tb in range(-2, 3):
        for fire in (False, True):
          dragon_sprite(key, fi, tb, fire)
    for core, dark in ENEMY_COLORS:
      for f in range(0, 12, 3):
        enemy_sprite(core, dark, f)
  except Exception:
    pass


FLAP_REST = {'ALIEN': 0, 'EAGLE': 0, 'WHALE': 0, 'FEY': 0, 'SILVER': 3, 'COCKATRICE': 2, 'GREEN': 2, 'YELLOW': 0, 'FOREST': 2, 'CLOCKWORK': 3, 'CHINESE': 0, 'WRAITH': 7, 'SKELETAL': 3, 'COSMIC': 0, 'RED': 2, 'BLUE': 2, 'UNICORN': 14}   # wings-up frame each flap starts from


def flap_cycle(key):
  """(resting wing phase, length of one full wing beat) for the player's dragon."""
  r = FLAP_REST.get(key)
  if r is not None:
    n = sheet(key).count('fly') if has_sheet(key) else 17
    return (r + 0.05) * 0.76, n * 0.76
  return math.pi / 2, 2 * math.pi                         # pixel-art dragons: sin(wing) peaks with the wings up


def breath_origin(key, d, flap_ph, vel, pitch):
  """where the breath / beam leaves the player's dragon on screen."""
  if key == "UNICORN":                                   # straight from the horn tip, whatever the wings are doing
    sh = sheet(key)
    tb = max(-2, min(2, int(round(int(vel * 0.8) / 6.0))))
    tx, ty = sh.tip(sh.fly_index(flap_ph), tb, fly=True)
    return int(d.x - PX.OX + tx), int(d.y - PX.OY + ty)
  mox, moy = BREATH_MOUTH.get(key, (0, 0))
  return d.x + 92 + mox, d.y + 4 - int(pitch * 0.4) + moy


def draw_any_dragon(surface, key, x, y, tilt, wing, fire=False, flapping=False):
  """Pixel-art dragon. (x, y) is the top-left of the 65x38 hitbox. While a wing beat is playing
  (flapping) the flight frames show even during breath, so every tap flaps the wings."""
  tb = max(-2, min(2, int(round(tilt / 6.0))))
  if fire and ((flapping and key != "WHALE") or key == "UNICORN"):   # (the whale has no wings: its jaws stay open)
    fire = False
  if has_sheet(key):                                     # Magma / Ice / Evil Unicorn: your full flap + breath loops
    sh = sheet(key)
    name = 'breath' if fire else 'fly'
    i = (sh.breath_index() if fire else sh.fly_index(wing)) % sh.count(name)
    k = (key, name, i, tb)
    spr = SPRITE_CACHE.get(k)
    if spr is None:
      spr = SPRITE_CACHE[k] = ck(sh.frame(name, i, tb))
    surface.blit(spr, (int(x) - PX.OX, int(y) - PX.OY))
    return
  if key in ("SKELETAL", "COSMIC"):                      # Bone Reaper / Void Dragon: full 17-frame flap + breath loops
    if key == "COSMIC":
      fire = False                                       # the Void Dragon keeps flapping while it attacks
    i = int(pygame.time.get_ticks() / 70) if fire else (fly_index(wing) if key == "SKELETAL" else void_fly_index(wing))
    k = (key, 'breath' if fire else 'fly', i % (8 if fire else 17), tb)
    spr = SPRITE_CACHE.get(k)
    if spr is None:
      fn = bone_frame if key == "SKELETAL" else void_frame
      spr = SPRITE_CACHE[k] = ck(fn('breath' if fire else 'fly', i, tb))
    surface.blit(spr, (int(x) - PX.OX, int(y) - PX.OY))
    return
  spr = dragon_sprite(key, PX.frame_index(wing), tb, bool(fire))
  surface.blit(spr, (int(x) - PX.OX, int(y) - PX.OY))

def draw_mage(surface, x, y):
  robe_d, robe_m, robe_l = (36, 14, 58), (62, 28, 96), (100, 56, 146)
  pygame.draw.polygon(surface, robe_d, [(x + 15, y + 12), (x + 1, y + 45), (x + 29, y + 45)])
  pygame.draw.polygon(surface, robe_m, [(x + 15, y + 14), (x + 4, y + 44), (x + 26, y + 44)])
  pygame.draw.polygon(surface, robe_l, [(x + 15, y + 15), (x + 11, y + 44), (x + 17, y + 44)])
  pygame.draw.line(surface, GOLD_BORDER, (x + 4, y + 43), (x + 26, y + 43), 2)
  pygame.draw.rect(surface, GOLD_BORDER, (x + 9, y + 26, 12, 3))
  for rx, ry in ((9, 35), (15, 38), (21, 35)):
    pygame.draw.circle(surface, GOLD_BORDER, (x + rx, y + ry), 1)
  pygame.draw.line(surface, WOOD_DARK, (x + 28, y + 6), (x + 30, y + 45), 3)
  pygame.draw.line(surface, WOOD_BROWN, (x + 28, y + 6), (x + 30, y + 45), 1)
  pygame.draw.line(surface, robe_m, (x + 20, y + 18), (x + 27, y + 25), 5)
  pygame.draw.circle(surface, SKIN_COLOR, (x + 28, y + 26), 3)
  pygame.draw.circle(surface, (200, 120, 255), (x + 28, y + 3), 9, 1)
  pygame.draw.circle(surface, MAGIC_PURPLE, (x + 28, y + 3), 6)
  pygame.draw.circle(surface, (255, 255, 255), (x + 28, y + 3), 2)
  pygame.draw.circle(surface, SKIN_COLOR, (x + 14, y + 13), 5)
  pygame.draw.polygon(surface, (225, 225, 235), [(x + 10, y + 15), (x + 14, y + 27), (x + 18, y + 15)])
  pygame.draw.circle(surface, (200, 120, 255), (x + 12, y + 12), 1)
  pygame.draw.circle(surface, (200, 120, 255), (x + 16, y + 12), 1)
  pygame.draw.ellipse(surface, robe_d, (x + 3, y + 7, 22, 7))
  pygame.draw.polygon(surface, robe_m, [(x + 8, y + 9), (x + 15, y - 12), (x + 21, y + 9)])
  pygame.draw.polygon(surface, robe_d, [(x + 15, y - 10), (x + 25, y - 16), (x + 19, y - 5)])
  pygame.draw.line(surface, GOLD_BORDER, (x + 8, y + 8), (x + 21, y + 8), 2)
  pygame.draw.circle(surface, FIRE_CORE, (x + 15, y - 1), 2)

def draw_archer(surface, x, y):
  """(x, y) is the top-left of the 30x45 hitbox."""
  cloak, cloak_d = (52, 98, 58), (30, 66, 40)
  pygame.draw.polygon(surface, WOOD_BROWN, [(x + 20, y + 14), (x + 27, y + 12), (x + 29, y + 30), (x + 22, y + 32)])
  for k in range(3):
    pygame.draw.line(surface, (205, 205, 195), (x + 22 + k * 2, y + 12 - k), (x + 23 + k * 2, y + 17), 1)
  pygame.draw.line(surface, (60, 45, 30), (x + 11, y + 36), (x + 10, y + 45), 4)
  pygame.draw.line(surface, (60, 45, 30), (x + 19, y + 36), (x + 20, y + 45), 4)
  pygame.draw.polygon(surface, cloak_d, [(x + 15, y + 15), (x + 4, y + 42), (x + 26, y + 42)])
  pygame.draw.polygon(surface, cloak, [(x + 15, y + 17), (x + 7, y + 41), (x + 23, y + 41)])
  pygame.draw.rect(surface, WOOD_DARK, (x + 8, y + 28, 14, 3))
  pygame.draw.circle(surface, SKIN_COLOR, (x + 15, y + 12), 6)
  pygame.draw.polygon(surface, cloak_d, [(x + 8, y + 13), (x + 15, y + 1), (x + 22, y + 13), (x + 15, y + 9)])
  pygame.draw.circle(surface, (20, 20, 20), (x + 12, y + 12), 1)
  pygame.draw.arc(surface, WOOD_BROWN, (x - 10, y + 8, 18, 34), math.pi / 2, 3 * math.pi / 2, 3)
  pygame.draw.line(surface, (210, 210, 200), (x - 1, y + 9), (x - 1, y + 41), 1)
  pygame.draw.line(surface, SKIN_COLOR, (x + 12, y + 24), (x + 1, y + 25), 3)

def siege_pose(o, kind):
  """Arm angle (degrees) and whether the stone is still loaded, driven by the unit's own timers."""
  if kind == 'cat':
    rest, cocked, total = -135.0, 20.0, 60.0
  else:
    rest, cocked, total = 146.0, 35.0, 45.0
  if o.get('fired'):
    u = min(1.0, o.get('swing', 0) / 10.0)
    if kind == 'cat':
      return cocked + (rest - cocked) * u, u < 0.5
    return cocked + ((rest - 360.0) - cocked) * u, u < 0.6          # swings up and over the top
  prog = min(1.0, (1.0 - max(0.0, o['timer']) / total) / 0.7)         # winds back, then holds
  return rest + (cocked - rest) * prog, True

def draw_griffin(surface, x, y, anim):
  x, y = int(x), int(y)
  f = math.sin(anim) * 20
  gold, tawny, tawny_d = (214, 168, 52), (196, 150, 70), (140, 98, 40)
  feather, feather_d = (236, 232, 222), (166, 156, 136)
  sx, sy = x + 46, y + 26

  def wing(ox, oy, length, col_a, col_b):
    for i in range(5):
      th = math.radians(-165 + i * 26 + f * 1.1)
      ln = length - abs(i - 2) * 4
      ca, sa = math.cos(th), math.sin(th)
      tipx, tipy = sx + ox + ca * ln, sy + oy + sa * ln
      px, py = -sa, ca
      quad = [(sx + ox + px * 4, sy + oy + py * 4), (tipx + px * 6, tipy + py * 6), (tipx - px * 6, tipy - py * 6), (sx + ox - px * 4, sy + oy - py * 4)]
      pygame.draw.polygon(surface, col_a if i % 2 == 0 else col_b, quad)
      pygame.draw.line(surface, tawny_d, (sx + ox, sy + oy), (tipx, tipy), 1)

  wing(10, -2, 52, feather_d, darken(feather_d, 0.8))                       # far wing
  for k in range(4):                                                         # tail tuft
    pygame.draw.polygon(surface, tawny_d, [(x + 74, y + 40), (x + 98 + k * 3, y + 30 + k * 8), (x + 80, y + 50)])
  pygame.draw.ellipse(surface, tawny_d, (x + 18, y + 18, 64, 44))           # lion hindquarters
  pygame.draw.ellipse(surface, tawny, (x + 20, y + 20, 60, 40))
  pygame.draw.ellipse(surface, lighten(tawny, 30), (x + 30, y + 24, 36, 10))
  for lx in (x + 58, x + 70):                                                # hind legs
    pygame.draw.line(surface, tawny_d, (lx, y + 52), (lx - 3, y + 68), 7)
    pygame.draw.line(surface, tawny, (lx, y + 52), (lx - 3, y + 68), 4)
    for k in range(3):
      pygame.draw.line(surface, BONE_WHITE, (lx - 3, y + 68), (lx - 9 + k * 3, y + 74), 2)
  pygame.draw.ellipse(surface, feather_d, (x - 2, y + 8, 44, 34))           # eagle foreparts
  pygame.draw.ellipse(surface, feather, (x, y + 10, 40, 30))
  for k in range(5):
    pygame.draw.arc(surface, feather_d, (x + 8 + k * 5, y + 24 + (k % 2) * 4, 10, 8), math.pi, 2 * math.pi, 1)
  for k in range(2):                                                         # front talons
    tx0 = x + 14 + k * 8
    pygame.draw.line(surface, gold, (tx0, y + 38), (tx0 - 6, y + 52), 5)
    for c in range(3):
      pygame.draw.line(surface, BONE_WHITE, (tx0 - 6, y + 52), (tx0 - 12 + c * 3, y + 58), 2)
  for k in range(3):                                                         # crest
    pygame.draw.polygon(surface, feather_d, [(x + 10 + k * 5, y + 12), (x + 6 + k * 7, y - 6 - k * 2), (x + 16 + k * 5, y + 12)])
  pygame.draw.polygon(surface, gold, [(x - 2, y + 20), (x - 22, y + 27), (x - 4, y + 37)])   # beak
  pygame.draw.polygon(surface, tawny_d, [(x - 22, y + 27), (x - 19, y + 36), (x - 13, y + 33)])
  pygame.draw.line(surface, tawny_d, (x - 4, y + 29), (x - 18, y + 28), 1)
  pygame.draw.circle(surface, (255, 205, 40), (x + 8, y + 20), 5)
  pygame.draw.circle(surface, (0, 0, 0), (x + 7, y + 20), 2)
  pygame.draw.line(surface, tawny_d, (x + 1, y + 15), (x + 14, y + 18), 2)
  cape = [(x + 50, y + 8), (x + 74, y + 20), (x + 66, y + 38), (x + 50, y + 26)]  # rider
  pygame.draw.polygon(surface, CLOTH_RED, cape)
  pygame.draw.polygon(surface, darken(CLOTH_RED, 0.7), cape, 1)
  pygame.draw.rect(surface, (150, 156, 168), (x + 49, y + 4, 10, 16), border_radius=2)
  pygame.draw.line(surface, GOLD_BORDER, (x + 49, y + 12), (x + 59, y + 12), 2)
  pygame.draw.circle(surface, SKIN_COLOR, (x + 54, y - 1), 5)
  pygame.draw.polygon(surface, (150, 156, 168), [(x + 48, y), (x + 54, y - 9), (x + 60, y)])
  pygame.draw.polygon(surface, CLOTH_RED, [(x + 54, y - 9), (x + 63, y - 14), (x + 58, y - 5)])
  pygame.draw.line(surface, WOOD_BROWN, (x + 58, y + 8), (x - 26, y + 2), 3)  # lance
  pygame.draw.polygon(surface, STONE_LIGHT, [(x - 26, y + 2), (x - 38, y + 3), (x - 26, y + 6)])
  pygame.draw.polygon(surface, CLOTH_BLUE, [(x - 12, y + 3), (x - 4, y + 11), (x - 4, y + 3)])
  wing(0, 0, 58, feather, lighten(feather_d, 25))                            # near wing

def draw_zeppelin(surface, x, y, anim):
  bob = int(math.sin(anim) * 5)
  x, y = int(x), int(y) + bob
  hull_d, hull_m, hull_l = (36, 52, 34), (62, 84, 52), (98, 122, 80)
  pygame.draw.polygon(surface, hull_d, [(x + 135, y + 22), (x + 172, y - 8), (x + 168, y + 34)])
  pygame.draw.polygon(surface, hull_d, [(x + 135, y + 58), (x + 172, y + 88), (x + 168, y + 46)])
  pygame.draw.ellipse(surface, hull_d, (x - 2, y - 2, 164, 84))
  pygame.draw.ellipse(surface, hull_m, (x, y, 160, 80))
  pygame.draw.ellipse(surface, hull_l, (x + 14, y + 6, 120, 22))
  for k in range(1, 7):
    sx = x + k * 22
    half = int(math.sqrt(max(0.0, 1 - ((sx - (x + 80)) / 80.0) ** 2)) * 38)
    pygame.draw.line(surface, hull_d, (sx, y + 40 - half), (sx, y + 40 + half), 1)
    pygame.draw.circle(surface, hull_l, (sx, y + 40 - half + 4), 1)
    pygame.draw.circle(surface, hull_l, (sx, y + 40 + half - 4), 1)
  pygame.draw.line(surface, hull_d, (x + 6, y + 40), (x + 154, y + 40), 1)
  pygame.draw.line(surface, IRON_GRAY, (x + 80, y), (x + 80, y - 20), 2)
  pygame.draw.polygon(surface, CLOTH_RED, [(x + 80, y - 20), (x + 100 + int(math.sin(anim * 3) * 3), y - 15), (x + 80, y - 10)])
  for rx in (x + 50, x + 80, x + 110):
    pygame.draw.line(surface, (110, 100, 90), (rx, y + 76), (rx, y + 90), 2)
  pygame.draw.rect(surface, WOOD_DARK, (x + 38, y + 88, 84, 32), border_radius=6)
  pygame.draw.rect(surface, WOOD_BROWN, (x + 41, y + 91, 78, 26), border_radius=5)
  for k in range(4):
    pygame.draw.rect(surface, (255, 210, 110), (x + 48 + k * 17, y + 98, 10, 9))
    pygame.draw.rect(surface, WOOD_DARK, (x + 48 + k * 17, y + 98, 10, 9), 1)
  pygame.draw.rect(surface, STONE_DARK, (x + 14, y + 105, 12, 10), border_radius=3)
  pygame.draw.rect(surface, IRON_GRAY, (x + 22, y + 106, 22, 8), border_radius=3)
  px, py = x + 164, y + 40
  pygame.draw.circle(surface, IRON_GRAY, (px, py), 6)
  for a in range(3):
    ang = anim * 9 + a * 2.094
    pygame.draw.line(surface, (200, 200, 205), (px, py), (px + int(math.cos(ang) * 18), py + int(math.sin(ang) * 18)), 3)
  pygame.draw.circle(surface, STONE_LIGHT, (px, py), 2)

def draw_stasis(surface, r):
  """Gold/cyan clock ring drawn over anything frozen in time by the Chrono Wyrm."""
  cx, cy = r.center
  rad = max(16, min(r.w, r.h) // 2 + 8)
  a = pygame.time.get_ticks() * 0.004
  pygame.draw.circle(surface, (255, 220, 120), (cx, cy), rad, 2)
  pygame.draw.circle(surface, (120, 230, 255), (cx, cy), rad - 5, 1)
  pygame.draw.line(surface, (255, 220, 120), (cx, cy), (int(cx + math.cos(a) * rad * 0.8), int(cy + math.sin(a) * rad * 0.8)), 2)
  pygame.draw.line(surface, (120, 230, 255), (cx, cy), (int(cx + math.cos(a * 0.2) * rad * 0.55), int(cy + math.sin(a * 0.2) * rad * 0.55)), 3)

def build_wisp():
  w = pygame.Surface((240, 70))
  w.fill(KEY)
  for i, c in enumerate(((120, 128, 140), (140, 148, 160), (160, 168, 180))):
    pygame.draw.ellipse(w, c, (i * 24, 8 + i * 8, 240 - i * 48, 54 - i * 16))
  w = w.convert()
  w.set_colorkey(KEY, pygame.RLEACCEL)
  w.set_alpha(70)
  return w

WYVERN_COLORS = [((92, 118, 44), (48, 64, 22), (214, 196, 130)), ((176, 86, 34), (96, 40, 16), (232, 200, 140))]

def draw_wyvern(surface, x, y, wing, col):
  """Small two-legged wyvern facing right; (x, y) is its 40x24 hitbox top-left."""
  main_c, dark_c, belly_c = col
  f = int(math.sin(wing) * 11)
  pygame.draw.polygon(surface, dark_c, [(x + 18, y + 8), (x + 6, y - 14 + f), (x + 24, y - 10 + f), (x + 32, y + 6)])      # far wing
  pygame.draw.polygon(surface, dark_c, [(x + 8, y + 14), (x - 12, y + 24), (x + 8, y + 19)])                              # tail
  pygame.draw.polygon(surface, main_c, [(x + 8, y + 14), (x - 6, y + 21), (x + 8, y + 18)])
  pygame.draw.polygon(surface, dark_c, [(x - 10, y + 20), (x - 17, y + 17), (x - 15, y + 27)])                            # barb
  pygame.draw.line(surface, dark_c, (x + 17, y + 20), (x + 14, y + 29), 3)                                                # legs
  pygame.draw.line(surface, BONE_WHITE, (x + 14, y + 29), (x + 10, y + 31), 1)
  pygame.draw.ellipse(surface, dark_c, (x + 4, y + 6, 32, 17))
  pygame.draw.ellipse(surface, main_c, (x + 6, y + 8, 28, 13))
  pygame.draw.ellipse(surface, belly_c, (x + 14, y + 16, 18, 5))
  pygame.draw.polygon(surface, main_c, [(x + 30, y + 10), (x + 36, y + 2), (x + 40, y + 4), (x + 34, y + 14)])            # neck
  pygame.draw.ellipse(surface, dark_c, (x + 33, y - 1, 17, 11))
  pygame.draw.ellipse(surface, main_c, (x + 34, y, 15, 9))
  pygame.draw.polygon(surface, dark_c, [(x + 35, y + 1), (x + 30, y - 6), (x + 40, y)])                                   # horn
  pygame.draw.circle(surface, (255, 60, 40), (x + 41, y + 3), 2)
  pygame.draw.line(surface, BONE_WHITE, (x + 44, y + 7), (x + 48, y + 6), 1)
  pygame.draw.polygon(surface, main_c, [(x + 20, y + 8), (x + 8, y - 20 + f), (x + 30, y - 16 + f), (x + 38, y + 6)])     # near wing
  pygame.draw.line(surface, BONE_WHITE, (x + 20, y + 8), (x + 8, y - 20 + f), 2)
  pygame.draw.line(surface, BONE_WHITE, (x + 20, y + 8), (x + 30, y - 16 + f), 2)

def wyvern_sprite(variant, frame):
  key = ("wyvern", variant, frame)
  spr = SPRITE_CACHE.get(key)
  if spr is None:
    s_ = pygame.Surface((84, 64), pygame.SRCALPHA)
    draw_wyvern(s_, 22, 22, frame * (2 * math.pi / 6), WYVERN_COLORS[variant])
    spr = SPRITE_CACHE[key] = ck(pygame.transform.flip(s_, True, False))
  return spr

def draw_coin(surface, x, y):
  img = coin_img(0)                                    # ruby-set gold coin (fd_items)
  surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))

def build_sky():
  s = pygame.Surface((WIDTH, HEIGHT))
  for y in range(HEIGHT):
    t = y / HEIGHT
    c = [DUSK_TOP[i] * (1 - t) + DUSK_BOTTOM[i] * t for i in range(3)]
    g = max(0.0, (t - 0.6) / 0.4) ** 2          # warm horizon glow
    c[0] += 75 * g; c[1] += 30 * g; c[2] += 8 * g
    pygame.draw.line(s, tuple(min(255, int(v)) for v in c), (0, y), (WIDTH, y))
  rng = random.Random(7)
  for _ in range(110):
    b = rng.randint(110, 255)
    pygame.draw.circle(s, (b, b, min(255, b + 15)), (rng.randint(0, WIDTH), rng.randint(0, 380)), rng.choice((1, 1, 1, 2)))
  return s.convert()

def build_moon():
  s = pygame.Surface((240, 240), pygame.SRCALPHA)
  c = (120, 120)
  for r in range(115, 55, -3):
    pygame.draw.circle(s, (255, 250, 215, int(46 * (1 - (r - 55) / 60) ** 1.6) + 2), c, r)
  pygame.draw.circle(s, MOON_LIGHT, c, 55)
  for (ox, oy, r) in [(-20, 18, 12), (14, -14, 8), (22, 22, 6), (-12, -24, 5), (0, 4, 4)]:
    pygame.draw.circle(s, MOON_SHADOW, (c[0] + ox, c[1] + oy), r)
    pygame.draw.circle(s, (200, 195, 175), (c[0] + ox, c[1] + oy), r, 1)
  return s.convert_alpha()

DAY_LIFT = (46, 56, 62)          # added over the dusk scenery to turn it into daylight
DAY = {'ok': None, 'sky': None, 'sun': None}

def ensure_day_assets():
  """Builds the daytime sky and sun the first time they are needed. Returns False if anything goes wrong."""
  if DAY['ok'] is None:
    try:
      sk = pygame.Surface((WIDTH, HEIGHT))
      top, bot = (34, 96, 176), (146, 172, 190)
      for y in range(HEIGHT):
        t = y / float(HEIGHT)
        pygame.draw.line(sk, tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)), (0, y), (WIDTH, y))
      su = pygame.Surface((240, 240), pygame.SRCALPHA)
      for r in range(115, 45, -3):
        pygame.draw.circle(su, (255, 240, 160, int(50 * (1 - (r - 45) / 70.0) ** 1.6) + 2), (120, 120), r)
      pygame.draw.circle(su, (255, 246, 200), (120, 120), 46)
      pygame.draw.circle(su, (255, 255, 235), (120, 120), 34)
      DAY['sky'], DAY['sun'] = sk.convert(), su.convert_alpha()
      DAY['ok'] = True
    except Exception:
      DAY['ok'] = False
  return DAY['ok']

def build_ridge(h, peak, valley, amps, color, edge, seed, smooth=False):
  """Seamlessly tiling mountain/hill strip, normalised to [peak, valley] in layer coords."""
  rng = random.Random(seed)
  ph = [rng.uniform(0, 6.28) for _ in amps]
  xs = range(0, WIDTH + 1, 4)
  raw = []
  for x in xs:
    v = 0.0
    for (f, a), p in zip(amps, ph):
      v += a * ((0.5 + 0.5 * math.sin(2 * math.pi * f * x / WIDTH + p)) if smooth else (1 - abs(math.sin(math.pi * f * x / WIDTH + p))))
    raw.append(-v)
  lo, hi = min(raw), max(raw)
  ys = [peak + (v - lo) / (hi - lo) * (valley - peak) for v in raw]
  s = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
  pts = [(x, y) for x, y in zip(xs, ys)]
  pygame.draw.polygon(s, color, pts + [(WIDTH, h), (0, h)])
  pygame.draw.lines(s, edge, False, pts, 2)
  return s, ys

def build_far_layer():
  s, ys = build_ridge(350, 75, 200, [(2, 200), (3, 80), (7, 30)], MOUNTAIN_FAR, (34, 38, 62), 3)
  x0 = 560
  seg = ys[x0 // 4:(x0 + 96) // 4]
  top, bot = min(seg), max(seg)
  col = (11, 12, 20)
  pygame.draw.rect(s, col, (x0 + 24, top - 46, 48, bot - top + 50))
  for i in range(4):
    pygame.draw.rect(s, col, (x0 + 24 + i * 13, top - 54, 9, 8))
  for tx in (x0 + 4, x0 + 72):
    pygame.draw.rect(s, col, (tx, top - 30, 18, bot - top + 40))
    pygame.draw.polygon(s, col, [(tx - 3, top - 30), (tx + 9, top - 56), (tx + 21, top - 30)])
  for wx, wy in [(x0 + 40, top - 30), (x0 + 54, top - 14), (x0 + 10, top - 12), (x0 + 78, top - 10), (x0 + 36, top + 2)]:
    pygame.draw.rect(s, (255, 190, 80), (wx, wy, 4, 7))
  return ck(s)

def build_clouds():
  out = []
  for w in (110, 150, 200):
    h = int(w * 0.5)
    c = pygame.Surface((w, h))
    c.fill(KEY)
    for fx, fy, fr in [(0.25, 0.62, 0.2), (0.45, 0.45, 0.26), (0.68, 0.58, 0.22), (0.85, 0.7, 0.15)]:
      pygame.draw.circle(c, (42, 36, 58), (int(w * fx), int(h * fy)), int(w * fr))
    for fx, fy, fr in [(0.45, 0.38, 0.18), (0.68, 0.5, 0.14)]:
      pygame.draw.circle(c, (62, 52, 78), (int(w * fx), int(h * fy)), int(w * fr))
    c = c.convert()
    c.set_colorkey(KEY, pygame.RLEACCEL)
    c.set_alpha(170)
    out.append(c)
  return out

def build_ground():
  s = pygame.Surface((WIDTH, GROUND_H))
  for y in range(GROUND_H):
    t = y / GROUND_H
    pygame.draw.line(s, (int(64 - 32 * t), int(46 - 24 * t), int(30 - 15 * t)), (0, y), (WIDTH, y))
  rng = random.Random(5)
  for _ in range(22):
    x, y = rng.randint(0, WIDTH), rng.randint(13, GROUND_H - 7)
    w, h = rng.randint(10, 20), rng.randint(6, 9)
    pygame.draw.ellipse(s, (92, 90, 96), (x, y, w, h))
  for _ in range(90):
    c = rng.choice(((84, 64, 44), (44, 32, 22), (100, 92, 82)))
    pygame.draw.circle(s, c, (rng.randint(0, WIDTH), rng.randint(9, GROUND_H - 2)), rng.randint(1, 2))
  pygame.draw.rect(s, (30, 78, 34), (0, 0, WIDTH, 8))
  pygame.draw.rect(s, (20, 56, 24), (0, 5, WIDTH, 3))
  pygame.draw.line(s, GOLD_BORDER, (0, 0), (WIDTH, 0), 3)
  return s.convert()

def build_vignette():
  sw, sh = 200, 150
  s = pygame.Surface((sw, sh), pygame.SRCALPHA)
  for y in range(sh):
    for x in range(sw):
      d = math.hypot((x / sw - 0.5) * 2, (y / sh - 0.5) * 2)
      a = int(170 * max(0.0, (d - 0.55) / 0.9) ** 1.5)
      s.set_at((x, y), (0, 0, 0, min(a, 200)))
  return pygame.transform.smoothscale(s, (WIDTH, HEIGHT)).convert_alpha()

def build_mist():
  m = pygame.Surface((60, 18))
  m.fill(KEY)
  pygame.draw.ellipse(m, (80, 74, 96), m.get_rect())
  pygame.draw.ellipse(m, (96, 90, 114), (10, 4, 40, 9))
  m = m.convert()
  m.set_colorkey(KEY, pygame.RLEACCEL)
  m.set_alpha(80)
  return m

SKY = build_sky()
MOON = build_moon()
FAR_LAYER = build_far_layer()
_ns, _nys = build_ridge(270, 40, 170, [(2, 160), (4, 60), (8, 22)], MOUNTAIN_NEAR, (50, 54, 78), 11)
ENV.decorate_peaks(_ns, _nys)
NEAR_LAYER = ck(_ns)
_hs, _hys = build_ridge(170, 0, 45, [(3, 40), (5, 18), (8, 8)], HILL_MID, HILL_MID_LIGHT, 21, smooth=True)
ENV.decorate_hills(_hs, _hys)
HILL_LAYER = ck(_hs)
CLOUDS = build_clouds()
GROUND = ENV.build_ground()
VIGNETTE = build_vignette()
MIST = build_mist()
try:
  WISP = build_wisp()
except Exception:
  WISP = None

ENV.build_all()
ENV.menu_art()

# ------------------------------------------------------------------ Fantasy Forest tileset (user art)
from fd_forest import forest_img, forest_size

DUSK_MAP = {
  'rockmt': {(101, 115, 146): (30, 32, 50), (146, 161, 185): (70, 74, 106)},
  'grassmt': {(19, 76, 76): (14, 22, 28), (30, 111, 80): (20, 34, 36), (51, 152, 75): (34, 56, 48)},
  'clouds': {(199, 207, 221): (36, 32, 54), (255, 255, 255): (54, 48, 76)},
}

def _dusk(name):
  m = DUSK_MAP[name]
  return lambda c: m.get(c, (int(c[0] * 0.3), int(c[1] * 0.3), int(c[2] * 0.36)))

def _scenery_tint(c):
  return (int(c[0] * 0.64) + 8, int(c[1] * 0.64) + 6, int(c[2] * 0.68) + 18)

def forest_layer(name, top_y, bottom_y):
    """One of the pack's parallax layers at 2x, cropped to its art, tinted for dusk, tiled to a width that wraps
    seamlessly (a multiple of 640) and extended down so it always reaches bottom_y."""
    src = forest_img(name, 2, _dusk(name), 'dusk')
    w, h = src.get_size()
    first = h
    for y in range(h):
      if any(src.get_at((x, y))[3] for x in range(0, w, 3)):
        first = y
        break
    art = src.subsurface((0, first, w, h - first))
    lw = w * max(1, -(-WIDTH // w))
    lh = max(art.get_height(), bottom_y - top_y)
    lay = pygame.Surface((lw, lh), pygame.SRCALPHA)
    for k in range(lw // w):
      piece = art if k % 2 == 0 or name == 'clouds' else pygame.transform.flip(art, True, False)
      lay.blit(piece, (k * w, 0))
    if lh > art.get_height():                       # extend the bottom row down to the ground
      row = lay.subsurface((0, art.get_height() - 1, lw, 1)).copy()
      for y in range(art.get_height(), lh):
        lay.blit(row, (0, y))
    return lay

def bank_layer(top_y, bottom_y):
  """Only the long cloud bank from the pack's cloud art (the separate clouds drift on their own)."""
  src = forest_img('clouds', 1, _dusk('clouds'), 'dusk')
  w, h = src.get_size()
  keep = set()
  stack = [(x, h - 1) for x in range(w) if src.get_at((x, h - 1))[3]]
  keep.update(stack)
  while stack:
    x, y = stack.pop()
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
      nx %= w
      if 0 <= ny < h and (nx, ny) not in keep and src.get_at((nx, ny))[3]:
        keep.add((nx, ny))
        stack.append((nx, ny))
  y0 = min(p[1] for p in keep)
  b = pygame.Surface((w, h - y0), pygame.SRCALPHA)
  for x, y in keep:
    b.set_at((x, y - y0), src.get_at((x, y)))
  b = pygame.transform.scale(b, (w * 2, (h - y0) * 2))
  lw = b.get_width() * max(1, -(-WIDTH // b.get_width()))
  lay = pygame.Surface((lw, max(b.get_height(), bottom_y - top_y)), pygame.SRCALPHA)
  for k in range(lw // b.get_width()):
    lay.blit(b, (k * b.get_width(), 0))
  return lay

def _put_castle(lay):
  lw = lay.get_width()
  tops = []
  for x in range(0, lw, 4):
    t = lay.get_height()
    for y in range(lay.get_height()):
      if lay.get_at((x, y))[3]:
        t = y
        break
    tops.append(t)
  best = min(range(len(tops) // 4, len(tops) * 3 // 4), key=lambda i: tops[i])
  x0 = best * 4 - 48
  seg = tops[max(0, (x0) // 4):(x0 + 96) // 4]
  top, bot = min(seg), max(seg)
  col = (11, 12, 20)
  pygame.draw.rect(lay, col, (x0 + 24, top - 46, 48, bot - top + 56))
  for i in range(4):
    pygame.draw.rect(lay, col, (x0 + 24 + i * 13, top - 54, 9, 8))
  for tx in (x0 + 4, x0 + 72):
    pygame.draw.rect(lay, col, (tx, top - 30, 18, bot - top + 46))
    pygame.draw.polygon(lay, col, [(tx - 3, top - 30), (tx + 9, top - 56), (tx + 21, top - 30)])
  pygame.draw.line(lay, col, (x0 + 13, top - 56), (x0 + 13, top - 70), 2)
  pygame.draw.polygon(lay, (130, 30, 30), [(x0 + 13, top - 70), (x0 + 25, top - 66), (x0 + 13, top - 62)])
  for wx, wy in [(x0 + 40, top - 30), (x0 + 54, top - 14), (x0 + 10, top - 12), (x0 + 78, top - 10), (x0 + 36, top + 2)]:
    pygame.draw.rect(lay, (255, 190, 80), (wx, wy, 4, 7))

def _cloud_pieces():
  """Split the pack's cloud art into its separate clouds, in three depth tints and two sizes."""
  src = forest_img('clouds', 1)
  w, h = src.get_size()
  seen = set()
  pieces = []
  for y0 in range(0, 200):
    for x0 in range(w):
      if (x0, y0) in seen or not src.get_at((x0, y0))[3]:
        continue
      stack, pts = [(x0, y0)], []
      seen.add((x0, y0))
      while stack:
        x, y = stack.pop()
        pts.append((x, y))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
          nx %= w
          if 0 <= ny < h and (nx, ny) not in seen and src.get_at((nx, ny))[3]:
            seen.add((nx, ny))
            stack.append((nx, ny))
      if len(pts) < 150 or max(p[1] for p in pts) >= 200:
        continue
      xs = [p[0] for p in pts]
      wrap = min(xs) == 0 and max(xs) == w - 1
      sx = [x + w if wrap and x < w // 2 else x for x in xs]
      bx, by = min(sx), min(p[1] for p in pts)
      pc = pygame.Surface((max(sx) - bx + 1, max(p[1] for p in pts) - by + 1), pygame.SRCALPHA)
      for (x, y), xx in zip(pts, sx):
        pc.set_at((xx - bx, y - by), src.get_at((x, y)))
      pieces.append(pc)
  out = []
  tints = (((199, 207, 221), (255, 255, 255)), )
  for depth, (lo, hi) in enumerate((((40, 34, 58), (58, 50, 80)), ((52, 45, 72), (72, 63, 96)), ((64, 56, 86), (88, 78, 112)))):
    for pc in pieces:
      t = pc.copy()
      arr = pygame.PixelArray(t) if hasattr(pygame, 'PixelArray') else None
      if arr is not None:
        arr.replace((199, 207, 221), lo)
        arr.replace((255, 255, 255), hi)
        del arr
      sc = (1, 1.5, 2)[depth]
      out.append(pygame.transform.scale(t, (int(t.get_width() * sc), int(t.get_height() * sc))))
  return out

def build_forest_ground():
  s = pygame.Surface((WIDTH, GROUND_H), pygame.SRCALPHA)
  rng = random.Random(11)
  for x in range(0, WIDTH, 32):
    s.blit(forest_img('ground%d' % rng.randint(0, 3), 2), (x, 0))
  return s.convert_alpha()

def _mild_tint(c):
  return (int(c[0] * 0.82) + 4, int(c[1] * 0.82) + 3, int(c[2] * 0.84) + 10)

BANK_LAYER = None                              # (the pack's background layers are not used: the original land stays)
FOREST_OK = False
try:                                           # extra ground scenery from the Fantasy Forest pack
  for _k, _n in (("pgrass0", 'grass0'), ("pgrass1", 'grass1'), ("pgrass2", 'grass2'), ("tuft", 'tuft'), ("mushroom", 'mushroom'),
                 ("boulder0", 'rock0'), ("boulder1", 'rock1'), ("pebble", 'rock2'), ("vase", 'pot'), ("crate", 'crate1'), ("crate2", 'crate0'),
                 ("pbush", 'bush'), ("fern", 'fern0'), ("twig", 'sapling'), ("sprout", 'sprout0'), ("fence", 'fence')):
    _spr = forest_img(_n, 2, _mild_tint, 'mild')
    SPRITE_CACHE[_k] = (_spr, _spr.get_width() // 2, _spr.get_height() - 4)
  FOREST_OK = True
except Exception:
  pass

def bonfire_sprite(fr):
  return forest_img('fire%d' % (fr % 6), 2)

def coin_sprite(fr=0):
  return coin_img(fr)

def powerup_sprite(fr=0):
  return crystal_img(fr)                               # fire crystal (fd_items)

ENEMY_OX = (PX.CW - PX.AX) * PX.S - 65      # where the 65x38 hitbox sits inside the flipped enemy sprite
ENEMY_OY = PX.AY * PX.S


def enemy_sprite(core, dark, frame):
  fi = PX.frame_index(frame * (2 * math.pi / 12))
  key = ("enemy", core, dark, fi)
  spr = SPRITE_CACHE.get(key)
  if spr is None:
    pal = {'main': core, 'dark': dark, 'belly': (205, 195, 170), 'eye': (255, 60, 40), 'title': ''}
    raw = PX.draw_dragon_px(pal, None, fi, 0, False, (255, 150, 0))
    spr = SPRITE_CACHE[key] = ck(pygame.transform.flip(raw, True, False))
  return spr

def ice_sprite(w, h):
  key = ("ice", w, h)
  s = SPRITE_CACHE.get(key)
  if s is None:
    s = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    pygame.draw.rect(s, (150, 230, 255, 140), s.get_rect(), border_radius=6)
    pygame.draw.rect(s, (200, 255, 255, 200), s.get_rect(), 2, border_radius=6)
    pygame.draw.line(s, (255, 255, 255, 160), (6, 6), (w // 2, h // 3), 2)
    pygame.draw.polygon(s, (255, 255, 255, 90), [(4, 4), (w // 2, 4), (4, h // 2)])
    pygame.draw.polygon(s, (90, 160, 220, 90), [(w + 6, h + 6), (w // 2, h + 6), (w + 6, h // 2)])
    pygame.draw.line(s, (255, 255, 255, 140), (w - 4, 8), (w - 12, 14), 2)
    s = SPRITE_CACHE[key] = s.convert_alpha()
  return s

def acid_sprite(w, h, variant):
  key = ("acid", w, h, variant)
  s = SPRITE_CACHE.get(key)
  if s is None:
    rng = random.Random(variant * 31 + w)
    s = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    pygame.draw.rect(s, (100, 255, 50, 120), s.get_rect(), border_radius=6)
    for _ in range(4):
      pygame.draw.circle(s, (50, 200, 20, 180), (rng.randint(5, max(6, w)), rng.randint(5, max(6, h))), rng.randint(3, 6))
    s = SPRITE_CACHE[key] = s.convert_alpha()
  return s

def shield_sprite(sr):
  key = ("shield", sr)
  s = SPRITE_CACHE.get(key)
  if s is None:
    s = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (150, 220, 255, 90), (sr, sr), sr)
    pygame.draw.circle(s, (200, 255, 255, 200), (sr, sr), sr, 3)
    s = SPRITE_CACHE[key] = s.convert_alpha()
  return s

def red_shield_sprite(sr):
  key = ("rshield", sr)
  s = SPRITE_CACHE.get(key)
  if s is None:
    s = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 90, 70, 90), (sr, sr), sr)
    pygame.draw.circle(s, (255, 200, 150, 210), (sr, sr), sr, 4)
    s = SPRITE_CACHE[key] = s.convert_alpha()
  return s

def build_tower(h, banner):
  """Pre-render a whole tower (crenellations + body) once, at spawn."""
  w = TOWER_WIDTH
  s = pygame.Surface((w, h + 15), pygame.SRCALPHA)
  body = pygame.Rect(0, 15, w, h)
  pygame.draw.rect(s, STONE_DARK, body)
  pygame.draw.rect(s, STONE_WALL, (5, 15, w - 10, h))
  pygame.draw.rect(s, STONE_LIGHT, (w - 22, 15, 10, h))              # lit edge
  pygame.draw.rect(s, STONE_DARK, (5, 15, 10, h))                    # shaded edge
  for i, y in enumerate(range(30, h + 15, 26)):
    pygame.draw.line(s, STONE_DARK, (0, y), (w, y), 2)
    off = 14 if i % 2 else 0
    for bx in range(off + 10, w, 28):
      pygame.draw.line(s, STONE_DARK, (bx, y), (bx, y + 26), 1)
  for _ in range(12):
    bx, by = random.randint(6, w - 26), random.randint(20, max(21, h - 10))
    pygame.draw.rect(s, (75, 79, 84), (bx, by, random.randint(14, 24), 9))
  pygame.draw.rect(s, banner, (w // 2 - 12, 35, 24, 45))
  pygame.draw.polygon(s, banner, [(w // 2 - 12, 80), (w // 2, 93), (w // 2 + 12, 80)])
  pygame.draw.circle(s, lighten(banner, 60), (w // 2, 52), 5)
  if h > 230:                                                        # arrow slit with a warm glow
    pygame.draw.rect(s, (255, 170, 60), (w // 2 - 3, 120, 6, 22), border_radius=3)
    pygame.draw.rect(s, STONE_DARK, (w // 2 - 5, 118, 10, 26), 2, border_radius=4)
  for _ in range(4):                                                 # ivy
    ix, iy = random.randint(8, w - 8), h + 15 - random.randint(10, 90)
    for k in range(random.randint(3, 6)):
      pygame.draw.circle(s, IVY_GREEN, (ix + random.randint(-4, 4), iy - k * 6), random.randint(3, 5))
  for i in range(5):
    if i % 2 == 0:
      pygame.draw.rect(s, STONE_WALL, (i * 19, 0, 19, 15))
      pygame.draw.rect(s, STONE_DARK, (i * 19, 0, 19, 15), 1)
  return ck(s)

from fd_boss import draw_griffin, draw_griffin_boss, draw_feather, WING_PTS, griffin_frames, griffin_beak
griffin_frames()


def unit_anchor(name, o):
  """(anim kind, x, y): where an enemy's frame top-left goes (same spot the old single-animation art used)."""
  r = o['rect']
  if name == 'archers':
    return 'satyr', r.centerx - 24, r.bottom + 3 - 56
  if name == 'mages':
    mk = o.get('kind', 'skel')
    w, h = EA_KINDS[mk]['osize']
    return mk, r.centerx - w // 2, r.bottom + 4 - h
  if name == 'enemies':
    if o.get('kind') == 'wyvern':
      return 'eye', r.x - 8, r.y - 8
    foe = o.get('foe')
    if foe == 'imp':
      return 'imp', r.x - 2, r.y - 1
    if foe == 'garg':
      return 'garg', r.x - 12, r.y - 14
    if foe in (None, 'harpy') and o.get('kind') is None:
      return 'harpy', r.x - 7, r.y - 10
  return None

MAGE_ATTACK = {'pyro': 'ATTACK', 'wiz': 'RANGED_ATTACK', 'skel': 'ATTACK'}


# ---------------------------------------------------------------- Evil Unicorn: rainbow beam
BEAM_TILE = 48          # the beam's ripple repeats every 48 px, so one tile scrolls forever


def _beam_tile(fr):
  k = ("rbeam", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    W, H = BEAM_TILE * 2, 44
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    cy = H / 2.0
    n = len(RAINBOW)
    for x in range(W):
      ph = (x + fr * 6) / float(BEAM_TILE) * math.tau
      h = 13 + 2.2 * math.sin(ph)                                   # the beam swells as it pulses
      pygame.draw.line(s, (255, 200, 255, 50), (x, int(cy - h - 5)), (x, int(cy + h + 5)))
      pygame.draw.line(s, (255, 220, 255, 90), (x, int(cy - h - 2)), (x, int(cy + h + 2)))
      for b in range(n):
        y0 = cy - h + 2 * h * b / n
        y1 = cy - h + 2 * h * (b + 1) / n
        c = RAINBOW[b]
        lit = 0.25 + 0.25 * math.sin(ph * 2 + b * 0.6)              # light rolling along the bands
        c = tuple(min(255, int(v + (255 - v) * lit)) for v in c)
        pygame.draw.line(s, c, (x, int(y0)), (x, max(int(y0), int(y1) - 1)))
      core = 2.5 + 0.8 * math.sin(ph)
      pygame.draw.line(s, (255, 255, 255, 210), (x, int(cy - core)), (x, int(cy + core)))
    spr = SPRITE_CACHE[k] = s.convert_alpha() if pygame.display.get_surface() else s
  return spr


def _beam_flare(fr):
  k = ("rflare", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    R = 30
    s = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
    for i in range(10):                                              # turning rainbow star at the horn tip
      a = fr * 0.35 + i * math.tau / 10
      ln = R - (6 if i % 2 else 0)
      c = RAINBOW[i % len(RAINBOW)]
      p1 = (R + math.cos(a) * ln, R + math.sin(a) * ln)
      p2 = (R + math.cos(a + 0.18) * 6, R + math.sin(a + 0.18) * 6)
      p3 = (R + math.cos(a - 0.18) * 6, R + math.sin(a - 0.18) * 6)
      pygame.draw.polygon(s, c + (200,), (p1, p2, p3))
    pygame.draw.circle(s, (255, 190, 255, 120), (R, R), 13 + fr % 3)
    pygame.draw.circle(s, (255, 255, 255, 235), (R, R), 8)
    spr = SPRITE_CACHE[k] = s
  return spr


def _beam_taper(fr):
  k = ("rtaper", fr)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    tile = _beam_tile(fr)
    th = tile.get_height()
    spr = pygame.Surface((24, th), pygame.SRCALPHA)
    for k_ in range(24):
      h = max(1, int(th * (0.3 + 0.7 * k_ / 24.0)))
      col = pygame.transform.scale(tile.subsurface((k_, 0, 1, th)), (1, h))
      spr.blit(col, (k_, th // 2 - h // 2))
    SPRITE_CACHE[k] = spr
  return spr


def draw_rainbow_beam(surface, hx, hy, ln, t):
  """straight rainbow beam from (hx, hy) for ln pixels; t is a frame counter."""
  ln = int(ln)
  if ln <= 0:
    return
  fr = t % 8
  tile = _beam_tile(fr)
  th = tile.get_height()
  top = int(hy - th // 2)
  x, end = int(hx), int(hx) + ln
  first = True
  while x < end:
    w = min(BEAM_TILE * 2, end - x)
    if first and w > 24:                                             # tapers in from the horn
      surface.blit(_beam_taper(fr), (x, top))
      surface.blit(tile, (x + 24, top), (24, 0, w - 24, th))
      first = False
    else:
      surface.blit(tile, (x, top), (0, 0, w, th))
    x += w
  if ln < WIDTH:                                                     # glowing head while it shoots out
    pygame.draw.circle(surface, (255, 240, 255), (end, int(hy)), 10)
  f = _beam_flare(t % 18)
  surface.blit(f, (int(hx) - f.get_width() // 2, int(hy) - f.get_height() // 2))


# ---------------------------------------------------------------- Wraith Wyrm: Soul Siphon
def draw_siphon(surface, hx, hy, tx, ty, t):
  """a wavering ghostly tether from the jaws to the foe being drained, with souls flowing back along it."""
  dx, dy = tx - hx, ty - hy
  ln = math.hypot(dx, dy) or 1.0
  nx, ny = -dy / ln, dx / ln
  segs = max(6, int(ln / 14))
  for amp, ph, col, w in ((9, 0.0, (30, 120, 150), 7), (7, 1.7, (110, 235, 255), 3), (4, 3.1, (235, 255, 255), 1)):
    pts = []
    for k in range(segs + 1):
      u = k / float(segs)
      off = math.sin(u * 9 + t * 0.35 + ph) * amp * math.sin(math.pi * u)
      pts.append((int(hx + dx * u + nx * off), int(hy + dy * u + ny * off)))
    pygame.draw.lines(surface, col, False, pts, w)
  for k in range(5):                                       # souls drifting home
    u = 1.0 - ((t * 0.035 + k / 5.0) % 1.0)
    px, py = hx + dx * u, hy + dy * u + math.sin(t * 0.3 + k) * 4
    pygame.draw.circle(surface, (150, 245, 255), (int(px), int(py)), 4)
    pygame.draw.circle(surface, (255, 255, 255), (int(px), int(py)), 2)
  r = 12 + int(abs(math.sin(t * 0.2)) * 5)                 # grip on the victim
  pygame.draw.circle(surface, (110, 235, 255), (int(tx), int(ty)), r, 2)
  pygame.draw.circle(surface, (220, 255, 255), (int(tx), int(ty)), max(3, r - 7), 1)


def draw_soul(surface, w):
  """a hunting ghost wisp: a pale head with a fading tail"""
  tr = w.get('trail', [])
  n = len(tr)
  for i, (x, y) in enumerate(tr):
    f = (i + 1) / float(n + 1)
    pygame.draw.circle(surface, (int(40 + 110 * f), int(110 + 135 * f), int(140 + 115 * f)), (int(x), int(y)), max(1, int(2 + f * 6)))
  x, y = int(w['x']), int(w['y'])
  pygame.draw.circle(surface, (120, 235, 255), (x, y), 9)
  pygame.draw.circle(surface, (235, 255, 255), (x, y), 6)
  ex = 1 if w.get('vx', 0) >= 0 else -1
  pygame.draw.circle(surface, (20, 60, 80), (x + ex * 2 - 2, y - 1), 1)
  pygame.draw.circle(surface, (20, 60, 80), (x + ex * 2 + 2, y - 1), 1)


# ---------------------------------------------------------------- Clockwork Dragon: brass missiles
def missile_sprite(ang_deg):
  q = int(round(ang_deg / 10.0)) * 10 % 360
  k = ("missile", q)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((30, 14), pygame.SRCALPHA)
    pygame.draw.polygon(s, (110, 70, 30), [(2, 1), (8, 5), (8, 9), (2, 13)])          # fins
    pygame.draw.rect(s, (196, 150, 70), (6, 4, 16, 6), border_radius=2)               # brass body
    pygame.draw.line(s, (240, 210, 130), (7, 5), (21, 5), 1)
    pygame.draw.rect(s, (120, 84, 40), (12, 4, 2, 6))
    pygame.draw.polygon(s, (210, 50, 40), [(22, 4), (28, 7), (22, 10)])              # red nose
    pygame.draw.polygon(s, (255, 200, 80), [(6, 5), (0, 7), (6, 9)])                # flame
    spr = SPRITE_CACHE[k] = pygame.transform.rotate(s, -q)
  return spr


def draw_missile(surface, m):
  spr = missile_sprite(math.degrees(m['a']))
  surface.blit(spr, (int(m['x']) - spr.get_width() // 2, int(m['y']) - spr.get_height() // 2))


def draw_boom(surface, bm):
  t = bm['t']
  r = 10 + t * 4
  x, y = int(bm['x']), int(bm['y'])
  if t < 5:
    pygame.draw.circle(surface, (255, 240, 180), (x, y), max(4, 22 - t * 3))
  pygame.draw.circle(surface, (255, 170, 50), (x, y), r, 4)
  pygame.draw.circle(surface, (255, 230, 140), (x, y), max(1, r - 6), 2)


# ---------------------------------------------------------------- Forest Dragon: bramble vine
def draw_vine(surface, v, frac, ground_y):
  """a thorny vine bursting up from the ground to (x, ty); frac is how far it has grown (0-1)"""
  if frac <= 0:
    return
  x0 = v['x']
  h = (ground_y - v['ty']) * frac
  n = max(3, int(h / 12))
  pts = []
  for k in range(n + 1):
    u = k / float(n)
    pts.append((int(x0 + math.sin(u * 5.5 + v['t'] * 0.25) * 9 * u * v['side']), int(ground_y - h * u)))
  pygame.draw.lines(surface, (34, 58, 16), False, pts, 11)
  pygame.draw.lines(surface, (78, 120, 34), False, pts, 7)
  pygame.draw.lines(surface, (130, 180, 60), False, pts, 2)
  for k in range(1, n):                                     # thorns and leaves along the stalk
    x, y = pts[k]
    sd = 1 if k % 2 else -1
    pygame.draw.polygon(surface, (220, 210, 150), [(x + sd * 4, y - 2), (x + sd * 12, y - 7), (x + sd * 4, y + 3)])
    if k % 3 == 0:
      pygame.draw.ellipse(surface, (90, 150, 40), (x - sd * 16 - 6, y - 4, 14, 7))
  tx, ty = pts[-1]
  for a in (-2.4, -1.6, -0.8, -1.2, -2.0):                 # a claw of thorns at the tip
    ex, ey = tx + math.cos(a) * 16, ty + math.sin(a) * 16
    pygame.draw.line(surface, (60, 90, 26), (tx, ty), (int(ex), int(ey)), 5)
    pygame.draw.line(surface, (230, 220, 160), (int(ex), int(ey)), (int(tx + math.cos(a) * 21), int(ty + math.sin(a) * 21)), 2)


def draw_burble_beam(surface, mx, my, ang, t):
  """the Jabberwock's sweeping green beam from its jaws to off screen"""
  ca, sa = math.cos(ang), math.sin(ang)
  nx, ny = -sa, ca
  rnd = random.Random(int(t) // 2)
  for col, w, amp in (((30, 110, 30), 22, 5), ((90, 230, 70), 13, 4), ((200, 255, 180), 6, 2), ((255, 255, 255), 2, 1)):
    pts = []
    for q in range(0, 48):
      d = q * 26
      off = rnd.uniform(-amp, amp) if q else 0
      pts.append((int(mx + ca * d + nx * off), int(my + sa * d + ny * off)))
    pygame.draw.lines(surface, col, False, pts, w)
  pygame.draw.circle(surface, (200, 255, 170), (int(mx), int(my)), 14)
  pygame.draw.circle(surface, (255, 255, 255), (int(mx), int(my)), 7)


def icicle_sprite(ang_deg):
  q = int(round(ang_deg / 15.0)) * 15 % 360
  k = ("icicle", q)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((26, 10), pygame.SRCALPHA)
    pygame.draw.polygon(s, (90, 160, 220), [(0, 5), (8, 0), (25, 5), (8, 10)])
    pygame.draw.polygon(s, (200, 240, 255), [(3, 5), (9, 2), (22, 5), (9, 7)])
    pygame.draw.line(s, (255, 255, 255), (5, 4), (18, 4), 1)
    spr = SPRITE_CACHE[k] = pygame.transform.rotate(s, -q)
  return spr


# ---------------------------------------------------------------- Forest Dragon razor leaves / Cockatrice eggs and chicks
def leaf_sprite(rot, col):
  q = int(rot // 30) * 30 % 360
  k = ("rleaf", q, col)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((22, 12), pygame.SRCALPHA)
    pygame.draw.polygon(s, (40, 60, 16), [(0, 6), (7, 0), (21, 6), (7, 11)])
    pygame.draw.polygon(s, col, [(2, 6), (8, 2), (19, 6), (8, 9)])
    pygame.draw.line(s, (230, 240, 160), (3, 6), (18, 6), 1)
    spr = SPRITE_CACHE[k] = pygame.transform.rotate(s, q)
  return spr


def egg_shot_sprite(rot):
  q = int(rot // 30) * 30 % 360
  k = ("cegg", q)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    s = pygame.Surface((14, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (120, 100, 70), (0, 0, 14, 18))
    pygame.draw.ellipse(s, (246, 236, 214), (1, 1, 12, 16))
    pygame.draw.ellipse(s, (255, 255, 250), (3, 3, 4, 6))
    for x, y in ((8, 9), (5, 12), (9, 5), (10, 13)):
      s.set_at((x, y), (170, 120, 70))
    spr = SPRITE_CACHE[k] = pygame.transform.rotate(s, q)
  return spr


def chick_sprite(fr, flip):
  """a super tiny cockatrice: the Cockatrice's own flight frames shrunk right down"""
  fr = int(fr) % 21
  k = ("chick", fr, flip)
  spr = SPRITE_CACHE.get(k)
  if spr is None:
    src = sheet('COCKATRICE').frame('fly', fr)
    s = pygame.transform.scale(src, (42, 32))
    if flip:
      s = pygame.transform.flip(s, True, False)
    spr = SPRITE_CACHE[k] = s
  return spr
