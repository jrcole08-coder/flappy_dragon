"""The new foes from your art: banshee, vulture, Egyptian scarab, flying snakes, djinn and wyvern.
Each one flies in from the right and attacks with its own animation (see fd_newfoes for the frames).
spawn(game, kind) adds them; ai(game, e) runs one each frame; draw(gs, game, e) draws it."""
import math
import random
import pygame
from fd_core import WIDTH, HEIGHT, GROUND_Y, BOSS_X, GROUND_LISTS, MAX_HEARTS, add_glow, blit_text, hud_font
from fd_sound import AUDIO
from fd_newfoes import nf_frame, nf_count, nf_has, nf_bottom, META

# (hitbox w, h), speed, what its attack does, and how many game frames per animation frame
FOE = {'banshee': dict(box=(44, 54), speed=2.4, ticks=3, attack='wail', every=(90, 130), fire=13, pts=12),
       'vulture': dict(box=(50, 40), speed=4.2, ticks=2, attack='dash', every=(70, 110), fire=4, pts=10),
       'scarab': dict(box=(44, 38), speed=3.6, ticks=2, attack='charge', every=(60, 100), fire=4, pts=10),
       'snake': dict(box=(36, 30), speed=4.6, ticks=2, attack='spit', every=(80, 140), fire=5, pts=4),
       'djinn': dict(box=(40, 60), speed=2.2, ticks=2, attack='magic', every=(80, 120), fire=12, pts=12),
       'wyrm': dict(box=(56, 40), speed=5.0, ticks=2, attack='fire', every=(90, 140), fire=10, pts=10)}
ART = {'wyrm': 'wyvern'}                       # (the floating-eye swarm already uses the name "wyvern" in the code)
ATTACK_ANIM = {'banshee': 'attack', 'vulture': 'attack', 'scarab': 'attack', 'snake': 'spit', 'djinn': 'attack', 'wyrm': 'flap'}
NAMES = ('banshee', 'vulture', 'scarab', 'snake', 'djinn', 'wyrm')

# which new foes each world favours (they can turn up anywhere)
WORLD_FOES = {'desert': ('scarab', 'scarab', 'vulture', 'djinn', 'djinn'), 'swamp': ('snake', 'snake', 'banshee', 'banshee'),
              'frozen': ('wyrm', 'wyrm', 'banshee'), 'volcano': ('wyrm', 'vulture', 'vulture'), 'skyisle': ('vulture', 'wyrm', 'djinn'),
              'void': ('banshee', 'djinn', 'djinn'), 'kingdom': ('vulture', 'banshee')}


def pool_for(game):
  """extra spawn choices for the current world and threat level"""
  t = game.threat
  out = []
  if t >= 2:
    out += ['vulture', 'snake']
  if t >= 3:
    out += ['banshee', 'scarab', 'wyrm']
  if t >= 4:
    out += ['djinn']
  if t >= 2:
    out += list(WORLD_FOES.get(game.world(), ()))
  return ['nf:' + k for k in out]


def spawn(game, kind):
  c = FOE[kind]
  n = random.choice((2, 3, 3, 4)) if kind == 'snake' else (2 if kind == 'vulture' and random.random() < 0.3 else 1)
  base = random.randint(90, GROUND_Y - 200)
  for i in range(n):
    w, h = c['box']
    x = WIDTH + 20 + i * 70
    by = max(50, min(GROUND_Y - h - 30, base + (i % 2) * 46 - (i // 2) * 30))
    if kind == 'scarab':                         # scarabs skim low over the sand
      by = random.randint(GROUND_Y - 190, GROUND_Y - 90)
    game.enemies.append({'rect': pygame.Rect(x, by, w, h), 'fx': float(x), 'nf': kind, 'foe': kind, 'speed': c['speed'] + game.threat * 0.12,
                         'passed': False, 'state': 'normal', 'vy': 0.0, 'by': float(by), 'phase': random.uniform(0, 6.3) + i,
                         'age': 0.0, 'atk': 0.0, 'ct': random.randint(*c['every']) * 0.6, 'fired': False, 'dash': 0.0})


def ai(game, e):
  d, r = game.dragon, e['rect']
  k = e['nf']
  c = FOE[k]
  ts = game.ts
  e['age'] += ts
  sp = e['speed']
  if e['atk'] > 0:                                # mid attack
    e['atk'] += ts
    fi = e['atk'] / c['ticks']
    n = nf_count(ART.get(k, k), ATTACK_ANIM[k])
    if c['attack'] in ('dash', 'charge'):          # lunges at you: fast and homing on your height
      if fi >= c['fire']:
        sp = e['speed'] * (3.4 if k == 'scarab' else 3.0)
        e['by'] += (d.centery - r.h // 2 - e['by']) * (0.05 if k == 'scarab' else 0.08)
        if random.random() < 0.5:
          game.emit(r.right, r.centery, random.uniform(1, 3), random.uniform(-1, 1), random.randint(4, 8),
                    (230, 220, 200) if k == 'vulture' else (120, 230, 120))
    elif not e['fired'] and fi >= c['fire']:
      e['fired'] = True
      sx, sy = float(r.left + 4), float(r.centery - (6 if k != 'snake' else 2))
      a = math.atan2(d.centery - sy, d.centerx - sx)
      if c['attack'] == 'wail':                   # a cold ring of sound
        spd = 7.0 + game.threat * 0.12
        game.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (180, 235, 255), 'r': 13,
                          'home': False, 'kind': 'sonic', 'pal': ((235, 250, 255), (150, 220, 255), (70, 140, 200)), 'fr': 0.0})
        AUDIO.play('whoosh', 0.5)
      elif c['attack'] == 'spit':                 # venom
        spd = 8.0 + game.threat * 0.1
        game.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (130, 255, 90), 'r': 7, 'home': False})
        game.burst(sx, sy, 6, 2, 2, 5, (150, 255, 110))
      elif c['attack'] == 'magic':                # a ball of blue djinn magic that curves after you
        spd = 5.2 + game.threat * 0.1
        game.orbs.append({'x': sx, 'y': sy - 8, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (90, 200, 255), 'r': 11,
                          'home': True, 'kind': 'wiz'})
        game.burst(sx, sy, 10, 3, 3, 7, (150, 230, 255))
        AUDIO.play('whoosh', 0.4)
      elif c['attack'] == 'fire':                 # the wyvern spits a fireball
        game.fireballs.append({'x': sx - 10, 'y': sy, 'vx': math.cos(a) * 8.0, 'vy': math.sin(a) * 8.0, 'state': 'normal', 'straight': True})
        AUDIO.play('launch', 0.4)
    if fi >= n:
      e['atk'] = 0.0
      e['fired'] = False
      e['ct'] = random.randint(*c['every'])
  else:
    e['ct'] -= ts
    in_range = d.centerx + 110 < r.x < WIDTH - 40
    if c['attack'] in ('dash', 'charge'):
      in_range = in_range and r.x - d.right < 520 and abs(r.centery - d.centery) < 220
    if e['ct'] <= 0 and in_range:
      e['atk'] = 1.0
      if c['attack'] in ('dash', 'charge'):
        AUDIO.play('whoosh', 0.5)
    if k in ('banshee', 'djinn'):                 # slow drifters hang back to cast
      sp *= 0.35 if r.x < WIDTH - 220 else 1.0
  e['fx'] -= sp * ts
  r.x = int(e['fx'])
  wave = {'banshee': (0.05, 34), 'djinn': (0.04, 22), 'snake': (0.11, 26), 'vulture': (0.06, 18), 'scarab': (0.09, 10), 'wyrm': (0.07, 30)}[k]
  y = e['by'] + math.sin(e['age'] * wave[0] + e['phase']) * wave[1]
  r.y = int(max(30, min(GROUND_Y - r.h - 8, y)))


def draw(gs, game, e):
  k = e['nf']
  art = ART.get(k, k)
  r = e['rect']
  c = FOE[k]
  if e.get('atk', 0) > 0:
    an = ATTACK_ANIM[k]
    spr, ax, ay = nf_frame(art, an, e['atk'] / c['ticks'], clamp=True)
  else:
    spr, ax, ay = nf_frame(art, 'fly', e['age'] / c['ticks'] + e['phase'] * 3)
  if k == 'djinn' and e.get('atk', 0) > 0:
    add_glow(gs, r.centerx - 10, r.centery - 6, 40, (14, 50, 80))
  gs.blit(spr, (r.centerx - ax, r.centery - ay))


# ---------------------------------------------------------------- deaths
def corpse(game, e):
  """the new foes play their own death animation (the wyvern has none yet: it tumbles and fades)"""
  k = e['nf']
  art = ART.get(k, k)
  r = e['rect']
  if nf_has(art, 'death'):
    n = nf_count(art, 'death')
    floor = GROUND_Y - nf_bottom(art, 'death', n - 1) - 2
    floats = k in ('banshee', 'djinn', 'snake')    # these vanish in the air
    game.corpses.append({'k': 'nf', 'art': art, 'x': float(r.centerx), 'y': float(r.centery), 't': 0, 'vy': 0.0 if floats else -1.5,
                         'floor': float(r.centery) if floats else float(floor), 'n': n, 'rate': 4 if k != 'banshee' else 6})
  else:
    game.corpses.append({'k': 'nf', 'art': art, 'x': float(r.centerx), 'y': float(r.centery), 't': 0, 'vy': -3.0,
                         'floor': float(GROUND_Y - 20), 'n': 10, 'rate': 4, 'spin': True})
  game.burst(r.centerx, r.centery, 12, 4, 3, 8, {'banshee': (190, 235, 255), 'djinn': (110, 220, 255), 'snake': (120, 200, 90),
                                                 'scarab': (90, 210, 110), 'vulture': (60, 50, 50), 'wyrm': (170, 150, 90)}.get(k, (200, 200, 200)))


_SPIN = {}


def draw_corpse(gs, c):
  if c.get('spin'):                               # no death frames: tumbles and fades
    spr, ax, ay = nf_frame(c['art'], 'fly', 0)
    key = ('nfspin', c['art'], (c['t'] // 3) % 12)
    rot = _SPIN.get(key)
    if rot is None:
      rot = _SPIN[key] = pygame.transform.rotate(spr, ((c['t'] // 3) % 12) * 30)
    rot = rot.copy()
    rot.set_alpha(max(0, 255 - c['t'] * 6))
    gs.blit(rot, (int(c['x']) - rot.get_width() // 2, int(c['y']) - rot.get_height() // 2))
    return
  spr, ax, ay = nf_frame(c['art'], 'death', c['t'] // c['rate'], clamp=True)
  end = c['n'] * c['rate']
  if c['t'] > end:
    spr = spr.copy()
    spr.set_alpha(max(0, 255 - (c['t'] - end) * 9))
  gs.blit(spr, (int(c['x']) - ax, int(c['y']) - ay))


# ---------------------------------------------------------------- your new catapult art
def catapult_frame(o, siege_pose):
  """(anim, frame) for a catapult from its timers: cranks back while loading, then swings and throws"""
  if not o.get('fired'):
    prog = min(1.0, (1.0 - max(0.0, o.get('timer', 35)) / 35.0) / 0.8)
    return 'crank', int(prog * 9)
  sw = o.get('swing', 0)
  return 'attack', min(20, 8 + int(sw * 1.3))


def trebuchet_frame(o):
  """your trebuchet art: hauls the arm down while loading, then swings over the top and lets go"""
  if not o.get('fired'):
    prog = min(1.0, 1.0 - max(0.0, o.get('timer', 30)) / 30.0)
    return 'attack', int(prog * 8)
  return 'attack', min(20, 8 + int(o.get('swing', 0) * 0.75))


def ballista_frame(o):
  """your ballista art: winds and aims while loading, the bolt leaves on frame 15, then it settles"""
  if o.get('mode') != 'fired':
    prog = min(1.0, 1.0 - max(0.0, o.get('timer', 35)) / 35.0)
    return 'attack', int(prog * 14)
  return 'attack', min(20, 15 + o.get('ft', 0) // 3)
