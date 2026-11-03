"""Achievements: long-term goals with gold rewards, shown on their own page (from the Quests board).
Lifetime numbers live in data['stats']; record_run() adds a finished run, check() unlocks anything newly earned."""
import pygame

# key, title, description, stat, target, gold
ACHIEVEMENTS = [
  ('first_flight', "First Flight", "Finish your first run", 'runs', 1, 50),
  ('frequent_flyer', "Frequent Flyer", "Play 50 runs", 'runs', 50, 400),
  ('slayer1', "Monster Slayer", "Defeat 100 foes", 'kills', 100, 150),
  ('slayer2', "Legend of the Skies", "Defeat 1,000 foes", 'kills', 1000, 600),
  ('slayer3', "Scourge of the Realm", "Defeat 5,000 foes", 'kills', 5000, 1500),
  ('boss1', "Giant Killer", "Defeat your first boss", 'bosses', 1, 200),
  ('boss_all', "Boss Hunter", "Defeat all 9 bosses at least once", 'boss_types', 9, 2500),
  ('hydra', "Heads Will Roll", "Slay the Hydra", 'hydra', 1, 1000),
  ('score1', "Rising Star", "Score 5,000 in one run", 'best', 5000, 150),
  ('score2', "Sky Champion", "Score 25,000 in one run", 'best', 25000, 600),
  ('score3', "Dragon Lord", "Score 60,000 in one run", 'best', 60000, 2000),
  ('endless', "No End in Sight", "Score 15,000 in Endless mode", 'best_endless', 15000, 700),
  ('pillars', "Needle Threader", "Pass 40 pillars in the Obstacle Course", 'best_obstacle', 40, 600),
  ('tutorial', "Star Pupil", "Finish the Tutorial", 'tutorial', 1, 100),
  ('hatch1', "Proud Parent", "Hatch your first egg", 'hatched', 1, 150),
  ('hatch2', "Dragon Breeder", "Hatch 15 eggs", 'hatched', 15, 800),
  ('adult', "All Grown Up", "Raise a baby to Adult", 'adults', 1, 500),
  ('roster5', "Collector", "Own 5 dragons", 'owned', 5, 300),
  ('roster12', "Dragon Keeper", "Own 12 dragons", 'owned', 12, 1200),
  ('lvl10', "Seasoned", "Raise a dragon to level 10", 'max_level', 10, 500),
  ('lvl20', "Ascended", "Raise a dragon to level 20", 'max_level', 20, 2500),
  ('ult', "Unleashed", "Use an Ultimate", 'ults', 1, 300),
  ('quests', "Quest Master", "Complete 25 quests", 'quests', 25, 800),
  ('worlds', "World Traveller", "Fly in all 7 worlds", 'worlds', 7, 700),
  ('gold', "Dragon's Hoard", "Collect 5,000 coins in total", 'coins', 5000, 500),
]
PER_PAGE = 10


def stats(data):
  return data.setdefault('stats', {'runs': 0, 'kills': 0, 'bosses': 0, 'boss_types': [], 'ults': 0, 'coins': 0, 'worlds': []})


def value(data, stat):
  """the current number for one achievement"""
  s = stats(data)
  if stat == 'boss_types':
    return len(s.get('boss_types', []))
  if stat == 'hydra':
    return 1 if 'hydra' in s.get('boss_types', []) else 0
  if stat == 'worlds':
    return len(s.get('worlds', []))
  if stat == 'best':
    return data.get('high_score', 0)
  if stat in ('best_endless', 'best_obstacle'):
    return data.get(stat, 0)
  if stat == 'tutorial':
    return 1 if data.get('adv_tutorial_done') else 0
  if stat == 'hatched':
    return data.get('hatched', 0)
  if stat == 'adults':
    return sum(1 for bb in data.get('babies', []) if bb.get('level', 1) >= 10)
  if stat == 'owned':
    return len(data.get('unlocked', []))
  if stat == 'max_level':
    return max([v[0] for v in data.get('dlv', {}).values()] or [1])
  if stat == 'quests':
    return data.get('completed_quests', 0)
  return s.get(stat, 0)


def record_run(game):
  """add a finished run to the lifetime numbers"""
  d = game.data
  s = stats(d)
  rs = getattr(game, 'run_stats', None) or {}
  s['runs'] = s.get('runs', 0) + 1
  s['kills'] = s.get('kills', 0) + sum((rs.get('kills') or {}).values())
  bl = rs.get('bosses') or []
  s['bosses'] = s.get('bosses', 0) + len(bl)
  bt = s.setdefault('boss_types', [])
  for b in bl:
    if b not in bt:
      bt.append(b)
  s['coins'] = s.get('coins', 0) + int(getattr(game, 'run_coins', 0))
  w = game.world()
  if w not in s.setdefault('worlds', []):
    s['worlds'].append(w)


def check(game, quiet=False):
  """unlock (and pay out) everything newly earned; returns how many"""
  d = game.data
  got = d.setdefault('achieved', [])
  n = 0
  for key, title, desc, stat, target, gold in ACHIEVEMENTS:
    if key not in got and value(d, stat) >= target:
      got.append(key)
      d['coins'] += gold
      n += 1
      if not quiet:
        game.toast("Achievement: %s!  +%d gold" % (title, gold))
  return n


def page_count():
  return (len(ACHIEVEMENTS) + PER_PAGE - 1) // PER_PAGE


def card_rects(WIDTH):
  w, h, gx, gy = 460, 66, 20, 4
  x0 = WIDTH // 2 - w - gx // 2
  return [pygame.Rect(x0 + (i % 2) * (w + gx), 120 + (i // 2) * (h + gy), w, h) for i in range(PER_PAGE)]


def nav_rects(WIDTH):
  """prev / back / next, clear of the tab bar along the bottom"""
  y = 478
  return (pygame.Rect(WIDTH // 2 - 340, y, 200, 44), pygame.Rect(WIDTH // 2 - 100, y, 200, 44), pygame.Rect(WIDTH // 2 + 140, y, 200, 44))


def draw(gs, game, fonts, colors, WIDTH):
  small, tiny = fonts
  PANEL_DARK, GOLD_BORDER, PARCHMENT, GOLD = colors
  from fd_core import panel
  d = game.data
  got = d.get('achieved', [])
  page = getattr(game, 'ach_page', 0) % page_count()
  items = ACHIEVEMENTS[page * PER_PAGE:(page + 1) * PER_PAGE]
  for r, (key, title, desc, stat, target, gold) in zip(card_rects(WIDTH), items):
    done = key in got
    panel(gs, r, (40, 54, 30) if done else (34, 24, 20), 236, GOLD if done else GOLD_BORDER, 3, 10)
    t1 = small.render(title, True, GOLD if done else PARCHMENT)
    gs.blit(t1, (r.left + 14, r.top + 6))
    t2 = tiny.render(desc, True, (220, 205, 180))
    gs.blit(t2, (r.left + 14, r.top + 31))
    rw = tiny.render(("DONE  +%d" % gold) if done else ("+%d gold" % gold), True, (140, 230, 120) if done else (230, 190, 90))
    gs.blit(rw, rw.get_rect(topright=(r.right - 12, r.top + 5)))
    v = min(target, value(d, stat))
    bar = pygame.Rect(r.left + 14, r.bottom - 14, r.w - 28, 7)
    pygame.draw.rect(gs, (24, 16, 12), bar, border_radius=3)
    f = 1.0 if done else v / float(target)
    if f > 0:
      pygame.draw.rect(gs, (120, 220, 100) if done else (230, 170, 40), (bar.x, bar.y, max(4, int(bar.w * f)), bar.h), border_radius=3)
    if not done and target > 1:
      pt = tiny.render("{:,} / {:,}".format(v, target), True, (200, 190, 170))
      gs.blit(pt, pt.get_rect(bottomright=(r.right - 12, bar.top - 1)))
  hd = tiny.render("%d / %d earned      page %d of %d" % (len(got), len(ACHIEVEMENTS), page + 1, page_count()), True, PARCHMENT)
  gs.blit(hd, hd.get_rect(center=(WIDTH // 2, 106)))
