"""Flappy Dragon screens and rendering."""
from fd_core import *
from fd_foes import foe_frame
from fd_satyr import satyr_frame
from fd_extra import extra_frame
from fd_phoenix import phx_frame, phx_frames
from fd_witch import ws_frame, ws_count
from fd_spider import sp_frame, sp_count
from fd_night import night_frame, night_count
from fd_hydra import hyd_frame, hyd_mouths, hyd_frames
from fd_beholder import beh_frame, beh_frames, beh_point, beam_line, BEAM_HALF as BEH_HALF, SCALE as BEH_SCALE, EYE as BEH_EYE
from fd_jabber import jab_frame, jab_fx, jab_mouth, jab_frames
from fd_cyclops import cyc_frame, cyc_count
from fd_baby import baby_frame, baby_count
from fd_eggs import egg_sprite, nest_sprites, EGG_STYLE, RARITY_COL, RARITY_ORDER
from fd_villagers import villager_frame
from fd_items import NEST_RAISE, coin_img, crystal_img, life_heart
import time
import math
import random
from fd_mages import mage_frame, mage_frames
from fd_art import *
import fd_ui as UIX
import fd_extras as FX
import fd_pixart as PX
import fd_core as _FDC
import fd_modes as MODE
import fd_ground as GATK
import fd_foes2 as NF
import fd_boss2 as NB
import fd_perks as PERK
import fd_achieve as ACH
import fd_goart as GOA
import fd_isles as ISL
from fd_sound import AUDIO

BOLT_CACHE = {}


def bolt_sprite(deg):
  spr = BOLT_CACHE.get(deg)
  if spr is None:
    base = pygame.Surface((100, 30), pygame.SRCALPHA)
    cy = 15
    pygame.draw.rect(base, (105, 65, 32), (20, cy - 3, 76, 6))
    pygame.draw.line(base, (150, 100, 55), (20, cy - 2), (96, cy - 2), 1)
    for k in range(3):
      fx = 92 - k * 10
      pygame.draw.polygon(base, (190, 60, 30), [(fx, cy - 3), (fx + 12, cy - 3), (fx + 16, cy - 10), (fx + 4, cy - 10)])
      pygame.draw.polygon(base, (190, 60, 30), [(fx, cy + 3), (fx + 12, cy + 3), (fx + 16, cy + 10), (fx + 4, cy + 10)])
    pygame.draw.polygon(base, (70, 72, 80), [(0, cy), (24, cy - 10), (24, cy + 10)])
    pygame.draw.polygon(base, (255, 170, 50), [(6, cy), (24, cy - 6), (24, cy + 6)])
    pygame.draw.polygon(base, (255, 245, 200), [(12, cy), (24, cy - 3), (24, cy + 3)])
    spr = BOLT_CACHE[deg] = pygame.transform.rotate(base, -deg)
  return spr


BOSSBAR_CACHE = {}
CRESCENTS = {}
SCALED = {}


_BIGC = {}


def big_crystal(fr):
  """the power-up crystal 15% larger than its art"""
  src = powerup_sprite(fr)
  k = (id(src), fr)
  spr = _BIGC.get(k)
  if spr is None:
    spr = _BIGC[k] = pygame.transform.smoothscale(src, (int(src.get_width() * 1.15), int(src.get_height() * 1.15)))
  return spr

def scaled_frame(kind, fr, k):
  key = (kind, fr, k)
  spr = SCALED.get(key)
  if spr is None:
    src = extra_frame(kind, fr)
    spr = SCALED[key] = pygame.transform.scale(src, (int(src.get_width() * k), int(src.get_height() * k)))
  return spr


def fire_crescent(fr):
  spr = CRESCENTS.get(fr)
  if spr is None:
    H, W = 120, 56
    spr = pygame.Surface((W, H), pygame.SRCALPHA)
    rnd = random.Random(fr * 5 + 1)
    cols = ((190, 36, 14), (235, 92, 18), (255, 160, 30), (255, 226, 110))
    R = H * 0.62
    cx = W + R * 0.35 - 4
    n = 18
    for li, col in enumerate(cols):
      th = 1.0 - li * 0.2
      outer, inner = [], []
      for k in range(n + 1):
        a = -math.radians(62) * th + math.radians(124) * th * k / n
        j = 1 + rnd.uniform(-0.04, 0.04)
        outer.append((int(cx - math.cos(a) * R * j), int(H / 2 + math.sin(a) * R * j)))
      wid = 30 - li * 7
      for k in range(n, -1, -1):
        a = -math.radians(62) * th + math.radians(124) * th * k / n
        ri = R - wid * math.sin(math.pi * (k / float(n))) ** 0.7 - 1
        inner.append((int(cx - math.cos(a) * ri), int(H / 2 + math.sin(a) * ri)))
      pygame.draw.polygon(spr, col, outer + inner)
    for _ in range(14):
      spr.set_at((int(rnd.uniform(W * 0.45, W - 1)), int(rnd.uniform(8, H - 9))), rnd.choice(cols[1:]))
    CRESCENTS[fr] = spr
  return spr


def draw_star(gs, cx, cy, full):
  pts = []
  for j in range(10):
    a = math.radians(-90 + j * 36)
    rr = 8 if j % 2 == 0 else 3.5
    pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
  pygame.draw.polygon(gs, (255, 170, 40) if full else (62, 58, 62), pts)

def draw_badge(gs, x, y, t):
  """pulsing '!' bubble: an egg is ready to hatch"""
  pulse = (math.sin(t * 6) + 1) / 2
  r = 13 + int(pulse * 2)
  add_glow(gs, x, y, 26 + int(pulse * 6), (120, 90, 10))
  pygame.draw.circle(gs, (60, 20, 10), (x + 1, y + 2), r)
  pygame.draw.circle(gs, (255, 196, 40), (x, y), r)
  pygame.draw.circle(gs, (255, 240, 160), (x - 4, y - 4), 4)
  pygame.draw.circle(gs, (130, 60, 10), (x, y), r, 2)
  blit_text(gs, small_font, "!", (110, 30, 10), (x, y + 1), "center", shadow=False)

def draw_heart(gs, cx, cy, full):
  col, hi, dk = ((226, 40, 52), (255, 140, 150), (110, 14, 24)) if full else ((52, 40, 48), (80, 68, 76), (30, 22, 28))
  pts = [(cx, cy + 12), (cx - 13, cy), (cx - 13, cy - 6), (cx - 8, cy - 11), (cx - 3, cy - 11), (cx, cy - 7), (cx + 3, cy - 11), (cx + 8, cy - 11), (cx + 13, cy - 6), (cx + 13, cy)]
  pygame.draw.polygon(gs, dk, [(x, y + 1) for x, y in pts])
  pygame.draw.polygon(gs, col, pts)
  pygame.draw.polygon(gs, dk, pts, 2)
  pygame.draw.circle(gs, hi, (cx - 6, cy - 5), 2)


def draw_death_ray(gs, sx, sy, ang, half, t):
    """the Beholder's death ray, carrying on from the edge of its art right across the sky"""
    ca, sa = math.cos(ang), math.sin(ang)
    L = 1600
    ex, ey = sx + ca * L, sy + sa * L
    nx, ny = -sa, ca
    fl = 1.0 + 0.12 * math.sin(t * 1.7)
    for w, c in ((half * 1.25 * fl, (40, 230, 50)), (half * 0.95 * fl, (150, 255, 150)), (half * 0.55, (245, 255, 245))):
      pygame.draw.polygon(gs, c, [(sx + nx * w, sy + ny * w), (ex + nx * w, ey + ny * w), (ex - nx * w, ey - ny * w), (sx - nx * w, sy - ny * w)])
    random.seed(int(t))                                  # spiky crackles along the ray (steady within a frame)
    for _ in range(7):
      q = random.uniform(30, 900)
      px, py = sx + ca * q, sy + sa * q
      s_ = random.choice((-1, 1)) * random.uniform(14, 40)
      pygame.draw.line(gs, (60, 255, 70), (int(px), int(py)), (int(px + nx * s_ + ca * 20), int(py + ny * s_ + sa * 20)), 2)
    random.seed()
    add_glow(gs, int(sx), int(sy), int(half * 2.6), (30, 110, 40))
    pygame.draw.circle(gs, (245, 255, 245), (int(sx), int(sy)), int(half * 1.1))


EYE_CACHE = {}


def draw_seeker(gs, o):
    """a heat-seeking eyeball with a green trail, its pupil fixed on where it is going"""
    x, y = o['x'], o['y']
    sp = math.hypot(o['vx'], o['vy']) or 1.0
    ux, uy = o['vx'] / sp, o['vy'] / sp
    for k in range(1, 5):                                # trail
      pygame.draw.circle(gs, (40, 160 - k * 20, 60), (int(x - ux * k * 7), int(y - uy * k * 7)), max(2, 9 - k * 2))
    add_glow(gs, int(x), int(y), 24, (20, 70, 30))
    pygame.draw.circle(gs, (60, 50, 70), (int(x), int(y)), 11)
    pygame.draw.circle(gs, (236, 232, 220), (int(x), int(y)), 9)
    pygame.draw.line(gs, (200, 60, 60), (int(x - 7), int(y + 2)), (int(x - 3), int(y + 1)), 1)
    pygame.draw.line(gs, (200, 60, 60), (int(x + 2), int(y + 6)), (int(x + 4), int(y + 3)), 1)
    ix, iy = x + ux * 3.5, y + uy * 3.5
    pygame.draw.circle(gs, (60, 220, 90), (int(ix), int(iy)), 5)
    pygame.draw.circle(gs, (10, 20, 10), (int(ix + ux), int(iy + uy)), 2)
    pygame.draw.circle(gs, (255, 255, 255), (int(x - 3), int(y - 4)), 2)

class GameDraw:
  def draw(self):
    gs = game_surface
    st = self.state
    _FDC.UI['stone'] = st not in ("MENU", "PLAYING", "PAUSED", "INTRO", "GAMEOVER")
    self.draw_background()
    if st == "MENU":
      self.draw_menu()
    elif st == "LAIR":
      self.draw_lair()
    elif st == "WORLDS":
      self.draw_worlds()
    elif st == "MODES":
      self.draw_modes()
    elif st == "ACHIEVE":
      self.draw_achieve()
    elif st == "QUESTS":
      self.draw_quests()
    elif st == "REPORT":
      self.draw_report()
    elif st == "OPTIONS":
      self.draw_options()
    elif st == "HOARD":
      self.draw_hoard()
    elif st in ("SELECT", "RARE_SELECT"):
      self.draw_select()
    elif st == "DRAGON_INFO":
      self.draw_dragon_info()
    elif st == "ENEMIES":
      self.draw_enemies()
    elif st == "EGGS":
      self.draw_eggs()
    elif st == "EGG_INFO":
      self.draw_egg_info()
    elif st == "ROOSTS":
      self.draw_roosts()
    elif st == "HATCHLINGS":
      self.draw_hatchlings()
    elif st == "HATCH_INFO":
      self.draw_hatch_info()
    elif st == "ENEMY_INFO":
      self.draw_enemy_info()
    elif st == "INTRO":
      self.draw_intro()
    else:
      self.draw_game()
    if st not in ("PLAYING", "PAUSED", "GAMEOVER", "INTRO"):
      gs.blit(VIGNETTE, (0, 0))
    if UIX.tab_bar_shown(self):                           # icon tabs along the bottom of every menu screen
      UIX.draw_tab_bar(gs, UIX.TAB_OF_STATE[st], self.anim, self.mouse, ('eggs',) if self.eggs_ready() else ())
    ox = oy = 0
    if self.shake_t > 0 and self.shake_i:
      ox, oy = random.randint(-self.shake_i, self.shake_i), random.randint(-self.shake_i, self.shake_i)
    if st in ("PLAYING", "PAUSED"):                    # floating scores, combo and boss hit flash
      FX.juice_draw(gs, self, small_font, hud_font)
    if st == "PLAYING":
      FX.tutorial_draw(gs, self, small_font)
      if getattr(self, 'mode', '') == 'tutorial':
        MODE.tutorial_draw(gs, self, (small_font, tiny_font, button_font), panel, (PANEL_DARK, GOLD_BORDER, PARCHMENT, BANNER_GOLD))
    if st == "MENU":                                   # which build this is, for bug reports
      vt = text(tiny_font, FX.BUILD, (220, 200, 170))
      gs.blit(vt, vt.get_rect(bottomright=(WIDTH - 12, HEIGHT - 8)))
    if self.toast_t > 0:
      self.toast_t -= 1
      img = text(small_font, self.toast_msg, PARCHMENT)
      tr = img.get_rect(center=(WIDTH // 2, 18 if self.state == "GAMEOVER" else GROUND_Y - 70)).inflate(34, 12)
      panel(gs, tr, PANEL_DARK, 240, GOLD_BORDER, 2, 8)
      gs.blit(img, img.get_rect(center=tr.center))
    self.present(ox, oy)

  def draw_background(self):
    gs = game_surface
    if UIX.art_ok('level'):                              # your painted level layers
      night = not self.day
      wk = self.world()
      sky_img = UIX.level_sky(wk, night)
      for y0, y1 in UIX.sky_spans(wk):                    # only where scenery doesn't cover the sky
        gs.blit(sky_img, (0, y0), (0, y0, WIDTH, y1 - y0))
      if night:
        for x, y, ph in self.twinkle[::3]:
          r = 1 + int((math.sin(self.anim * 3 + ph) + 1) * 0.9)
          pygame.draw.circle(gs, STAR_WHITE, (x, y), r)
      sky = UIX.sky_ok()
      if sky:                                              # your painted sun / moon and clouds
        orb = UIX.sky_orb(night, wk)
        gs.blit(orb, orb.get_rect(center=(WIDTH - 560, 150)))   # clear of the hearts and threat panels
        wxk = getattr(self, 'wx_kind', 'clear')
        stormy = wxk in ('storm', 'rain')
        for c in self.clouds:
          gs.blit(UIX.sky_cloud(c[2], night, stormy, 'sandstorm' if wxk == 'sand' else wk), (int(c[0]), int(c[1])))
      else:
        if night:
          gs.blit(MOON, (WIDTH - 240, -10))
        else:
          gs.blit(DAY['sun'], (WIDTH - 240, -10))
        for c in self.clouds:
          gs.blit(CLOUDS[c[2] % len(CLOUDS)], (int(c[0]), int(c[1])))
      UIX.level_layers(gs, wk, self.far_x, self.mid_x, night)
      for m in self.mist:
        gs.blit(MIST, (int(m[0]), int(m[1])))
      return
    if self.day:
      gs.blit(DAY['sky'], (0, 0))
      gs.blit(DAY['sun'], (WIDTH - 240, -10))
    else:
      gs.blit(SKY, (0, 0))
      for x, y, ph in self.twinkle:
        r = 1 + int((math.sin(self.anim * 3 + ph) + 1) * 0.9)
        pygame.draw.circle(gs, STAR_WHITE, (x, y), r)
      gs.blit(MOON, (WIDTH - 240, -10))
    if BANK_LAYER is not None:
      self.blit_layer(BANK_LAYER, 250, self.far_x * 0.5)
      for c in self.clouds:
        gs.blit(CLOUDS[c[2] % len(CLOUDS)], (int(c[0]), int(c[1])))
      self.blit_layer(FAR_LAYER, 300, self.far_x)
      self.blit_layer(NEAR_LAYER, 400, self.near_x)
    else:
      self.blit_layer(FAR_LAYER, 250, self.far_x)
      for c in self.clouds:
        gs.blit(CLOUDS[c[2] % len(CLOUDS)], (int(c[0]), int(c[1])))
      self.blit_layer(NEAR_LAYER, 330, self.near_x)
      self.blit_layer(HILL_LAYER, 430, self.mid_x)
    for m in self.mist:
      gs.blit(MIST, (int(m[0]), int(m[1])))
    if self.day:
      gs.fill(DAY_LIFT, special_flags=pygame.BLEND_RGB_ADD)

  def lift_ground(self, gs):
    if self.day:
      gs.fill((38, 44, 30), (0, GROUND_Y, WIDTH, GROUND_H), special_flags=pygame.BLEND_RGB_ADD)

  def blit_layer(self, layer, y0, x):
    if layer is None:
      return
    lw = layer.get_width()
    o = int(x) % lw
    game_surface.blit(layer, (-o, y0))
    if lw - o < WIDTH:
      game_surface.blit(layer, (-o + lw, y0))

  def draw_backdrop_ground(self):
    self.draw_scenery()
    if UIX.art_ok('level'):
      UIX.level_ground(game_surface, self.world(), getattr(self, 'ground_x', 0.0), not self.day)
    else:
      game_surface.blit(GROUND, (0, GROUND_Y))
      self.lift_ground(game_surface)

  def draw_scenery(self):
    if not self.day and UIX.art_ok('level'):           # at night the trees, bushes and villagers are darkened too
      self.draw_scenery_to(UIX.NightProxy(game_surface))
      return
    self.draw_scenery_to(game_surface)

  def draw_scenery_to(self, gs):
    for s in self.scenery:
      t, x = s['type'], int(s['x'])
      if t == "fg_hill":
        gs.blit(SPRITE_CACHE["fg_hill"][0], (x - 50, GROUND_Y - 16))
      elif t in ("smith", "peasant"):
        spr = extra_frame('smith', int(s['anim'] * 0.6))
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      elif t in ("knight", "dwarf"):
        spr = scaled_frame(t, int(s['anim'] * 0.8), 1.4) if t == "knight" else extra_frame(t, int(s['anim'] * 0.8))
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      elif t == "villager":
        m = s.get('mode', 'walk')
        spr = villager_frame(s['v'], m, int(s['anim'] * (0.4 if m == 'idle' else 0.7 if m == 'walk' else 1.0)), 1.25, bool(s.get('right')))   # sheet faces left; flip the ones heading right
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      elif t == "bonfire":
        spr = bonfire_sprite(int(s['anim'] * 0.8))
        add_glow(gs, x, GROUND_Y - 20, 70, (110, 50, 8))
        gs.blit(spr, (x - spr.get_width() // 2, GROUND_Y + 8 - spr.get_height()))
      elif t in ("sheep", "deer"):
        spr = ENV.runner_sprite(t, 0, int(s['anim'] * 0.7) % 4)
        gs.blit(spr, (x, GROUND_Y + 4 - spr.get_height()))
      else:
        spr, ox, oy = SPRITE_CACHE.get(t) or SPRITE_CACHE["bush"]
        gs.blit(spr, (x - ox, GROUND_Y + 4 - oy))

  def fog_puff(self, r):
    r = max(4, int(r) // 4 * 4)
    k = ('fog', r)
    img = SCALED.get(k)
    if img is None:
      img = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
      for i in range(8, 0, -1):
        t = i / 8.0
        pygame.draw.circle(img, (110 + int(60 * (1 - t)), 50 + int(50 * (1 - t)), 150 + int(60 * (1 - t)), int(60 * (1 - t) ** 1.2 + 8)), (r, r), int(r * t))
      SCALED[k] = img
    return img

  def draw_curse(self, gs):
    for f in getattr(self, 'fog', ()):
      img = self.fog_puff(f['r'])
      gs.blit(img, (int(f['x']) - img.get_width() // 2, int(f['y']) - img.get_height() // 2))
    t = self.anim
    for name in GROUND_LISTS + ('enemies',):                    # little skulls circle anything cursed
      for o in getattr(self, name):
        if o.get('curse') and not o.get('shattered'):
          r = o['rect']
          cx, cy = r.centerx, (r.top + 30 if name == 'towers' else r.centery)
          left = o['curse'] / float(max(1, o.get('curse_max', 40)))
          rad = 18 + 10 * left
          for j in range(3):
            a = t * 5 + j * 2.09
            sx, sy = int(cx + math.cos(a) * rad), int(cy + math.sin(a) * rad * 0.6)
            pygame.draw.circle(gs, (60, 20, 80), (sx + 1, sy + 1), 5)
            pygame.draw.circle(gs, (230, 190, 255), (sx, sy), 5)
            pygame.draw.rect(gs, (230, 190, 255), (sx - 3, sy + 2, 6, 3))
            pygame.draw.circle(gs, (50, 10, 60), (sx - 2, sy - 1), 1)
            pygame.draw.circle(gs, (50, 10, 60), (sx + 2, sy - 1), 1)
    for w in getattr(self, 'wisps', ()):                       # hunting soul wisps
      x, y = int(w['x']), int(w['y'])
      add_glow(gs, x, y, 26, (70, 30, 100))
      ang = math.atan2(w['vy'], w['vx'])
      tx, ty = x - math.cos(ang) * 22, y - math.sin(ang) * 22
      wob = math.sin(w['t'] * 0.5) * 4
      pygame.draw.polygon(gs, (190, 110, 255), [(x - math.sin(ang) * 6, y + math.cos(ang) * 6), (tx - math.sin(ang) * wob, ty + math.cos(ang) * wob), (x + math.sin(ang) * 6, y - math.cos(ang) * 6)])
      pygame.draw.circle(gs, (240, 220, 255), (x, y), 7)
      pygame.draw.circle(gs, (60, 20, 80), (int(x + math.cos(ang) * 2 - 2), int(y - 2)), 2)
      pygame.draw.circle(gs, (60, 20, 80), (int(x + math.cos(ang) * 2 + 3), int(y - 2)), 2)
    for bx, by, vx, vy, rot, vr, life in getattr(self, 'bones', ()):   # flying bone shards
      ca, sa = math.cos(rot) * 6, math.sin(rot) * 6
      pygame.draw.line(gs, (70, 60, 48), (bx - ca, by - sa + 1), (bx + ca, by + sa + 1), 4)
      pygame.draw.line(gs, (232, 220, 190), (bx - ca, by - sa), (bx + ca, by + sa), 2)
      pygame.draw.circle(gs, (240, 230, 205), (int(bx - ca), int(by - sa)), 2)
      pygame.draw.circle(gs, (240, 230, 205), (int(bx + ca), int(by + sa)), 2)

  def hole_halo(self, R):
    """soft gravitational-lensing halo around a black hole (cached per size)"""
    R = max(2, int(R) // 2 * 2)
    k = ('halo', R)
    img = SCALED.get(k)
    if img is None:
      size = int(R * 6) + 8
      img = pygame.Surface((size, size), pygame.SRCALPHA)
      c = size // 2
      for i in range(10, 0, -1):
        t = i / 10.0
        pygame.draw.circle(img, (110, 40, 200, int(70 * (1 - t) ** 1.4 + 6)), (c, c), int(size / 2 * t))
      for i in range(6):
        rr = int(R * (1.3 + i * 0.32))
        pygame.draw.circle(img, (170, 130, 255, int(120 * (1 - i / 6.0))), (c, c), rr, 2)
      SCALED[k] = img
    return img

  def draw_holes(self, gs):
    holes = getattr(self, 'holes', ())
    if self.breath and self.selected == "COSMIC":            # a line of starlight from the jaws to the hole
      live = [h for h in holes if h['state'] == 'open']
      if live:
        d = self.dragon
        tb = max(-2, min(2, int(round(self.vel * 0.8 / 6.0))))
        mx, my = void_mouth(void_fly_index(self.flap_ph), tb)
        hx, hy = d.x - PX.OX + mx, d.y - PX.OY + my
        h = live[0]
        pr = 7 + int(abs(math.sin(self.anim * 9)) * 5)            # a pulsing star-burst at the jaws
        add_glow(gs, int(hx), int(hy), 30, (90, 40, 140))
        pygame.draw.circle(gs, (240, 225, 255), (int(hx), int(hy)), pr, 2)
        pygame.draw.circle(gs, (255, 255, 255), (int(hx), int(hy)), 3)
        for k in range(14):
          u = k / 13.0
          x = hx + (h['x'] - hx) * u + random.uniform(-3, 3)
          y = hy + (h['y'] - hy) * u + random.uniform(-3, 3)
          r = 2 + (k % 2) * 2
          pygame.draw.polygon(gs, (235, 215, 255), [(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3), (x, y + r), (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)])
    for h in holes:
      cx, cy, R, t = int(h['x']), int(h['y']), h['R'], h['t']
      if h['state'] == 'closing':                             # collapse: a shockwave ring
        u = h['ct'] / float(VOID_HOLE['close'])
        rr = int(20 + 170 * u)
        if rr > 2:
          pygame.draw.circle(gs, (220, 190, 255), (cx, cy), rr, max(1, int(6 * (1 - u))))
      if R < 1:
        continue
      halo = self.hole_halo(R)
      gs.blit(halo, (cx - halo.get_width() // 2, cy - halo.get_height() // 2))
      for k in range(46):                                    # stars streaming in along spirals
        ph = k * 2.39996
        sp = 0.6 + (k % 7) * 0.12
        life = (t * 0.022 * sp + (k * 0.618) % 1.0) % 1.0
        dist = R * 1.15 + 140 * (1 - life)
        ang = ph + life * 5.0
        x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist * 0.85
        col = (255, 255, 255) if k % 3 else (200, 170, 255)
        pygame.draw.circle(gs, col, (int(x), int(y)), 2 if life > 0.7 else 1)
      pygame.draw.circle(gs, (255, 240, 255), (cx, cy), int(R * 1.1), 3)     # photon ring
      pygame.draw.circle(gs, (190, 120, 255), (cx, cy), int(R * 1.1) + 3, 1)
      pygame.draw.circle(gs, (0, 0, 0), (cx, cy), int(R))

  def draw_particles(self):
    gs = game_surface
    for x, y, vx, vy, life, col, big in getattr(self, 'stars', ()):
      f = min(1.0, life / 30.0)
      tw = 0.6 + 0.4 * math.sin(life * 0.7 + x * 0.1)       # twinkle
      c = (int(col[0] * f * tw + 20 * (1 - f)), int(col[1] * f * tw + 10 * (1 - f)), int(col[2] * f * tw + 40 * (1 - f)))
      if big:
        r = 2 + 4 * f
        pygame.draw.polygon(gs, c, [(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28), (x, y + r), (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)])
      else:
        pygame.draw.circle(gs, c, (int(x), int(y)), max(1, int(2 * f)))
    for p in self.particles:
      pygame.draw.circle(gs, p[5], (int(p[0]), int(p[1])), int(p[4]))

  def draw_sound_btn(self):
    gs = game_surface
    r = SND_BTN
    panel(gs, r, PANEL_DARK, 220, GOLD_BORDER, 2, 8)
    on = AUDIO.ok and AUDIO.enabled
    c = PARCHMENT if on else (140, 120, 120)
    pygame.draw.polygon(gs, c, [(r.x + 10, r.y + 15), (r.x + 18, r.y + 15), (r.x + 27, r.y + 8), (r.x + 27, r.y + 32), (r.x + 18, r.y + 25), (r.x + 10, r.y + 25)])
    if on:
      pygame.draw.arc(gs, c, (r.x + 24, r.y + 13, 10, 14), -1.1, 1.1, 2)
      pygame.draw.arc(gs, c, (r.x + 27, r.y + 8, 14, 24), -1.1, 1.1, 2)
    else:
      pygame.draw.line(gs, (230, 80, 70), (r.x + 30, r.y + 13), (r.x + 42, r.y + 27), 3)
      pygame.draw.line(gs, (230, 80, 70), (r.x + 42, r.y + 13), (r.x + 30, r.y + 27), 3)

  def draw_coin_panel(self, y=14):
    gs = game_surface
    if UIX.ART.has('coin_box') and UIX.art_ok('lair'):    # your painted coin box
      UIX.art_coin_panel(gs, self.data['coins'], y - 2)
      return
    panel(gs, pygame.Rect(WIDTH - 160, y, 146, 40), PANEL_DARK, 220, GOLD_BORDER, 2, 8)
    draw_coin(gs, WIDTH - 138, y + 20)
    blit_text(gs, button_font, str(self.data['coins']), PARCHMENT, (WIDTH - 118, y + 6), shadow=False)

  def draw_menu(self):
    gs = game_surface
    a = self.anim
    if UIX.art_ok('menu'):
      return self.draw_art_menu()
    for x, y, vy, size, ph in self.embers:
      pygame.draw.circle(gs, (255, 190, 80), (int(x), int(y)), max(1, size // 3))
    self.draw_backdrop_ground()
    self.draw_particles()
    my = 320 + math.sin(a * 1.3) * 45
    draw_any_dragon(gs, self.selected, int(self.menu_dragon_x), int(my), int(math.cos(a * 1.3) * 6), a * 7)

    bounce = int(math.sin(a) * 5)
    art = ENV.menu_art()
    crest = pygame.Rect(WIDTH // 2 - 300, 22 + bounce, 600, 140)
    add_glow(gs, WIDTH // 2, crest.centery, 150, (46, 18, 6))
    for i, tx in enumerate((crest.left - 16, crest.right + 16)):             # torches
      pygame.draw.rect(gs, WOOD_DARK, (tx - 3, crest.centery + 4, 6, 30))
      fl = 3 * math.sin(a * 9 + i * 2)
      add_glow(gs, tx, crest.centery - 4, 38, (130, 60, 8))
      pygame.draw.polygon(gs, (255, 120, 20), [(tx - 7, crest.centery + 4), (tx, crest.centery - 20 - fl), (tx + 7, crest.centery + 4)])
      pygame.draw.polygon(gs, FIRE_CORE, [(tx - 3, crest.centery + 4), (tx, crest.centery - 8 - fl), (tx + 3, crest.centery + 4)])
    if art.get('title') is not None:
      gs.blit(art['crest'], crest.topleft)
      gs.blit(art['title'], art['title'].get_rect(center=(crest.centerx, crest.centery - 6)))
      k = (math.sin(a * 3) + 1) / 2
      for sx, sy, ph in ((-200, -34, 0.0), (130, -40, 1.7), (222, 6, 3.1)):
        r = int(2 + 6 * ((math.sin(a * 3 + ph) + 1) / 2))
        cx, cy = crest.centerx + sx, crest.centery + sy
        pygame.draw.line(gs, (255, 244, 190), (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(gs, (255, 244, 190), (cx, cy - r), (cx, cy + r), 1)
    else:
      panel(gs, crest, (12, 12, 20), 225, GOLD_BORDER, 4, 14)
      img = text(title_font, "Raid the Realm", (228, 58, 28))
      tr = img.get_rect(center=(WIDTH // 2, crest.centery))
      gs.blit(text(title_font, "Raid the Realm", (70, 10, 6)), tr.move(4, 4))
      gs.blit(img, tr)

    rec = pygame.Rect(WIDTH // 2 - 150, 172, 300, 30)
    panel(gs, rec, PANEL_DARK, 215, GOLD_BORDER, 2, 8)
    blit_text(gs, small_font, "REALM RECORD: %d" % self.data['high_score'], PARCHMENT, rec.center, "center", shadow=False)

    for k, label, col, bg, border in MENU_ITEMS:
      r = MENU_RECTS[k]
      if k == "play" and art.get('play') is not None:
        pulse = (math.sin(a * 3) + 1) / 2
        add_glow(gs, r.centerx, r.centery, 125 + int(pulse * 20), (110 + int(pulse * 40), 30, 8))
        gs.blit(art['playh'] if r.collidepoint(self.mouse) else art['play'], r.topleft)
        continue
      draw_button(gs, r, label, col, r.collidepoint(self.mouse), bg, border)
      if k == "lair" and self.eggs_ready():
        draw_badge(gs, r.right - 6, r.top + 4, a)
    blit_text(gs, tiny_font, "Click / SPACE flap  |  S shield  |  D dash  |  P pause", (150, 140, 130), (WIDTH // 2, HEIGHT - 26), "center", shadow=False)
    self.draw_coin_panel(HEIGHT - 54)
    self.draw_sound_btn()

  def draw_art_menu(self):
    """the live main menu from your painted night battlement"""
    gs = game_surface
    a = self.anim
    UIX.draw_live_menu_bg(gs, a)
    self.draw_particles()
    UIX.draw_menu_title(gs, a, 4 + int(math.sin(a) * 4))
    UIX.draw_menu_record(gs, pygame.Rect(WIDTH // 2 - 175, 168, 350, 42), self.data['high_score'])
    for k, label, col, bg, border in MENU_ITEMS:
      r = MENU_RECTS[k]
      hov = r.collidepoint(self.mouse)
      if k == "play":
        pulse = (math.sin(a * 3) + 1) / 2
        add_glow(gs, r.centerx, r.centery, 130 + int(pulse * 20), (90 + int(pulse * 40), 24, 6))
      UIX.red_button(gs, r, label, hov)
      if k == "lair" and self.eggs_ready():
        draw_badge(gs, r.right - 30, r.top + 4, a)
    im = UIX._outlined(UIX._ink_font(14), "Tap / SPACE flap  |  S shield  |  D dash  |  P pause", (230, 214, 190))
    gs.blit(im, im.get_rect(center=(WIDTH // 2, HEIGHT - 18)))
    self.draw_coin_panel()
    self.draw_sound_btn()

  def draw_options(self):
    gs = game_surface
    d = self.data
    rows = {}
    for k, r in OPT_RECTS.items():
      if k in ("weather", "difficulty") and self.opt_from == "PAUSED":
        continue
      if k in OPT_SLIDERS:
        rows[k] = ("Music" if k == "music" else "Sound Effects", "", d.get('music_vol' if k == 'music' else 'sfx_vol', 100), r)
      elif k == "display":
        rows[k] = ("Display", "FULLSCREEN" if self.fullscreen else "WINDOWED", self.fullscreen, r)
      elif k == "difficulty":
        e = d.get('difficulty', 'easy') == 'easy'
        rows[k] = ("Difficulty", "EASY" if e else "HARD", e, r)
      elif k == "hand":
        lefty = d.get('lefty', False)
        rows[k] = ("Controls", "LEFT HAND" if lefty else "RIGHT HAND", not lefty, r)
      else:
        on = d.get(k, True)
        rows[k] = ({"weather": "Weather", "shake": "Camera Shake", "vibrate": "Vibration"}[k], "ON" if on else "OFF", on, r)
    if UIX.art_ok():                                   # your painted study
      UIX.draw_art_study(gs, self, self.anim, rows, OPT_SLIDERS, slider_track)
      UIX.art_title(gs, "OPTIONS", 50, self.anim)
      if self.opt_from != "PAUSED":
        UIX.art_footer(gs, "Easy: 3 hearts   |   Hard: one hit and you fall")
        for k_, lab_ in (('backup', "BACKUP SAVE"), ('restore', "RESTORE SAVE")):
          br = SAVE_BTNS[k_]
          if UIX.art_ok('info'):
            UIX.red_button(gs, br, lab_, br.collidepoint(self.mouse))
          else:
            draw_button(gs, br, lab_, PARCHMENT, br.collidepoint(self.mouse), font=small_font)
    else:
      UIX.draw_study(gs, self, self.anim, rows, OPT_SLIDERS, slider_track)
      UIX.draw_study_title(gs, "OPTIONS", 46, self.anim)
      if self.opt_from != "PAUSED":
        im = UIX._ink_font(16).render("Easy: 3 hearts   |   Hard: one hit and you fall", True, (70, 44, 20))
        gs.blit(im, im.get_rect(center=(WIDTH // 2, UIX.OPT_SHEET.bottom - 30)))
    if self.opt_from == "PAUSED":
      draw_button(gs, BACK_BTN, "RETURN", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def draw_flip_dragon(self, gs, d):
    """Dragon somersault: clockwise on screen = front flip, counter-clockwise = back flip."""
    p = min(1.0, self.flip_t / float(FLIP_FRAMES))
    ease = p * p * (3 - 2 * p)
    ang = -360.0 * ease * self.flip_dir                  # pygame rotates counter-clockwise for positive angles
    spr = dragon_sprite(self.selected, PX.frame_index(self.flap_ph), 0, bool(self.breath))
    sw, sh = spr.get_size()
    px, py = PX.OX + 32, PX.OY + 19                      # centre of the hitbox inside the sprite
    vx, vy = sw / 2.0 - px, sh / 2.0 - py
    r = math.radians(ang)
    nx = vx * math.cos(r) + vy * math.sin(r)
    ny = -vx * math.sin(r) + vy * math.cos(r)
    rot = pygame.transform.rotate(spr, ang)
    gs.blit(rot, rot.get_rect(center=(int(d.centerx + nx), int(d.centery + ny))))

  def draw_lair(self):
    """the Den: a dragon's cave with your dragon asleep on the hoard, a crackling fire, and the menu on hanging signs"""
    gs = game_surface
    if UIX.art_ok('lair'):                              # your painted cave
      UIX.draw_art_den(gs, self, self.anim)
      UIX.art_stone_title(gs, "THE DRAGONS LAIR", 56, self.anim)
    else:
      UIX.draw_den(gs, self, self.anim)
      UIX.draw_title(gs, "THE DRAGONS LAIR", 50, self.anim)
    self.draw_coin_panel()

  def world(self):
    w = self.data.get('world', 'kingdom')
    return w if UIX.world_ok(w) else 'kingdom'

  def draw_worlds(self):
    """pick which world to fly in"""
    gs = game_surface
    t = self.anim
    if UIX.art_ok('menu'):
      UIX.draw_live_menu_bg(gs, t)
    else:
      self.draw_backdrop_ground()
    UIX.art_wide_title(gs, "CHOOSE YOUR REALM", 54, t, 40, 400) if UIX.art_ok('lair') else UIX.draw_title(gs, "CHOOSE YOUR REALM", 52, t)
    self.draw_coin_panel()
    cur = self.world()
    for key, title, r in self.world_rects():
      hov = r.collidepoint(self.mouse)
      sel = key == cur
      if sel:
        add_glow(gs, r.centerx, r.centery, r.w // 2 + 20, (90, 64, 10))
      pygame.draw.rect(gs, (20, 12, 6), r.inflate(14, 14), border_radius=10)
      gs.blit(UIX.world_card(key, r.w, r.h), r.topleft)
      pygame.draw.rect(gs, BANNER_GOLD if (sel or hov) else GOLD_BORDER, r.inflate(14, 14), 5 if sel else 3, border_radius=10)
      pl = pygame.Rect(r.x + 20, r.bottom - 22, r.w - 40, 44)
      if UIX.art_ok('info'):
        UIX.red_button(gs, pl, title.upper() + ("  - FLYING" if sel else ""), hov)
      else:
        draw_button(gs, pl, title, PARCHMENT, hov, font=small_font)
    # (the tab bar along the bottom replaces the old RETURN button here)

  def draw_modes(self):
    """the Play screen: choose Adventure, Endless, Obstacle Course or Tutorial"""
    gs = game_surface
    t = self.anim
    if UIX.art_ok('menu'):
      UIX.draw_live_menu_bg(gs, t)
    else:
      self.draw_backdrop_ground()
    UIX.art_wide_title(gs, "CHOOSE A MODE", 54, t, 40, 470) if UIX.art_ok('lair') else UIX.draw_title(gs, "CHOOSE A MODE", 52, t)
    self.draw_coin_panel()
    d = self.data
    for (key, title, desc, rk), r in MODE.mode_rects(WIDTH):
      hov = r.collidepoint(self.mouse)
      panel(gs, r, (36, 24, 20) if not hov else (60, 36, 24), 236, BANNER_GOLD if hov else GOLD_BORDER, 3, 12)
      add_glow(gs, r.centerx, r.top + 34, 90, (50, 30, 10) if hov else (24, 14, 6))
      blit_text(gs, button_font, title, BANNER_GOLD, (r.centerx, r.top + 30), "center")
      words, lines, cur = desc.split(), [], ''
      for w_ in words:                                 # wrap the description to the card
        test = (cur + ' ' + w_).strip()
        if tiny_font.size(test)[0] > r.w - 36 and cur:
          lines.append(cur)
          cur = w_
        else:
          cur = test
      lines.append(cur)
      for i, ln in enumerate(lines[:2]):
        blit_text(gs, tiny_font, ln, PARCHMENT, (r.centerx, r.top + 60 + i * 20), "center", shadow=False)
      if rk:
        best = d.get(rk, 0)
        lab = ("Best: %d pillars" % best) if key == 'obstacle' else ("Best: %d" % best)
      else:
        lab = "Completed!" if d.get('adv_tutorial_done') else "Reward: %d gold" % MODE.TUT_REWARD
      blit_text(gs, tiny_font, lab, (230, 200, 140), (r.centerx, r.bottom - 22), "center", shadow=False)
    if UIX.art_ok('info'):
      UIX.red_button(gs, BACK_BTN, "RETURN", BACK_BTN.collidepoint(self.mouse))
    else:
      draw_button(gs, BACK_BTN, "RETURN", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def world_rects(self):
    ws = UIX.worlds_available()
    n = max(1, len(ws))
    cols = min(4, n)                                  # up to 4 a row, 2 rows: room for all 7 worlds above RETURN
    rows = (n + cols - 1) // cols
    gap = 30
    w = min(340, (WIDTH - 80 - (cols - 1) * gap) // cols)
    h = w // 2 if rows == 1 else w * 9 // 20
    top = 150 if rows == 1 else 122
    x0 = WIDTH // 2 - (cols * w + (cols - 1) * gap) // 2
    out = []
    for i, (key, title, *_r) in enumerate(ws):
      row, col = divmod(i, cols)
      in_row = min(cols, n - row * cols)              # centre a short last row
      xr = WIDTH // 2 - (in_row * w + (in_row - 1) * gap) // 2
      out.append((key, title, pygame.Rect(xr + col * (w + gap), top + row * (h + 40), w, h)))
    return out

  def draw_gale(self, gs, d):
    """wind streaks and swirls racing out in front of the Wind dragon, over the area its gust blasts"""
    t = pygame.time.get_ticks()
    x0, y0, w, h = d.right, d.y - 40, 300, 110
    rnd = random.Random(7)
    for k in range(22):
      sp = rnd.uniform(0.7, 1.3)
      u = ((t * 0.0016 * sp) + rnd.random()) % 1.0           # each streak races from the mouth to the far edge
      y = y0 + rnd.uniform(0, h) + math.sin(t * 0.008 + k) * 6
      x = x0 + u * w
      ln = int(26 + 40 * sp)
      a = int(220 * math.sin(u * math.pi))
      c = (min(255, 200 + a // 5), min(255, 214 + a // 6), 230)
      wid = 3 if k % 4 == 0 else 2 if k % 2 else 1
      pygame.draw.line(gs, c, (int(x), int(y)), (int(x - ln), int(y + 2)), wid)
    for k in range(3):                                        # curling gust swirls
      u = ((t * 0.0011) + k / 3.0) % 1.0
      cx, cy = int(x0 + 40 + u * (w - 60)), int(y0 + h * (0.3 + 0.2 * k))
      rr = int(10 + 16 * u)
      pygame.draw.arc(gs, (235, 245, 255), (cx - rr, cy - rr, rr * 2, rr * 2), t * 0.01 + k, t * 0.01 + k + 4.2, 2)
    add_glow(gs, x0 + w // 2, y0 + h // 2, 90, (26, 30, 38))

  def draw_phased(self, gs, d):
    """the Wraith Wyrm gone ethereal: see-through, cold blue, rippling, with fading afterimages"""
    p = self.phase_a
    tmp = getattr(self, '_phase_tmp', None)
    if tmp is None:
      tmp = self._phase_tmp = pygame.Surface((168, 128), pygame.SRCALPHA)
    tmp.fill((0, 0, 0, 0))
    draw_any_dragon(tmp, "WRAITH", PX.OX, PX.OY, int(self.vel * 0.8), self.flap_ph, self.breath, getattr(self, 'flap_left', 0.0) > 0)
    v = int(90 * p)
    tmp.fill((0, v // 2, v), special_flags=pygame.BLEND_RGB_ADD)          # spirit-blue
    t = pygame.time.get_ticks() / 1000.0
    ox, oy = d.x - PX.OX, d.y - PX.OY
    for k, (dx, a) in enumerate(((-26, 50), (-13, 80))):                 # afterimages trailing behind
      ghost = tmp.copy()
      ghost.set_alpha(int(a * p))
      gs.blit(ghost, (ox + int(dx * p), oy + int(math.sin(t * 6 + k) * 3 * p)))
    alpha = int(255 - p * (140 + 25 * math.sin(t * 9)))                 # shimmers as it fades in and out of the world
    amp = 4.0 * p
    for y in range(0, 128, 4):                                          # the body ripples like a heat haze
      strip = tmp.subsurface((0, y, 168, 4)).copy()
      strip.set_alpha(alpha)
      gs.blit(strip, (ox + int(math.sin(t * 11 + y * 0.18) * amp), oy + y))
    add_glow(gs, d.centerx, d.centery, int(46 + 10 * p), (int(20 * p), int(60 * p), int(80 * p)))

  def draw_achieve(self):
    gs = game_surface
    if UIX.art_ok('quests'):
      gs.blit(UIX._cover_surf('quest_bg'), (0, 0))
    else:
      self.draw_backdrop_ground()
    dim(gs, 150)
    UIX.art_wide_title(gs, "ACHIEVEMENTS", 46, self.anim, 40, 420) if UIX.art_ok('lair') else UIX.draw_title(gs, "ACHIEVEMENTS", 46, self.anim)
    self.draw_coin_panel()
    ACH.draw(gs, self, (small_font, tiny_font), (PANEL_DARK, GOLD_BORDER, PARCHMENT, BANNER_GOLD), WIDTH)
    for r, lab in zip(ACH.nav_rects(WIDTH), ("< PREV", "BACK", "NEXT >")):
      if UIX.art_ok('info'):
        UIX.red_button(gs, r, lab, r.collidepoint(self.mouse))
      else:
        draw_button(gs, r, lab, PARCHMENT, r.collidepoint(self.mouse), font=small_font)

  def draw_quests(self):
    """a tavern notice board: the current bounty is a pinned poster with a wax seal, the next one is tucked behind"""
    gs = game_surface
    if UIX.art_ok('quests'):                            # your painted notice board
      UIX.draw_art_quests(gs, self, self.anim)
      UIX.art_wide_title(gs, "REALM QUESTS", 58, self.anim, 40, 420)
      self.draw_coin_panel()
      self.draw_ach_button(gs)
      return
    UIX.draw_notice_board(gs, self, self.anim)
    UIX.draw_title(gs, "REALM QUESTS", 46, self.anim)
    self.draw_ach_button(gs)

  def draw_ach_button(self, gs):
    n = len(self.data.get('achieved', []))
    lab = "ACHIEVEMENTS %d/%d" % (n, len(ACH.ACHIEVEMENTS))
    if UIX.art_ok('stables'):
      UIX.art_wood_button(gs, ACH_BTN, lab, ACH_BTN.collidepoint(self.mouse))
    else:
      draw_button(gs, ACH_BTN, lab, BANNER_GOLD, ACH_BTN.collidepoint(self.mouse), font=small_font)

  def draw_upgrade_icon(self, key, cx, cy):
    gs = game_surface
    if key == "thick_scales":
      pts = [(cx - 16, cy - 18), (cx + 16, cy - 18), (cx + 16, cy + 2), (cx, cy + 20), (cx - 16, cy + 2)]
      pygame.draw.polygon(gs, (110, 160, 215), pts)
      pygame.draw.polygon(gs, PARCHMENT, pts, 2)
      pygame.draw.line(gs, PARCHMENT, (cx, cy - 16), (cx, cy + 16), 2)
    elif key == "deep_lungs":
      pygame.draw.polygon(gs, (255, 110, 20), [(cx, cy - 22), (cx + 15, cy + 4), (cx, cy + 20), (cx - 15, cy + 4)])
      pygame.draw.polygon(gs, FIRE_CORE, [(cx, cy - 6), (cx + 7, cy + 6), (cx, cy + 15), (cx - 7, cy + 6)])
    else:
      pygame.draw.arc(gs, CLOTH_RED, (cx - 16, cy - 18, 32, 32), 0, math.pi, 7)
      pygame.draw.line(gs, CLOTH_RED, (cx - 14, cy - 2), (cx - 14, cy + 16), 7)
      pygame.draw.line(gs, CLOTH_RED, (cx + 13, cy - 2), (cx + 13, cy + 16), 7)
      pygame.draw.rect(gs, BONE_WHITE, (cx - 18, cy + 12, 8, 7))
      pygame.draw.rect(gs, BONE_WHITE, (cx + 9, cy + 12, 8, 7))

  def draw_hoard(self):
    """the Hoard as a blacksmith's forge: each upgrade is forged on an anvil (sparks fly when you buy one)"""
    gs = game_surface
    t = self.anim
    if UIX.art_ok('hoard'):                             # your painted forge
      UIX.update_sparks(self)
      UIX.draw_art_forge(gs, self, t)
      UIX.art_wide_title(gs, "THE DRAGON'S FORGE", 56, t)
      self.draw_coin_panel()
      UIX.draw_sparks(gs, self)
      return
    gs.blit(UIX.forge_backdrop(), (0, 0))
    UIX.forge_fire(gs, t)
    UIX.draw_title(gs, "THE DRAGON'S FORGE", 46, t)
    self.draw_coin_panel()
    UIX.update_sparks(self)
    for key, title, desc, rect in UPGRADES:
      lvl = self.data['upgrades'][key]
      cx = rect.centerx
      for ax in (rect.left + 30, rect.right - 30):          # chains for the hanging sign
        pygame.draw.line(gs, (90, 90, 96), (ax, rect.top - 34), (ax, rect.top), 2)
      gs.blit(UIX.metal_sign(rect.w, 40, title.upper()), (rect.left, rect.top))
      atop = rect.top + 176
      UIX.anvil(gs, cx, atop)
      bob = int(math.sin(t * 2 + rect.x) * 2)
      add_glow(gs, cx, atop - 26, 44, (90, 54, 10) if lvl < 3 else (40, 90, 30))
      self.draw_upgrade_icon(key, cx, atop - 26 + bob)
      for i in range(3):
        UIX.ingot(gs, cx - 34 + i * 34, rect.top + 96, i < lvl)
      pr = pygame.Rect(rect.left + 6, rect.top + 46, rect.w - 12, 24)
      pygame.draw.rect(gs, (226, 210, 170), pr, border_radius=4)
      pygame.draw.rect(gs, (120, 90, 50), pr, 1, border_radius=4)
      blit_text(gs, tiny_font, desc, (60, 34, 12), pr.center, "center", shadow=False)
      if lvl < 3:
        cost = UPGRADE_COSTS[lvl]
        btn = upgrade_btn(rect)
        ok = self.data['coins'] >= cost
        draw_button(gs, btn, "FORGE: %d" % cost, PARCHMENT if ok else (150, 50, 50), ok and btn.collidepoint(self.mouse), IRON_GRAY, GOLD_BORDER if ok else STONE_DARK, small_font)
      else:
        blit_text(gs, button_font, "MASTERED", LEAF_GREEN, (rect.centerx, rect.bottom - 22), "center")
    UIX.draw_sparks(gs, self)

  def draw_select(self):
    gs = game_surface
    rare = self.state == "RARE_SELECT"
    boxes = RARE_BOXES if rare else SELECT_BOXES
    if UIX.art_ok('stables'):                           # your painted barn
      hovered = UIX.draw_art_stables(gs, self, boxes, rare, lambda k: DRAGON_PALETTES[k], self.anim)
      UIX.art_wide_title(gs, "MYTHICAL CREATURES" if rare else "DRAGONS ROOST", 54, self.anim, 40, 420)
      self.draw_coin_panel()
      UIX.art_desc_plate(gs, pygame.Rect(WIDTH // 2 - 346, 464, 500, 46), DRAGON_PALETTES[hovered]['desc'])
      UIX.art_wood_button(gs, RARE_BTN, "ROOST" if rare else "MYTHICAL", RARE_BTN.collidepoint(self.mouse))
      self.draw_pending()
      return
    gs.blit(UIX.stable_backdrop(), (0, 0))                # the stables: each dragon in its own stall
    UIX.draw_title(gs, "MYTHICAL CREATURES" if rare else "DRAGONS ROOST", 50, self.anim)
    self.draw_coin_panel()
    hovered = self.selected if self.selected in [b[0] for b in boxes] else boxes[0][0]
    for key, rect in boxes:
      if rect.collidepoint(self.mouse) and not self.pending:
        hovered = key
      unlocked = key in self.data['unlocked']
      sel = self.selected == key
      if sel:
        add_glow(gs, rect.centerx, rect.centery, rect.w // 2 + 26, (90, 64, 10))
      gs.blit(UIX.stall_surface(rect.w, rect.h), rect.topleft)
      pal = DRAGON_PALETTES[key]
      if unlocked:
        draw_any_dragon(gs, key, rect.centerx - 25, rect.top + 40, 0, self.anim + rect.x * 0.01, False)
      else:                                              # a dark shape behind locked bars
        sil = UIX.dragon_silhouette(key)
        gs.blit(sil, (rect.centerx - 25 - PX.OX, rect.top + 40 - PX.OY))
        gs.blit(UIX.stall_bars(rect.w, rect.h), rect.topleft)
      pq = pygame.Rect(rect.x + 10, rect.bottom - 44, rect.w - 20, 38)
      status = "RIDING" if sel else ("IN THE STABLE" if unlocked else "%d COINS" % pal['cost'])
      scol = (20, 90, 20) if sel else ((70, 40, 10) if unlocked else (150, 20, 20))
      gs.blit(UIX.plaque(pq.w, pq.h, (pal['title'], status), ((40, 20, 4), scol)), pq.topleft)
      if sel:
        pygame.draw.rect(gs, BANNER_GOLD, rect.inflate(4, 4), 2, border_radius=12)
    pr = pygame.Rect(WIDTH // 2 - 330, HEIGHT - 116, 560, 50)
    gs.blit(UIX.plaque(pr.w, pr.h, tuple(UIX._wrap(UIX._ink_font(14), DRAGON_PALETTES[hovered]['desc'], pr.w - 30)[:2]), ((50, 24, 6), (50, 24, 6))), pr.topleft)
    pass  # (the tab bar replaces this RETURN button)
    draw_button(gs, RARE_BTN, "ROOST" if rare else "MYTHICAL", BANNER_GOLD, RARE_BTN.collidepoint(self.mouse), (60, 20, 20), BANNER_GOLD, small_font)
    self.draw_pending()

  def draw_pending(self):
    gs = game_surface
    if self.pending:
      dim(gs, 160)
      pop = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 100, 440, 180)
      panel(gs, pop, PARCHMENT, 255, WOOD_DARK, 6, 12)
      pal = DRAGON_PALETTES[self.pending]
      blit_text(gs, small_font, "Unlock %s for %d?" % (pal['title'], pal['cost']), WOOD_DARK, (pop.centerx, pop.top + 50), "center", shadow=False)
      draw_button(gs, BUY_YES, "YES", PARCHMENT, BUY_YES.collidepoint(self.mouse))
      draw_button(gs, BUY_NO, "NO", PARCHMENT, BUY_NO.collidepoint(self.mouse))

  def info_sprite(self, key, fi, fire, sc):
    k = ('info', key, fi, fire, sc)
    s = SCALED.get(k)
    if s is None:
      b = dragon_sprite(key, fi, 0, fire)
      s = SCALED[k] = pygame.transform.scale(b, (int(b.get_width() * sc), int(b.get_height() * sc)))
    return s

  def info_backdrop(self):
    if UIX.art_ok('info'):
      game_surface.blit(UIX.info_backdrop(), (0, 0))
      t = self.anim
      for i, (x, y, rad) in enumerate(UIX.IA.LIGHTS):
        f = 0.75 + 0.2 * math.sin(t * (8 + i) + i * 1.9)
        add_glow(game_surface, int(INFO_OX + x * INFO_K), int(INFO_OY + y * INFO_K), int(rad * INFO_K), (int(54 * f), int(32 * f), 6))
    else:
      self.draw_backdrop_ground()

  def info_title(self, label):
    if UIX.art_ok('info'):
      UIX.info_title(game_surface, label)
    else:
      UIX.draw_title(game_surface, label, 70, self.anim, False)

  def info_panel(self, gs, rect, *a, **k):
    if not UIX.art_ok('info'):                         # (your frame and panel are painted in the background)
      panel(gs, rect, *a, **k)

  def info_floor(self, gs, pr):
    if UIX.art_ok('info'):
      UIX.pedestal(gs, pr.centerx, pr.bottom - 10, int(pr.w * 0.72))
    else:
      pygame.draw.ellipse(gs, (30, 18, 14), (pr.centerx - 120, pr.bottom - 50, 240, 26))

  def info_rule(self, gs, ip, y):
    if UIX.art_ok('info'):
      UIX.gold_divider(gs, ip.left + 12, ip.right - 12, y)
    else:
      pygame.draw.line(gs, STONE_DARK, (ip.left + 16, y), (ip.right - 16, y), 2)

  def info_star(self, gs, x, y, on):
    if UIX.art_ok('info'):
      UIX.gold_star(gs, x, y, on)
    else:
      draw_star(gs, x, y, on)

  def info_button(self, gs, rect, label, col, hov, *a, **k):
    if UIX.art_ok('info'):
      off = col not in (PARCHMENT, BANNER_GOLD)
      UIX.red_button(gs, rect, label, hov and not off, off)
    else:
      draw_button(gs, rect, label, col, hov, *a, **k)

  def draw_dragon_info(self):
    gs = game_surface
    key = self.info_key
    pal = DRAGON_PALETTES[key]
    stars, breath, special = DRAGON_INFO.get(key, ((3, 3, 3, 3), "Dragon fire", "-"))
    unlocked = key in self.data['unlocked']
    self.info_backdrop()
    rare = self.info_from == "RARE_SELECT"
    blit_text(gs, small_font, "MYTHICAL CREATURES" if rare else "DRAGONS ROOST", (236, 222, 196), (24, 22), "midleft")
    self.info_title(pal['title'].upper())
    pr = INFO_PORTRAIT
    self.info_panel(gs, pr, PANEL_DARK, 225, GOLD_BORDER, 4, 12)
    add_glow(gs, pr.centerx, pr.centery + 10, 150, BREATH_GLOW.get(key, (60, 40, 20)))
    self.info_floor(gs, pr)
    t = self.anim
    fire = False                                            # (details page: only the idle flying loop)
    fi = PX.frame_index(t * 7)
    sc = 2.0
    spr = self.info_sprite(key, fi, fire, sc)
    bob = int(math.sin(t * 2.2) * 6)
    sx, sy = pr.centerx - spr.get_width() // 2 - 18, pr.centery - spr.get_height() // 2 - 6 + bob
    gs.set_clip(pr.inflate(-8, -8))
    gs.blit(spr, (sx, sy))
    if fire:
      mox, moy = BREATH_MOUTH.get(key, (0, 0))
      hx, hy = sx + int((PX.OX + 92 + mox) * sc), sy + int((PX.OY + 4 + moy) * sc)
      if key == "UNICORN":
        draw_rainbow_beam(gs, hx, hy, pr.right - hx, int(t * 30))
      fn = {"RED": lava_stream_sprite, "BLUE": frost_stream_sprite, "GREEN": acid_stream_sprite, "ALIEN": acid_stream_sprite, "SILVER": blade_stream_sprite, "SKELETAL": death_stream_sprite, "CHINESE": water_stream_sprite}.get(key)
      if fn:
        gs.blit(fn(int(t * 12) % 4), (hx - 6, hy + 3 - 64))
      else:
        add_glow(gs, hx + 20, hy + 6, 50, BREATH_GLOW.get(key, DEFAULT_GLOW))
    gs.set_clip(None)
    if not unlocked:
      dim(gs, 90, pr.inflate(-8, -8))
    else:                                                  # level badge and XP bar along the top of the picture
      lv_, xp_ = self.dragon_lv(key)
      blit_text(gs, small_font, "LEVEL %d" % lv_, BANNER_GOLD, (pr.left + 22, pr.top + 26), "midleft")
      bar = pygame.Rect(pr.left + 22 + small_font.size("LEVEL 10")[0] + 12, pr.top + 21, 150, 10)
      pygame.draw.rect(gs, (40, 26, 18), bar, border_radius=5)
      cap_ = self.dragon_cap()
      f = 1.0 if lv_ >= cap_ else min(1.0, xp_ / float(dragon_need(lv_)))
      if f > 0:
        pygame.draw.rect(gs, (230, 170, 40), (bar.x, bar.y, max(5, int(bar.w * f)), bar.h), border_radius=5)
      pygame.draw.rect(gs, GOLD_BORDER, bar, 1, border_radius=5)
      txt = ("MAX (cap %d)" % cap_) if lv_ >= cap_ else "%d / %d XP   (cap %d)" % (xp_, dragon_need(lv_), cap_)
      blit_text(gs, tiny_font, txt, (236, 222, 196), (bar.right + 8, bar.centery), "midleft")
      gn = GATK.ground_name(key)
      if gn:                                               # its ground attack, and when it unlocks
        ok_ = lv_ >= GROUND_LEVEL
        gt = ("GROUND ATTACK: %s" % gn) if ok_ else ("GROUND ATTACK at Lv %d: %s" % (GROUND_LEVEL, gn))
        blit_text(gs, tiny_font, gt, (140, 230, 120) if ok_ else (220, 190, 140), (pr.centerx, pr.bottom - 22), "center")
    ip = INFO_PANEL
    self.info_panel(gs, ip, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
    if getattr(self, 'info_page', 'stats') == 'levels':
      self.draw_level_page(gs, ip, key)
      self.info_button(gs, INFO_BACK, "BACK TO ROSTER", PARCHMENT, INFO_BACK.collidepoint(self.mouse), font=small_font)
      self.info_button(gs, INFO_LEVELS, "STATS", PARCHMENT, INFO_LEVELS.collidepoint(self.mouse), font=small_font)
      lab = ("SELECTED" if self.selected == key else "SELECT DRAGON") if unlocked else "UNLOCK  %d" % pal['cost']
      self.info_button(gs, INFO_SELECT, lab, BANNER_GOLD, INFO_SELECT.collidepoint(self.mouse), font=small_font)
      self.draw_coin_panel()
      self.draw_pending()
      return
    words, lines, cur = pal['desc'].split(), [], ''
    for w in words:
      test = (cur + ' ' + w).strip()
      if small_font.size(test)[0] > ip.w - 36 and cur:
        lines.append(cur)
        cur = w
      else:
        cur = test
    lines.append(cur)
    for i, ln in enumerate(lines[:3]):
      blit_text(gs, small_font, ln, PARCHMENT, (ip.left + 18, ip.top + 16 + i * 24), shadow=False)
    y0 = ip.top + 22 + min(3, len(lines)) * 24
    self.info_rule(gs, ip, y0)
    for i, (lab, v) in enumerate(zip(("POWER", "RANGE", "BREATH TIME", "SPEED"), stars)):
      yy = y0 + 28 + i * 36
      blit_text(gs, small_font, lab, (255, 210, 150), (ip.left + 18, yy), "midleft", shadow=False)
      for s_ in range(5):
        self.info_star(gs, ip.right - 118 + s_ * 21, yy, s_ < v)
    y1 = y0 + 28 + 4 * 36 - 8
    self.info_rule(gs, ip, y1)
    secs = ((380 if key == "RED" else 240) + self.data['upgrades']['deep_lungs'] * 60) / float(FPS)
    blit_text(gs, tiny_font, "BREATH:  %s, %.1f s" % (breath, secs), PARCHMENT, (ip.left + 18, y1 + 18), "midleft", shadow=False)
    lv_, xp_ = self.dragon_lv(key)
    if key in ("RED", "GREEN", "ALIEN", "SILVER") and lv_ < GROUND_LEVEL:
      special = "%s (Lv %d)" % (special, GROUND_LEVEL)
    blit_text(gs, tiny_font, "SPECIAL:  %s" % special, PARCHMENT, (ip.left + 18, y1 + 40), "midleft", shadow=False)
    if unlocked:
      st_txt, st_col = ("SELECTED", BANNER_GOLD) if self.selected == key else ("OWNED", (110, 220, 110))
    else:
      st_txt, st_col = "LOCKED  -  %d gold" % pal['cost'], (255, 120, 110)
    blit_text(gs, tiny_font, "STATUS:", PARCHMENT, (ip.left + 18, y1 + 62), "midleft", shadow=False)
    blit_text(gs, tiny_font, st_txt, st_col, (ip.left + 26 + tiny_font.size("STATUS:")[0], y1 + 62), "midleft", shadow=False)
    self.info_button(gs, INFO_BACK, "BACK TO ROSTER", PARCHMENT, INFO_BACK.collidepoint(self.mouse), font=small_font)
    self.info_button(gs, INFO_LEVELS, "LEVEL REWARDS", PARCHMENT, INFO_LEVELS.collidepoint(self.mouse), font=small_font)
    if unlocked:
      lab = "SELECTED" if self.selected == key else "SELECT DRAGON"
    else:
      lab = "UNLOCK  %d" % pal['cost']
    self.info_button(gs, INFO_SELECT, lab, BANNER_GOLD, INFO_SELECT.collidepoint(self.mouse), font=small_font)
    self.draw_coin_panel()
    self.draw_pending()

  def draw_level_page(self, gs, ip, key):
    """dragon details, second page: what each level gives and how to earn XP"""
    lv_, xp_ = self.dragon_lv(key)
    cap_ = self.dragon_cap()
    blit_text(gs, small_font, "LEVEL REWARDS", BANNER_GOLD, (ip.centerx, ip.top + 22), "center", shadow=False)
    gn = GATK.ground_name(key) or "-"
    pk_ = PERK.PERK.get(key)
    rows = ((GROUND_LEVEL, "Ground attack", gn),
            (PERK.LV_SPECIAL, "Stronger special", "Breath lasts 25% longer, hits bosses 25% harder"),
            (PERK.LV_PERK, "Passive skill", PERK.PERK_TEXT.get(pk_, "-")),
            (PERK.LV_ULT, "Ultimate: " + PERK.ULT_NAME.get(key, ""), "Defeat %d foes, then tap ULT to clear the screen" % PERK.ULT_NEED))
    y = ip.top + 46
    for lvn, head, txt_ in rows:
      ok_ = lv_ >= lvn
      col = (140, 230, 120) if ok_ else (220, 190, 140)
      badge = pygame.Rect(ip.left + 14, y, 54, 40)
      pygame.draw.rect(gs, (50, 70, 40) if ok_ else (60, 44, 30), badge, border_radius=8)
      pygame.draw.rect(gs, col, badge, 2, border_radius=8)
      blit_text(gs, tiny_font, "Lv %d" % lvn, col, badge.center, "center", shadow=False)
      im_ = text(small_font, head + ("  (unlocked)" if ok_ else ""), col)
      if im_.get_width() > ip.w - 96:
        im_ = pygame.transform.smoothscale(im_, (ip.w - 96, max(1, int(im_.get_height() * (ip.w - 96) / float(im_.get_width())))))
      gs.blit(im_, (badge.right + 10, y - 2))
      im_ = text(tiny_font, txt_, PARCHMENT)
      if im_.get_width() > ip.w - 96:
        im_ = pygame.transform.smoothscale(im_, (ip.w - 96, max(1, int(im_.get_height() * (ip.w - 96) / float(im_.get_width())))))
      gs.blit(im_, (badge.right + 10, y + 21))
      y += 47
    self.info_rule(gs, ip, y + 2)
    for i, ln in enumerate(("Earn XP every run: score and bosses beaten.",
                            "Your baby companion shares 35% (70% if it matches).",
                            "Level cap %d now: every Adult baby raises it by 1." % cap_)):
      im_ = text(tiny_font, ln, (210, 196, 170))
      if im_.get_width() > ip.w - 30:
        im_ = pygame.transform.smoothscale(im_, (ip.w - 30, max(1, int(im_.get_height() * (ip.w - 30) / float(im_.get_width())))))
      gs.blit(im_, (ip.left + 16, y + 8 + i * 17))

  def bestiary_frames(self, key):
    """Flying / walking frames for one bestiary entry (never attacks)."""
    if key == 'archer':
      return [anim_frame('satyr', 'WALK', i) for i in range(anim_count('satyr', 'WALK'))]
    if key == 'catapult':                              # your catapult art
      return [NF.nf_frame('catapult2', 'crank', i, 1.0)[0] for i in range(NF.nf_count('catapult2', 'crank'))]
    if key in ('trebuchet', 'ballista'):                # your art, at rest
      return [NF.nf_frame(key + '2', 'attack', 0, 1.0)[0]]
    if key in ('catapult', 'trebuchet'):
      kind = 'cat' if key == 'catapult' else 'treb'
      fake = {'fired': False, 'swing': 0, 'timer': 60 if kind == 'cat' else 45}
      ang, ld = siege_pose(fake, kind)
      qa = int(round(ang / 6.0)) * 6
      if kind == 'cat':
        return [cached_sprite(("catapult", qa, ld), 120, 120, 30, 40, lambda s_, x_, y_, qa=qa, ld=ld: draw_catapult(s_, x_, y_, qa, ld))[0]]
      return [cached_sprite(("trebuchet", qa, ld), 160, 160, 45, 60, lambda s_, x_, y_, qa=qa, ld=ld: draw_trebuchet(s_, x_, y_, qa, ld))[0]]
    if key == 'ballista':
      return [cached_sprite(("ballista", 'aiming'), 100, 110, 30, 40, lambda s, x, y: draw_ballista(s, x, y, 'aiming'))[0]]
    if key in ('pyro', 'wiz', 'skel'):
      return [anim_frame(key, 'WALK', i) for i in range(anim_count(key, 'WALK'))]
    if key == 'golem':
      return [extra_frame('golem', i) for i in range(12)]
    if key in ('harpy', 'garg', 'eye'):
      return [anim_frame(key, 'MOVE', i) for i in range(anim_count(key, 'MOVE'))]
    if key == 'imp':
      return [anim_frame('imp', 'MOVE', i) for i in range(anim_count('imp', 'MOVE'))]
    if key == 'spider':
      return [sp_frame('walk', i, 1.0)[0] for i in range(sp_count('walk'))]
    if key == 'cyclops':
      return [cyc_frame('walk', i) for i in range(cyc_count('walk'))]
    if key == 'witch':
      return [ws_frame('w_move', i) for i in range(ws_count('w_move'))]
    if key in ('moth', 'bat'):
      return [night_frame(key, 'fly', i, 2)[0] for i in range(night_count(key, 'fly'))]
    if key in NF.FOE:                                  # the new foes and bosses: their flying loops
      return [NF.nf_frame(NF.ART.get(key, key), 'fly', i, 1.0)[0] for i in range(NF.nf_count(NF.ART.get(key, key), 'fly'))]
    if key in ('sphinx', 'manticore', 'mothman'):
      return [NF.nf_frame(key, 'fly', i, 1.0)[0] for i in range(NF.nf_count(key, 'fly'))]
    if key == 'griffin':
      return list(griffin_frames())
    if key == 'phoenix':
      return [phx_frame('fly', i, 2)[0] for i in range(21)]
    if key == 'demon':
      return [extra_frame('demon', i) for i in range(8)]
    if key == 'jabber':
      return jab_frames()
    if key == 'hydra':
      return hyd_frames()
    if key == 'beholder':
      return beh_frames()
    return [extra_frame('imp', 0)]

  BESTIARY_FPS = {'banshee': 8, 'vulture': 10, 'scarab': 10, 'snake': 10, 'djinn': 9, 'wyrm': 10, 'sphinx': 9, 'manticore': 9, 'mothman': 9, 'beholder': 9, 'hydra': 9, 'jabber': 9, 'moth': 8, 'bat': 12, 'griffin': 6, 'golem': 8, 'cyclops': 8, 'witch': 8, 'demon': 9, 'phoenix': 10}

  def fit_art(self, key, t, bw, bh, cap=4.0):
    """Bestiary picture: every frame cropped to the creature's real outline and scaled by one
    size per creature, so each one fills its box the same way (no jumping between frames)."""
    k = ('best', key, bw, bh, cap)
    fs = SCALED.get(k)
    if fs is None:
      raw = self.bestiary_frames(key)
      box = None
      for f in raw:
        r = f.get_bounding_rect()
        if r.w and r.h:
          box = r if box is None else box.union(r)
      if box is None:
        box = raw[0].get_rect()
      sc = min(cap, bw / float(box.w), bh / float(box.h))
      if sc > 1.5:
        sc = round(sc * 2) / 2.0                      # half-pixel steps keep the pixel art tidy
      size = (max(1, int(box.w * sc)), max(1, int(box.h * sc)))
      fs = []
      for f in raw:
        crop = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        crop.blit(f, (0, 0), box)
        fs.append(pygame.transform.scale(crop, size))
      SCALED[k] = fs
    return fs[int(t * self.BESTIARY_FPS.get(key, 10)) % len(fs)]

  def sketch_art(self, key, t, bw, bh):
    """the creature's animation as a sepia ink drawing for the Monster Manual"""
    self.fit_art(key, t, bw, bh)
    k = ('sketch', key, bw, bh)
    fs = SCALED.get(k)
    if fs is None:
      fs = SCALED[k] = UIX.ink_sketch(SCALED[('best', key, bw, bh, 4.0)])
    return fs[int(t * self.BESTIARY_FPS.get(key, 10)) % len(fs)]

  def draw_enemies(self):
    gs = game_surface
    if UIX.art_ok('bestiary'):                          # your painted library
      UIX.draw_art_book(gs, self, self.anim, self.fit_art)
      UIX.art_title(gs, "BESTIARY", 54, self.anim)
      return
    UIX.draw_book(gs, self, self.anim, self.sketch_art)
    UIX.draw_title(gs, "BESTIARY", 46, self.anim)

  def egg_glow(self, rarity):
    return {'common': (40, 60, 20), 'uncommon': (20, 50, 90), 'rare': (70, 20, 100), 'epic': (110, 60, 8), 'legendary': (90, 40, 120)}[rarity]

  def draw_eggs(self):
    gs = game_surface
    if UIX.art_ok('eggs'):
      return self.draw_art_eggs()
    gs.blit(UIX.hatchery_backdrop(), (0, 0))
    UIX.draw_title(gs, "THE HATCHERY", 46, self.anim)
    eggs = self.data['eggs']
    blit_text(gs, tiny_font, "%d egg%s  -  %d hatched" % (len(eggs), "" if len(eggs) == 1 else "s", self.data.get('hatched', 0)), (230, 210, 180), (EGG_ROOST_BTN.left - 30, EGG_ROOST_BTN.centery), "midright")
    g = EGG_GRID
    cw, ch, gap, pitch = EGG_CARD
    if not eggs:
      pnl = pygame.Rect(WIDTH // 2 - 250, 180, 500, 150)
      panel(gs, pnl, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
      blit_text(gs, small_font, "No eggs yet!", PARCHMENT, (pnl.centerx, pnl.top + 44), "center")
      blit_text(gs, tiny_font, "Defeat a boss and a dragon egg will drop.", (200, 190, 170), (pnl.centerx, pnl.top + 82), "center", shadow=False)
      blit_text(gs, tiny_font, "The harder the boss, the rarer the egg.", (200, 190, 170), (pnl.centerx, pnl.top + 104), "center", shadow=False)
    gs.set_clip(g)
    t = self.anim
    for i, (egg, idxs) in enumerate(self.egg_stacks()):            # identical eggs stack on one card
      n = len(idxs)
      col, row = i % 4, i // 4
      r = pygame.Rect(g.x + col * (cw + gap), int(g.y + row * pitch - self.egg_scroll), cw, ch)
      if r.bottom < g.top or r.top > g.bottom:
        continue
      rar = egg['r']
      gs.blit(UIX.stone_surface(r.w, r.h, RARITY_COL[rar]), r.topleft)         # a little warming nook with an iron cradle
      UIX.hearth_fire(gs, r.centerx, r.top + 118, t + i, 90)
      UIX.cradle(gs, r.centerx, r.top + 82, 64)
      add_glow(gs, r.centerx, r.top + 66, 52, self.egg_glow(rar))
      if n > 1:                                                   # a little pile behind the front egg
        back = egg_sprite(rar, 2, 0, 0)
        for k in range(min(2, n - 1)):
          bx = r.centerx + (-1 if k == 0 else 1) * 30 - back.get_width() // 2
          gs.blit(back, (bx, r.top + 78 - back.get_height() // 2))
      spr = egg_sprite(rar, 3, int(t * 6 + i), math.sin(t * 2.4 + i) * 7)
      gs.blit(spr, (r.centerx - spr.get_width() // 2, r.top + 96 - spr.get_height()))
      UIX.cradle(gs, r.centerx, r.top + 82, 64, front=True)
      UIX.steam(gs, r.centerx, r.top + 40, t + i * 0.4, 3, 12)
      if n > 1:
        bd = pygame.Rect(r.right - 46, r.top + 8, 38, 24)
        pygame.draw.rect(gs, (40, 20, 12), bd, border_radius=10)
        pygame.draw.rect(gs, RARITY_COL[rar], bd, 2, border_radius=10)
        blit_text(gs, small_font, "x%d" % n, PARCHMENT, bd.center, "center", shadow=False)
      pl = pygame.Rect(r.x + 20, r.bottom - 40, r.w - 40, 28)
      gs.blit(UIX.brass_plate(pl.w, pl.h), pl.topleft)
      blit_text(gs, small_font, EGG_STYLE[rar][0], (60, 28, 6), pl.center, "center", shadow=False)
    gs.set_clip(None)
    pass  # (the tab bar replaces this RETURN button)
    used = sum(1 for s in self.data['roosts'] if s)
    draw_button(gs, EGG_ROOST_BTN, "ROOSTS %d/%d" % (used, len(self.data['roosts'])), BANNER_GOLD, EGG_ROOST_BTN.collidepoint(self.mouse), font=small_font)
    if self.eggs_ready():
      draw_badge(gs, EGG_ROOST_BTN.right - 6, EGG_ROOST_BTN.top + 2, self.anim)
    self.draw_coin_panel()

  def draw_art_eggs(self):
    """the Hatchery from your painted egg room"""
    gs = game_surface
    t = self.anim
    gs.blit(UIX._cover_surf('hatch_bg'), (0, 0))
    UIX.art_lights(gs, 'hatch_bg', UIX.EA.LIGHTS, t)
    UIX.art_wide_title(gs, "THE HATCHERY", 54, t, 40, 420)
    self.draw_coin_panel()
    eggs = self.data['eggs']
    g = EGG_GRID
    cw, ch, gap, pitch = EGG_CARD
    if not eggs:
      pl = pygame.Rect(WIDTH // 2 - 260, 200, 520, 110)
      UIX.art_desc_plate(gs, pl, "No eggs yet! Defeat a boss and a dragon egg will drop. The harder the boss, the rarer the egg.")
    gs.set_clip(g)
    for i, (egg, idxs) in enumerate(self.egg_stacks()):
      col, row = i % 4, i // 4
      r = pygame.Rect(g.x + col * (cw + gap), int(g.y + row * pitch - self.egg_scroll), cw, ch)
      if r.bottom < g.top or r.top > g.bottom:
        continue
      hov = r.collidepoint(self.mouse) and g.collidepoint(self.mouse)
      UIX.draw_art_egg_card(gs, r, egg['r'], len(idxs), hov, t, i, self.egg_glow(egg['r']))
    gs.set_clip(None)
    blit_text(gs, tiny_font, "%d egg%s  -  %d hatched" % (len(eggs), "" if len(eggs) == 1 else "s", self.data.get('hatched', 0)), (240, 220, 190), (EGG_ROOST_BTN.left - 24, EGG_ROOST_BTN.centery), "midright")
    used = sum(1 for s in self.data['roosts'] if s)
    UIX.art_wood_button(gs, EGG_ROOST_BTN, "HEARTHS %d/%d" % (used, len(self.data['roosts'])), EGG_ROOST_BTN.collidepoint(self.mouse))
    if self.eggs_ready():
      draw_badge(gs, EGG_ROOST_BTN.right - 6, EGG_ROOST_BTN.top + 2, t)

  def draw_art_roosts(self):
    """the Hatching Hearths from your painted hearth room: eggs warm in its cradles, timers on its brass plates"""
    gs = game_surface
    t = self.anim
    gs.blit(UIX.hearth_backdrop(), (0, 0))
    UIX.hearth_lights(gs, t)
    self.draw_coin_panel()
    roosts = self.data['roosts']
    ink = (60, 30, 8)
    for i, r in enumerate(ROOST_RECTS):
      owned = i < len(roosts)
      slot = roosts[i] if owned else None
      pl = pygame.Rect(r.x + 6, r.y + 2, r.w - 12, int(UIX.HA.PLATE_H * HEARTH_K) - 4)
      cx, cy = UIX.hearth_pt(*UIX.HA.CRADLE[i])
      if owned:                                          # the fire under the cradle
        UIX.fire_flames(gs, cx, int(642 * HEARTH_K), t * 1.1 + i, 0.4)
      if slot:
        rar = slot['r']
        left = self.roost_left(slot)
        hatching = self.hatching and self.hatching['slot'] == i
        if hatching:
          shake = math.sin(self.hatching['t'] * 1.3) * (6 + self.hatching['t'] * 0.3)
        elif left <= 0:
          shake = math.sin(t * 9) * 8
        else:
          shake = math.sin(t * 1.8 + i) * 4
        add_glow(gs, cx, cy - 34, 60, self.egg_glow(rar))
        spr = UIX.art_egg(rar, int(110 * HEARTH_K), shake)
        rim_y = int(572 * HEARTH_K)                      # top of the painted cradle's rim
        ex, ey = UIX.egg_in_cradle(gs, cx + 0, rim_y, int(134 * HEARTH_K), spr, back=False)   # sits in the painted cradle
        UIX.steam(gs, cx, ey + 6, t + i * 0.3, 4, 16)
        if hatching and self.hatching['t'] > 12:          # cracks spreading over the shell
          k = min(6, (self.hatching['t'] - 12) // 4)
          ccx, ccy = cx, ey + spr.get_height() // 2
          pts = [(ccx - 24, ccy - 6), (ccx - 12, ccy + 4), (ccx - 2, ccy - 8), (ccx + 8, ccy + 6), (ccx + 18, ccy - 4), (ccx + 26, ccy + 4), (ccx + 30, ccy - 2)][:k + 1]
          if len(pts) > 1:
            pygame.draw.lines(gs, (255, 250, 220), False, pts, 2)
          if self.hatching['t'] > 34:
            add_glow(gs, ccx, ccy, 90, (140, 120, 60))
          if self.hatching['t'] > 40:                     # the baby dragon pops out
            kk = min(1.0, (self.hatching['t'] - 40) / 12.0)
            bs = baby_frame('idle', int(t * 7), 1.3, self.hatching.get('type'))
            gs.blit(bs, (cx - bs.get_width() // 2, int(ey - 30 * kk - bs.get_height() * 0.5)))
      if not owned:                                      # a cold, locked hearth
        sh = pygame.Surface((r.w, r.h - pl.h), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 120))
        gs.blit(sh, (r.x, pl.bottom))
        tt = UIX._fit_text("HEARTH %d" % (i + 1), pl.w - 16, 16, ink)
        gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 17)))
        if i == len(roosts):
          price = ROOST_PRICES[i - 1]
          tt = UIX._fit_text("build a new hearth", pl.w - 16, 12, (90, 50, 20))
          gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 38)))
          br = pygame.Rect(r.x + 10, r.bottom - 58, r.w - 20, 44)
          UIX.art_wood_button(gs, br, "BUY %d" % price, br.collidepoint(self.mouse) and self.data['coins'] >= price)
        else:
          tt = UIX._fit_text("LOCKED", pl.w - 16, 13, (150, 30, 20))
          gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 38)))
        continue
      if slot:
        left = self.roost_left(slot)
        total = EGG_HATCH_HOURS[slot['r']] * 3600.0
        tt = UIX._fit_text("%s egg" % EGG_STYLE[slot['r']][0], pl.w - 16, 14, ink)
        gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 15)))
        frac = 1.0 - left / total
        UIX.art_quest_bar(gs, pl.x + 4, pl.bottom + 3, pl.w - 8, frac, left <= 0)
        if left > 0:
          s_ = int(left)
          tt = UIX._fit_text("%d:%02d:%02d" % (s_ // 3600, (s_ // 60) % 60, s_ % 60), pl.w - 16, 22, (120, 30, 10))
          gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 36)))
          cost, skip = skip_cost(left)
          sr = speed_rect(r)
          lbl = ("-1 HOUR: %d" if skip >= 3600 else "HATCH NOW: %d") % cost
          UIX.art_wood_button(gs, sr, lbl, sr.collidepoint(self.mouse) and self.data['coins'] >= cost)
        else:
          pulse = (math.sin(t * 6) + 1) / 2
          tt = UIX._fit_text("READY!", pl.w - 16, 22, (int(40 + 60 * pulse), 140, 30))
          gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 36)))
          im = UIX._outlined(UIX._ink_font(15), "tap to hatch", (220, 250, 200))
          gs.blit(im, im.get_rect(center=(r.centerx, r.bottom - 14)))
      else:
        tt = UIX._fit_text("EMPTY", pl.w - 16, 16, ink)
        gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 17)))
        tt = UIX._fit_text("add an egg", pl.w - 16, 12, (90, 50, 20))
        gs.blit(tt, tt.get_rect(center=(pl.centerx, pl.top + 38)))
    UIX.art_wood_button(gs, EGG_ROOST_BTN, "EGGS", EGG_ROOST_BTN.collidepoint(self.mouse))

  def draw_egg_info(self):
    gs = game_surface
    eggs = self.data['eggs']
    if not eggs or self.egg_idx >= len(eggs):
      return
    egg = eggs[self.egg_idx]
    rar = egg['r']
    self.info_backdrop()
    blit_text(gs, small_font, "DRAGON EGG", (236, 222, 196), (24, 22), "midleft")
    self.info_title("%s EGG" % EGG_STYLE[rar][0].upper())
    pr = INFO_PORTRAIT
    self.info_panel(gs, pr, PANEL_DARK, 225, RARITY_COL[rar], 4, 12)
    t = self.anim
    add_glow(gs, pr.centerx, pr.centery, 150 + int(math.sin(t * 3) * 10), self.egg_glow(rar))
    self.info_floor(gs, pr)
    spr = UIX.art_egg(rar, int(pr.h * 0.6), math.sin(t * 2.0) * 6) if UIX.art_ok('eggs') else egg_sprite(rar, 8, int(t * 6), math.sin(t * 2.0) * 6)   # your painted egg
    bob = int(math.sin(t * 2.6) * 5)
    gs.blit(spr, (pr.centerx - spr.get_width() // 2, pr.bottom - 52 - spr.get_height() + bob))
    for k in range(6):                                  # orbiting sparkles
      a = t * 1.6 + k * 1.05
      x = pr.centerx + math.cos(a) * 120
      y = pr.centery - 10 + math.sin(a) * 40
      sz = 2 + (k % 2)
      pygame.draw.line(gs, RARITY_COL[rar], (x - sz * 2, y), (x + sz * 2, y), 1)
      pygame.draw.line(gs, RARITY_COL[rar], (x, y - sz * 2), (x, y + sz * 2), 1)
    ip = INFO_PANEL
    self.info_panel(gs, ip, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
    blit_text(gs, small_font, "RARITY", (255, 210, 150), (ip.left + 18, ip.top + 30), "midleft", shadow=False)
    for s_ in range(5):
      self.info_star(gs, ip.right - 118 + s_ * 21, ip.top + 30, s_ <= RARITY_ORDER.index(rar))
    lines = (("HATCHES IN", "%d hours on a hearth" % EGG_HATCH_HOURS[rar]),
             ("HATCHES INTO", "%s %s baby dragon" % ("An" if EGG_STYLE[rar][0][0] in "AEIOU" else "A", EGG_STYLE[rar][0])))
    for i, (lab, val) in enumerate(lines):
      y = ip.top + 76 + i * 58
      blit_text(gs, small_font, lab, (255, 210, 150), (ip.left + 18, y), "midleft", shadow=False)
      blit_text(gs, tiny_font, val, PARCHMENT, (ip.left + 18, y + 24), "midleft", shadow=False)
    same = sum(1 for e in eggs if e['r'] == rar)
    if same > 1:
      blit_text(gs, tiny_font, "You have %d of these eggs" % same, BANNER_GOLD, (ip.centerx, ip.bottom - 46), "center", shadow=False)
    free = None in self.data['roosts']
    blit_text(gs, tiny_font, "Hearths free: %d of %d" % (self.data['roosts'].count(None), len(self.data['roosts'])), (180, 170, 150), (ip.centerx, ip.bottom - 24), "center", shadow=False)
    self.info_button(gs, INFO_BACK, "BACK", PARCHMENT, INFO_BACK.collidepoint(self.mouse), font=small_font)
    self.info_button(gs, INFO_SELECT, "PLACE ON HEARTH" if free else "HEARTHS FULL", BANNER_GOLD if free else (170, 150, 140), INFO_SELECT.collidepoint(self.mouse), font=small_font)

  def pet_sprite(self, bb, anim, fr, scale, flip=False):
    return baby_frame(anim, fr, round(scale * self.pet_scale(bb['level']), 2), bb.get('type'), flip)

  def draw_bar(self, gs, r, frac, col):
    pygame.draw.rect(gs, (30, 10, 10), r, border_radius=5)
    if frac > 0:
      pygame.draw.rect(gs, col, (r.x, r.y, max(3, int(r.w * min(1.0, frac))), r.h), border_radius=5)
    pygame.draw.rect(gs, GOLD_BORDER, r, 2, border_radius=5)

  def draw_hearts_fx(self, gs, x, y, t):
    for k in range(3):
      u = (t + k * 12) % 36 / 36.0
      hx, hy = int(x - 16 + k * 16 + math.sin(u * 6 + k) * 4), int(y - u * 50)
      if u < 0.95:
        draw_heart(gs, hx, hy, True)

  def draw_hatchlings(self):
    gs = game_surface
    if UIX.art_ok('babies'):
      return self.draw_art_hatchlings()
    self.draw_backdrop_ground()
    UIX.draw_title(gs, "THE NURSERY", 44, self.anim)
    babies = self.data.get('babies', [])
    for bb in babies:
      self.pet_defaults(bb)
    comp = self.find_pet(self.data.get('companion'))
    blit_text(gs, tiny_font, "%d whelp%s" % (len(babies), "" if len(babies) == 1 else "s"), (180, 170, 150), (24, 20), "midleft", shadow=False)
    blit_text(gs, tiny_font, "With you: %s" % (comp['name'] if comp else "none"), (180, 170, 150), (24, 42), "midleft", shadow=False)
    t = self.anim
    if not babies:
      pnl = pygame.Rect(WIDTH // 2 - 250, 180, 500, 150)
      panel(gs, pnl, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
      blit_text(gs, small_font, "No whelps yet!", PARCHMENT, (pnl.centerx, pnl.top + 44), "center")
      blit_text(gs, tiny_font, "Place a dragon egg in a roost and wait for it to hatch.", (200, 190, 170), (pnl.centerx, pnl.top + 90), "center", shadow=False)
    else:
      g = EGG_GRID
      cw, ch, gap, pitch = EGG_CARD
      gs.set_clip(g)
      for i, bb in enumerate(babies):
        col, row = i % 4, i // 4
        r = pygame.Rect(g.x + col * (cw + gap), int(g.y + row * pitch - self.hb_scroll), cw, ch)
        if r.bottom < g.top or r.top > g.bottom:
          continue
        rar = bb['r']
        panel(gs, r, PANEL_DARK, 225, RARITY_COL[rar], 3, 10)
        add_glow(gs, r.centerx, r.top + 64, 50, self.egg_glow(rar))
        spr = self.pet_sprite(bb, 'idle', int(t * 7 + i), 1.1)
        gs.blit(spr, (r.centerx - spr.get_width() // 2, min(r.top + 8, r.bottom - 60 - spr.get_height()) + int(math.sin(t * 3 + i) * 4)))
        blit_text(gs, small_font, bb['name'], PARCHMENT, (r.centerx, r.bottom - 38), "center")
        blit_text(gs, tiny_font, "Lv %d %s" % (bb['level'], DRAGON_PALETTES[bb['type']]['title'].split()[0]), RARITY_COL[rar], (r.centerx, r.bottom - 16), "center", shadow=False)
      gs.set_clip(None)
    self.draw_hb_scrollbar(gs)

  def draw_art_hatchlings(self):
    """the hatchlings' treasure hall from your painted background"""
    gs = game_surface
    t = self.anim
    gs.blit(UIX._cover_surf('baby_bg'), (0, 0))
    UIX.art_lights(gs, 'baby_bg', UIX.YA.LIGHTS, t)
    UIX.art_wide_title(gs, "THE NURSERY", 54, t, 40, 400)
    self.draw_coin_panel()
    babies = self.data.get('babies', [])
    for bb in babies:
      self.pet_defaults(bb)
    comp = self.find_pet(self.data.get('companion'))
    info = UIX._outlined(UIX._ink_font(15), "%d whelp%s" % (len(babies), "" if len(babies) == 1 else "s"), (250, 236, 200))
    gs.blit(info, (20, 14))
    info = UIX._outlined(UIX._ink_font(15), "With you: %s" % (comp['name'] if comp else "none"), (250, 236, 200))
    gs.blit(info, (20, 38))
    if not babies:
      UIX.art_desc_plate(gs, pygame.Rect(WIDTH // 2 - 270, 250, 540, 80), "No whelps yet! Place a dragon egg on a hatching hearth and wait for it to hatch.")
    else:
      g = EGG_GRID
      cw, ch, gap, pitch = EGG_CARD
      gs.set_clip(g)
      for i, bb in enumerate(babies):
        col, row = i % 4, i // 4
        r = pygame.Rect(g.x + col * (cw + gap), int(g.y + row * pitch - self.hb_scroll), cw, ch)
        if r.bottom < g.top or r.top > g.bottom:
          continue
        rar = bb['r']
        hov = r.collidepoint(self.mouse) and g.collidepoint(self.mouse)
        gs.blit(UIX.ART.scaled('egg_frame_gold' if hov else 'egg_frame', r.w, r.h), r.topleft)
        pr = UIX._frac_rect(r, UIX.EA.PLATE)
        add_glow(gs, r.centerx, pr.top - 50, 50, self.egg_glow(rar))
        spr = self.pet_sprite(bb, 'idle', int(t * 7 + i), 1.05)
        gs.blit(spr, (r.centerx - spr.get_width() // 2, pr.top - 6 - spr.get_height() + int(math.sin(t * 3 + i) * 3)))
        nm_ = bb['name'][5:] if bb['name'].startswith("Baby ") else bb['name']   # (the card is too small for the full name)
        t1 = UIX._fit_text(nm_, pr.w - 34, 15, (60, 28, 6))
        gs.blit(t1, t1.get_rect(center=pr.center))
        lv_ = UIX._outlined(UIX._ink_font(13), "Lv %d" % bb['level'], (255, 230, 150))
        gs.blit(lv_, lv_.get_rect(topright=(r.right - 14, r.top + 12)))
      gs.set_clip(None)
    self.draw_hb_scrollbar(gs)

  def hb_max_scroll(self):
    cw, ch, gap, pitch = EGG_CARD
    rows = (len(self.data.get('babies', [])) + 3) // 4
    return max(0, rows * pitch - (pitch - ch) - EGG_GRID.h)

  def draw_hb_scrollbar(self, gs):
    """a scroll bar down the right of the Nursery grid, once there are more whelps than fit"""
    ms = self.hb_max_scroll()
    if ms <= 0:
      return
    tr = HB_SCROLL
    pygame.draw.rect(gs, (40, 26, 16), tr.inflate(6, 6), border_radius=8)
    pygame.draw.rect(gs, (90, 60, 34), tr, border_radius=6)
    full = tr.h + ms
    th = max(44, int(tr.h * tr.h / float(full)))
    ty = tr.top + int((tr.h - th) * min(1.0, self.hb_scroll / float(ms)))
    hot = getattr(self, 'hb_bar', False) or tr.inflate(20, 0).collidepoint(self.mouse)
    pygame.draw.rect(gs, (255, 214, 110) if hot else (226, 172, 60), (tr.x, ty, tr.w, th), border_radius=6)
    pygame.draw.rect(gs, (120, 74, 20), (tr.x, ty, tr.w, th), 2, border_radius=6)
    for k in (-6, 0, 6):                                   # grip lines
      pygame.draw.line(gs, (150, 96, 30), (tr.x + 3, ty + th // 2 + k), (tr.right - 4, ty + th // 2 + k), 1)

  def draw_hatch_info(self):
    gs = game_surface
    babies = self.data.get('babies', [])
    if not babies or self.hb_idx >= len(babies):
      return
    bb = self.pet_defaults(babies[self.hb_idx])
    rar, typ = bb['r'], bb['type']
    self.info_backdrop()
    blit_text(gs, small_font, "%s WHELP" % DRAGON_PALETTES[typ]['title'].split()[0].upper(), (236, 222, 196), (24, 22), "midleft")
    self.info_title(bb['name'].upper())
    pr = INFO_PORTRAIT
    self.info_panel(gs, pr, (30, 20, 16), 230, RARITY_COL[rar], 4, 12)
    t = self.anim
    add_glow(gs, pr.centerx, pr.centery, 140, self.egg_glow(rar))
    back, front = nest_sprites(4)
    gs.blit(back, (pr.centerx - back.get_width() // 2, pr.bottom - 100 - NEST_RAISE * 4))
    react = self.pet_react > 0
    hop = -int(abs(math.sin(self.pet_react * 0.25)) * 26) if react else int(math.sin(t * 2.5) * 6)
    spr = self.pet_sprite(bb, 'attack' if react else 'idle', int(t * 7), 2.4)
    gs.set_clip(pr.inflate(-8, -8))
    gs.blit(spr, (pr.centerx - spr.get_width() // 2, pr.bottom - 64 - spr.get_height() + hop))
    gs.blit(front, (pr.centerx - front.get_width() // 2, pr.bottom - 100 - NEST_RAISE * 4))
    if react:
      self.draw_hearts_fx(gs, pr.centerx, pr.top + 90, 50 - self.pet_react)
    gs.set_clip(None)
    blit_text(gs, tiny_font, "tap to play", (180, 170, 150), (pr.centerx, pr.bottom - 14), "center", shadow=False)
    ip = INFO_PANEL
    self.info_panel(gs, ip, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
    x0 = ip.left + (30 if UIX.art_ok('info') else 18)
    if UIX.art_ok('info'):
      ip = ip.inflate(-24, -16)
    blit_text(gs, small_font, "%s  %s" % (EGG_STYLE[rar][0], DRAGON_PALETTES[typ]['title']), RARITY_COL[rar], (x0, ip.top + 18), "midleft", shadow=False)
    lv = bb['level']
    blit_text(gs, small_font, "LEVEL %d  -  %s" % (lv, self.pet_stage(lv).upper()), (255, 210, 150), (x0, ip.top + 50), "midleft", shadow=False)
    need = self.pet_need(lv)
    self.draw_bar(gs, pygame.Rect(x0, ip.top + 66, ip.w - 36, 12), 1.0 if lv >= PET_MAX_LEVEL else bb['xp'] / float(need), (120, 180, 255))
    blit_text(gs, tiny_font, "MAX LEVEL" if lv >= PET_MAX_LEVEL else "XP %d / %d" % (bb['xp'], need), PARCHMENT, (x0, ip.top + 90), "midleft", shadow=False)
    hp = self.pet_happy(bb)
    blit_text(gs, small_font, "HAPPINESS", (255, 210, 150), (x0, ip.top + 118), "midleft", shadow=False)
    self.draw_bar(gs, pygame.Rect(x0, ip.top + 134, ip.w - 36, 12), hp / 100.0, (110, 220, 110) if hp > 50 else ((240, 190, 60) if hp > 20 else (230, 80, 70)))
    mood = "Overjoyed" if hp > 80 else ("Happy" if hp > 50 else ("Hungry" if hp > 20 else "Very hungry!"))
    blit_text(gs, tiny_font, "%d%%  -  %s" % (int(hp), mood), PARCHMENT, (x0, ip.top + 158), "midleft", shadow=False)
    blit_text(gs, small_font, "POWER", (255, 210, 150), (x0, ip.top + 188), "midleft", shadow=False)
    pw = self.pet_power(bb)
    for s_ in range(5):
      self.info_star(gs, ip.right - 118 + s_ * 21, ip.top + 188, s_ < max(1, min(5, int(round(pw * 2.2)))))
    comp = self.data.get('companion') == bb['id']
    blit_text(gs, tiny_font, "Flies with you and spits %s at foes" % {'RED': 'lava', 'BLUE': 'frost', 'GREEN': 'acid', 'CHRONO': 'time magic', 'YELLOW': 'sparks', 'SILVER': 'gusts', 'CHINESE': 'water', 'SKELETAL': 'soul fire', 'COSMIC': 'starlight', 'UNICORN': 'rainbows', 'WRAITH': 'ghost fire', 'CLOCKWORK': 'tiny rockets', 'FOREST': 'razor leaves', 'COCKATRICE': 'eggs', 'WHALE': 'stardust', 'FEY': 'fairy dust', 'ALIEN': 'acid', 'EAGLE': 'feathers', 'RAVEN': 'dark feathers', 'PERYTON': 'red feathers'}.get(typ, 'fire'), (200, 190, 170), (x0, ip.top + 216), "midleft", shadow=False)
    blit_text(gs, tiny_font, "Grows with every run", (200, 190, 170), (x0, ip.top + 236), "midleft", shadow=False)
    blit_text(gs, tiny_font, "COMPANION" if comp else "Resting in the den", BANNER_GOLD if comp else (170, 160, 150), (x0, ip.top + 262), "midleft", shadow=False)
    labels = ("BACK", "FEED %d" % PET_FEED_COST, "WITH YOU!" if comp else "FLY WITH ME")
    for r, lab in zip(PET_BTNS, labels):
      self.info_button(gs, r, lab, BANNER_GOLD if lab.startswith(("FEED", "FLY", "WITH")) else PARCHMENT, r.collidepoint(self.mouse), font=small_font)
    self.draw_coin_panel()

  def draw_roosts(self):
    """the Hatchery: each roost is a stone hearth with the egg warming in an iron cradle and a big timer above"""
    gs = game_surface
    if UIX.art_ok('hearths'):
      return self.draw_art_roosts()
    gs.blit(UIX.hatchery_backdrop(), (0, 0))
    UIX.draw_title(gs, "HATCHING HEARTHS", 46, self.anim)
    self.draw_coin_panel()
    roosts = self.data['roosts']
    t = self.anim
    for i, r in enumerate(ROOST_RECTS):
      owned = i < len(roosts)
      slot = roosts[i] if owned else None
      hr = pygame.Rect(r.x, r.top + 66, r.w, r.h - 66 - 56)
      gs.blit(UIX.hearth_surface(hr.w, hr.h, owned), hr.topleft)
      if owned:
        UIX.hearth_fire(gs, hr.centerx, hr.bottom - 14, t + i, hr.w - 50)
      pl = pygame.Rect(r.x + 4, r.top, r.w - 8, 60)
      gs.blit(UIX.brass_plate(pl.w, pl.h), pl.topleft)
      cyc = hr.bottom - 74                               # where the cradle sits in the hearth
      ex = ey = 0
      if slot:
        rar = slot['r']
        left = self.roost_left(slot)
        hatching = self.hatching and self.hatching['slot'] == i
        if hatching:
          shake = math.sin(self.hatching['t'] * 1.3) * (6 + self.hatching['t'] * 0.3)
        elif left <= 0:
          shake = math.sin(t * 9) * 8
        else:
          shake = math.sin(t * 1.8 + i) * 4
        UIX.cradle(gs, hr.centerx, cyc, 74)
        add_glow(gs, hr.centerx, cyc - 20, 56, self.egg_glow(rar))
        spr = egg_sprite(rar, 3, int(t * 6 + i), shake)
        ex, ey = hr.centerx - spr.get_width() // 2, cyc + 16 - spr.get_height()
        gs.blit(spr, (ex, ey))
        UIX.cradle(gs, hr.centerx, cyc, 74, front=True)
        UIX.steam(gs, hr.centerx, ey + 6, t + i * 0.3, 4, 16)
        if hatching and self.hatching['t'] > 12:      # cracks spreading over the shell
          k = min(6, (self.hatching['t'] - 12) // 4)
          cx, cy = hr.centerx, ey + spr.get_height() // 2
          pts = [(cx - 24, cy - 6), (cx - 12, cy + 4), (cx - 2, cy - 8), (cx + 8, cy + 6), (cx + 18, cy - 4), (cx + 26, cy + 4), (cx + 30, cy - 2)][:k + 1]
          if len(pts) > 1:
            pygame.draw.lines(gs, (255, 250, 220), False, pts, 2)
          if self.hatching['t'] > 34:
            add_glow(gs, cx, cy, 90, (140, 120, 60))
          if self.hatching['t'] > 40:                     # the baby dragon pops out
            k = min(1.0, (self.hatching['t'] - 40) / 12.0)
            bs = baby_frame('idle', int(t * 7), 1.3, self.hatching.get('type'))
            gs.blit(bs, (hr.centerx - bs.get_width() // 2, int(ey - 30 * k - bs.get_height() * 0.5)))
      elif owned:
        UIX.cradle(gs, hr.centerx, cyc, 74)
        UIX.cradle(gs, hr.centerx, cyc, 74, front=True)
      if not owned:
        dim(gs, 120, r.inflate(-2, -2))
        blit_text(gs, small_font, "HEARTH %d" % (i + 1), (170, 150, 140), (pl.centerx, pl.top + 18), "center", shadow=False)
        if i == len(roosts):
          price = ROOST_PRICES[i - 1]
          br = pygame.Rect(r.x + 16, r.bottom - 62, r.w - 32, 42)
          draw_button(gs, br, "BUY %d" % price, BANNER_GOLD, br.collidepoint(self.mouse), font=small_font)
          blit_text(gs, tiny_font, "build a new hearth", (200, 180, 170), (pl.centerx, pl.top + 42), "center", shadow=False)
        else:
          blit_text(gs, tiny_font, "LOCKED", (200, 160, 160), (pl.centerx, pl.top + 42), "center", shadow=False)
        continue
      if slot:
        left = self.roost_left(slot)
        total = EGG_HATCH_HOURS[slot['r']] * 3600.0
        blit_text(gs, tiny_font, "%s egg" % EGG_STYLE[slot['r']][0], (60, 30, 8), (pl.centerx, pl.top + 13), "center", shadow=False)
        bar = pygame.Rect(pl.x + 10, pl.bottom - 12, pl.w - 20, 6)
        pygame.draw.rect(gs, (60, 30, 10), bar, border_radius=3)
        frac = 1.0 - left / total
        pygame.draw.rect(gs, (110, 200, 90) if left <= 0 else (255, 120, 30), (bar.x, bar.y, max(2, int(bar.w * frac)), bar.h), border_radius=3)
        if left > 0:
          s_ = int(left)
          blit_text(gs, button_font, "%d:%02d:%02d" % (s_ // 3600, (s_ // 60) % 60, s_ % 60), (255, 244, 210), (pl.centerx, pl.top + 33), "center")
          cost, skip = skip_cost(left)
          sr = speed_rect(r)
          lbl = ("-1 HOUR: %d" if skip >= 3600 else "HATCH NOW: %d") % cost
          draw_button(gs, sr, lbl, BANNER_GOLD if self.data['coins'] >= cost else (150, 120, 110), sr.collidepoint(self.mouse), font=tiny_font)
        else:
          pulse = (math.sin(t * 6) + 1) / 2
          blit_text(gs, button_font, "READY!", (int(160 + 95 * pulse), 255, int(120 + 80 * pulse)), (pl.centerx, pl.top + 33), "center")
          blit_text(gs, small_font, "tap to hatch", (220, 240, 200), (r.centerx, r.bottom - 30), "center")
      else:
        blit_text(gs, tiny_font, "HEARTH %d" % (i + 1), (60, 30, 8), (pl.centerx, pl.top + 13), "center", shadow=False)
        blit_text(gs, small_font, "EMPTY", (255, 240, 200), (pl.centerx, pl.top + 33), "center")
        blit_text(gs, tiny_font, "place an egg from", (210, 190, 170), (r.centerx, r.bottom - 40), "center", shadow=False)
        blit_text(gs, tiny_font, "the Hatchery page", (210, 190, 170), (r.centerx, r.bottom - 22), "center", shadow=False)
    draw_button(gs, EGG_ROOST_BTN, "EGGS", BANNER_GOLD, EGG_ROOST_BTN.collidepoint(self.mouse), font=small_font)
    self.draw_coin_panel()

  def draw_enemy_info(self):
    gs = game_surface
    key, name, kind, desc, stars, attack, weak, appears, pts = ENEMY_INFO[self.en_idx]
    boss = kind == "BOSS"
    self.info_backdrop()
    blit_text(gs, small_font, "ENEMIES  %d / %d" % (self.en_idx + 1, len(ENEMY_INFO)), (236, 222, 196), (24, 22), "midleft")
    self.info_title(name.upper())
    pr = INFO_PORTRAIT
    self.info_panel(gs, pr, (40, 14, 14) if boss else PANEL_DARK, 225, BANNER_GOLD if boss else GOLD_BORDER, 4, 12)
    add_glow(gs, pr.centerx, pr.centery, 140, (90, 30, 8) if boss else (40, 40, 60))
    self.info_floor(gs, pr)
    spr = self.fit_art(key, self.anim, pr.w - 40, pr.h - 60, 5.0)
    gs.set_clip(pr.inflate(-8, -8))
    gs.blit(spr, (pr.centerx - spr.get_width() // 2, pr.bottom - 34 - spr.get_height()))
    gs.set_clip(None)
    ip = INFO_PANEL
    self.info_panel(gs, ip, PANEL_DARK, 225, STONE_LIGHT, 3, 12)
    kc = {"BOSS": (255, 120, 110), "FLYING": ICE_BLUE, "GROUND": (200, 180, 140)}[kind]
    blit_text(gs, tiny_font, kind, kc, (ip.left + 18, ip.top + 18), "midleft", shadow=False)
    words, lines, cur = desc.split(), [], ''
    for w in words:
      test = (cur + ' ' + w).strip()
      if tiny_font.size(test)[0] > ip.w - 36 and cur:
        lines.append(cur)
        cur = w
      else:
        cur = test
    lines.append(cur)
    for i, ln in enumerate(lines[:4]):
      blit_text(gs, tiny_font, ln, PARCHMENT, (ip.left + 18, ip.top + 34 + i * 19), shadow=False)
    y0 = ip.top + 42 + min(4, len(lines)) * 19
    self.info_rule(gs, ip, y0)
    for i, (lab, v) in enumerate(zip(("DANGER", "TOUGHNESS", "SPEED"), stars)):
      yy = y0 + 24 + i * 32
      blit_text(gs, small_font, lab, (255, 210, 150), (ip.left + 18, yy), "midleft", shadow=False)
      for s_ in range(5):
        self.info_star(gs, ip.right - 118 + s_ * 21, yy, s_ < v)
    y1 = y0 + 24 + 3 * 32 - 6
    self.info_rule(gs, ip, y1)
    for i, (lab, val) in enumerate((("ATTACK", attack), ("WEAK TO", weak), ("APPEARS", appears), ("POINTS", pts))):
      blit_text(gs, tiny_font, "%s:" % lab, (255, 210, 150), (ip.left + 18, y1 + 16 + i * 21), "midleft", shadow=False)
      blit_text(gs, tiny_font, val, PARCHMENT, (ip.left + 22 + max(86, tiny_font.size("WEAK TO:")[0] + 8), y1 + 16 + i * 21), "midleft", shadow=False)
    self.info_button(gs, EN_PREV, "< PREV", PARCHMENT, EN_PREV.collidepoint(self.mouse), font=small_font)
    self.info_button(gs, EN_BACK, "BACK", PARCHMENT, EN_BACK.collidepoint(self.mouse), font=small_font)
    self.info_button(gs, EN_NEXT, "NEXT >", PARCHMENT, EN_NEXT.collidepoint(self.mouse), font=small_font)

  def draw_intro(self):
    gs = game_surface
    t = self.intro_t
    self.draw_game()
    if t < 180:
      n = 3 - t // 60
      loc = (t % 60) / 60.0
      img = ENV.fire_text(str(n), 150)
      sc = 1.0 + 0.55 * max(0.0, 1 - loc * 5)
      im = pygame.transform.smoothscale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
      if loc > 0.8:
        im.set_alpha(int(255 * (1 - loc) / 0.2))
      add_glow(gs, WIDTH // 2, 170, 120, (90, 40, 8))
      gs.blit(im, im.get_rect(center=(WIDTH // 2, 170)))
    else:
      loc = t - 180
      img = ENV.fire_text("DESTROY!", 104)
      if img.get_width() > WIDTH - 40:
        img = pygame.transform.smoothscale(img, (WIDTH - 40, int(img.get_height() * (WIDTH - 40) / float(img.get_width()))))
      sc = 1.0 + 0.6 * max(0.0, 1 - loc / 12.0)
      im = pygame.transform.smoothscale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
      add_glow(gs, WIDTH // 2, 170, 200, (90, 40, 8))
      gs.blit(im, im.get_rect(center=(WIDTH // 2, 170)))

  def draw_game(self):
    gs, d, st = game_surface, self.dragon, self.state
    self.draw_scenery()
    if getattr(self, 'mode', 'adventure') == 'obstacle':   # the pillars of the obstacle course
      MODE.obstacle_draw(gs, self, self.world(), GROUND_Y)
    self.draw_particles()

    self.draw_holes(gs)
    GATK.draw(gs, self)
    for name in ('towers', 'mages', 'archers', 'catapults', 'trebuchets', 'ballistas', 'golems', 'cyclopes', 'enemies'):
      for o in getattr(self, name):
        if o.get('shattered'):
          continue
        ost = o['state']
        r = o['rect'].copy()
        if ost == 'stunned':
          r.x += random.randint(-4, 4)
          r.y += random.randint(-4, 4)
        if name == 'towers':
          gs.blit(o['surf'], (r.x - o.get('ox', 0), r.y - o.get('top', 15)))
        elif name == 'golems':
          if o['wind'] > 0:
            fi = 12 + min(2, (18 - o['wind']) // 6)
          else:
            fi = (int(self.wing * 0.4) + o['ph']) % 12
          spr = scaled_frame('golem', fi, 1.21)
          gs.blit(spr, (r.centerx - spr.get_width() // 2, r.bottom + 2 - spr.get_height()))
        elif name == 'cyclopes':
          if o['wind'] > 0:
            spr = cyc_frame('throw', min(8, (45 - o['wind']) // 5), 1.25)
          elif o['post'] > 0:
            spr = cyc_frame('throw', 9 + min(7, (40 - o['post']) // 5), 1.25)
          else:
            spr = cyc_frame('walk', int(self.wing * 0.5) + o['ph'], 1.25)
          gs.blit(spr, (r.centerx - int(93 * 1.25), r.bottom + 2 - spr.get_height()))
        elif name == 'mages':
          mk, ax, ay = unit_anchor(name, o)
          if ost == 'stunned':
            anim_blit(gs, mk, 'HURT', int(self.anim * 6), ax, ay)
          elif o.get('atk', 0) > 0:                      # casting
            anim_blit(gs, mk, MAGE_ATTACK[mk], o['atk'] // 3, ax, ay, clamp=True)
          else:
            anim_blit(gs, mk, 'IDLE', int(self.wing * 0.45) + o.get('ph', 0), ax, ay)
        elif name == 'archers':
          k_, ax, ay = unit_anchor(name, o)
          if ost == 'stunned':
            anim_blit(gs, 'satyr', 'HURT', int(self.anim * 6), ax, ay)
          elif 0 < o.get('atk', 0) < 48:                    # draws, aims and looses an arrow
            anim_blit(gs, 'satyr', 'ATTACK', o['atk'] // 4, ax, ay, clamp=True)
          else:
            anim_blit(gs, 'satyr', 'IDLE', int(self.wing * 0.45) + o.setdefault('ph', random.randint(0, 11)), ax, ay)
        elif name == 'catapults':                       # your catapult art: cranks back, then swings and throws
          an_, fi_ = NF.catapult_frame(o, siege_pose)
          spr, ax_, ay_ = NF.nf_frame('catapult2', an_, fi_, clamp=True)
          gs.blit(spr, (r.centerx - ax_, r.bottom + 4 - spr.get_height()))
        elif name in ('trebuchets', 'ballistas'):        # your trebuchet and ballista art
          art = 'trebuchet2' if name == 'trebuchets' else 'ballista2'
          an_, fi_ = NF.trebuchet_frame(o) if name == 'trebuchets' else NF.ballista_frame(o)
          spr, ax_, ay_ = NF.nf_frame(art, an_, fi_, clamp=True)
          gs.blit(spr, (r.centerx - ax_, r.bottom + 4 - spr.get_height()))
        elif o.get('kind') == 'wyvern':
          wf = int(((self.wing * 1.6 + o['phase']) % (2 * math.pi)) / (2 * math.pi) * 6) % 6
          k_, ax, ay = unit_anchor(name, o)
          an = 'HURT' if ost == 'stunned' else ('ATTACK' if o.get('ds', -1) in (1, 2) else 'MOVE')
          anim_blit(gs, 'eye', an, wf, ax, ay)
        else:
          frame = int(((self.wing * 0.8 + o['phase']) % (2 * math.pi)) / (2 * math.pi) * 6) % 6
          if o.get('foe') == 'spider':
            vx, vy = o.get('vx', -3.0), o.get('vy', 2.0)
            ln = math.hypot(vx, vy) or 1.0
            ux, uy = -vx / ln, -vy / ln                  # silk trails back along the fall path
            px_, py_ = r.centerx + 4, r.top + 4
            prev = (px_, py_)
            for k in range(1, 16):
              u = k / 15.0
              wav = math.sin(u * 6 + o['age'] * 0.2) * 4 * u
              pt = (int(px_ + ux * 95 * u - uy * wav), int(py_ + uy * 95 * u + ux * wav))
              c = int(235 - 150 * u)
              pygame.draw.line(gs, (c, c + 4 if c < 251 else 255, min(255, c + 20)), prev, pt, 1)
              prev = pt
            spr, ax_, ay_ = sp_frame('walk', int(o['age'] * 0.3 + o['phase'] * 3))   # legs paddling as it drifts on its silk
            gs.blit(spr, (r.centerx - ax_ + int(math.sin(o['age'] * 0.15) * 3), r.centery - ay_))
          elif o.get('foe') in ('moth', 'bat'):
            k_ = o['foe']
            if o.get('cast', 0) > 0:
              spr, ax, ay = night_frame(k_, 'attack', min(16, int(o['cast'] / (3 if k_ == 'moth' else 2))), NIGHT_SCALE[k_])
            else:
              spr, ax, ay = night_frame(k_, 'fly', int(o['age'] * (0.35 if k_ == 'moth' else 0.5) + o['phase'] * 3), NIGHT_SCALE[k_])
            if k_ == 'moth' and o.get('cast', 0) > 20:
              add_glow(gs, r.centerx - 30, r.centery - 6, 44, (60, 20, 80))
            gs.blit(spr, (r.centerx - ax, r.centery - ay))
          elif o.get('isle'):
            ISL.draw(gs, self, o)
          elif o.get('nf'):
            NF.draw(gs, self, o)
          elif o.get('foe') == 'witch':
            if o.get('cast', 0) > 0:
              spr = ws_frame('w_attack', min(5, int(o['cast'] / 6)), 1.3)
            else:
              spr = ws_frame('w_move', int(o['age'] * 0.15), 1.3)
            add_glow(gs, r.centerx - 10, r.centery - 6, 40, (20, 60, 20))
            gs.blit(spr, (r.centerx - spr.get_width() // 2 + 4, r.bottom + 8 - spr.get_height()))
          elif o.get('foe') == 'imp':
            k_, ax, ay = unit_anchor(name, o)
            near = 0 < r.x - self.dragon.right < 170 and abs(r.centery - self.dragon.centery) < 90
            an = 'HURT' if ost == 'stunned' else ('ATTACK' if near else 'MOVE')
            anim_blit(gs, 'imp', an, int(self.wing * 0.5 + o['phase'] * 2), ax, ay + int(math.sin(self.anim * 6 + o['phase']) * 3))
          elif o.get('foe') == 'garg':
            k_, ax, ay = unit_anchor(name, o)
            an = 'HURT' if ost == 'stunned' else ('ATTACK_1' if o.get('ds', -1) == 2 else 'MOVE')
            anim_blit(gs, 'garg', an, frame if an == 'MOVE' else int(self.anim * 9), ax, ay)
          else:
            k_, ax, ay = unit_anchor(name, o)
            an = 'HURT' if ost == 'stunned' else ('ATTACK' if o.get('ds', -1) == 2 else 'MOVE')
            anim_blit(gs, 'harpy', an, frame if an == 'MOVE' else int(self.anim * 9), ax, ay)
        if name == 'enemies' and o.get('ds') == 1:
          pulse = 120 + int(100 * abs(math.sin(o['dt'] * 0.5)))
          add_glow(gs, r.centerx, r.centery, 46, (pulse, 10, 10))
          blit_text(gs, button_font, "!", (255, 90, 60), (r.centerx, r.top - 18), "center")
        elif name == 'enemies' and o.get('ds') == 2:
          for k in range(3):
            pygame.draw.line(gs, (255, 150, 90), (r.right + 4, r.y + 8 + k * (r.h - 16) // 2), (r.right + 34 + k * 8, r.y + 8 + k * (r.h - 16) // 2), 2)
        if ost == 'stasis':
          draw_stasis(gs, r)
        if ost == 'frozen':
          gs.blit(ice_sprite(r.w, r.h), (r.x - 5, r.y - 5))
        elif ost == 'melted':
          gs.blit(acid_sprite(r.w, r.h, (pygame.time.get_ticks() // 120) % 2), (r.x - 5, r.y - 5))
        elif ost == 'stunned':
          for _ in range(4):
            pygame.draw.circle(gs, (255, 255, 100), (r.x + random.randint(0, r.w), r.y + random.randint(0, r.h)), random.randint(2, 4))

    self.draw_curse(gs)
    for sp in self.spears:
      L = math.hypot(sp['vx'], sp['vy']) or 1.0
      ux, uy = sp['vx'] / L, sp['vy'] / L
      hx, hy = int(sp['x']), int(sp['y'])
      add_glow(gs, hx + 4, hy, 30, (150, 60, 8))
      for i in range(12):
        t = i / 12.0
        tx, ty = sp['x'] - ux * (66 + i * 4) + random.uniform(-3, 3), sp['y'] - uy * (66 + i * 4) + random.uniform(-4, 4) * (0.4 + t)
        pygame.draw.circle(gs, (255, int(210 - 170 * t), int(70 - 60 * t)), (int(tx), int(ty)), int(5 * (1 - t)) + 1)
      spr = bolt_sprite(int(round(math.degrees(math.atan2(-sp['vy'], -sp['vx'])) / 6.0)) * 6)
      cx, cy = sp['x'] - ux * 38, sp['y'] - uy * 38
      gs.blit(spr, (int(cx - spr.get_width() / 2), int(cy - spr.get_height() / 2)))

    for o in self.orbs:
      if o.get('kind') == 'sonic' and not o.get('shattered'):          # bat screech: rings of red sound
        o['fr'] = o.get('fr', 0) + 1
        th = math.atan2(-o['vy'], o['vx'])
        add_glow(gs, int(o['x']), int(o['y']), 30, (20, 50, 70) if o.get('pal') else (70, 10, 16))
        for k in range(3):
          rad = 8 + k * 7 + (o['fr'] % 6)
          cxo, cyo = o['x'] - math.cos(th) * rad, o['y'] + math.sin(th) * rad
          col = o.get('pal', ((255, 230, 230), (255, 90, 100), (200, 30, 50)))[k]
          pygame.draw.arc(gs, col, (int(cxo - rad), int(cyo - rad), rad * 2, rad * 2), th - 0.9, th + 0.9, 3 if k else 2)
        continue
      if o.get('kind') == 'mothorb' and not o.get('shattered'):        # moth magic: a pulsing violet sphere with sparkles
        o['fr'] = o.get('fr', 0) + 1
        ox_, oy_ = int(o['x']), int(o['y'])
        add_glow(gs, ox_, oy_, 34, (70, 24, 96))
        pr_ = 11 + int(abs(math.sin(o['fr'] * 0.25)) * 3)
        pygame.draw.circle(gs, (120, 40, 190), (ox_, oy_), pr_)
        pygame.draw.circle(gs, (210, 140, 255), (ox_, oy_), pr_ - 3)
        pygame.draw.circle(gs, (255, 240, 255), (ox_ - 2, oy_ - 2), 4)
        for k in range(4):
          a = o['fr'] * 0.18 + k * math.pi / 2
          sx_, sy_ = ox_ + int(math.cos(a) * (pr_ + 6)), oy_ + int(math.sin(a) * (pr_ + 6))
          pygame.draw.line(gs, (255, 220, 255), (sx_ - 3, sy_), (sx_ + 3, sy_), 1)
          pygame.draw.line(gs, (255, 220, 255), (sx_, sy_ - 3), (sx_, sy_ + 3), 1)
        continue
      if o.get('kind') == 'witchbolt' and not o.get('shattered'):
        o['fr'] = o.get('fr', 0) + 0.4
        spr = ws_frame('w_bolt', int(o['fr']), 2.0)
        ang = math.degrees(math.atan2(-o['vy'], -o['vx']))          # the art points left
        rs = pygame.transform.rotate(spr, -ang if abs(ang) > 0.5 else 0)
        add_glow(gs, int(o['x']), int(o['y']), 26, (30, 80, 30))
        gs.blit(rs, (int(o['x']) - rs.get_width() // 2, int(o['y']) - rs.get_height() // 2))
        continue
      if not o.get('shattered') and o.get('kind') == 'seeker':      # Beholder's heat-seeking eyeballs
        draw_seeker(gs, o)
        continue
      if not o.get('shattered') and o.get('kind') in ('wiz', 'skel'):
        o['fr'] = o.get('fr', 0) + 0.35
        nm = 'wiz_orb' if o['kind'] == 'wiz' else 'skel_orb'
        spr = proj_frame(nm, int(o['fr']), 1.3 if nm == 'wiz_orb' else 2.2)
        ang = math.degrees(math.atan2(-o['vy'], -o['vx']))
        rs = pygame.transform.rotate(spr, -int(ang // 15) * 15)
        oc = o.get('col', MAGIC_PURPLE)
        add_glow(gs, int(o['x']), int(o['y']), int(o.get('r', 12) * 2.2), (oc[0] // 3, oc[1] // 3, oc[2] // 3))
        gs.blit(rs, (int(o['x']) - rs.get_width() // 2, int(o['y']) - rs.get_height() // 2))
        continue
      if not o.get('shattered'):
        ox_, oy_ = int(o['x']), int(o['y'])
        oc = o.get('col', MAGIC_PURPLE)
        orr = o.get('r', 12)
        add_glow(gs, ox_, oy_, int(orr * 2.2), (oc[0] // 3, oc[1] // 3, oc[2] // 3))
        if not o.get('home', True):
          ol = math.hypot(o['vx'], o['vy']) or 1.0
          pygame.draw.line(gs, oc, (ox_, oy_), (int(ox_ - o['vx'] / ol * 22), int(oy_ - o['vy'] / ol * 22)), 3)
        pygame.draw.circle(gs, oc, (ox_, oy_), orr)
        pygame.draw.circle(gs, (min(255, oc[0] + 90), min(255, oc[1] + 90), min(255, oc[2] + 90)), (ox_, oy_), max(2, orr * 2 // 3))
        pygame.draw.circle(gs, (255, 255, 255), (ox_, oy_), max(2, orr // 3))

    for a in self.arrows:
      if not a.get('shattered') and a.get('kind') in ('icicle', 'icicle_fall'):   # hydra ice shards
        spr = icicle_sprite(math.degrees(math.atan2(a['vy'], a['vx'])))
        add_glow(gs, int(a['x']), int(a['y']), 16, (30, 60, 90))
        gs.blit(spr, (int(a['x']) - spr.get_width() // 2, int(a['y']) - spr.get_height() // 2))
      elif not a.get('shattered') and a.get('kind') == 'feather':
        draw_feather(gs, a)
      elif not a.get('shattered') and a.get('kind') == 'log':
        q = int(a.get('rot', 0.0) * 40 / 15.0) % 24
        k = ('logrot', q)
        spr = SCALED.get(k)
        if spr is None:
          spr = SCALED[k] = pygame.transform.rotate(cyc_frame('club', 0, 1.25), -q * 15)
        gs.blit(spr, (int(a['x']) - spr.get_width() // 2, int(a['y']) - spr.get_height() // 2))
      elif not a.get('shattered') and a.get('kind') == 'boulder':
        spr = scaled_frame('boulder', int(a.get('rot', 0.0)) % 8, 1.5)
        gs.blit(spr, (int(a['x']) - 18, int(a['y']) - 18))
      elif not a.get('shattered') and a.get('kind') == 'satyr':
        ang = math.degrees(math.atan2(-a['vy'], -a['vx']))          # the art points left
        q = int(round(ang / 10.0)) * 10
        k = ('satyr_arrow', q)
        spr = SCALED.get(k)
        if spr is None:
          spr = SCALED[k] = pygame.transform.rotate(proj_frame('arrow', 0, 1.3), -q)
        gs.blit(spr, (int(a['x']) - spr.get_width() // 2, int(a['y']) - spr.get_height() // 2))
      elif not a.get('shattered'):
        ax, ay = int(a['x']), int(a['y'])
        ang = math.atan2(a.get('vy', 0), a.get('vx', 1))
        ex, ey = ax + math.cos(ang) * 15, ay + math.sin(ang) * 15
        ca, sa = math.cos(ang), math.sin(ang)
        add_glow(gs, int(ex), int(ey), 24, (150, 60, 8))
        for i in range(8):
          t = i / 8.0
          pr = int(5 * (1 - t)) + 1
          pygame.draw.circle(gs, (255, int(200 - 150 * t), int(60 - 50 * t)), (int(ax - ca * (8 + i * 4) + random.uniform(-2, 2)), int(ay - sa * (8 + i * 4) + random.uniform(-2, 2))), pr)
        pygame.draw.line(gs, WOOD_BROWN, (ax - ca * 15, ay - sa * 15), (ex, ey), 3)
        pygame.draw.polygon(gs, (255, 225, 110), [(ex + ca * 9, ey + sa * 9), (ex - sa * 5, ey + ca * 5), (ex + sa * 5, ey - ca * 5)])
        pygame.draw.circle(gs, (255, 255, 230), (int(ex + ca * 3), int(ey + sa * 3)), 2)

    for fb in self.fireballs:
      if fb.get('ember') and not fb.get('shattered'):          # phoenix fire feather
        x, y = int(fb['x']), int(fb['y'])
        ang = math.atan2(fb['vy'], fb['vx'])
        ca, sa = math.cos(ang), math.sin(ang)
        add_glow(gs, x, y, 22, (120, 40, 5))
        pygame.draw.polygon(gs, (220, 60, 20), [(x + ca * 11, y + sa * 11), (x - sa * 5, y + ca * 5), (x - ca * 9, y - sa * 9), (x + sa * 5, y - ca * 5)])
        pygame.draw.polygon(gs, (255, 190, 60), [(x + ca * 7, y + sa * 7), (x - sa * 2, y + ca * 2), (x - ca * 5, y - sa * 5), (x + sa * 2, y - ca * 2)])
        continue
      if not fb.get('shattered') and fb.get('kind') == 'pyro':
        fb['fr'] = fb.get('fr', 0) + 0.3
        ang = math.degrees(math.atan2(-fb['vy'], -fb['vx']))
        spr = pygame.transform.rotate(proj_frame('fire', int(fb['fr'])), -int(ang // 15) * 15)
        add_glow(gs, int(fb['x']), int(fb['y']), 34, (130, 50, 5))
        gs.blit(spr, (int(fb['x']) - spr.get_width() // 2, int(fb['y']) - spr.get_height() // 2))
        continue
      if not fb.get('shattered'):
        add_glow(gs, int(fb['x']), int(fb['y']), 34, (130, 50, 5))
        pygame.draw.circle(gs, (255, 120, 10), (int(fb['x']), int(fb['y'])), 15)
        pygame.draw.circle(gs, FIRE_CORE, (int(fb['x']), int(fb['y'])), 9)

    for coin in self.coins:
      gs.blit(coin_sprite(int(self.anim * 4) + coin['rect'].y), (coin['rect'].x - 3, coin['ry'] - 2))
    for pu in self.powerups:
      cx_, cy_ = pu['rect'].centerx, pu['ry'] + pu['rect'].h // 2
      add_glow(gs, cx_, cy_, 35 + int(math.sin(pu['t'] * 2) * 6), (110, 30, 10))
      spr = big_crystal(int(pu['t'] * 1.5))
      gs.blit(spr, (cx_ - spr.get_width() // 2, cy_ - spr.get_height() // 2))

    b = self.boss
    if b:
      if b['type'] == 'griffin':
        draw_griffin_boss(gs, b)
      elif b['type'] == 'jabber':
        self.draw_jabber(gs, b)
      elif b['type'] == 'beholder':
        self.draw_beholder(gs, b)
      elif b['type'] == 'hydra':
        self.draw_hydra(gs, b)
      elif b['type'] in NB.NEW_BOSSES:
        NB.draw(gs, b)
      elif b['type'] == 'demon':
        self.draw_demon(gs, b)
      elif b['type'] == 'phoenix':
        self.draw_phoenix(gs, b)
      else:
        draw_zeppelin(gs, int(b['x']), int(b['y']), b['timer'])

    for c in getattr(self, 'corpses', ()):             # enemy death animations
      if c['k'] in ('moth', 'bat'):
        spr, ax, ay = night_frame(c['k'], 'death', min(c['n'] - 1, c['t'] // c.get('rate', 3)), NIGHT_SCALE[c['k']])
        if c['t'] > c['n'] * c.get('rate', 3):            # fades once it has landed
          spr = spr.copy()
          spr.set_alpha(max(0, 255 - (c['t'] - c['n'] * c.get('rate', 3)) * 9))
        gs.blit(spr, (int(c['x']) - ax, int(c['y']) - ay))
      elif c['k'] == 'cyclops':
        gs.blit(cyc_frame('death', min(c['n'] - 1, c['t'] // 5), 1.25), (int(c['x']), int(c['y'])))
      elif c['k'] == 'nf':
        NF.draw_corpse(gs, c)
      elif c['k'] == 'siege':                            # buckling: shakes, leans over and flashes before it bursts
        f = c['t'] / float(c['rate'])
        key = ('siege_lean', id(c['img']), int(f * 8), c['lean'])
        spr = SCALED.get(key)
        if spr is None:
          src = c['img']
          ck = src.get_colorkey() if hasattr(src, 'get_colorkey') else None
          if ck is not None:                             # real alpha first, so turning it doesn't show the key colour
            src = src.copy()
            src.set_colorkey(ck)
            try:
              src = src.convert_alpha()
            except Exception:
              pass
          spr = pygame.transform.rotate(src, c['lean'] * int(f * 8) * 3)
          if len(SCALED) > 900:
            SCALED.clear()
          SCALED[key] = spr
        w0, h0 = c['img'].get_size()
        jx, jy = random.randint(-3, 3), random.randint(-2, 2)
        gs.blit(spr, (int(c['x']) + w0 // 2 - spr.get_width() // 2 + jx, int(c['y']) + h0 - spr.get_height() + jy + int(f * 6)))
        if c['t'] % 4 < 2:
          add_glow(gs, int(c['cx']), int(c['cy']), 46, (90, 40, 10))
      elif c['k'] == 'witch':
        spr = ws_frame('w_death', min(c['n'] - 1, c['t'] // c['rate']), 1.3)
        end = c['n'] * c['rate']
        if c['t'] > end:
          spr = spr.copy()
          spr.set_alpha(max(0, 255 - (c['t'] - end) * 9))
        gs.blit(spr, (int(c['x']), int(c['y'])))
      elif c['k'] == 'spider':                           # your spider's own death animation, then it fades
        spr, ax_, ay_ = sp_frame('death', c['t'] // c['rate'], clamp=True)
        end = c['n'] * c['rate']
        if c['t'] > end:
          spr = spr.copy()
          spr.set_alpha(max(0, 255 - (c['t'] - end) * 9))
        gs.blit(spr, (int(c['x']) - ax_, int(c['y']) - ay_))
      else:
        anim_blit(gs, c['k'], c.get('anim', 'DEATH'), c['t'] // c.get('rate', 4), c['x'], c['y'], clamp=True)
    for p in self.rubble:
      q = int(p['rot'] / 30) % 12
      img = p['rots'].get(q)
      if img is None:
        img = p['rots'][q] = pygame.transform.rotate(p['img'], q * 30)
      gs.blit(img, (int(p['x']), int(p['y'])))
    for t in self.tornados:
      spr = tornado_sprite(int(t['f']))
      add_glow(gs, int(t['x']), int(t['y']) - 50, 60, (30, 50, 80))
      if t['y'] >= GROUND_Y - 10:
        gs.blit(spr, (int(t['x']) - spr.get_width() // 2, GROUND_Y + 12 - spr.get_height()))
      else:
        small = pygame.transform.scale(spr, (spr.get_width() // 3, spr.get_height() // 3))
        gs.blit(small, (int(t['x']) - small.get_width() // 2, int(t['y']) - small.get_height() // 2))

    if self.egg_drop:
      e = self.egg_drop
      add_glow(gs, int(e['x']), int(e['y']), 46 + int(math.sin(self.anim * 6) * 6), (90, 80, 40))
      spr = egg_sprite(e['r'], 2, int(self.anim * 8), math.sin(self.anim * 5) * 9)
      gs.blit(spr, (int(e['x']) - spr.get_width() // 2, int(e['y']) - spr.get_height() // 2))

    for pts, col, w in self.bolts:
      pygame.draw.lines(gs, (40, 90, 200), False, pts, w + 6)
      pygame.draw.lines(gs, col, False, pts, w)
      pygame.draw.lines(gs, (255, 255, 240), False, pts, max(1, w - 4))

    if UIX.art_ok('level'):
      UIX.level_ground(gs, self.world(), getattr(self, 'ground_x', 0.0), not self.day)
    else:
      gs.blit(GROUND, (0, GROUND_Y))
      self.lift_ground(gs)
    if self.lava:
      fr = int(self.anim * 12)
      for p in self.lava:
        if p['life'] < 50 and (p['life'] // 4) % 2 == 0:
          continue
        if self.selected == "RED":
          gs.blit(lava_pool_sprite((fr + int(p['x'])) % 4), (int(p['x']) - 40, GROUND_Y - 38))
        else:
          gs.blit(acid_pool_sprite((fr + int(p['x'])) // 2), (int(p['x']) - 40, GROUND_Y - 74))

    if self.dash_state == 'out':
      add_glow(gs, d.centerx + 20, d.centery, 90, (120, 60, 12))
      for k in range(5):
        yy = d.y + 4 + k * 8
        pygame.draw.line(gs, (255, 230, 170), (d.x - 20 - k * 6, yy), (d.x - 90 - k * 14, yy), 2)
    dd = getattr(self, 'death', None)
    if st == "GAMEOVER" and dd is not None:
      dd.draw(gs)
    elif self.hit_inv <= 0 or (self.hit_inv // 4) % 2 == 0:
      if self.flip_t > 0:
        self.draw_flip_dragon(gs, d)
      else:
        if self.selected in TALON_DRAGONS:            # dives (attack frames) only while it strikes
          tl = getattr(self, 'talon', None)
          if self.breath:
            add_glow(gs, d.centerx, d.centery, 60, (70, 50, 14))
          if tl and tl.get('dir', 1) < 0:               # diving back to the left: the frames are mirrored
            tmp = getattr(self, '_eagle_tmp', None)
            if tmp is None:
              tmp = self._eagle_tmp = pygame.Surface((168, 128), pygame.SRCALPHA)
            tmp.fill((0, 0, 0, 0))
            draw_any_dragon(tmp, self.selected, PX.OX, PX.OY, 0, self.flap_ph, True, False)
            gs.blit(pygame.transform.flip(tmp, True, False), (d.x + d.w - 168 + PX.OX, d.y - PX.OY))
          else:
            draw_any_dragon(gs, self.selected, d.x, d.y, 0 if tl else int(self.vel * 0.8), self.flap_ph, bool(tl), getattr(self, 'flap_left', 0.0) > 0 and not tl)
        elif self.selected == "WRAITH" and getattr(self, 'phase_a', 0.0) > 0:
          self.draw_phased(gs, d)
        else:
          draw_any_dragon(gs, self.selected, d.x, d.y, int(self.vel * 0.8), self.flap_ph, self.breath, getattr(self, 'flap_left', 0.0) > 0)
    pet = getattr(self, 'pet', None)
    if pet and st in ("PLAYING", "PAUSED", "INTRO") and hasattr(self, 'pet_pos'):
      for s in self.pet_shots:
        spr = baby_frame('shot', int(s['fr']), 1.6, pet['type'], True)
        add_glow(gs, int(s['x']), int(s['y']), 22, BREATH_GLOW.get(pet['type'], DEFAULT_GLOW))
        gs.blit(spr, (int(s['x']) - spr.get_width() // 2, int(s['y']) - spr.get_height() // 2))
      ps = baby_frame('attack' if self.pet_atk > 0 else 'move', int(self.anim * 8) if self.pet_atk <= 0 else min(5, (18 - self.pet_atk) // 3),
                      round(0.62 * self.pet_scale(pet['level']), 2), pet['type'], True)
      gs.blit(ps, (int(self.pet_pos[0]) + 30 - ps.get_width() // 2, int(self.pet_pos[1]) + 20 - ps.get_height() // 2))
    if self.breath:
      hx, hy = breath_origin(self.selected, d, self.flap_ph, self.vel, self.pitch)
      add_glow(gs, hx, hy + 6, 70, BREATH_GLOW.get(self.selected, DEFAULT_GLOW))
      if self.selected == "UNICORN":
        draw_rainbow_beam(gs, hx, hy, getattr(self, 'beam_len', 0), int(pygame.time.get_ticks() / 33))
      if self.selected == "WHALE":
        self.draw_maw(gs, hx, hy)
      sl = getattr(self, 'siphon_line', None)
      if self.selected == "WRAITH" and sl:
        add_glow(gs, int(sl[2]), int(sl[3]), 40, (20, 80, 100))
        draw_siphon(gs, sl[0], sl[1], sl[2], sl[3], int(pygame.time.get_ticks() / 33))
      if self.selected == "SILVER":                       # the Wind dragon's gale: streaks of wind tearing forward across the blast zone
        self.draw_gale(gs, d)
      if self.selected in ("RED", "BLUE", "GREEN", "ALIEN", "SKELETAL"):   # (the Wind and Lung dragons' attacks are in their own frames)
        fr = int(self.anim * 14)
        gs.blit(({"RED": lava_stream_sprite, "BLUE": frost_stream_sprite, "GREEN": acid_stream_sprite, "ALIEN": acid_stream_sprite, "SILVER": blade_stream_sprite, "SKELETAL": death_stream_sprite, "CHINESE": water_stream_sprite}[self.selected])(fr % 4), (hx - 6, hy + 3 - 64))
    if getattr(self, 'novas', None):                     # Fey Dragon's Glamour Nova rings
      self.draw_novas(gs)
    for bf in getattr(self, 'butterflies', ()):
      self.draw_butterfly(gs, bf)
    for lf in getattr(self, 'leaves', ()):               # Forest Dragon's razor leaves
      spr = leaf_sprite(lf['rot'], lf['col'])
      gs.blit(spr, (int(lf['x']) - spr.get_width() // 2, int(lf['y']) - spr.get_height() // 2))
    for eg in getattr(self, 'eggs_shot', ()):            # Cockatrice eggs and the chicks that hatch from them
      spr = egg_shot_sprite(eg['rot'])
      gs.blit(spr, (int(eg['x']) - spr.get_width() // 2, int(eg['y']) - spr.get_height() // 2))
    for c in getattr(self, 'chicks', ()):
      spr = chick_sprite(c['t'] // 2 + c['flap'], c['vx'] < 0)
      gs.blit(spr, (int(c['x']) - 21, int(c['y']) - 16))
    for v in getattr(self, 'vines', ()):                 # Forest Dragon's bramble vines
      draw_vine(gs, v, self.vine_frac(v), GROUND_Y + 6)
    hd = getattr(self, 'heart_drop', None)
    if hd:                                              # the heart power-up a boss leaves behind
      add_glow(gs, int(hd['x']), int(hd['y']), 40 + int(math.sin(hd['t'] * 0.15) * 6), (110, 20, 30))
      h_ = life_heart(True, int(hd['t'] / 6), 46)
      gs.blit(h_, (int(hd['x']) - 23, int(hd['y']) - 23))
    for m in getattr(self, 'missiles', ()):              # Clockwork Dragon's missiles
      draw_missile(gs, m)
    for bm in getattr(self, 'booms', ()):
      add_glow(gs, int(bm['x']), int(bm['y']), 50, (120, 70, 10))
      draw_boom(gs, bm)
    for w in getattr(self, 'souls', ()):                 # Wraith Wyrm's hunting souls
      add_glow(gs, int(w['x']), int(w['y']), 22, (20, 70, 90))
      draw_soul(gs, w)
    for g in self.globs:
      gx, gy = int(g[0]), int(g[1])
      if self.selected in ("GREEN", "ALIEN"):
        pygame.draw.circle(gs, (60, 160, 76), (gx, gy), 7)
        pygame.draw.circle(gs, (140, 238, 120), (gx, gy), 5)
        pygame.draw.circle(gs, (255, 255, 255), (gx - 2, gy - 2), 2)
      else:
        pygame.draw.circle(gs, (255, 96, 20), (gx, gy), 7)
        pygame.draw.circle(gs, (255, 176, 44), (gx, gy), 5)
        pygame.draw.circle(gs, (255, 236, 110), (gx - 1, gy - 1), 2)
    if self.shield_active:
      sr = 50 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 3)
      gs.blit(shield_sprite(sr), (d.centerx - sr, d.centery - sr))

    self.draw_weather(gs)
    if st in ("PLAYING", "PAUSED"):
      self.draw_hud()
    elif st == "GAMEOVER":
      dd = getattr(self, 'death', None)
      if dd is None or dd.done:
        self.draw_gameover()
    if st == "PAUSED":
      self.draw_pause()

  def draw_hud(self):
    gs = game_surface
    sel = self.selected
    gx, gy, gw, gh = CHARGE_X[0], 100, 44, 310
    panel(gs, pygame.Rect(gx, gy, gw, gh), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    inner = pygame.Rect(gx + 10, gy + 15, gw - 20, gh - 30)
    pygame.draw.rect(gs, (40, 10, 10), inner, border_radius=4)
    fh = int(min(self.dp, 100) / 100.0 * inner.h)
    if fh > 0:
      pygame.draw.rect(gs, ICE_BLUE, (inner.x, inner.bottom - fh, inner.w, fh), border_radius=4)
      pygame.draw.rect(gs, (230, 255, 255), (inner.x + 2, inner.bottom - fh, 4, fh), border_radius=2)
    v = SPRITE_CACHE.get("shield_lbl")
    if v is None:
      v = SPRITE_CACHE["shield_lbl"] = pygame.transform.rotate(text(small_font, "SHIELD CHARGE", MOON_LIGHT), 90)
    gs.blit(v, (gx + gw // 2 - v.get_width() // 2, gy + gh // 2 - v.get_height() // 2))

    draw_button(gs, PAUSE_BTN, "PAUSE", PARCHMENT, PAUSE_BTN.collidepoint(self.mouse), font=small_font)
    PERK.draw(gs, self, (small_font, hud_font), panel, (PANEL_DARK, GOLD_BORDER, PARCHMENT), ULT_BTN)   # level 20: the Ultimate

    if self.shield_active:
      panel(gs, SHIELD_BTN, (20, 40, 80), 235, ICE_BLUE, 3, 12)
      s_txt = text(small_font, "ACTIVE: %ds" % (self.shield_timer // 60 + 1), MOON_LIGHT)
    elif self.shields > 0:
      panel(gs, SHIELD_BTN, (10, 25, 40), 235, MAGIC_PURPLE, 3, 12)
      add_glow(gs, SHIELD_BTN.centerx, SHIELD_BTN.centery, 60, (24, 8, 40))
      s_txt = text(small_font, "SHIELD: %d/%d" % (self.shields, self.max_shields), ICE_BLUE)
    else:
      panel(gs, SHIELD_BTN, (40, 40, 40), 235, STONE_DARK, 3, 12)
      s_txt = text(small_font, "SHIELD: 0/%d" % self.max_shields, (100, 100, 100))
    gs.blit(s_txt, s_txt.get_rect(center=SHIELD_BTN.center))

    if self.dash_state == 'out':
      panel(gs, DASH_BTN, (60, 24, 10), 235, (255, 200, 60), 3, 12)
      add_glow(gs, DASH_BTN.centerx, DASH_BTN.centery, 60, (40, 18, 4))
      d_txt = text(small_font, "DASHING!", (255, 240, 180))
    elif self.dash_cd > 0:
      panel(gs, DASH_BTN, (40, 40, 40), 235, STONE_DARK, 3, 12)
      d_txt = text(small_font, "DASH %ds" % (self.dash_cd // 60 + 1), (120, 120, 120))
    else:
      panel(gs, DASH_BTN, (10, 25, 40), 235, (255, 150, 40), 3, 12)
      add_glow(gs, DASH_BTN.centerx, DASH_BTN.centery, 60, (40, 18, 4))
      d_txt = text(small_font, "DASH: READY", (255, 210, 120))
    gs.blit(d_txt, d_txt.get_rect(center=DASH_BTN.center))
    if self.dash_cd > 0:
      frac = 1.0 - self.dash_cd / float(DASH_COOLDOWN)
      pygame.draw.rect(gs, (255, 150, 40), (DASH_BTN.x + 8, DASH_BTN.bottom - 9, int((DASH_BTN.w - 16) * frac), 4), border_radius=2)

    panel(gs, pygame.Rect(15, 15, 300, 50), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    blit_text(gs, hud_font, "SCORE: %d" % self.score, MOON_LIGHT, (35, 18))
    panel(gs, pygame.Rect(330, 15, 100, 50), PANEL_DARK, 215, GOLD_BORDER, 3, 8)
    draw_coin(gs, 355, 40)
    blit_text(gs, button_font, str(int(self.run_coins)), MOON_LIGHT, (375, 25))
    hot = min(1.0, (self.threat - 1) / 8)
    panel(gs, pygame.Rect(WIDTH - 180, 15, 165, 50), (70 + int(60 * hot), 20, 20), 225, (200, 50, 50), 3, 8)
    blit_text(gs, small_font, "THREAT: %d" % self.threat, PARCHMENT, (WIDTH - 180 + 82, 40), "center")

    nh = max(3 if self.data.get('difficulty', 'easy') == 'easy' else 0, self.hearts)
    if nh:
      hp = pygame.Rect(WIDTH - 15 - (21 + nh * 48), 72, 21 + nh * 48, 50)
      panel(gs, hp, PANEL_DARK, 215, GOLD_BORDER, 2, 8)
      for i in range(nh):                                  # dragon-heart life gauge (boss hearts can push it past 3)
        h_ = life_heart(i < self.hearts, int(self.anim * 3) + i * 3, 44)
        gs.blit(h_, (hp.x + 34 + i * 48 - 22, hp.centery - 22))

    q = self.bounty if getattr(self, 'mode', 'adventure') in ('adventure', 'endless') else None   # (no quests on the course or in the tutorial)
    if q:
      br = pygame.Rect(434, 15, 182, 50)
      panel(gs, br, PARCHMENT, 245, WOOD_DARK, 3, 5)
      if q.get('done'):
        blit_text(gs, small_font, "+%d GOLD!" % quest_gold(q), (200, 130, 10), br.center, "center", shadow=False)
      else:
        blit_text(gs, tiny_font, q['desc'], WOOD_DARK, (br.centerx, br.top + 16), "center", shadow=False)
        blit_text(gs, small_font, "%d/%d" % (q['progress'], q['target']), CLOTH_RED, (br.centerx, br.top + 35), "center", shadow=False)

    b = self.boss
    if b and b['state'] != 'dying':
      self.draw_boss_bar(b)

    if self.breath:
      panel(gs, pygame.Rect(15, 75, 300, 18), IRON_GRAY, 230, GOLD_BORDER, 2, 5)
      pygame.draw.rect(gs, BREATH_BAR.get(sel, (255, 80, 0)), (17, 77, max(0, int(self.breath_timer / self.breath_time * 296)), 14), border_radius=4)

  def draw_phoenix(self, gs, b):
    st, atk, at = b['state'], b.get('atk'), b.get('at', 0)
    if st in ('ash', 'dying'):                  # explodes into embers, then (the first time) is reborn from the smoke
      t = b['dt']
      if t < 64:
        anim, fi = 'death', t // 4
      elif st == 'ash' and t >= 130:
        anim, fi = 'death', 30 + min(10, (t - 130) // 9)
      else:
        return
    elif atk == 'cast':                         # flares white-hot and hurls fireballs
      anim, fi = 'cast', min(16, int(at / 3.5))
    elif atk == 'slash':                        # wraps itself in fire, then spreads its wings
      anim, fi = 'wrap', min(40, int(at * 0.68))
    elif atk == 'burst':                        # engulfed, it bursts into a ring of fire feathers
      anim, fi = 'burst', min(40, int(at * 0.7))
    elif atk == 'warn':                         # winds up for the dive
      anim, fi = 'charge', min(2, at // 14)
    elif atk == 'dive':                         # streaks forward wrapped in flame
      anim, fi = 'charge', 3 + (at // 2) % 9
    else:
      anim, fi = 'fly', int(b['timer'] * 8)
    spr, ax, ay = phx_frame(anim, fi, 3)
    cx, cy = int(b['x']) + 55, int(b['y']) + 55
    al = b.get('alpha', 255)
    add_glow(gs, cx, cy, 110 if anim != 'rebirth' else 150, (90, 34, 4))
    if atk == 'warn' and (at // 5) % 2 == 0:
      add_glow(gs, cx, cy, 90, (150, 40, 10))
      blit_text(gs, hud_font, "!", (255, 90, 60), (cx, cy - 90), "center")
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    gs.blit(spr, (cx - ax, cy - ay))
    if b.get('flash', 0) > 0 and b['flash'] % 2:
      add_glow(gs, cx, cy, 70, (120, 110, 90))
    for w in b.get('fwaves', []):
      gs.blit(fire_crescent(int(w['fr']) % 4), (int(w['x']) - 28, int(w['y']) - 60))
      add_glow(gs, int(w['x']), int(w['y']), 50, (90, 30, 6))

  def draw_maw(self, gs, mx, my):
    """Cosmic Whale: a big starry vortex in front of its open jaws, with streams of starlight being sucked in"""
    t = pygame.time.get_ticks() / 1000.0
    cx, cy = mx + 58, my                                 # just in front of the jaws, not over the head
    R = MAW['range']
    add_glow(gs, int(cx + 40), int(cy), 90, (30, 18, 70))
    for i in range(10):                                  # suction streaks curving into the mouth from the whole cone
      ph = (t * 1.6 + i * 0.137) % 1.0
      ang = (i / 9.0 - 0.5) * 1.3
      d0 = R * (1 - ph)
      d1 = max(10, d0 - 70)
      pts = []
      for k in range(5):
        dd = d0 + (d1 - d0) * k / 4.0
        a = ang * (dd / R) + math.sin(t * 3 + i) * 0.08 * (dd / R)
        pts.append((int(cx + math.cos(a) * dd), int(cy + math.sin(a) * dd * 0.9)))
      bright = int(120 + 135 * ph)
      pygame.draw.lines(gs, (bright, min(255, bright + 20), 255), False, pts, 2 if ph > 0.5 else 1)
    for arm in range(4):                                 # the swirling vortex itself
      prev = None
      for k in range(13):
        rr = 5 + k * 5.0
        a = t * 7.0 + arm * 1.571 - k * 0.45
        p = (int(cx + math.cos(a) * rr * 1.2), int(cy + math.sin(a) * rr * 0.85))
        if prev:
          c = ((255, 255, 255), (225, 205, 255), (170, 150, 250), (120, 100, 220), (80, 70, 180))[min(4, k // 3)]
          pygame.draw.line(gs, c, prev, p, 3 if k < 4 else 2)
        prev = p
    for k in range(3):                                   # rings closing in on the mouth
      ph = ((t * 1.8 + k * 0.33) % 1.0)
      rr = int(70 * (1 - ph)) + 5
      col = (int(150 + 100 * ph), int(130 + 110 * ph), 255)
      pygame.draw.ellipse(gs, col, (int(cx - rr * 1.2), int(cy - rr * 0.85), int(rr * 2.4), int(rr * 1.7)), 2)
    pygame.draw.circle(gs, (255, 255, 255), (int(cx), int(cy)), 4)
    tg = getattr(self, 'maw_target', None)
    if tg:                                               # a tunnel of starlight dragging at the boss
      bx, by = tg
      add_glow(gs, int(bx), int(by), 70, (50, 30, 110))
      for lane in (-1, 0, 1):                            # three twisting ribbons of starlight from the boss to the maw
        prev = None
        for k in range(17):
          f = k / 16.0
          px = bx + (cx - bx) * f
          py = by + (cy - by) * f + math.sin(t * 8 + f * 9 + lane * 2.1) * 18 * (1 - f) * (1 if lane else 0.5)
          if prev:
            c = (int(130 + 120 * f), int(110 + 130 * f), 255)
            pygame.draw.line(gs, c, prev, (int(px), int(py)), 2)
          prev = (int(px), int(py))
      for i in range(22):                                # bits of the boss being pulled along them
        ph = (t * 1.9 + i / 22.0) % 1.0
        px = bx + (cx - bx) * ph
        py = by + (cy - by) * ph + math.sin(t * 9 + i * 1.7) * 20 * (1 - ph)
        c = ((255, 140, 140) if i % 3 == 0 else (int(170 + 85 * ph), int(150 + 100 * ph), 255))
        pygame.draw.circle(gs, c, (int(px), int(py)), 2 + int(4 * (1 - ph)))

  def draw_novas(self, gs):
    d = self.dragon
    t = pygame.time.get_ticks() / 1000.0
    for nv in self.novas:
      cx, cy, r = d.x + nv['ox'], d.y + nv['oy'], int(nv['r'])
      fade = max(0.35, 1.0 - nv['r'] / float(NOVA['r']))   # (stays bright enough to see all the way across)
      cx, cy = int(cx), int(cy)
      w0 = max(1, int(6 * fade + 0.5))
      pygame.draw.circle(gs, (255, 150, 240), (cx, cy), r, w0)
      if r > 9:
        pygame.draw.circle(gs, (140, 240, 255), (cx, cy), r - 7, max(1, w0 // 2))
      if r > 16 and fade > 0.4:
        pygame.draw.circle(gs, (255, 255, 230), (cx, cy), r - 14, 1)
      nsp = 16 if r < 300 else 24
      for k in range(nsp):                                # sparkles riding the ring
        a = k * 2 * math.pi / nsp + t * 2.0
        x, y = int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)
        q = 2 + int(3 * fade)
        pygame.draw.line(gs, (255, 255, 255), (x - q, y), (x + q, y), 1)
        pygame.draw.line(gs, (255, 255, 255), (x, y - q), (x, y + q), 1)

  def draw_butterfly(self, gs, bf):
    x, y, sz = int(bf['x']), int(bf['y']), bf['sz']
    flap = abs(math.sin(bf['t'] * 0.55 + bf['ph']))
    w = max(1, int(9 * sz * (0.35 + 0.65 * flap)))
    h = int(7 * sz)
    c = bf['col']
    al = 255 if bf['t'] < bf['life'] - 20 else max(0, int(255 * (bf['life'] - bf['t']) / 20.0))
    if al < 250:
      c = tuple(int(v * al / 255.0) for v in c)
    dk = tuple(max(0, v - 80) for v in c)
    pygame.draw.polygon(gs, c, [(x, y), (x - w, y - h), (x - w, y + 1)])
    pygame.draw.polygon(gs, c, [(x, y), (x + w, y - h), (x + w, y + 1)])
    pygame.draw.polygon(gs, dk, [(x, y + 1), (x - int(w * 0.7), y + int(h * 0.8)), (x - 1, y + 3)])
    pygame.draw.polygon(gs, dk, [(x, y + 1), (x + int(w * 0.7), y + int(h * 0.8)), (x + 1, y + 3)])
    pygame.draw.line(gs, (40, 20, 40), (x, y - 3), (x, y + 4), 2)

  def draw_beholder(self, gs, b):
    st, atk, at = b['state'], b.get('atk'), b.get('at', 0)
    cx, cy = int(b['x']) + 55, int(b['y']) + 65
    if st == 'dying':
      spr, ax, ay = beh_frame('death', b.get('dt', 0) // 4)
    else:
      tint = 'white' if b.get('flash', 0) > 0 else None
      spr, ax, ay = beh_frame(b.get('anim', 'hover'), b.get('fi', 0), tint=tint)
    al = b.get('alpha', 255)
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    add_glow(gs, cx, cy, 120, (22, 40, 26))
    if st != 'dying' and atk == 'laser' and 10 <= at < 28 and at % 6 < 4:   # where the ray is about to go
      sx, sy, _a = beam_line(b)
      ca, sa = math.cos(b.get('ang', math.pi)), math.sin(b.get('ang', math.pi))
      for q in range(0, 1500, 34):
        pygame.draw.line(gs, (110, 255, 130), (int(sx + ca * q), int(sy + sa * q)), (int(sx + ca * (q + 16)), int(sy + sa * (q + 16))), 2)
    gs.blit(spr, (cx - ax, cy - ay))
    if st != 'dying' and b.get('ray'):
      sx, sy, _a = beam_line(b)
      draw_death_ray(gs, sx, sy, b.get('ang', math.pi), BEH_HALF * BEH_SCALE, at)
    if st != 'dying' and atk == 'laser' and at < 32:       # the great eye glows brighter as it charges
      ex, ey = beh_point(b, BEH_EYE)
      add_glow(gs, int(ex), int(ey), 14 + at, (20, 80 + at * 3, 30))

  def draw_hydra(self, gs, b):
    st, atk, at = b['state'], b.get('atk'), b.get('at', 0)
    cx, cy = int(b['x']) + 98, int(b['y']) + 85
    if st == 'dying':
      fi = 0 if b.get('landed', -1) < 0 else (b['dt'] - b['landed']) // 5
      spr, ax, ay = hyd_frame('death', fi)
    else:
      tint = 'red' if atk == 'lunge_warn' and at % 10 < 5 else ('white' if b.get('flash', 0) > 0 and atk != 'lunge_warn' else None)
      spr, ax, ay = hyd_frame(b.get('anim', 'fly'), b.get('fi', 0), tint=tint)
    al = b.get('alpha', 255)
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    add_glow(gs, cx, cy, 170, (40, 24, 50))
    gs.blit(spr, (cx - ax, cy - ay))
    if atk == 'lunge_warn' and at % 10 < 6 and st != 'dying':
      blit_text(gs, hud_font, "!", (255, 90, 60), (cx, cy - 170), "center")

  def draw_jabber(self, gs, b):
    st, atk, at = b['state'], b.get('atk'), b.get('at', 0)
    cx, cy = int(b['x']) + 65, int(b['y']) + 65
    if st == 'dying':
      fi = 0 if b.get('landed', -1) < 0 else min(16, (b['dt'] - b['landed']) // 4)
      spr, ax, ay = jab_frame('death', fi)
    else:
      tint = 'white' if b.get('flash', 0) > 0 and atk != 'charge_warn' else ('red' if atk == 'charge_warn' and at % 10 < 5 else None)
      spr, ax, ay = jab_frame('fly', b.get('fi', 0), tint=tint)
    al = b.get('alpha', 255)
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    add_glow(gs, cx, cy, 120, (24, 40, 18))
    gs.blit(spr, (cx - ax, cy - ay))
    if st == 'dying':
      return
    mx, my = jab_mouth(b)
    k = at - b.get('spit_t', -99)
    if atk in ('spit', 'burble') and 0 <= k < 8:             # the spit bursts out of its jaws
      fx, dx, dy = jab_fx('spit', k // 2)
      gs.blit(fx, (int(mx + dx), int(my + dy)))
    if atk == 'beam':
      if at < 34:                                            # green burble crackling at the jaws, and where it is aiming
        add_glow(gs, int(mx), int(my), 30 + at, (30, 90, 20))
        fx, dx, dy = jab_fx('beam', at // 3)
        gs.blit(fx, (int(mx + dx), int(my + dy)))
        if at > 12 and at % 6 < 4:
          ca, sa = math.cos(b['ang']), math.sin(b['ang'])
          for q in range(2, 40, 3):
            pygame.draw.line(gs, (120, 255, 90), (int(mx + ca * q * 26), int(my + sa * q * 26)), (int(mx + ca * (q * 26 + 12)), int(my + sa * (q * 26 + 12))), 2)
      elif b.get('beam'):
        draw_burble_beam(gs, mx, my, b['ang'], at)
    if atk == 'charge_warn' and at % 10 < 6:
      blit_text(gs, hud_font, "!", (255, 90, 60), (cx, cy - 120), "center")

  def draw_demon(self, gs, b):
    if b['state'] == 'dying':
      fi = 14 if b.get('landed', -1) < 0 else 15 + min(5, (b['dt'] - b['landed']) // 12)
    elif b['atk'] == 'slash':
      fi = 8 + min(5, b['at'] // 6)
    elif b.get('flash', 0) > 0:
      fi = 14
    else:
      fi = int(b['timer'] * 9) % 8
    spr = scaled_frame('demon', fi, 1.5)
    al = b.get('alpha', 255)
    if al < 255:
      spr = spr.copy()
      spr.set_alpha(max(0, al))
    if al > 0:
      add_glow(gs, int(b['x']) + 75, int(b['y']) + 80, 120, (50, 18, 4))
      gs.blit(spr, (int(b['x']) - 30, int(b['y']) - 24))
      if b.get('sh', 0) > 0 and (b['sh'] > 40 or (b['sh'] // 4) % 2 == 0):
        sr = 108 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 4)
        gs.blit(red_shield_sprite(sr), (int(b['x']) + 75 - sr, int(b['y']) + 78 - sr))
    for w in b.get('fwaves', []):
      gs.blit(fire_crescent(int(w['fr']) % 4), (int(w['x']) - 28, int(w['y']) - 60))
      add_glow(gs, int(w['x']), int(w['y']), 50, (90, 30, 6))

  def draw_boss_bar(self, b):
    gs = game_surface
    bw, bh = 400, 22
    x0, y0 = WIDTH // 2 - bw // 2, 120
    pct = max(0.0, min(1.0, b['hp'] / float(b['max_hp'])))
    key = ("bossbar", int(pct * bw))
    spr = BOSSBAR_CACHE.get(key)
    if spr is None:
      if len(BOSSBAR_CACHE) > 400:
        BOSSBAR_CACHE.clear()
      spr = pygame.Surface((bw + 40, bh + 24), pygame.SRCALPHA)
      pygame.draw.rect(spr, (30, 22, 18), (4, 0, bw + 32, bh + 24), border_radius=8)
      pygame.draw.rect(spr, GOLD_BORDER, (4, 0, bw + 32, bh + 24), 3, border_radius=8)
      pygame.draw.rect(spr, (50, 12, 12), (20, 8, bw, bh), border_radius=5)
      fw = int(pct * bw)
      for i in range(bh):
        k = i / float(bh)
        col = (255, 150, 110) if k < 0.15 else (int(230 - 80 * k), int(50 - 30 * k), int(40 - 20 * k))
        if fw > 6:
          pygame.draw.line(spr, col, (23, 8 + i), (20 + fw - 3, 8 + i))
      pygame.draw.rect(spr, (120, 80, 20), (20, 8, bw, bh), 2, border_radius=5)
      for i in range(1, 10):
        pygame.draw.line(spr, (20, 8, 6), (20 + bw * i // 10, 8 + bh - 5), (20 + bw * i // 10, 8 + bh - 1))
      for cx in (8, bw + 32):
        pygame.draw.polygon(spr, (220, 170, 50), [(cx, 20 - 12), (cx + 10, 20), (cx, 20 + 12), (cx - 10, 20)])
        pygame.draw.polygon(spr, (60, 30, 10), [(cx, 20 - 12), (cx + 10, 20), (cx, 20 + 12), (cx - 10, 20)], 1)
      BOSSBAR_CACHE[key] = spr
    gs.blit(spr, (x0 - 20, y0 - 8))
    nm = {"griffin": "GRIFFIN", "demon": "FIRE DEMON", "phoenix": "PHOENIX", "beholder": "BEHOLDER", "jabber": "JABBERWOCK", "hydra": "HYDRA", "sphinx": "SPHINX", "manticore": "MANTICORE", "mothman": "MOTHMAN"}.get(b['type'], "SKY FORTRESS")
    blit_text(gs, small_font, nm, (255, 226, 150), (WIDTH // 2, y0 - 26), "center")
    blit_text(gs, tiny_font, "%d%%" % int(pct * 100 + 0.5), (255, 240, 220), (WIDTH // 2, y0 + bh // 2), "center")

  def draw_gameover(self):
    gs = game_surface
    dim(gs, 120)
    if GOA.ok():
      return self.draw_art_gameover()
    pnl = pygame.Rect(WIDTH // 2 - 340, HEIGHT // 2 - 192, 680, 400)
    panel(gs, pnl, PARCHMENT, 252, WOOD_DARK, 6, 12)
    blit_text(gs, hud_font, "SIEGE CASUALTY", (190, 40, 20), (pnl.centerx, pnl.top + 40), "center", shadow=False)
    mode = getattr(self, 'mode', 'adventure')
    if mode == 'obstacle':
      main = "Pillars passed: %d" % getattr(self, 'pillars_passed', 0)
    else:
      main = ("Endless  -  Score: %d" if mode == 'endless' else "Score: %d") % self.score
    blit_text(gs, button_font, main, WOOD_DARK, (pnl.centerx, pnl.top + 88), "center", shadow=False)
    if self.new_record:
      pulse = 180 + int(75 * math.sin(self.anim * 6))
      blit_text(gs, small_font, "NEW REALM RECORD!", (pulse, int(pulse * 0.6), 20), (pnl.centerx, pnl.top + 118), "center", shadow=False)
    else:
      rk = MODE.RECORD_KEY.get(mode) or 'high_score'
      blit_text(gs, small_font, "Record: %d" % self.data.get(rk, 0), (110, 80, 40), (pnl.centerx, pnl.top + 118), "center", shadow=False)
    blit_text(gs, small_font, "Coins Pillaged: %d" % int(self.run_coins), (180, 120, 10), (pnl.centerx, pnl.top + 144), "center", shadow=False)
    lv, xp = self.dragon_lv()                              # the dragon's level and the XP it just earned
    name = DRAGON_PALETTES.get(self.selected, {}).get('title', 'Dragon')
    sh = getattr(self, 'xp_share', 0)
    extra = ("   (%d from your %sbaby)" % (sh, "matching " if getattr(self, 'xp_match', False) else "")) if sh else ""
    blit_text(gs, tiny_font, "%s  -  Level %d   +%d XP%s" % (name, lv, getattr(self, 'xp_gain', 0), extra), (70, 50, 30), (pnl.centerx, pnl.top + 172), "center", shadow=False)
    bar = pygame.Rect(pnl.centerx - 130, pnl.top + 186, 260, 9)
    pygame.draw.rect(gs, (90, 70, 50), bar, border_radius=4)
    if lv < self.dragon_cap():
      f = min(1.0, xp / float(dragon_need(lv)))
      if f > 0:
        pygame.draw.rect(gs, (230, 170, 40), (bar.x, bar.y, max(4, int(bar.w * f)), bar.h), border_radius=4)
    else:
      pygame.draw.rect(gs, (230, 170, 40), bar, border_radius=4)
    if getattr(self, 'level_up', 0):
      pulse = 180 + int(75 * math.sin(self.anim * 6))
      msg = "LEVEL UP!  Now level %d" % self.level_up
      if self.level_up == GROUND_LEVEL and self.selected in GROUND_DRAGONS:
        msg = "LEVEL %d!  Ground attack unlocked!" % self.level_up
      elif self.level_up == PERK.LV_SPECIAL:
        msg = "LEVEL 10!  Stronger special unlocked!"
      elif self.level_up == PERK.LV_PERK:
        msg = "LEVEL 15!  " + PERK.PERK_TEXT.get(PERK.PERK.get(self.selected), "New skill unlocked!")
      elif self.level_up == PERK.LV_ULT:
        msg = "LEVEL 20!  Ultimate unlocked: " + PERK.ULT_NAME.get(self.selected, "")
      blit_text(gs, tiny_font, msg, (pulse, int(pulse * 0.55), 20), (pnl.centerx, pnl.top + 212), "center", shadow=False)
    if self.over_t > 25:
      draw_button(gs, RETRY_BTN, "RETRY", BANNER_GOLD, RETRY_BTN.collidepoint(self.mouse), font=small_font)
      draw_button(gs, REPORT_BTN, "AFTERMATH REPORT", PARCHMENT, REPORT_BTN.collidepoint(self.mouse), font=small_font)
      draw_button(gs, OVER_MENU_BTN, "MAIN MENU", PARCHMENT, OVER_MENU_BTN.collidepoint(self.mouse), font=small_font)

  def go_lines(self):
    """the words on the game-over parchment: (main line, record line, record is new, coins line, xp line, level-up line)"""
    mode = getattr(self, 'mode', 'adventure')
    if mode == 'obstacle':
      main = "Pillars passed: %d" % getattr(self, 'pillars_passed', 0)
    else:
      main = ("Endless  -  Score: %d" if mode == 'endless' else "Score: %d") % self.score
    if self.new_record:
      rec = "NEW REALM RECORD!"
    else:
      rk = MODE.RECORD_KEY.get(mode) or 'high_score'
      rec = "Record: %d" % self.data.get(rk, 0)
    coins = "Coins Pillaged: %d" % int(self.run_coins)
    lv, xp = self.dragon_lv()
    name = DRAGON_PALETTES.get(self.selected, {}).get('title', 'Dragon')
    sh = getattr(self, 'xp_share', 0)
    extra = ("   (%d from your %sbaby)" % (sh, "matching " if getattr(self, 'xp_match', False) else "")) if sh else ""
    xpl = "%s  -  Level %d   +%d XP%s" % (name, lv, getattr(self, 'xp_gain', 0), extra)
    up = None
    if getattr(self, 'level_up', 0):
      up = "LEVEL UP!  Now level %d" % self.level_up
      if self.level_up == GROUND_LEVEL and self.selected in GROUND_DRAGONS:
        up = "LEVEL %d!  Ground attack unlocked!" % self.level_up
      elif self.level_up == PERK.LV_SPECIAL:
        up = "LEVEL 10!  Stronger special unlocked!"
      elif self.level_up == PERK.LV_PERK:
        up = "LEVEL 15!  " + PERK.PERK_TEXT.get(PERK.PERK.get(self.selected), "New skill unlocked!")
      elif self.level_up == PERK.LV_ULT:
        up = "LEVEL 20!  Ultimate unlocked: " + PERK.ULT_NAME.get(self.selected, "")
    return main, rec, self.new_record, coins, xpl, up, lv, xp

  def draw_art_gameover(self):
    """your Siege Casualty panel: the words are drawn on the parchment, the buttons and XP bar are your art"""
    gs = game_surface
    px, pt = WIDTH // 2 - GOA.PANEL_W // 2, (HEIGHT - GOA.PANEL_H) // 2
    gs.blit(GOA.img('go_panel'), (px, pt))
    cx = WIDTH // 2
    main, rec, new, coins, xpl, up, lv, xp = self.go_lines()
    ink = (54, 30, 14)
    blit_text(gs, button_font, main, ink, (cx, pt + 178), "center", shadow=False)
    if new:
      pulse = 170 + int(60 * math.sin(self.anim * 6))
      blit_text(gs, small_font, rec, (pulse, int(pulse * 0.55), 10), (cx, pt + 208), "center", shadow=False)
    else:
      blit_text(gs, small_font, rec, (120, 82, 30), (cx, pt + 208), "center", shadow=False)
    blit_text(gs, small_font, coins, (176, 116, 16), (cx, pt + 235), "center", shadow=False)
    img = tiny_font.render(xpl, True, ink)
    if img.get_width() > GOA.PANEL_W - 300:
      img = pygame.transform.smoothscale(img, (GOA.PANEL_W - 300, img.get_height()))
    gs.blit(img, img.get_rect(center=(cx, pt + 259)))
    bx, by = cx - GOA.BAR_W // 2, pt + 268                 # the XP bar: your empty bar, then the fill up to the XP earned
    tx, ty, tw, th = GOA.TRACK
    f = 1.0 if lv >= self.dragon_cap() else max(0.0, min(1.0, xp / float(dragon_need(lv))))
    gs.blit(GOA.img('go_bar'), (bx, by))
    if f > 0:                                             # (the fill shows through the dark track)
      gs.blit(GOA.img('go_fill'), (bx + tx, by + ty), (0, 0, max(2, int(tw * f)), th))
    if up:
      pulse = 180 + int(75 * math.sin(self.anim * 6))
      blit_text(gs, tiny_font, up, (pulse, int(pulse * 0.5), 20), (cx, pt + 318), "center", shadow=False)
    if self.over_t > 25:
      for r, lab in ((RETRY_BTN, "RETRY"), (REPORT_BTN, "AFTERMATH REPORT"), (OVER_MENU_BTN, "MAIN MENU")):
        hov = r.collidepoint(self.mouse)
        gs.blit(GOA.img('go_btn_down' if hov else 'go_btn'), r.topleft)
        for sz in (22, 20, 18, 16):                       # (shrink to fit between the gems)
          t = UIX.small_fire(lab, sz)
          if t.get_width() <= r.w - 76:
            break
        gs.blit(t, t.get_rect(center=(r.centerx, r.centery - 1)))

  def draw_report(self):
    """Aftermath report: the war-camp tent, the run written up on two scrolls."""
    gs = game_surface
    if UIX.art_ok('report'):
      return self.draw_art_report()
    gs.blit(UIX.tent_backdrop(), (0, 0))
    UIX.lantern(gs, WIDTH // 2 - 430, 150, self.anim)
    UIX.lantern(gs, WIDTH // 2 + 430, 150, self.anim + 1.3)
    rs = getattr(self, 'run_stats', None) or {'kills': {}, 'powerups': 0, 'eggs': [], 'quests': [], 'dist': 0.0, 'bosses': [], 'ticks': 0, 'hearts_lost': 0}
    UIX.draw_title(gs, "AFTERMATH REPORT", 42, self.anim, False)
    ink, red, faint = (52, 30, 14), (150, 30, 20), (120, 96, 60)
    fh, fr, ft = UIX._ink_font(20), UIX._ink_font(16), UIX._ink_font(13)
    names = {e[0]: e[1] for e in ENEMY_INFO}
    names.update({'tower': 'Tower'})
    lp = pygame.Rect(WIDTH // 2 - 375, 82, 360, 410)
    rp = pygame.Rect(WIDTH // 2 + 15, 82, 360, 410)
    gs.blit(UIX.scroll_sheet(lp.w, lp.h - 20, 31), (lp.left - 12, lp.top - 5))
    gs.blit(UIX.scroll_sheet(rp.w, rp.h - 20, 32), (rp.left - 12, rp.top - 5))
    kills = sorted(rs['kills'].items(), key=lambda kv: (-kv[1], names.get(kv[0], kv[0])))
    total = sum(v for _k, v in kills)
    im = fh.render("Foes Slain: %d" % total, True, red)
    gs.blit(im, im.get_rect(center=(lp.centerx, lp.top + 30)))
    pygame.draw.line(gs, faint, (lp.left + 24, lp.top + 46), (lp.right - 24, lp.top + 46), 1)
    if not kills:
      im = fr.render("None this time!", True, ink)
      gs.blit(im, im.get_rect(center=(lp.centerx, lp.top + 90)))
    lr = REPORT_LIST                                      # scrollable list: drag or use the wheel
    full = len(kills) * REPORT_ROW
    self.report_scroll = max(0.0, min(max(0, full - lr.h), getattr(self, 'report_scroll', 0.0)))
    gs.set_clip(lr)
    for i, (k, v) in enumerate(kills):
      y = lr.top + 16 + i * REPORT_ROW - int(self.report_scroll)
      if y < lr.top - REPORT_ROW or y > lr.bottom + REPORT_ROW:
        continue
      try:
        ic = self.sketch_art(k, 0.0, 34, 24) if k in names and k != 'tower' else None
      except Exception:
        ic = None
      if ic is not None:
        gs.blit(ic, (lp.left + 34 - ic.get_width() // 2, y - ic.get_height() // 2))
      nm = names.get(k, k.title())
      im = fr.render(nm, True, ink)
      gs.blit(im, im.get_rect(midleft=(lp.left + 58, y)))
      tx = lp.left + 66 + max(118, im.get_width())
      if v <= 15:
        UIX.tally(gs, tx, y, v)
      else:
        w_ = UIX.tally(gs, tx, y, 10)
        im = ft.render("+%d" % (v - 10), True, red)
        gs.blit(im, im.get_rect(midleft=(tx + w_ + 4, y)))
    gs.set_clip(None)
    if full > lr.h:                                        # scroll bar
      tr = pygame.Rect(lp.right - 14, lr.top, 6, lr.h)
      pygame.draw.rect(gs, (200, 176, 128), tr, border_radius=3)
      th = max(30, int(lr.h * lr.h / float(full)))
      ty = lr.top + int((lr.h - th) * self.report_scroll / float(full - lr.h))
      pygame.draw.rect(gs, (120, 80, 40), (tr.x, ty, tr.w, th), border_radius=3)
    secs = rs['ticks'] // FPS
    bosses = ", ".join(names.get(b, b.title()) for b in rs['bosses']) or "None"
    eggs = ("%d  (%s)" % (len(rs['eggs']), ", ".join(e.capitalize() for e in rs['eggs']))) if rs['eggs'] else "0"
    lines = [("Dragon", DRAGON_PALETTES[self.selected]['title']),
             ("Score", "%d" % self.score),
             ("Coins Collected", "%d" % int(self.run_coins)),
             ("Distance Flown", "{:,} m".format(int(rs['dist'] / PX_PER_M))),
             ("Time Survived", "%d:%02d" % (secs // 60, secs % 60)),
             ("Power-ups", "%d" % rs['powerups']),
             ("Eggs Found", eggs),
             ("Bosses Defeated", bosses),
             ("Hearts Lost", "%d" % rs['hearts_lost']),
             ("Quests Completed", "%d" % len(rs['quests']))]
    im = fh.render("Campaign Ledger", True, red)
    gs.blit(im, im.get_rect(center=(rp.centerx, rp.top + 30)))
    pygame.draw.line(gs, faint, (rp.left + 24, rp.top + 46), (rp.right - 24, rp.top + 46), 1)
    for i, (lab, val) in enumerate(lines):
      y = rp.top + 64 + i * 25
      im = fr.render(lab, True, ink)
      gs.blit(im, im.get_rect(midleft=(rp.left + 26, y)))
      f = fr if fr.size(val)[0] < 150 else ft
      while f.size(val)[0] > 170 and len(val) > 4:
        val = val[:-2].rstrip() + "."
      im = f.render(val, True, red)
      gs.blit(im, im.get_rect(midright=(rp.right - 26, y)))
      pygame.draw.line(gs, (214, 194, 150), (rp.left + 26, y + 11), (rp.right - 26, y + 11), 1)
    y = rp.top + 64 + len(lines) * 25
    for desc, gold in rs['quests'][:3]:
      t_ = "+ %s (+%d gold)" % (desc, gold)
      while ft.size(t_)[0] > rp.w - 56 and len(t_) > 6:
        t_ = t_[:-2]
      im = ft.render(t_, True, (40, 100, 30))
      gs.blit(im, (rp.left + 28, y - 6))
      y += 17
    draw_button(gs, BACK_BTN, "BACK", PARCHMENT, BACK_BTN.collidepoint(self.mouse))

  def draw_art_report(self):
    """the Aftermath Report written on your two parchments in the war room"""
    gs = game_surface
    t = self.anim
    gs.blit(UIX.report_backdrop(), (0, 0))
    for i, (x, y, rad) in enumerate(UIX.RA.LIGHTS):
      f = 0.75 + 0.2 * math.sin(t * (8 + i) + i * 1.9)
      px, py = UIX.report_pt(x, y)
      add_glow(gs, px, py, int(rad * REPORT_K), (int(54 * f), int(32 * f), 6))
    rs = getattr(self, 'run_stats', None) or {'kills': {}, 'powerups': 0, 'eggs': [], 'quests': [], 'dist': 0.0, 'bosses': [], 'ticks': 0, 'hearts_lost': 0}
    tr = report_rect(UIX.RA.TITLE)                       # title on your blank plaque
    for sz in (40, 36, 32, 28):
      tt = ENV.fire_text("AFTERMATH REPORT", sz)
      if tt.get_width() <= tr.w - 40:
        break
    gs.blit(tt, tt.get_rect(center=tr.center))
    ink, red, faint = (52, 30, 14), (150, 30, 20), (150, 120, 80)
    fh, fr, ft = UIX._ink_font(19), UIX._ink_font(16), UIX._ink_font(13)
    names = {e[0]: e[1] for e in ENEMY_INFO}
    names.update({'tower': 'Tower'})
    kills = sorted(rs['kills'].items(), key=lambda kv: (-kv[1], names.get(kv[0], kv[0])))
    total = sum(v for _k, v in kills)
    hx, hy = UIX.report_pt(*UIX.RA.PAGE_TOP_L)
    im = fh.render("Foes Slain: %d" % total, True, red)
    gs.blit(im, im.get_rect(center=(hx, hy + 2)))
    lr = REPORT_LIST
    if not kills:
      im = fr.render("None this time!", True, ink)
      gs.blit(im, im.get_rect(center=(lr.centerx, lr.top + 30)))
    full = len(kills) * REPORT_ROW
    self.report_scroll = max(0.0, min(max(0, full - lr.h), getattr(self, 'report_scroll', 0.0)))
    gs.set_clip(lr)
    for i, (k, v) in enumerate(kills):
      y = lr.top + 14 + i * REPORT_ROW - int(self.report_scroll)
      if y < lr.top - REPORT_ROW or y > lr.bottom + REPORT_ROW:
        continue
      try:
        ic = self.fit_art(k, 0.0, 34, 24) if k in names and k != 'tower' else None
      except Exception:
        ic = None
      if ic is not None:
        gs.blit(ic, (lr.left + 22 - ic.get_width() // 2, y - ic.get_height() // 2))
      im = fr.render(names.get(k, k.title()), True, ink)
      gs.blit(im, im.get_rect(midleft=(lr.left + 46, y)))
      tx = lr.left + 52 + max(120, im.get_width())
      if v <= 15:
        UIX.tally(gs, tx, y, v)
      else:
        w_ = UIX.tally(gs, tx, y, 10)
        im = ft.render("+%d" % (v - 10), True, red)
        gs.blit(im, im.get_rect(midleft=(tx + w_ + 4, y)))
    gs.set_clip(None)
    if full > lr.h:                                        # scroll bar
      sb = pygame.Rect(lr.right - 4, lr.top, 5, lr.h)
      pygame.draw.rect(gs, (200, 176, 128), sb, border_radius=3)
      th = max(30, int(lr.h * lr.h / float(full)))
      ty = lr.top + int((lr.h - th) * self.report_scroll / float(full - lr.h))
      pygame.draw.rect(gs, (120, 80, 40), (sb.x, ty, sb.w, th), border_radius=3)
    secs = rs['ticks'] // FPS
    bosses = ", ".join(names.get(b, b.title()) for b in rs['bosses']) or "None"
    eggs = ("%d  (%s)" % (len(rs['eggs']), ", ".join(e.capitalize() for e in rs['eggs']))) if rs['eggs'] else "0"
    lines = [("Dragon", DRAGON_PALETTES[self.selected]['title']),
             ("Score", "%d" % self.score),
             ("Coins Collected", "%d" % int(self.run_coins)),
             ("Distance Flown", "{:,} m".format(int(rs['dist'] / PX_PER_M))),
             ("Time Survived", "%d:%02d" % (secs // 60, secs % 60)),
             ("Power-ups", "%d" % rs['powerups']),
             ("Eggs Found", eggs),
             ("Bosses Defeated", bosses),
             ("Hearts Lost", "%d" % rs['hearts_lost']),
             ("Quests Completed", "%d" % len(rs['quests']))]
    hx, hy = UIX.report_pt(*UIX.RA.PAGE_TOP_R)
    im = fh.render("Campaign Ledger", True, red)
    gs.blit(im, im.get_rect(center=(hx, hy + 2)))
    rp = report_rect(UIX.RA.PAGE_R)
    step = min(24, (rp.h - 6) // (len(lines) + min(2, len(rs['quests']))))
    for i, (lab, val) in enumerate(lines):
      y = rp.top + 10 + i * step
      im = fr.render(lab, True, ink)
      gs.blit(im, im.get_rect(midleft=(rp.left + 8, y)))
      f = fr if fr.size(val)[0] < 140 else ft
      while f.size(val)[0] > 160 and len(val) > 4:
        val = val[:-2].rstrip() + "."
      im = f.render(val, True, red)
      gs.blit(im, im.get_rect(midright=(rp.right - 8, y)))
      pygame.draw.line(gs, (214, 194, 150), (rp.left + 8, y + step // 2), (rp.right - 8, y + step // 2), 1)
    y = rp.top + 10 + len(lines) * step
    for desc, gold in rs['quests'][:2]:
      t_ = "+ %s (+%d gold)" % (desc, gold)
      while ft.size(t_)[0] > rp.w - 16 and len(t_) > 6:
        t_ = t_[:-2]
      im = ft.render(t_, True, (40, 100, 30))
      gs.blit(im, (rp.left + 8, y - 6))
      y += 16
    br = REPORT_BACK                                     # BACK on your red plate
    hov = br.collidepoint(self.mouse)
    if hov:
      add_glow(gs, br.centerx, br.centery, br.w // 2, (90, 40, 10))
    bt = UIX.small_fire("BACK", 24)
    gs.blit(bt, bt.get_rect(center=(br.centerx, br.centery + (1 if hov else 0))))

  def draw_pause(self):
    gs = game_surface
    dim(gs, 150)
    if not self.confirm_menu:
      self.draw_sound_btn()
      blit_text(gs, title_font, "PAUSED", PARCHMENT, (WIDTH // 2, HEIGHT // 2 - 85), "center")
      draw_button(gs, RESUME_BTN, "RESUME", PARCHMENT, RESUME_BTN.collidepoint(self.mouse))
      draw_button(gs, OPT_BTN, "OPTIONS", PARCHMENT, OPT_BTN.collidepoint(self.mouse))
      draw_button(gs, MENU_BTN, "MAIN MENU", PARCHMENT, MENU_BTN.collidepoint(self.mouse))
    else:
      cp = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 80, 400, 160)
      panel(gs, cp, PARCHMENT, 255, WOOD_DARK, 6, 12)
      blit_text(gs, hud_font, "Abandon Siege?", WOOD_DARK, (cp.centerx, cp.top + 40), "center", shadow=False)
      draw_button(gs, YES_BTN, "YES", PARCHMENT, YES_BTN.collidepoint(self.mouse))
      draw_button(gs, NO_BTN, "NO", PARCHMENT, NO_BTN.collidepoint(self.mouse))
