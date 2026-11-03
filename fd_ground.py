"""Ground attacks: once a dragon reaches GROUND_LEVEL, its breath also strikes the ground ahead.
(Magma / Acid / Alien pools, Wind tornados and Forest vines live in fd_logic; the rest are here.)

  Ice ......... frost patches that freeze ground troops
  Lightning ... bolts from the sky
  Bone Reaper . skeleton hands that drag troops under
  Cosmic ...... falling meteors
  Unicorn ..... a rainbow shockwave along the ground
  Wraith ...... ghost pools that drain the troops standing in them
  Chinese ..... water geysers that blast troops into the sky
  Clockwork ... dropped bombs
  Cockatrice .. eggs that crack and turn troops to stone
  Whale ....... gravity wells that pull troops in
  Fey ......... mushroom rings that turn troops into butterflies
  Giant Eagle . a stomp shockwave
"""
import math
import random
import pygame
from fd_core import WIDTH, HEIGHT, GROUND_Y, BOSS_X, GROUND_LISTS, MAX_HEARTS, add_glow, blit_text, hud_font
from fd_sound import AUDIO

KIND = {'BLUE': 'frost', 'YELLOW': 'strike', 'SKELETAL': 'hands', 'COSMIC': 'meteor', 'UNICORN': 'wave', 'WRAITH': 'ghost',
        'CHINESE': 'geyser', 'CLOCKWORK': 'bomb', 'COCKATRICE': 'stone', 'WHALE': 'well', 'FEY': 'ring', 'EAGLE': 'stomp', 'RAVEN': 'stomp', 'PERYTON': 'stomp'}
NAME = {'frost': "Frost patches", 'strike': "Lightning strikes", 'hands': "Grasping skeleton hands", 'meteor': "Meteor shower",
        'wave': "Rainbow shockwave", 'ghost': "Ghost pools", 'geyser': "Water geysers", 'bomb': "Bombs away", 'stone': "Stone eggs",
        'well': "Gravity wells", 'ring': "Mushroom rings", 'stomp': "Stomp shockwave",
        'lava': "Burning lava pools", 'acid': "Acid pools", 'tornado': "Tornados", 'vines': "Thorn vines"}
OTHER = {'RED': 'lava', 'GREEN': 'acid', 'ALIEN': 'acid', 'SILVER': 'tornado', 'FOREST': 'vines'}
EVERY = {'frost': 40, 'strike': 32, 'hands': 38, 'meteor': 34, 'wave': 60, 'ghost': 50, 'geyser': 36, 'bomb': 28,
         'stone': 36, 'well': 70, 'ring': 60, 'stomp': 70}
LIFE = {'frost': 220, 'strike': 16, 'hands': 56, 'meteor': 120, 'wave': 46, 'ghost': 190, 'geyser': 52, 'bomb': 120,
        'stone': 120, 'well': 130, 'ring': 100, 'stomp': 40}
MAX_LIVE = 5
GROUND_NAMES = ('archers', 'mages', 'catapults', 'trebuchets', 'ballistas', 'golems', 'cyclopes')
PTS = {'catapults': 25, 'trebuchets': 25, 'ballistas': 30, 'golems': 40, 'cyclopes': 40, 'enemies': 20}


def ground_name(key):
  k = KIND.get(key) or OTHER.get(key)
  return NAME.get(k) if k else None


def targets(game, low=90):
  """ground troops (and low flyers) that a ground attack can reach"""
  for name in GROUND_NAMES + ('enemies',):
    for o in getattr(game, name, ()):
      if o.get('shattered') or o.get('state', 'normal') != 'normal' or o.get('swallowed'):
        continue
      if name == 'enemies' and o['rect'].bottom < GROUND_Y - low:
        continue
      yield name, o


def kill(game, name, o, col, sound=True):
  r = o['rect']
  o['shattered'] = True
  game.burst(r.centerx, r.centery, 18, 6, 4, 10, col)
  game.score += int(PTS.get(name, 20) * game.score_mult)
  game.dp += 10
  game.bounty_add('shatter')
  if sound:
    try:
      AUDIO.play('shatter', 0.5)
    except Exception:
      pass


def in_zone(o, x, half, GROUND_Y, tall=150):
  r = o['rect']
  return abs(r.centerx - x) < half + r.w // 2 and r.bottom > GROUND_Y - tall


def aim_x(game, lo=140, hi=520):
  """where to put the next one: under the nearest troop ahead, or somewhere ahead"""
  d = game.dragon
  best = None
  for name, o in targets(game):
    dx = o['rect'].centerx - d.centerx
    if lo - 60 < dx < hi + 120 and (best is None or dx < best):
      best = dx
  return d.centerx + (best if best is not None else random.randint(lo, hi))


def update(game):
  d = game.dragon
  key = game.selected
  k = KIND.get(key)
  fx = game.__dict__.setdefault('gfx', [])
  if k and game.breath and game.ground_ok() and game.state == "PLAYING":
    game.gfx_t = getattr(game, 'gfx_t', 0) + 1
    if game.gfx_t >= EVERY[k] and len(fx) < MAX_LIVE:
      game.gfx_t = 0
      spawn(game, k, d, GROUND_Y)
  elif not game.breath:
    game.gfx_t = 10 ** 6                               # the next breath starts with one straight away
  sc = game.scroll_px
  keep = []
  for e in fx:
    e['t'] += 1
    e['x'] -= sc
    step(game, e, GROUND_Y)
    if e['t'] < e['life'] and e['x'] > -150 and not e.get('done'):
      keep.append(e)
  game.gfx = keep


def spawn(game, k, d, GROUND_Y):
  e = {'k': k, 't': 0, 'life': LIFE[k], 'hit': [], 'ph': random.uniform(0, 6.3)}
  if k in ('bomb', 'stone'):                            # dropped from the dragon, they arc down to the ground
    e.update(x=float(d.centerx + 20), y=float(d.bottom), vx=random.uniform(4, 7), vy=-1.0)
  elif k == 'meteor':                                   # streak down from the top of the sky
    tx = aim_x(game, 200, 560)
    e.update(x=float(tx + 160), y=-40.0, vx=-4.0, vy=11.0)
  elif k in ('wave', 'stomp'):
    e.update(x=float(d.centerx + (40 if k == 'wave' else 0)), r=0.0)
  else:
    e.update(x=float(aim_x(game)))
  game.gfx.append(e)
  try:
    AUDIO.play({'strike': 'thunder', 'geyser': 'whoosh', 'wave': 'whoosh', 'stomp': 'roar'}.get(k, 'whoosh'), 0.35)
  except Exception:
    pass


def step(game, e, GROUND_Y):
  k, t = e['k'], e['t']
  if k == 'frost':                                      # icy ground: anyone walking onto it freezes solid
    for name, o in targets(game, 60):
      if in_zone(o, e['x'], 46, GROUND_Y, 120):
        o['state'] = 'frozen'
        o['vy'] = 0.0
        game.score += int(PTS.get(name, 20) * game.score_mult * 0.5)
        game.dp += 5
        game.burst(o['rect'].centerx, o['rect'].centery, 8, 3, 3, 6, (210, 248, 255))
  elif k == 'strike':
    if t == 4:
      for name, o in list(targets(game)):
        if in_zone(o, e['x'], 42, GROUND_Y):
          kill(game, name, o, (255, 245, 150))
      game.burst(e['x'], GROUND_Y - 6, 16, 6, 3, 8, (255, 240, 140))
      game.shake_for(3, 5)
  elif k == 'hands':
    if t == 16:
      for name, o in list(targets(game)):
        if in_zone(o, e['x'], 40, GROUND_Y, 110):
          kill(game, name, o, (220, 224, 200))
  elif k in ('meteor', 'bomb', 'stone'):
    if not e.get('landed'):
      e['x'] += e['vx']
      e['y'] += e['vy']
      if k != 'meteor':
        e['vy'] += 0.55
      if e['y'] >= GROUND_Y - 6:
        e['y'] = GROUND_Y - 6
        e['landed'] = t
        rad = {'meteor': 70, 'bomb': 66, 'stone': 58}[k]
        col = {'meteor': (255, 150, 60), 'bomb': (255, 190, 80), 'stone': (170, 166, 156)}[k]
        for name, o in list(targets(game)):
          if in_zone(o, e['x'], rad, GROUND_Y, 140):
            kill(game, name, o, col)
        game.burst(e['x'], GROUND_Y - 10, 26, 7, 4, 12, col)
        if k != 'stone':
          game.burst(e['x'], GROUND_Y - 20, 12, 4, 6, 14, (90, 86, 80))
        game.shake_for(5 if k != 'stone' else 2, 7)
        e['life'] = t + 30
  elif k in ('wave', 'stomp'):                          # a ring racing out along the ground
    e['r'] = (t / float(e['life'])) * (220 if k == 'wave' else 170)
    for side in (-1, 1):
      fx_ = e['x'] + side * e['r']
      for name, o in list(targets(game)):
        if id(o) not in e['hit'] and in_zone(o, fx_, 18, GROUND_Y, 120):
          e['hit'].append(id(o))
          kill(game, name, o, (255, 140, 230) if k == 'wave' else (200, 170, 110), sound=False)
  elif k == 'ghost':                                    # stand in it too long and your soul is drained
    for name, o in list(targets(game, 50)):
      if in_zone(o, e['x'], 48, GROUND_Y, 110):
        o['ghost_t'] = o.get('ghost_t', 0) + 1
        if o['ghost_t'] % 6 == 0:
          game.emit(o['rect'].centerx, o['rect'].top, 0, -1.6, 5, (150, 240, 255))
        if o['ghost_t'] > 24:
          kill(game, name, o, (140, 240, 255))
  elif k == 'geyser':
    if t == 12:
      for name, o in list(targets(game)):
        if in_zone(o, e['x'], 38, GROUND_Y):
          o['state'] = 'blown'                          # blasted up into the sky (counted when it leaves the map)
          o['blow_v'] = [random.uniform(1, 3), -random.uniform(15, 19)]
          game.score += int(PTS.get(name, 20) * game.score_mult)
          game.bounty_add('shatter')
  elif k == 'well':                                     # pulls troops into the middle and crushes them
    for name, o in list(targets(game)):
      r = o['rect']
      dx = e['x'] - r.centerx
      if abs(dx) < 140 and r.bottom > GROUND_Y - 120:
        mv = int(max(-5, min(5, dx * 0.08))) or (1 if dx > 0 else -1)
        r.x += mv
        if 'fx' in o:
          o['fx'] = float(r.x)
        if abs(dx) < 16:
          kill(game, name, o, (190, 160, 255))
  elif k == 'ring':
    for name, o in list(targets(game)):
      if id(o) not in e['hit'] and in_zone(o, e['x'], 56, GROUND_Y, 120):
        e['hit'].append(id(o))
        game.glamour(name, o)


# ---------------------------------------------------------------- drawing
_C = {}


def _blob(w, h, col, alpha):
  k = ('blob', w, h, col, alpha)
  s = _C.get(k)
  if s is None:
    s = _C[k] = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(6, 0, -1):
      f = i / 6.0
      pygame.draw.ellipse(s, col + (int(alpha * (1.2 - f)),), (int(w * (1 - f) / 2), int(h * (1 - f) / 2), int(w * f), int(h * f)))
  return s


def draw(gs, game):
  now = pygame.time.get_ticks() / 1000.0
  for e in getattr(game, 'gfx', ()):
    k, t, x = e['k'], e['t'], int(e['x'])
    fade = max(0.0, min(1.0, (e['life'] - t) / 20.0, t / 6.0))
    if k == 'frost':
      gs.blit(_blob(120, 30, (190, 240, 255), int(200 * fade)), (x - 60, GROUND_Y - 18))
      for i in range(5):
        cx = x - 44 + i * 22
        h = 12 + (i * 7) % 11
        pygame.draw.polygon(gs, (220, 248, 255), [(cx - 5, GROUND_Y - 2), (cx, GROUND_Y - 2 - h), (cx + 5, GROUND_Y - 2)])
        pygame.draw.polygon(gs, (120, 200, 240), [(cx - 5, GROUND_Y - 2), (cx, GROUND_Y - 2 - h), (cx + 5, GROUND_Y - 2)], 1)
    elif k == 'strike':
      if t < 10:
        pts, bx, by = [], x + random.randint(-10, 10), 0
        while by < GROUND_Y:
          pts.append((bx, by))
          bx += random.randint(-18, 18)
          by += random.randint(28, 50)
        pts.append((x, GROUND_Y))
        pygame.draw.lines(gs, (255, 240, 150), False, pts, 6)
        pygame.draw.lines(gs, (255, 255, 255), False, pts, 2)
        add_glow(gs, x, GROUND_Y - 20, 70, (110, 100, 30))
    elif k == 'hands':
      rise = min(1.0, t / 14.0) if t < 30 else max(0.0, 1 - (t - 30) / 26.0)
      for i, dx in enumerate((-26, 0, 24)):
        hx, top = x + dx, GROUND_Y - int((34 + i * 6) * rise)
        pygame.draw.line(gs, (226, 228, 214), (hx, GROUND_Y), (hx, top), 5)
        for f in (-2, -1, 0, 1, 2):                     # bony fingers clawing up
          ang = -math.pi / 2 + f * 0.32 + math.sin(now * 6 + i) * 0.1
          pygame.draw.line(gs, (236, 238, 226), (hx, top), (hx + int(math.cos(ang) * 11), top + int(math.sin(ang) * 11)), 2)
      gs.blit(_blob(110, 22, (40, 230, 80), int(110 * fade)), (x - 55, GROUND_Y - 12))
    elif k in ('meteor', 'bomb', 'stone'):
      y = int(e['y'])
      if not e.get('landed'):
        if k == 'meteor':
          for i in range(6):
            pygame.draw.circle(gs, (255, 200 - i * 25, 60), (x + i * 7, y - i * 16), max(2, 11 - i * 2))
          pygame.draw.circle(gs, (110, 80, 70), (x, y), 9)
          add_glow(gs, x, y, 40, (120, 60, 10))
        elif k == 'bomb':
          pygame.draw.circle(gs, (40, 40, 46), (x, y), 9)
          pygame.draw.circle(gs, (110, 110, 120), (x - 3, y - 3), 3)
          pygame.draw.line(gs, (160, 120, 60), (x + 4, y - 8), (x + 8, y - 14), 2)
          if int(now * 20) % 2:
            pygame.draw.circle(gs, (255, 220, 90), (x + 8, y - 15), 3)
        else:
          pygame.draw.ellipse(gs, (236, 226, 200), (x - 8, y - 11, 16, 22))
          pygame.draw.ellipse(gs, (150, 130, 100), (x - 8, y - 11, 16, 22), 2)
      else:
        lt = t - e['landed']
        if lt < 14:
          add_glow(gs, x, GROUND_Y - 16, 60 + lt * 3, (120, 70, 20) if k != 'stone' else (60, 60, 60))
        if k == 'stone' and lt < 26:                      # cracked shell halves
          pygame.draw.arc(gs, (236, 226, 200), (x - 18, GROUND_Y - 20, 16, 16), 0, math.pi, 3)
          pygame.draw.arc(gs, (236, 226, 200), (x + 2, GROUND_Y - 20, 16, 16), 0, math.pi, 3)
    elif k in ('wave', 'stomp'):
      r = int(e['r'])
      col = (255, 140, 230) if k == 'wave' else (210, 180, 120)
      for side in (-1, 1):
        cx = x + side * r
        for j in range(4 if k == 'wave' else 1):
          c = ((255, 90, 90), (255, 220, 90), (110, 230, 140), (120, 170, 255))[j] if k == 'wave' else col
          pygame.draw.arc(gs, c, (cx - 18, GROUND_Y - 34 + j * 4, 36, 40 - j * 4), 0, math.pi, 3)
      if k == 'stomp' and t < 8:
        add_glow(gs, x, GROUND_Y - 10, 80, (90, 70, 30))
    elif k == 'ghost':
      gs.blit(_blob(130, 34, (120, 230, 255), int(150 * fade)), (x - 65, GROUND_Y - 20))
      for i in range(3):
        wy = GROUND_Y - 14 - int(((now * 30 + i * 13) % 40))
        pygame.draw.circle(gs, (180, 250, 255), (x - 30 + i * 30 + int(math.sin(now * 3 + i) * 5), wy), 3)
    elif k == 'geyser':
      h = int(min(1.0, t / 10.0) * 150) if t < 34 else int(150 * max(0.0, 1 - (t - 34) / 18.0))
      if h > 0:
        pygame.draw.rect(gs, (90, 190, 255), (x - 14, GROUND_Y - h, 28, h), border_radius=10)
        pygame.draw.rect(gs, (210, 240, 255), (x - 6, GROUND_Y - h, 12, h), border_radius=6)
        for i in range(5):
          pygame.draw.circle(gs, (220, 245, 255), (x + random.randint(-22, 22), GROUND_Y - h + random.randint(-8, 8)), random.randint(3, 6))
    elif k == 'well':
      for i in range(3):                                  # rings spiralling inwards
        ph = (now * 1.6 + i / 3.0) % 1.0
        rr = int(140 * (1 - ph)) + 6
        pygame.draw.ellipse(gs, (int(150 + 100 * ph), int(130 + 110 * ph), 255), (x - rr, GROUND_Y - 12 - rr // 6, rr * 2, rr // 3 + 4), 2)
      add_glow(gs, x, GROUND_Y - 10, 46, (50, 30, 100))
    elif k == 'ring':
      for i in range(9):                                  # a fairy ring of glowing mushrooms
        a = i / 9.0 * math.tau
        mx, my = x + int(math.cos(a) * 56), GROUND_Y - 6 + int(math.sin(a) * 7)
        pygame.draw.rect(gs, (240, 230, 220), (mx - 2, my - 8, 4, 8))
        pygame.draw.ellipse(gs, ((255, 120, 220), (140, 230, 255), (255, 230, 120))[i % 3], (mx - 7, my - 14, 14, 9))
      add_glow(gs, x, GROUND_Y - 14, 60, (70, 30, 80))
