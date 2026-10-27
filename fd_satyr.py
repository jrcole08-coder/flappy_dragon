import base64
import zlib
import pygame

SAT = (48, 56, '5d2c288a4836bf6f4a272727e69c69f6ca9fc7cfddf8f8f8ffffff583828ed7614ffa214657392ffc82592a1b9353535494949', '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')
SCACHE = {}


def satyr_frame(fr):
  """Frame (0-11) of the Satyr Archer, facing left."""
  fr %= 12
  s = SCACHE.get(fr)
  if s is None:
    w, h, pal, data = SAT
    if 'raw' not in SCACHE:
      SCACHE['pal'] = [None] + [tuple(int(pal[i + k:i + k + 2], 16) for k in (0, 2, 4)) for i in range(0, len(pal), 6)]
      SCACHE['raw'] = zlib.decompress(base64.b64decode(data))
    raw, p = SCACHE['raw'], SCACHE['pal']
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    base = fr * w * h
    for i in range(w * h):
      v = raw[base + i]
      if v:
        s.set_at((i % w, i // w), p[v] + (255,))
    SCACHE[fr] = s
  return s
