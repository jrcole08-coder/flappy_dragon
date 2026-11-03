"""Beta polish: build version, first-run tutorial, pausing when the app goes to the background,
juicier hits (combo counter, floating score, boss hit freeze + flash) and save backup codes."""
import base64
import json
import math
import zlib
import pygame

BUILD = "beta 0.3"        # shown on the main menu (the GitHub build adds its run number: "beta 0.3.14")
try:
  import fd_build                    # written by the GitHub build, so every APK knows its own number
  BUILD = fd_build.BUILD
except Exception:
  pass


# ---------------------------------------------------------------- first-run tutorial
TUTORIAL = [
  ("tap", "TAP anywhere to flap your wings and fly up"),
  ("power", "Grab a glowing crystal to charge your SPECIAL breath"),
  ("dash", "Tap DASH to charge forward through foes"),
  ("shield", "Fill the bar on the left to earn SHIELDS - tap SHIELD to use one"),
  ("hearts", "Hearts at the top right are your lives - don't let them run out!"),
]
TUT_TIME = 250            # frames each hint stays up (about 4 seconds)


def tutorial_start(game):
  if not game.data.get('tutorial_done'):
    game.tut = {'i': 0, 't': 0}
  else:
    game.tut = None


def tutorial_update(game):
  tu = getattr(game, 'tut', None)
  if not tu:
    return
  tu['t'] += 1
  if tu['t'] > TUT_TIME:
    tu['i'] += 1
    tu['t'] = 0
    if tu['i'] >= len(TUTORIAL):
      game.tut = None
      game.data['tutorial_done'] = True
      try:
        from fd_core import save_data
        save_data(game.data)
      except Exception:
        pass


def tutorial_draw(surf, game, font):
  tu = getattr(game, 'tut', None)
  if not tu:
    return
  from fd_core import WIDTH, HEIGHT, panel, PANEL_DARK, GOLD_BORDER, PARCHMENT, text
  kind, msg = TUTORIAL[tu['i']]
  fade = min(1.0, tu['t'] / 12.0, (TUT_TIME - tu['t']) / 12.0)
  if fade <= 0:
    return
  img = text(font, msg, PARCHMENT)
  r = img.get_rect(center=(WIDTH // 2, 150)).inflate(40, 22)
  panel(surf, r, PANEL_DARK, int(235 * fade), GOLD_BORDER, 3, 10)
  img.set_alpha(int(255 * fade))
  surf.blit(img, img.get_rect(center=r.center))
  hint = text(font, "%d / %d" % (tu['i'] + 1, len(TUTORIAL)), (200, 180, 150))
  hint.set_alpha(int(200 * fade))
  surf.blit(hint, hint.get_rect(midtop=(r.centerx, r.bottom + 4)))
  t = pygame.time.get_ticks() / 1000.0                 # a bouncing arrow pointing at what the hint is about
  arrows = {'tap': None, 'dash': 'DASH_BTN', 'shield': 'SHIELD_BTN', 'hearts': 'hearts', 'power': None}
  tgt = arrows.get(kind)
  if tgt:
    import fd_core
    if tgt == 'hearts':
      x, y = WIDTH - 180, 120
    else:
      rr = getattr(fd_core, tgt)
      x, y = rr.right + 18, rr.centery
    bob = int(math.sin(t * 6) * 6)
    col = (255, 220, 120)
    if tgt == 'hearts':
      pygame.draw.polygon(surf, col, [(x, y + bob), (x - 12, y + 18 + bob), (x + 12, y + 18 + bob)])
    else:
      pygame.draw.polygon(surf, col, [(x + bob, y), (x + 20 + bob, y - 12), (x + 20 + bob, y + 12)])


# ---------------------------------------------------------------- juicier hits
def combo_hit(game, x, y, pts):
  """called for every foe destroyed: keeps a combo going and floats the score up"""
  c = getattr(game, 'combo', 0)
  game.combo = c + 1 if getattr(game, 'combo_t', 0) > 0 else 1
  game.combo_t = 110                                  # frames before the combo runs out
  mult = 1 + min(4, (game.combo - 1) // 5)            # x2 at 6 in a row, up to x5
  bonus = int(pts * (mult - 1))
  if bonus:
    game.score += bonus
  game.floats = getattr(game, 'floats', [])
  label = "+%d" % (pts + bonus) + ("  x%d" % mult if mult > 1 else "")
  stack = sum(1 for f in game.floats if f[2] < 18)       # several kills at once stack upward instead of overlapping
  game.floats.append([float(x), float(y) - stack * 22, 0, label, mult])
  if len(game.floats) > 24:
    del game.floats[:-24]


def juice_update(game):
  if getattr(game, 'combo_t', 0) > 0:
    game.combo_t -= 1
    if game.combo_t == 0:
      game.combo = 0
  keep = []
  for f in getattr(game, 'floats', ()):
    f[1] -= 1.2
    f[2] += 1
    if f[2] < 50:
      keep.append(f)
  game.floats = keep
  if getattr(game, 'flash_t', 0) > 0:
    game.flash_t -= 1


def boss_hit_fx(game, big=False):
  """a short freeze and white flash when a boss takes a big hit"""
  game.freeze = max(getattr(game, 'freeze', 0), 5 if big else 3)
  game.flash_t = 6 if big else 4


def juice_draw(surf, game, font, big_font):
  from fd_core import WIDTH, HEIGHT, text
  for x, y, t, label, mult in getattr(game, 'floats', ()):
    col = (255, 240, 170) if mult == 1 else ((255, 190, 80) if mult < 4 else (255, 110, 90))
    img = text(font, label, col)
    img.set_alpha(max(0, 255 - t * 5))
    surf.blit(img, img.get_rect(center=(int(x), int(y))))
  c = getattr(game, 'combo', 0)
  if c >= 3 and getattr(game, 'combo_t', 0) > 0:
    mult = 1 + min(4, (c - 1) // 5)
    pulse = 1.0 + 0.08 * math.sin(pygame.time.get_ticks() / 70.0)
    img = text(big_font, "COMBO %d" % c + ("  x%d" % mult if mult > 1 else ""), (255, 210, 90))
    img = pygame.transform.scale(img, (int(img.get_width() * pulse) // 2 * 2, int(img.get_height() * pulse) // 2 * 2))
    img.set_alpha(min(255, game.combo_t * 6))
    surf.blit(img, img.get_rect(midtop=(WIDTH // 2, 100)))
  ft = getattr(game, 'flash_t', 0)
  if ft > 0:
    v = min(255, int(ft * 14))                         # brighten in place (no new full-screen surface)
    surf.fill((v, v, v), special_flags=pygame.BLEND_RGB_ADD)


# ---------------------------------------------------------------- pausing when the app is hidden
BACKGROUND_EVENTS = tuple(getattr(pygame, n) for n in ('APP_WILLENTERBACKGROUND', 'APP_DIDENTERBACKGROUND', 'WINDOWMINIMIZED')
                          if hasattr(pygame, n))
FOREGROUND_EVENTS = tuple(getattr(pygame, n) for n in ('APP_DIDENTERFOREGROUND', 'WINDOWRESTORED', 'WINDOWFOCUSGAINED') if hasattr(pygame, n))


def handle_app_event(game, e):
  """True if the event was the app going to / coming back from the background (handled here)."""
  if e.type in BACKGROUND_EVENTS:
    if pygame.time.get_ticks() < getattr(game, 'bg_grace_until', 0):
      return True                                    # (switching to fullscreen at the start of a run sends these: not a real exit)
    from fd_core import save_data
    if game.state in ("PLAYING", "INTRO"):
      game.pause()
    try:
      save_data(game.data)
    except Exception:
      pass
    try:
      from fd_sound import AUDIO
      AUDIO.set_muffled(True)
    except Exception:
      pass
    game.backgrounded = True
    return True
  if e.type in FOREGROUND_EVENTS:
    game.backgrounded = False
    return True
  return False


# ---------------------------------------------------------------- save backup codes
CODE_PREFIX = "FD1-"


def export_code(data):
  """the whole save as a short-ish text code you can copy somewhere safe"""
  raw = json.dumps(data, separators=(',', ':')).encode('utf-8')
  return CODE_PREFIX + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode('ascii').rstrip('=')


def import_code(code):
  """the save inside a backup code, or None if the code isn't valid"""
  code = ''.join(code.split())
  if not code.startswith(CODE_PREFIX):
    return None
  body = code[len(CODE_PREFIX):]
  body += '=' * (-len(body) % 4)
  try:
    data = json.loads(zlib.decompress(base64.urlsafe_b64decode(body.encode('ascii'))).decode('utf-8'))
  except Exception:
    return None
  if not isinstance(data, dict) or 'coins' not in data or 'unlocked' not in data:
    return None
  return data


def clipboard_put(txt):
  """copy text to the phone's clipboard (Android) or the computer's; True if it worked"""
  try:                                               # Android, through pyjnius
    from jnius import autoclass, cast
    act = autoclass('org.kivy.android.PythonActivity').mActivity
    Ctx = autoclass('android.content.Context')
    ClipData = autoclass('android.content.ClipData')
    cm = cast('android.content.ClipboardManager', act.getSystemService(Ctx.CLIPBOARD_SERVICE))
    cm.setPrimaryClip(ClipData.newPlainText("Raid the Realm save", txt))
    return True
  except Exception:
    pass
  try:
    pygame.scrap.init()
    pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode('utf-8'))
    return True
  except Exception:
    pass
  try:
    import pygame._sdl2 as _s                         # noqa
  except Exception:
    pass
  return False


def clipboard_get():
  try:
    from jnius import autoclass, cast
    act = autoclass('org.kivy.android.PythonActivity').mActivity
    Ctx = autoclass('android.content.Context')
    cm = cast('android.content.ClipboardManager', act.getSystemService(Ctx.CLIPBOARD_SERVICE))
    clip = cm.getPrimaryClip()
    if clip is not None and clip.getItemCount() > 0:
      return str(clip.getItemAt(0).coerceToText(act))
  except Exception:
    pass
  try:
    pygame.scrap.init()
    v = pygame.scrap.get(pygame.SCRAP_TEXT)
    if v:
      return v.decode('utf-8', 'ignore').strip('\x00')
  except Exception:
    pass
  return None
