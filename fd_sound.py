"""Flappy Dragon sound: every effect, loop and the music are synthesised in code (no audio files).
If the audio system is missing or anything fails, the game just runs silently."""
import math
import random
import array
import time
import threading
import pygame

RATE = 22050


def _env(i, n, attack=0.01, rate=RATE):
  a = max(1, int(attack * rate))
  if i < a:
    return i / a
  return max(0.0, 1.0 - (i - a) / float(max(1, n - a))) ** 1.5


def _wave(kind, ph):
  if kind == 'sine':
    return math.sin(ph)
  if kind == 'sq':
    return 1.0 if math.sin(ph) >= 0 else -1.0
  if kind == 'saw':
    return ((ph / (2 * math.pi)) % 1.0) * 2 - 1
  if kind == 'tri':
    return abs(((ph / (2 * math.pi)) % 1.0) * 4 - 2) - 1
  return random.uniform(-1, 1)


def tone(f0, f1, dur, kind='sine', vol=0.5, attack=0.01, rate=RATE):
  n = int(dur * rate)
  out, ph = [], 0.0
  for i in range(n):
    f = f0 + (f1 - f0) * i / float(n)
    ph += 2 * math.pi * f / rate
    out.append(_wave(kind, ph) * vol * _env(i, n, attack, rate))
  return out


def noise(dur, vol=0.5, smooth=0, rate=RATE):
  n = int(dur * rate)
  out, last = [], 0.0
  for i in range(n):
    v = random.uniform(-1, 1)
    if smooth:
      last += (v - last) / smooth
      v = last * 2.2
    out.append(v * vol * _env(i, n, 0.004, rate))
  return out


def mix(*parts):
  n = max(len(p) for p in parts)
  out = [0.0] * n
  for p in parts:
    for i, v in enumerate(p):
      out[i] += v
  return out


def seq(*parts):
  out = []
  for p in parts:
    out.extend(p)
  return out


def pcm(samples, channels, gain=1.0, repeat=1):
  buf = array.array('h')
  for v in samples:
    v = max(-1.0, min(1.0, v * gain))
    s = int(v * 30000)
    for _ in range(repeat * channels):
      buf.append(s)
  return buf.tobytes()


def build_effects():
  fx = {}
  fx['flap'] = mix(noise(0.07, 0.25, 4), tone(220, 420, 0.08, 'sine', 0.3))
  fx['coin'] = seq(tone(988, 988, 0.06, 'sq', 0.22), tone(1319, 1319, 0.14, 'sq', 0.22))
  fx['click'] = tone(700, 500, 0.05, 'sq', 0.2)
  fx['power'] = mix(tone(160, 900, 0.4, 'saw', 0.25, 0.02), noise(0.4, 0.15, 3))
  fx['shatter'] = mix(noise(0.3, 0.55, 2), tone(180, 60, 0.25, 'sine', 0.4))
  fx['die'] = mix(tone(420, 50, 0.7, 'sq', 0.25, 0.01), noise(0.5, 0.3, 5))
  fx['launch'] = mix(tone(130, 45, 0.28, 'sine', 0.5), noise(0.18, 0.3, 6))
  fx['thunder'] = mix(noise(1.0, 0.7, 14), tone(60, 35, 1.0, 'sine', 0.3, 0.05))
  fx['quest'] = seq(tone(523, 523, 0.1, 'sq', 0.2), tone(659, 659, 0.1, 'sq', 0.2), tone(784, 784, 0.1, 'sq', 0.2), tone(1047, 1047, 0.3, 'sq', 0.22))
  fx['shield'] = mix(tone(500, 1100, 0.3, 'sine', 0.3, 0.02), tone(250, 550, 0.3, 'tri', 0.2, 0.02))
  fx['roar'] = mix(tone(95, 55, 0.8, 'saw', 0.35, 0.05), noise(0.7, 0.25, 8))
  fx['whoosh'] = noise(0.45, 0.35, 10)
  fx['chime'] = mix(seq(tone(1568, 1568, 0.07, 'sine', 0.18), tone(2093, 2093, 0.07, 'sine', 0.18), tone(2637, 2637, 0.16, 'sine', 0.16)), tone(1047, 1400, 0.3, 'tri', 0.08, 0.02))
  fx['laser'] = mix(tone(240, 900, 0.5, 'saw', 0.22, 0.02), tone(120, 450, 0.5, 'sq', 0.12, 0.02), noise(0.5, 0.15, 3))
  return fx


# ---------------------------------------------------------------- seamless loops (built in the background)
def _lp(xs, k):
  out, y = [], 0.0
  for x in xs:
    y += (x - y) / k
    out.append(y)
  return out


def _loop(xs, xf=2200):
  """Cross-fade the end into the start so the loop has no click."""
  n = len(xs)
  out = xs[:n - xf]
  for i in range(xf):
    t = i / float(xf)
    out[i] = xs[i] * t + xs[n - xf + i] * (1 - t)
  return out


def _white(n):
  return [random.uniform(-1, 1) for _ in range(n)]


def _clicks(n, count, length, vol, freq=0):
  out = [0.0] * n
  for _ in range(count):
    p = random.randint(0, n - length - 1)
    a = random.uniform(0.3, 1.0) * vol
    for i in range(length):
      d = math.exp(-i * 5.0 / length)
      out[p + i] += (math.sin(i * freq) if freq else random.uniform(-1, 1)) * a * d
  return out


def loop_fire():
  """Soft roar underneath, with lots of sharp, uneven crackles and a few louder pops."""
  n = int(3.0 * RATE)
  w = _white(n)
  low = _lp(w, 10)
  mid = _lp(w, 4)
  out = []
  wob = random.uniform(0, 6)
  for i in range(n):
    t = i / float(RATE)
    am = 0.7 + 0.3 * math.sin(2 * math.pi * 2.3 * t + wob) * math.sin(2 * math.pi * 3.7 * t)
    out.append((low[i] * 1.1 + mid[i] * 0.25) * am)

  def burst(pos, length, amp):
    prev = 0.0
    for i in range(length):
      if pos + i >= n:
        break
      x = random.uniform(-1, 1)
      out[pos + i] += (x - prev) * 0.5 * amp * math.exp(-i * 6.0 / length)
      prev = x

  for _ in range(95):
    r = random.random()
    p = random.randint(0, n - 900)
    if r < 0.62:
      burst(p, random.randint(40, 140), random.uniform(0.15, 0.4))
    elif r < 0.9:
      burst(p, random.randint(140, 380), random.uniform(0.4, 0.75))
    else:
      for k in range(random.randint(3, 5)):
        burst(p + k * random.randint(120, 420), random.randint(40, 110), random.uniform(0.25, 0.55))
  for _ in range(9):
    p = random.randint(0, n - 1200)
    burst(p, 110, 1.0)
    for i in range(500):
      out[p + i] += math.sin(i * 0.04) * math.exp(-i / 90.0) * 0.45
  return _loop(out)


def loop_wind():
  n = int(2.0 * RATE)
  low = _lp(_white(n), 7)
  return _loop([low[i] * 1.6 * (0.55 + 0.45 * math.sin(2 * math.pi * 0.7 * i / RATE)) for i in range(n)])


def loop_zap():
  n = int(1.2 * RATE)
  w = _white(n)
  out, gate = [], 0.0
  for i in range(n):
    if i % 90 == 0:
      gate = 1.0 if random.random() < 0.5 else 0.15
    out.append(w[i] * 0.45 * gate + (0.08 if math.sin(2 * math.pi * 100 * i / RATE) > 0 else -0.08))
  return _loop(out)


def loop_hiss():
  n = int(1.4 * RATE)
  w = _white(n)
  lp = _lp(w, 6)
  bub = _clicks(n, 40, 90, 0.25, 0.09)
  return _loop([(w[i] - lp[i]) * 0.5 + bub[i] for i in range(n)])


def loop_acid():
  """Wet pressurised spray: bright hiss in spurts, dense sizzle, and bubbling blorps."""
  n = int(1.6 * RATE)
  w = _white(n)
  lp = _lp(w, 3)
  hi = [w[i] - lp[i] for i in range(n)]
  siz = _clicks(n, 420, 36, 0.16)
  out = []
  for i in range(n):
    t = i / float(RATE)
    spurt = 0.62 + 0.38 * abs(math.sin(2 * math.pi * 3.1 * t + 0.6)) * (0.7 + 0.3 * math.sin(2 * math.pi * 7.3 * t))
    out.append(hi[i] * 0.55 * spurt + siz[i])
  for _ in range(30):
    p = random.randint(0, n - 2600)
    f0 = random.uniform(160, 520)
    ln = random.randint(900, 2400)
    ph = 0.0
    amp = random.uniform(0.12, 0.32)
    for i in range(ln):
      ph += 2 * math.pi * (f0 + f0 * 1.8 * i / float(ln)) / RATE
      out[p + i] += math.sin(ph) * amp * math.exp(-i * 4.0 / ln) * min(1.0, i / 60.0)
  return _loop(out, 1800)


def loop_rain():
  n = int(2.5 * RATE)
  w = _white(n)
  lp = _lp(w, 10)
  drops = _clicks(n, 110, 70, 0.12, 0.22)
  return _loop([(w[i] - lp[i]) * 0.34 + lp[i] * 0.25 + drops[i] for i in range(n)])


def loop_gale():
  n = int(2.6 * RATE)
  low = _lp(_white(n), 9)
  out = []
  for i in range(n):
    t = i / float(RATE)
    am = 0.5 + 0.3 * math.sin(2 * math.pi * 0.35 * t) + 0.2 * math.sin(2 * math.pi * 0.83 * t + 2)
    out.append(low[i] * 2.0 * am + math.sin(2 * math.pi * (620 + 80 * math.sin(2 * math.pi * 0.5 * t)) * t) * 0.025 * am)
  return _loop(out)


LOOPS = {'fire': loop_fire, 'wind': loop_wind, 'zap': loop_zap, 'hiss': loop_hiss, 'acid': loop_acid, 'rain': loop_rain, 'gale': loop_gale}
LOOP_GAIN = {'fire': 0.7, 'wind': 0.5, 'zap': 1.3, 'hiss': 0.8, 'acid': 0.85, 'rain': 0.3, 'gale': 0.3}
BREATH_LOOP = {'RED': 'fire', 'CHINESE': 'hiss', 'BLUE': 'wind', 'CLOCKWORK': 'wind', 'FOREST': 'wind', 'COCKATRICE': 'wind', 'SILVER': 'wind', 'CHRONO': 'wind', 'YELLOW': 'zap', 'GREEN': 'acid', 'SKELETAL': 'hiss', 'WRAITH': 'hiss', 'WHALE': 'wind', 'FEY': 'zap', 'ALIEN': 'acid', 'EAGLE': 'wind'}
WEATHER_LOOP = {'rain': 'rain', 'storm': 'rain', 'wind': 'gale'}


# ---------------------------------------------------------------- music: lofi medieval "Tavern Tape"
MUSIC_RATE = 11025
BPM = 78
SPB = 60.0 / BPM
SWING = 0.35
_SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nf(name):
  m = _SEMI[name[0]] + (12 * (int(name[-1]) + 1))
  if len(name) == 3:
    m += 1 if name[1] == '#' else -1
  return 440.0 * 2 ** ((m - 69) / 12.0)


_DM = ('D2', ['D3', 'F3', 'A3', 'C4'])
_G = ('G2', ['G3', 'B3', 'D4', 'F4'])
_C = ('C2', ['C3', 'E3', 'G3', 'B3'])
_AM = ('A2', ['A2', 'C3', 'E3', 'G3'])
CHORDS = [_DM, _G, _DM, _C, _DM, _G, _C, _AM]
MELODY = ['A4:1 D5:1 F5:1.5 E5:0.5', 'D5:1 B4:1 G4:2', 'A4:1 D5:1 F5:1.5 G5:0.5', 'E5:2 C5:1 R:1',
          'A4:1 D5:1 F5:1.5 E5:0.5', 'D5:1.5 B4:0.5 G4:1 B4:1', 'C5:1 E5:1 G5:1 E5:1', 'D5:3 R:1']
ARP = (0, 1, 2, 3, 2, 1, 2, 1)


def _lute(f, dur, rate):
  """Plucked lute: a few decaying harmonics, brighter at the attack."""
  n = int(dur * rate)
  parts = []
  for h in range(1, 7):
    fr = f * h * (1 + 0.0003 * h * h)
    if fr < rate * 0.45:
      parts.append((2 * math.pi * fr / rate, 1.0 / h ** 1.2, (2.2 + 1.6 * h) / rate))
  out = []
  for i in range(n):
    v = 0.0
    for w, amp, dec in parts:
      v += amp * math.sin(w * i) * math.exp(-dec * i)
    out.append(v * min(1.0, i / (0.003 * rate)))
  return out


def _flute(f, dur, rate):
  """Breathy wooden flute with a slow vibrato."""
  n = int(dur * rate)
  out = []
  ph = 0.0
  for i in range(n):
    t = i / rate
    vib = math.sin(2 * math.pi * 5.2 * t) * min(1.0, t / 0.35) * 0.004
    ph += 2 * math.pi * f * (1 + vib) / rate
    v = math.sin(ph) + 0.18 * math.sin(2 * ph) + 0.05 * math.sin(3 * ph) + random.uniform(-0.05, 0.05)
    env = min(1.0, t / 0.05) * min(1.0, max(0.0, (dur - t) / 0.08))
    out.append(v * env)
  return out


def _bass(f, dur, rate):
  n = int(dur * rate)
  w = 2 * math.pi * f / rate
  return [(math.sin(w * i) + 0.3 * math.sin(2 * w * i)) * math.exp(-2.5 * i / rate) * min(1.0, i / (0.005 * rate)) * min(1.0, max(0.0, (n - i) / (0.03 * rate))) for i in range(n)]


def _kick(rate):
  n = int(0.28 * rate)
  out, ph = [], 0.0
  for i in range(n):
    t = i / rate
    ph += 2 * math.pi * (45 + 90 * math.exp(-28 * t)) / rate
    out.append(math.sin(ph) * math.exp(-9 * t))
  return out


def _snare(rate):
  n = int(0.22 * rate)
  y = 0.0
  out = []
  for i in range(n):
    t = i / rate
    y += (random.uniform(-1, 1) - y) * 0.7
    out.append(y * math.exp(-22 * t) * 0.8 + math.sin(2 * math.pi * 185 * t) * math.exp(-25 * t) * 0.4)
  return out


def _hat(rate):
  n = int(0.05 * rate)
  prev = 0.0
  out = []
  for i in range(n):
    x = random.uniform(-1, 1)
    out.append((x - prev) * math.exp(-70 * i / rate) * 0.5)
    prev = x
  return out


def build_music():
  rate = MUSIC_RATE
  bar_n = int(4 * SPB * rate)
  body = bar_n * len(CHORDS)
  tail = int(3.0 * rate)
  out = [0.0] * (body + tail)
  cache = {}

  def get(kind, f, dur):
    key = (kind, round(f, 2), round(dur, 3))
    if key not in cache:
      cache[key] = {'l': _lute, 'f': _flute, 'b': _bass}[kind](f, dur, rate)
    return cache[key]

  def add(wave, t0, gain):
    end = min(len(out), t0 + len(wave))
    if end <= t0:
      return
    seg = wave[:end - t0]
    out[t0:end] = [a + b * gain for a, b in zip(out[t0:end], seg)]

  kick, snare, hat = _kick(rate), _snare(rate), _hat(rate)
  for bi, (root, tones) in enumerate(CHORDS):
    b0 = bi * bar_n
    time.sleep(0.002)
    for e, idx in enumerate(ARP):
      add(get('l', nf(tones[idx]), 1.6), b0 + int((e * 0.5 + (SWING * 0.25 if e % 2 else 0)) * SPB * rate), 0.20)
    for st, ln in ((0, 1.5), (2.5, 1.0)):
      add(get('b', nf(root), ln * SPB), b0 + int(st * SPB * rate), 0.45)
    pos = 0.0
    for tok in MELODY[bi].split():
      nm, ln = tok.split(':')
      ln = float(ln)
      if nm != 'R':
        add(get('f', nf(nm), ln * SPB * 0.95 + 0.05), b0 + int(pos * SPB * rate), 0.22)
      pos += ln
    for st in (0, 2.5):
      add(kick, b0 + int(st * SPB * rate), 0.6)
    for st in (1, 3):
      add(snare, b0 + int(st * SPB * rate), 0.35)
    for k in range(8):
      sh = SWING * 0.25 * SPB if k % 2 else 0
      add(hat, b0 + int((k * 0.5 * SPB + sh) * rate), 0.14)
  d = int(0.75 * SPB * rate)
  dry = out[:]
  for k, g in ((1, 0.30), (2, 0.16), (3, 0.08)):
    out[d * k:] = [a + b * g for a, b in zip(out[d * k:], dry[:len(out) - d * k])]
  y = 0.0
  for i in range(len(out)):
    y += (out[i] - y) * 0.45
    out[i] = y
  res = out[:body]
  res[:tail] = [a + b for a, b in zip(res[:tail], out[body:body + tail])]
  peak = max(abs(v) for v in res) or 1.0
  return [math.tanh(v / peak * 1.1) * 0.6 for v in res]


class Audio:
  def __init__(self):
    self.ok = False
    self.enabled = True
    self.music_on = True
    self.sfx_on = True
    self.fx = {}
    self.music = None
    self.music_chan = None
    self.music_bytes = None
    self.muffled = None
    self.muffled_bytes = None
    self.muf_chan = None
    self.muf = 0.0
    self.muf_want = 0.0
    self.loop_bytes = {}
    self.loops = {}
    self.chans = {}
    self.want = {'breath': None, 'weather': None}
    self.playing = {'breath': None, 'weather': None}
    self.thread = None
    self.volume = 0.6
    self.music_level = 1.0                  # 0..1 from the options slider
    self.sfx_level = 1.0
    self.theme = None                       # pre-rendered theme (Sound objects) when available
    self.last = {}
    try:
      info = pygame.mixer.get_init()
      if not info or info[0] != RATE or info[1] != -16:
        if info:
          pygame.mixer.quit()
        pygame.mixer.init(RATE, -16, 1, 512)
      info = pygame.mixer.get_init()
      if not info or info[1] != -16:
        return
      self.rate, _fmt, self.channels = info
      if self.rate != RATE:
        return
      pygame.mixer.set_num_channels(15)
      pygame.mixer.set_reserved(4)
      self.music_chan = pygame.mixer.Channel(0)
      self.muf_chan = pygame.mixer.Channel(3)
      self.chans = {'breath': pygame.mixer.Channel(1), 'weather': pygame.mixer.Channel(2)}
      for k, samples in build_effects().items():
        self.fx[k] = pygame.mixer.Sound(buffer=pcm(samples, self.channels))
      self.ok = True
    except Exception:
      self.ok = False

  def music_vol(self):
    return 0.40 * self.music_level if (self.enabled and self.music_on) else 0.0

  def set_levels(self, music=None, sfx=None):
    """volume sliders, 0..1"""
    if music is not None:
      self.music_level = max(0.0, min(1.0, float(music)))
    if sfx is not None:
      self.sfx_level = max(0.0, min(1.0, float(sfx)))
      for slot, chan in self.chans.items():
        try:
          chan.set_volume(self.sfx_level)
        except Exception:
          pass
    self.refresh()

  def refresh(self):
    if not self.ok:
      return
    try:
      self._music_mix()
      for slot in self.chans:
        self._apply(slot)
    except Exception:
      pass

  def _music_mix(self):
    v = self.music_vol()
    if self.music_chan:
      self.music_chan.set_volume(v * (1.0 - self.muf) if self.muffled else v)
    if self.muf_chan and self.muffled:
      self.muf_chan.set_volume(v * self.muf * 1.15)

  def set_muffled(self, on):
    """Paused: crossfade to a low-passed copy of the music that plays in sync on its own channel."""
    self.muf_want = 1.0 if on else 0.0

  def set_enabled(self, on):
    self.enabled = bool(on)
    self.refresh()

  def set_music(self, on):
    self.music_on = bool(on)
    self.refresh()

  def set_sfx(self, on):
    self.sfx_on = bool(on)
    self.refresh()

  def play(self, name, vol=1.0):
    if not (self.ok and self.enabled and self.sfx_on):
      return
    try:
      now = pygame.time.get_ticks()
      if now - self.last.get(name, -999) < 70:
        return
      self.last[name] = now
      snd = self.fx.get(name)
      if snd:
        snd.set_volume(min(1.0, self.volume * vol * self.sfx_level))
        snd.play()
    except Exception:
      pass

  def start_music(self):
    """Build the music and the looping ambience in a background thread; tick() picks them up when ready."""
    if not self.ok or self.thread is not None:
      return

    try:                                      # the pre-rendered theme (OGG), decoded here on the main thread
      import io
      from fd_music import theme_bytes
      main = pygame.mixer.Sound(file=io.BytesIO(theme_bytes()))
      try:
        muf = pygame.mixer.Sound(file=io.BytesIO(theme_bytes(True)))
      except Exception:
        muf = None
      if main.get_length() > 5:
        self.theme = (main, muf)
    except Exception:
      self.theme = None

    def work():
      if self.theme:
        self.music_bytes = b'theme'
      else:
        self.synth_music()
      for name, fn in LOOPS.items():
        try:
          time.sleep(0.01)
          self.loop_bytes[name] = pcm(fn(), self.channels, LOOP_GAIN[name])
        except Exception:
          self.loop_bytes[name] = b''
    self.thread = threading.Thread(target=work)
    self.thread.daemon = True
    self.thread.start()

  def synth_music(self):
    """fallback: the old in-code tavern tune"""
    if True:
      try:
        mus = build_music()
        try:
          a = b = 0.0
          low = []
          for v in mus:                       # two-pole low-pass = "through a wall" muffle
            a += (v - a) * 0.12
            b += (a - b) * 0.12
            low.append(b)
          self.muffled_bytes = pcm(low, self.channels, 1.4, repeat=2)
        except Exception:
          self.muffled_bytes = b''
        self.music_bytes = pcm(mus, self.channels, 1.0, repeat=2)
      except Exception:
        self.music_bytes = b''

  def set_loop(self, slot, name):
    """slot is 'breath' or 'weather'; name is a key of LOOPS or None to stop."""
    if not self.ok or self.want.get(slot) == name:
      return
    self.want[slot] = name
    self._apply(slot)

  def _apply(self, slot):
    try:
      name = self.want[slot]
      chan = self.chans.get(slot)
      if chan is None:
        return
      if not (self.enabled and self.sfx_on):
        name = None
      if name == self.playing[slot]:
        return
      if name is None:
        chan.stop()
        self.playing[slot] = None
        return
      snd = self.loops.get(name)
      if snd:
        chan.set_volume(self.sfx_level)
        chan.play(snd, loops=-1)
        self.playing[slot] = name
    except Exception:
      pass

  def tick(self):
    if not self.ok:
      return
    try:
      if self.music is None and self.music_bytes is not None:
        if self.theme and self.music_bytes == b'theme':
          self.music, self.muffled = self.theme
          if not self.muf_chan:
            self.muffled = None
          self._music_mix()
          self.music_chan.play(self.music, loops=-1)
          if self.muffled:
            self.muf_chan.play(self.muffled, loops=-1)
        elif self.music_bytes:
          self.music = pygame.mixer.Sound(buffer=self.music_bytes)
          if self.muffled_bytes and self.muf_chan:
            try:
              self.muffled = pygame.mixer.Sound(buffer=self.muffled_bytes)
            except Exception:
              self.muffled = None
          self._music_mix()
          self.music_chan.play(self.music, loops=-1)
          if self.muffled:
            self.muf_chan.play(self.muffled, loops=-1)
        else:
          self.music = False
      if self.muffled and abs(self.muf - self.muf_want) > 0.001:
        self.muf += max(-0.06, min(0.06, self.muf_want - self.muf))
        self._music_mix()
      for name, raw in list(self.loop_bytes.items()):
        if name not in self.loops:
          self.loops[name] = pygame.mixer.Sound(buffer=raw) if raw else False
          for slot in self.want:
            if self.want[slot] == name:
              self._apply(slot)
    except Exception:
      self.music = False


AUDIO = Audio()
