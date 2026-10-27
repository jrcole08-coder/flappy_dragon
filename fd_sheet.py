"""Shared loader for the full-animation dragons drawn from your sprite sets (Magma, Ice, Evil Unicorn).
Each data module (fd_magma / fd_ice / fd_unicorn) holds packed 168x128 frames plus the order to play them in."""
import base64, zlib, math, importlib
import pygame

MODS = {'RED': 'fd_magma', 'BLUE': 'fd_ice', 'UNICORN': 'fd_unicorn', 'WRAITH': 'fd_wraith', 'CHINESE': 'fd_lung', 'CLOCKWORK': 'fd_clockwork', 'GREEN': 'fd_poison', 'YELLOW': 'fd_lightning', 'FOREST': 'fd_forest_dragon', 'SILVER': 'fd_wind', 'COCKATRICE': 'fd_cockatrice', 'WHALE': 'fd_whale', 'FEY': 'fd_fey', 'ALIEN': 'fd_alien', 'EAGLE': 'fd_eagle'}
W, H = 168, 128


class Sheet:
  def __init__(self, mod):
    self.m = mod
    self._raw, self._f, self._r = {}, {}, {}

  def _frame(self, name, j):
    k = (name, j)
    s = self._f.get(k)
    if s is None:
      n, data = self.m.FRAMES[name]
      raw = self._raw.get(name)
      if raw is None:
        raw = self._raw[name] = zlib.decompress(base64.b64decode(data))
      m = W * H * 4
      s = self._f[k] = pygame.image.frombuffer(raw[j * m:(j + 1) * m], (W, H), 'RGBA').copy()
      if sum(1 for q in self._f if q[0] == name) >= n:
        self._raw.pop(name, None)                  # every frame unpacked: free the raw pixels
    return s

  def count(self, name):
    return len(self.m.SEQ[name])

  def frame(self, name, i, tb=0):
    """step i of the 'fly' / 'breath' / 'death' loop, tilted by tb steps (6 degrees each, nose down for +)."""
    seq = self.m.SEQ[name]
    j = seq[i % len(seq)]
    if not tb:
      return self._frame(name, j)
    k = (name, j, tb)
    s = self._r.get(k)
    if s is None:
      r = pygame.transform.rotate(self._frame(name, j), -tb * 6)
      s = pygame.Surface((W, H), pygame.SRCALPHA)
      s.blit(r, (W // 2 - r.get_width() // 2, H // 2 - r.get_height() // 2))
      self._r[k] = s
    return s

  def fly_index(self, wing):
    """one frame every 2 game frames while flapping (wing grows 0.38 a frame), slower while gliding"""
    return int(wing / 0.76) % self.count('fly')

  def breath_index(self):
    return int(pygame.time.get_ticks() / 70) % self.count('breath')

  def tip(self, i, tb=0, fly=False):
    """mouth (or horn) tip in the 168x128 frame for breath step i (or flight step i), following the tilt."""
    pts = self.m.FLY_TIP if fly else self.m.TIP
    x, y = pts[i % len(pts)]
    if tb:
      a = math.radians(tb * 6)
      dx, dy = x - W / 2.0, y - H / 2.0
      x, y = W / 2.0 + dx * math.cos(a) - dy * math.sin(a), H / 2.0 + dx * math.sin(a) + dy * math.cos(a)
    return x, y

  def death(self, i):
    i = max(0, min(self.count('death') - 1, i))
    return self.frame('death', i), self.m.BOTTOM[i]


_SHEETS = {}


def has_sheet(key):
  return key in MODS


def sheet(key):
  s = _SHEETS.get(key)
  if s is None:
    s = _SHEETS[key] = Sheet(importlib.import_module(MODS[key]))
  return s
