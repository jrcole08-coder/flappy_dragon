"""Double-resolution shaded dragon art (pre-rendered). Frames: 4 wing poses x 5 head tilts x (normal, breathing)."""
import base64
import zlib
import pygame

HD_ART = {}
_RAW = {}
_SURF = {}


def hd_frame(key, fi, tb, fire):
  """Returns a 168x128 RGBA surface, or None if this dragon has no HD art."""
  art = HD_ART.get(key)
  if art is None:
    return None
  k = (key, fi, tb, bool(fire))
  s = _SURF.get(k)
  if s is None:
    w, h, data = art
    raw = _RAW.get(key)
    if raw is None:
      raw = _RAW[key] = zlib.decompress(base64.b64decode(data))
    i = ((fi * 5) + (tb + 2)) * 2 + (1 if fire else 0)
    n = w * h * 4
    s = _SURF[k] = pygame.image.frombuffer(raw[i * n:(i + 1) * n], (w, h), 'RGBA').copy()
    if sum(1 for q in _SURF if q[0] == key) >= 40:
      _RAW.pop(key, None)                     # every frame built: free the raw pixels
  return s
