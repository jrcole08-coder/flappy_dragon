"""The three new bosses from your art: the Sphinx, the Manticore and the Mothman.
make(kind) builds one; ai(game, b) runs its attacks; dying(game, b) plays its death; draw(gs, b) draws it."""
import math
import random
import pygame
from fd_core import WIDTH, HEIGHT, GROUND_Y, BOSS_X, GROUND_LISTS, MAX_HEARTS, add_glow, blit_text, hud_font
from fd_sound import AUDIO
from fd_newfoes import nf_frame, nf_count, nf_has, nf_bottom

NEW_BOSSES = ('sphinx', 'manticore', 'mothman')
HP = {'sphinx': 700.0, 'manticore': 780.0, 'mothman': 840.0}
BOX = {'sphinx': (130, 110), 'manticore': (140, 120), 'mothman': (120, 150)}     # hit box (w, h)
TICKS = 2                                   # game frames per animation frame
NAMES = {'sphinx': "SPHINX", 'manticore': "MANTICORE", 'mothman': "MOTHMAN"}
# attack order (the second list is used once it is below half health)
SEQ = {'sphinx': (['bite', 'buffet', 'pounce', 'buffet'], ['pounce', 'buffet', 'bite', 'pounce', 'buffet']),
       'manticore': (['tail', 'bite', 'tail', 'swoop'], ['tail', 'swoop', 'tail', 'bite', 'swoop']),
       'mothman': (['magic', 'claw', 'drive', 'magic'], ['magic', 'drive', 'magic', 'claw', 'drive'])}
ANIM = {('sphinx', 'bite'): 'bite', ('sphinx', 'buffet'): 'buffet', ('sphinx', 'pounce'): 'pounce',
        ('manticore', 'bite'): 'bite', ('manticore', 'tail'): 'tail', ('manticore', 'swoop'): 'dive',
        ('mothman', 'claw'): 'claw', ('mothman', 'magic'): 'magic', ('mothman', 'drive'): 'drive'}
RUSH = ('pounce', 'swoop', 'drive')            # these fly right across the sky at you
LUNGE = ('bite', 'claw')                      # these dart forward a little way and snap


def make(kind, WIDTH, HEIGHT):
  y = HEIGHT // 2 - 120.0
  return {'type': kind, 'x': WIDTH + 160.0, 'y': y, 'by': y, 'hp': HP[kind], 'max_hp': HP[kind], 'timer': 0.0, 'state': 'entering',
          'atk': 'idle', 'at': 0, 'cool': 70, 'seq': 0, 'fi': 0, 'anim': 'fly', 'flash': 0, 'hurt': 0, 'dt': 0, 'alpha': 255, 'ghost': False}


def rect(b):
  w, h = BOX[b['type']]
  return pygame.Rect(int(b['x']), int(b['y']), w, h)


def centre(b):
  w, h = BOX[b['type']]
  return b['x'] + w / 2.0, b['y'] + h / 2.0


def _hit_dragon(game, b):
  """body attacks: the shield soaks one, otherwise it costs a heart (or the run)"""
  d = game.dragon
  if game.dash_inv:
    return
  if game.shield_active:
    if not b.get('hit'):
      game.shield_active = False
      game.burst(d.centerx, d.centery, 16, 6, 4, 10, (200, 230, 255))
      AUDIO.play('shatter', 0.6)
    b['hit'] = True
  else:
    game.dead = True


def ai(game, b):
  d = game.dragon
  k = b['type']
  b['at'] += 1
  at, atk = b['at'], b['atk']
  if b.get('flash', 0) > 0:
    b['flash'] -= 1
  fast = b['hp'] <= b['max_hp'] / 2
  cx, cy = centre(b)
  w, h = BOX[k]
  if atk not in RUSH + ('rush_warn', 'return'):
    b['y'] += (b['by'] + math.sin(b['timer'] * 0.9) * 70 - b['y']) * 0.12
  b['anim'], b['fi'] = 'fly', int(b['timer'] * 8)
  if atk == 'idle':
    if b['x'] > BOSS_X:
      b['x'] -= 4
    b['cool'] -= 1
    if b['cool'] <= 0:
      seq = SEQ[k][1 if fast else 0]
      nxt = seq[b['seq'] % len(seq)]
      b['seq'] += 1
      b['at'] = 0
      b['hit'] = False
      b['atk'] = 'rush_warn' if nxt in RUSH else nxt
      b['next'] = nxt
      AUDIO.play('roar', 0.6)
    return
  if atk == 'rush_warn':                            # flashes red and lines up with you, then goes
    b['anim'], b['fi'] = 'fly', int(b['timer'] * 8)
    b['flash'] = 3 if at % 10 < 5 else 0
    b['warn'] = True
    if at < 30:
      b['ty'] = max(10.0, min(GROUND_Y - h - 10.0, d.centery - h / 2.0))
    b['y'] += (b.get('ty', b['y']) - b['y']) * 0.12
    if at >= 40:
      b['atk'], b['at'], b['warn'] = b['next'], 0, False
      AUDIO.play('whoosh', 0.9)
    return
  if atk == 'return':
    b['anim'], b['fi'] = 'fly', int(b['timer'] * 8)
    b['x'] -= 6
    if b['x'] <= BOSS_X:
      b['x'] = float(BOSS_X)
      b['atk'], b['at'], b['cool'] = 'idle', 0, 45 if fast else 70
    return
  an = ANIM[(k, atk)]
  n = nf_count(k, an)
  b['anim'], b['fi'] = an, min(n - 1, at // TICKS)
  if atk in RUSH:                                   # tears across the sky
    b['fi'] = min(n - 1, max(n // 3, at // TICKS))
    b['x'] -= (15 if k != 'mothman' else 18) * game.ts
    if game.tick:
      col = {'sphinx': (230, 200, 120), 'manticore': (200, 120, 60), 'mothman': (160, 40, 50)}[k]
      game.emit(b['x'] + w, b['y'] + random.randint(20, h - 20), random.uniform(1, 3), random.uniform(-1, 1), random.randint(6, 11), col)
    if d.colliderect(rect(b).inflate(-20, -20)):
      _hit_dragon(game, b)
    if b['x'] < -w - 120:
      b['x'], b['y'], b['hit'] = WIDTH + 90.0, b['by'], False
      b['atk'], b['at'] = 'return', 0
    return
  if atk in LUNGE:                                  # darts forward and snaps
    mid = n * TICKS // 2
    b['x'] += (-9 if at < mid else 9) * game.ts
    b['y'] += (d.centery - h / 2.0 - b['y']) * 0.06
    if at < mid + 6 and d.colliderect(rect(b).inflate(-30, -30)):
      _hit_dragon(game, b)
  elif atk == 'buffet':                             # Sphinx: beats its wings and flings blades of sand
    if at in (14, 20, 26, 32) or (fast and at in (17, 29)):
      sx, sy = b['x'] + 10, cy - 10
      a = math.atan2(d.centery - sy, d.centerx - sx) + random.uniform(-0.25, 0.25)
      game.orbs.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(a) * 8.5, 'vy': math.sin(a) * 8.5, 'state': 'normal', 'col': (240, 200, 110), 'r': 10,
                        'home': False})
      game.burst(sx, sy, 8, 3, 3, 7, (240, 210, 140))
      AUDIO.play('whoosh', 0.4)
  elif atk == 'tail':                               # Manticore: a fan of tail spikes
    if at in (16, 26) or (fast and at == 36):
      sx, sy = b['x'] + w * 0.7, b['y'] + 10
      for j in range(5 if fast else 4):
        a = math.atan2(d.centery - sy, d.centerx - sx) + (j - 2) * 0.16
        game.arrows.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(a) * 10.5, 'vy': math.sin(a) * 10.5, 'state': 'normal', 'kind': 'icicle'})
      game.burst(sx, sy, 10, 3, 3, 7, (200, 150, 90))
      AUDIO.play('launch', 0.5)
  elif atk == 'magic':                              # Mothman: wing-dust motes that hunt you
    if 18 <= at <= 34 and at % 4 == 2:
      sx, sy = cx - 10 + random.uniform(-40, 40), cy - 30 + random.uniform(-30, 30)
      a = math.atan2(d.centery - sy, d.centerx - sx)
      game.orbs.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(a) * 4.0, 'vy': math.sin(a) * 4.0, 'state': 'normal', 'col': (255, 70, 80), 'r': 8,
                        'home': True})
      game.emit(sx, sy, 0, 0, 8, (255, 120, 120))
  if at >= n * TICKS + 8:
    b['atk'], b['at'], b['cool'] = 'idle', 0, 40 if fast else 65


def dying(game, b):
  """falls to the ground and plays its death (the Sphinx has no death frames yet: it crumbles into sand)"""
  k = b['type']
  w, h = BOX[k]
  b['dt'] += 1
  has = nf_has(k, 'death')
  n = nf_count(k, 'death') if has else 1
  if b.get('landed', -1) < 0:
    b['vy'] = b.get('vy', 0.0) + 0.9
    cy = b['y'] + h / 2.0
    if cy + (nf_bottom(k, 'death', 0) if has else nf_bottom(k, 'fly', 0)) >= GROUND_Y - 4:
      b['landed'] = b['dt']
      game.shake_for(14, 18)
      game.burst(b['x'] + w / 2, GROUND_Y - 6, 30, 6, 6, 14, (200, 180, 150))
      AUDIO.play('shatter', 0.9)
    else:
      b['y'] += b['vy']
  else:
    kk = b['dt'] - b['landed']
    b['fi'] = min(n - 1, kk // 4)
    if not has and kk % 3 == 0:                    # (no death frames) the Sphinx crumbles into sand
      game.burst(b['x'] + random.randint(10, w - 10), b['y'] + random.randint(10, h - 10), 6, 3, 3, 7, random.choice(((230, 200, 130), (200, 170, 100), (250, 230, 170))))
    hold = n * 4 + 40
    if kk > hold:
      b['alpha'] = max(0, 255 - (kk - hold) * 8)
    if kk > hold + 32:
      game.boss = None


def draw(gs, b):
  k = b['type']
  cx, cy = centre(b)
  if b['state'] == 'dying':
    if nf_has(k, 'death'):
      spr, ax, ay = nf_frame(k, 'death', b.get('fi', 0) if b.get('landed', -1) >= 0 else 0, clamp=True)
    else:
      spr, ax, ay = nf_frame(k, 'fly', 0)
  else:
    an = b.get('anim', 'fly')
    spr, ax, ay = nf_frame(k, an, b.get('fi', 0), clamp=an != 'fly')
  if b.get('flash', 0) > 0 and b['state'] != 'dying':
    spr = spr.copy()
    spr.fill((150, 40, 40) if b.get('warn') else (110, 110, 120), special_flags=pygame.BLEND_RGB_ADD)
  al = b.get('alpha', 255)
  if al < 255:
    spr = spr.copy()
    spr.set_alpha(max(0, al))
  add_glow(gs, int(cx), int(cy), 120, {'sphinx': (50, 40, 20), 'manticore': (50, 26, 14), 'mothman': (50, 10, 16)}[k])
  if k == 'mothman' and b['state'] != 'dying':        # the glowing red eyes
    add_glow(gs, int(cx - 14), int(cy - 50), 26, (110, 10, 14))
  gs.blit(spr, (int(cx - ax), int(cy - ay)))
  if b.get('warn') and b.get('at', 0) % 10 < 6 and b['state'] != 'dying':
    blit_text(gs, hud_font, "!", (255, 90, 60), (int(cx), int(b['y']) - 30), "center")
