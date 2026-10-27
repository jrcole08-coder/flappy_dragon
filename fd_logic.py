"""Flappy Dragon game logic (state, input, AI, spawning)."""
from fd_villagers import random_villager
from fd_death import DragonDeath
from fd_cyclops import cyc_frame, cyc_count
from fd_extra import extra_frame
from fd_eggs import RARITY_ORDER
from fd_jabber import jab_mouth, JAB, DEATH_BOTTOM as JAB_BOTTOM, SCALE as JAB_SCALE
from fd_hydra import hyd_mouths, DEATH_BOTTOM as HYD_BOTTOM, SCALE as HYD_SCALE
from fd_beholder import beh_point, beam_line, STALKS as BEH_STALKS, LASER_ON as BEH_LASER_ON, BEAM_HALF as BEH_HALF, SCALE as BEH_SCALE, beh_count
import fd_ui as UIX
from fd_night import night_frame, night_count, night_muzzle, night_bottom
import time
from fd_core import *
from fd_art import *
from fd_sound import AUDIO, BREATH_LOOP, WEATHER_LOOP

_VIB = {'v': None, 'tries': 0, 'fx': None, 'sdk': 0}
TOWER_POOL = []                                       # (height, art) painted once per session


def _android_context():
  """Find the running Android activity/context, whichever way this build was packaged."""
  from jnius import autoclass
  for cls, attr in (('org.kivy.android.PythonActivity', 'mActivity'), ('org.renpy.android.PythonActivity', 'mActivity')):
    try:
      act = getattr(autoclass(cls), attr)
      if act is not None:
        return act
    except Exception:
      pass
  try:                                                  # pygame 2 / SDL2 builds (incl. Pydroid)
    return autoclass('org.libsdl.app.SDLActivity').getContext()
  except Exception:
    return None


def _setup_vibrator():
  from jnius import autoclass
  ctx = _android_context()
  if ctx is None:
    return None
  Build = autoclass('android.os.Build$VERSION')
  sdk = int(Build.SDK_INT)
  _VIB['sdk'] = sdk
  vib = None
  if sdk >= 31:                                         # Android 12+: VibratorManager
    try:
      vm = ctx.getSystemService("vibrator_manager")
      if vm is not None:
        vib = vm.getDefaultVibrator()
    except Exception:
      vib = None
  if vib is None:
    vib = ctx.getSystemService("vibrator")
  if vib is None or not vib.hasVibrator():
    return None
  if sdk >= 26:
    _VIB['fx'] = autoclass('android.os.VibrationEffect')
  return vib


def vibrate(ms):
  """Phone vibration on Android (pyjnius, needs the VIBRATE permission). Quietly does nothing elsewhere."""
  if _VIB['v'] is False:
    return
  try:
    if _VIB['v'] is None:
      _VIB['v'] = _setup_vibrator() or False
      if _VIB['v'] is False:
        raise RuntimeError("no vibrator")
    ms = int(ms)
    if _VIB['fx'] is not None:                          # Android 8+: one-shot effect
      _VIB['v'].vibrate(_VIB['fx'].createOneShot(ms, -1))
    else:
      _VIB['v'].vibrate(ms)
    return
  except Exception:
    pass
  try:                                                  # older pygame-for-Android builds
    import android                                      # noqa
    android.vibrate(ms / 1000.0)
    _VIB['v'] = 'android'
    return
  except Exception:
    pass
  try:                                                  # plyer, if it is installed
    from plyer import vibrator
    vibrator.vibrate(time=ms / 1000.0)
    _VIB['v'] = 'plyer'
    return
  except Exception:
    pass
  _VIB['tries'] += 1
  _VIB['v'] = False if _VIB['tries'] >= 3 else None     # try setting up again a couple of times

class GameLogic:
  def __init__(self):
    self.data = load_data()
    for _bb in self.data.get('babies', []):
      self.pet_defaults(_bb)
    AUDIO.set_enabled(self.data.get('sound', True))
    AUDIO.set_levels(self.data.get('music_vol', 100) / 100.0, self.data.get('sfx_vol', 100) / 100.0)
    AUDIO.set_music(self.data.get('music', True) and self.data.get('music_vol', 100) > 0)
    AUDIO.set_sfx(self.data.get('sfx', True) and self.data.get('sfx_vol', 100) > 0)
    self.opt_drag = None
    AUDIO.start_music()
    self.state = "MENU"
    self.selected = "RED"
    self.pending = None
    self.en_scroll, self.en_drag, self.en_idx = 0.0, None, 0
    self.en_page, self.en_flip = 0, None
    self.egg_scroll, self.egg_drag, self.egg_idx = 0.0, None, 0
    self.hatching = None
    self.hb_scroll, self.hb_drag = 0.0, None
    self.hb_view, self.den, self.den_sel, self.hb_idx, self.pet_react = 'den', {}, None, 0, 0
    self.egg_drop = None
    self.confirm_menu = False
    self.opt_from = "MENU"
    self.fullscreen = False
    self.anim = 0.0
    self.shake_i = self.shake_t = 0
    self.far_x = self.near_x = self.mid_x = 0.0
    self.twinkle = [(random.randint(0, WIDTH), random.randint(0, 360), random.uniform(0, 6.28)) for _ in range(26)]
    self.clouds = [[random.uniform(-100, WIDTH), random.randint(20, 200), random.randint(0, 99), random.uniform(0.2, 0.5)] for _ in range(7)]
    self.mist = [[random.uniform(0, WIDTH), random.randint(HEIGHT - 100, GROUND_Y - 8), random.uniform(1, 3)] for _ in range(14)]
    self.embers = [self.new_ember(True) for _ in range(34)]
    self.menu_dragon_x = -140.0
    self.scroll = float(BASE_SCROLL)
    self.scroll_px = 6
    self.mouse = (0, 0)
    self.over_t = 0
    self.new_record = False
    self.surface = screen            # the surface we present to (changes if fullscreen is toggled)
    self.view_sy = 1.0
    self.view = (1.0, 0, 0)          # (scale, x_offset, y_offset) of the picture when letterboxed
    self.scale_buf = None
    self.intro_layer = None
    self.intro_t = 0
    self.toast_msg, self.toast_t = '', 0
    self.info_key, self.info_from, self.info_t = 'RED', 'SELECT', 0
    self.pending = None
    self.reset_run()
    self.roll_quest()

  def reset_run(self):
    self.dragon = pygame.Rect(150, HEIGHT // 2, 65, 38)
    self.vel = 0.0
    self.wing = 0.0
    self.flap_ph, self.flap_left = flap_cycle(self.selected)[0], 0.0    # the player's own wing beat (driven by taps)
    self.pitch = 0.0
    self.hold = False
    self.hold_t = 0
    self.gliding = False
    self.glide_mult = 1.0
    self.glide_y0 = 0.0
    self.glide_f0 = 0.0
    self.trail = []
    self.flip_t = 0
    self.flip_dir = 1
    self.score = 0
    self.dp = 0.0
    self.shields = 0
    self.shield_active = False
    self.shield_timer = 0
    self.hearts = 3 if self.data.get('difficulty', 'easy') == 'easy' else 0
    self.hit_inv = 0
    self.dash_state = 'idle'
    self.dash_cd = 0
    self.dash_inv = 0
    self.dash_boss = False
    self.run_coins = 0.0
    self.breath = False
    self.breath_timer = 0
    self.ts = 1.0
    self.slow_acc = 0.0
    self.tick = True
    self.threat = 1
    self.boss = None
    self.b1 = self.b2 = self.b3 = self.b4 = self.b5 = self.b6 = False
    self.talon, self.talon_q, self.talon_home = None, 0, False   # griffin, phoenix, jabberwock, demon, hydra, beholder
    self.heart_drop, self.heart_delay = None, 0
    self.init_weather()
    self.day = (random.random() < 0.45 or not self.data.get('weather', True)) and ensure_day_assets()
    for n in GROUND_LISTS + ('enemies', 'fireballs', 'arrows', 'orbs', 'spears', 'scenery', 'particles', 'powerups', 'coins', 'bolts', 'globs', 'lava', 'rubble', 'tornados', 'corpses', 'holes', 'fog', 'wisps', 'bones', 'souls', 'missiles', 'booms', 'vines', 'leaves', 'eggs_shot', 'chicks', 'novas', 'butterflies'):
      setattr(self, n, [])
    self.spawn_t = self.scenery_t = self.power_t = 0
    self.dead = False
    self.death = None
    self.prefill_scenery()
    if self.data.get('fullscreen', True):
      self.set_fullscreen(True, quiet=True)

  def init_weather(self):
    k = random.choices(WEATHER_KINDS, WEATHER_WEIGHTS)[0]
    if not self.data.get('weather', True):
      k = "clear"
    self.wx_kind, self.wx_t, self.gust = k, 0, 0.0
    self.flash, self.bolt, self.bolt_t = 0, None, random.randint(90, 240)
    n = {"rain": 70, "storm": 95, "snow": 55, "wind": 22}.get(k, 0)
    self.wx_parts = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0.7, 1.3), random.uniform(0, 6.28)] for _ in range(n)]

  def update_weather(self):
    try:
      self._update_weather()
    except Exception:
      self.wx_kind = "clear"

  def _update_weather(self):
    k = self.wx_kind
    if k == "clear":
      return
    self.wx_t += 1
    wind = 0.0
    if k in ("wind", "storm"):
      wind = math.sin(self.wx_t * 0.02) * math.sin(self.wx_t * 0.013)
    self.gust = wind * (0.13 if k == "wind" else 0.05)
    for p in self.wx_parts:
      if k in ("rain", "storm"):
        p[1] += 22 * p[2]
        p[0] -= 4 + wind * 4
      elif k == "snow":
        p[1] += 1.8 * p[2]
        p[0] += math.sin(self.wx_t * 0.04 + p[3]) * 0.8 - 1
      elif k == "wind":
        p[0] -= 26 * p[2]
        p[1] += math.sin(self.wx_t * 0.05 + p[3]) * 0.6
      if p[1] > HEIGHT or p[0] < -60 or p[0] > WIDTH + 20:
        if k == "wind":
          p[0], p[1] = WIDTH + random.uniform(0, 80), random.uniform(0, GROUND_Y)
        else:
          p[0], p[1] = random.uniform(0, WIDTH + 40), -random.uniform(0, 30)
    if k == "storm":
      if self.flash > 0:
        self.flash -= 1
      self.bolt_t -= 1
      if self.bolt_t <= 0:
        self.bolt_t = random.randint(150, 420)
        self.flash = 7
        AUDIO.play('thunder')
        bx, by, pts = random.randint(60, WIDTH - 60), 0, []
        while by < GROUND_Y - 20:
          pts.append((bx, by))
          bx += random.randint(-28, 28)
          by += random.randint(30, 60)
        pts.append((bx, GROUND_Y))
        self.bolt = pts
        self.shake_for(3, 6)

  def draw_weather(self, gs):
    try:
      self._draw_weather(gs)
    except Exception:
      self.wx_kind = "clear"

  def _draw_weather(self, gs):
    k = self.wx_kind
    if k == "clear":
      return
    if k == "storm":
      gs.fill((46, 46, 34), special_flags=pygame.BLEND_RGB_SUB)
    elif k == "rain":
      gs.fill((24, 24, 18), special_flags=pygame.BLEND_RGB_SUB)
    elif k == "fog":
      gs.fill((56, 62, 74), special_flags=pygame.BLEND_RGB_ADD)
      for i in range(6 if WISP else 0):
        gs.blit(WISP, (int((self.wx_t * (0.5 + i * 0.12) + i * 190) % (WIDTH + 260)) - 240, 40 + i * 70))
    elif k == "snow":
      gs.fill((14, 16, 24), special_flags=pygame.BLEND_RGB_ADD)
    if k in ("rain", "storm"):
      for p in self.wx_parts:
        x, y = int(p[0]), int(p[1])
        pygame.draw.line(gs, (150, 170, 205), (x, y), (x - 3, y + 11), 1)
    elif k == "snow":
      for p in self.wx_parts:
        pygame.draw.circle(gs, (240, 245, 255), (int(p[0]), int(p[1])), 2 if p[2] > 1.0 else 1)
    elif k == "wind":
      for p in self.wx_parts:
        x, y = int(p[0]), int(p[1])
        pygame.draw.line(gs, (170, 180, 195), (x, y), (x + int(34 * p[2]), y + 1), 1)
    if k == "storm" and self.flash > 0:
      if self.bolt:
        pygame.draw.lines(gs, (190, 200, 255), False, self.bolt, 6)
        pygame.draw.lines(gs, (255, 255, 255), False, self.bolt, 2)
      c = min(120, self.flash * 18)
      gs.fill((c, c, c), special_flags=pygame.BLEND_RGB_ADD)
    if self.state == "PLAYING" and k in WEATHER_NAMES and self.wx_t < 200:
      col = (255, 255, 255) if self.wx_t < 150 else (190, 190, 200)
      blit_text(gs, small_font, "Weather: " + WEATHER_NAMES[k], col, (WIDTH // 2, 82), "center")

  def egg_stacks(self):
    """eggs of the same rarity share one card: [(egg, [indices]), ...] rarest first"""
    groups, order = {}, []
    for i, egg in enumerate(self.data['eggs']):
      k = egg['r']
      if k not in groups:
        groups[k] = []
        order.append(k)
      groups[k].append(i)
    order.sort(key=lambda k: -RARITY_ORDER.index(k) if k in RARITY_ORDER else 0)
    return [(self.data['eggs'][groups[k][0]], groups[k]) for k in order]

  def pick_quest(self, avoid=()):
    owned = self.data.get('unlocked', [])
    pool = [q for q in BOUNTIES if (not q.get('dragon') or q['dragon'] in owned) and q['desc'] not in avoid]
    q = random.choice(pool or BOUNTIES).copy()
    q['progress'] = 0
    q['done'] = False
    return q

  def roll_quest(self):
    d = self.data
    q = d.get('active_quest')
    changed = False
    if not q or q.get('done'):
      q = d.get('next_quest') or self.pick_quest()
      d['active_quest'] = q
      d['next_quest'] = None
      changed = True
    if not d.get('next_quest'):
      d['next_quest'] = self.pick_quest((q['desc'],))
      changed = True
    if changed:
      save_data(d)
    self.bounty = q

  def start_run(self):
    prewarm_dragon(self.selected)
    prewarm_siege()
    self.reset_run()
    self.run_bosses = 0
    self.run_stats = {'kills': {}, 'powerups': 0, 'eggs': [], 'quests': [], 'dist': 0.0, 'bosses': [], 'ticks': 0, 'hearts_lost': 0}
    self.pet = self.find_pet(self.data.get('companion'))
    d = self.dragon
    self.pet_pos = [float(d.x - 60), float(d.y - 30)]
    self.pet_cd = 90.0
    self.pet_shots = []
    self.pet_atk = 0
    self.compute_params()
    self.roll_quest()
    self.confirm_menu = False
    self.intro_t = 0
    self.state = "INTRO"

  def new_ember(self, anywhere=False):
    return [random.uniform(0, WIDTH), random.uniform(0, HEIGHT) if anywhere else HEIGHT + 5, random.uniform(0.4, 1.4), random.randint(2, 5), random.uniform(0, 6.28)]

  def shake_for(self, intensity, duration):
    if not self.data.get('shake', True):
      return
    self.shake_i, self.shake_t = intensity, max(self.shake_t, duration)

  def emit(self, x, y, vx, vy, size, color):
    if len(self.particles) < MAX_PARTICLES:
      self.particles.append([x, y, vx, vy, size, color])

  def burst(self, x, y, n, speed, smin, smax, color):
    for _ in range(n):
      self.emit(x, y, random.uniform(-speed, speed), random.uniform(-speed, speed), random.randint(smin, smax), color)

  def compute_params(self):
    up, sel = self.data['upgrades'], self.selected
    self.threat = 1 + self.score // 300
    self.scroll = BASE_SCROLL * 0.2 if self.boss else BASE_SCROLL + self.threat * 0.4
    self.scroll *= getattr(self, 'glide_mult', 1.0)
    self.scroll_px = max(2, int(math.ceil(self.scroll)))
    self.gravity = 0.40 if sel == "BLUE" else BASE_GRAVITY
    self.breath_time = (380 if sel == "RED" else 240) + up['deep_lungs'] * 60
    self.score_mult = 1
    self.coin_val = 1.5 if sel == "CHINESE" else 1.0
    self.ts = 0.5 if (sel == "CHRONO" and self.breath) else 1.0
    self.slow_acc = getattr(self, 'slow_acc', 0.0) + self.ts
    self.tick = self.slow_acc >= 1.0
    if self.tick:
      self.slow_acc -= 1.0
    self.max_shields = 3 + up['thick_scales']
    self.magnet = 50 + up['coin_magnet'] * 60

  def bounty_add(self, kind, key=None, n=1):
    q = self.bounty
    if q and q['type'] == kind and not q.get('done') and q.get('foe') in (None, key) and q.get('dragon') in (None, self.selected):
      q['progress'] += n

  def kill_key(self, name, o):
    if name == 'enemies':
      return 'eye' if o.get('kind') == 'wyvern' else (o.get('foe') or 'harpy')
    if name == 'mages':
      return o.get('kind', 'skel')
    return KILL_KEY.get(name, name)

  def note_boss(self, btype):
    self.heart_delay = 100                          # a heart power-up floats in a moment after every boss
    rs = getattr(self, 'run_stats', None)
    if rs is not None:
      rs['bosses'].append(btype)
    self.bounty_add('boss', btype)

  def garrison(self, tw, perch):
    """an archer or a mage standing on top of a tower; it falls if the tower is destroyed."""
    r = tw['rect']
    feet = r.top - perch
    if random.random() < 0.6:
      u = {'rect': pygame.Rect(r.centerx - 15, feet - 45, 30, 45), 'fired': False, 'passed': False, 'state': 'normal', 'perch': tw}
      self.archers.append(u)
    else:
      mk = random.choice(('pyro', 'wiz', 'skel'))
      mw, mh = {'pyro': (34, 66), 'wiz': (30, 60), 'skel': (36, 72)}[mk]
      u = {'rect': pygame.Rect(r.centerx - mw // 2, feet - mh, mw, mh), 'timer': 0, 'passed': False, 'state': 'normal', 'kind': mk,
           'ph': random.randint(0, 11), 'perch': tw}
      self.mages.append(u)

  def perch_check(self, o):
    """units on a tower drop to the ground when the tower crumbles, shatters or is blown away."""
    tw = o.get('perch')
    if tw is not None and (tw.get('shattered') or tw.get('state') in ('blown', 'spun') or tw not in self.towers):
      o['perch'] = None
      if not o.get('shattered'):                    # the tower is gone: the unit on top falls to its death
        o['shattered'] = True
        self.score += 10 * self.score_mult
      return True
    if o.get('fall') is not None:
      o['fall'] += BASE_GRAVITY * 1.4
      o['rect'].y += int(o['fall']) + 1
      if o['rect'].bottom >= GROUND_Y:
        o['rect'].bottom = GROUND_Y
        o['fall'] = None
        self.burst(o['rect'].centerx, GROUND_Y - 4, 8, 2, 3, 6, (150, 140, 130))
      return True
    return False

  def spawn_scenery(self, x):
    t = random.choices(SCENERY_TYPES, SCENERY_WEIGHTS)[0]
    if t == "grass":
      t = "grass%d" % random.randint(0, 2)
    elif t == "flowers":
      t = "flowers%d" % random.randint(0, 1)
    elif t == "pgrass":
      t = random.choice(("pgrass0", "pgrass1", "pgrass2", "tuft"))
    elif t == "boulder":
      t = random.choice(("boulder0", "boulder1", "pebble"))
    elif t == "crate":
      t = random.choice(("crate", "crate2"))
    elif t == "pbush":
      t = random.choice(("pbush", "fern"))
    elif t == "twig":
      t = random.choice(("twig", "sprout"))
    sc = {'type': t, 'x': float(x), 'anim': random.uniform(0, 10), 'mod': random.uniform(0.8, 2.5)}
    if t == "villager":                       # random outfit + what they are doing
      sc['v'] = random_villager()
      sc['mode'] = random.choices(('walk', 'run', 'idle'), (5, 3, 3))[0]
      sc['right'] = sc['mode'] == 'idle' and random.random() < 0.5 or (sc['mode'] == 'walk' and random.random() < 0.3)
      sc['mod'] = {'walk': random.uniform(0.5, 1.1), 'run': random.uniform(2.0, 3.4), 'idle': 0.0}[sc['mode']]
      if sc['right']:
        sc['mod'] = -sc['mod']                # walking the other way
    self.scenery.append(sc)

  def prefill_scenery(self):
    for _ in range(16):
      self.spawn_scenery(random.randint(0, WIDTH))

  def update_scenery(self, speed, interval):
    keep = []
    for s in self.scenery:
      if speed:
        s['anim'] += 0.2
        s['x'] -= speed + (s['mod'] if s['type'] in ("sheep", "deer", "knight", "dwarf", "villager") else 0)
      if s['x'] > -170:
        keep.append(s)
    self.scenery = keep
    self.scenery_t += 1
    if self.scenery_t > interval and speed:
      self.scenery_t = 0
      self.spawn_scenery(WIDTH)

  def run(self):
    self.crash = None
    while True:
      try:
        for e in pygame.event.get():
          if e.type == pygame.QUIT:
            self.quit()
          self.handle_event(e)
        self.mouse = self.map_pos(pygame.mouse.get_pos())
        self.update()
        self.draw()
      except SystemExit:
        raise
      except Exception:
        self.report_crash()
      clock.tick(FPS)

  def report_crash(self):
    """An error no longer freezes the game: it is written to fd_error_log.txt and shown on screen."""
    import traceback
    tb = traceback.format_exc()
    first = self.crash is None
    self.crash = tb.strip().splitlines()[-1][:110]
    if first:
      try:
        path = os.path.join(os.path.dirname(os.path.abspath(SAVE_FILE)) or '.', 'fd_error_log.txt')
        with open(path, 'a') as f:
          f.write('\n==== %s  state=%s\n%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), self.state, tb))
      except Exception:
        pass
    try:                                              # keep playing if we can; show what went wrong
      scr = pygame.display.get_surface()
      if scr is not None:
        f = pygame.font.Font(None, 24)
        lines = ["Oops - an error happened (saved to fd_error_log.txt):", self.crash]
        for i, ln in enumerate(lines):
          img = f.render(ln, True, (255, 255, 255), (150, 20, 20))
          scr.blit(img, (10, 10 + i * 26))
        pygame.display.flip()
    except Exception:
      pass

  def quit(self):
    save_data(self.data)
    pygame.quit()
    sys.exit()

  def handle_event(self, e):
    st = self.state
    if (e.type == pygame.MOUSEBUTTONUP and e.button == 1) or (e.type == pygame.KEYUP and e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)):
      self.hold = False
    click = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
    pos = self.map_pos(e.pos) if hasattr(e, 'pos') else (0, 0)
    key = e.key if e.type == pygame.KEYDOWN else None
    if key == pygame.K_F11:
      self.set_fullscreen(not self.fullscreen)
      self.data['fullscreen'] = self.fullscreen
      save_data(self.data)
      return
    if key == pygame.K_m or (click and st in ("MENU", "PAUSED") and SND_BTN.collidepoint(pos)):
      self.toggle_sound()
      return
    if click:
      UI['press'] = (pos, pygame.time.get_ticks())       # buttons sink when pressed
    if click and UIX.tab_bar_shown(self) and pos[1] >= UIX.TAB_BAR.top - 26:
      for k, _lab, r in UIX.tab_rects():
        if r.collidepoint(pos):
          self.tab_action(k)
      return

    if st == "MENU":
      if key in (pygame.K_RETURN, pygame.K_SPACE):
        self.start_run()
      if click:
        for k, r in MENU_RECTS.items():
          if r.collidepoint(pos):
            self.menu_action(k)
    elif st == "OPTIONS":
      drag = getattr(self, 'opt_drag', None)
      if drag and e.type == pygame.MOUSEMOTION:
        self.set_volume_from(drag, pos[0])
      elif drag and e.type == pygame.MOUSEBUTTONUP:
        self.opt_drag = None
        save_data(self.data)
        AUDIO.play('click')                     # lets you hear the new sound-effect level
      elif (click and BACK_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = self.opt_from
      elif click:
        for k, r in OPT_RECTS.items():
          if k in ("weather", "difficulty") and self.opt_from == "PAUSED":
            continue
          if r.collidepoint(pos):
            if k in OPT_SLIDERS:
              self.opt_drag = k
              self.set_volume_from(k, pos[0])
            else:
              self.option_action(k)
      elif key in (pygame.K_LEFT, pygame.K_RIGHT):
        k = 'music'
        self.data['music_vol'] = max(0, min(100, self.data.get('music_vol', 100) + (5 if key == pygame.K_RIGHT else -5)))
        self.apply_volumes()
    elif st in ("LAIR", "WORLDS"):
      if (click and BACK_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "MENU"
      elif click and st == "LAIR":
        for k, r in LAIR_RECTS.items():
          if r.collidepoint(pos):
            self.menu_action(k)
    elif st in ("QUESTS", "HOARD"):
      if (click and BACK_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "LAIR"
      elif click and st == "HOARD":
        for k, _t, _d, rect in UPGRADES:
          lvl = self.data['upgrades'][k]
          btn = upgrade_btn(rect)
          if lvl < 3 and btn.collidepoint(pos) and self.data['coins'] >= UPGRADE_COSTS[lvl]:
            self.data['coins'] -= UPGRADE_COSTS[lvl]
            self.data['upgrades'][k] += 1
            save_data(self.data)
            AUDIO.play('shatter', 0.6)
            UIX.spark_burst(self, rect.centerx, 330)       # hammered out on the anvil
    elif st in ("SELECT", "RARE_SELECT"):
      boxes = SELECT_BOXES if st == "SELECT" else RARE_BOXES
      if click:
        if self.pending:
          if BUY_YES.collidepoint(pos):
            cost = DRAGON_PALETTES[self.pending]['cost']
            if self.data['coins'] >= cost:
              self.data['coins'] -= cost
              self.data['unlocked'].append(self.pending)
              self.selected = self.pending
              save_data(self.data)
            self.pending = None
          elif BUY_NO.collidepoint(pos):
            self.pending = None
        else:
          for k, r in boxes:
            if r.collidepoint(pos):
              AUDIO.play('click')
              self.info_key, self.info_from, self.info_t = k, st, 0
              self.state = "DRAGON_INFO"
              return
          if RARE_BTN.collidepoint(pos):
            AUDIO.play('click')
            self.state = "RARE_SELECT" if st == "SELECT" else "SELECT"
      elif key == pygame.K_ESCAPE:
        self.pending = None
        self.state = "LAIR" if st == "SELECT" else "SELECT"
    elif st == "ENEMIES":                         # the Monster Manual: swipe / corner tabs turn pages
      last = (len(ENEMY_INFO) + 1) // 2 - 1
      pa, na = UIX.book_arrows()
      if click:
        if pa.collidepoint(pos) and self.en_page > 0:
          self.turn_page(-1)
        elif na.collidepoint(pos) and self.en_page < last:
          self.turn_page(1)
        elif UIX.book_rect().collidepoint(pos):
          self.en_drag = [pos[0], pos[1], False]
      elif e.type == pygame.MOUSEMOTION and self.en_drag:
        if abs(pos[0] - self.en_drag[0]) > 12:
          self.en_drag[2] = True
      elif e.type == pygame.MOUSEBUTTONUP and self.en_drag:
        dx = pos[0] - self.en_drag[0]
        if self.en_drag[2] and dx < -50 and self.en_page < last:
          self.turn_page(1)
        elif self.en_drag[2] and dx > 50 and self.en_page > 0:
          self.turn_page(-1)
        elif not self.en_drag[2]:
          lr, rr = UIX.page_rects()
          i = self.en_page * 2 + (1 if rr.collidepoint(pos) else 0)
          if (lr.collidepoint(pos) or rr.collidepoint(pos)) and i < len(ENEMY_INFO):
            AUDIO.play('click')
            self.en_idx = i
            self.info_t = 0
            self.state = "ENEMY_INFO"
        self.en_drag = None
      elif e.type == getattr(pygame, 'MOUSEWHEEL', -1) and e.y:
        d = -1 if e.y > 0 else 1
        if 0 <= self.en_page + d <= last:
          self.turn_page(d)
      elif key in (pygame.K_RIGHT, pygame.K_d) and self.en_page < last:
        self.turn_page(1)
      elif key in (pygame.K_LEFT, pygame.K_a) and self.en_page > 0:
        self.turn_page(-1)
      elif key == pygame.K_ESCAPE:
        self.state = "LAIR"
    elif st == "EGGS":
      g = EGG_GRID
      cw, ch, gap, pitch = EGG_CARD
      eggs = self.egg_stacks()
      rows = (len(eggs) + 3) // 4
      max_s = max(0, rows * pitch - (pitch - ch) - g.h)
      if click:
        if EGG_BACK_BTN.collidepoint(pos):
          self.state = "LAIR"
        elif EGG_ROOST_BTN.collidepoint(pos):
          AUDIO.play('click')
          self.state = "ROOSTS"
        elif g.collidepoint(pos):
          self.egg_drag = [pos[1], self.egg_scroll, pos, False]
      elif e.type == pygame.MOUSEMOTION and self.egg_drag:
        dy = pos[1] - self.egg_drag[0]
        if abs(dy) > 8:
          self.egg_drag[3] = True
        self.egg_scroll = max(0.0, min(max_s, self.egg_drag[1] - dy))
      elif e.type == pygame.MOUSEBUTTONUP and self.egg_drag:
        if not self.egg_drag[3]:
          px, py = self.egg_drag[2]
          col = (px - g.x) // (cw + gap)
          row = int((py - g.y + self.egg_scroll) // pitch)
          inside = (px - g.x) % (cw + gap) < cw and (py - g.y + self.egg_scroll) % pitch < ch
          i = row * 4 + col
          if inside and 0 <= col < 4 and 0 <= i < len(eggs):
            AUDIO.play('click')
            self.egg_idx = eggs[i][1][0]
            self.state = "EGG_INFO"
        self.egg_drag = None
      elif e.type == getattr(pygame, 'MOUSEWHEEL', -1):
        self.egg_scroll = max(0.0, min(max_s, self.egg_scroll - e.y * 60))
      elif key == pygame.K_ESCAPE:
        self.state = "LAIR"
    elif st == "HATCHLINGS":
      babies = self.data.get('babies', [])
      if click and EGG_BACK_BTN.collidepoint(pos) or key == pygame.K_ESCAPE:
        self.state = "LAIR"
      elif click and HB_VIEW_BTN.collidepoint(pos):
        self.hb_view = 'list' if self.hb_view == 'den' else 'den'
        AUDIO.play('click')
      elif self.hb_view == 'den':
        if click and self.den_sel is not None and HB_DETAIL_BTN.collidepoint(pos):
          for k, bb in enumerate(babies):
            if bb.get('id') == self.den_sel:
              self.hb_idx = k
              self.pet_react = 0
              self.state = "HATCH_INFO"
          AUDIO.play('click')
        elif click and DEN_RECT.collidepoint(pos):
          best, bd = None, 70.0
          for bid, dv in self.den.items():
            dd = math.hypot(dv[0] - pos[0], dv[1] - pos[1])
            if dd < bd:
              best, bd = bid, dd
          self.den_sel = best
          if best is not None:
            self.den[best][4] = 45
            self.den[best][3] = -6.0
            AUDIO.play('coin', 0.5)
      else:
        g = EGG_GRID
        cw, ch, gap, pitch = EGG_CARD
        rows = (len(babies) + 3) // 4
        max_s = max(0, rows * pitch - (pitch - ch) - g.h)
        if click and g.collidepoint(pos):
          self.hb_drag = [pos[1], self.hb_scroll, pos, False]
        elif e.type == pygame.MOUSEMOTION and self.hb_drag:
          dy = pos[1] - self.hb_drag[0]
          if abs(dy) > 8:
            self.hb_drag[3] = True
          self.hb_scroll = max(0.0, min(max_s, self.hb_drag[1] - dy))
        elif e.type == pygame.MOUSEBUTTONUP and self.hb_drag:
          if not self.hb_drag[3]:
            px, py = self.hb_drag[2]
            col = (px - g.x) // (cw + gap)
            row = int((py - g.y + self.hb_scroll) // pitch)
            inside = (px - g.x) % (cw + gap) < cw and (py - g.y + self.hb_scroll) % pitch < ch
            k = row * 4 + col
            if inside and 0 <= col < 4 and 0 <= k < len(babies):
              AUDIO.play('click')
              self.hb_idx = k
              self.pet_react = 0
              self.state = "HATCH_INFO"
          self.hb_drag = None
        elif e.type == getattr(pygame, 'MOUSEWHEEL', -1):
          self.hb_scroll = max(0.0, min(max_s, self.hb_scroll - e.y * 60))
    elif st == "HATCH_INFO":
      babies = self.data.get('babies', [])
      if not babies or self.hb_idx >= len(babies):
        self.state = "HATCHLINGS"
        return
      bb = self.pet_defaults(babies[self.hb_idx])
      if (click and PET_BTNS[0].collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "HATCHLINGS"
      elif click and PET_BTNS[1].collidepoint(pos):
        k = (BABY_NAMES.index(bb['name']) + 1) % len(BABY_NAMES) if bb['name'] in BABY_NAMES else 0
        bb['name'] = BABY_NAMES[k]
        save_data(self.data)
        AUDIO.play('click')
      elif click and PET_BTNS[2].collidepoint(pos):
        self.pet_feed(bb)
        self.pet_react = 50
      elif click and PET_BTNS[3].collidepoint(pos):
        self.data['companion'] = None if self.data.get('companion') == bb['id'] else bb['id']
        save_data(self.data)
        AUDIO.play('click')
        if self.data['companion'] is not None:
          self.toast("%s will fly with you!" % bb['name'])
      elif click and INFO_PORTRAIT.collidepoint(pos):
        self.pet_react = 50
        AUDIO.play('coin', 0.5)
    elif st == "EGG_INFO":
      eggs = self.data['eggs']
      if not eggs or self.egg_idx >= len(eggs):
        self.state = "EGGS"
      elif (click and INFO_BACK.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "EGGS"
      elif (click and INFO_SELECT.collidepoint(pos)) or key in (pygame.K_RETURN, pygame.K_SPACE):
        roosts = self.data['roosts']
        if None in roosts:
          egg = eggs.pop(self.egg_idx)
          roosts[roosts.index(None)] = {'r': egg['r'], 'id': egg['id'], 'boss': egg.get('boss'), 'start': time.time()}
          save_data(self.data)
          AUDIO.play('coin')
          self.toast("Your egg is warming in the roost!")
          self.state = "ROOSTS"
        else:
          self.toast("All roosts are full - buy another roost!")
    elif st == "ROOSTS":
      if (click and EGG_ROOST_BTN.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "EGGS"
      elif click and not self.hatching:
        roosts = self.data['roosts']
        for i, r in enumerate(ROOST_RECTS):
          if not r.collidepoint(pos):
            continue
          if i < len(roosts):
            slot = roosts[i]
            left = self.roost_left(slot) if slot else 0
            if slot and left > 0:
              if speed_rect(r).collidepoint(pos):
                cost, skip = skip_cost(left)
                if self.data['coins'] >= cost:
                  self.data['coins'] -= cost
                  slot['start'] -= skip
                  save_data(self.data)
                  AUDIO.play('coin')
                  self.toast("Ready to hatch!" if self.roost_left(slot) <= 0 else "The egg warms up - 1 hour sooner!")
                else:
                  self.toast("Not enough gold!")
            elif slot and left <= 0:
              odds = HATCH_TYPES.get(slot['r'], (('GREEN', 1),))
              self.hatching = {'slot': i, 't': 0, 'type': random.choices([o_[0] for o_ in odds], [o_[1] for o_ in odds])[0]}
              AUDIO.play('roar', 0.6)
            elif slot is None:
              self.toast("Pick an egg from Dragon Eggs to place here")
          elif i == len(roosts):
            price = ROOST_PRICES[i - 1]
            if self.data['coins'] >= price:
              self.data['coins'] -= price
              roosts.append(None)
              save_data(self.data)
              AUDIO.play('coin')
              self.toast("New roost built!")
            else:
              self.toast("Not enough gold!")
    elif st == "ENEMY_INFO":
      n = len(ENEMY_INFO)
      if (click and EN_BACK.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.state = "ENEMIES"
        self.en_page, self.en_flip = self.en_idx // 2, None   # open the book at this beast's page
      elif (click and EN_PREV.collidepoint(pos)) or key in (pygame.K_LEFT, pygame.K_a):
        self.en_idx = (self.en_idx - 1) % n
        AUDIO.play('click')
      elif (click and EN_NEXT.collidepoint(pos)) or key in (pygame.K_RIGHT, pygame.K_d):
        self.en_idx = (self.en_idx + 1) % n
        AUDIO.play('click')
    elif st == "DRAGON_INFO":
      k = self.info_key
      if click and self.pending:
        if BUY_YES.collidepoint(pos):
          cost = DRAGON_PALETTES[self.pending]['cost']
          if self.data['coins'] >= cost:
            self.data['coins'] -= cost
            self.data['unlocked'].append(self.pending)
            self.selected = self.pending
            save_data(self.data)
            AUDIO.play('coin')
          self.pending = None
        elif BUY_NO.collidepoint(pos):
          self.pending = None
      elif (click and INFO_BACK.collidepoint(pos)) or key == pygame.K_ESCAPE:
        self.pending = None
        self.state = self.info_from
      elif (click and INFO_SELECT.collidepoint(pos)) or key in (pygame.K_RETURN, pygame.K_SPACE):
        if k in self.data['unlocked']:
          self.selected = k
          AUDIO.play('click')
          self.state = self.info_from
        elif self.data['coins'] >= DRAGON_PALETTES[k]['cost']:
          self.pending = k
        else:
          self.toast("Not enough gold!")
    elif st == "INTRO":
      if click or key in (pygame.K_SPACE, pygame.K_RETURN):
        self.state = "PLAYING"
    elif st == "PLAYING":
      if click:
        if PAUSE_BTN.collidepoint(pos):
          self.pause()
        elif SHIELD_BTN.collidepoint(pos):
          self.use_shield()
        elif DASH_BTN.collidepoint(pos):
          self.try_dash()
        else:
          self.flap()
          self.hold, self.hold_t = True, 0
      elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
        self.flap()
        self.hold, self.hold_t = True, 0
      elif key in (pygame.K_p, pygame.K_ESCAPE):
        self.pause()
      elif key in (pygame.K_s, pygame.K_DOWN):
        self.use_shield()
      elif key in (pygame.K_d, pygame.K_RIGHT, pygame.K_LSHIFT, pygame.K_RSHIFT):
        self.try_dash()
    elif st == "PAUSED":
      if click:
        if not self.confirm_menu:
          if RESUME_BTN.collidepoint(pos):
            self.state = "PLAYING"
          elif OPT_BTN.collidepoint(pos):
            self.opt_from = "PAUSED"
            self.state = "OPTIONS"
          elif MENU_BTN.collidepoint(pos):
            self.confirm_menu = True
        else:
          if YES_BTN.collidepoint(pos):
            self.state = "MENU"
            self.confirm_menu = False
          elif NO_BTN.collidepoint(pos):
            self.confirm_menu = False
      elif key in (pygame.K_p, pygame.K_ESCAPE):
        self.state = "PLAYING"
    elif st == "GAMEOVER":
      dd = getattr(self, 'death', None)
      if (click or key in (pygame.K_SPACE, pygame.K_RETURN)) and dd and not dd.done and dd.t > 30:
        dd.t = max(dd.t, 140)                     # tap to hurry the ashes along
      elif click and self.over_t > 25 and REPORT_BTN.collidepoint(pos):
        AUDIO.play('click')
        self.state = "REPORT"
        self.report_scroll, self.report_drag = 0.0, None
      elif (click or key in (pygame.K_SPACE, pygame.K_RETURN)) and self.over_t > 25:
        self.state = "MENU"
    elif st == "REPORT":
      drag = getattr(self, 'report_drag', None)
      if (click and (REPORT_BACK if UIX.art_ok("report") else BACK_BTN).collidepoint(pos)) or key == pygame.K_ESCAPE:
        AUDIO.play('click')
        self.state = "GAMEOVER"
      elif click and REPORT_LIST.collidepoint(pos):
        self.report_drag = (pos[1], getattr(self, 'report_scroll', 0.0))
      elif e.type == pygame.MOUSEMOTION and drag:
        self.report_scroll = drag[1] - (pos[1] - drag[0])      # (clamped when drawn)
      elif e.type == pygame.MOUSEBUTTONUP:
        self.report_drag = None
      elif e.type == getattr(pygame, 'MOUSEWHEEL', -1):
        self.report_scroll = getattr(self, 'report_scroll', 0.0) - e.y * 46
      elif key in (pygame.K_DOWN, pygame.K_s):
        self.report_scroll = getattr(self, 'report_scroll', 0.0) + 46
      elif key in (pygame.K_UP, pygame.K_w):
        self.report_scroll = max(0.0, getattr(self, 'report_scroll', 0.0) - 46)

  def turn_page(self, d):
    """flip the Monster Manual one spread forward (+1) or back (-1)"""
    self.en_page += d
    self.en_flip = (d, pygame.time.get_ticks())
    AUDIO.play('click')

  def set_volume_from(self, k, x):
    """slider dragged/tapped: x position -> 0-100"""
    x0, x1, _y = slider_track(OPT_RECTS[k])
    v = int(round(max(0.0, min(1.0, (x - x0) / float(x1 - x0))) * 100))
    self.data['music_vol' if k == 'music' else 'sfx_vol'] = v
    self.apply_volumes()

  def apply_volumes(self):
    d = self.data
    d['music'] = d.get('music_vol', 100) > 0
    d['sfx'] = d.get('sfx_vol', 100) > 0
    AUDIO.set_levels(d.get('music_vol', 100) / 100.0, d.get('sfx_vol', 100) / 100.0)
    AUDIO.set_music(d['music'])
    AUDIO.set_sfx(d['sfx'])

  def option_action(self, k):
    AUDIO.play('click')
    d = self.data
    if k == "music":
      d['music'] = not d.get('music', True)
      AUDIO.set_music(d['music'])
    elif k == "sfx":
      d['sfx'] = not d.get('sfx', True)
      AUDIO.set_sfx(d['sfx'])
      if d['sfx']:
        AUDIO.play('click')
    elif k == "display":
      self.set_fullscreen(not self.fullscreen)
      d['fullscreen'] = self.fullscreen
    elif k == "difficulty":
      d['difficulty'] = 'hard' if d.get('difficulty', 'easy') == 'easy' else 'easy'
    elif k == "shake":
      d['shake'] = not d.get('shake', True)
      if not d['shake']:
        self.shake_t = 0
    elif k == "vibrate":
      d['vibrate'] = not d.get('vibrate', True)
      if d['vibrate']:
        self.buzz(60)
    elif k == "weather":
      d['weather'] = not d.get('weather', True)
      if not d['weather']:
        self.wx_kind, self.wx_parts, self.flash, self.bolt = "clear", [], 0, None
        self.day = ensure_day_assets()
      else:
        self.init_weather()
    save_data(d)

  def toggle_sound(self):
    on = not AUDIO.enabled
    self.data['sound'] = on
    save_data(self.data)
    AUDIO.set_enabled(on)
    AUDIO.play('click')

  def flap(self):
    if self.dash_state == 'out':
      return
    if self.selected == "EAGLE" and self.breath and self.state == "PLAYING":   # Talon Strike: every tap dives at the nearest foe
      self.talon_tap()
      return
    self.vel = FLAP_STRENGTH
    self.start_flap()
    AUDIO.play('flap', 0.7)

  def start_flap(self):
    """one full wing beat per tap, starting from the wings-up pose (a tap late in a beat starts a fresh one)."""
    rest, ln = flap_cycle(self.selected)
    if getattr(self, 'flap_left', 0.0) < ln * 0.55:
      self.flap_ph, self.flap_left = rest, ln

  def step_flap(self, running=False):
    rest, ln = flap_cycle(self.selected)
    if running or self.selected == "CHINESE":     # galloping (or a wingless serpent slithering): keeps moving
      self.flap_ph = getattr(self, 'flap_ph', rest) + ln / 34.0
      self.flap_left = 0.0
      return
    left = getattr(self, 'flap_left', 0.0)
    if left > 0:
      st = min(left, ln / 22.0)                   # a beat lasts about a third of a second
      self.flap_ph = getattr(self, 'flap_ph', rest) + st
      self.flap_left = left - st
      if self.flap_left <= 1e-6:
        self.flap_ph, self.flap_left = rest, 0.0  # settles back on the wings-up pose

  def tab_action(self, k):
    if k == 'home':
      AUDIO.play('click')
      self.state = "MENU"
    elif k == 'lair':
      AUDIO.play('click')
      self.state = "LAIR"
    else:
      self.menu_action(k)

  def menu_action(self, k):
    AUDIO.play('click')
    if k == "play":
      self.start_run()
    elif k == "hatchlings":
      self.state = "HATCHLINGS"
      self.hb_scroll, self.hb_drag = 0.0, None
    elif k == "eggs":
      self.state = "EGGS"
      self.egg_scroll, self.egg_drag = 0.0, None
    elif k == "enemies":
      self.state = "ENEMIES"
      self.en_scroll, self.en_drag = 0.0, None
    elif k == "lair":
      self.state = "LAIR"
    elif k == "worlds":
      self.state = "WORLDS"
    elif k == "roster":
      self.state = "SELECT"
    elif k == "hoard":
      self.state = "HOARD"
    elif k == "quests":
      self.state = "QUESTS"
    elif k == "options":
      self.opt_from = "MENU"
      self.state = "OPTIONS"
    elif k == "exit":
      self.quit()

  def map_pos(self, pos):
    """Touch/mouse position -> game coordinates (undoes letterboxing)."""
    sc, vx, vy = self.view
    if sc == 1.0 and not vx and not vy and self.view_sy == 1.0:
      return pos
    return (int((pos[0] - vx) / sc), int((pos[1] - vy) / self.view_sy))

  def display_is_full(self, surf):
    try:
      if surf.get_flags() & pygame.FULLSCREEN:
        return True
    except Exception:
      pass
    try:
      ww, wh = pygame.display.get_window_size()
      dw, dh = pygame.display.get_desktop_sizes()[0]
      return ww >= dw - 2 and wh >= dh - 2
    except Exception:
      return False

  def set_fullscreen(self, on, quiet=False):
    """Try a few fullscreen methods (phones are picky) and check which one really worked."""
    self.view = (1.0, 0, 0)
    self.view_sy = 1.0
    self.scale_buf = None
    if not on:
      try:
        self.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
      except Exception:
        pass
      self.fullscreen = False
      return
    for size, flags in (((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN),
              ((0, 0), pygame.FULLSCREEN)):
      try:
        surf = pygame.display.set_mode(size, flags)
      except Exception:
        continue
      if self.display_is_full(surf):
        self.surface = surf
        self.fullscreen = True
        return
    try:
      self.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    except Exception:
      pass
    self.fullscreen = False
    if not quiet:
      self.toast("Fullscreen isn't available here")

  def toast(self, msg):
    self.toast_msg, self.toast_t = msg, 150

  def present(self, ox, oy):
    surf = self.surface
    sw, sh = surf.get_size()
    if (sw, sh) == (WIDTH, HEIGHT):
      self.view = (1.0, 0, 0)
      self.view_sy = 1.0
      surf.blit(game_surface, (ox, oy))
    else:
      sc = min(sw / float(WIDTH), sh / float(HEIGHT))
      dw, dh = int(WIDTH * sc), int(HEIGHT * sc)
      vx, vy = (sw - dw) // 2, (sh - dh) // 2
      self.view = (sc, vx, vy)
      self.view_sy = sc
      buf = self.scale_buf
      if buf is None or buf.get_size() != (dw, dh):
        buf = self.scale_buf = pygame.Surface((dw, dh)).convert()
      try:
        pygame.transform.scale(game_surface, (dw, dh), buf)
      except Exception:
        buf = pygame.transform.scale(game_surface, (dw, dh))
      surf.blit(buf, (vx + int(ox * sc), vy + int(oy * sc)))
      if vx > 0 or vy > 0:
        try:
          if vx > 0:
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, 0, 1, HEIGHT)), (vx, dh)), (0, vy))
            surf.blit(pygame.transform.scale(game_surface.subsurface((WIDTH - 1, 0, 1, HEIGHT)), (sw - vx - dw, dh)), (vx + dw, vy))
          if vy > 0:
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, 0, WIDTH, 1)), (dw, vy)), (vx, 0))
            surf.blit(pygame.transform.scale(game_surface.subsurface((0, HEIGHT - 1, WIDTH, 1)), (dw, sh - vy - dh)), (vx, vy + dh))
        except Exception:
          surf.fill((0, 0, 0))
    pygame.display.flip()

  def pause(self):
    self.hold = False
    self.state = "PAUSED"
    self.confirm_menu = False

  def use_shield(self):
    if self.shields > 0 and not self.shield_active:
      self.shields -= 1
      self.shield_active = True
      self.shield_timer = 420
      AUDIO.play('shield')

  def try_dash(self):
    if self.dash_state != 'idle' or self.dash_cd > 0 or self.state != "PLAYING":
      return
    self.dash_state = 'out'
    self.dash_cd = DASH_COOLDOWN
    self.dash_boss = False
    self.dash_inv = 999
    self.vel = 0.0
    AUDIO.play('whoosh')
    AUDIO.play('roar', 0.5)
    self.shake_for(3, 6)

  def dash_target(self):
    return 150 + min(DASH_REACH, (WIDTH - 215) // 2)

  def update_dash(self):
    d = self.dragon
    if self.dash_cd > 0:
      self.dash_cd -= 1
    st = self.dash_state
    if st == 'idle':
      return
    tr = DRAGON_PALETTES[self.selected]['trail']
    if st == 'out':
      self.vel = 0.0
      for _ in range(3):
        self.emit(d.x + random.randint(0, 30), d.centery + random.randint(-18, 18), random.uniform(-6, -2), random.uniform(-1, 1), random.randint(8, 14), random.choice(tr))
      d.x += DASH_SPEED
      self.dash_sweep()
      if d.x >= self.dash_target():
        d.x = self.dash_target()
        self.dash_state = 'back'
        self.dash_inv = 45
    else:
      if self.dash_inv > 0:
        self.dash_inv -= 1
      d.x -= 3 if d.x - 150 > 60 else 2
      if d.x <= 150:
        d.x = 150
        self.dash_state = 'idle'
        self.dash_inv = 0

  def dash_sweep(self):
    d = self.dragon
    sw = pygame.Rect(d.x - 10, d.y - 22, d.w + 50, d.h + 44)
    hit = 0
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if o.get('shattered') or not sw.colliderect(o['rect']):
          continue
        o['shattered'] = True
        hit += 1
        cx, cy = o['rect'].center
        self.burst(cx, cy, 22, 6, 6, 14, FIRE_CORE)
        self.burst(cx, cy, 14, 5, 4, 10, DRAGON_PALETTES[self.selected]['main'])
        self.score += 10 * self.score_mult
        self.dp += 4
        self.bounty_add('shatter')
    for p in self.fireballs + self.arrows + self.orbs:
      if not p.get('shattered') and sw.colliderect(pygame.Rect(int(p['x'] - 14), int(p['y'] - 14), 28, 28)):
        p['shattered'] = True
        self.burst(p['x'], p['y'], 8, 4, 3, 8, FIRE_CORE)
    for p in self.spears:
      if not p.get('shattered') and sw.colliderect(pygame.Rect(int(p['x'] - 30), int(p['y'] - 12), 60, 24)):
        p['shattered'] = True
        self.burst(p['x'], p['y'], 10, 5, 3, 9, FIRE_CORE)
    b = self.boss
    if b and b.get('fwaves'):
      for w in b['fwaves']:
        if sw.colliderect(pygame.Rect(int(w['x'] - 10), int(w['y'] - 55), 30, 110)):
          w['x'] = -999.0
          self.burst(w['x'] + 999, w['y'], 10, 5, 4, 9, (255, 150, 40))
    if b and b['state'] == 'fighting' and not b.get('ghost') and not self.dash_boss and sw.colliderect(self.boss_rect(b)):
      self.dash_boss = True
      if b.get('sh', 0) > 0:
        b['hp'] += 30
        self.burst(d.right + 20, d.centery, 20, 6, 4, 10, (255, 90, 70))
      b['hp'] -= 30
      b['flash'] = 10
      self.burst(d.right + 20, d.centery, 30, 7, 6, 14, (255, 220, 120))
      self.dash_state = 'back'
      self.dash_inv = 45
    if hit:
      AUDIO.play('shatter', 0.8)
      self.shake_for(6, 8)

  def update(self):
    st = self.state
    self.update_hatching()
    self._ntick = getattr(self, '_ntick', 0) + 1
    if self._ntick % 60 == 0 and st != "ROOSTS":
      self.check_egg_notify()
    if self.state == "HATCHLINGS":
      self.update_den()
    if self.pet_react > 0:
      self.pet_react -= 1
    AUDIO.set_muffled(self.state == "PAUSED" or (self.state == "OPTIONS" and self.opt_from == "PAUSED"))
    AUDIO.tick()
    if st != "PLAYING":
      AUDIO.set_loop('breath', None)
      AUDIO.set_loop('weather', None)
    if st == "PAUSED":
      return
    self.anim += 0.05
    if self.shake_t > 0:
      self.shake_t -= 1

    playing = st in ("PLAYING", "INTRO")
    self.far_x += self.scroll * 0.1 if playing else 0.05
    self.near_x += self.scroll * 0.2 if playing else 0.10
    self.mid_x += self.scroll * 0.4 if playing else 0.2
    for c in self.clouds:
      c[0] -= c[3] if playing else c[3] * 0.2
      if c[0] < -220:
        c[0], c[1], c[2] = WIDTH + 50, random.randint(20, 220), random.randint(0, 99)
    for m in self.mist:
      m[0] -= m[2] * self.scroll * 0.1 if playing else 0.5
      if m[0] < -60:
        m[0] = WIDTH + 10

    if st == "INTRO":
      self.update_intro()
      self.update_scenery(self.scroll_px, 10)
    elif playing:
      self.update_playing()
      self.update_scenery(self.scroll_px, max(4, 10 - self.threat // 2))
    elif st == "GAMEOVER":
      dd = getattr(self, 'death', None)
      if dd and not dd.done:
        dd.update(self)                           # the results panel waits for the death animation
      else:
        self.over_t += 1
      self.vel += BASE_GRAVITY
      self.dragon.y = min(self.dragon.y + int(self.vel), GROUND_Y - self.dragon.height + 8)
      self.update_scenery(0, 99)
    else:
      self.update_scenery(1, 24)
      if st == "MENU":
        self.update_menu_fx()
    self.update_particles()

  def fill_tower_pool(self, want):
    """pre-paint towers during the countdown (they are detailed, slow-ish to paint) so spawning never hitches.
    The pool is kept for the whole session; towers are picked from it at random."""
    if len(TOWER_POOL) < want:
      h = random.randint(170, 340)
      TOWER_POOL.append((h, tower_art(h, random.choice([BANNER_GOLD, BANNER_BLUE, CLOTH_RED]))))
      return True
    return False

  def update_intro(self):
    self.intro_t += 1
    if self.intro_t % 3 == 0 and not self.fill_tower_pool(12):
      prewarm_step(self.intro_t // 3)                # then unpack enemy animations ahead of time
    self.update_weather()
    self.wing += 0.38
    self.flap_ph = getattr(self, 'flap_ph', 0.0) + flap_cycle(self.selected)[1] / 34.0   # flaps on its own during the countdown
    self.dragon.y = HEIGHT // 2 + int(math.sin(self.intro_t * 0.07) * 14)
    self.vel = 0.0
    t = self.intro_t
    if t in (1, 61, 121):
      AUDIO.play('click')
    elif t == 181:
      AUDIO.play('roar', 0.8)
      self.shake_for(3, 12)
    if t >= INTRO_FRAMES:
      self.dragon.y = HEIGHT // 2
      self.state = "PLAYING"

  def update_menu_fx(self):
    for e in self.embers:
      e[1] -= e[2]
      e[0] += math.sin(self.anim * 2 + e[4]) * 0.4
      if e[1] < -10:
        e[:] = self.new_ember()
    self.menu_dragon_x += 2.2
    if self.menu_dragon_x > WIDTH + 140:
      self.menu_dragon_x = -140.0
    if int(self.anim * 20) % 2 == 0:
      tr = DRAGON_PALETTES[self.selected]['trail']
      my = 320 + math.sin(self.anim * 1.3) * 45
      if self.selected == "COSMIC":
        self.emit_star(self.menu_dragon_x + 4, my + 24, -1.0)
      else:
        self.emit(self.menu_dragon_x + 4, my + 24, random.uniform(-2.5, -0.5), random.uniform(-1, 1), random.randint(5, 9), random.choice(tr))

  def emit_star(self, x, y, vx):
    """Void dragon trail: twinkling little stars that drift and fade"""
    st = self.__dict__.setdefault('stars', [])
    if len(st) < 90:
      st.append([x + random.uniform(-4, 4), y + random.uniform(-8, 8), vx + random.uniform(-1.2, 0.3), random.uniform(-0.4, 0.4),
                 random.randint(28, 46), random.choice(((255, 255, 255), (225, 200, 255), (175, 220, 255), (255, 175, 240))), random.random() < 0.45])

  def update_particles(self):
    st = getattr(self, 'stars', None)
    if st:
      for p in st:
        p[0] += p[2]; p[1] += p[3]; p[4] -= 1
      self.stars = [p for p in st if p[4] > 0]
    alive = []
    for p in self.particles:
      p[0] += p[2]
      p[1] += p[3]
      p[4] -= 0.30
      if p[4] >= 1:
        alive.append(p)
    self.particles = alive

  def update_glide(self, d):
    """Tap = flap. Hold = glide (no gravity); slide finger up/down to climb (slows the world) or dive (speeds it up)."""
    if self.hold and self.dash_state != 'out':
      self.hold_t += 1
    else:
      self.hold_t = 0
    glide = self.hold_t >= GLIDE_DELAY
    if glide:
      fy = self.mouse[1]
      if not self.gliding:
        self.gliding = True
        self.glide_y0, self.glide_f0 = float(d.y), float(fy)
      self.glide_y0 += GLIDE_SINK
      want = self.glide_y0 + (fy - self.glide_f0)
      lo, hi = 50.0, float(GROUND_Y - 70)
      if want < lo or want > hi:                       # finger ran past the limit: re-anchor so it responds at once
        want = max(lo, min(hi, want))
        self.glide_y0, self.glide_f0 = want, float(fy)
      goal = max(-GLIDE_UP, min(GLIDE_DOWN, (want - d.y) * 0.22))
      self.vel = self.vel * 0.6 + goal * 0.4 + self.gust * 0.3
      self.track_circle(fy)
    else:
      self.gliding = False
      self.trail = []
      self.vel += self.gravity + self.gust
    if self.flip_t > 0:
      self.flip_t += 1
      if self.flip_t > FLIP_FRAMES:
        self.flip_t = 0
    if self.gliding:
      tgt = 1.0 + 0.075 * self.vel if self.vel > 0 else 1.0       # diving speeds the world up; climbing never slows it
    else:
      tgt = 1.0
    self.glide_mult += (tgt - self.glide_mult) * 0.12

  def track_circle(self, fy):
    """Watch the held finger: a full circle clockwise = front flip, counter-clockwise = back flip."""
    if self.flip_t > 0:
      self.trail = []
      return
    self.trail.append((float(self.mouse[0]), float(fy)))
    if len(self.trail) > 50:
      self.trail.pop(0)
    n = len(self.trail)
    if n < 16:
      return
    cx = sum(p[0] for p in self.trail) / n
    cy = sum(p[1] for p in self.trail) / n
    rad = [math.hypot(p[0] - cx, p[1] - cy) for p in self.trail]
    mean_r = sum(rad) / n
    if mean_r < 10 or min(rad) < mean_r * 0.35:
      return
    tot, prev = 0.0, None
    for p in self.trail:
      a = math.atan2(p[1] - cy, p[0] - cx)
      if prev is not None:
        da = a - prev
        while da > math.pi:
          da -= 2 * math.pi
        while da < -math.pi:
          da += 2 * math.pi
        tot += da
      prev = a
    if abs(tot) >= math.radians(300):
      self.flip_t = 1
      self.flip_dir = 1 if tot > 0 else -1
      self.trail = []
      AUDIO.play('whoosh', 0.6)

  def update_playing(self):
    sel, d = self.selected, self.dragon
    self.compute_params()
    sc = self.scroll_px
    self.update_glide(d)
    self.update_weather()
    AUDIO.set_loop('weather', WEATHER_LOOP.get(self.wx_kind))
    AUDIO.set_loop('breath', BREATH_LOOP.get(sel, 'fire') if self.breath else None)
    d.y += int(self.vel)
    rs = getattr(self, 'run_stats', None)
    if rs is not None:
      rs['dist'] += sc
      rs['ticks'] += 1
      q = self.bounty
      if q and not q.get('done') and q['type'] in ('distance', 'score'):
        q['progress'] = max(q['progress'], int(rs['dist'] / PX_PER_M) if q['type'] == 'distance' else int(self.score))
    self.update_dash()
    self.update_talon()
    self.running = False
    if sel == "UNICORN" and d.bottom >= GROUND_Y - UNI_HOOF:   # the Evil Unicorn lands and gallops instead of crashing
      d.bottom = GROUND_Y - UNI_HOOF
      self.vel = min(self.vel, 0.0)
      self.running = True
      if random.random() < 0.5:                  # kicked-up dust
        self.emit(d.x + random.randint(0, 60), GROUND_Y - 4, random.uniform(-4, -1.5), random.uniform(-1.6, -0.3), random.randint(4, 7),
                  random.choice(((150, 130, 110), (110, 96, 84), (190, 170, 150))))
    self.wing += 0.1 if (self.gliding and not self.running) else 0.38     # (world animation clock)
    self.step_flap(self.running)
    self.pitch = 0.0 if self.running else max(-18.0, min(self.vel * 2.2, 28.0))
    self.dead = False
    self.bolts = []

    if not self.boss and not self.towers:
      if self.score >= BOSS_SCORES[0] and not self.b1:
        self.boss = {'type': 'griffin', 'x': WIDTH + 100.0, 'y': HEIGHT // 2, 'hp': 150.0, 'max_hp': 150.0, 'timer': 0.0, 'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 80, 'seq': 0, 'waves': []}
        AUDIO.play('roar')
      elif self.score >= BOSS_SCORES[1] and not self.b2:
        self.boss = {'type': 'phoenix', 'x': WIDTH + 120.0, 'y': HEIGHT // 2 - 90.0, 'by': HEIGHT // 2 - 90.0, 'hp': 340.0, 'max_hp': 340.0, 'timer': 0.0, 'state': 'entering',
                     'atk': 'idle', 'at': 0, 'cool': 70, 'seq': 0, 'fwaves': [], 'flash': 0, 'hurt': 0, 'lives': 1, 'dt': 0, 'alpha': 255, 'ghost': False}
        AUDIO.play('roar')
      elif self.score >= BOSS_SCORES[2] and not self.b6:
        self.boss = {'type': 'beholder', 'x': WIDTH + 150.0, 'y': HEIGHT // 2 - 110.0, 'by': HEIGHT // 2 - 110.0, 'hp': 420.0, 'max_hp': 420.0, 'timer': 0.0,
                     'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 60, 'seq': 0, 'fi': 0, 'anim': 'hover', 'flash': 0, 'hurt': 0, 'dt': 0, 'alpha': 255,
                     'ghost': False, 'ray': False, 'ang': math.pi}
        AUDIO.play('roar')
      elif self.score >= BOSS_SCORES[3] and not self.b3:
        self.boss = {'type': 'jabber', 'x': WIDTH + 160.0, 'y': HEIGHT // 2 - 100.0, 'by': HEIGHT // 2 - 100.0, 'hp': 480.0, 'max_hp': 480.0, 'timer': 0.0,
                     'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 60, 'seq': 0, 'fi': 0, 'flash': 0, 'hurt': 0, 'dt': 0, 'alpha': 255, 'ghost': False,
                     'beam': None, 'ang': math.pi, 'spit_t': -99}
        AUDIO.play('roar')
      elif self.score >= BOSS_SCORES[4] and not self.b4:
        self.boss = {'type': 'demon', 'x': WIDTH + 150.0, 'y': HEIGHT // 2 - 60.0, 'hp': 640.0, 'max_hp': 640.0, 'timer': 0.0, 'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 60, 'sh': 0, 'fwaves': [], 'by': HEIGHT // 2 - 60.0, 'ghost': False, 'hurt': 0, 'flash': 0, 'dt': 0, 'seq': 0, 'alpha': 255}
        AUDIO.play('roar')
      elif self.score >= BOSS_SCORES[5] and not self.b5 and self.b4:
        self.boss = {'type': 'hydra', 'x': WIDTH + 170.0, 'y': HEIGHT // 2 - 110.0, 'by': HEIGHT // 2 - 110.0, 'hp': 760.0, 'max_hp': 760.0, 'timer': 0.0,
                     'state': 'entering', 'atk': 'idle', 'at': 0, 'cool': 60, 'seq': 0, 'fi': 0, 'anim': 'fly', 'flash': 0, 'hurt': 0, 'dt': 0, 'alpha': 255,
                     'ghost': False}
        AUDIO.play('roar')

    if self.shield_active:
      self.shield_timer -= 1
      if self.shield_timer <= 0:
        self.shield_active = False
    if sel == "SKELETAL" and self.shields < self.max_shields:
      self.dp += 0.15
    if self.dp >= 100:
      if self.shields < self.max_shields:
        self.shields += 1
        self.dp -= 100
        self.shake_for(5, 10)
        self.burst(d.centerx, d.centery, 20, 5, 10, 15, ICE_BLUE)
      else:
        self.dp = 100

    hx, hy = breath_origin(sel, d, getattr(self, 'flap_ph', 0.0), self.vel, self.pitch)
    if not self.breath:
      self.beam_len = 0
      if getattr(self, 'siphon', None) is not None:
        self.siphon_release()
    if self.breath:
      self.breath_timer -= 1
      if self.breath_timer <= 0:
        self.breath = False
      if sel == "YELLOW":
        pass                                   # chain lightning is built in update_breath
      else:
        cols = BREATH_COLORS.get(sel, DEFAULT_BREATH)
        for _ in range(0 if sel in ("RED", "BLUE", "GREEN", "SILVER", "COSMIC", "SKELETAL", "UNICORN", "WRAITH", "CHINESE", "CLOCKWORK", "FOREST", "COCKATRICE", "WHALE", "FEY", "ALIEN", "EAGLE") else 4):
          if sel == "SILVER":
            self.emit(hx, hy + random.randint(-20, 20), random.uniform(15, 25), random.uniform(-1, 1), random.randint(8, 14), random.choice(cols))
          else:
            self.emit(hx, hy + random.randint(-12, 18), random.uniform(10, 17), random.uniform(-3.5, 3.5), random.randint(10, 20), random.choice(cols))
    else:
      tr = DRAGON_PALETTES[sel]['trail']
      if sel == "COSMIC":
        self.emit_star(d.x + 4, d.centery + 4 + int(self.pitch * 0.3), -2.0)
      elif sel == "CHINESE":                      # crackling sparks
        for _ in range(2):
          self.emit(d.x + 6 + random.randint(-6, 10), d.centery + random.randint(-14, 14), random.uniform(-4.5, -1.0), random.uniform(-2.2, 2.2),
                    random.randint(2, 5), random.choice(((255, 240, 150), (255, 255, 255), (255, 190, 60), (255, 120, 40))))
      elif sel == "COCKATRICE":                   # loose feathers
        if random.random() < 0.35:
          self.emit(d.x + random.randint(0, 40), d.centery + random.randint(-12, 10), random.uniform(-3, -1), random.uniform(0.2, 1.2), random.randint(4, 6),
                    random.choice(((200, 60, 40), (230, 140, 50), (120, 140, 50), (250, 210, 120))))
      elif sel == "FOREST":                       # falling leaves
        if random.random() < 0.5:
          self.emit(d.x + random.randint(0, 40), d.centery + random.randint(-14, 10), random.uniform(-3, -1), random.uniform(0.2, 1.4), random.randint(4, 7),
                    random.choice(((110, 170, 40), (150, 200, 60), (190, 160, 50), (90, 130, 30))))
      elif sel == "CLOCKWORK":                    # steam puffs from its joints
        if random.random() < 0.6:
          self.emit(d.x + random.randint(4, 30), d.centery + random.randint(-12, 6), random.uniform(-2.5, -0.8), random.uniform(-1.4, -0.2),
                    random.randint(6, 11), random.choice(((210, 210, 210), (170, 170, 175), (240, 240, 240))))
        if random.random() < 0.12:
          self.emit(d.x + 20, d.centery, random.uniform(-3, -1), random.uniform(-1, 1), 3, (255, 200, 90))
      elif sel == "WHALE":                        # stardust shed from its tail
        if random.random() < 0.6:
          self.emit_star(d.x - 30 + random.randint(-6, 6), d.centery + 10 + random.randint(-10, 10), -2.2)
      elif sel == "FEY":                          # fairy glitter
        if random.random() < 0.7:
          self.emit(d.x + random.randint(-4, 24), d.centery + random.randint(-16, 14), random.uniform(-2.6, -0.8), random.uniform(-0.6, 0.6), random.randint(2, 5),
                    random.choice(((255, 150, 240), (140, 240, 255), (255, 255, 200), (255, 255, 255))))
      elif sel == "UNICORN":                      # a rainbow streak behind it
        self.emit(d.x + 4, d.centery - 2 + int(self.pitch * 0.3), random.uniform(-3.5, -1.5), random.uniform(-0.5, 0.5), random.randint(5, 9), random.choice(RAINBOW))
      else:
        self.emit(d.x + 4, d.centery + 4 + int(self.pitch * 0.3), random.uniform(-3.5, -1), random.uniform(-1, 1), random.randint(6, 11), tr[0] if random.random() > 0.4 else tr[1])

    if not self.boss:
      self.spawn_t += 1
      if self.spawn_t > max(35, 75 - self.threat * 5):
        self.spawn_t = 0
        self.spawn_enemy()
    self.power_t += 1
    if self.power_t > 340:
      self.power_t = 0
      self.powerups.append({'rect': pygame.Rect(WIDTH, random.randint(120, 380), 34, 34), 't': 0.0, 'ry': 0})
    if random.random() < 0.02 and not self.boss:
      self.coins.append({'rect': pygame.Rect(WIDTH, random.randint(100, 400), 20, 20), 't': random.uniform(0, 5), 'ry': 0})

    self.update_items()
    if self.breath:
      self.update_breath()
    self.update_rubble()
    self.update_corpses()
    self.update_holes()
    self.update_curse()
    self.update_souls()
    self.update_missiles()
    self.update_vines()
    self.update_leaves()
    self.update_eggs_shot()
    self.update_novas()
    self.update_heart_drop()

    self.update_tornados()
    self.update_egg_drop()
    self.update_pet()
    if sel in ("RED", "GREEN", "ALIEN"):
      self.update_lava(hx, hy)
    self.update_boss()

    for name in GROUND_LISTS:
      for o in getattr(self, name):
        r, ost = o['rect'], o['state']
        if ost == 'blown':
          r.x += 15
          r.y -= 2
        else:
          r.x -= sc
        if ost == 'stasis':
          o['st'] = o.get('st', STASIS_FRAMES) - 1
          if o['st'] <= 0:
            o['state'] = ost = 'normal'
        falling = self.perch_check(o) if (o.get('perch') is not None or o.get('fall') is not None) else False
        if ost == 'normal' and not o.get('shattered') and r.x < WIDTH - 50 and not falling and not o.get('curse') and not o.get('drain'):
          self.unit_ai(name, o)                     # (cursed foes are too busy withering to attack)
        if ost == 'frozen' and not o.get('shattered') and d.colliderect(r):
          self.shatter_frozen(o)
        if ost == 'normal' and not o.get('shattered') and not o.get('curse') and not o.get('drain') and d.colliderect(r):
          self.hit_dragon(o, melee=True)
        if r.right < d.x and not o.get('passed'):
          o['passed'] = True
          self.score += 10 * self.score_mult
          self.bounty_add('dodge')

    for e in self.enemies:
      r, ost = e['rect'], e['state']
      if ost == 'blown':
        e['fx'] += 15
        r.y -= 2
      elif ost == 'spun':
        pass
      elif ost in STUCK_STATES:
        e['fx'] -= sc
        e['vy'] += BASE_GRAVITY * 1.5
        r.y += int(e['vy'])
        if r.bottom >= GROUND_Y:
          r.bottom = GROUND_Y
          e['vy'] = 0
          if ost == 'frozen':
            self.shatter_frozen(e)
      elif ost == 'stasis':
        e['st'] = e.get('st', STASIS_FRAMES) - 1
        if e['st'] <= 0:
          e['state'] = 'normal'
      elif e.get('drain'):                             # held fast by the Soul Siphon
        e['fx'] -= 0.6 * self.ts
      elif e.get('foe') == 'witch' and not e.get('curse'):
        self.witch_ai(e)
      elif e.get('foe') in ('moth', 'bat'):
        if not e.get('curse'):
          self.night_ai(e)
        else:
          e['fx'] -= 1.0 * self.ts
      elif e.get('foe') == 'spider':                   # drifts down diagonally on its silk
        e['age'] += self.ts
        e['fx'] += e['vx'] * self.ts
        e['fy'] += e['vy'] * self.ts
        r.y = int(e['fy'])
        if r.top > GROUND_Y + 10:
          e['shattered'] = e['gone'] = True         # (fell off the bottom: not a kill)
      else:
        sp = e['speed']
        ds = e.get('ds', -1)
        if ds == 0:
          if d.centerx + 260 < r.x < WIDTH - 140:
            e['ds'] = 1
            e['dt'] = 0.0
        elif ds == 1:
          e['dt'] += self.ts
          sp *= 0.25
          if e['dt'] > 42:
            e['ds'] = 2
            e['ty'] = d.centery - r.h // 2
            AUDIO.play('whoosh', 0.5)
        elif ds == 2:
          sp *= 2.0
          r.y += int((e['ty'] - r.y) * 0.06)
          self.emit(r.right, r.centery, random.uniform(1, 4), random.uniform(-1, 1), random.randint(5, 9), (255, 120, 60))
        e['fx'] -= sp * self.ts
      r.x = int(e['fx'])
      if ost == 'normal' and e.get('kind') == 'wyvern':
        e['age'] += self.ts
        r.y = int(e['by'] + math.sin(e['age'] * 0.12 + e['wph']) * 30)
      if ost == 'frozen' and not e.get('shattered') and d.colliderect(r):
        self.shatter_frozen(e)
      if ost == 'normal' and not e.get('shattered') and not e.get('curse') and not e.get('drain') and d.colliderect(r):
        self.hit_dragon(e, melee=True)
      if r.right < d.x and not e.get('passed'):
        e['passed'] = True
        self.score += (2 if e.get('kind') == 'wyvern' else (3 if e.get('foe') in ('imp', 'spider') else 10)) * self.score_mult

    for o in self.orbs:
      ost = o['state']
      if ost == 'blown':
        o['x'] += 15
        o['y'] -= 2
      elif ost in STUCK_STATES:
        o['vy'] = o.get('vy', 0) + BASE_GRAVITY * 1.5
        o['y'] += int(o['vy'])
        o['shattered'] = o['y'] >= GROUND_Y
      elif ost == 'stasis':
        o['st'] = o.get('st', STASIS_FRAMES) - 1
        if o['st'] <= 0:
          o['state'] = 'normal'
      elif o.get('kind') == 'seeker':                # Beholder's eyeballs: turn toward you and chase you down
        o['life'] = o.get('life', 0) + 1
        a = math.atan2(o['vy'], o['vx'])
        want = math.atan2(d.centery - o['y'], d.centerx - o['x'])
        da = (want - a + math.pi) % (2 * math.pi) - math.pi
        a += max(-0.075, min(0.075, da)) if o['life'] > 10 else 0.0
        o['spd'] = min(8.0, o.get('spd', 4.5) + 0.035)
        o['vx'], o['vy'] = math.cos(a) * o['spd'], math.sin(a) * o['spd']
        o['x'] += o['vx'] * self.ts
        o['y'] += o['vy'] * self.ts
        if o['life'] > 280 or o['y'] > GROUND_Y - 4:  # pops when it tires out
          o['shattered'] = True
          self.burst(o['x'], o['y'], 8, 3, 3, 6, (90, 255, 120))
      else:
        o['x'] += o['vx'] * self.ts
        if o['x'] > d.x and o.get('home', True):
          o['vy'] += (d.centery - o['y']) * 0.005 * self.ts
        o['y'] += o['vy'] * self.ts
      orr = int(o.get('r', 10) * 0.9)
      if ost == 'normal' and d.colliderect(pygame.Rect(int(o['x'] - orr), int(o['y'] - orr), orr * 2, orr * 2)):
        if not self.shield_active:
          self.dead = True
        else:
          o['shattered'] = True
      if self.state == "PLAYING" and not o.get('shattered'):
        self.emit(o['x'], o['y'], random.uniform(0, 2), random.uniform(-1, 1), random.randint(4, 8), o.get('col', MAGIC_PURPLE))

    for sp in self.spears:
      sp['x'] += sp['vx'] * self.ts
      sp['y'] += sp['vy'] * self.ts
      L = math.hypot(sp['vx'], sp['vy']) or 1.0
      for k in (0, 22, 44, 66):
        px, py = sp['x'] - sp['vx'] / L * k, sp['y'] - sp['vy'] / L * k
        if d.colliderect(pygame.Rect(int(px - 7), int(py - 7), 14, 14)):
          self.dead = True                    # unblockable
          break
      if sp['x'] < -120 or sp['y'] < -100 or sp['y'] > HEIGHT + 100:
        sp['shattered'] = True

    for lst, is_fire in ((self.fireballs, True), (self.arrows, False)):
      for p in lst:
        ost = p['state']
        if ost == 'blown':
          p['x'] += 15
          p['y'] -= 4
        elif ost in STUCK_STATES:
          p['vy'] = p.get('vy', 0) + BASE_GRAVITY * 1.5
          p['y'] += int(p['vy'])
          p['shattered'] = p['y'] >= GROUND_Y
        elif ost == 'stasis':
          p['st'] = p.get('st', STASIS_FRAMES) - 1
          if p['st'] <= 0:
            p['state'] = 'normal'
        else:
          ts = self.ts
          if is_fire and p.get('straight'):
            pass
          elif is_fire:
            p['vx'] -= 0.02 * ts
            p['vy'] += FIREBALL_GRAVITY * ts
          elif p.get('kind') in ('boulder', 'log'):
            p['vy'] += FIREBALL_GRAVITY * ts
            p['rot'] = p.get('rot', 0.0) + 0.25 * ts
          elif p.get('kind') not in ('feather', 'icicle'):
            p['vy'] += FIREBALL_GRAVITY * 0.5 * ts
          p['x'] += p['vx'] * ts
          p['y'] += p['vy'] * ts
        if is_fire and self.state == "PLAYING" and not p.get('shattered'):
          self.emit(p['x'], p['y'], random.uniform(1, 3), random.uniform(-1, 2), random.randint(6, 12), (240, random.randint(60, 130), 10))
        pr = pygame.Rect(int(p['x'] - 11), int(p['y'] - 11), 22, 22) if is_fire else (pygame.Rect(int(p['x'] - 9), int(p['y'] - 5), 18, 10) if p.get('kind') in ('feather', 'icicle', 'icicle_fall') else (pygame.Rect(int(p['x'] - 17), int(p['y'] - 17), 34, 34) if p.get('kind') == 'boulder' else (pygame.Rect(int(p['x'] - 24), int(p['y'] - 12), 48, 24) if p.get('kind') == 'log' else pygame.Rect(int(p['x'] - 15), int(p['y'] - 2), 30, 4))))
        if d.colliderect(pr) and ost == 'normal':
          if is_fire and sel == "RED":
            p['shattered'] = True
            self.score += 5
            self.emit(p['x'], p['y'], random.uniform(-3, 3), random.uniform(-3, 3), random.randint(8, 15), FIRE_CORE)
          elif not self.shield_active:
            self.dead = True
          else:
            p['shattered'] = True
        elif pr.right < d.x and not p.get('passed'):
          p['passed'] = True
          self.bounty_add('dodge')

    if self.hit_inv > 0:
      self.hit_inv -= 1
    if self.dash_inv > 0 or self.hit_inv > 0:
      self.dead = False
    elif self.dead and self.hearts > 0:
      self.take_heart()
    for name in ('archers', 'mages', 'enemies', 'cyclopes', 'golems'):   # killed enemies play their death animation
      for o in getattr(self, name):
        if o.get('shattered') and not o.get('corpse') and not o.get('swallowed') and o.get('state') != 'frozen' and o['rect'].right > 0:
          o['corpse'] = True
          self.make_corpse(name, o)
    for o in self.towers:                           # every destroyed tower crumbles into falling bricks
      if o.get('state') in ('blown', 'spun') and not o.get('shattered'):
        o['shattered'] = True
        self.score += 15 * self.score_mult
      if o.get('shattered') and not o.get('crumbled'):
        self.crumble_fx(o)
    rs = getattr(self, 'run_stats', None)
    for name in GROUND_LISTS + ('enemies',):          # tally every foe defeated this run (for quests and the aftermath report)
      for o in getattr(self, name):
        if o.get('shattered') and not o.get('tallied') and not o.get('gone'):
          o['tallied'] = True
          kk = self.kill_key(name, o)
          if rs is not None:
            rs['kills'][kk] = rs['kills'].get(kk, 0) + 1
          self.bounty_add('kill', kk)
    for name in GROUND_LISTS + ('enemies',):
      setattr(self, name, [o for o in getattr(self, name) if not o.get('shattered') and o['rect'].right > 0 and o['rect'].x < WIDTH + 400])
    self.arrows = [a for a in self.arrows if not a.get('shattered') and -50 < a['x'] < WIDTH + 400 and a['y'] < HEIGHT + 50]
    self.fireballs = [f for f in self.fireballs if not f.get('shattered') and f['y'] < HEIGHT + 50 and -100 < f['x'] < WIDTH + 400]
    self.orbs = [o for o in self.orbs if not o.get('shattered') and o['y'] < HEIGHT + 50 and -100 < o['x'] < WIDTH + 400]
    self.spears = [s for s in self.spears if not s.get('shattered')]

    q = self.bounty
    if q and q['progress'] >= q['target'] and not q.get('done'):
      q['done'] = True
      self.data['completed_quests'] += 1
      save_data(self.data)
      self.score += 100
      gold = quest_gold(q)
      self.data['coins'] += gold
      save_data(self.data)
      self.toast("BOUNTY COMPLETE!  +%d GOLD" % gold)
      if rs is not None:
        rs['quests'].append((q['desc'], gold))
      AUDIO.play('quest')
      if self.shields < self.max_shields:
        self.shields += 1
      self.shake_for(5, 15)

    if d.top < -25 or d.bottom > GROUND_Y + 1:
      if not self.shield_active:
        if self.hearts > 0:
          if self.hit_inv <= 0:
            self.take_heart()
            self.dead = False
          if d.bottom > GROUND_Y + 1:
            d.bottom = GROUND_Y - 6
            self.vel = FLAP_STRENGTH
            self.start_flap()
          if d.top < -25:
            d.top = -25
            self.vel = 0
        else:
          self.dead = True
      else:
        if d.bottom > GROUND_Y + 1:
          d.bottom = GROUND_Y + 1
          self.vel = FLAP_STRENGTH
          self.start_flap()
        if d.top < -25:
          d.top = -25
          self.vel = 0

    if self.dead:
      self.die()

  def buzz(self, ms):
    if self.data.get('vibrate', True):
      vibrate(ms)

  def take_heart(self):
    self.buzz(120)
    self.hearts -= 1
    if getattr(self, 'run_stats', None) is not None:
      self.run_stats['hearts_lost'] += 1
    self.dead = False
    self.hit_inv = 100
    d = self.dragon
    self.burst(d.centerx, d.centery, 22, 6, 6, 12, (255, 60, 70))
    self.shake_for(8, 12)
    AUDIO.play('shatter', 0.8)

  def die(self):
    if self.egg_drop:                               # an egg you earned is never lost
      self.collect_egg()
    self.buzz(350)
    AUDIO.play('die')
    self.state = "GAMEOVER"
    self.over_t = 0
    self.pet_gain_xp()
    data = self.data
    data['coins'] += int(self.run_coins)
    self.new_record = self.score > data['high_score']
    if self.new_record:
      data['high_score'] = self.score
    save_data(data)
    d = self.dragon
    self.burst(d.centerx, d.centery, 14, 5, 5, 10, FIRE_CORE)
    self.shake_for(12, 20)
    self.bolts = []
    self.vel = -4.0
    self.breath = False
    try:                                            # dragon rears up, burns and crumbles to ash
      if has_sheet(self.selected):
        from fd_death import SheetDeath
        self.death = SheetDeath(self.selected, d.x - PX.OX, d.y - PX.OY, GROUND_Y)
      elif self.selected == "SKELETAL":
        from fd_death import BoneDeath
        self.death = BoneDeath(d.x - PX.OX, d.y - PX.OY, GROUND_Y)
      else:
        spr = dragon_sprite(self.selected, PX.frame_index(self.flap_ph), 0, False)
        self.death = DragonDeath(spr, self.selected, d.center, (PX.OX + 32, PX.OY + 19), GROUND_Y)
    except Exception:
      self.death = None

  # ------------------------------------------------------------------ hatchlings (companions)
  def pet_defaults(self, bb):
    bb.setdefault('type', OLD_BABY_TYPE.get(bb.get('r'), 'GREEN'))
    bb.setdefault('name', random.choice(BABY_NAMES))
    bb.setdefault('xp', 0)
    bb.setdefault('level', 1)
    bb.setdefault('happy', 70.0)
    bb.setdefault('happy_t', time.time())
    return bb

  def find_pet(self, pid):
    if pid is None:
      return None
    for bb in self.data.get('babies', []):
      if bb.get('id') == pid:
        return self.pet_defaults(bb)
    return None

  def pet_happy(self, bb):
    return max(0.0, min(100.0, bb.get('happy', 70.0) - (time.time() - bb.get('happy_t', time.time())) / 3600.0 * PET_HAPPY_DECAY))

  def pet_need(self, level):
    return 60 + level * 40

  def pet_stage(self, level):
    return "Baby" if level < 5 else ("Juvenile" if level < PET_MAX_LEVEL else "Adult")

  def pet_scale(self, level):
    return 1.0 if level < 5 else (1.25 if level < PET_MAX_LEVEL else 1.5)

  def pet_power(self, bb):
    return PET_RARITY_POWER.get(bb['r'], 1.0) * (1 + 0.06 * (bb['level'] - 1)) * (0.6 + 0.4 * self.pet_happy(bb) / 100.0)

  def pet_feed(self, bb):
    if self.data['coins'] < PET_FEED_COST:
      self.toast("Not enough gold!")
      return
    self.data['coins'] -= PET_FEED_COST
    bb['happy'] = min(100.0, self.pet_happy(bb) + 25)
    bb['happy_t'] = time.time()
    save_data(self.data)
    AUDIO.play('coin')
    self.toast("%s loved that! Happiness %d%%" % (bb['name'], int(bb['happy'])))

  def pet_gain_xp(self):
    bb = getattr(self, 'pet', None)
    if not bb:
      return
    gain = max(5, self.score // 20) + getattr(self, 'run_bosses', 0) * 60
    bb['xp'] += gain
    msg = "%s earned %d XP" % (bb['name'], gain)
    old_stage = self.pet_stage(bb['level'])
    while bb['level'] < PET_MAX_LEVEL and bb['xp'] >= self.pet_need(bb['level']):
      bb['xp'] -= self.pet_need(bb['level'])
      bb['level'] += 1
      msg = "%s grew to level %d!" % (bb['name'], bb['level'])
    if self.pet_stage(bb['level']) != old_stage:
      msg = "%s is now %s %s!" % (bb['name'], "an" if self.pet_stage(bb['level'])[0] in "AE" else "a", self.pet_stage(bb['level']))
    if bb['level'] >= PET_MAX_LEVEL:
      bb['xp'] = 0
    save_data(self.data)
    self.toast(msg)

  def pet_targets(self):
    out = []
    for name in GROUND_LISTS + ('enemies',):
      if name == 'towers':
        continue
      for o in getattr(self, name):
        if not o.get('shattered') and o.get('state') == 'normal':
          out.append((o, name, o['rect'].center))
    b = self.boss
    if b and b['state'] == 'fighting' and not b.get('ghost') and b.get('atk') != 'dive':
      out.append((b, 'boss', self.boss_rect(b).center))
    return out

  def update_pet(self):
    """Companion hatchling: follows the dragon and spits little shots of its own element at foes ahead."""
    bb = self.pet
    if not bb:
      return
    d = self.dragon
    tx, ty = d.x - 62, d.y - 40 + math.sin(self.anim * 3) * 8
    self.pet_pos[0] += (tx - self.pet_pos[0]) * 0.12
    self.pet_pos[1] += (ty - self.pet_pos[1]) * 0.12
    if self.pet_atk > 0:
      self.pet_atk -= 1
    self.pet_cd -= self.pet_power(bb) * self.ts
    px, py = self.pet_pos[0] + 30, self.pet_pos[1] + 20
    if self.pet_cd <= 0:
      best, bd = None, 520.0
      for c in self.pet_targets():
        x, y = c[2]
        if x > px + 30:
          dd = math.hypot(x - px, y - py)
          if dd < bd:
            best, bd = c, dd
      if best:
        a = math.atan2(best[2][1] - py, best[2][0] - px)
        self.pet_shots.append({'x': px, 'y': py, 'vx': math.cos(a) * 11, 'vy': math.sin(a) * 11, 'fr': 0.0, 'life': 70})
        self.pet_cd = 80.0
        self.pet_atk = 18
        AUDIO.play('whoosh', 0.35)
      else:
        self.pet_cd = 12.0
    keep = []
    for s in self.pet_shots:
      s['x'] += s['vx'] * self.ts
      s['y'] += s['vy'] * self.ts
      s['fr'] += 0.5
      s['life'] -= 1
      hit = False
      sr = pygame.Rect(int(s['x'] - 10), int(s['y'] - 8), 20, 16)
      for o, name, _c in self.pet_targets():
        r = self.boss_rect(o) if name == 'boss' else o['rect']
        if sr.colliderect(r):
          self.pet_effect(o, name, bb)
          hit = True
          break
      if not hit:
        for lst in (self.fireballs, self.arrows, self.orbs):
          for p in lst:
            if p.get('state') == 'normal' and not p.get('shattered') and sr.collidepoint(int(p['x']), int(p['y'])):
              p['shattered'] = True
              hit = True
              break
      if hit:
        self.burst(s['x'], s['y'], 8, 3, 3, 7, (255, 230, 160))
      elif s['life'] > 0 and -20 < s['x'] < WIDTH + 20:
        keep.append(s)
    self.pet_shots = keep

  def pet_effect(self, o, name, bb):
    if name == 'boss':
      if o.get('sh', 0) > 0:
        return
      o['hp'] -= (3 + bb['level'] * 0.6) * PET_RARITY_POWER.get(bb['r'], 1.0) * BOSS_RESIST.get(o.get('type'), {}).get(bb['type'], 1.0)
      o['flash'] = 3
      return
    st = {'BLUE': 'frozen', 'YELLOW': 'stunned', 'SILVER': 'blown', 'CHRONO': 'stasis'}.get(bb['type'])
    cx, cy = o['rect'].center
    if st:
      o['state'] = st
      if st == 'stasis':
        o['st'] = STASIS_FRAMES
      if st == 'frozen':
        o['vy'] = 0.0
    else:
      o['shattered'] = True
      self.burst(cx, cy, 18, 5, 6, 12, (255, 200, 120))
      self.score += 10 * self.score_mult
      AUDIO.play('shatter', 0.5)
    self.dp += 5

  def update_den(self):
    """Hatchlings flutter around their den; tapped ones hop and show hearts."""
    r = DEN_RECT
    babies = self.data.get('babies', [])[:14]
    ids = set()
    for i, bb in enumerate(babies):
      bid = bb.get('id', i)
      ids.add(bid)
      dv = self.den.get(bid)
      if dv is None:
        dv = self.den[bid] = [random.uniform(r.left + 60, r.right - 60), random.uniform(r.top + 80, r.bottom - 70), random.uniform(-1, 1), random.uniform(-0.5, 0.5), 0, random.uniform(0, 6)]
      if random.random() < 0.01:
        dv[2], dv[3] = random.uniform(-1.4, 1.4), random.uniform(-0.8, 0.8)
      if dv[4] > 0:
        dv[4] -= 1
        dv[3] += 0.3
      dv[0] += dv[2]
      dv[1] += dv[3]
      if dv[0] < r.left + 50 or dv[0] > r.right - 50:
        dv[2] = -dv[2]
        dv[0] = max(r.left + 50, min(r.right - 50, dv[0]))
      if dv[1] < r.top + 70 or dv[1] > r.bottom - 60:
        dv[3] = -dv[3] * 0.6
        dv[1] = max(r.top + 70, min(r.bottom - 60, dv[1]))
    for bid in [k for k in self.den if k not in ids]:
      del self.den[bid]

  def roost_left(self, slot):
    """Seconds until the egg in this roost hatches."""
    return max(0.0, EGG_HATCH_HOURS[slot['r']] * 3600.0 - (time.time() - slot['start']))

  def eggs_ready(self):
    """how many eggs in the roosts are ready to hatch (cached for half a second)"""
    now = time.time()
    if now - getattr(self, '_ready_t', 0) > 0.5:
      self._ready_t = now
      self._ready_n = sum(1 for sl in self.data.get('roosts', []) if sl and self.roost_left(sl) <= 0)
    return self._ready_n

  def check_egg_notify(self):
    """tell the player (once per egg) when an egg finishes incubating"""
    for sl in self.data.get('roosts', []):
      if sl and not sl.get('told') and self.roost_left(sl) <= 0:
        sl['told'] = True
        save_data(self.data)
        self._ready_t = 0
        self.toast("Your %s egg is ready to hatch! (Lair > Dragon Eggs > Roosts)" % sl['r'].capitalize())
        AUDIO.play('coin')
        self.buzz(60)
        break

  def update_hatching(self):
    h = self.hatching
    if not h:
      return
    h['t'] += 1
    if h['t'] >= 66:
      roosts = self.data['roosts']
      slot = roosts[h['slot']]
      if slot:
        name = random.choice(BABY_NAMES)
        typ = h.get('type', 'GREEN')
        bb = self.pet_defaults({'id': slot.get('id', 0), 'r': slot['r'], 'type': typ, 'name': name, 'born': time.time(), 'happy': 80.0})
        self.data.setdefault('babies', []).append(bb)
        if self.data.get('companion') is None:
          self.data['companion'] = bb['id']
        self.data['hatched'] = self.data.get('hatched', 0) + 1
        roosts[h['slot']] = None
        save_data(self.data)
        AUDIO.play('coin')
        self.toast("%s the %s hatchling has hatched!" % (name, DRAGON_PALETTES[typ]['title'].split()[0]))
      self.hatching = None

  def drop_egg(self, btype, x, y):
    odds = BOSS_EGG_ODDS.get(btype)
    if not odds:
      return
    rarity = random.choices([o[0] for o in odds], [o[1] for o in odds])[0]
    self.egg_drop = {'x': float(x), 'y': float(y), 'r': rarity, 't': 0, 'boss': btype}

  def collect_egg(self):
    e = self.egg_drop
    if not e:
      return
    self.data['egg_id'] = self.data.get('egg_id', 0) + 1
    self.data['eggs'].append({'id': self.data['egg_id'], 'r': e['r'], 'boss': e['boss']})
    if getattr(self, 'run_stats', None) is not None:
      self.run_stats['eggs'].append(e['r'])
    self.bounty_add('egg')
    save_data(self.data)
    self.egg_drop = None
    AUDIO.play('coin')
    self.toast("You found a %s Dragon Egg!" % e['r'].capitalize())
    self.burst(self.dragon.centerx, self.dragon.centery, 26, 6, 4, 10, (255, 230, 150))

  def update_egg_drop(self):
    e = self.egg_drop
    if not e:
      return
    d = self.dragon
    e['t'] += 1
    if e['t'] < 60:                                      # pops out of the boss and floats up
      e['y'] -= 1.2
    else:                                                # then drifts to the dragon so it is never lost
      e['x'] += (d.centerx - e['x']) * 0.05
      e['y'] += (d.centery - e['y']) * 0.05
    if e['t'] % 4 == 0:
      self.emit(e['x'] + random.randint(-14, 14), e['y'] + random.randint(-18, 18), random.uniform(-1, 1), random.uniform(-2, 0), random.randint(3, 6), (255, 240, 180))
    if e['t'] > 30 and d.inflate(20, 20).collidepoint(int(e['x']), int(e['y'])):
      self.collect_egg()

  def witch_ai(self, e):
    """Witch: drifts in slowly, hovering and bobbing, and hurls green magic bolts at the dragon."""
    d, r = self.dragon, e['rect']
    e['age'] += self.ts
    slow = 0.35 if r.x < WIDTH - 160 else 1.0           # slows right down once she is on screen
    e['fx'] -= e['speed'] * slow * self.ts
    r.y = int(e['by'] + math.sin(e['age'] * 0.05 + e['phase']) * 26)
    if e['cast'] > 0:
      e['cast'] += self.ts
      if int(e['cast']) == 13 and not e.get('fired'):
        e['fired'] = True
        sx, sy = float(r.left - 6), float(r.top + 26)
        a = math.atan2(d.centery - sy, d.centerx - sx)
        spd = 6.0 + self.threat * 0.15
        self.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (120, 255, 110), 'r': 11,
                          'home': False, 'kind': 'witchbolt', 'fr': 0.0})
        self.burst(sx, sy, 10, 3, 3, 7, (140, 255, 120))
        AUDIO.play('whoosh', 0.5)
      if e['cast'] >= 36:
        e['cast'] = 0
        e['fired'] = False
        e['ct'] = random.randint(70, 110)
    elif d.centerx + 120 < r.x < WIDTH - 40:
      e['ct'] -= self.ts
      if e['ct'] <= 0:
        e['cast'] = 1.0

  def night_ai(self, e):
    """Giant moth: drifts in slowly on a wide wave and flings homing spheres of purple magic.
    Giant bat: zig-zags in, sliding toward your height, and lets out a red sonic screech."""
    d, r = self.dragon, e['rect']
    moth = e['foe'] == 'moth'
    e['age'] += self.ts
    if moth:
      e['fx'] -= e['speed'] * (0.3 if r.x < WIDTH - 170 else 1.0) * self.ts
      y = e['by'] + math.sin(e['age'] * 0.035 + e['phase']) * 46
    else:
      e['fx'] -= e['speed'] * (0.5 if e['cast'] > 0 else 1.0) * self.ts
      e['by'] += (d.centery - r.h // 2 - e['by']) * 0.01 * self.ts
      y = e['by'] + math.sin(e['age'] * 0.09 + e['phase']) * 34
    r.y = int(max(40, min(GROUND_Y - r.h - 20, y)))
    fire_at, end = (45, 51) if moth else (22, 34)          # matches the attack animations (3 / 2 ticks a frame)
    if e['cast'] > 0:
      e['cast'] += self.ts
      if e['cast'] >= fire_at and not e.get('fired'):
        e['fired'] = True
        mx, my = night_muzzle(e['foe'], NIGHT_SCALE[e['foe']])
        sx, sy = float(r.centerx + mx), float(r.centery + my)
        a = math.atan2(d.centery - sy, d.centerx - sx)
        if moth:
          spd = 4.6 + self.threat * 0.1
          self.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (196, 90, 255), 'r': 12,
                            'home': True, 'kind': 'mothorb', 'fr': 0.0})
          self.burst(sx, sy, 12, 3, 3, 7, (220, 150, 255))
        else:
          spd = 8.5 + self.threat * 0.15
          self.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd, 'state': 'normal', 'col': (255, 60, 70), 'r': 13,
                            'home': False, 'kind': 'sonic', 'fr': 0.0})
        AUDIO.play('whoosh', 0.5)
      if e['cast'] >= end:
        e['cast'] = 0
        e['fired'] = False
        e['ct'] = random.randint(80, 120) if moth else random.randint(55, 85)
    elif d.centerx + 150 < r.x < WIDTH - 60:
      e['ct'] -= self.ts
      if e['ct'] <= 0:
        e['cast'] = 1.0

  def spawn_enemy(self):
    pool = ["tower", "catapult", "trebuchet", "enemy_dragon"]
    if self.threat >= 4:
      pool += ["mage", "ballista"]
    if self.threat >= 5:
      pool += ["archer", "archer"]
    if self.b1:
      pool += ["golem", "golem"]
    if self.threat >= 5:
      pool += ["cyclops"]
    if self.threat >= 3:
      pool += ["witch", "spiders", "moth"]
    if self.threat >= 2:
      pool += ["bat"]
    if self.threat >= 2:
      pool += ["swarm"]
    if self.threat >= 4:
      pool += ["swarm"]
    t = random.choice(pool)
    if t == "swarm":
      n = random.randint(3, 5)
      base = random.randint(130, GROUND_Y - 170)
      spd = 7 + self.threat * 0.3
      variant = random.randint(0, 1)
      for i in range(n):
        dy = 0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2) * 22
        dx = i * 42
        by = max(60, min(GROUND_Y - 110, base + dy))
        self.enemies.append({'rect': pygame.Rect(WIDTH + dx, by, 36, 30), 'fx': float(WIDTH + dx), 'kind': 'wyvern', 'variant': variant,
                                     'speed': spd, 'passed': False, 'state': 'normal', 'vy': 0.0, 'phase': i * 0.7, 'by': float(by), 'wph': i * 0.5, 'age': 0.0})
      return
    if t == "spiders":
      n = random.randint(3, 5)
      vx = -(3.0 + self.threat * 0.12)
      vy = 1.9 + self.threat * 0.06
      x0 = WIDTH - random.randint(80, 260)
      for i in range(n):
        x, y = x0 + i * 62, -30 - i * 42
        self.enemies.append({'rect': pygame.Rect(x, y, 39, 25), 'fx': float(x), 'fy': float(y), 'foe': 'spider', 'vx': vx, 'vy': vy, 'speed': 0,
                             'passed': False, 'state': 'normal', 'phase': i * 1.3, 'ds': -1, 'dt': 0.0, 'ty': 0, 'age': 0.0})
      return
    if t in ("moth", "bat"):
      n = 1 if t == "moth" else random.choice((1, 2, 2, 3))
      for i in range(n):
        w, h = NIGHT_BOX[t]
        by = random.randint(90, GROUND_Y - 220)
        x = WIDTH + i * 120
        self.enemies.append({'rect': pygame.Rect(x, by, w, h), 'fx': float(x), 'foe': t, 'speed': 2.2 if t == "moth" else 5.0 + self.threat * 0.25,
                             'passed': False, 'state': 'normal', 'vy': 0.0, 'phase': random.uniform(0, 6.28), 'ds': -1, 'dt': 0.0, 'ty': 0,
                             'by': float(by), 'cast': 0, 'ct': random.randint(20, 50), 'age': 0.0})
      return
    if t == "witch":
      by = random.randint(110, GROUND_Y - 200)
      self.enemies.append({'rect': pygame.Rect(WIDTH, by, 44, 72), 'fx': float(WIDTH), 'foe': 'witch', 'speed': 2.4, 'passed': False, 'state': 'normal',
                           'vy': 0.0, 'phase': random.uniform(0, 6.28), 'ds': -1, 'dt': 0.0, 'ty': 0, 'by': float(by), 'cast': 0, 'ct': 50, 'age': 0.0})
      return
    if t == "tower":
      pool = TOWER_POOL
      if len(pool) >= 4:                            # reuse one of the pre-painted towers
        h, art = random.choice(pool)
      else:
        h = random.randint(170, 340)
        art = tower_art(h, random.choice([BANNER_GOLD, BANNER_BLUE, CLOTH_RED]))
        pool.append((h, art))
      if 'ck' not in art:
        art['ck'] = ck(art['surf'])
      tw = {'rect': pygame.Rect(WIDTH, GROUND_Y - h, TOWER_WIDTH, h), 'passed': False, 'state': 'normal',
            'surf': art['ck'], 'ox': art['ox'], 'top': art['top']}
      self.towers.append(tw)
      if art['perch'] is not None and random.random() < TOWER_GARRISON:
        self.garrison(tw, art['perch'])
    elif t == "catapult":
      self.catapults.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 40, 60, 40), 'fired': False, 'passed': False, 'state': 'normal', 'timer': 35})
    elif t == "trebuchet":
      self.trebuchets.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 55, 70, 55), 'fired': False, 'passed': False, 'state': 'normal', 'timer': 30})
    elif t == "enemy_dragon":
      foe = random.choice(('harpy', 'harpy', 'garg', 'imp', 'imp'))
      fw, fh = {'harpy': (40, 60), 'garg': (56, 56), 'imp': (36, 33)}[foe]
      if foe == 'imp':
        n = random.randint(3, 5)
        base = random.randint(110, GROUND_Y - 170)
        spd = random.randint(6, 8) + self.threat * 0.4
        for i in range(n):
          dy = 0 if i == 0 else (1 if i % 2 else -1) * ((i + 1) // 2) * 24
          dx = i * 46
          by = max(60, min(GROUND_Y - 110, base + dy))
          self.enemies.append({'rect': pygame.Rect(WIDTH + dx, by, fw, fh), 'fx': float(WIDTH + dx), 'foe': 'imp', 'speed': spd, 'passed': False, 'state': 'normal',
                                     'vy': 0.0, 'phase': i * 0.8, 'ds': -1, 'dt': 0.0, 'ty': 0})
        return
      self.enemies.append({'rect': pygame.Rect(WIDTH, random.randint(50, 340), fw, fh), 'fx': float(WIDTH), 'foe': foe,
                                 'speed': random.randint(6, 9) + self.threat * 0.5, 'passed': False, 'state': 'normal', 'vy': 0.0, 'phase': random.uniform(0, 6.28),
                                 'ds': 0 if (self.threat >= 4 and random.random() < 0.6) else -1, 'dt': 0.0, 'ty': 0})
    elif t == "cyclops":
      self.cyclopes.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 92, 58, 92), 'timer': 52, 'wind': 0, 'post': 0, 'passed': False, 'state': 'normal', 'ph': random.randint(0, 13)})
    elif t == "golem":
      self.golems.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 87, 53, 87), 'timer': 45, 'wind': 0, 'passed': False, 'state': 'normal', 'ph': random.randint(0, 11)})
    elif t == "archer":
      self.archers.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 45, 30, 45), 'fired': False, 'passed': False, 'state': 'normal'})
    elif t == "mage":
      mk = random.choice(('pyro', 'wiz', 'skel'))
      mw, mh = {'pyro': (34, 66), 'wiz': (30, 60), 'skel': (36, 72)}[mk]
      self.mages.append({'rect': pygame.Rect(WIDTH, GROUND_Y - mh, mw, mh), 'timer': 0, 'passed': False, 'state': 'normal', 'kind': mk, 'ph': random.randint(0, 11)})
    elif t == "ballista":
      self.ballistas.append({'rect': pygame.Rect(WIDTH, GROUND_Y - 40, 40, 40), 'timer': 35, 'passed': False, 'state': 'normal', 'mode': 'aiming'})

  def unit_ai(self, name, o):
    if not self.tick:                       # time is slowed: units act every other frame
      return
    r, d = o['rect'], self.dragon
    if name == 'catapults' or name == 'trebuchets':
      cat = name == 'catapults'
      if not o['fired']:
        o['timer'] -= 1                 # arm winds back while the timer runs down
        if o['timer'] <= 0:
          o['fired'] = True
          o['swing'] = 0
          o['launched'] = False
      elif not o.get('launched'):
        o['swing'] = o.get('swing', 0) + 1
        if o['swing'] >= 4:             # stone leaves the arm part-way through the swing
          o['launched'] = True
          self.fireballs.append({'x': r.centerx, 'y': r.top, 'vx': -8 if cat else -6, 'vy': -4 if cat else -14, 'state': 'normal'})
          self.shake_for(3, 5)
          AUDIO.play('launch')
          self.burst(r.centerx, r.top + 10, 6, 3, 4, 8, STONE_LIGHT)
      else:
        o['swing'] = min(o.get('swing', 0) + 1, 10)
    elif name == 'golems':
      if o['wind'] > 0:
        o['wind'] -= 1
        if o['wind'] == 5:
          sx, sy = float(r.left + 2), float(r.top + 12)
          T = max(38.0, min(70.0, abs(d.centerx - sx) / 8.0))
          g = FIREBALL_GRAVITY
          self.arrows.append({'x': sx, 'y': sy, 'vx': (d.centerx - sx) / T, 'vy': (d.centery - sy - 0.5 * g * T * T) / T, 'state': 'normal', 'kind': 'boulder', 'rot': 0.0})
          self.burst(sx, sy, 8, 3, 3, 7, (150, 150, 156))
          self.shake_for(3, 5)
          AUDIO.play('launch', 0.6)
        return
      if r.centerx < d.centerx + 90:
        return
      o['timer'] += 1
      if o['timer'] > 55:
        o['timer'] = -20
        o['wind'] = 13
    elif name == 'cyclopes':
      if o['post'] > 0:
        o['post'] -= 1
      if o['wind'] > 0:                         # winding up: the club leaves his hand on the last frame
        o['wind'] -= 1
        if o['wind'] == 4:
          sx, sy = float(r.left + 10), float(r.top + 6)
          T = max(40.0, min(72.0, abs(d.centerx - sx) / 8.0))
          g = FIREBALL_GRAVITY
          self.arrows.append({'x': sx, 'y': sy, 'vx': (d.centerx - sx) / T, 'vy': (d.centery - sy - 0.5 * g * T * T) / T, 'state': 'normal', 'kind': 'log', 'rot': 0.0})
          self.shake_for(3, 5)
          AUDIO.play('launch', 0.7)
          o['post'] = 40
        return
      if r.centerx < d.centerx + 110:
        return
      o['timer'] += 1
      if o['timer'] > 55:
        o['timer'] = -10
        o['wind'] = 45
    elif name == 'mages':
      if o.get('atk', 0) > 0:                     # casting animation plays out
        o['atk'] += 1
        if o['atk'] // 3 >= anim_count(o.get('kind', 'skel'), MAGE_ATTACK[o.get('kind', 'skel')]):
          o['atk'] = 0
      if r.centerx < d.centerx + 30:
        return
      o['timer'] += 1
      mk = o.get('kind', 'skel')
      if mk == 'pyro' and o['timer'] > 40:
        o['timer'] = -80
        sx, sy = float(r.left + 2), float(r.top + 20)
        T = max(35.0, min(65.0, abs(d.centerx - sx) / 9.0))
        vx = (d.centerx - sx + 0.01 * T * T) / T
        vy = (d.centery - sy - 0.09 * T * T) / T
        self.fireballs.append({'x': sx, 'y': sy, 'vx': vx, 'vy': vy, 'state': 'normal', 'kind': 'pyro'})
        o['atk'] = 1
        self.burst(sx, sy, 8, 3, 3, 7, (255, 150, 30))
        AUDIO.play('launch', 0.6)
      elif mk == 'wiz' and o['timer'] > 35:
        o['timer'] = -115
        sx, sy = float(r.left + 4), float(r.top + 12)
        base = math.atan2(d.centery - sy, d.centerx - sx)
        for da in (-0.2, 0.0, 0.2):
          self.orbs.append({'x': sx, 'y': sy, 'vx': math.cos(base + da) * 8.0, 'vy': math.sin(base + da) * 8.0, 'state': 'normal', 'col': (100, 200, 255), 'r': 7, 'home': False, 'kind': 'wiz'})
        o['atk'] = 1
        self.burst(sx, sy, 8, 3, 3, 6, (120, 210, 255))
        AUDIO.play('whoosh')
      elif mk == 'skel' and o['timer'] > 45:
        o['timer'] = -135
        sx, sy = float(r.left + 6), float(r.top + 2)
        dx, dy = d.centerx - sx, d.centery - sy
        dist = max(math.hypot(dx, dy), 1.0)
        spd = 3.4 + self.threat * 0.1
        self.orbs.append({'x': sx, 'y': sy, 'vx': dx / dist * spd, 'vy': dy / dist * spd, 'state': 'normal', 'col': (200, 60, 220), 'r': 13, 'home': True, 'kind': 'skel'})
        o['atk'] = 1
        self.burst(sx, sy, 8, 2, 3, 6, (200, 80, 230))
        AUDIO.play('whoosh')
    elif name == 'ballistas' and o['mode'] == 'aiming':
      o['timer'] -= 1
      if o['timer'] <= 0:
        o['mode'] = 'fired'
        hx, hy = float(r.x - 18), float(r.y - 11)
        dx, dy = d.centerx - hx, d.centery - hy
        ang = math.atan2(dy, -dx) if dx < 0 else 0.0
        ang = max(-0.7, min(0.2, ang))
        self.spears.append({'x': hx, 'y': hy, 'vx': -math.cos(ang) * 20, 'vy': math.sin(ang) * 20})
        self.burst(hx, hy, 6, 3, 3, 6, (255, 170, 50))
        self.shake_for(2, 3)
        AUDIO.play('whoosh')
    elif name == 'archers':
      o['atk'] = o.get('atk', 0) + 1                # draw the bow (attack animation), loose on frame 7
      if not o['fired'] and o['atk'] >= 28:
        dx, dy = d.centerx - r.centerx, d.centery - r.centery
        dist = max(math.hypot(dx, dy), 1)
        spd = 12 + self.threat * 0.3
        self.arrows.append({'x': float(r.centerx - 14), 'y': float(r.centery - 14), 'vx': dx / dist * spd, 'vy': dy / dist * spd, 'state': 'normal', 'kind': 'satyr'})
        o['fired'] = True

  def hit_dragon(self, o, melee):
    if not self.shield_active:
      self.dead = True
    else:
      o['shattered'] = True
      AUDIO.play('shatter')
      self.score += 10
      self.shake_for(6, 8)
      self.bounty_add('shatter')

  def update_items(self):
    d = self.dragon
    for lst, is_pu in ((self.powerups, True), (self.coins, False)):
      keep = []
      for it in lst:
        it['t'] += 0.14
        r = it['rect']
        dx, dy = d.centerx - r.centerx, d.centery - r.centery
        dist = math.hypot(dx, dy)
        if 0 < dist < self.magnet:
          r.x += int(dx / dist * 8)
          r.y += int(dy / dist * 8)
        else:
          r.x -= self.scroll_px
        it['ry'] = r.y + int(math.sin(it['t']) * 8)
        if d.colliderect(pygame.Rect(r.x, it['ry'], r.w, r.h)):
          if is_pu:
            self.breath, self.breath_timer = True, self.breath_time
            if getattr(self, 'run_stats', None) is not None:
              self.run_stats['powerups'] += 1
            self.bounty_add('power')
            AUDIO.play('power')
            self.shake_for(6, 12)
            self.burst(r.x + 17, it['ry'] + 17, 20, 5, 6, 14, GOLD_BORDER)
          else:
            self.run_coins += self.coin_val
            self.bounty_add('collect')
            AUDIO.play('coin', 0.7)
            self.burst(r.x + 10, it['ry'] + 10, 5, 3, 4, 8, GOLD_BORDER)
        elif r.right >= 0:
          keep.append(it)
      lst[:] = keep

  def zig(self, x0, y0, x1, y1, n, amp):
    pts = [(x0, y0)]
    for i in range(1, n):
      t = i / float(n)
      pts.append((int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t + random.uniform(-amp, amp))))
    pts.append((x1, y1))
    return pts

  def update_lava(self, hx, hy):
    if self.breath and random.random() < 0.12 and len(self.globs) < 8:
      self.globs.append([float(hx), float(hy), random.uniform(5, 10), random.uniform(-3, 0)])
    keep = []
    for g in self.globs:
      g[0] += g[2]
      g[1] += g[3]
      g[3] += 0.55
      if g[1] >= GROUND_Y - 4:
        self.burst(g[0], GROUND_Y - 6, 6, 3, 3, 7, (255, 150, 30) if self.selected == "RED" else (150, 255, 90))
        for p in self.lava:
          if abs(p['x'] - g[0]) < 30:
            p['life'] = max(p['life'], 260)
            break
        else:
          if len(self.lava) < 8:
            self.lava.append({'x': g[0], 'life': 260})
      elif g[0] < WIDTH + 40:
        keep.append(g)
    self.globs = keep
    pools = []
    for p in self.lava:
      p['x'] -= self.scroll_px
      p['life'] -= 1
      if p['life'] > 0 and p['x'] > -50:
        pools.append(p)
    self.lava = pools
    for p in pools:
      zone = pygame.Rect(int(p['x'] - 34), GROUND_Y - 22, 68, 26)
      if random.random() < 0.3:
        self.emit(p['x'] + random.randint(-28, 28), GROUND_Y - 6, random.uniform(-0.6, 0.6), random.uniform(-2.4, -0.8), random.randint(4, 7), random.choice(BREATH_COLORS[self.selected][:3]))
      for name in GROUND_LISTS:
        for o in getattr(self, name):
          if o.get('state', 'normal') == 'normal' and zone.colliderect(o['rect']):
            o['burn'] = o.get('burn', 0) + 1
            if o['burn'] % 4 == 0:
              self.emit(o['rect'].centerx + random.randint(-10, 10), o['rect'].bottom - random.randint(4, 30), random.uniform(-1, 1), random.uniform(-3, -1), random.randint(5, 8), random.choice(BREATH_COLORS[self.selected][:3]))
            if o['burn'] >= (40 if name == 'towers' else 24):
              self.apply_breath(o, 20, (255, 120, 20))

  def chain_targets(self):
    out = []
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if o.get('shattered') or o.get('state') not in ('normal', 'stunned'):
          continue
        r = o['rect']
        out.append((o, name, (r.centerx, r.top + 30) if name == 'towers' else r.center))
    b = self.boss
    if b and b['state'] == 'fighting' and not b.get('ghost') and b.get('atk') != 'dive':
      out.append((b, 'boss', self.boss_rect(b).center))
    return out

  def chain_lightning(self, hx, hy):
    """Lightning Dragon: the bolt hits the nearest foe ahead, then jumps to anything close enough (up to 3 jumps)."""
    cands = self.chain_targets()
    best, bd = None, 1e9
    for c in cands:
      x, y = c[2]
      if hx + 10 < x < hx + 400 and abs(y - hy) < 170:
        dd = math.hypot(x - hx, y - hy)
        if dd < bd:
          best, bd = c, dd
    main_col, fork_col = (130, 205, 255), (200, 238, 255)
    if best is None:
      pts = self.zig(hx, hy, hx + random.randint(300, 380), hy + random.randint(-40, 40), 7, 22)
      self.bolts.append((pts, main_col, 8))
      for p in random.sample(pts[2:6], 2):
        self.bolts.append((self.zig(p[0], p[1], p[0] + random.randint(40, 100), p[1] + random.randint(-45, 45), 3, 12), fork_col, 4))
      return
    chain, last, seen = [best], best, {id(best[0])}
    for _ in range(CHAIN_JUMPS):
      nxt, nd = None, CHAIN_RANGE
      for c in cands:
        if id(c[0]) in seen:
          continue
        dd = math.hypot(c[2][0] - last[2][0], c[2][1] - last[2][1])
        if dd < nd:
          nxt, nd = c, dd
      if nxt is None:
        break
      chain.append(nxt)
      seen.add(id(nxt[0]))
      last = nxt
    px, py = hx, hy
    for i, (o, name, (x, y)) in enumerate(chain):
      pts = self.zig(int(px), int(py), int(x), int(y), max(3, int(math.hypot(x - px, y - py) / 45)), 16 if i == 0 else 12)
      self.bolts.append((pts, main_col, 8 if i == 0 else 6))
      if random.random() < 0.5:
        p = random.choice(pts[1:-1]) if len(pts) > 2 else pts[0]
        self.bolts.append((self.zig(p[0], p[1], p[0] + random.randint(-50, 50), p[1] + random.randint(-50, 50), 3, 10), fork_col, 3))
      if self.tick and random.random() < 0.5:
        self.emit(x + random.randint(-10, 10), y + random.randint(-10, 10), random.uniform(-3, 3), random.uniform(-3, 3), random.randint(4, 8), random.choice(((200, 238, 255), (255, 255, 255), (130, 205, 255))))
      if name == 'boss':
        if o.get('sh', 0) <= 0:
          o['hp'] -= 0.8 * self.boss_mult(o)
          o['hurt'] = o.get('hurt', 0) + 1
          if o['hurt'] % 14 == 1:
            o['flash'] = 3
      elif name == 'towers':
        if o['state'] == 'normal':
          self.crumble_tower(o)
      else:
        self.apply_breath(o, {'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'archers': 20, 'mages': 20, 'ballistas': 30, 'golems': 40, 'cyclopes': 40}.get(name, 20), (130, 205, 255))
      px, py = x, y

  def crumble_tower(self, o):
    """Tower struck by lightning: it breaks into bricks that fall from the top down, with dust at the base."""
    o['shattered'] = True
    self.score += 15 * self.score_mult
    self.bounty_add('shatter')
    self.dp += 15
    self.crumble_fx(o)

  def crumble_fx(self, o):
    """the falling-bricks effect, used whenever a tower is destroyed by anything."""
    if o.get('crumbled'):
      return
    o['crumbled'] = True
    r = o['rect']
    surf = o.get('surf')
    left = r.x - o.get('ox', 0)
    self.shake_for(10, 14)
    AUDIO.play('shatter', 0.8)
    if surf is None:
      return
    sw, sh = surf.get_size()
    top = r.y - o.get('top', 15)
    for cy in range(0, sh, 24):
      for cx in range(0, sw, 24):
        piece = surf.subsurface((cx, cy, min(24, sw - cx), min(24, sh - cy))).copy()
        self.rubble.append({'x': float(left + cx), 'y': float(top + cy), 'vx': random.uniform(-2.2, 2.2), 'vy': random.uniform(-3.0, 0.5),
                            'rot': 0.0, 'vr': random.uniform(-14, 14), 'img': piece, 'delay': int(cy / float(max(1, sh)) * 24), 'rots': {}})
    for _ in range(14):
      self.emit(r.x + random.randint(0, r.w), GROUND_Y - random.randint(0, 20), random.uniform(-2, 2), random.uniform(-2, -0.5), random.randint(10, 18), random.choice(((150, 140, 130), (120, 112, 104), (180, 172, 160))))

  def make_corpse(self, name, o):
    r = o['rect']
    drop = GROUND_Y - r.bottom                      # how far above the ground it died
    if name == 'golems':                            # stone golem breaks apart into tumbling rocks
      fi = (int(self.wing * 0.4) + o.get('ph', 0)) % 12
      src = extra_frame('golem', fi)
      spr = pygame.transform.scale(src, (int(src.get_width() * 1.21), int(src.get_height() * 1.21)))
      sw, sh = spr.get_size()
      x0, y0 = r.centerx - sw // 2, r.bottom + 2 - sh
      for cy in range(0, sh, 14):
        for cx in range(0, sw, 14):
          piece = spr.subsurface((cx, cy, min(14, sw - cx), min(14, sh - cy))).copy()
          self.rubble.append({'x': float(x0 + cx), 'y': float(y0 + cy), 'vx': random.uniform(-2.4, 2.4), 'vy': random.uniform(-4.0, 0.0),
                              'rot': 0.0, 'vr': random.uniform(-16, 16), 'img': piece, 'delay': int((sh - cy) / float(sh) * 6), 'rots': {}})
      for _ in range(16):
        self.emit(r.centerx + random.randint(-30, 30), r.bottom - random.randint(0, 40), random.uniform(-2, 2), random.uniform(-2.5, -0.5), random.randint(8, 15), random.choice(((150, 146, 140), (110, 106, 100), (180, 176, 168))))
      self.shake_for(6, 8)
      return
    if name == 'cyclopes':
      sc_ = 1.25
      spr = cyc_frame('death', 0, sc_)
      x, y = r.centerx - int(93 * sc_), r.bottom + 2 - spr.get_height()
      self.corpses.append({'k': 'cyclops', 'x': float(x), 'y': float(y), 't': 0, 'vy': 0.0, 'floor': float(y + drop), 'n': cyc_count('death'), 'rate': 5})
      return
    if name == 'enemies' and o.get('foe') in ('moth', 'bat'):  # plays its own death animation as it drops
      k, sc_ = o['foe'], NIGHT_SCALE[o['foe']]
      n = night_count(k, 'death')
      self.burst(r.centerx, r.centery, 14, 4, 3, 8, (170, 140, 90) if k == 'moth' else (150, 40, 60))
      self.corpses.append({'k': k, 'x': float(r.centerx), 'y': float(r.centery), 't': 0, 'vy': -1.5, 'floor': float(GROUND_Y - night_bottom(k, n - 1, sc_)),
                           'n': n, 'rate': 3})
      return
    an = unit_anchor(name, o)
    if not an:
      return
    k, x, y = an
    if k == 'eye':                                  # the eye just bursts where it is
      self.burst(r.centerx, r.centery, 18, 5, 3, 8, (200, 30, 40))
      self.burst(r.centerx, r.centery, 10, 4, 3, 7, (40, 110, 70))
      self.corpses.append({'k': 'eye', 'x': float(x), 'y': float(y), 't': 0, 'vy': 0.0, 'floor': float(y), 'anim': 'HURT', 'rate': 3,
                           'n': anim_count('eye', 'HURT')})
      return
    self.corpses.append({'k': k, 'x': float(x), 'y': float(y), 't': 0, 'vy': -2.0 if name == 'enemies' else 0.0,
                         'floor': float(y + drop), 'anim': 'DEATH', 'rate': 4, 'n': anim_count(k, 'DEATH')})

  def update_corpses(self):
    sc = self.scroll_px
    keep = []
    for c in self.corpses:
      c['t'] += 1
      c['x'] -= sc
      if c['y'] < c['floor'] - 0.5:                 # anything that died up high falls to the ground
        c['vy'] += 0.55
        c['y'] = min(c['floor'], c['y'] + c['vy'])
        if c['y'] >= c['floor']:
          c['vy'] = 0.0
      falling = c['y'] < c['floor'] - 0.5
      life = c['n'] * c.get('rate', 4) + (0 if c['k'] == 'eye' else 30)
      if (c['t'] < life or falling) and c['x'] > -200:
        keep.append(c)
    self.corpses = keep

  def update_rubble(self):
    sc = self.scroll_px
    keep = []
    for p in self.rubble:
      if p['delay'] > 0:
        p['delay'] -= 1
        p['x'] -= sc
      else:
        p['vy'] += 0.9
        p['x'] += p['vx'] - sc
        p['y'] += p['vy']
        p['rot'] += p['vr']
      if p['y'] < GROUND_Y - 6 and p['x'] > -40:
        keep.append(p)
      elif p['x'] > -40 and random.random() < 0.4:
        self.emit(p['x'] + 12, GROUND_Y - 4, random.uniform(-1.5, 1.5), random.uniform(-1.5, -0.3), random.randint(6, 12), (150, 140, 130))
    self.rubble = keep

  def update_tornados(self):
    """Wind Dragon: while breathing, small tornados drop to the ground and race forward,
    spinning up anything they touch and flinging it away."""
    d = self.dragon
    if self.selected == "SILVER" and self.breath:
      self.tornado_t = getattr(self, 'tornado_t', TORNADO_EVERY) + 1
      if self.tornado_t >= TORNADO_EVERY and len(self.tornados) < 3:
        self.tornado_t = 0
        self.tornados.append({'x': float(d.x + 120), 'y': float(d.centery), 'f': 0.0, 'life': 0})
        AUDIO.play('whoosh', 0.6)
    elif not self.breath:
      self.tornado_t = TORNADO_EVERY
    keep = []
    for t in self.tornados:
      t['life'] += 1
      t['f'] += 0.5
      if t['y'] < GROUND_Y - 10:                      # gust falls to the ground first
        t['y'] = min(GROUND_Y - 10.0, t['y'] + 16)
        t['x'] += 6
      else:
        t['x'] += TORNADO_SPEED
      zone = pygame.Rect(int(t['x'] - 34), GROUND_Y - 150, 68, 150) if t['y'] >= GROUND_Y - 10 else pygame.Rect(int(t['x'] - 20), int(t['y'] - 20), 40, 40)
      for name in GROUND_LISTS + ('enemies',):
        for o in getattr(self, name):
          if o.get('shattered') or o.get('state') != 'normal' or not zone.colliderect(o['rect']):
            continue
          o['state'] = 'spun'
          o['spin'] = 0
          o['tz'] = t
          self.dp += 10
          self.score += 5 * self.score_mult
      for lst in (self.fireballs, self.arrows):
        for p in lst:
          if p.get('state') == 'normal' and zone.collidepoint(int(p['x']), int(p['y'])):
            p['state'] = 'blown'
      if self.tick and random.random() < 0.6:
        self.emit(t['x'] + random.randint(-30, 30), GROUND_Y - random.randint(0, 120), random.uniform(-2, 2), random.uniform(-2, 0), random.randint(3, 6), random.choice(((235, 248, 255), (170, 215, 255))))
      if t['x'] < WIDTH + 80 and t['life'] < 400:
        keep.append(t)
    self.tornados = keep
    for name in GROUND_LISTS + ('enemies',):          # spin inside the funnel, then thrown away
      for o in getattr(self, name):
        if o.get('state') != 'spun':
          continue
        o['spin'] += 1
        t = o.get('tz')
        r = o['rect']
        if o['spin'] < 18 and t in self.tornados:
          r.centerx = int(t['x'] + math.cos(o['spin'] * 0.7) * 16)
          r.y -= 5
          if 'fx' in o:
            o['fx'] = float(r.x)
        else:
          o['state'] = 'blown'
          o.pop('tz', None)
          self.bounty_add('shatter')

  # ------------------------------------------------------------------ Bone Reaper: Grave Curse + hunting wisps
  def curse_breath(self):
    """Death Cloud: a streaming cloud (drawn like the magma breath) that curses everything it touches"""
    d = self.dragon
    beam = pygame.Rect(d.right, d.y - 45, 400, 130)
    heavy = ('towers', 'catapults', 'trebuchets', 'ballistas', 'golems', 'cyclopes')
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if o.get('shattered') or o.get('curse') or o.get('state') in ('blown', 'spun'):
          continue
        if beam.colliderect(o['rect']):
          o['curse'] = o['curse_max'] = CURSE['heavy'] if name in heavy else CURSE['time']
    for lst, w_ in ((self.arrows, 30), (self.fireballs, 22), (self.orbs, 20), (self.spears, 30)):   # shots rot away in the cloud
      for p in lst:
        if not p.get('shattered') and beam.collidepoint(p['x'], p['y']):
          p['shattered'] = True
          self.emit(p['x'], p['y'], 0, -1, 5, (190, 130, 240))
    b = self.boss
    if b and b['state'] == 'fighting' and not b.get('ghost') and b.get('atk') != 'dive' and b.get('sh', 0) <= 0 and beam.colliderect(self.boss_rect(b)):
      b['hp'] -= 0.9 * self.boss_mult(b)
      b['hurt'] = b.get('hurt', 0) + 1
      if b['hurt'] % 14 == 1:
        b['flash'] = 3

  # ------------------------------------------------------------------ boss heart power-up
  def update_heart_drop(self):
    if self.heart_delay > 0:
      self.heart_delay -= 1
      if self.heart_delay == 0 and self.heart_drop is None:
        self.heart_drop = {'x': float(WIDTH + 30), 'y': float(random.randint(150, GROUND_Y - 190)), 't': 0.0}
    h = self.heart_drop
    if not h:
      return
    d = self.dragon
    h['t'] += 1
    dx, dy = d.centerx - h['x'], d.centery - h['y']
    dist = math.hypot(dx, dy)
    if 0 < dist < 150:                              # drawn toward you once you are close
      h['x'] += dx / dist * 6
      h['y'] += dy / dist * 6
    else:
      h['x'] -= max(2.0, self.scroll_px * 0.8)
      h['y'] += math.sin(h['t'] * 0.08) * 1.2
    if dist < 40:
      self.heart_drop = None
      if self.hearts < MAX_HEARTS:
        self.hearts += 1
        self.toast("+1 HEART!")
      else:
        self.score += 200
        self.toast("Hearts full!  +200")
      if getattr(self, 'run_stats', None) is not None:
        self.run_stats['powerups'] += 1
      AUDIO.play('quest')
      self.burst(d.centerx, d.centery, 24, 5, 5, 12, (255, 80, 90))
    elif h['x'] < -60:
      self.heart_drop = None

  # ------------------------------------------------------------------ shared: everything a player attack can hit
  def foe_targets(self):
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if not (o.get('shattered') or o.get('swallowed')):
          yield name, o

  def hit_foe(self, name, o, chip_key, chips, color):
    """normal foes fall to one hit; big ones (golems, cyclopes, siege, towers) take several"""
    if name in ('golems', 'cyclopes', 'catapults', 'trebuchets', 'ballistas', 'towers'):
      o[chip_key] = o.get(chip_key, 0) + 1
      self.emit(o['rect'].centerx, o['rect'].centery, random.uniform(-2, 2), random.uniform(-2, 0), random.randint(4, 7), color)
      if o[chip_key] < chips:
        return False
    pts = {'towers': 15, 'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(name, 20)
    self.apply_breath(o, pts, color)
    return True

  def boss_live(self):
    b = self.boss
    return b if (b is not None and b['state'] == 'fighting' and not b.get('ghost')) else None

  # ------------------------------------------------------------------ Forest Dragon: Razor Leaf Storm
  def leaf_breath(self):
    """a whirling stream of razor leaves pours from the jaws"""
    self.leaf_cd = getattr(self, 'leaf_cd', 0) - 1
    if self.leaf_cd > 0 or len(self.leaves) >= LEAF['max']:
      return
    self.leaf_cd = LEAF['every']
    d = self.dragon
    hx, hy = breath_origin('FOREST', d, self.flap_ph, self.vel, self.pitch)
    for _ in range(2):
      self.leaves.append({'x': float(hx), 'y': float(hy + random.uniform(-4, 4)), 'vx': random.uniform(10.5, 14.0), 'vy': random.uniform(-2.2, 2.2),
                          'ph': random.uniform(0, 6.28), 'rot': random.uniform(0, 360), 't': 0, 'hits': 0,
                          'col': random.choice(((110, 180, 40), (150, 210, 60), (200, 190, 60), (90, 150, 30)))})

  def update_leaves(self):
    keep = []
    b = self.boss_live()
    br = self.boss_rect(b) if b else None
    for lf in getattr(self, 'leaves', ()):
      lf['t'] += 1
      lf['x'] += lf['vx']
      lf['y'] += lf['vy'] + math.sin(lf['t'] * 0.45 + lf['ph']) * 2.2      # whirls as it flies
      lf['rot'] = (lf['rot'] + 34) % 360
      dead = False
      lr = pygame.Rect(int(lf['x'] - 7), int(lf['y'] - 7), 14, 14)
      for name, o in self.foe_targets():
        if lr.colliderect(o['rect']) and id(o) != lf.get('last'):
          lf['last'] = id(o)
          self.hit_foe(name, o, 'cut', LEAF['heavy'], lf['col'])
          lf['hits'] += 1
          if lf['hits'] >= LEAF['pierce']:
            dead = True
            break
      if not dead:
        for lst in (self.fireballs, self.arrows, self.orbs):        # slices enemy shots out of the air
          for p in lst:
            if not p.get('shattered') and abs(p['x'] - lf['x']) < 12 and abs(p['y'] - lf['y']) < 12:
              p['shattered'] = True
              dead = True
      if not dead and br is not None and lr.colliderect(br):
        if b.get('sh', 0) <= 0:
          b['hp'] -= 0.6 * self.boss_mult(b)
          b['hurt'] = b.get('hurt', 0) + 1
          if b['hurt'] % 14 == 1:
            b['flash'] = 3
        dead = True
      if dead:
        self.emit(lf['x'], lf['y'], random.uniform(-2, 2), random.uniform(-2, 1), random.randint(3, 5), lf['col'])
      elif lf['t'] < LEAF['life'] and lf['x'] < WIDTH + 20 and -20 < lf['y'] < GROUND_Y:
        keep.append(lf)
    self.leaves = keep

  # ------------------------------------------------------------------ Giant Eagle: Talon Strike
  def talon_target(self):
    """the nearest foe on screen (or the boss if it is the only thing left)"""
    d = self.dragon
    best, bd = None, None
    for name, o in self.foe_targets():
      r = o['rect']
      if r.right < 0 or r.left > WIDTH:
        continue
      dd = (r.centerx - d.centerx) ** 2 + (r.centery - d.centery) ** 2
      if bd is None or dd < bd:
        best, bd = (name, o), dd
    b = self.boss_live()
    if b is not None:
      br = self.boss_rect(b)
      dd = (br.centerx - d.centerx) ** 2 + (br.centery - d.centery) ** 2
      if bd is None or dd < bd:
        best = ('boss', b)
    return best

  def talon_tap(self):
    if getattr(self, 'talon', None):                 # already diving: the next tap queues another strike
      self.talon_q = min(3, getattr(self, 'talon_q', 0) + 1)
      return
    tgt = self.talon_target()
    if tgt is None:                                  # nothing to strike: an ordinary flap
      self.vel = FLAP_STRENGTH
      self.start_flap()
      AUDIO.play('flap', 0.7)
      return
    self.talon = {'tgt': tgt, 't': 0}
    self.dash_inv = 999                              # takes no damage while it strikes
    self.flap_left = 0.0
    AUDIO.play('whoosh', 0.9)
    AUDIO.play('roar', 0.35)

  def update_talon(self):
    d = self.dragon
    tl = getattr(self, 'talon', None)
    if not tl:
      if getattr(self, 'talon_home', False):          # glide back to its usual place
        d.x += (150 - d.x) * 0.12 if abs(d.x - 150) > 2 else (150 - d.x)
        if self.dash_inv > 0 and self.dash_state == 'idle':
          self.dash_inv -= 1
        if d.x == 150:
          self.talon_home = False
          if self.dash_state == 'idle':
            self.dash_inv = 0
      return
    tl['t'] += 1
    name, o = tl['tgt']
    gone = o.get('shattered') if name != 'boss' else (self.boss_live() is None)
    if gone:
      nt = self.talon_target()
      if nt is None or tl['t'] > 90:
        self.end_talon()
        return
      tl['tgt'] = nt
      name, o = nt
    tr = self.boss_rect(o) if name == 'boss' else o['rect']
    tx, ty = tr.centerx, tr.centery
    dx, dy = tx - d.centerx, ty - d.centery
    dist = math.hypot(dx, dy) or 1.0
    spd = 34.0 + min(40.0, tl['t'] * 3.0)             # gets there fast, however far away it is
    self.vel = 0.0
    if dist <= spd + 14:
      d.centerx, d.centery = int(tx), int(ty)
      self.talon_hit(name, o)
      return
    tl['dir'] = -1 if dx < -20 else 1               # which way it is diving (the art is mirrored for a dive to the left)
    d.x += int(dx / dist * spd)
    d.y += int(dy / dist * spd)
    d.y = max(-20, min(GROUND_Y - d.h, d.y))
    for _ in range(3):                                # feather streaks behind the dive
      self.emit(d.centerx - dx / dist * random.uniform(10, 50), d.centery - dy / dist * random.uniform(10, 50) + random.uniform(-10, 10),
                -dx / dist * 3, -dy / dist * 3, random.randint(4, 8), random.choice(((250, 230, 180), (220, 180, 90), (255, 255, 255))))

  def talon_hit(self, name, o):
    d = self.dragon
    if name == 'boss':
      if o.get('sh', 0) <= 0:
        o['hp'] -= 45 * self.boss_mult(o)
      o['flash'] = 8
      self.burst(d.centerx, d.centery, 30, 7, 6, 14, (255, 220, 140))
    else:
      pts = {'towers': 15, 'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(name, 20)
      o['shattered'] = True
      self.score += int(pts * self.score_mult)
      self.dp += pts
      self.bounty_add('shatter')
      cx, cy = o['rect'].center
      self.burst(cx, cy, 24, 6, 6, 14, (255, 230, 170))
      self.burst(cx, cy, 14, 5, 4, 10, (190, 140, 50))
    AUDIO.play('shatter', 0.8)
    self.shake_for(7, 9)
    self.end_talon()
    if getattr(self, 'talon_q', 0) > 0 and self.breath:   # a queued tap strikes again straight away
      self.talon_q -= 1
      self.talon_tap()

  def end_talon(self):
    self.talon = None
    self.talon_home = True
    self.dash_inv = 30                               # a moment of safety as it pulls up
    self.vel = FLAP_STRENGTH * 0.6

  # ------------------------------------------------------------------ Cosmic Whale: Cosmic Maw
  def maw_breath(self):
    """the whale's starry jaws open into a vortex: foes and shots in front are dragged in and swallowed"""
    d = self.dragon
    mx, my = breath_origin('WHALE', d, self.flap_ph, self.vel, self.pitch)
    R, cone = MAW['range'], MAW['cone']

    def inside(x, y):
      dx, dy = x - mx, y - my
      return -30 < dx < R and abs(dy) < 70 + dx * cone

    def drag(x, y, k=1.0):
      dx, dy = mx - x, my - y
      dist = math.hypot(dx, dy) or 1.0
      f = ((1 - min(1.0, dist / R)) * MAW['pull'] + 2.5) * k
      sw = 0.22 * f                                    # a little swirl as they spiral in
      return dx / dist * f - dy / dist * sw, dy / dist * f + dx / dist * sw, dist

    for e in self.enemies:                             # flyers are dragged in and gulped down
      if e.get('shattered') or e.get('swallowed'):
        continue
      r = e['rect']
      if not inside(r.centerx, r.centery):
        continue
      vx, vy, dist = drag(r.centerx, r.centery)
      e['fx'] = e.get('fx', float(r.x)) + vx
      r.x = int(e['fx'])
      r.y += int(round(vy))
      for key in ('by', 'fy'):
        if key in e:
          e[key] += vy
      if dist < MAW['gulp'] + 10:
        self.gulp(e, 35)
    for name in ('archers', 'mages'):                  # small ground units are lifted off their feet
      for o in getattr(self, name):
        if o.get('shattered') or o.get('swallowed'):
          continue
        r = o['rect']
        if not inside(r.centerx, r.centery):
          continue
        vx, vy, dist = drag(r.centerx, r.centery, 0.75)
        r.x += int(round(vx))
        r.y += int(round(vy))
        o['perch'] = None
        o['fall'] = 0.0
        if dist < MAW['gulp'] + 12:
          self.gulp(o, 20)
    for name in ('towers', 'catapults', 'trebuchets', 'ballistas', 'golems', 'cyclopes'):   # big things are torn apart bit by bit
      for o in getattr(self, name):
        if o.get('shattered'):
          continue
        r = o['rect']
        if not (inside(r.centerx, r.top + 10) or inside(r.centerx, r.centery)) or r.left - mx > R * 0.7:
          continue
        o['maw'] = o.get('maw', 0) + 1
        if o['maw'] % 3 == 0:                          # chunks fly into its mouth
          px, py = r.centerx + random.randint(-20, 20), r.top + random.randint(0, 30)
          self.emit(px, py, (mx - px) * 0.06, (my - py) * 0.06, random.randint(4, 8), random.choice((STONE_LIGHT, WOOD_BROWN, (200, 180, 255))))
        if o['maw'] > MAW['heavy']:
          o['shattered'] = True
          self.score += 25 * self.score_mult
          self.bounty_add('shatter')
          self.dp += 25
          self.burst(r.centerx, r.centery, 18, 5, 3, 8, (200, 180, 255))
    for lst, rr in ((self.arrows, 10), (self.fireballs, 14), (self.orbs, 12)):   # shots are sucked in too
      for p in lst:
        if p.get('shattered') or not inside(p['x'], p['y']):
          continue
        vx, vy, dist = drag(p['x'], p['y'], 1.7)
        p['x'] += vx
        p['y'] += vy
        if 'vx' in p:
          p['vx'] *= 0.85
          p['vy'] *= 0.85
        if dist < MAW['gulp'] + rr:
          p['shattered'] = True
          self.burst(p['x'], p['y'], 4, 2, 2, 5, (220, 200, 255))
    if self.tick or random.random() < 0.5:             # starlight streaming into the jaws
      for _ in range(2):
        ang = random.uniform(-0.7, 0.7)
        dist = random.uniform(120, R)
        px, py = mx + math.cos(ang) * dist, my + math.sin(ang) * dist * 0.8
        self.emit(px, py, (mx - px) * 0.07, (my - py) * 0.07, random.randint(2, 5), random.choice(((255, 255, 255), (200, 180, 255), (140, 120, 255), (150, 255, 240))))
    b = self.boss_live()
    if b and b.get('atk') != 'dive':
      br = self.boss_rect(b)
      if inside(br.centerx, br.centery) and br.left - mx < R * 0.85 and b.get('sh', 0) <= 0:
        b['hp'] -= 0.9 * self.boss_mult(b)
        b['hurt'] = b.get('hurt', 0) + 1
        if b['hurt'] % 14 == 1:
          b['flash'] = 3
        if random.random() < 0.4:
          px, py = br.centerx + random.randint(-30, 30), br.centery + random.randint(-30, 30)
          self.emit(px, py, (mx - px) * 0.05, (my - py) * 0.05, random.randint(4, 8), (255, 120, 120))

  def gulp(self, o, pts):
    o['shattered'] = True
    o['swallowed'] = True                           # (no ordinary death animation: it is gone down the whale's throat)
    self.score += int(pts * self.score_mult)
    self.dp += pts
    self.bounty_add('shatter')
    cx, cy = o['rect'].center
    self.burst(cx, cy, 10, 3, 3, 7, random.choice(((200, 180, 255), (255, 255, 255), (140, 120, 255))))
    AUDIO.play('whoosh', 0.3)

  # ------------------------------------------------------------------ Fey Dragon: Glamour Nova
  def nova_breath(self):
    """each burst of the fey's magic sends a ring of glamour rippling outward (timed to the burst in its animation)"""
    from fd_sheet import sheet as _sheet
    idx = _sheet('FEY').breath_index()
    last = getattr(self, 'nova_idx', -1)
    self.nova_idx = idx
    self.nova_wait = getattr(self, 'nova_wait', 99) + 1
    if (idx == 1 and last != 1 and self.nova_wait > 20) or self.nova_wait > 50:
      self.nova_wait = 0
      d = self.dragon
      self.novas.append({'r': 20.0, 'hit': set(), 'boss': False, 't': 0, 'ox': 32, 'oy': 21})
      self.burst(d.x + 32, d.y + 21, 14, 4, 3, 7, random.choice(((255, 150, 240), (140, 240, 255), (255, 255, 220))))
      AUDIO.play('chime', 0.5)

  def update_novas(self):
    d = self.dragon
    if not self.breath:
      self.nova_wait = 99                           # the first ring bursts out the moment you breathe again
    keep = []
    b = self.boss_live()
    for nv in getattr(self, 'novas', ()):
      nv['t'] += 1
      nv['r'] += NOVA['grow'] * (1.0 - nv['r'] / (NOVA['r'] * 1.25))
      cx, cy = d.x + nv['ox'], d.y + nv['oy']            # the ring stays centred on the dragon
      r0, r1 = nv['r'] - NOVA['band'], nv['r'] + 8
      for name, o in list(self.foe_targets()):
        if id(o) in nv['hit']:
          continue
        rc = o['rect']
        dist = math.hypot(rc.centerx - cx, rc.centery - cy)
        if r0 - max(rc.w, rc.h) * 0.4 < dist < r1:
          nv['hit'].add(id(o))
          self.glamour(name, o)
      for lst in (self.arrows, self.fireballs, self.orbs):
        for p in lst:
          if not p.get('shattered') and r0 < math.hypot(p['x'] - cx, p['y'] - cy) < r1:
            p['shattered'] = True
            for _ in range(4):
              self.emit(p['x'], p['y'], random.uniform(-2, 2), random.uniform(-2, 1), random.randint(2, 4), random.choice(((255, 255, 220), (255, 150, 240), (140, 240, 255))))
      if b and not nv['boss']:
        br = self.boss_rect(b)
        if math.hypot(br.centerx - cx, br.centery - cy) < r1 + br.w * 0.4 and b.get('sh', 0) <= 0 and b.get('atk') != 'dive':
          nv['boss'] = True
          b['hp'] -= NOVA['boss'] * self.boss_mult(b)
          b['flash'] = 4
          for _ in range(6):
            self.add_butterfly(br.centerx + random.randint(-30, 30), br.centery + random.randint(-30, 30), True)
      if nv['r'] < NOVA['r']:
        keep.append(nv)
    self.novas = keep
    keep = []
    for bf in getattr(self, 'butterflies', ()):         # the polymorphed foes flutter away
      bf['t'] += 1
      bf['vx'] += random.uniform(-0.25, 0.25)
      bf['vx'] = max(-2.6, min(1.2, bf['vx'])) - self.scroll_px * 0.004
      bf['vy'] = -0.9 + math.sin(bf['t'] * 0.18 + bf['ph']) * 1.4
      bf['x'] += bf['vx']
      bf['y'] += bf['vy']
      if bf['t'] < bf['life'] and bf['y'] > -20:
        keep.append(bf)
    self.butterflies = keep[-90:]

  def add_butterfly(self, x, y, small=False):
    self.butterflies.append({'x': float(x), 'y': float(y), 'vx': random.uniform(-2, 1), 'vy': -1.0, 't': 0, 'ph': random.uniform(0, 6.3),
                             'life': NOVA['fly_life'] + random.randint(-20, 30), 'col': random.choice(((255, 140, 230), (140, 230, 255), (255, 230, 120), (190, 150, 255), (150, 255, 190))),
                             'sz': random.uniform(0.6, 0.9) if small else random.uniform(0.9, 1.4)})

  def glamour(self, name, o):
    """a foe caught by the ring is turned into a flutter of butterflies (big foes take a couple of rings)"""
    rc = o['rect']
    if name in ('golems', 'cyclopes', 'catapults', 'trebuchets', 'ballistas', 'towers'):
      o['glam'] = o.get('glam', 0) + 1
      for _ in range(2):
        self.add_butterfly(rc.centerx + random.randint(-20, 20), rc.centery + random.randint(-20, 20), True)
      if o['glam'] < NOVA['chips']:
        return
    pts = {'towers': 15, 'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(name, 20)
    o['shattered'] = True
    o['swallowed'] = True                         # (it becomes butterflies instead of a corpse)
    if name == 'towers':
      o['crumbled'] = True
    self.score += int(pts * self.score_mult)
    self.dp += pts
    self.bounty_add('shatter')
    for _ in range(NOVA['flies'] + (2 if name in ('golems', 'cyclopes') else 0)):
      self.add_butterfly(rc.centerx + random.randint(-14, 14), rc.centery + random.randint(-14, 14))
    for _ in range(8):
      self.emit(rc.centerx, rc.centery, random.uniform(-3, 3), random.uniform(-3, 1), random.randint(2, 5), random.choice(((255, 255, 220), (255, 150, 240), (140, 240, 255))))

  # ------------------------------------------------------------------ Cockatrice: egg barrage + hatchlings
  def egg_breath(self):
    """a steady stream of eggs flies from the beak"""
    self.egg_cd = getattr(self, 'egg_cd', 0) - 1
    if self.egg_cd > 0 or len(self.eggs_shot) >= EGG_SHOT['max']:
      return
    self.egg_cd = EGG_SHOT['every']
    d = self.dragon
    hx, hy = breath_origin('COCKATRICE', d, self.flap_ph, self.vel, self.pitch)
    self.eggs_shot.append({'x': float(hx), 'y': float(hy), 'vx': random.uniform(10.0, 12.0), 'vy': random.uniform(-2.4, -0.6), 'rot': 0.0, 't': 0})
    AUDIO.play('whoosh', 0.25)

  def crack_egg(self, x, y, hatch):
    for k in range(8):                              # shell shards
      self.emit(x, y, random.uniform(-3, 3), random.uniform(-3.5, 0.5), random.randint(3, 5), random.choice(((250, 240, 220), (220, 200, 170), (255, 255, 255))))
    self.emit(x, y, 0, -0.5, 6, (255, 230, 120))
    if hatch and len(self.chicks) < EGG_SHOT['chicks']:
      self.chicks.append({'x': float(x), 'y': float(y), 'vx': random.uniform(-1, 1), 'vy': -3.0, 't': 0, 'pecks': 0, 'flap': random.uniform(0, 6)})
    AUDIO.play('shatter', 0.25)

  def update_eggs_shot(self):
    keep = []
    b = self.boss_live()
    br = self.boss_rect(b) if b else None
    for eg in getattr(self, 'eggs_shot', ()):
      eg['t'] += 1
      eg['vy'] += 0.18                              # a gentle arc
      eg['x'] += eg['vx']
      eg['y'] += eg['vy']
      eg['rot'] = (eg['rot'] + 22) % 360
      er = pygame.Rect(int(eg['x'] - 7), int(eg['y'] - 8), 14, 16)
      hit = None
      for name, o in self.foe_targets():
        if er.colliderect(o['rect']):
          hit = (name, o)
          break
      if hit is None and br is not None and er.colliderect(br):
        hit = ('boss', b)
      if hit is not None:                           # cracks open and a tiny cockatrice bursts out
        self.crack_egg(eg['x'], eg['y'], True)
        continue
      smash = eg['y'] >= GROUND_Y - 4
      if not smash:
        for lst in (self.fireballs, self.arrows, self.orbs):
          for p in lst:
            if not p.get('shattered') and abs(p['x'] - eg['x']) < 12 and abs(p['y'] - eg['y']) < 12:
              p['shattered'] = True
              smash = True
      if smash:
        self.crack_egg(eg['x'], eg['y'], False)
      elif eg['x'] < WIDTH + 30:
        keep.append(eg)
    self.eggs_shot = keep
    keep = []
    for c in getattr(self, 'chicks', ()):           # hatchlings hunt the nearest foe and peck it to bits
      c['t'] += 1
      best, bd, bname = None, 900.0 ** 2, None
      if c['t'] > 6:
        for name, o in self.foe_targets():
          dx, dy = o['rect'].centerx - c['x'], o['rect'].centery - c['y']
          dd = dx * dx + dy * dy
          if dd < bd:
            best, bd, bname = o, dd, name
      tx = ty = None
      if best is not None:
        tx, ty = best['rect'].center
      elif c['t'] > 6 and b is not None:
        tx, ty = br.center
      if tx is not None:
        dx, dy = tx - c['x'], ty - c['y']
        dist = math.hypot(dx, dy) or 1.0
        c['vx'] += dx / dist * 0.9
        c['vy'] += dy / dist * 0.9
        if dist < 20:
          if best is not None:
            self.hit_foe(bname, best, 'peck', 3, (230, 140, 50))
          else:
            if b.get('sh', 0) <= 0:
              b['hp'] -= 4.0 * self.boss_mult(b)
              b['flash'] = 3
          c['pecks'] += 1
          c['vx'], c['vy'] = -c['vx'] * 0.6, -4.0     # bounces off for the next peck
          self.emit(c['x'], c['y'], random.uniform(-2, 2), random.uniform(-2, 0), 4, (255, 230, 150))
      else:
        c['vy'] -= 0.05
      sp = math.hypot(c['vx'], c['vy'])
      if sp > 8.0:
        c['vx'] *= 8.0 / sp
        c['vy'] *= 8.0 / sp
      c['x'] += c['vx']
      c['y'] += c['vy']
      if c['pecks'] < EGG_SHOT['pecks'] and c['t'] < EGG_SHOT['chick_life'] and -40 < c['x'] < WIDTH + 40 and -40 < c['y'] < GROUND_Y:
        keep.append(c)
      else:
        self.burst(c['x'], c['y'], 6, 2, 3, 6, (255, 220, 140))
    self.chicks = keep

  # ------------------------------------------------------------------ Forest Dragon: bramble vines (no longer used)
  def vine_breath(self):
    """while breathing, thorny vines burst up out of the ground under foes ahead and crush them"""
    self.vine_cd = getattr(self, 'vine_cd', 0) - 1
    if self.vine_cd > 0 or len(self.vines) >= VINE['max']:
      return
    d = self.dragon
    taken = [v['o'] for v in self.vines]
    best, bd = None, 1e9
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        r = o['rect']
        if o.get('shattered') or any(q is o for q in taken) or r.centerx < d.right - 10 or r.x > WIDTH - 30 or r.centery < GROUND_Y - VINE['reach']:
          continue
        dd = r.centerx - d.centerx
        if dd < bd:
          best, bd = (name, o), dd
    if best is None:
      b = self.boss
      if b is not None and b['state'] == 'fighting' and not b.get('ghost') and 'boss' not in taken:
        br = self.boss_rect(b)
        if br.bottom > GROUND_Y - VINE['reach']:
          best = ('boss', 'boss')
    if best is None:
      return
    name, o = best
    if o == 'boss':
      x, ty = self.boss_rect(self.boss).centerx, max(GROUND_Y - VINE['reach'], self.boss_rect(self.boss).bottom - 30)
    else:
      x, ty = o['rect'].centerx, (o['rect'].top + 20 if name == 'towers' else o['rect'].centery)
    self.vines.append({'x': float(x), 'ty': float(ty), 'o': o, 'name': name, 't': 0, 'side': random.choice((-1, 1))})
    self.vine_cd = VINE['every']
    self.shake_for(3, 4)
    for _ in range(8):
      self.emit(x + random.uniform(-14, 14), GROUND_Y - 4, random.uniform(-2, 2), random.uniform(-3.5, -1), random.randint(5, 9), random.choice(((110, 84, 50), (80, 60, 36), (120, 170, 50))))

  def update_vines(self):
    keep = []
    g, hold = VINE['grow'], VINE['hold']
    for v in getattr(self, 'vines', ()):
      v['t'] += 1
      o = v['o']
      if v['t'] <= g and o != 'boss' and not o.get('shattered'):
        v['x'] = float(o['rect'].centerx)            # follows its prey while it grows
      else:
        v['x'] -= self.scroll_px
      if v['t'] == g:                              # the thorns snap shut
        if o == 'boss':
          b = self.boss
          if b is not None and b['state'] == 'fighting' and b.get('sh', 0) <= 0:
            b['hp'] -= 14.0 * self.boss_mult(b)
            b['flash'] = 3
        elif not o.get('shattered'):
          pts = {'towers': 15, 'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(v['name'], 20)
          self.apply_breath(o, pts, (120, 180, 50))
        self.burst(v['x'], v['ty'], 12, 4, 4, 8, random.choice(((120, 190, 50), (90, 140, 30), (200, 180, 70))))
        AUDIO.play('shatter', 0.4)
      top = GROUND_Y - (GROUND_Y - v['ty']) * self.vine_frac(v)
      for lst in (self.fireballs, self.arrows, self.orbs):   # shots that hit the stalk are knocked down
        for p in lst:
          if not p.get('shattered') and abs(p['x'] - v['x']) < 12 and top < p['y'] < GROUND_Y:
            p['shattered'] = True
      if v['t'] < g + hold + 8 and v['x'] > -40:
        keep.append(v)
    self.vines = keep

  def vine_frac(self, v):
    g, hold = VINE['grow'], VINE['hold']
    t = v['t']
    if t <= g:
      return t / float(g)
    if t <= g + hold:
      return 1.0
    return max(0.0, 1.0 - (t - g - hold) / 8.0)

  # ------------------------------------------------------------------ Clockwork Dragon: homing missiles
  def missile_breath(self):
    """while breathing, brass missiles launch from the jaws a few times a second"""
    self.missile_cd = getattr(self, 'missile_cd', 0) - 1
    if self.missile_cd > 0 or len(self.missiles) >= MISSILE['max']:
      return
    self.missile_cd = MISSILE['every']
    d = self.dragon
    hx, hy = breath_origin('CLOCKWORK', d, self.flap_ph, self.vel, self.pitch)
    side = getattr(self, 'missile_side', 1)
    self.missile_side = -side
    self.missiles.append({'x': float(hx), 'y': float(hy + side * 5), 'a': math.radians(-18 * side + random.uniform(-6, 6)), 'v': 6.0, 't': 0})
    AUDIO.play('launch', 0.35)
    self.burst(hx, hy + side * 5, 5, 2, 3, 6, (255, 200, 90))

  def missile_target(self, m):
    best, bd = None, 900.0 ** 2
    for name in GROUND_LISTS + ('enemies',):
      for o in getattr(self, name):
        if o.get('shattered') or o.get('swallowed') or o.get('state') == 'blown':
          continue
        r = o['rect']
        if r.centerx < m['x'] - 120 or r.x > WIDTH:
          continue
        dd = (r.centerx - m['x']) ** 2 + (r.centery - m['y']) ** 2
        if dd < bd:
          best, bd = (r.centerx, r.top + 30 if name == 'towers' else r.centery), dd
    b = self.boss
    if best is None and b is not None and b['state'] == 'fighting' and not b.get('ghost'):
      best = self.boss_rect(b).center
    return best

  def missile_blast(self, x, y):
    R = MISSILE['blast']
    self.booms.append({'x': x, 'y': y, 't': 0})
    self.burst(x, y, 18, 6, 4, 10, random.choice(((255, 180, 60), (255, 230, 120))))
    self.burst(x, y, 8, 3, 6, 12, (120, 120, 120))
    self.shake_for(4, 5)
    AUDIO.play('shatter', 0.4)
    blast = pygame.Rect(int(x - R), int(y - R), R * 2, R * 2)
    targets = ((self.towers, 15), (self.catapults, 25), (self.trebuchets, 25), (self.enemies, 35), (self.archers, 20), (self.mages, 20),
               (self.ballistas, 30), (self.golems, 40), (self.cyclopes, 40))
    for lst, pts in targets:
      for o in lst:
        if not o.get('shattered') and blast.colliderect(o['rect']):
          self.apply_breath(o, pts, (255, 180, 60))
    for lst in (self.fireballs, self.arrows, self.orbs):
      for p in lst:
        if abs(p['x'] - x) < R and abs(p['y'] - y) < R:
          p['shattered'] = True
    b = self.boss
    if b is not None and b['state'] == 'fighting' and not b.get('ghost') and blast.colliderect(self.boss_rect(b)) and b.get('sh', 0) <= 0:
      b['hp'] -= 5.0 * self.boss_mult(b)
      b['flash'] = 3

  def update_missiles(self):
    keep = []
    for m in getattr(self, 'missiles', ()):
      m['t'] += 1
      m['v'] = min(MISSILE['speed'], m['v'] + 0.5)
      tgt = self.missile_target(m) if m['t'] > 4 else None
      if tgt is not None:                           # turns toward its target, a little at a time
        want = math.atan2(tgt[1] - m['y'], tgt[0] - m['x'])
        da = (want - m['a'] + math.pi) % (2 * math.pi) - math.pi
        m['a'] += max(-MISSILE['turn'], min(MISSILE['turn'], da))
      m['x'] += math.cos(m['a']) * m['v']
      m['y'] += math.sin(m['a']) * m['v']
      if m['t'] % 2 == 0:
        self.emit(m['x'] - math.cos(m['a']) * 10, m['y'] - math.sin(m['a']) * 10, random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.2), random.randint(4, 7),
                  random.choice(((190, 190, 190), (150, 150, 150), (255, 170, 60))))
      hit = m['y'] >= GROUND_Y - 4
      mr = pygame.Rect(int(m['x'] - 7), int(m['y'] - 7), 14, 14)
      if not hit:
        for name in GROUND_LISTS + ('enemies',):
          for o in getattr(self, name):
            if not o.get('shattered') and mr.colliderect(o['rect']):
              hit = True
              break
          if hit:
            break
      if not hit:
        for lst in (self.fireballs, self.arrows, self.orbs):
          for p in lst:
            if not p.get('shattered') and abs(p['x'] - m['x']) < 14 and abs(p['y'] - m['y']) < 14:
              hit = True
              break
      b = self.boss
      if not hit and b is not None and b['state'] == 'fighting' and not b.get('ghost') and mr.colliderect(self.boss_rect(b)):
        hit = True
      if hit:
        self.missile_blast(m['x'], m['y'])
      elif m['t'] < MISSILE['life'] and -60 < m['x'] < WIDTH + 60 and -60 < m['y'] < GROUND_Y:
        keep.append(m)
    self.missiles = keep
    for bm in getattr(self, 'booms', ()):
      bm['t'] += 1
    self.booms = [bm for bm in getattr(self, 'booms', ()) if bm['t'] < 12]

  # ------------------------------------------------------------------ Wraith Wyrm: Soul Siphon
  def siphon_pool(self):
    for name in GROUND_LISTS + ('enemies',):
      if name == 'towers':
        continue
      for o in getattr(self, name):
        if not (o.get('shattered') or o.get('swallowed') or o.get('curse')):
          yield name, o

  def siphon_release(self):
    t = self.siphon
    self.siphon, self.siphon_line = None, None
    if t and t[1] is not None:
      t[1].pop('drain', None)                       # it shakes free

  def siphon_breath(self):
    """a ghostly tether locks onto the nearest foe ahead and drains it; when it dies the tether jumps to the next."""
    d = self.dragon
    hx, hy = breath_origin('WRAITH', d, self.flap_ph, self.vel, self.pitch)
    t = getattr(self, 'siphon', None)
    if t is not None:
      name, o = t
      if o is None:
        b = self.boss
        ok = b is not None and b['state'] == 'fighting' and not b.get('ghost')
      else:
        ok = not (o.get('shattered') or o.get('swallowed')) and -20 < o['rect'].centerx < WIDTH + 10 and o['rect'].centerx > hx - 60
      if not ok:
        self.siphon_release()
        t = None
    if t is None:
      best, bd = None, SIPHON['range'] ** 2
      for name, o in self.siphon_pool():
        r = o['rect']
        if r.centerx < hx - 30 or r.x > WIDTH - 20 or o.get('state') == 'blown':
          continue
        dd = (r.centerx - hx) ** 2 + (r.centery - hy) ** 2
        if dd < bd:
          best, bd = (name, o), dd
      b = self.boss
      if best is None and b is not None and b['state'] == 'fighting' and not b.get('ghost') and b.get('atk') != 'dive':
        best = ('boss', None)
      self.siphon = t = best
      if t is None:
        self.siphon_line = None
        return
    name, o = t
    if o is None:                                   # draining the boss
      b = self.boss
      br = self.boss_rect(b)
      tx, ty = br.centerx, br.centery
      if b.get('sh', 0) <= 0:
        b['hp'] -= 0.75 * self.boss_mult(b)
        b['hurt'] = b.get('hurt', 0) + 1
        if b['hurt'] % 14 == 1:
          b['flash'] = 3
    else:
      tx, ty = o['rect'].centerx, o['rect'].centery
      o['drain'] = o.get('drain', 0) + 1
      need = SIPHON['heavy'] if name in ('golems', 'cyclopes', 'catapults', 'trebuchets', 'ballistas') else SIPHON['time']
      if o['drain'] >= need:
        self.siphon_kill(name, o)
        self.siphon = None
    self.siphon_line = (hx, hy, tx, ty)
    if random.random() < 0.6:                       # soul motes flow down the tether
      u = random.random()
      self.emit(tx + (hx - tx) * u, ty + (hy - ty) * u + random.uniform(-6, 6), (hx - tx) * 0.02, (hy - ty) * 0.02, random.randint(3, 6),
                random.choice(((150, 245, 255), (230, 255, 255), (80, 190, 220))))

  def siphon_kill(self, name, o, soul=True, gen=1):
    """a drained foe dies and its soul rises out of the body as a wisp that hunts the nearest foe"""
    o['shattered'] = True
    o.pop('drain', None)
    pts = {'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(name, 20)
    self.score += int(pts * self.score_mult)
    self.dp += pts
    self.bounty_add('shatter')
    if self.breath:
      self.breath_timer = min(self.breath_time, self.breath_timer + SIPHON['refill'])   # each soul feeds the breath
    r = o['rect']
    self.burst(r.centerx, r.centery, 12, 4, 3, 7, random.choice(((150, 245, 255), (230, 255, 255))))
    AUDIO.play('shatter', 0.45)
    if soul and gen <= 2 and len(self.souls) < SIPHON['souls']:   # (a soul's own kills release one more generation)
      self.souls.append({'x': float(r.centerx), 'y': float(r.centery), 'vx': random.uniform(-0.5, 0.5), 'vy': -3.2, 't': 0, 'trail': [], 'gen': gen})

  def update_souls(self):
    keep = []
    for w in getattr(self, 'souls', ()):
      w['t'] += 1
      best, bd, bname = None, 700.0 ** 2, None
      if w['t'] > 10:                               # rises out of the body first
        for name, o in self.siphon_pool():
          dx, dy = o['rect'].centerx - w['x'], o['rect'].centery - w['y']
          dd = dx * dx + dy * dy
          if dd < bd:
            best, bd, bname = o, dd, name
      b = self.boss
      tx = ty = None
      if best is not None:
        tx, ty = best['rect'].centerx, best['rect'].centery
      elif w['t'] > 10 and b is not None and b['state'] == 'fighting' and not b.get('ghost'):
        br = self.boss_rect(b)
        tx, ty = br.centerx, br.centery
      if tx is not None:
        dx, dy = tx - w['x'], ty - w['y']
        dist = math.hypot(dx, dy) or 1.0
        w['vx'] += dx / dist * 1.0
        w['vy'] += dy / dist * 1.0
        if dist < 26:
          self.burst(w['x'], w['y'], 10, 3, 3, 7, (200, 255, 255))
          if best is not None:
            heavy = bname in ('golems', 'cyclopes', 'catapults', 'trebuchets', 'ballistas')
            if heavy and best.get('drain', 0) + 22 < SIPHON['heavy']:
              best['drain'] = best.get('drain', 0) + 22  # weakens big foes
            else:
              self.siphon_kill(bname, best, gen=w.get('gen', 1) + 1)
          else:
            b['hp'] -= 6 * self.boss_mult(b)
            b['flash'] = 3
          continue
      else:
        w['vy'] -= 0.04
        w['vx'] *= 0.96
      sp = math.hypot(w['vx'], w['vy'])
      if sp > 9.0:
        w['vx'] *= 9.0 / sp
        w['vy'] *= 9.0 / sp
      w['x'] += w['vx']
      w['y'] += w['vy']
      w['trail'].append((w['x'], w['y']))
      if len(w['trail']) > 9:
        w['trail'].pop(0)
      if w['t'] < SIPHON['soul_life'] and -60 < w['x'] < WIDTH + 80 and -80 < w['y'] < GROUND_Y:
        keep.append(w)
    self.souls = keep

  def curse_kill(self, o, name):
    """a cursed foe bursts into bones and rises as a wisp"""
    o['shattered'] = True
    o['swallowed'] = True                          # (no ordinary death animation)
    pts = {'towers': 15, 'catapults': 25, 'trebuchets': 25, 'enemies': 35, 'golems': 40, 'cyclopes': 40, 'ballistas': 30}.get(name, 20)
    self.score += int(pts * self.score_mult)
    self.dp += pts
    self.bounty_add('shatter')
    r = o['rect']
    cx, cy = r.centerx, r.centery if name != 'towers' else r.top + 30
    for _ in range(9 if name != 'towers' else 4):
      self.bones.append([float(cx), float(cy), random.uniform(-4, 4), random.uniform(-6, -1), random.uniform(0, 6.3), random.uniform(-0.4, 0.4), 40])
    self.burst(cx, cy, 10, 4, 3, 7, random.choice(((190, 110, 255), (240, 210, 255))))
    AUDIO.play('shatter', 0.5)
    if len(self.wisps) < CURSE['wisps']:
      self.wisps.append({'x': float(cx), 'y': float(cy), 'vx': random.uniform(-1, 3), 'vy': -3.0, 't': 0})
    for lst_name in GROUND_LISTS + ('enemies',):    # the curse jumps to anything standing close by
      if lst_name == 'towers':
        continue
      for q in getattr(self, lst_name):
        if q is o or q.get('shattered') or q.get('curse'):
          continue
        if abs(q['rect'].centerx - cx) < CURSE['spread'] and abs(q['rect'].centery - cy) < CURSE['spread']:
          q['curse'] = q['curse_max'] = max(18, CURSE['time'] // 2)

  def update_curse(self):
    sc = self.scroll_px
    for name in GROUND_LISTS + ('enemies',):        # cursed things wither, then burst
      for o in getattr(self, name):
        c = o.get('curse')
        if c and not o.get('shattered'):
          o['curse'] = c - 1
          if o['curse'] <= 0:
            self.curse_kill(o, name)
    keep = []
    for w in self.wisps:                           # wisps hunt the nearest foe
      w['t'] += 1
      best, bd = None, 600.0 ** 2
      for name in GROUND_LISTS + ('enemies',):
        if name == 'towers':
          continue
        for o in getattr(self, name):
          if o.get('shattered') or (o.get('curse', 0) and o['curse'] < 12):
            continue
          dx, dy = o['rect'].centerx - w['x'], o['rect'].centery - w['y']
          dd = dx * dx + dy * dy
          if dd < bd:
            best, bd = o, dd
      if best is not None:
        dx, dy = best['rect'].centerx - w['x'], best['rect'].centery - w['y']
        dist = math.sqrt(bd) or 1.0
        w['vx'] += dx / dist * 0.9
        w['vy'] += dy / dist * 0.9
        if dist < 24:
          best['curse'] = best['curse_max'] = 6      # it bursts a moment later (and makes a new wisp)
          self.burst(w['x'], w['y'], 8, 3, 3, 6, (220, 170, 255))
          continue
      else:
        w['vx'] += 0.25
        w['vy'] -= 0.05
      sp = math.hypot(w['vx'], w['vy'])
      if sp > 8.5:
        w['vx'] *= 8.5 / sp
        w['vy'] *= 8.5 / sp
      w['x'] += w['vx']
      w['y'] += w['vy']
      if w['t'] % 3 == 0:
        self.emit(w['x'], w['y'], -w['vx'] * 0.2, -w['vy'] * 0.2, 5, (180, 110, 250))
      if w['t'] < CURSE['wisp_life'] and -60 < w['x'] < WIDTH + 80 and -80 < w['y'] < GROUND_Y:
        keep.append(w)
    self.wisps = keep
    for bn in self.bones:                          # bone shards from a cursed burst
      bn[0] += bn[2] - sc * 0.5
      bn[1] += bn[3]
      bn[3] += 0.45
      bn[4] += bn[5]
      bn[6] -= 1
      if bn[1] > GROUND_Y - 4:
        bn[1] = GROUND_Y - 4
        bn[3] *= -0.3
        bn[2] *= 0.6
    self.bones = [bn for bn in self.bones if bn[6] > 0]

  # ------------------------------------------------------------------ Void dragon: Singularity
  def void_breath(self):
    """while breathing, a black hole opens ahead of the dragon (one at a time) and stays open as long as you hold."""
    d = self.dragon
    live = [h for h in self.holes if h['state'] == 'open']
    if live:
      live[0]['hold'] = 12                                  # stays open as long as you keep breathing
      return
    closing = [h for h in self.holes if h['state'] == 'closing']
    if closing:                                             # breathing again before it shut: it re-opens
      h = closing[0]
      h['state'], h['hold'] = 'open', 12
      return
    x = d.right + 250
    y = max(90, min(GROUND_Y - 90, d.centery))
    self.holes.append({'x': float(x), 'y': float(y), 't': 0, 'state': 'open', 'R': 0.0, 'hold': 3, 'ct': 0})
    AUDIO.play('whoosh')
    self.shake_for(4, 4)

  def swallow(self, o, pts):
    o['shattered'] = True
    o['swallowed'] = True
    self.score += int(pts * self.score_mult)
    self.dp += pts
    self.bounty_add('shatter')
    cx, cy = o['rect'].center if 'rect' in o else (o['x'], o['y'])
    self.burst(cx, cy, 10, 3, 3, 7, random.choice(((200, 120, 255), (255, 220, 255), (120, 80, 220))))

  def update_holes(self):
    sc = self.scroll_px
    for h in self.holes:
      h['t'] += 1
      if h['state'] == 'open':                              # loosely follows the dragon's altitude, staying ahead of it
        d = self.dragon
        ty = max(90, min(GROUND_Y - 90, d.centery))
        h['y'] += (ty - h['y']) * 0.06
        h['x'] += (d.right + 250 - h['x']) * 0.05
      else:
        h['x'] -= sc * 0.25
      if h['state'] == 'open':
        h['hold'] -= 1
        h['R'] = min(VOID_HOLE['r'], h['R'] + 3.0)
        self.hole_pull(h)
        if h['hold'] <= 0 or h['t'] > VOID_HOLE['life']:
          h['state'] = 'closing'
          h['ct'] = 0
          self.shake_for(8, 8)
          AUDIO.play('shatter', 0.5)
          self.burst(h['x'], h['y'], 26, 7, 3, 8, (220, 180, 255))
      else:
        h['ct'] += 1
        h['R'] = max(0.0, h['R'] - 2.0)
    self.holes = [h for h in self.holes if not (h['state'] == 'closing' and h['ct'] > VOID_HOLE['close']) and h['x'] > -200]

  def hole_pull(self, h):
    cx, cy, R, rng = h['x'], h['y'], h['R'], VOID_HOLE['pull']
    def pull(dx, dy, dist, k=1.0):
      f = ((1 - dist / rng) * 10.0 + 2.0) * k
      sw = 0.18 * f                                        # a little swirl around the hole
      return dx / dist * f - dy / dist * sw, dy / dist * f + dx / dist * sw
    for e in self.enemies:                                 # flyers are dragged in and swallowed
      if e.get('shattered') or e.get('state') == 'blown':
        continue
      r = e['rect']
      dx, dy = cx - r.centerx, cy - r.centery
      dist = math.hypot(dx, dy) or 1.0
      if dist < rng:
        mx, my = pull(dx, dy, dist)
        e['fx'] = e.get('fx', float(r.x)) + mx
        r.x = int(e['fx'])
        r.y += int(round(my))
        for key in ('by', 'fy'):
          if key in e:
            e[key] += my
        if dist < R + 12:
          self.swallow(e, 35)
    for name in ('archers', 'mages'):                      # small ground units get lifted off their feet
      for o in getattr(self, name):
        if o.get('shattered'):
          continue
        r = o['rect']
        dx, dy = cx - r.centerx, cy - r.centery
        dist = math.hypot(dx, dy) or 1.0
        if dist < rng * 0.8:
          mx, my = pull(dx, dy, dist, 0.7)
          r.x += int(round(mx))
          r.y += int(round(my))
          o['perch'] = None
          o['fall'] = 0.0                                  # drops back down if the hole closes first
          if dist < R + 14:
            self.swallow(o, 20)
    for name in ('towers', 'catapults', 'trebuchets', 'ballistas', 'golems', 'cyclopes'):   # heavy things get torn apart
      for o in getattr(self, name):
        if o.get('shattered'):
          continue
        r = o['rect']
        near = max(r.left - cx, cx - r.right, 0) ** 2 + max(r.top - cy, cy - r.bottom, 0) ** 2
        if near < (R * 2.6) ** 2:
          o['void'] = o.get('void', 0) + 1
          if o['void'] % 6 == 0:
            self.emit(r.centerx + random.randint(-20, 20), r.top + random.randint(0, 40), (cx - r.centerx) * 0.03, (cy - r.top) * 0.03, random.randint(4, 8), (200, 140, 255))
          if o['void'] > 18:
            o['shattered'] = True
            self.score += 25 * self.score_mult
            self.bounty_add('shatter')
            self.dp += 25
    for lst, rr in ((self.arrows, 10), (self.fireballs, 14), (self.orbs, 12), (self.spears, 10)):   # shots are sucked in too
      for p in lst:
        if p.get('shattered'):
          continue
        dx, dy = cx - p['x'], cy - p['y']
        dist = math.hypot(dx, dy) or 1.0
        if dist < rng:
          mx, my = pull(dx, dy, dist, 1.6)
          p['x'] += mx
          p['y'] += my
          if 'vx' in p:
            p['vx'] *= 0.9
            p['vy'] *= 0.9
          if dist < R + rr:
            p['shattered'] = True
            self.burst(p['x'], p['y'], 4, 2, 2, 5, (220, 180, 255))
    b = self.boss
    if b and b['state'] == 'fighting' and not b.get('ghost') and b.get('atk') != 'dive':
      br = self.boss_rect(b)
      if math.hypot(br.centerx - cx, br.centery - cy) < rng * 0.65 and b.get('sh', 0) <= 0:
        b['hp'] -= 0.9 * self.boss_mult(b)
        b['hurt'] = b.get('hurt', 0) + 1
        if b['hurt'] % 14 == 1:
          b['flash'] = 3

  def update_breath(self):
    d, sel = self.dragon, self.selected
    if sel == "COSMIC":
      self.void_breath()
      return
    if sel == "SKELETAL":
      self.curse_breath()
      return
    if sel == "WRAITH":
      self.siphon_breath()
      return
    if sel == "CLOCKWORK":
      self.missile_breath()
      return
    if sel == "FOREST":
      self.leaf_breath()
      return
    if sel == "COCKATRICE":
      self.egg_breath()
      return
    if sel == "EAGLE":
      return                                     # (its special works by tapping: see talon_tap)
    if sel == "WHALE":
      self.maw_breath()
      return
    if sel == "FEY":
      self.nova_breath()
      return
    beam = pygame.Rect(d.right, d.y - 45, 400, 130)
    if sel == "YELLOW":
      self.chain_lightning(*breath_origin(sel, d, getattr(self, 'flap_ph', 0.0), self.vel, self.pitch))
    elif sel == "SILVER":
      beam = pygame.Rect(d.right, d.y - 30, 260, 90)       # the gust itself still knocks shots away
    elif sel == "UNICORN":
      beam = self.rainbow_beam()
    targets = ((self.towers, 15, STONE_DARK), (self.catapults, 25, WOOD_BROWN), (self.trebuchets, 25, WOOD_BROWN), (self.enemies, 35, (100, 100, 100)),
                   (self.archers, 20, CLOTH_DARK), (self.mages, 20, MAGIC_PURPLE), (self.ballistas, 30, WOOD_DARK), (self.golems, 40, STONE_DARK), (self.cyclopes, 40, WOOD_BROWN))
    for lst, pts, col in (() if sel in ("YELLOW", "SILVER") else targets):
      for o in lst:
        if beam.colliderect(o['rect']):
          self.apply_breath(o, pts, random.choice(RAINBOW) if sel == "UNICORN" else col)
    for fb in self.fireballs:
      if beam.colliderect(pygame.Rect(int(fb['x'] - 11), int(fb['y'] - 11), 22, 22)):
        self.apply_breath(fb, 5, (255, 100, 0))
    for o in self.orbs:
      if beam.colliderect(pygame.Rect(int(o['x'] - 10), int(o['y'] - 10), 20, 20)):
        self.apply_breath(o, 5, MAGIC_PURPLE)
    for a in self.arrows:
      if beam.colliderect(pygame.Rect(int(a['x'] - 15), int(a['y'] - 2), 30, 4)):
        self.apply_breath(a, 2, STONE_LIGHT)
    b = self.boss
    if sel != "YELLOW" and b and b['state'] == 'fighting' and b.get('atk') != 'dive' and not b.get('ghost') and beam.colliderect(self.boss_rect(b)):
      if b.get('sh', 0) > 0:
        if random.random() < 0.5:
          self.emit(b['x'] + 5, b['y'] + random.randint(10, 140), random.uniform(-3, 0), random.uniform(-2, 2), random.randint(4, 8), (255, 120, 90))
        return
      b['hp'] -= (1.2 if sel in ("RED", "CHINESE", "GREEN", "ALIEN") else 1.0 if sel == "UNICORN" else 0.8) * self.boss_mult(b)
      b['hurt'] = b.get('hurt', 0) + 1
      if b['hurt'] % 14 == 1:
        b['flash'] = 3
      self.emit(b['x'] + random.randint(0, 50), b['y'] + random.randint(0, 50), random.uniform(-2, 2), random.uniform(-2, 2), random.randint(5, 10), (255, 50, 50))

  def rainbow_beam(self):
    """Evil Unicorn: a straight rainbow beam from the horn that shoots out to the edge of the screen."""
    d = self.dragon
    hx, hy = breath_origin('UNICORN', d, self.flap_ph, self.vel, self.pitch)
    self.beam_len = min(WIDTH + 20 - hx, getattr(self, 'beam_len', 0) + 120)     # shoots out fast, then holds
    ln = max(1, int(self.beam_len))
    if random.random() < 0.7:                    # glitter along the beam
      self.emit(hx + random.uniform(10, ln), hy + random.uniform(-12, 12), random.uniform(-2, 1), random.uniform(-1.4, 1.4), random.randint(3, 6),
                random.choice(RAINBOW + ((255, 255, 255),)))
    return pygame.Rect(hx, hy - 18, ln, 36)

  def shatter_frozen(self, o):
    if o.get('shattered'):
      return
    o['shattered'] = True
    cx, cy = o['rect'].center if 'rect' in o else (o['x'], o['y'])
    self.burst(cx, cy, 26, 6, 3, 9, random.choice(((210, 248, 255), (150, 226, 246), (255, 255, 255))))
    self.burst(cx, cy, 12, 4, 3, 7, (66, 140, 190))
    AUDIO.play('shatter', 0.7)
    self.shake_for(8, 10)
    self.score += 10 * self.score_mult
    self.bounty_add('shatter')

  def apply_breath(self, o, pts, color):
    if o.get('state', 'normal') != 'normal':
      return
    new_state = BREATH_STATE.get(self.selected)
    if new_state:
      o['state'] = new_state
      if new_state == 'frozen':
        o['vy'] = 0.0
        self.burst(*((o['rect'].center) if 'rect' in o else (o['x'], o['y'])), 8, 3, 3, 6, (210, 248, 255))
      if new_state == 'stasis':
        o['st'] = STASIS_FRAMES
        self.burst(*( (o['rect'].center) if 'rect' in o else (o['x'], o['y']) ), 6, 3, 3, 6, (255, 225, 120))
    else:
      o['shattered'] = True
      self.shake_for(10, 12)
      AUDIO.play('shatter', 0.7)
      cx, cy = o['rect'].center if 'rect' in o else (o['x'], o['y'])
      self.burst(cx, cy, 24, 6, 8, 16, SHATTER_TINT.get(self.selected, color))
      self.bounty_add('shatter')
      if 'rect' in o:
        self.score += int(pts * self.score_mult)
    self.dp += pts

  def griffin_ai(self, b):
    """Griffin: feather volleys, wind gusts, a diving strike and (new) a golden lightning bolt.
    Thunder Bolt: it tucks its wings, crackles with gold, glides to your height, marks the line
    with a flickering golden trail and then fires a bolt straight across the screen along it."""
    d = self.dragon
    atk = b.setdefault('atk', 'idle')
    b['at'] = b.get('at', 0) + 1
    at = b['at']
    pushed = False
    for w in b['waves']:
      w['x'] -= 11
      w['h'] = min(170, w['h'] + 3)
      if abs(w['x'] - d.centerx) < 34 and abs(d.centery - w['y']) < w['h']:
        pushed = True
    b['waves'] = [w for w in b['waves'] if w['x'] > -40]
    if pushed:
      d.x = max(40, d.x - 5)
    elif d.x < 150:
      d.x = min(150, d.x + 2)
    if b.get('stun', 0) > 0:
      b['stun'] -= 1
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    b['anim'], b['fi'] = 'fly', int(b['timer'] * 7)
    b['tilt'] = 0
    if atk == 'idle':
      b['cool'] = b.get('cool', 70) - 1
      if b['cool'] <= 0:
        seq = ['volley', 'gust', 'thunder', 'volley', 'dive'] if b['hp'] <= b['max_hp'] / 2 else ['volley', 'thunder', 'volley', 'dive']
        nxt = seq[b.get('seq', 0) % len(seq)]
        b['seq'] = b.get('seq', 0) + 1
        b['atk'] = {'volley': 'volley', 'gust': 'gust_warn', 'dive': 'dive_warn', 'thunder': 'thunder'}[nxt]
        b['at'] = 0
        b['lock'], b['bolt'] = None, 0
        if nxt != 'volley':
          AUDIO.play('roar', 0.7)
    elif atk == 'volley':
      b['fi'] = int(at * 0.55)                     # quick, hard wing beats fling the feathers
      if 24 <= at <= 34 and (at - 24) % 2 == 0:
        k = (at - 24) // 2
        sx, sy = b['x'] + 34 + k * 9, b['y'] + 6 + k * 5
        base = math.atan2(d.centery - sy, d.centerx - sx)
        ang = base + (k - 2.5) * 0.11
        sp = 8.5
        self.arrows.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(ang) * sp, 'vy': math.sin(ang) * sp, 'state': 'normal', 'kind': 'feather'})
      if at >= 46:
        b['atk'] = 'idle'
        b['cool'] = 70
    elif atk == 'thunder':
      b['anim'] = 'attack'
      if at < 25:                                   # wings tuck in
        b['fi'] = at // 5
      elif at < 61:                                 # crackling with golden lightning
        b['fi'] = 5 + (at - 25) // 4
        b['flash'] = 0
        if at < 44:
          ty = max(20.0, min(GROUND_Y - 120.0, d.centery - 52.0))
          b['y'] += (ty - b['y']) * 0.12           # lines up with you...
        elif b.get('lock') is None:
          b['lock'] = griffin_beak(b)[1]            # ...then locks the line
          AUDIO.play('roar', 0.5)
        if self.tick and random.random() < 0.6:
          self.emit(b['x'] + random.randint(10, 90), b['y'] + random.randint(10, 90), random.uniform(-2, 2), random.uniform(-2, 2), random.randint(3, 6),
                    random.choice(((255, 214, 60), (255, 244, 160), (255, 255, 255))))
      elif at < 76:                                 # the bolt
        b['fi'] = 14 + min(2, (at - 61) // 5)
        if at == 61:
          b['bolt'] = 14
          self.shake_for(8, 10)
          AUDIO.play('thunder', 0.8)
        if b.get('bolt', 0) > 0:
          b['bolt'] -= 1
          ly = b['lock']
          if b['bolt'] > 3 and not self.dash_inv and d.right < griffin_beak(b)[0] and d.top - 14 < ly < d.bottom + 14:
            if self.shield_active:
              self.shield_active = False
              self.burst(d.centerx, d.centery, 16, 6, 4, 10, (255, 230, 90))
              AUDIO.play('shatter', 0.6)
            else:
              self.dead = True
      else:
        b['atk'], b['at'], b['cool'], b['lock'], b['bolt'] = 'idle', 0, 70, None, 0
    elif atk == 'dive_warn':
      b['anim'], b['fi'] = 'attack', min(4, at // 8)
      b['flash'] = 3 if at % 12 < 6 else 0
      if at == 26:
        b['ty'] = max(10, min(GROUND_Y - 100, d.centery - 50))
      if at >= 40:
        b['atk'] = 'dive'
        b['at'] = 0
        b['sx'], b['sy'] = b['x'], b['y']
        b['ty'] = b.get('ty', b['y'])
        b['hit'] = False
    elif atk == 'dive':
      u = min(1.0, at / 22.0)
      b['x'] = b['sx'] - (b['sx'] + 170) * u
      b['y'] = b['sy'] + (b['ty'] - b['sy']) * min(1.0, u * 1.4)
      b['anim'], b['fi'] = 'attack', 4                # wings folded tight
      b['tilt'] = -18 if b['ty'] > b['sy'] else 18
      if not b['hit'] and d.colliderect(pygame.Rect(int(b['x']) + 8, int(b['y']) + 16, 84, 70)):
        if self.shield_active:
          b['hit'] = True
        else:
          self.dead = True
      if at >= 24:
        b['atk'] = 'recover'
        b['at'] = 0
        b['x'] = WIDTH + 120.0
    elif atk == 'recover':
      b['x'] -= 7
      if b['x'] <= BOSS_X:
        b['x'] = BOSS_X
        b['atk'] = 'idle'
        b['cool'] = 110
        b['stun'] = 90
    elif atk == 'gust_warn':
      b['fi'] = 2                                   # wings raised
      b['flash'] = 3 if at % 8 < 4 else 0
      if at >= 30:
        b['atk'] = 'gust'
        b['at'] = 0
    elif atk == 'gust':
      b['fi'] = int(at * 0.8)                       # powerful downstrokes
      if at in (2, 12, 22):
        b['waves'].append({'x': b['x'] + 10.0, 'y': b['y'] + 50.0, 'h': 60.0})
      if at >= 40:
        b['atk'] = 'idle'
        b['cool'] = 80

  def hydra_ai(self, b):
    """Hydra: Twin Breath (the fire and ice heads take turns spitting bolts), Fire & Ice Barrage (a gout of fire,
    then a rain of ice shards) and Elemental Lunge (it rears up, then lunges across the sky breathing both)."""
    d = self.dragon
    b['at'] += 1
    at, atk = b['at'], b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    fast = b['hp'] <= b['max_hp'] / 2
    b['anim'], b['fi'] = 'fly', int(b['timer'] * 4)
    if atk not in ('lunge_warn', 'lunge', 'return'):
      b['y'] += (b['by'] + math.sin(b['timer'] * 0.9) * 60 - b['y']) * 0.15
    (fx_, fy_), (ix_, iy_) = hyd_mouths(b)
    def aim(x, y):
      return math.atan2(d.centery - y, d.centerx - x)
    if atk == 'idle':
      b['cool'] -= 1
      if b['cool'] <= 0:
        seq = ['twin', 'barrage', 'lunge', 'twin', 'barrage'] if fast else ['twin', 'barrage', 'twin', 'lunge']
        nxt = seq[b['seq'] % len(seq)]
        b['seq'] += 1
        b['at'] = 0
        b['atk'] = 'lunge_warn' if nxt == 'lunge' else nxt
        AUDIO.play('roar', 0.6)
    elif atk == 'twin':                             # heads take turns: fire bolt, ice shard, fire bolt...
      b['anim'], b['fi'] = 'twin', min(20, at // 4)
      if 8 <= at <= 72 and (at - 8) % (6 if fast else 8) == 0:
        k = (at - 8) // (6 if fast else 8)
        if k % 2 == 0:
          a = aim(fx_, fy_)
          self.fireballs.append({'x': float(fx_), 'y': float(fy_), 'vx': math.cos(a) * 8.5, 'vy': math.sin(a) * 8.5, 'state': 'normal', 'straight': True})
        else:
          a = aim(ix_, iy_)
          self.arrows.append({'x': float(ix_), 'y': float(iy_), 'vx': math.cos(a) * 10.0, 'vy': math.sin(a) * 10.0, 'state': 'normal', 'kind': 'icicle'})
        AUDIO.play('whoosh', 0.4)
      if at >= 84:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 45 if fast else 70
    elif atk == 'barrage':                          # a gout of fire, then ice shards rain down ahead
      b['anim'], b['fi'] = 'barrage', min(20, at // 4)
      if at in (8, 14, 20):
        a = aim(fx_, fy_)
        self.fireballs.append({'x': float(fx_), 'y': float(fy_), 'vx': math.cos(a) * 9.5, 'vy': math.sin(a) * 9.5, 'state': 'normal', 'straight': True})
      if 32 <= at <= 72 and at % 4 == 0:
        self.arrows.append({'x': float(ix_), 'y': float(iy_), 'vx': random.uniform(-10.0, -4.5), 'vy': random.uniform(-1.0, 3.5), 'state': 'normal', 'kind': 'icicle_fall'})
      if at >= 84:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 45 if fast else 70
    elif atk == 'lunge_warn':                       # rears up, flashing, and lines up with you
      b['anim'], b['fi'] = 'lunge', min(12, int(at * 0.3))
      b['flash'] = 3 if at % 10 < 5 else 0
      if at < 30:
        b['ty'] = max(10.0, min(GROUND_Y - 150.0, d.centery - 65.0))
      b['y'] += (b.get('ty', b['y']) - b['y']) * 0.1
      if at >= 42:
        b['atk'], b['at'], b['hit'] = 'lunge', 0, False
        AUDIO.play('whoosh', 0.9)
    elif atk == 'lunge':                            # tears across the sky breathing fire and frost together
      b['anim'], b['fi'] = 'lunge', 13 + (at // 3) % 4
      b['x'] -= 16 * self.ts
      if self.tick:
        self.emit(b['x'] + random.randint(-40, 0), b['y'] + random.randint(30, 90), random.uniform(-2, 0), random.uniform(-1, 1), random.randint(6, 11),
                  random.choice(((255, 140, 30), (255, 210, 90), (150, 220, 255), (220, 245, 255))))
      if not self.dash_inv and d.colliderect(pygame.Rect(int(b['x']) - 50, int(b['y']) + 20, 190, 95)):
        if self.shield_active:
          if not b.get('hit'):
            self.shield_active = False
            self.burst(d.centerx, d.centery, 16, 6, 4, 10, (200, 230, 255))
            AUDIO.play('shatter', 0.6)
          b['hit'] = True
        else:
          self.dead = True
      if b['x'] < -300:
        b['x'], b['y'], b['hit'] = WIDTH + 90.0, b['by'], False
        b['atk'], b['at'] = 'return', 0
    elif atk == 'return':
      b['x'] -= 6
      if b['x'] <= BOSS_X:
        b['x'] = float(BOSS_X)
        b['atk'], b['at'], b['cool'] = 'idle', 0, 60 if fast else 90

  def beholder_ai(self, b):
    """Beholder: Death Ray (the great eye charges, the beholder lines the ray up on you, then fires it across the sky)
    and Seeker Eyes (its eyestalks stretch out and spit eyeballs that turn and chase you)."""
    d = self.dragon
    b['at'] += 1
    at, atk = b['at'], b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    fast = b['hp'] <= b['max_hp'] / 2
    if atk not in ('laser',):
      b['y'] += (b['by'] + math.sin(b['timer'] * 0.8) * 80 - b['y']) * 0.12
    b['anim'], b['fi'] = 'hover', int(b['timer'] * 7)
    if atk == 'idle':
      b['ray'] = False
      b['cool'] -= 1
      if b['cool'] <= 0:
        seq = ['laser', 'eyes', 'laser', 'eyes', 'eyes'] if fast else ['eyes', 'laser', 'eyes', 'laser']
        b['atk'] = seq[b['seq'] % len(seq)]
        b['seq'] += 1
        b['at'] = 0
        if b['atk'] == 'laser':
          AUDIO.play('roar', 0.5)
    elif atk == 'eyes':                             # eyestalks stretch and spit heat-seeking eyeballs
      b['anim'], b['fi'] = 'eyes', min(20, at // 4)
      if at in (52, 56, 60) or (fast and at == 64):
        for k in range(2 if not fast else 3):
          px, py = BEH_STALKS[(at // 4 + k * 2) % len(BEH_STALKS)]
          sx, sy = beh_point(b, (px, py))
          a0 = random.uniform(-1.2, 1.2)           # flies out away from the body first, then turns on you
          self.orbs.append({'x': float(sx), 'y': float(sy), 'vx': math.cos(a0) * 4.5, 'vy': math.sin(a0) * 4.5, 'state': 'normal',
                            'col': (90, 255, 120), 'r': 11, 'home': False, 'kind': 'seeker', 'life': 0, 'spd': 4.5 + (0.8 if fast else 0.0)})
        AUDIO.play('whoosh', 0.5)
      if at >= 90:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 45 if fast else 70
    elif atk == 'laser':                            # charges, lines the ray up on you, fires
      fi = min(20, at // 4)
      b['anim'], b['fi'] = 'laser', fi
      on = BEH_LASER_ON[fi]
      sx, sy, _a = beam_line(b)
      want = math.atan2(d.centery - sy, d.centerx - sx)
      want = math.pi - max(-0.5, min(0.5, math.pi - want)) if want > 0 else -math.pi + max(-0.5, min(0.5, want + math.pi))
      if at < 26:                                   # rises or sinks toward your height and takes aim
        b['y'] += max(-6.0, min(6.0, (d.centery - sy) * 0.07))
        b['ang'] = want
      elif fast and on:                             # wounded, it sweeps the ray slowly after you
        da = (want - b['ang'] + math.pi) % (2 * math.pi) - math.pi
        b['ang'] += max(-0.006, min(0.006, da))
      b['y'] = max(-40.0, min(GROUND_Y - 150.0, b['y']))
      if at < 32 and self.tick and random.random() < 0.6:   # green light gathering at the great eye
        ex, ey = beh_point(b, (33, 43))
        a = random.uniform(0, 6.3)
        self.emit(ex + math.cos(a) * 34, ey + math.sin(a) * 34, -math.cos(a) * 2.2, -math.sin(a) * 2.2, random.randint(3, 5), random.choice(((90, 255, 120), (220, 255, 220))))
      if on and not b.get('ray'):
        AUDIO.play('laser', 0.8)
        self.shake_for(10, 12)
      b['ray'] = bool(on)
      if on:
        sx, sy, _a = beam_line(b)
        ang = b.get('ang', math.pi)
        px, py = d.centerx - sx, d.centery - sy
        along = px * math.cos(ang) + py * math.sin(ang)
        perp = abs(-px * math.sin(ang) + py * math.cos(ang))
        if along > -20 and perp < BEH_HALF * BEH_SCALE + 12 and not self.dash_inv:
          if self.shield_active:
            self.shield_active = False
            self.burst(d.centerx, d.centery, 16, 6, 4, 10, (120, 255, 140))
            AUDIO.play('shatter', 0.6)
          else:
            self.dead = True
      if at >= 84:
        b['ray'] = False
        b['atk'], b['at'], b['cool'] = 'idle', 0, 50 if fast else 80

  def jabber_ai(self, b):
    """Jabberwock: spit volleys, a sweeping green burble beam and a charge straight across the sky.
    Every attack uses its flapping flight frames, so the wings keep beating while it attacks."""
    d = self.dragon
    b['at'] += 1
    at, atk = b['at'], b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    fast = b['hp'] <= b['max_hp'] / 2
    b['fi'] = int(b['timer'] * 7)
    if atk not in ('charge_warn', 'charge', 'return'):
      b['y'] += (b['by'] + math.sin(b['timer'] * 1.1) * 70 - b['y']) * 0.2
    if atk == 'idle':
      b['cool'] -= 1
      if b['cool'] <= 0:
        seq = ['spit', 'beam', 'burble', 'charge', 'beam', 'spit'] if fast else ['spit', 'beam', 'spit', 'charge']
        nxt = seq[b['seq'] % len(seq)]
        b['seq'] += 1
        b['at'], b['beam'] = 0, None
        b['atk'] = 'charge_warn' if nxt == 'charge' else nxt
        if nxt in ('beam', 'charge'):
          AUDIO.play('roar', 0.6)
    elif atk in ('spit', 'burble'):
      b['fi'] = int(at * 0.5)                       # quicker, harder wing beats while it spits
      shots = (14, 24, 34) if atk == 'spit' else (26,)
      if at in shots:
        mx, my = jab_mouth(b)
        a0 = math.atan2(d.centery - my, d.centerx - mx)
        fan = (0.0,) if atk == 'spit' else tuple((k - 3) * 0.17 for k in range(7))
        spd = (8.0 if atk == 'spit' else 6.0) + (1.0 if fast else 0.0)
        for k in fan:
          self.orbs.append({'x': float(mx), 'y': float(my), 'vx': math.cos(a0 + k) * spd, 'vy': math.sin(a0 + k) * spd, 'state': 'normal',
                            'col': (255, 120, 230), 'r': 12, 'home': False, 'kind': 'jspit', 'fr': 0.0})
        b['spit_t'] = at
        AUDIO.play('whoosh', 0.6)
      if at >= 50:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 50 if fast else 75
    elif atk == 'beam':
      mx, my = jab_mouth(b)
      want = math.atan2(d.centery - my, d.centerx - mx)
      if at < 34:                                   # gathers a burble of green energy and takes aim
        b['ang'] = want
        if self.tick and random.random() < 0.7:
          self.emit(mx + random.uniform(-10, 10), my + random.uniform(-10, 10), random.uniform(-1, 1), random.uniform(-1, 1), random.randint(3, 6),
                    random.choice(((120, 255, 90), (200, 255, 170), (40, 200, 60))))
      elif at < 84:                                 # fires, then sweeps slowly toward you
        if at == 34:
          b['beam'] = True
          self.shake_for(8, 10)
          AUDIO.play('thunder', 0.6)
        da = (want - b['ang'] + math.pi) % (2 * math.pi) - math.pi
        b['ang'] += max(-0.011, min(0.011, da))
        px, py = d.centerx - mx, d.centery - my
        along = px * math.cos(b['ang']) + py * math.sin(b['ang'])
        perp = abs(-px * math.sin(b['ang']) + py * math.cos(b['ang']))
        if along > 0 and perp < 22 and not self.dash_inv:
          if self.shield_active:
            self.shield_active = False
            self.burst(d.centerx, d.centery, 16, 6, 4, 10, (150, 255, 120))
            AUDIO.play('shatter', 0.6)
          else:
            self.dead = True
      else:
        b['beam'] = None
        b['atk'], b['at'], b['cool'] = 'idle', 0, 55 if fast else 80
    elif atk == 'charge_warn':                      # rears, flashes and lines up with you
      b['flash'] = 3 if at % 10 < 5 else 0
      if at < 28:
        b['ty'] = max(10.0, min(GROUND_Y - 150.0, d.centery - 65.0))
      b['y'] += (b.get('ty', b['y']) - b['y']) * 0.1
      if at >= 40:
        b['atk'], b['at'], b['hit'] = 'charge', 0, False
        AUDIO.play('whoosh', 0.9)
    elif atk == 'charge':                           # beats its wings hard and tears straight across the sky
      b['fi'] = int(at * 0.8)
      b['x'] -= 17 * self.ts
      if self.tick:
        self.emit(b['x'] + 110, b['y'] + random.randint(30, 100), random.uniform(2, 5), random.uniform(-1, 1), random.randint(8, 13), (150, 170, 120))
      if not self.dash_inv and d.colliderect(pygame.Rect(int(b['x']) + 15, int(b['y']) + 25, 100, 85)):
        if self.shield_active:
          if not b.get('hit'):
            self.shield_active = False
            self.burst(d.centerx, d.centery, 16, 6, 4, 10, (180, 200, 140))
            AUDIO.play('shatter', 0.6)
          b['hit'] = True
        else:
          self.dead = True
      if b['x'] < -260:
        b['x'], b['y'], b['hit'] = WIDTH + 80.0, b['by'], False
        b['atk'], b['at'] = 'return', 0
    elif atk == 'return':
      b['x'] -= 6
      if b['x'] <= BOSS_X:
        b['x'] = float(BOSS_X)
        b['atk'], b['at'], b['cool'] = 'idle', 0, 60 if fast else 90

  def boss_mult(self, b):
    return BOSS_RESIST.get(b.get('type'), {}).get(self.selected, 1.0)

  def boss_rect(self, b):
    if b['type'] == 'hydra':
      return pygame.Rect(int(b['x']), int(b['y']), 150, 130)
    if b['type'] == 'beholder':
      return pygame.Rect(int(b['x']), int(b['y']) + 8, 110, 120)
    if b['type'] == 'jabber':
      return pygame.Rect(int(b['x']), int(b['y']), 130, 130)
    if b['type'] == 'phoenix':
      return pygame.Rect(int(b['x']), int(b['y']), 110, 110)
    if b['type'] == 'demon':
      return pygame.Rect(int(b['x']), int(b['y']), 150, 150)
    return pygame.Rect(int(b['x']), int(b['y']), 100, 100)

  def update_fwaves(self, b):
    d = self.dragon
    for w in b['fwaves']:
      w['x'] -= 10.5 * self.ts
      w['fr'] += 0.3
      w['y'] += w.get('vy', 0.0) * self.ts
      if self.tick and random.random() < 0.5:
        self.emit(w['x'] + 14, w['y'] + random.randint(-45, 45), random.uniform(1, 3), random.uniform(-1, 1), random.randint(4, 8), random.choice(((255, 140, 30), (255, 210, 90), (220, 60, 20))))
      if d.colliderect(pygame.Rect(int(w['x'] - 10), int(w['y'] - 55), 30, 110)):
        w['x'] = -999.0
        if not self.shield_active:
          self.dead = True
        else:
          self.burst(d.centerx, d.centery, 14, 5, 4, 9, (255, 150, 40))
          AUDIO.play('shatter', 0.5)
    b['fwaves'] = [w for w in b['fwaves'] if w['x'] > -60]

  def phoenix_fire(self, x, y, ang, spd, ember=False):
    self.fireballs.append({'x': float(x), 'y': float(y), 'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd, 'state': 'normal', 'straight': True, 'ember': ember})

  def phoenix_ai(self, b):  # (attack timings match the new strike / flare animations)
    """Phoenix: fireball volley, fire-crescent wing slash, burst of fire feathers, and a burning dive.
    The first time it dies it falls to ash and is reborn with half its health."""
    d = self.dragon
    b['at'] += 1
    at = b['at']
    atk = b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    self.update_fwaves(b)
    cx, cy = b['x'] + 55, b['y'] + 55
    fast = b['lives'] == 0
    if atk not in ('dive', 'warn', 'return'):
      b['y'] = b['by'] + math.sin(b['timer'] * 1.2) * 60
    if atk == 'idle':
      b['cool'] -= 1
      if b['cool'] <= 0:
        b['atk'] = ('cast', 'slash', 'burst', 'warn')[b['seq'] % 4]
        b['seq'] += 1
        b['at'] = 0
        if b['atk'] == 'warn':
          b['ty'] = float(max(60, min(GROUND_Y - 120, d.centery - 55)))
          AUDIO.play('roar', 0.5)
    elif atk == 'cast':                         # 10 frames x 6 ticks: fireballs on frames 4 and 7
      if at in (30, 41):                        # out of the beak as the wings sweep forward
        bx, by = cx + PHX_BEAK[0], cy + PHX_BEAK[1]
        a0 = math.atan2(d.centery - by, d.centerx - bx)
        for k in ((-0.22, 0, 0.22) if not fast else (-0.32, -0.11, 0.11, 0.32)):
          self.phoenix_fire(bx, by, a0 + k, 7.5)
        AUDIO.play('whoosh', 0.6)
      if at >= 60:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 40 if fast else 70
    elif atk == 'slash':                        # crescent leaves on frame 4
      if at == 12:                              # the blazing crescent leaves the spreading wings
        sx, sy = float(cx - 70), float(cy + 5)
        ty = max(80, min(GROUND_Y - 70, d.centery))
        trav = max(10.0, (sx - d.centerx) / 10.5)
        b['fwaves'].append({'x': sx, 'y': sy, 'vy': (ty - sy) / trav, 'fr': 0.0})
        self.shake_for(3, 5)
        AUDIO.play('whoosh')
      if at >= 60:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 40 if fast else 70
    elif atk == 'burst':                        # feathers explode outwards as the flames burst
      if at == 18:
        n = 16 if fast else 12
        for k in range(n):
          self.phoenix_fire(cx, cy, k * 2 * math.pi / n + 0.15, 5.0, True)
        self.shake_for(6, 10)
        self.burst(cx, cy, 30, 7, 5, 12, (255, 150, 40))
        AUDIO.play('roar', 0.4)
      if at >= 60:
        b['atk'], b['at'], b['cool'] = 'idle', 0, 40 if fast else 70
    elif atk == 'warn':                         # glows and lines up with the dragon, then dives
      b['y'] += (b['ty'] - b['y']) * 0.12
      if at >= 40:
        b['atk'], b['at'] = 'dive', 0
        AUDIO.play('whoosh', 0.9)
    elif atk == 'dive':
      b['x'] -= 17 * self.ts
      if self.tick:
        self.emit(cx + 40, cy + random.randint(-20, 20), random.uniform(1, 4), random.uniform(-1, 1), random.randint(8, 14), random.choice(((255, 140, 30), (255, 210, 90), (220, 60, 20))))
      if not self.dash_inv and d.colliderect(pygame.Rect(int(b['x']) + 10, int(b['y']) + 20, 90, 70)):
        if not self.shield_active:
          self.dead = True
        else:
          self.burst(d.centerx, d.centery, 16, 6, 4, 10, (255, 150, 40))
          AUDIO.play('shatter', 0.6)
          self.shield_active = False
      if b['x'] < -180:
        b['x'] = WIDTH + 60.0
        b['y'] = b['by']
        b['atk'], b['at'] = 'return', 0
    elif atk == 'return':
      b['x'] -= 6
      if b['x'] <= BOSS_X:
        b['x'] = float(BOSS_X)
        b['atk'], b['at'], b['cool'] = 'idle', 0, 50 if fast else 80

  def phoenix_down(self, b):
    """Death / rebirth sequence. state 'ash': explodes into embers in mid-air, then is reborn from the smoke."""
    b['dt'] += 1
    t = b['dt']
    if t <= 60:                                 # bursts apart in mid-air (no fall: it is reborn right where it died)
      if t % 3 == 0:
        self.emit(b['x'] + random.randint(20, 90), b['y'] + random.randint(20, 100), random.uniform(-2, 2), random.uniform(-3, -1), random.randint(6, 12), random.choice(((255, 140, 30), (255, 210, 90), (200, 60, 20))))
    if b['state'] == 'dying':                   # final death: the embers fade away
      if t > 120:
        b['alpha'] = max(0, 255 - (t - 120) * 6)
      if t > 165:
        self.boss = None
      return
    if t == 130:
      AUDIO.play('roar', 0.8)
      self.toast("The Phoenix rises from the ashes!")
    if 130 <= t < 230 and t % 2 == 0:
      self.emit(b['x'] + 55 + random.randint(-40, 40), b['y'] + 55 + random.randint(-50, 50), random.uniform(-1, 1), random.uniform(-5, -2), random.randint(8, 16), random.choice(((255, 120, 20), (255, 200, 60), (255, 240, 160))))
    if t >= 230:
      b['y'] += (b['by'] - b['y']) * 0.08
    if t >= 260:
      b['state'] = 'fighting'
      b['lives'] = 0
      b['hp'] = b['max_hp'] * 0.55
      b['atk'], b['at'], b['cool'] = 'idle', 0, 30
      b['ghost'] = False

  def demon_ai(self, b):
    d = self.dragon
    b['at'] += 1
    at = b['at']
    atk = b['atk']
    if b.get('flash', 0) > 0:
      b['flash'] -= 1
    if b.get('sh', 0) > 0:
      b['sh'] -= 1
    self.update_fwaves(b)
    if atk != 'phase':
      b['y'] = b['by'] + math.sin(b['timer'] * 1.3) * 28
    if atk == 'idle':
      b['cool'] -= 1
      if b['hurt'] > 30 and b['cool'] < 50:
        b['cool'] = 0
        b['seq'] = 1 if b['seq'] % 2 else 3
      if b['cool'] <= 0:
        b['hurt'] = 0
        nxt = ('slash', 'phase', 'slash', 'guard')[b['seq'] % 4]
        b['seq'] += 1
        if nxt == 'guard':
          b['sh'] = 145
          b['cool'] = 150
          AUDIO.play('shield')
          self.burst(b['x'] + 75, b['y'] + 75, 24, 6, 4, 10, (255, 110, 80))
        else:
          b['atk'] = nxt
          b['at'] = 0
        if nxt == 'phase':
          AUDIO.play('whoosh', 0.7)
    elif atk == 'slash':
      if at in (18, 38, 58):
        k = (58, 38, 18).index(at)
        off = (0, -95, 95)[k] if k else 0
        ty = d.centery + off
        ty = max(80, min(GROUND_Y - 70, ty))
        self.shake_for(3, 5)
        AUDIO.play('whoosh')
        sx, sy = float(b['x'] + 5), float(b['y'] + 112)
        trav = max(10.0, (sx - d.centerx) / 10.5)
        b['fwaves'].append({'x': sx, 'y': sy, 'vy': (ty - sy) / trav, 'fr': 0.0})
        self.burst(sx, sy, 12, 5, 4, 9, (255, 150, 40))
      if at >= 66:
        b['atk'] = 'idle'
        b['cool'] = 55
        b['at'] = 0
    elif atk == 'phase':
      if at < 24:
        b['alpha'] = int(255 * (1 - at / 24.0))
        if at >= 6:
          b['ghost'] = True
      elif at == 24:
        b['alpha'] = 0
        ny = b['by']
        for _ in range(8):
          ny = random.uniform(100, GROUND_Y - 150)
          if abs(ny - b['y']) > 110:
            break
        b['by'] = ny
        b['y'] = ny
        b['x'] = BOSS_X + random.uniform(-70, 70)
        self.burst(b['x'] + 50, b['y'] + 60, 26, 5, 4, 10, (255, 150, 40))
      elif at < 50:
        b['alpha'] = int(255 * ((at - 24) / 26.0))
        if at % 3 == 0:
          self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 110), random.uniform(-2, 2), random.uniform(-3, -1), random.randint(5, 9), random.choice(((255, 140, 30), (255, 210, 90))))
        if at >= 44:
          b['ghost'] = False
      else:
        b['alpha'] = 255
        b['ghost'] = False
        b['atk'] = 'idle'
        b['cool'] = 60
        b['at'] = 0
      if at < 24 and at % 3 == 0:
        self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 110), random.uniform(-2, 2), random.uniform(-3, -1), random.randint(5, 9), random.choice(((255, 140, 30), (255, 210, 90))))

  def update_boss(self):
    b = self.boss
    d = self.dragon
    if not b:
      if d.x < 150:
        d.x = min(150, d.x + 2)
      return
    b['timer'] += 0.05
    if b['state'] == 'entering':
      b['x'] -= 6 if b['x'] > BOSS_X + 120 else 2
      if b['x'] <= BOSS_X:
        b['state'] = 'fighting'
    elif b['state'] == 'ash' or (b['state'] == 'dying' and b['type'] == 'phoenix'):
      self.phoenix_down(b)
      return
    elif b['state'] == 'fighting':
      if b['type'] in ('demon', 'phoenix', 'jabber', 'hydra', 'beholder'):
        pass
      elif b.get('atk') not in ('dive', 'dive_warn_lock', 'thunder'):
        if b['type'] != 'griffin' or b.get('atk') != 'dive':
          b['y'] = HEIGHT // 2 - 50 + math.sin(b['timer']) * (100 if b['type'] == 'griffin' else 150)
      if b['hp'] <= 0 and b['type'] == 'phoenix':
        b['fwaves'] = []
        b['dt'] = 0
        b['atk'] = 'idle'
        if b['lives'] > 0:
          b['state'] = 'ash'
          b['hp'] = 0
          self.shake_for(10, 20)
        else:
          b['state'] = 'dying'
          self.shake_for(15, 30)
          self.score += 300
          self.b2 = True
          self.drop_egg('phoenix', b['x'] + 55, b['y'] + 55)
          self.run_bosses = getattr(self, 'run_bosses', 0) + 1
          self.note_boss(b['type'])
      elif b['hp'] <= 0:
        b['state'] = 'dying'
        b['tilt'] = 0
        b['fi'] = None
        b['atk'] = 'idle'
        b['waves'] = []
        b['fwaves'] = []
        b['ghost'] = False
        b['alpha'] = 255
        self.shake_for(15, 30)
        self.score += 300
        if b['type'] == 'griffin':
          self.b1 = True
        elif b['type'] == 'jabber':
          self.b3 = True
          b['beam'] = None
        elif b['type'] == 'hydra':
          self.b5 = True
        elif b['type'] == 'beholder':
          self.b6 = True
          b['ray'] = False
          b['anim'] = 'death'
        else:
          self.b4 = True
        self.drop_egg(b['type'], b['x'] + 50, b['y'] + 50)
        self.run_bosses = getattr(self, 'run_bosses', 0) + 1
        self.note_boss(b['type'])
        b['vy'] = 0.0
        b['landed'] = -1
      elif b['type'] == 'griffin':
        self.griffin_ai(b)
      elif b['type'] == 'demon':
        self.demon_ai(b)
      elif b['type'] == 'jabber':
        self.jabber_ai(b)
      elif b['type'] == 'hydra':
        self.hydra_ai(b)
      elif b['type'] == 'beholder':
        self.beholder_ai(b)
      elif b['type'] == 'phoenix':
        self.phoenix_ai(b)
      elif b['type'] == 'zeppelin' and random.random() < 0.04:
        self.fireballs.append({'x': float(b['x']), 'y': float(b['y'] + 50), 'vx': -8, 'vy': 0, 'state': 'normal'})
        self.fireballs.append({'x': float(b['x'] + 50), 'y': float(b['y'] + 80), 'vx': -2, 'vy': 5, 'state': 'normal'})
    elif b['type'] == 'demon':  # dying: drops quickly to the ground, then plays the death animation there
      b['dt'] += 1
      floor = GROUND_Y - 148.0
      if b.get('landed', -1) < 0:
        b['vy'] = b.get('vy', 0.0) + 1.1
        b['y'] = min(floor, b['y'] + b['vy'])
        if b['y'] >= floor:
          b['landed'] = b['dt']
          self.shake_for(10, 14)
          self.burst(b['x'] + 75, GROUND_Y - 6, 26, 6, 6, 14, (150, 140, 130))
          AUDIO.play('shatter', 0.7)
      if b['dt'] % 3 == 0:
        self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(20, 100), random.uniform(-3, 3), random.uniform(-4, -1), random.randint(8, 16), random.choice(((255, 100, 0), (255, 200, 60), (200, 40, 20))))
      if b.get('landed', -1) >= 0 and b['dt'] - b['landed'] > 110:
        self.boss = None
    elif b['type'] == 'beholder':  # dying: shudders and swells in the air, then bursts apart
      b['dt'] += 1
      b['y'] += 0.3
      fi = b['dt'] // 4
      if fi < 13 and b['dt'] % 5 == 0:
        self.emit(b['x'] + random.randint(10, 100), b['y'] + random.randint(20, 110), random.uniform(-2, 2), random.uniform(-2, 0.5), random.randint(3, 6),
                  random.choice(((90, 255, 120), (200, 40, 50), (120, 110, 140))))
      if b['dt'] == 56:                                   # bursts apart
        self.shake_for(16, 20)
        self.burst(b['x'] + 55, b['y'] + 65, 40, 8, 4, 12, (110, 100, 130))
        self.burst(b['x'] + 55, b['y'] + 65, 24, 7, 3, 9, (90, 255, 120))
        AUDIO.play('shatter', 0.9)
      if fi >= beh_count('death') - 1:
        b['alpha'] = max(0, b.get('alpha', 255) - 12)
      if b['dt'] > 4 * beh_count('death') + 24:
        self.boss = None
    elif b['type'] == 'hydra':  # dying: drops to the ground and collapses into a heap of bones
      b['dt'] += 1
      floor = GROUND_Y - 65.0 - HYD_BOTTOM[0] * HYD_SCALE
      if b.get('landed', -1) < 0:
        b['vy'] = b.get('vy', 0.0) + 0.9
        b['y'] = min(floor, b['y'] + b['vy'])
        if b['y'] >= floor:
          b['landed'] = b['dt']
          self.shake_for(14, 18)
          self.burst(b['x'] + 75, GROUND_Y - 6, 34, 6, 6, 14, (200, 190, 170))
          AUDIO.play('shatter', 0.9)
      else:
        k = b['dt'] - b['landed']
        b['y'] = GROUND_Y - 65.0 - HYD_BOTTOM[min(len(HYD_BOTTOM) - 1, k // 5)] * HYD_SCALE
        if k > 110:
          b['alpha'] = max(0, 255 - (k - 110) * 8)
        if k > 142:
          self.boss = None
    elif b['type'] == 'jabber':  # dying: drops to the ground, its knees buckle and it collapses, then fades
      b['dt'] += 1
      floor = GROUND_Y - 65.0 - JAB_BOTTOM[0] * JAB_SCALE
      if b.get('landed', -1) < 0:
        b['vy'] = b.get('vy', 0.0) + 0.9
        b['y'] = min(floor, b['y'] + b['vy'])
        if b['y'] >= floor:
          b['landed'] = b['dt']
          self.shake_for(12, 16)
          self.burst(b['x'] + 65, GROUND_Y - 6, 30, 6, 6, 14, (120, 130, 100))
          AUDIO.play('shatter', 0.8)
      else:
        b['y'] = GROUND_Y - 65.0 - JAB_BOTTOM[min(16, (b['dt'] - b['landed']) // 4)] * JAB_SCALE
        k = b['dt'] - b['landed']
        if k > 100:
          b['alpha'] = max(0, 255 - (k - 100) * 8)
        if k > 132:
          self.boss = None
    elif b['type'] == 'griffin':  # dying: folds up in the air and crumbles into golden dust
      b['dt'] = b.get('dt', 0) + 1
      b['tilt'] = 0
      b['y'] += 0.6
      if b['dt'] >= 28 and b['dt'] % 2 == 0:
        for _ in range(3):
          self.emit(b['x'] + random.randint(20, 80), b['y'] + random.randint(25, 80), random.uniform(-1.6, 1.6), random.uniform(-1.8, 0.4), random.randint(4, 8),
                    random.choice(((255, 214, 60), (255, 236, 140), (200, 150, 40))))
      if b['dt'] > 40:
        b['alpha'] = max(0, 255 - (b['dt'] - 40) * 12)
      if b['dt'] > 62:
        self.boss = None
    else:  # dying: falls fast, crashes onto the ground, lies there and fades away
      b['dt'] = b.get('dt', 0) + 1
      floor = GROUND_Y - 109.0
      if b.get('landed', -1) < 0:
        b['vy'] = b.get('vy', 0.0) + 1.0
        b['y'] = min(floor, b['y'] + b['vy'])
        b['tilt'] = min(90, b.get('tilt', 0) + 6)
        self.emit(b['x'] + random.randint(0, 100), b['y'] + random.randint(0, 100), random.uniform(-4, 4), random.uniform(-4, 4), random.randint(10, 25), (255, 100, 0))
        if b['y'] >= floor:
          b['landed'] = b['dt']
          b['tilt'] = 90
          self.shake_for(10, 14)
          self.burst(b['x'] + 50, GROUND_Y - 6, 26, 6, 6, 14, (150, 140, 130))
          AUDIO.play('shatter', 0.7)
      else:
        t = b['dt'] - b['landed']
        if t > 60:
          b['alpha'] = max(0, 255 - (t - 60) * 6)
        if t % 6 == 0:
          self.emit(b['x'] + random.randint(10, 90), GROUND_Y - random.randint(0, 30), random.uniform(-1, 1), random.uniform(-2, -0.5), random.randint(6, 12), (120, 112, 104))
        if t > 105:
          self.boss = None
