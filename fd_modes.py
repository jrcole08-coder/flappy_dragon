"""Play modes: Adventure (bosses and quests), Endless (no bosses, keeps getting harder),
Obstacle Course (fly through gaps between pillars, no foes) and the advanced-moves Tutorial.
The game keeps the current mode in game.mode."""
import math
import random
import pygame

MODES = [('adventure', "ADVENTURE", "Bosses, quests and eggs - the full game", 'high_score'),
         ('endless', "ENDLESS", "No bosses. Foes keep coming, faster and faster", 'best_endless'),
         ('obstacle', "OBSTACLE COURSE", "No foes. Fly through the gaps between pillars", 'best_obstacle'),
         ('tutorial', "TUTORIAL", "Learn gliding, diving, swoops, flips and more", None)]

RECORD_KEY = {m[0]: m[3] for m in MODES}


def mode_rects(WIDTH):
  """the four mode cards on the Play screen (2 x 2)"""
  w, h, gx, gy = min(480, (WIDTH - 120) // 2), 140, 36, 22
  x0 = WIDTH // 2 - w - gx // 2
  out = []
  for i, m in enumerate(MODES):
    col, row = i % 2, i // 2
    out.append((m, pygame.Rect(x0 + col * (w + gx), 128 + row * (h + gy), w, h)))
  return out


# ---------------------------------------------------------------- obstacle course
PILLAR_W = 86
PILLAR_EVERY = 400          # pixels flown between pillar pairs
GAP_START, GAP_MIN = 230, 158
MOVE_FROM = 15              # after this many pillars, pairs start sliding up and down


def pillar_motion(passed):
  """(chance a new pair moves, how far it slides, how fast) for the later stretches of the course"""
  if passed < MOVE_FROM:
    return 0.0, 0, 0.0
  k = min(1.0, (passed - MOVE_FROM) / 40.0)              # ramps up over the next 40 pillars
  return 0.45 + 0.55 * k, int(35 + 75 * k), 0.022 + 0.028 * k

# stone colours per world: (light, mid, dark, mortar, cap trim)
PILLAR_STONE = {'kingdom': ((176, 172, 160), (138, 134, 124), (92, 88, 82), (70, 66, 62), (200, 176, 90)),
                'desert': ((226, 186, 128), (196, 150, 96), (150, 108, 66), (120, 84, 50), (240, 210, 120)),
                'swamp': ((128, 138, 104), (98, 108, 80), (62, 72, 52), (44, 52, 38), (110, 160, 70)),
                'frozen': ((214, 236, 250), (160, 196, 226), (104, 140, 180), (80, 110, 150), (240, 250, 255)),
                'volcano': ((84, 74, 78), (58, 50, 54), (34, 28, 32), (255, 110, 30), (255, 160, 50)),
                'skyisle': ((246, 242, 232), (216, 210, 196), (170, 164, 150), (150, 144, 130), (230, 190, 80)),
                'void': ((90, 100, 130), (62, 70, 98), (38, 42, 64), (90, 230, 255), (120, 240, 255))}
_PC = {}


def pillar_body(world, h):
  """a stone column h pixels tall (bricks, shading), made once per world and cut to size"""
  k = ('body', world)
  s = _PC.get(k)
  if s is None:
    lt, md, dk, mo, tr = PILLAR_STONE.get(world, PILLAR_STONE['kingdom'])
    W, H = PILLAR_W, 640
    s = pygame.Surface((W, H))
    for x in range(W):                                     # rounded shading: light on the left, dark on the right
      f = x / float(W - 1)
      c = tuple(int(lt[i] * (1 - f) + dk[i] * f) if f > 0.5 else int(lt[i] + (md[i] - lt[i]) * f * 2) for i in range(3))
      pygame.draw.line(s, c, (x, 0), (x, H))
    for row, y in enumerate(range(0, H, 22)):              # brick courses
      pygame.draw.line(s, mo, (0, y), (W, y), 2)
      off = 0 if row % 2 else W // 2
      for x in (off - W // 2, off):
        if 0 < x < W:
          pygame.draw.line(s, mo, (x, y), (x, y + 22), 2)
    pygame.draw.line(s, dk, (0, 0), (0, H), 2)
    pygame.draw.line(s, dk, (W - 1, 0), (W - 1, H), 2)
    _PC[k] = s = s.convert() if pygame.display.get_surface() else s
  return s.subsurface((0, 0, PILLAR_W, max(1, min(640, int(h)))))


def pillar_cap(world):
  k = ('cap', world)
  s = _PC.get(k)
  if s is None:
    lt, md, dk, mo, tr = PILLAR_STONE.get(world, PILLAR_STONE['kingdom'])
    W, H = PILLAR_W + 18, 26
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(s, md, (0, 0, W, H), border_radius=5)
    pygame.draw.rect(s, lt, (3, 3, W // 2, H - 6), border_radius=4)
    pygame.draw.rect(s, dk, (0, 0, W, H), 3, border_radius=5)
    pygame.draw.line(s, tr, (6, H // 2), (W - 6, H // 2), 2)
    _PC[k] = s
  return s


def obstacle_update(game, d, WIDTH, GROUND_Y):
  """spawn, move and check the pillar pairs"""
  if not hasattr(game, 'pillars'):
    game.pillars, game.pillar_dist, game.pillars_passed = [], 0.0, 0
  game.pillar_dist += game.scroll_px
  if game.pillar_dist >= PILLAR_EVERY:
    game.pillar_dist = 0.0
    gap = max(GAP_MIN, GAP_START - game.pillars_passed * 2)
    lo, hi = 110 + gap // 2, GROUND_Y - 50 - gap // 2
    chance, amp, spd = pillar_motion(game.pillars_passed)
    moving = random.random() < chance
    if moving:
      amp = min(amp, (hi - lo) // 2 - 4)
      lo, hi = lo + amp, hi - amp                             # keep the whole slide on screen
    else:
      amp = 0
    last = game.pillars[-1]['base'] if game.pillars else (lo + hi) // 2
    cy = max(lo, min(hi, last + random.randint(-170 + amp, 170 - amp)))   # never an impossible jump from the last gap
    p = {'x': float(WIDTH + 20), 'cy': cy, 'base': cy, 'gap': gap, 'passed': False, 'amp': amp, 'spd': spd,
         'ph': random.uniform(0, 6.28), 't': 0.0}
    game.pillars.append(p)
    if moving and not getattr(game, 'pillars_moving_told', False):
      game.pillars_moving_told = True
      game.toast("The pillars are moving!")
    if random.random() < 0.6:                                 # a coin floating in the gap (it moves with the gap)
      c = {'rect': pygame.Rect(WIDTH + 20 + PILLAR_W // 2 - 10, cy - 10, 20, 20), 't': 0.0, 'ry': 0}
      game.coins.append(c)
      p['coin'] = c
  keep = []
  for p in game.pillars:
    p['x'] -= game.scroll_px
    if p.get('amp'):                                          # the later pillars slide up and down
      p['t'] += game.ts
      ny = int(p['base'] + math.sin(p['t'] * p['spd'] + p['ph']) * p['amp'])
      c = p.get('coin')
      if c is not None and c in game.coins:
        c['rect'].y += ny - p['cy']
      p['cy'] = ny
    top = pygame.Rect(int(p['x']), -40, PILLAR_W, p['cy'] - p['gap'] // 2 + 40)
    bot = pygame.Rect(int(p['x']), p['cy'] + p['gap'] // 2, PILLAR_W, GROUND_Y - (p['cy'] + p['gap'] // 2))
    hit = d.inflate(-14, -10)
    if (hit.colliderect(top) or hit.colliderect(bot)) and game.dash_inv <= 0 and game.hit_inv <= 0:
      if game.shield_active:
        game.shield_active = False                            # the shield breaks instead
        game.hit_inv = 60
        game.burst(d.centerx, d.centery, 16, 5, 4, 10, (180, 230, 255))
      else:
        game.dead = True
    if not p['passed'] and p['x'] + PILLAR_W < d.x:
      p['passed'] = True
      game.pillars_passed += 1
      game.score += 10 * game.score_mult
      game.dp += 6
      game.bounty_add('dodge')
    if p['x'] > -PILLAR_W - 30:
      keep.append(p)
  game.pillars = keep


def obstacle_draw(gs, game, world, GROUND_Y):
  cap = pillar_cap(world)
  for p in getattr(game, 'pillars', ()):
    x = int(p['x'])
    t = p['cy'] - p['gap'] // 2
    b = p['cy'] + p['gap'] // 2
    if t > 0:
      gs.blit(pillar_body(world, t), (x, 0))
      gs.blit(cap, (x - 9, t - 26))
    if GROUND_Y - b > 0:
      gs.blit(pillar_body(world, GROUND_Y - b + 10), (x, b))
      gs.blit(cap, (x - 9, b))


# ---------------------------------------------------------------- the advanced-moves tutorial
LESSONS = [('flap', "TAP anywhere to flap your wings", 4),
           ('glide', "HOLD your finger down to glide", 100),
           ('dive', "Keep holding and SLIDE your finger DOWN to dive", 14),
           ('swoop', "Dive, then SLIDE back UP to swoop (it won't take you as high)", 6),
           ('flip', "While holding, draw a CIRCLE with your finger to do a flip", 1),
           ('breath', "Fly into the glowing crystal to use your special breath", 1),
           ('dash', "Tap DASH to charge forward", 1),
           ('shield', "Tap SHIELD to raise a magic shield", 1)]
TUT_REWARD = 100


def tutorial_begin(game):
  game.tl = {'i': 0, 'n': 0, 'done_t': 0, 'finished': 0, 'dived': False}
  lesson_start(game)


def lesson_start(game):
  k = LESSONS[game.tl['i']][0]
  game.tl['n'] = 0
  if k == 'breath':
    game.powerups = [{'rect': pygame.Rect(game.dragon.right + 360, game.dragon.centery - 17, 34, 34), 't': 0.0, 'ry': 0}]
  elif k == 'dash':
    game.dash_cd = 0
  elif k == 'shield':
    game.shields = max(1, game.shields)


def tutorial_flap(game):
  tl = getattr(game, 'tl', None)
  if tl and LESSONS[tl['i']][0] == 'flap' and not tl['done_t']:
    tl['n'] += 1


def tutorial_update(game):
  tl = getattr(game, 'tl', None)
  if not tl:
    return
  if tl['finished']:
    tl['finished'] += 1
    return
  if tl['done_t']:                                    # a short "Nice!" before the next lesson
    tl['done_t'] += 1
    if tl['done_t'] > 70:
      tl['done_t'] = 0
      tl['i'] += 1
      if tl['i'] >= len(LESSONS):
        tl['i'] = len(LESSONS) - 1
        tl['finished'] = 1
        if not game.data.get('adv_tutorial_done'):
          game.data['adv_tutorial_done'] = True
          game.data['coins'] += TUT_REWARD
          tl['reward'] = TUT_REWARD
        return
      lesson_start(game)
    return
  k, _msg, need = LESSONS[tl['i']]
  if k == 'glide' and game.gliding:
    tl['n'] += 1
  elif k == 'dive' and game.gliding and game.vel > 5:
    tl['n'] += 1
  elif k == 'swoop':                                # a dive first, then climbing out of it
    if game.gliding and game.vel > 4:
      tl['dived'] = True
    elif tl.get('dived') and game.gliding and game.vel < -0.8:
      tl['n'] += 1
    elif not game.gliding:
      tl['dived'] = False
  elif k == 'flip' and game.flip_t > 0:
    tl['n'] = 1
  elif k == 'breath':
    if game.breath:
      tl['n'] = 1
    elif not game.powerups:                          # missed the crystal: here comes another
      lesson_start(game)
  elif k == 'dash' and game.dash_state == 'out':
    tl['n'] = 1
  elif k == 'shield' and game.shield_active:
    tl['n'] = 1
  if tl['n'] >= need:
    tl['done_t'] = 1
    try:
      from fd_sound import AUDIO
      AUDIO.play('quest')
    except Exception:
      pass


def tutorial_draw(gs, game, fonts, panel_fn, colors):
  tl = getattr(game, 'tl', None)
  if not tl:
    return
  small, tiny, big = fonts
  PANEL_DARK, GOLD_BORDER, PARCHMENT, GOLD = colors
  W = gs.get_width()
  r = pygame.Rect(W // 2 - 330, 92, 660, 96)
  panel_fn(gs, r, PANEL_DARK, 235, GOLD_BORDER, 3, 12)
  if tl['finished']:
    t1 = big.render("TUTORIAL COMPLETE!", True, GOLD)
    gs.blit(t1, t1.get_rect(center=(r.centerx, r.top + 34)))
    msg = ("+%d gold!   " % tl['reward'] if tl.get('reward') else "") + "Back to the Play menu in a moment..."
    t2 = tiny.render(msg, True, PARCHMENT)
    gs.blit(t2, t2.get_rect(center=(r.centerx, r.top + 70)))
    return
  k, msg, need = LESSONS[tl['i']]
  head = tiny.render("LESSON %d OF %d" % (tl['i'] + 1, len(LESSONS)), True, (220, 190, 140))
  gs.blit(head, head.get_rect(center=(r.centerx, r.top + 16)))
  if tl['done_t']:
    t1 = big.render("NICE!", True, GOLD)
  else:
    t1 = small.render(msg, True, PARCHMENT)
    if t1.get_width() > r.w - 30:
      t1 = tiny.render(msg, True, PARCHMENT)
  gs.blit(t1, t1.get_rect(center=(r.centerx, r.top + 46)))
  bar = pygame.Rect(r.left + 60, r.bottom - 22, r.w - 120, 10)       # progress through this lesson
  pygame.draw.rect(gs, (40, 26, 18), bar, border_radius=5)
  f = 1.0 if tl['done_t'] else min(1.0, tl['n'] / float(need))
  if f > 0:
    pygame.draw.rect(gs, (230, 170, 40), (bar.x, bar.y, max(6, int(bar.w * f)), bar.h), border_radius=5)
  pygame.draw.rect(gs, GOLD_BORDER, bar, 1, border_radius=5)
  if k in ('dash', 'shield') and not tl['done_t']:      # bouncing arrow at the button
    import fd_core
    br = fd_core.DASH_BTN if k == 'dash' else fd_core.SHIELD_BTN
    bob = int(math.sin(pygame.time.get_ticks() / 160.0) * 6)
    left_side = br.centerx < W // 2
    x = br.right + 16 + bob if left_side else br.left - 16 - bob
    pts = [(x, br.centery), (x + (22 if left_side else -22), br.centery - 14), (x + (22 if left_side else -22), br.centery + 14)]
    pygame.draw.polygon(gs, GOLD, pts)
    pygame.draw.polygon(gs, (60, 30, 10), pts, 2)
