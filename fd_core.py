"""
Flappy Dragon  --  optimised + visual refresh

Performance notes
  * Backgrounds (sky, stars, moon, mountains, hills, clouds, mist, ground) are pre-rendered once.
  * Towers, scenery, enemy dragons, siege engines, coins, shields, ice/acid overlays are cached sprites.
  * Text and panels are cached; glows are additive-blended cached sprites.
  * Particle count is capped and updated with a single pass (no list.remove in loops).
  * Off-screen scenery is now removed (the old version leaked it forever).
  * One central event loop instead of a pygame.event.get() per screen.
"""
import pygame
import random
import sys
import math
import json
import os

pygame.init()

def _wide_width():
  w = h = 0
  try:
    w, h = pygame.display.get_desktop_sizes()[0]
  except Exception:
    pass
  if not (w and h):
    try:
      info = pygame.display.Info()
      w, h = info.current_w, info.current_h
    except Exception:
      w = h = 0
  a = max(w, h) / float(min(w, h)) if (w and h) else 4 / 3.0   # the game is played sideways, so measure the screen in landscape even if it reports portrait
  if a < 1.34:
    a = 4 / 3.0
  return max(800, min(1600, int(round(600 * a / 8.0)) * 8))

WIDTH, HEIGHT = _wide_width(), 600
XO = (WIDTH - 800) // 2
BOSS_X = min(WIDTH - 200, 560)
FPS = 60
INTRO_FRAMES = 280
INTRO_FADE = 255
BASE_GRAVITY = 0.48
FLAP_STRENGTH = -8.5
GLIDE_DELAY = 9
GLIDE_UP = 8.0
GLIDE_DOWN = 10.5
GLIDE_SINK = 0.8
FLIP_FRAMES = 26
BASE_SCROLL = 5
TOWER_WIDTH = 95
FIREBALL_GRAVITY = 0.18
GROUND_H = 32
GROUND_Y = HEIGHT - GROUND_H
MAX_PARTICLES = 260

DUSK_TOP = (4, 6, 14)
DUSK_BOTTOM = (45, 25, 40)
MOON_LIGHT = (255, 254, 240)
MOON_SHADOW = (220, 215, 195)
STAR_WHITE = (255, 255, 255)
MOUNTAIN_FAR = (18, 20, 32)
MOUNTAIN_NEAR = (28, 30, 45)
HILL_MID = (35, 65, 35)
HILL_MID_LIGHT = (45, 80, 40)
HILL_FG = (25, 50, 25)

GOLD_BORDER = (218, 165, 32)
IRON_GRAY = (45, 48, 52)
STONE_WALL = (95, 100, 105)
STONE_DARK = (55, 58, 62)
STONE_LIGHT = (130, 135, 142)
IVY_GREEN = (34, 110, 45)
BANNER_GOLD = (230, 175, 20)
BANNER_BLUE = (25, 75, 160)
WOOD_BROWN = (100, 58, 24)
WOOD_DARK = (45, 25, 10)
FIRE_CORE = (255, 245, 180)
LEAF_GREEN = (25, 115, 25)
PINE_GREEN = (15, 75, 30)
TERRA_BROWN = (40, 28, 18)
PARCHMENT = (235, 225, 205)
BONE_WHITE = (240, 240, 235)
ICE_BLUE = (150, 230, 255)
SKIN_COLOR = (240, 190, 160)
CLOTH_RED = (180, 40, 40)
CLOTH_BLUE = (40, 60, 150)
CLOTH_DARK = (30, 35, 40)
MAGIC_PURPLE = (180, 50, 255)
PANEL_DARK = (16, 17, 24)

DRAGON_PALETTES = {
  "RED": {'main': (62, 48, 54), 'dark': (26, 18, 22), 'belly': (255, 150, 40), 'eye': (255, 235, 70), 'trail': [(255, 120, 20), (60, 50, 55)], 'cost': 0, 'title': "Magma Dragon", 'desc': "Molten breath leaves burning ground. Immune to fire!"},
  "BLUE": {'main': (122, 212, 236), 'dark': (40, 100, 150), 'belly': (222, 250, 255), 'eye': (255, 110, 200), 'trail': [(150, 226, 246), (235, 252, 255)], 'cost': 150, 'title': "Arctic Dragon", 'desc': "Freezes foes solid. Frozen foes shatter!"},
  "GREEN": {'main': (38, 198, 152), 'dark': (18, 92, 96), 'belly': (255, 216, 72), 'eye': (255, 70, 50), 'trail': [(176, 240, 70), (255, 170, 50)], 'cost': 300, 'title': "Acid Dragon", 'desc': "Acid globs burn the ground and shatter foes."},
  "CHRONO": {'main': (25, 105, 125), 'dark': (10, 42, 62), 'belly': (240, 210, 110), 'eye': (255, 235, 130), 'trail': [(120, 230, 255), (240, 210, 110)], 'cost': 600, 'title': "Chrono Wyrm", 'desc': "Breath slows time and freezes foes."},
  "YELLOW": {'main': (248, 204, 52), 'dark': (150, 96, 24), 'belly': (255, 246, 200), 'eye': (70, 200, 255), 'trail': [(120, 220, 255), (255, 236, 90)], 'cost': 450, 'title': "Lightning Dragon", 'desc': "Chain lightning leaps foe to foe and crumbles towers."},
  "SILVER": {'main': (150, 138, 168), 'dark': (58, 50, 78), 'belly': (236, 226, 212), 'eye': (255, 216, 60), 'trail': [(200, 236, 255), (255, 255, 255)], 'cost': 750, 'title': "Wind Dragon", 'desc': "Breathes tornados that fling foes far away."},
  "CHINESE": {'main': (200, 30, 40), 'dark': (140, 20, 20), 'belly': (240, 200, 50), 'eye': (0, 255, 150), 'trail': [(255, 230, 120), (255, 255, 255)], 'cost': 5000, 'title': "Lung Dragon", 'desc': "Blasts a roaring Tidal Jet of water that washes foes away and trails crackling sparks. +50% gold from coins."},
  "SKELETAL": {'main': (220, 205, 170), 'dark': (90, 20, 24), 'belly': (160, 150, 120), 'eye': (255, 40, 40), 'trail': [(180, 120, 240), (70, 64, 70)], 'cost': 5000, 'title': "Bone Reaper", 'desc': "Grave Curse fog: cursed foes burst into bones and rise as wisps that hunt the rest. Shields regrow on their own."},
  "COSMIC": {'main': (40, 22, 72), 'dark': (14, 8, 30), 'belly': (190, 70, 240), 'eye': (255, 150, 255), 'trail': [(230, 200, 255), (255, 255, 255)], 'cost': 6500, 'title': "Void Dragon", 'desc': "Opens a black hole that swallows foes and their shots. Leaves a trail of stars."},
  "UNICORN": {'main': (52, 34, 60), 'dark': (22, 12, 28), 'belly': (190, 30, 90), 'eye': (255, 60, 80), 'trail': [(255, 80, 160), (150, 90, 255)], 'cost': 8000, 'title': "Evil Unicorn", 'desc': "Rainbow beam blasts everything in a line, right off the screen. Gallops on the ground unharmed."},
  "WRAITH": {'main': (120, 230, 240), 'dark': (30, 60, 90), 'belly': (220, 255, 255), 'eye': (180, 255, 255), 'trail': [(150, 245, 255), (60, 120, 160)], 'cost': 7000, 'title': "Wraith Wyrm", 'desc': "Soul Siphon drains foes one by one. Each drained soul rises as a wisp that hunts the nearest foe."},
  "CLOCKWORK": {'main': (176, 140, 70), 'dark': (70, 50, 26), 'belly': (230, 200, 120), 'eye': (255, 90, 40), 'trail': [(200, 200, 200), (150, 150, 150)], 'cost': 7500, 'title': "Clockwork Dragon", 'desc': "Launches homing brass missiles that seek out foes and blow up on impact. Puffs steam as it flies."},
  "FOREST": {'main': (90, 120, 40), 'dark': (40, 56, 20), 'belly': (190, 170, 90), 'eye': (255, 220, 60), 'trail': [(120, 190, 50), (200, 170, 60)], 'cost': 600, 'title': "Forest Dragon", 'desc': "Razor Leaf Storm: a whirling stream of blade-sharp leaves that slices through everything ahead. Leaves a trail of falling leaves."},
  "COCKATRICE": {'main': (190, 110, 40), 'dark': (70, 60, 24), 'belly': (230, 170, 80), 'eye': (255, 230, 80), 'trail': [(200, 60, 40), (120, 140, 50)], 'cost': 6500, 'title': "Cockatrice", 'desc': "Pelts foes with a steady stream of eggs. Each egg that hits cracks open and a tiny cockatrice flies out to attack the nearest foe."},
  "ALIEN": {'main': (40, 120, 50), 'dark': (14, 40, 20), 'belly': (130, 255, 90), 'eye': (130, 255, 90), 'trail': [(130, 255, 90), (60, 200, 60)], 'cost': 900, 'title': "Alien Dragon", 'desc': "A dragon from beyond the stars. Sprays acid that melts foes and leaves bubbling pools on the ground."},
  "EAGLE": {'main': (190, 140, 50), 'dark': (90, 60, 20), 'belly': (240, 210, 140), 'eye': (255, 220, 80), 'trail': [(250, 230, 180), (220, 180, 90)], 'cost': 1200, 'title': "Giant Eagle", 'desc': "Talon Strike: each tap dives at the nearest foe, anywhere on screen, and destroys it. Takes no damage while it strikes."},
  "WHALE": {'main': (70, 50, 150), 'dark': (30, 18, 70), 'belly': (210, 220, 255), 'eye': (255, 255, 255), 'trail': [(200, 180, 255), (255, 255, 255)], 'cost': 8500, 'title': "Cosmic Whale", 'desc': "Cosmic Maw: opens its starry jaws and drags foes and their shots into a swirling vortex, swallowing them whole."},
  "FEY": {'main': (60, 150, 230), 'dark': (60, 30, 110), 'belly': (240, 120, 220), 'eye': (120, 255, 255), 'trail': [(255, 150, 240), (140, 240, 255)], 'cost': 7500, 'title': "Fey Dragon", 'desc': "Glamour Nova: bursts of fey magic ripple outward and turn every foe they touch into a flutter of butterflies."},
}

BREATH_COLORS = {
  "RED": [(255, 236, 110), (255, 176, 44), (255, 96, 20), (70, 40, 34)],
  "BLUE": [(200, 240, 255), (150, 200, 255), (255, 255, 255)],
  "SILVER": [(220, 220, 220), (200, 200, 200), (255, 255, 255)],
  "GREEN": [(100, 255, 50), (50, 200, 20), (150, 255, 100)],
  "ALIEN": [(130, 255, 90), (60, 220, 60), (180, 255, 140)],
  "EAGLE": [(250, 230, 180), (220, 180, 90), (255, 255, 255)],
  "SKELETAL": [(40, 40, 40), (10, 255, 10), (100, 0, 255)],
  "CHRONO": [(255, 225, 120), (120, 230, 255), (255, 255, 255)],
  "COSMIC": [(230, 200, 255), (190, 90, 255), (255, 255, 255)],
  "UNICORN": [(255, 70, 70), (255, 170, 40), (255, 240, 70), (80, 230, 90), (70, 170, 255), (170, 90, 255)],
}
DEFAULT_BREATH = [FIRE_CORE, (255, 160, 20), (255, 70, 0), (80, 80, 85)]
BREATH_BAR = {"ALIEN": (120, 255, 80), "EAGLE": (255, 210, 110), "WHALE": (190, 160, 255), "FEY": (255, 140, 240), "COCKATRICE": (255, 200, 90), "FOREST": (130, 210, 60), "CLOCKWORK": (240, 190, 90), "CHINESE": (90, 200, 255), "WRAITH": (120, 240, 255), "UNICORN": (255, 120, 220), "COSMIC": (200, 120, 255), "RED": (255, 110, 20), "BLUE": ICE_BLUE, "YELLOW": (255, 220, 0), "SILVER": (200, 200, 200), "GREEN": (100, 255, 50), "SKELETAL": (190, 110, 255), "CHRONO": (120, 230, 255)}
BREATH_GLOW = {"ALIEN": (24, 90, 24), "EAGLE": (100, 70, 20), "WHALE": (50, 30, 110), "FEY": (100, 40, 110), "COCKATRICE": (90, 50, 14), "FOREST": (30, 70, 16), "CLOCKWORK": (110, 70, 20), "CHINESE": (20, 70, 120), "WRAITH": (20, 90, 110), "UNICORN": (110, 40, 110), "COSMIC": (80, 30, 120), "RED": (140, 55, 6), "BLUE": (30, 80, 130), "YELLOW": (110, 100, 20), "SILVER": (70, 70, 80), "GREEN": (30, 100, 20), "SKELETAL": (60, 24, 90), "CHRONO": (20, 80, 100)}
DEFAULT_GLOW = (120, 50, 5)
RAINBOW = ((255, 64, 64), (255, 150, 40), (255, 236, 70), (70, 222, 96), (60, 170, 255), (110, 90, 255), (200, 90, 255))
PHX_BEAK = (-63, -33)     # phoenix beak from its body centre at 3x (strike frames)
MAX_HEARTS = 5
LEAF = {'every': 2, 'max': 44, 'life': 48, 'pierce': 2, 'heavy': 6}   # Forest Dragon's razor leaves
MAW = {'range': 360, 'cone': 0.55, 'gulp': 30, 'heavy': 34, 'pull': 9.0}   # Cosmic Whale's Cosmic Maw: reach, cone spread, swallow distance, frames to tear apart big foes
NOVA = {'r': 300, 'grow': 11.0, 'band': 34, 'chips': 2, 'boss': 22.0, 'flies': 4, 'fly_life': 110}   # Fey Dragon's Glamour Nova rings and butterflies
EGG_SHOT = {'every': 6, 'max': 10, 'chicks': 8, 'chick_life': 200, 'pecks': 2}   # Cockatrice eggs and hatchlings
VINE = {'every': 11, 'reach': 330, 'grow': 8, 'hold': 10, 'max': 4}   # Forest Dragon's bramble vines
MISSILE = {'every': 9, 'max': 8, 'speed': 11.0, 'turn': 0.13, 'life': 120, 'blast': 48}   # Clockwork Dragon's homing missiles
SIPHON = {'range': 560, 'time': 16, 'heavy': 42, 'refill': 10, 'souls': 6, 'soul_life': 170}   # Wraith Wyrm's Soul Siphon
NIGHT_SCALE = {'moth': 1.5, 'bat': 1.35}       # giant moth / bat art size
NIGHT_BOX = {'moth': (66, 60), 'bat': (54, 46)}  # their hitboxes
UNI_HOOF = 38             # Evil Unicorn: hooves sit this far below its hitbox, so it can gallop along the ground
BREATH_MOUTH = {'ALIEN': (-6, -4), 'EAGLE': (0, 0), 'WHALE': (-14, 16), 'FEY': (-6, 0), 'COCKATRICE': (-3, -10), 'SILVER': (7, -10), 'GREEN': (-17, 6), 'YELLOW': (-10, -2), 'FOREST': (20, 6), 'CHINESE': (0, 3), 'CLOCKWORK': (-5, 10), 'WRAITH': (7, 0), 'RED': (5, 6), 'BLUE': (3, 18), 'UNICORN': (24, 9)}   # mouth / horn tip offset from the usual breath point
BREATH_STATE = {"BLUE": "frozen", "YELLOW": "stunned", "SILVER": "blown", "CHRONO": "stasis"}
STASIS_FRAMES = 220
CHAIN_JUMPS = 3          # lightning jumps after the first hit
CHAIN_RANGE = 190        # how close the next foe must be for the lightning to jump
TORNADO_EVERY = 38       # frames between tornados while the Wind Dragon breathes
TORNADO_SPEED = 7.5
SHATTER_TINT = {"ALIEN": (140, 255, 80), "EAGLE": (240, 210, 140), "CHINESE": (150, 220, 255), "BLUE": (190, 235, 255), "GREEN": (110, 255, 60)}   # shard colour when ice / acid shatters something
WEATHER_KINDS = ["clear", "rain", "storm", "fog", "wind", "snow"]
WEATHER_WEIGHTS = [2, 3, 2, 2, 2, 2]
WEATHER_NAMES = {"rain": "Heavy Rain", "storm": "Thunderstorm", "fog": "Thick Fog", "wind": "Gale Winds", "snow": "Snowfall"}
STUCK_STATES = ("frozen", "stunned", "melted")
HOLD_STATES = ("stasis",)

ENEMY_COLORS = [((20, 85, 190), (10, 35, 110)), ((30, 140, 50), (10, 70, 20)), ((120, 30, 150), (60, 10, 90))]
UPGRADE_COSTS = [500, 1500, 3000]
BOUNTIES = [
  {"type": "collect", "target": 10, "desc": "Collect 10 Coins", "gold": 40},
  {"type": "collect", "target": 20, "desc": "Collect 20 Coins", "gold": 90},
  {"type": "collect", "target": 35, "desc": "Collect 35 Coins", "gold": 190},
  {"type": "shatter", "target": 5, "desc": "Shatter 5 Defenses", "gold": 50},
  {"type": "shatter", "target": 8, "desc": "Shatter 8 Defenses", "gold": 100},
  {"type": "shatter", "target": 15, "desc": "Shatter 15 Defenses", "gold": 230},
  {"type": "dodge", "target": 3, "desc": "Dodge 3 Fireballs", "gold": 40},
  {"type": "dodge", "target": 5, "desc": "Dodge 5 Fireballs", "gold": 90},
  {"type": "dodge", "target": 10, "desc": "Dodge 10 Fireballs", "gold": 210},
  # hunting quests (count across runs)
  {"type": "kill", "foe": "harpy", "target": 8, "desc": "Defeat 8 Harpies", "gold": 110},
  {"type": "kill", "foe": "garg", "target": 5, "desc": "Smash 5 Gargoyles", "gold": 120},
  {"type": "kill", "foe": "imp", "target": 15, "desc": "Swat 15 Imps", "gold": 120},
  {"type": "kill", "foe": "eye", "target": 12, "desc": "Pop 12 Floating Eyes", "gold": 100},
  {"type": "kill", "foe": "spider", "target": 10, "desc": "Squash 10 Undead Spiders", "gold": 140},
  {"type": "kill", "foe": "witch", "target": 3, "desc": "Defeat 3 Witches", "gold": 150},
  {"type": "kill", "foe": "moth", "target": 3, "desc": "Swat 3 Giant Moths", "gold": 150},
  {"type": "kill", "foe": "bat", "target": 6, "desc": "Drive off 6 Giant Bats", "gold": 140},
  {"type": "kill", "foe": "archer", "target": 6, "desc": "Defeat 6 Satyr Archers", "gold": 120},
  {"type": "kill", "foe": "pyro", "target": 3, "desc": "Douse 3 Pyromancers", "gold": 110},
  {"type": "kill", "foe": "wiz", "target": 3, "desc": "Defeat 3 Wizards", "gold": 110},
  {"type": "kill", "foe": "skel", "target": 3, "desc": "Lay 3 Skeleton Mages to Rest", "gold": 120},
  {"type": "kill", "foe": "golem", "target": 2, "desc": "Topple 2 Rock Golems", "gold": 160},
  {"type": "kill", "foe": "cyclops", "target": 2, "desc": "Defeat 2 Cyclopes", "gold": 170},
  {"type": "kill", "foe": "tower", "target": 6, "desc": "Bring Down 6 Towers", "gold": 130},
  {"type": "kill", "foe": "catapult", "target": 4, "desc": "Wreck 4 Catapults", "gold": 110},
  {"type": "kill", "foe": "trebuchet", "target": 3, "desc": "Wreck 3 Trebuchets", "gold": 120},
  {"type": "kill", "foe": "ballista", "target": 3, "desc": "Break 3 Ballistas", "gold": 120},
  {"type": "kill", "target": 40, "desc": "Defeat 40 Foes", "gold": 200},
  # bosses
  {"type": "boss", "foe": "griffin", "target": 1, "desc": "Defeat the Griffin", "gold": 250},
  {"type": "boss", "foe": "phoenix", "target": 1, "desc": "Defeat the Phoenix", "gold": 400},
  {"type": "boss", "foe": "beholder", "target": 1, "desc": "Blind the Beholder", "gold": 450},
  {"type": "boss", "foe": "jabber", "target": 1, "desc": "Slay the Jabberwock", "gold": 500},
  {"type": "boss", "foe": "hydra", "target": 1, "desc": "Slay the Hydra", "gold": 800},
  {"type": "boss", "foe": "demon", "target": 1, "desc": "Defeat the Fire Demon", "gold": 600},
  # one-run feats (best single run counts)
  {"type": "distance", "target": 1500, "desc": "Fly 1,500 m in One Run", "gold": 120},
  {"type": "distance", "target": 4000, "desc": "Fly 4,000 m in One Run", "gold": 300},
  {"type": "score", "target": 2000, "desc": "Score 2,000 in One Run", "gold": 150},
  {"type": "score", "target": 6000, "desc": "Score 6,000 in One Run", "gold": 400},
  {"type": "power", "target": 4, "desc": "Grab 4 Power-ups", "gold": 80},
  {"type": "egg", "target": 1, "desc": "Find a Dragon Egg", "gold": 200},
  # dragon quests (only offered once you own that dragon)
  {"type": "kill", "dragon": "RED", "target": 25, "desc": "Defeat 25 Foes as the Magma Dragon", "gold": 160},
  {"type": "kill", "dragon": "BLUE", "target": 25, "desc": "Defeat 25 Foes as the Arctic Dragon", "gold": 160},
  {"type": "kill", "dragon": "GREEN", "target": 25, "desc": "Defeat 25 Foes as the Acid Dragon", "gold": 160},
  {"type": "kill", "dragon": "ALIEN", "target": 25, "desc": "Melt 25 Foes as the Alien Dragon", "gold": 170},
  {"type": "kill", "dragon": "EAGLE", "target": 25, "desc": "Strike Down 25 Foes as the Giant Eagle", "gold": 180},
  {"type": "kill", "dragon": "YELLOW", "target": 25, "desc": "Defeat 25 Foes as the Lightning Dragon", "gold": 160},
  {"type": "kill", "dragon": "SILVER", "target": 25, "desc": "Defeat 25 Foes as the Wind Dragon", "gold": 160},
  {"type": "kill", "dragon": "CHINESE", "target": 30, "desc": "Wash Away 30 Foes as the Lung Dragon", "gold": 200},
  {"type": "kill", "dragon": "SKELETAL", "target": 30, "desc": "Curse 30 Foes as the Bone Reaper", "gold": 200},
  {"type": "kill", "dragon": "COSMIC", "target": 30, "desc": "Swallow 30 Foes as the Void Dragon", "gold": 200},
  {"type": "kill", "dragon": "UNICORN", "target": 30, "desc": "Blast 30 Foes as the Evil Unicorn", "gold": 200},
  {"type": "kill", "dragon": "WRAITH", "target": 30, "desc": "Drain 30 Souls as the Wraith Wyrm", "gold": 200},
  {"type": "kill", "dragon": "FOREST", "target": 30, "desc": "Slice 30 Foes as the Forest Dragon", "gold": 200},
  {"type": "kill", "dragon": "COCKATRICE", "target": 30, "desc": "Defeat 30 Foes as the Cockatrice", "gold": 200},
  {"type": "kill", "dragon": "CLOCKWORK", "target": 30, "desc": "Blow Up 30 Foes as the Clockwork Dragon", "gold": 200},
  {"type": "kill", "dragon": "WHALE", "target": 30, "desc": "Swallow 30 Foes as the Cosmic Whale", "gold": 200},
  {"type": "kill", "dragon": "FEY", "target": 30, "desc": "Turn 30 Foes into Butterflies as the Fey Dragon", "gold": 200},
]
QUEST_GOLD_PER = {"collect": 4, "shatter": 12, "dodge": 18}


def quest_gold(q):
  return int(q.get("gold") or QUEST_GOLD_PER.get(q.get("type"), 10) * q.get("target", 5))


screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Flappy Dragon")
game_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
clock = pygame.time.Clock()

title_font = pygame.font.SysFont("serif", 80, bold=True)
hud_font = pygame.font.SysFont("serif", 38, bold=True)
button_font = pygame.font.SysFont("serif", 28, bold=True)
small_font = pygame.font.SysFont("serif", 20, bold=True)
tiny_font = pygame.font.SysFont("serif", 16, bold=True)

SAVE_FILE = "dragon_save_v6.json"

def load_data():
  default = {
    "high_score": 0, "coins": 0, "unlocked": ["RED"],
    "upgrades": {"thick_scales": 0, "deep_lungs": 0, "coin_magnet": 0},
    "completed_quests": 0, "active_quest": None,
    "music": True, "sfx": True, "music_vol": 100, "sfx_vol": 100, "fullscreen": True, "weather": True, "difficulty": "easy", "shake": True, "vibrate": True, "eggs": [], "roosts": [None], "egg_id": 0, "hatched": 0, "babies": [], "companion": None,
  }
  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r") as f:
        data = json.load(f)
      for k, v in default.items():
        data.setdefault(k, v)
      for k, v in default["upgrades"].items():
        data["upgrades"].setdefault(k, v)
      if "VOID" in data["unlocked"]:           # Abyssal dragon became the Chrono Wyrm
        data["unlocked"] = ["CHRONO" if u == "VOID" else u for u in data["unlocked"]]
      return _test_grant(data)
    except (OSError, ValueError):
      pass
  return _test_grant(default)

TOWER_GARRISON = 0.35              # chance an open-topped tower has an archer or mage on it
CURSE = {'time': 40, 'heavy': 85, 'spread': 70, 'wisps': 8, 'wisp_life': 150}   # Bone Reaper: frames until a cursed foe bursts
VOID_HOLE = {'r': 34, 'pull': 270, 'life': 1200, 'close': 36}   # Void dragon black hole: core radius, pull range, max open frames
BOSS_SCORES = (1500, 4500, 9000, 14000, 20000, 27000)   # score needed to meet the Griffin, Phoenix, Beholder, Jabberwock, Demon and Hydra
TEST_GOLD = 50000          # one-time testing gift for this release (set to 0 to turn off)
TEST_PACK = True           # one-time testing gift: 1 egg of every rarity + one baby of every dragon (False to turn off)
TEST_BABIES = (('RED', 'common'), ('BLUE', 'common'), ('GREEN', 'common'), ('FOREST', 'uncommon'),
               ('YELLOW', 'rare'), ('SILVER', 'rare'), ('CLOCKWORK', 'rare'), ('CHINESE', 'epic'), ('WRAITH', 'epic'),
               ('SKELETAL', 'legendary'), ('COSMIC', 'legendary'), ('UNICORN', 'legendary'), ('COCKATRICE', 'epic'), ('WHALE', 'legendary'), ('FEY', 'epic'), ('ALIEN', 'uncommon'), ('EAGLE', 'rare'))
TEST_PACK_ID = 5           # bump to hand the testing gift out again (new babies were added)

def _test_grant(data):
  if TEST_GOLD and not data.get("test_gold_given"):
    data["coins"] = data.get("coins", 0) + TEST_GOLD
    data["test_gold_given"] = True
  if TEST_PACK and data.get("test_pack_given") != TEST_PACK_ID:
    import time as _t, random as _r
    for rar in ('common', 'uncommon', 'rare', 'epic', 'legendary'):
      data["egg_id"] = data.get("egg_id", 0) + 1
      data.setdefault("eggs", []).append({"id": data["egg_id"], "r": rar, "boss": "gift"})
    for typ, rar in TEST_BABIES:
      data["egg_id"] = data.get("egg_id", 0) + 1
      data.setdefault("babies", []).append({"id": data["egg_id"], "r": rar, "type": typ, "name": _r.choice(BABY_NAMES),
                                            "born": _t.time(), "happy": 80.0})
    if data.get("companion") is None and data["babies"]:
      data["companion"] = data["babies"][0]["id"]
    data["test_pack_given"] = TEST_PACK_ID
  return data

def save_data(data):
  try:
    with open(SAVE_FILE, "w") as f:
      json.dump(data, f)
  except OSError:
    pass

_text_cache, _glow_cache, _panel_cache, SPRITE_CACHE, _dim_cache = {}, {}, {}, {}, {}

def text(font, s, color):
  key = (id(font), s, color)
  img = _text_cache.get(key)
  if img is None:
    if len(_text_cache) > 500:
      _text_cache.clear()
    img = _text_cache[key] = font.render(s, True, color)
  return img

def blit_text(surf, font, s, color, pos, anchor="topleft", shadow=True):
  img = text(font, s, color)
  r = img.get_rect(**{anchor: pos})
  if shadow:
    surf.blit(text(font, s, (0, 0, 0)), r.move(2, 2))
  surf.blit(img, r)
  return r

def glow(radius, color):
  """Black-background radial glow, meant for BLEND_RGB_ADD."""
  key = (radius, color)
  g = _glow_cache.get(key)
  if g is None:
    g = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -2):
      k = (1 - r / radius) ** 2
      pygame.draw.circle(g, (int(color[0] * k), int(color[1] * k), int(color[2] * k)), (radius, radius), r)
    _glow_cache[key] = g.convert()
    g = _glow_cache[key]
  return g

def add_glow(surf, cx, cy, radius, color):
  surf.blit(glow(radius, color), (cx - radius, cy - radius), special_flags=pygame.BLEND_RGB_ADD)

def lighten(c, n):
  return tuple(min(255, v + n) for v in c)

UI = {'stone': False, 'stone_fn': None, 'press': None}   # menu look: stone panels on menu screens, last button press


def panel(surf, rect, fill=PANEL_DARK, alpha=215, border=GOLD_BORDER, bw=3, radius=10):
  if UI['stone'] and UI['stone_fn'] is not None and UI['stone_fn'](surf, rect, fill, alpha, border, bw, radius):
    return
  key = (rect.w, rect.h, fill, alpha, border, bw, radius)
  s = _panel_cache.get(key)
  if s is None:
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*fill, alpha), s.get_rect(), border_radius=radius)
    sheen = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(sheen, (255, 255, 255, 16), (bw + 1, bw + 1, rect.w - 2 * bw - 2, max(2, rect.h // 2 - bw)), border_radius=max(2, radius - 2))
    s.blit(sheen, (0, 0))
    if bw:
      pygame.draw.rect(s, border, s.get_rect(), bw, border_radius=radius)
    s = s.convert_alpha()
    _panel_cache[key] = s
  surf.blit(s, rect.topleft)

_banner_cache = {}

def banner_surface(w, h, hover=False):
  """Royal banner button: crimson scale-pattern cloth in a wood frame with gold trim and sword-pommel end caps.
  The returned surface is 24px wider than the button (12px cap on each side)."""
  key = (w, h, hover)
  s = _banner_cache.get(key)
  if s is not None:
    return s
  s = pygame.Surface((w + 24, h), pygame.SRCALPHA)
  ox = 12
  base = (160, 38, 30) if hover else (120, 26, 24)
  gold = lighten(GOLD_BORDER, 40) if hover else GOLD_BORDER
  dgold = tuple(int(v * 0.6) for v in gold)
  pygame.draw.rect(s, (66, 38, 18), (ox, 0, w, h), border_radius=6)
  for y in range(3, h - 3, 3):
    pygame.draw.line(s, (78, 46, 22) if (y // 3) % 2 else (58, 32, 14), (ox + 3, y), (ox + w - 4, y))
  for y in range(5, h - 5):
    t = (y - 5) / float(max(1, h - 11))
    col = tuple(min(255, int(base[k] * (1.25 - 0.5 * t))) for k in range(3))
    pygame.draw.line(s, col, (ox + 7, y), (ox + w - 8, y))
  scl = tuple(int(v * 0.7) for v in base)
  for yy in range(9, h - 8, 6):
    for xx in range(ox + 12 + ((yy // 6) % 2) * 4, ox + w - 12, 8):
      pygame.draw.arc(s, scl, (xx - 4, yy - 4, 9, 9), math.pi + 0.35, 2 * math.pi - 0.35, 1)
  pygame.draw.rect(s, gold, (ox + 5, 4, w - 10, h - 8), 2, border_radius=4)
  pygame.draw.rect(s, tuple(int(v * 0.4) for v in gold), (ox, 0, w, h), 2, border_radius=6)
  cy = h // 2
  for cx, dr in ((ox - 2, -1), (ox + w + 1, 1)):
    pygame.draw.polygon(s, dgold, [(cx - dr * 4, cy - h // 2 + 4), (cx + dr * 9, cy), (cx - dr * 4, cy + h // 2 - 4)])
    pygame.draw.polygon(s, gold, [(cx - dr * 3, cy - h // 2 + 7), (cx + dr * 7, cy), (cx - dr * 3, cy + h // 2 - 7)])
    pygame.draw.circle(s, (255, 236, 150), (cx + dr * 6, cy), 3)
  if hover:
    sheen = pygame.Surface((w - 16, max(2, h // 2 - 6)), pygame.SRCALPHA)
    sheen.fill((255, 200, 120, 40))
    s.blit(sheen, (ox + 8, 6))
  s = _banner_cache[key] = s.convert_alpha()
  return s

_sheen_cache = {}


def _sheen(h):
  s = _sheen_cache.get(h)
  if s is None:
    s = pygame.Surface((26, h), pygame.SRCALPHA)
    for x in range(26):
      a = int(70 * (1 - abs(x - 13) / 13.0))
      pygame.draw.line(s, (255, 240, 200, a), (x, 0), (x, h))
    s = _sheen_cache[h] = s.convert_alpha()
  return s


def draw_button(surf, rect, label, color=PARCHMENT, hover=False, bg=IRON_GRAY, border=GOLD_BORDER, font=None):
  """banner button that lifts when touched, sinks when pressed and has a light glinting across it now and then"""
  font = font or button_font
  t = pygame.time.get_ticks()
  pr = UI.get('press')
  pressed = pr is not None and rect.collidepoint(pr[0]) and 0 <= t - pr[1] < 170
  dy = 3 if pressed else (-2 if hover else 0)
  if hover and not pressed:
    add_glow(surf, rect.centerx, rect.centery, rect.w // 2 + 8, (60, 30, 6))
  surf.blit(banner_surface(rect.w, rect.h, hover or pressed), (rect.x - 12, rect.y + dy))
  ph = ((t + rect.x * 37 + rect.y * 91) % 3400) / 3400.0          # a glint sweeps across every few seconds
  if ph < 0.3 and rect.w > 40:
    prev = surf.get_clip()
    surf.set_clip(pygame.Rect(rect.x + 6, rect.y + dy + 4, rect.w - 12, rect.h - 8).clip(prev))
    gx = rect.x - 26 + int((rect.w + 52) * ph / 0.3)
    surf.blit(_sheen(rect.h), (gx, rect.y + dy))
    surf.set_clip(prev)
  if color == PARCHMENT:
    color = (255, 255, 230) if hover else (255, 236, 190)
  img = text(font, label, color)
  r = img.get_rect(center=(rect.centerx, rect.centery - 1 + dy))
  surf.blit(text(font, label, (30, 0, 0)), r.move(2, 2))
  surf.blit(img, r)

def dim(surf, alpha, rect=None):
  rect = rect or surf.get_rect()
  key = (rect.w, rect.h, alpha)
  s = _dim_cache.get(key)
  if s is None:
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    _dim_cache[key] = s = s.convert_alpha()
  surf.blit(s, rect.topleft)

KEY = (255, 0, 255)

def ck(surf):
  """Convert an opaque-with-transparent-background surface to a fast colorkey surface."""
  out = pygame.Surface(surf.get_size()).convert()
  out.fill(KEY)
  out.blit(surf, (0, 0))
  out.set_colorkey(KEY, pygame.RLEACCEL)
  return out

def cached_sprite(key, w, h, ox, oy, draw_fn):
  """Pre-render draw_fn(surface, ox, oy) into a sprite. Returns (surface, ox, oy)."""
  spr = SPRITE_CACHE.get(key)
  if spr is None:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_fn(s, ox, oy)
    spr = SPRITE_CACHE[key] = (ck(s), ox, oy)
  return spr

MENU_ITEMS = [
  ("play", "ENTER REALM", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("lair", "LAIR", BANNER_GOLD, WOOD_DARK, GOLD_BORDER),
  # ("worlds", "WORLDS", ICE_BLUE, STONE_DARK, GOLD_BORDER),   # (hidden until the Worlds page is built)
  ("options", "OPTIONS", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("exit", "ABANDON SIEGE", PARCHMENT, IRON_GRAY, GOLD_BORDER),
]
LAIR_ITEMS = [
  ("roster", "DRAGON ROSTER", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("hoard", "THE HOARD", BANNER_GOLD, WOOD_DARK, GOLD_BORDER),
  ("quests", "QUESTS", ICE_BLUE, STONE_DARK, GOLD_BORDER),
  ("enemies", "ENEMIES", PARCHMENT, IRON_GRAY, GOLD_BORDER),
  ("eggs", "DRAGON EGGS", BANNER_GOLD, WOOD_DARK, GOLD_BORDER),
  ("hatchlings", "HATCHLINGS", BANNER_GOLD, WOOD_DARK, GOLD_BORDER),
]
LAIR_RECTS = {k: pygame.Rect(max(12, WIDTH // 2 - 612) if i < 3 else min(WIDTH - 302, WIDTH // 2 + 322), 128 + (i % 3) * 107, 290, 64) for i, (k, *_r) in enumerate(LAIR_ITEMS)}   # hanging signs in the cave
SND_BTN = pygame.Rect(14, 14, 50, 40)
# roster detail page: star ratings (power, range, breath time, speed) and breath / special text
DRAGON_INFO = {
  "RED": ((4, 3, 5, 3), "Lava stream", "Burning lava pools"),
  "BLUE": ((3, 4, 3, 4), "Frost blast", "Frozen foes shatter"),
  "GREEN": ((3, 3, 3, 4), "Acid spray", "Bubbling acid pools"),
  "ALIEN": ((3, 3, 3, 4), "Acid spray", "Bubbling acid pools"),
  "EAGLE": ((5, 5, 3, 5), "Talon Strike", "Each tap dives at the nearest foe"),
  "CHRONO": ((2, 4, 3, 3), "Time wave", "Slows time for everyone"),
  "YELLOW": ((5, 5, 3, 3), "Chain lightning", "Jumps foe to foe, crumbles towers"),
  "SILVER": ((4, 4, 3, 5), "Tornado gust", "Tornados fling foes away"),
  "CHINESE": ((4, 4, 4, 5), "Tidal jet", "Washes foes away; +50% gold"),
  "CLOCKWORK": ((5, 5, 3, 3), "Homing missiles", "Missiles seek foes and explode"),
  "FOREST": ((4, 5, 3, 4), "Razor leaf storm", "Leaves slice through foes and shots"),
  "COCKATRICE": ((3, 4, 4, 4), "Egg barrage", "Hatched chicks hunt the nearest foe"),
  "SKELETAL": ((4, 4, 3, 3), "Grave Curse", "Cursed foes rise as hunting wisps; shields regrow"),
  "COSMIC": ((5, 4, 3, 4), "Singularity", "Black hole pulls in foes & shots"),
  "WRAITH": ((4, 4, 3, 4), "Soul Siphon", "Drained souls hunt the nearest foe"),
  "UNICORN": ((4, 5, 3, 4), "Rainbow beam", "Full-screen beam; runs on the ground"),
  "WHALE": ((4, 3, 4, 3), "Cosmic Maw", "Swallows foes & shots"),
  "FEY": ((4, 4, 3, 4), "Glamour Nova", "Foes turn to butterflies"),
}
# Bestiary: every enemy, (key, name, kind, description, (danger, toughness, speed), attack, weakness, appears, points)
ENEMY_INFO = [
  ("archer", "Satyr Archer", "GROUND", "Goat-legged archers that loose arrows up into the sky.", (3, 1, 2), "Arcing arrows", "Any breath", "From the start", "10"),
  ("catapult", "Catapult", "GROUND", "Winds back its arm and lobs a boulder in a high arc.", (3, 2, 1), "Lobbed boulders", "Any breath", "From the start", "10"),
  ("trebuchet", "Trebuchet", "GROUND", "A giant siege engine that flings stones far into the sky.", (4, 3, 1), "Long-range stones", "Any breath", "From the start", "10"),
  ("ballista", "Ballista", "GROUND", "Takes careful aim, then fires a heavy bolt straight at you.", (4, 2, 1), "Aimed bolts", "Any breath", "From the start", "10"),
  ("pyro", "Pyromancer", "GROUND", "A fire mage who hurls fireballs that arc toward you.", (4, 1, 2), "Fireballs", "Ice and acid", "From the start", "10"),
  ("wiz", "Wizard", "GROUND", "Casts a fan of three arcane orbs aimed right at you.", (4, 1, 2), "Triple orbs", "Any breath", "From the start", "10"),
  ("skel", "Skeleton Mage", "GROUND", "A risen sorcerer whose cursed orbs follow you through the air.", (4, 2, 2), "Homing curse orbs", "Any breath", "From the start", "10"),
  ("golem", "Rock Golem", "GROUND", "Lumbers in once the Griffin falls and hurls huge boulders.", (4, 5, 1), "Thrown boulders", "Lightning and acid", "After the Griffin", "10"),
  ("harpy", "Harpy", "FLYING", "Swooping bird-women. The fiercest flash a red ! and lunge at you.", (3, 2, 4), "Flying lunge", "Any breath, dash", "From the start", "10"),
  ("garg", "Gargoyle", "FLYING", "Stone-winged brutes that charge straight through the sky.", (3, 3, 3), "Charge", "Any breath, dash", "From the start", "10"),
  ("imp", "Imp", "FLYING", "Little devils that fly in packs of three to five.", (2, 1, 4), "Swarm", "Any breath", "From the start", "3 each"),
  ("cyclops", "Cyclops", "GROUND", "A one-eyed brute who winds up and hurls his huge wooden club at you.", (4, 4, 1), "Thrown club", "Lightning and acid", "Threat level 5", "10"),
  ("spider", "Undead Spider", "FLYING", "Poisonous skull spiders that drop from the sky in diagonal lines of three to five, trailing silk.", (2, 1, 2), "Falling swarm", "Any breath", "Threat level 3", "3 each"),
  ("witch", "Witch", "FLYING", "Hovers high above the battle and hurls bolts of green magic straight at you.", (4, 1, 2), "Magic bolts", "Any breath, dash", "Threat level 3", "10"),
  ("moth", "Giant Moth", "FLYING", "A huge, gross moth that flutters slowly in and flings spheres of purple magic that drift after you.", (3, 2, 1), "Homing magic", "Any breath, dash", "Threat level 3", "10"),
  ("bat", "Giant Bat", "FLYING", "Swoops in on a zig-zag path, drifting toward your height, and hits you with a red sonic screech.", (3, 2, 4), "Sonic screech", "Any breath, dash", "Threat level 2", "10"),
  ("eye", "Floating Eye", "FLYING", "Eyeballs that drift in groups of three to five.", (1, 1, 3), "Ramming", "Anything", "From the start", "2 each"),
  ("griffin", "Griffin", "BOSS", "King of the skies: feather volleys, wind gusts and a diving strike.", (4, 3, 4), "Feathers, gusts, dive", "Stay out of the dive", "Score 1,500", "300"),
  ("phoenix", "Phoenix", "BOSS", "Fireballs, crescent slashes, a burst of fire feathers and a burning dive. Rises once from its own ashes.", (5, 4, 5), "Fire volleys, dive", "Finish it twice!", "Score 4,500", "300"),
  ("beholder", "Beholder", "BOSS", "A floating eye tyrant. Charges its great eye to fire a death ray, and its eyestalks spit eyeballs that hunt you across the sky.", (5, 4, 3), "Death ray, seeker eyes", "Lightning and wind", "Score 9,000", "300"),
  ("jabber", "Jabberwock", "BOSS", "The jaws that bite, the claws that catch! Spits volleys of spit-balls, sweeps a burbling green beam and charges straight through the sky.", (5, 5, 4), "Spit, beam, charge", "Fire and lightning", "Score 14,000", "300"),
  ("demon", "Fire Demon", "BOSS", "Sends fire crescents from his sword, phases out to dodge and raises a red shield.", (5, 5, 3), "Fire crescents", "Hit him between shields", "Score 20,000", "300"),
  ("hydra", "Hydra", "BOSS", "A two-headed horror: one head breathes fire, the other frost. Spits bolts in turn, rains ice shards and lunges across the sky.", (5, 5, 4), "Fire & ice, lunge", "Lightning and acid", "Score 27,000", "300"),
]
ENEMY_GRID = pygame.Rect(WIDTH // 2 - 375, 100, 750, 384)
ENEMY_CARD = (236, 160, 21, 176)          # card w, h, column gap, row pitch
EN_PREV = pygame.Rect(WIDTH // 2 - 380, 508, 190, 46)
EN_BACK = pygame.Rect(WIDTH // 2 - 110, 508, 220, 46)
EN_NEXT = pygame.Rect(WIDTH // 2 + 190, 508, 190, 46)
# Dragon eggs: bosses drop them, roosts hatch them over real hours
EGG_HATCH_HOURS = {'common': 2, 'uncommon': 4, 'rare': 6, 'epic': 9, 'legendary': 12}
EGG_REWARD = {'common': 150, 'uncommon': 300, 'rare': 600, 'epic': 1200, 'legendary': 2500}
BOSS_EGG_ODDS = {'griffin': (('common', 70), ('uncommon', 30)),
                 'phoenix': (('uncommon', 35), ('rare', 50), ('epic', 15)),
                 'beholder': (('uncommon', 25), ('rare', 55), ('epic', 20)),
                 'jabber': (('rare', 45), ('epic', 40), ('legendary', 15)),
                 'demon': (('rare', 25), ('epic', 45), ('legendary', 30)),
                 'hydra': (('epic', 50), ('legendary', 50))}
BOSS_NAMES = {'gift': 'Test Pack', 'griffin': "Griffin", 'phoenix': "Phoenix", 'beholder': "Beholder", 'jabber': "Jabberwock", 'demon': "Fire Demon", 'hydra': "Hydra"}
BABY_NAMES = ('Ember', 'Pip', 'Scorch', 'Nibbles', 'Talon', 'Ash', 'Blaze', 'Fizz', 'Cinder', 'Spark', 'Mossy', 'Frost', 'Glimmer',
              'Rune', 'Sable', 'Zephyr', 'Pebble', 'Sprout', 'Nova', 'Comet', 'Smudge', 'Bramble', 'Ziggy', 'Onyx')
HATCH_TYPES = {'common': (('RED', 34), ('BLUE', 33), ('GREEN', 33)),
               'uncommon': (('RED', 20), ('BLUE', 20), ('GREEN', 20), ('FOREST', 20), ('YELLOW', 20), ('ALIEN', 15)),
               'rare': (('FOREST', 20), ('YELLOW', 20), ('SILVER', 20), ('CLOCKWORK', 15), ('COCKATRICE', 15), ('BLUE', 10), ('EAGLE', 15)),
               'epic': (('SILVER', 20), ('CLOCKWORK', 20), ('CHINESE', 15), ('WRAITH', 15), ('SKELETAL', 15), ('COCKATRICE', 15), ('FEY', 15)),
               'legendary': (('CHINESE', 20), ('SKELETAL', 20), ('COSMIC', 20), ('UNICORN', 20), ('WRAITH', 20), ('WHALE', 20))}
OLD_BABY_TYPE = {'common': 'GREEN', 'uncommon': 'BLUE', 'rare': 'CHRONO', 'epic': 'YELLOW', 'legendary': 'SKELETAL'}
PET_RARITY_POWER = {'common': 1.0, 'uncommon': 1.15, 'rare': 1.3, 'epic': 1.5, 'legendary': 1.8}
PET_FEED_COST = 40
PET_MAX_LEVEL = 10
PET_HAPPY_DECAY = 2.0          # happiness lost per real hour
# boss weak spots: damage multipliers by the player's dragon (fire resisted, ice and wind hurt more)
BOSS_RESIST = {'demon': {'RED': 0.5, 'CHINESE': 1.6, 'BLUE': 1.6, 'SILVER': 1.6},
               'phoenix': {'RED': 0.5, 'CHINESE': 1.6, 'BLUE': 1.6, 'SILVER': 1.6},
               'beholder': {'YELLOW': 1.4, 'SILVER': 1.3, 'SKELETAL': 0.6},
               'jabber': {'GREEN': 0.6, 'ALIEN': 0.6, 'FOREST': 0.7, 'RED': 1.3, 'YELLOW': 1.3},
               'hydra': {'RED': 0.6, 'BLUE': 0.6, 'YELLOW': 1.4, 'GREEN': 1.3, 'ALIEN': 1.3}}
DEN_RECT = pygame.Rect(WIDTH // 2 - 390, 170, 780, 300)   # where the hatchlings flutter about
HB_VIEW_BTN = pygame.Rect(WIDTH // 2 + 170, HEIGHT - 114, 200, 42)
HB_DETAIL_BTN = pygame.Rect(WIDTH // 2 + 2, HEIGHT - 114, 156, 42)
PET_BTNS = [pygame.Rect(WIDTH // 2 - 398 + i * 200, 508, 196, 46) for i in range(4)]
ROOST_PRICES = [600, 1500, 3000]          # 2nd, 3rd and 4th roost
MAX_ROOSTS = 4
EGG_GRID = pygame.Rect(WIDTH // 2 - 370, 112, 740, 342)
EGG_CARD = (170, 168, 20, 184)            # w, h, column gap, row pitch (4 columns)
EGG_ROOST_BTN = pygame.Rect(WIDTH - 214, HEIGHT - 110, 198, 44)
EGG_BACK_BTN = pygame.Rect(WIDTH // 2 - 360, HEIGHT - 80, 200, 45)
HEARTH_K = min(WIDTH / 1672.0, 0.806)          # scale of your hearth-room picture (it is drawn from the top of the screen)
HEARTH_OX = (WIDTH - int(1672 * HEARTH_K)) // 2
ROOST_RECTS = [pygame.Rect(HEARTH_OX + int((285 + 285 * i) * HEARTH_K), int(255 * HEARTH_K), int(250 * HEARTH_K), int(405 * HEARTH_K)) for i in range(MAX_ROOSTS)]   # the four painted hearths
HATCH_SKIP_GOLD = 100                     # gold to knock one hour off a hatching egg
def speed_rect(r):
  """the 'speed up' button inside a roost card."""
  return pygame.Rect(r.x + 14, r.top + int(r.h * 0.275), r.w - 28, 32)
def skip_cost(left):
  """(gold, seconds skipped) for one tap of speed-up."""
  if left > 3600:
    return HATCH_SKIP_GOLD, 3600.0
  return max(20, int(math.ceil(left / 3600.0 * HATCH_SKIP_GOLD))), left
INFO_K = max(WIDTH / 1870.0, HEIGHT / 841.0, 0.805)    # scale of your trophy-room picture on the detail pages
INFO_OX, INFO_OY = (WIDTH - int(1870 * INFO_K)) // 2, -int(40 * INFO_K)


def info_rect(box):
  l, t, r, b = box
  return pygame.Rect(INFO_OX + int(l * INFO_K), INFO_OY + int(t * INFO_K), int((r - l) * INFO_K), int((b - t) * INFO_K))


INFO_PORTRAIT = info_rect((354, 246, 916, 648))     # inside your gold picture frame
INFO_PANEL = info_rect((982, 246, 1516, 648))       # inside your dark stats panel
INFO_BACK = pygame.Rect(WIDTH // 2 - 290, 508, 260, 46)
INFO_SELECT = pygame.Rect(WIDTH // 2 + 30, 508, 260, 46)
OPT_KEYS = ["music", "sfx", "display", "weather", "difficulty", "shake", "vibrate"]
OPT_RECTS = {k: pygame.Rect(WIDTH // 2 - 262, 127 + i * 46, 506, 42) for i, k in enumerate(OPT_KEYS)}   # rows on the hanging parchment
OPT_SLIDERS = ("music", "sfx")              # these rows are 0-100 volume sliders


def slider_track(r):
  """(x0, x1, y) of the volume slider inside an options row."""
  return r.right - 248, r.right - 76, r.centery
MENU_RECTS = {k: (pygame.Rect(WIDTH // 2 - 200, 222, 400, 66) if k == "play" else pygame.Rect(WIDTH // 2 - 160, 302 + (i - 1) * 56, 320, 48)) for i, (k, *_r) in enumerate(MENU_ITEMS)}

SELECT_BOXES = [(k, pygame.Rect(WIDTH // 2 - 402 + (i % 4) * 202, 112 + (i // 4) * 178, 190, 172)) for i, k in enumerate(("RED", "BLUE", "GREEN", "FOREST", "YELLOW", "SILVER", "ALIEN", "EAGLE"))]   # stalls in the barn
RARE_BOXES = [(k, pygame.Rect(WIDTH // 2 - 424 + (i % 5) * 172, 112 + (i // 5) * 172, 160, 162)) for i, k in enumerate(("CHINESE", "SKELETAL", "COSMIC", "UNICORN", "WRAITH", "CLOCKWORK", "COCKATRICE", "FEY", "WHALE"))]
UPGRADES = [("thick_scales", "Thick Scales", "Max Shields +1", pygame.Rect(WIDTH // 2 - 430, 172, 240, 330)),
      ("deep_lungs", "Deep Lungs", "Breath Duration +1s", pygame.Rect(WIDTH // 2 - 120, 172, 240, 330)),
      ("coin_magnet", "Coin Magnet", "Pulls Nearby Coins", pygame.Rect(WIDTH // 2 + 190, 172, 240, 330))]   # one column per anvil


def upgrade_btn(rect):
  """the price plaque you tap to forge an upgrade (on the anvil's pedestal)"""
  return pygame.Rect(rect.centerx - 110, 459, 220, 46)

BACK_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 80, 260, 45)
REPORT_K = min(WIDTH / 1672.0, 0.75)            # scale of your war-room picture (drawn from just above the top of the screen)
REPORT_OX, REPORT_OY = (WIDTH - int(1672 * REPORT_K)) // 2, -20


def report_rect(box):
  l, t, r, b = box
  return pygame.Rect(REPORT_OX + int(l * REPORT_K), REPORT_OY + int(t * REPORT_K), int((r - l) * REPORT_K), int((b - t) * REPORT_K))


REPORT_LIST = report_rect((322, 318, 770, 655))   # scrollable foes list: the left parchment
REPORT_BACK = report_rect((622, 745, 1048, 806))  # the red button plate under the parchments
REPORT_ROW = 30
REPORT_BTN = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 + 70, 230, 44)     # on the game-over panel
OVER_MENU_BTN = pygame.Rect(WIDTH // 2 + 44, HEIGHT // 2 + 70, 156, 44)
PX_PER_M = 12.0                   # scrolled pixels per metre flown
KILL_KEY = {'towers': 'tower', 'catapults': 'catapult', 'trebuchets': 'trebuchet', 'archers': 'archer', 'ballistas': 'ballista', 'golems': 'golem', 'cyclopes': 'cyclops'}
SEL_BACK_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 55, 260, 40)
RARE_BTN = pygame.Rect(WIDTH // 2 + 170, 464, 176, 46)
PAUSE_BTN = pygame.Rect(WIDTH - 110, GROUND_Y - 46, 95, 35)
SHIELD_BTN = pygame.Rect(15, 480, 140, 50)
DASH_BTN = pygame.Rect(15, 424, 140, 50)
DASH_COOLDOWN = 600
DASH_SPEED = 30
DASH_REACH = 400
RESUME_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 - 20, 260, 45)
OPT_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 40, 260, 45)
MENU_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 100, 260, 45)
YES_BTN = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 20, 110, 45)
NO_BTN = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 20, 110, 45)
BUY_YES = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 10, 110, 45)
BUY_NO = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 10, 110, 45)

GROUND_LISTS = ('towers', 'catapults', 'trebuchets', 'archers', 'mages', 'ballistas', 'golems', 'cyclopes')
SCENERY_TYPES = ["oak", "pine", "birch", "bush", "grass", "flowers", "rock", "smith", "knight", "dwarf", "fg_hill",
                 "pgrass", "mushroom", "boulder", "vase", "crate", "bonfire", "pbush", "twig", "fence", "villager"]
SCENERY_WEIGHTS = [13, 13, 8, 16, 22, 10, 6, 5, 2, 2, 5,
                   8, 4, 4, 2, 2, 2, 4, 4, 2, 7]
