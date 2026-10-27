"""Dragon death animation (recreated from the reference GIF): the dragon rears up roaring,
molten cracks spread over its body as it chars, it topples to the ground, then burns away
into embers and ash. Element colours change per dragon."""
import math
import random
import pygame

# per dragon: (white-hot core, glow, ember, char tint, ash)
DEATH_COLS = {
  'RED': ((255, 244, 170), (255, 170, 40), (230, 70, 10), (70, 28, 22), (60, 52, 50)),
  'BLUE': ((240, 252, 255), (140, 210, 255), (60, 130, 220), (40, 60, 90), (190, 214, 230)),
  'GREEN': ((236, 255, 190), (150, 255, 70), (60, 180, 20), (30, 56, 24), (70, 84, 56)),
  'YELLOW': ((255, 255, 220), (255, 236, 90), (240, 170, 20), (70, 60, 24), (80, 76, 60)),
  'SILVER': ((255, 255, 255), (220, 230, 245), (150, 160, 190), (60, 62, 74), (170, 172, 184)),
}
DEATH_COLS['COSMIC'] = ((255, 236, 255), (200, 110, 255), (130, 40, 200), (30, 14, 50), (70, 56, 96))
DEFAULT_COLS = DEATH_COLS['RED']

REAR, BURN, FALL, GONE = 22, 66, 92, 150           # end tick of each phase
CRACK_STAGES, DISSOLVE_STAGES = 7, 12


def _silhouette(spr):
  try:
    return pygame.mask.from_surface(spr, 60).to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
  except Exception:
    return None


def _clip(layer, sil):
  if sil is not None:
    layer.blit(sil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
  return layer


class DragonDeath:
  def __init__(self, spr, key, hit_center, pivot, ground_y):
    """spr: the dragon's sprite at the moment of death (any surface); pivot: (x, y) inside spr that
    sits at hit_center on screen (the centre of the hitbox)."""
    self.t = 0
    self.key = key
    self.cols = DEATH_COLS.get(key, DEFAULT_COLS)
    core, glow, ember, char, ash = self.cols
    base = pygame.Surface(spr.get_size(), pygame.SRCALPHA)
    base.blit(spr, (0, 0))
    self.base = base
    self.w, self.h = base.get_size()
    self.pivot = pivot
    self.cx, self.cy = float(hit_center[0]), float(hit_center[1])
    self.vy = 0.0
    self.ground = ground_y
    self.ang = 0.0
    self.squash = 1.0
    self.alpha = 255
    self.done = False
    sil = _silhouette(base)
    rnd = random.Random(7)
    self.pts = []                                           # points inside the body (for embers)
    try:
      m = pygame.mask.from_surface(base, 60)
      for _ in range(400):
        x, y = rnd.randrange(self.w), rnd.randrange(self.h)
        if m.get_at((x, y)):
          self.pts.append((x, y))
    except Exception:
      pass
    if not self.pts:
      self.pts = [(self.w // 2, self.h // 2)]
    # --- molten cracks and blotches, revealed a few at a time
    cracks = []
    for _ in range(26):
      x, y = rnd.choice(self.pts)
      seg = [(x, y)]
      a = rnd.uniform(0, math.tau)
      for _ in range(rnd.randint(3, 6)):
        a += rnd.uniform(-0.9, 0.9)
        x += math.cos(a) * rnd.uniform(4, 9); y += math.sin(a) * rnd.uniform(3, 7)
        seg.append((x, y))
      blob = rnd.random() < 0.45
      cracks.append((seg, blob, rnd.uniform(3, 7)))
    self.crack_stages = []
    for k in range(1, CRACK_STAGES + 1):
      n = int(len(cracks) * k / CRACK_STAGES)
      f = 1.0 - 0.62 * (k / float(CRACK_STAGES))            # body chars as the fire takes hold
      s = base.copy()
      s.fill((int(255 * f + char[0] * (1 - f) * 0.6), int(255 * f + char[1] * (1 - f) * 0.6), int(255 * f + char[2] * (1 - f) * 0.6), 255), special_flags=pygame.BLEND_RGBA_MULT)
      layer = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
      for seg, blob, r in cracks[:n]:
        pygame.draw.lines(layer, ember, False, seg, 3)
        pygame.draw.lines(layer, glow, False, seg, 2)
        pygame.draw.lines(layer, core, False, seg, 1)
        if blob:
          bx, by = seg[len(seg) // 2]
          pygame.draw.ellipse(layer, ember, (bx - r, by - r * 0.7, r * 2, r * 1.4))
          pygame.draw.ellipse(layer, glow, (bx - r * 0.7, by - r * 0.5, r * 1.4, r))
          pygame.draw.ellipse(layer, core, (bx - r * 0.3, by - r * 0.25, r * 0.6, r * 0.5))
      s.blit(_clip(layer, sil), (0, 0))
      self.crack_stages.append(s)
    # --- burning away: holes with glowing rims eat the charred body
    self.dissolve = []
    cur = self.crack_stages[-1].copy()
    holes = []
    for k in range(DISSOLVE_STAGES):
      for _ in range(10 + k * 4):
        holes.append((rnd.choice(self.pts), rnd.uniform(2, 4) + k * 0.6))
      s = cur.copy()
      rim = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
      for (x, y), r in holes:
        pygame.draw.circle(rim, glow, (x, y), int(r + 2))
      for (x, y), r in holes:
        pygame.draw.circle(rim, core, (x, y), int(r + 1))
      s.blit(_clip(rim, sil), (0, 0))
      for (x, y), r in holes:
        pygame.draw.circle(s, (0, 0, 0, 0), (x, y), int(r))
      self.dissolve.append(s)

  # ------------------------------------------------------------------
  def _world(self, px, py):
    """sprite pixel -> screen position (rotation + squash around the pivot)."""
    vx, vy = px - self.pivot[0], (py - self.pivot[1]) * self.squash
    a = math.radians(self.ang)
    return (self.cx + vx * math.cos(a) + vy * math.sin(a), self.cy - vx * math.sin(a) + vy * math.cos(a))

  def update(self, game):
    t = self.t = self.t + 1
    core, glow, ember, char, ash = self.cols
    if t <= REAR:                                           # rear up, head back, roaring
      u = t / float(REAR)
      self.ang = 62 * (1 - (1 - u) ** 2)
      self.cy -= 0.7
      if t % 2 == 0:                                        # a last gout of flame from the jaws
        hx, hy = self._world(self.pivot[0] + 60, self.pivot[1] - 15)
        game.emit(hx, hy, random.uniform(-1, 1), random.uniform(-4, -2), random.randint(5, 9), random.choice((core, glow, ember)))
    elif t <= BURN:                                         # burning: shudders, sways, cracks spread
      self.ang = 62 + math.sin(t * 0.35) * 5
      self.cx += math.sin(t * 2.1) * 0.8
      for _ in range(2):
        x, y = self._world(*random.choice(self.pts))
        game.emit(x, y, random.uniform(-0.6, 0.6), random.uniform(-2.4, -0.8), random.randint(2, 5), random.choice((glow, ember, core)))
    elif t <= FALL:                                         # topples forward and drops
      u = (t - BURN) / float(FALL - BURN)
      self.ang = 62 - 82 * u
      self.vy += 0.7
      self.cy += self.vy
      floor = self.ground - self.h * 0.18
      if self.cy >= floor:
        self.cy = floor
        if self.vy > 2:
          game.shake_for(6, 8)
          for _ in range(14):
            game.emit(self.cx + random.uniform(-40, 40), self.ground - 6, random.uniform(-2.4, 2.4), random.uniform(-2.2, -0.4), random.randint(6, 11), random.choice((ash, char, ember)))
        self.vy = 0
        self.squash = max(0.62, self.squash - 0.06)
      for _ in range(2):
        x, y = self._world(*random.choice(self.pts))
        game.emit(x, y, random.uniform(-0.6, 0.6), random.uniform(-2.2, -0.6), random.randint(2, 5), random.choice((glow, ember)))
    elif t <= GONE:                                         # burns away to embers and ash
      floor = self.ground - self.h * 0.18
      self.cy = min(floor, self.cy + 2)
      self.squash = max(0.5, self.squash - 0.004)
      for _ in range(4):
        x, y = self._world(*random.choice(self.pts))
        game.emit(x, y, random.uniform(-0.8, 0.8), random.uniform(-3.0, -0.8), random.randint(2, 6), random.choice((core, glow, ember, ash, ash)))
      if t % 5 == 0:
        game.emit(self.cx + random.uniform(-30, 30), self.ground - 10, random.uniform(-0.4, 0.4), random.uniform(-1.4, -0.6), random.randint(8, 13), ash)
      if t > GONE - 20:
        self.alpha = max(0, int(255 * (GONE - t) / 20.0))
    else:
      self.done = True

  def frame(self):
    t = self.t
    if t <= REAR:
      return self.base
    if t <= BURN:
      k = int((t - REAR) / float(BURN - REAR) * CRACK_STAGES)
      return self.crack_stages[min(CRACK_STAGES - 1, k)]
    if t <= FALL:
      return self.crack_stages[-1]
    k = int((t - FALL) / float(GONE - FALL) * DISSOLVE_STAGES)
    return self.dissolve[min(DISSOLVE_STAGES - 1, k)]

  def draw(self, gs):
    if self.done:
      return
    t = self.t
    core, glow, ember, char, ash = self.cols
    if t > FALL - 6:                                        # glowing ash pile under the body
      a = max(0.0, min(1.0, (GONE + 10 - t) / 40.0))
      pile = pygame.Surface((150, 40), pygame.SRCALPHA)
      pygame.draw.ellipse(pile, ash + (int(200 * a),), (0, 14, 150, 22))
      pygame.draw.ellipse(pile, ember + (int(170 * a),), (30, 18, 90, 14))
      pygame.draw.ellipse(pile, glow + (int(150 * a),), (52, 21, 46, 8))
      gs.blit(pile, (int(self.cx) - 75, int(self.ground) - 32))
    spr = self.frame()
    if t <= 3:                                             # hit flash
      spr = spr.copy()
      spr.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if self.squash != 1.0:
      spr = pygame.transform.scale(spr, (self.w, max(1, int(self.h * self.squash))))
    if self.alpha < 255:
      spr = spr.copy()
      spr.set_alpha(self.alpha)
    pvx, pvy = self.pivot[0], self.pivot[1] * self.squash
    rot = pygame.transform.rotate(spr, self.ang)
    vx, vy = spr.get_width() / 2.0 - pvx, spr.get_height() / 2.0 - pvy
    a = math.radians(self.ang)
    nx = vx * math.cos(a) + vy * math.sin(a)
    ny = -vx * math.sin(a) + vy * math.cos(a)
    gs.blit(rot, rot.get_rect(center=(int(self.cx + nx), int(self.cy + ny))))


class BoneDeath:
  """Bone Reaper's death (from your animation): it folds its wings and collapses mid-air,
  drops to the ground and shatters into a spray of bones and dust."""
  def __init__(self, x, y, ground_y):
    from fd_bone import bone_death
    self.frame = bone_death
    self.x, self.y = float(x), float(y)            # top-left of the 168x128 dragon frame
    self.vy = -2.5
    self.ground = ground_y
    self.t = 0
    self.landed = None
    self.done = False
    self.bones = []

  def update(self, game):
    self.t += 1
    if self.landed is None:
      if self.t > 12:                               # hangs for a moment as the wings fold, then falls
        self.vy += 0.55
        self.y += self.vy
      if self.y + 112 >= self.ground:
        self.y = self.ground - 112
        self.landed = self.t
        game.shake_for(10, 10)
        cx = self.x + 70
        for _ in range(26):                         # bursts into bones
          self.bones.append([cx + random.uniform(-40, 40), self.ground - random.uniform(10, 60), random.uniform(-5, 5), random.uniform(-9, -2),
                             random.uniform(0, 6.3), random.uniform(-0.4, 0.4)])
        for _ in range(18):
          game.emit(cx + random.uniform(-50, 50), self.ground - 6, random.uniform(-2.4, 2.4), random.uniform(-2.4, -0.4), random.randint(7, 12),
                    random.choice(((200, 190, 170), (120, 110, 100), (180, 120, 240))))
      return
    for b in self.bones:
      b[0] += b[2]; b[1] += b[3]; b[3] += 0.5; b[4] += b[5]
      if b[1] > self.ground - 3:
        b[1] = self.ground - 3; b[3] *= -0.25; b[2] *= 0.5; b[5] *= 0.5
    if self.t - self.landed > 90:
      self.done = True

  def draw(self, gs):
    if self.done:
      return
    if self.landed is None:
      gs.blit(self.frame(self.t // 2), (int(self.x), int(self.y)))
      return
    k = self.t - self.landed
    f = max(0.0, 1 - k / 90.0)
    for bx, by, vx, vy, rot, vr in self.bones:
      ca, sa = math.cos(rot) * 7, math.sin(rot) * 7
      col = (int(70 * f + 30), int(62 * f + 26), int(54 * f + 26))
      pygame.draw.line(gs, col, (bx - ca, by - sa + 1), (bx + ca, by + sa + 1), 4)
      pygame.draw.line(gs, (int(232 * f + 40 * (1 - f)), int(222 * f + 36 * (1 - f)), int(198 * f + 36 * (1 - f))), (bx - ca, by - sa), (bx + ca, by + sa), 2)
      pygame.draw.circle(gs, (int(240 * f + 40 * (1 - f)),) * 3, (int(bx - ca), int(by - sa)), 2)
      pygame.draw.circle(gs, (int(240 * f + 40 * (1 - f)),) * 3, (int(bx + ca), int(by + sa)), 2)


SHEET_DEATH_COLS = {
  'RED': ((255, 236, 110), (255, 150, 30), (230, 70, 10), (60, 40, 36)),
  'BLUE': ((240, 252, 255), (170, 225, 255), (90, 160, 230), (200, 220, 235)),
  'GREEN': ((200, 255, 120), (120, 240, 60), (60, 160, 30), (30, 70, 30)),
  'YELLOW': ((255, 255, 220), (255, 236, 90), (140, 200, 255), (90, 80, 40)),
  'SILVER': ((255, 255, 255), (210, 245, 250), (120, 220, 230), (90, 110, 130)),
  'COCKATRICE': ((255, 230, 120), (230, 120, 50), (200, 50, 40), (110, 120, 50)),
  'FOREST': ((200, 230, 90), (120, 180, 50), (70, 120, 30), (110, 80, 40)),
  'CHINESE': ((255, 240, 160), (255, 160, 60), (220, 50, 40), (120, 30, 30)),
  'CLOCKWORK': ((255, 220, 120), (200, 160, 80), (140, 110, 60), (90, 90, 90)),
  'WRAITH': ((230, 255, 255), (140, 240, 255), (70, 170, 200), (40, 90, 120)),
  'ALIEN': ((200, 255, 150), (120, 240, 70), (60, 170, 40), (20, 60, 24)),
  'EAGLE': ((255, 240, 190), (240, 200, 100), (190, 140, 50), (110, 80, 30)),
  'WHALE': ((255, 255, 255), (200, 180, 255), (120, 90, 220), (120, 255, 230)),
  'FEY': ((255, 255, 200), (255, 150, 240), (140, 240, 255), (180, 255, 160)),
  'UNICORN': ((255, 80, 80), (255, 230, 80), (80, 220, 110), (90, 150, 255), (190, 90, 255), (255, 255, 255)),
}


class SheetDeath:
  """Death from your animation sets (Magma, Ice, Evil Unicorn): it plays its own death frames as it
  drops to the ground, lies there for a moment, then fades away in a puff of its colours."""
  STEP = 3                                        # game frames per animation frame
  HOLD, FADE = 45, 30

  def __init__(self, key, x, y, ground_y):
    from fd_sheet import sheet
    self.sh = sheet(key)
    self.cols = SHEET_DEATH_COLS.get(key, SHEET_DEATH_COLS['RED'])
    self.x, self.y = float(x), float(y)            # top-left of the 168x128 dragon frame
    self.vy = -2.0
    self.ground = ground_y
    self.t = 0
    self.landed = None
    self.done = False
    self.n = self.sh.count('death')
    self.alpha = 255
    self.floats = key in ('WRAITH', 'YELLOW', 'FOREST', 'COCKATRICE', 'WHALE', 'FEY', 'EAGLE')   # dissolves in the air instead of falling
    self.land_at = {'GREEN': 5, 'SILVER': 6, 'ALIEN': 4}.get(key)         # the Acid Dragon only melts into its puddle once it hits the ground

  def _fi(self):
    fi = min(self.n - 1, self.t // self.STEP)
    if self.land_at is not None:
      if self.landed is None:
        return min(fi, self.land_at)
      return min(self.n - 1, self.land_at + (self.t - self.landed) // self.STEP)
    return fi

  def update(self, game):
    self.t += 1
    spr, bottom = self.sh.death(self._fi())
    if self.landed is None:
      if self.floats:
        self.y += 0.4
        self.vy = 0.0
      elif self.t > 6:                             # a moment of shock, then it drops
        self.vy += 0.5
        self.y += self.vy
      if self.y + bottom >= self.ground and not self.floats:
        self.landed = self.t
        game.shake_for(8, 10)
        cx = self.x + 72
        for _ in range(20):
          game.emit(cx + random.uniform(-55, 55), self.ground - 6, random.uniform(-2.4, 2.4), random.uniform(-2.6, -0.4), random.randint(6, 11), random.choice(self.cols))
    if self.landed is not None:
      self.y = self.ground - bottom                # stays on the ground as the frames change
    if self.t % 3 == 0:
      game.emit(self.x + random.uniform(30, 130), self.y + random.uniform(30, bottom), random.uniform(-0.6, 0.6), random.uniform(-2.0, -0.5), random.randint(3, 6), random.choice(self.cols))
    end = self.n * self.STEP + self.HOLD + ((self.landed or 0) if self.land_at is not None else 0)
    if self.t > end:
      self.alpha = max(0, int(255 * (1 - (self.t - end) / float(self.FADE))))
      if self.t % 2 == 0:
        game.emit(self.x + random.uniform(30, 130), self.y + random.uniform(50, bottom), random.uniform(-0.8, 0.8), random.uniform(-2.4, -0.8), random.randint(4, 8), random.choice(self.cols))
    if self.t > end + self.FADE:
      self.done = True

  def draw(self, gs):
    if self.done:
      return
    spr, _b = self.sh.death(self._fi())
    if self.t <= 3:                                # hit flash
      spr = spr.copy()
      spr.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGBA_ADD)
    elif self.alpha < 255:
      spr = spr.copy()
      spr.set_alpha(self.alpha)
    gs.blit(spr, (int(self.x), int(self.y)))
