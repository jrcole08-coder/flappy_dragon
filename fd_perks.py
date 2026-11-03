"""Level rewards for every dragon.
  Level 10: a stronger special (breath lasts 25% longer and hits bosses 25% harder).
  Level 15: a passive of its own (PERK).
  Level 20: an Ultimate: fill the bar by defeating foes, then tap ULT to unleash it across the whole screen."""
import math
import random
import pygame
from fd_core import WIDTH, HEIGHT, GROUND_Y, BOSS_X, GROUND_LISTS, MAX_HEARTS, add_glow, blit_text, hud_font
from fd_sound import AUDIO
import fd_ground as G
import fd_ultfx as UFX

LV_SPECIAL, LV_PERK, LV_ULT = 10, 15, 20
ULT_NEED = 40                    # foes defeated to charge the Ultimate

PERK = {'RED': 'refill', 'BLUE': 'scales', 'GREEN': 'magnet', 'ALIEN': 'refill', 'YELLOW': 'chain', 'SILVER': 'dash', 'FOREST': 'heal',
        'SKELETAL': 'refill', 'COSMIC': 'bossshield', 'UNICORN': 'coins', 'WRAITH': 'ghost', 'CHINESE': 'coins', 'CLOCKWORK': 'charge',
        'COCKATRICE': 'charge', 'WHALE': 'heal', 'FEY': 'heart', 'EAGLE': 'talon2', 'RAVEN': 'talon2', 'PERYTON': 'talon2'}
PERK_TEXT = {'refill': "Kills keep your special breath going longer",
             'scales': "Arrows, spikes and shards bounce off",
             'magnet': "Coins fly to you from twice as far",
             'chain': "Lightning jumps one extra time",
             'dash': "Dash recharges twice as fast",
             'heal': "Every 30 foes defeated heals a heart",
             'bossshield': "A free shield after every boss",
             'coins': "Coins are worth double",
             'ghost': "Stays safe twice as long after a hit",
             'charge': "Shield charge fills 50% faster",
             'heart': "Starts every run with an extra heart",
             'talon2': "Every tap strikes one extra foe"}
ULT_NAME = {'RED': "METEOR STORM", 'BLUE': "BLIZZARD", 'GREEN': "ACID RAIN", 'ALIEN': "ABDUCTION", 'YELLOW': "THUNDERSTORM", 'SILVER': "HURRICANE",
            'FOREST': "OVERGROWTH", 'SKELETAL': "DEATH TOLL", 'COSMIC': "SUPERNOVA", 'UNICORN': "PRISM BURST", 'WRAITH': "SOUL HARVEST",
            'CHINESE': "TIDAL WAVE", 'CLOCKWORK': "CARPET BOMB", 'COCKATRICE': "STONE GAZE", 'WHALE': "BLACK HOLE", 'FEY': "WILD MAGIC",
            'EAGLE': "TALON STORM", 'RAVEN': "MURDER OF CROWS", 'PERYTON': "STAMPEDE"}
ULT_COL = {'RED': (255, 120, 30), 'BLUE': (170, 230, 255), 'GREEN': (130, 255, 80), 'ALIEN': (130, 255, 90), 'YELLOW': (255, 240, 120),
           'SILVER': (220, 230, 240), 'FOREST': (120, 200, 60), 'SKELETAL': (150, 255, 150), 'COSMIC': (200, 140, 255), 'UNICORN': (255, 140, 230),
           'WRAITH': (140, 240, 255), 'CHINESE': (100, 200, 255), 'CLOCKWORK': (255, 190, 90), 'COCKATRICE': (200, 196, 186), 'WHALE': (170, 140, 255),
           'FEY': (255, 150, 240), 'EAGLE': (255, 220, 140), 'RAVEN': (170, 120, 230), 'PERYTON': (255, 90, 90)}


def lv(game):
  return game.dragon_lv()[0]


def has_special(game):
  return lv(game) >= LV_SPECIAL


def perk(game):
  return PERK.get(game.selected) if lv(game) >= LV_PERK else None


def has_ult(game):
  return lv(game) >= LV_ULT


def on_kill(game):
  """called for every foe defeated"""
  p = perk(game)
  if p == 'refill' and game.breath:
    game.breath_timer = min(game.breath_time, game.breath_timer + 12)
  elif p == 'heal':
    game.heal_kills = getattr(game, 'heal_kills', 0) + 1
    if game.heal_kills >= 30:
      game.heal_kills = 0
      if game.hearts < MAX_HEARTS:
        game.hearts += 1
        game.toast("+1 HEART!")
  if has_ult(game) and not game.__dict__.get('ult_fx'):
    game.ult = min(ULT_NEED, getattr(game, 'ult', 0) + 1)


def ultimate(game):
  """unleash it: every foe on screen is destroyed, shots are wiped away and a boss takes a big hit"""
  if not has_ult(game) or getattr(game, 'ult', 0) < ULT_NEED or game.state != "PLAYING":
    return False
  game.ult = 0
  st_ = game.data.setdefault('stats', {})
  st_['ults'] = st_.get('ults', 0) + 1
  col = ULT_COL.get(game.selected, (255, 255, 255))
  game.ult_fx = {'t': 0, 'name': ULT_NAME.get(game.selected, "ULTIMATE"), 'col': col, 'k': game.selected, 'seed': random.randint(1, 9999)}
  for name in GROUND_LISTS + ('enemies',):
    for o in getattr(game, name):
      r = o['rect']
      if o.get('shattered') or r.right < 0 or r.left > WIDTH:
        continue
      o['shattered'] = True
      if name == 'towers':
        o['state'] = 'blown'
      game.score += int(25 * game.score_mult)
      game.dp += 8
      game.bounty_add('shatter')
      game.burst(r.centerx, r.centery, 20, 7, 5, 12, col)
  for lst in (game.fireballs, game.arrows, game.orbs):
    for p in lst:
      if -20 < p['x'] < WIDTH + 20:
        p['shattered'] = True
  b = game.boss_live()
  if b:
    b['hp'] -= b['max_hp'] * 0.12 * game.boss_mult(b)
    b['flash'] = 10
  game.shake_for(16, 26)
  AUDIO.play('roar')
  AUDIO.play('shatter', 1.0)
  return True


def update(game):
  fx = getattr(game, 'ult_fx', None)
  if fx:
    fx['t'] += 1
    if fx['t'] > UFX.LIFE:
      game.ult_fx = None


def draw(gs, game, fonts, panel_fn, colors, ult_btn):
  """the ULT button (and its charge ring) and the flash when it goes off"""
  small, big = fonts
  PANEL_DARK, GOLD_BORDER, PARCHMENT = colors
  fx = getattr(game, 'ult_fx', None)
  if fx:
    t = fx['t']
    UFX.draw(gs, game, fx)                          # the Ultimate's own animation across the screen
    if t < 14:
      v = int((14 - t) * 12)
      c = fx['col']
      gs.fill((min(255, c[0] * v // 255), min(255, c[1] * v // 255), min(255, c[2] * v // 255)), special_flags=pygame.BLEND_RGB_ADD)
    if t < 60:
      img = big.render(fx['name'] + "!", True, fx['col'])
      sc = 1.0 + max(0.0, (10 - t) / 10.0) * 0.6
      img = pygame.transform.scale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
      img.set_alpha(255 if t < 45 else int(255 * (60 - t) / 15.0))
      gs.blit(img, img.get_rect(center=(gs.get_width() // 2, 230)))
  if not has_ult(game) or game.state not in ("PLAYING", "PAUSED"):
    return
  ch = getattr(game, 'ult', 0) / float(ULT_NEED)
  ready = ch >= 1.0
  col = ULT_COL.get(game.selected, (255, 255, 255))
  panel_fn(gs, ult_btn, (50, 20, 50) if ready else (30, 30, 34), 235, col if ready else (90, 90, 96), 3, 12)
  if ready:
    add_glow(gs, ult_btn.centerx, ult_btn.centery, 60 + int(math.sin(pygame.time.get_ticks() / 120.0) * 8), (col[0] // 4, col[1] // 4, col[2] // 4))
  lab = small.render("ULTIMATE!" if ready else "ULT %d%%" % int(ch * 100), True, PARCHMENT if ready else (170, 170, 176))
  gs.blit(lab, lab.get_rect(center=ult_btn.center))
  if not ready:
    pygame.draw.rect(gs, col, (ult_btn.x + 8, ult_btn.bottom - 9, int((ult_btn.w - 16) * ch), 4), border_radius=2)
