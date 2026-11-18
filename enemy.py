import math
import random
import sys
import pygame

# =========================================================
# Config
# =========================================================
W, H = 960, 540
FPS = 60

GROUND_Y = 460
GRAVITY = 1200.0

WORLD_W = 5200  # 横に長い世界（スクロール用）
SEGMENT_W = 960  # 画面1枚ぶんを「区画」として扱う

# 区画（画面）ごとの「菌テーマ」：色パレットと出やすさ
THEMES = [
    {
        "name": "Pastel",
        "palette": {
            "cute": (255, 150, 220),
            "evil": (190, 120, 255),
            "spore": (170, 255, 240),
        },
        "weights": {"cute": 0.65, "evil": 0.10, "spore": 0.25},
        "faces": {"cute": ["happy", "sleepy", "uwu"], "evil": ["angry"], "spore": [None]},
    },
    {
        "name": "Toxic",
        "palette": {
            "cute": (255, 210, 120),
            "evil": (120, 255, 120),
            "spore": (60, 220, 160),
        },
        "weights": {"cute": 0.20, "evil": 0.60, "spore": 0.20},
        "faces": {"cute": ["happy", "uwu"], "evil": ["angry"], "spore": [None]},
    },
    {
        "name": "DeepSea",
        "palette": {
            "cute": (140, 200, 255),
            "evil": (80, 120, 255),
            "spore": (120, 255, 220),
        },
        "weights": {"cute": 0.35, "evil": 0.25, "spore": 0.40},
        "faces": {"cute": ["sleepy", "happy", "uwu"], "evil": ["angry"], "spore": [None]},
    },
    {
        "name": "Candy",
        "palette": {
            "cute": (255, 120, 160),
            "evil": (255, 110, 255),
            "spore": (255, 220, 140),
        },
        "weights": {"cute": 0.72, "evil": 0.08, "spore": 0.20},
        "faces": {"cute": ["happy", "uwu"], "evil": ["angry"], "spore": [None]},
    },
]

def theme_for_segment(seg: int):
    return THEMES[seg % len(THEMES)]

def weighted_choice(weights: dict):
    r = random.random()
    acc = 0.0
    last_k = None
    for k, w in weights.items():
        last_k = k
        acc += float(w)
        if r <= acc:
            return k
    return last_k

def clamp(v, a, b):
    return max(a, min(b, v))

def aabb(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

# =========================================================
# Projectiles
# =========================================================
class Projectile:
    """
    typ: "germ" or "flame"
    germ_kind: "cute" | "evil" | "spore"
    """
    def __init__(self, typ, x, y, vx, vy, germ_kind=None, *, palette=None, face=None):
        self.typ = typ
        self.germ_kind = germ_kind  # 菌の種類
        # 区画（画面）ごとに色を変えるためのパレット（dict: kind -> (r,g,b)）
        self.palette = palette or {}
        # 顔のバリエーション（"happy"/"angry"/"sleepy" など）
        self.face = face

        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)

        if self.typ == "flame":
            self.r = 8
            self.life = 1.1
            self.gravity = 900.0
        else:
            # 菌の種類で見た目と性能を変える
            if self.germ_kind == "cute":
                self.r = 7
                self.life = 2.0
                self.gravity = 120.0   # ふわっと落ちる
            elif self.germ_kind == "evil":
                self.r = 6
                self.life = 1.8
                self.gravity = 0.0     # 直線気味
            else:  # "spore"
                self.r = 6
                self.life = 2.2
                self.gravity = 200.0

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

        # 菌ごとの床反応
        if self.typ == "germ" and self.y + self.r > GROUND_Y:
            self.y = GROUND_Y - self.r
            if self.germ_kind == "spore":
                # sporeは跳ねる
                self.vx *= 0.55
                self.vy *= -0.55
            elif self.germ_kind == "cute":
                # cuteはコロコロ転がって弱く跳ねる
                self.vx *= 0.70
                self.vy *= -0.18
            else:
                # evilは床で減速して消えやすい感じ
                self.vx *= 0.25
                self.vy *= -0.10

    def draw(self, surf, cam_x):
        if self.typ == "flame":
            col = (255, 138, 61)
            pygame.draw.circle(surf, col, (int(self.x - cam_x), int(self.y)), self.r)
            return

        # 菌の色（区画テーマのパレットがあれば優先）
        if self.germ_kind in self.palette:
            col = self.palette[self.germ_kind]
        else:
            if self.germ_kind == "cute":
                col = (255, 170, 220)  # ピンク
            elif self.germ_kind == "evil":
                col = (160, 90, 255)   # 紫
            else:
                col = (182, 255, 234)  # ミント

        cx = int(self.x - cam_x)
        cy = int(self.y)

        # 見た目：もっと「かわいい」に寄せる
        # - 外側リング
        # - つや（ハイライト）
        # - 大きめの目（キラ目）
        # - ほっぺ
        # - 表情（happy/sleepy/uwu）
        # - 小さいアクセ（星）

        # 外側リング（ぷに感）
        ring = (255, 255, 255)
        pygame.draw.circle(surf, ring, (cx, cy), self.r)
        pygame.draw.circle(surf, col, (cx, cy), max(1, self.r - 2))

        # ハイライト（ツヤ）
        hi = (255, 255, 255)
        pygame.draw.circle(surf, hi, (cx - max(2, self.r // 3), cy - max(2, self.r // 3)), max(2, self.r // 3))
        pygame.draw.circle(surf, (255, 255, 255), (cx - 1, cy - 1), 1)

        if self.germ_kind == "cute":
            eye = (40, 40, 55)
            white = (255, 255, 255)

            # 目（キラ目）
            ex1, ex2 = cx - 4, cx + 4
            ey = cy - 1
            pygame.draw.circle(surf, eye, (ex1, ey), 2)
            pygame.draw.circle(surf, eye, (ex2, ey), 2)
            pygame.draw.circle(surf, white, (ex1 - 1, ey - 1), 1)
            pygame.draw.circle(surf, white, (ex2 - 1, ey - 1), 1)

            # ほっぺ
            blush = (255, 120, 170)
            pygame.draw.circle(surf, blush, (cx - 7, cy + 3), 2)
            pygame.draw.circle(surf, blush, (cx + 7, cy + 3), 2)

            # 口（表情）
            if self.face == "sleepy":
                pygame.draw.line(surf, eye, (cx - 6, cy - 2), (cx - 2, cy - 2), 2)
                pygame.draw.line(surf, eye, (cx + 2, cy - 2), (cx + 6, cy - 2), 2)
                pygame.draw.arc(surf, eye, (cx - 4, cy + 3, 8, 5), math.pi * 0.10, math.pi * 0.90, 2)
            elif self.face == "uwu":
                pygame.draw.arc(surf, eye, (cx - 6, cy + 2, 6, 4), math.pi * 0.10, math.pi * 0.90, 2)
                pygame.draw.arc(surf, eye, (cx, cy + 2, 6, 4), math.pi * 0.10, math.pi * 0.90, 2)
            else:
                pygame.draw.arc(surf, eye, (cx - 4, cy + 2, 8, 5), math.pi * 0.10, math.pi * 0.90, 2)

            # 小アクセ（星）
            star = (255, 245, 150)
            pygame.draw.circle(surf, star, (cx + self.r - 2, cy - self.r + 2), 1)

        elif self.germ_kind == "evil":
            # 悪い菌：かわいいを保ちつつ、色で“悪い”感（顔は怒り/ニヤ）
            outline = (25, 10, 45)
            pygame.draw.circle(surf, outline, (cx, cy), self.r, 2)

            eye = (25, 10, 45)
            pygame.draw.line(surf, eye, (cx - 7, cy - 4), (cx - 2, cy - 2), 2)
            pygame.draw.line(surf, eye, (cx + 2, cy - 2), (cx + 7, cy - 4), 2)
            pygame.draw.circle(surf, eye, (cx - 4, cy), 2)
            pygame.draw.circle(surf, eye, (cx + 4, cy), 2)

            # ニヤ口
            pygame.draw.arc(surf, eye, (cx - 5, cy + 2, 10, 6), math.pi * 0.05, math.pi * 0.95, 2)

        else:
            # spore：ふわふわ＋粒々多め
            dot = (245, 250, 255)
            pygame.draw.circle(surf, dot, (cx + 2, cy - 2), 1)
            pygame.draw.circle(surf, dot, (cx - 2, cy + 2), 1)
            pygame.draw.circle(surf, dot, (cx + 5, cy + 1), 1)

# =========================================================
# Virus enemy
# =========================================================
class Virus:
    def __init__(self, x, y_ground, size=1.0):
        self.size = float(size)
        base = 46.0
        self.w = base * self.size
        self.h = base * self.size

        self.x = float(x)
        self.y = float(y_ground - self.h)

        # 大きいほど強い（例）
        self.hp = max(1, round(1 * self.size))
        self.touch_damage = max(1, round(1 * self.size))
        self.speed = (65.0 / math.sqrt(self.size))  # big = slower
        self.dir = -1 if random.random() < 0.5 else 1

        self.dead = False
        self.death_timer = 0.0
        self.remove = False

        # 移動範囲（そのへんで反転）
        self.patrol_left = self.x - 140
        self.patrol_right = self.x + 140

    def stomped(self):
        if self.dead:
            return
        self.dead = True
        self.death_timer = 0.18  # 演出→散布

    def explode(self, projectiles, *, theme=None):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        # 菌（直線弾）
        base_bullets = 4
        count = max(2, round(base_bullets * self.size))
        spread = (math.pi * 0.70) + (self.size * 0.25)
        center = -math.pi / 2

        for i in range(count):
            t = 0.5 if count == 1 else i / (count - 1)
            a = center - spread / 2 + spread * t + (random.random() - 0.5) * 0.22

            if theme is None:
                kind = random.choice(["cute", "evil", "spore"])
                palette = None
                face = None
            else:
                kind = weighted_choice(theme["weights"])
                palette = theme.get("palette")
                face_list = theme.get("faces", {}).get(kind, [None])
                face = random.choice(face_list) if face_list else None

            # 菌の種類で速度を変える（かわいい=少し遅い、悪い=速い）
            if kind == "cute":
                sp = 200 * (0.85 + 0.08 * self.size)
            elif kind == "evil":
                sp = 310 * (0.85 + 0.08 * self.size)
            else:
                sp = 235 * (0.85 + 0.08 * self.size)

            projectiles.append(
                Projectile(
                    "germ",
                    cx,
                    cy,
                    math.cos(a) * sp,
                    math.sin(a) * sp,
                    germ_kind=kind,
                    palette=palette,
                    face=face,
                )
            )

        # 炎（重力あり、数少なめ）
        flames = max(1, round(1.2 * self.size))
        for _ in range(flames):
            a = center + (random.random() - 0.5) * 0.8
            vx = math.cos(a) * 190
            vy = math.sin(a) * 320
            projectiles.append(Projectile("flame", cx, self.y + 10, vx, vy))

    def update(self, dt, projectiles, *, theme=None):
        if self.dead:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.explode(projectiles, theme=theme)
                self.remove = True
            return

        self.x += self.speed * self.dir * dt
        if self.x < self.patrol_left:
            self.x = self.patrol_left
            self.dir = 1
        if self.x + self.w > self.patrol_right:
            self.x = self.patrol_right - self.w
            self.dir = -1

        # 床に置く
        self.y = GROUND_Y - self.h

    def draw(self, surf, cam_x):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        # 死亡演出（つぶれ）
        sx, sy = 1.0, 1.0
        if self.dead:
            p = clamp(1 - self.death_timer / 0.18, 0, 1)
            sx = 1 + p * 0.25
            sy = 1 - p * 0.55

        r = min(self.w, self.h) * 0.45
        body = (124, 255, 169)
        spike = (42, 224, 122)

        rect = pygame.Rect(0, 0, int(r * 2 * sx), int(r * 2 * sy))
        rect.center = (int(cx - cam_x), int(cy))
        pygame.draw.ellipse(surf, body, rect)

        for i in range(10):
            a = i * (math.pi * 2 / 10)
            x1 = (cx - cam_x) + math.cos(a) * r
            y1 = cy + math.sin(a) * r
            x2 = (cx - cam_x) + math.cos(a) * (r + 10 * self.size)
            y2 = cy + math.sin(a) * (r + 10 * self.size)
            pygame.draw.line(surf, spike, (x1, y1), (x2, y2), 3)

# =========================================================
# Player
# =========================================================
class Player:
    def __init__(self):
        self.w, self.h = 34, 54
        self.x = 80.0
        self.y = float(GROUND_Y - self.h)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def update(self, dt, keys):
        accel = 1600.0
        max_speed = 300.0

        if keys[pygame.K_LEFT]:
            self.vx -= accel * dt
        if keys[pygame.K_RIGHT]:
            self.vx += accel * dt

        # 摩擦
        self.vx *= math.pow(0.0009, dt)
        self.vx = clamp(self.vx, -max_speed, max_speed)

        # ジャンプ
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -520.0
            self.on_ground = False

        # 重力
        self.vy += GRAVITY * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        # 地面
        if self.y + self.h >= GROUND_Y:
            self.y = float(GROUND_Y - self.h)
            self.vy = 0.0
            self.on_ground = True

        self.x = clamp(self.x, 0, WORLD_W - self.w)

    def draw(self, surf, cam_x):
        pygame.draw.rect(surf, (127, 178, 255), pygame.Rect(int(self.x - cam_x), int(self.y), self.w, self.h))

# =========================================================
# Spawning by segment (画面が変わる=区画が変わる)
# =========================================================
def segment_index(x):
    return int(x // SEGMENT_W)

def spawn_for_segment(seg):
    # 区画ごとに敵を固定で出す（例）
    # ここを増やせば「画面が変わるごとに出現」になる
    spawns = {
        0: [(520, 1.0), (780, 1.5)],
        1: [(SEGMENT_W + 600, 2.2)],
        2: [(SEGMENT_W*2 + 520, 1.0), (SEGMENT_W*2 + 700, 1.0), (SEGMENT_W*2 + 840, 2.2)],
        3: [(SEGMENT_W*3 + 720, 1.5), (SEGMENT_W*3 + 860, 1.5)],
        4: [(SEGMENT_W*4 + 760, 2.2)],
    }

    viruses = []
    for x, size in spawns.get(seg, []):
        viruses.append(Virus(x, GROUND_Y, size))
    return viruses

# =========================================================
# Main loop
# =========================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Virus Platformer (Python/Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    player = Player()
    viruses = []
    projectiles = []

    spawned_segments = set()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1/20)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(dt, keys)

        # カメラ（プレイヤー中心、端で止まる）
        cam_x = clamp(player.x - W * 0.40, 0, WORLD_W - W)

        # 区画（画面）ごとの菌テーマ
        seg = segment_index(player.x)
        theme = theme_for_segment(seg)

        # 区画が変わったら、その区画の敵をスポーン（1回だけ）
        if seg not in spawned_segments:
            spawned_segments.add(seg)
            viruses.extend(spawn_for_segment(seg))

        # 敵更新（死ぬときにこの区画のテーマで菌を出す）
        for v in viruses:
            v.update(dt, projectiles, theme=theme)
        viruses = [v for v in viruses if not v.remove]

        # 踏み判定
        px, py, pw, ph = player.rect()
        for v in viruses:
            if v.dead:
                continue
            vx, vy, vw, vh = v.x, v.y, v.w, v.h
            if not aabb(px, py, pw, ph, vx, vy, vw, vh):
                continue

            # 上から踏んだ判定：落下中 & 前フレームの足が敵上面より上
            player_falling = player.vy > 0
            enemy_top = vy
            player_bottom_prev = (player.y - player.vy * (1/60.0)) + player.h
            stomped = player_falling and player_bottom_prev <= enemy_top + 12

            if stomped:
                v.stomped()
                player.vy = -360.0
            else:
                # 横当たりは簡易ノックバック（今回はHPなど未実装）
                player.vx = (-1 if player.x < vx else 1) * 260.0
                player.vy = -260.0

        # 弾更新
        for b in projectiles:
            b.update(dt)
        projectiles = [b for b in projectiles if b.life > 0]

        # Draw
        screen.fill((11, 18, 32))

        # Ground
        pygame.draw.rect(screen, (12, 42, 27), pygame.Rect(0, GROUND_Y, W, H - GROUND_Y))
        pygame.draw.line(screen, (31, 107, 69), (0, GROUND_Y), (W, GROUND_Y), 2)

        # 背景に区画線（“画面が変わる”が分かりやすい）
        for i in range(0, WORLD_W + 1, SEGMENT_W):
            x = int(i - cam_x)
            pygame.draw.line(screen, (30, 40, 60), (x, 0), (x, H), 1)

        # Enemies & bullets & player
        for v in viruses:
            v.draw(screen, cam_x)
        for b in projectiles:
            b.draw(screen, cam_x)
        player.draw(screen, cam_x)

        # HUD
        seg_now = segment_index(player.x)
        theme_now = theme_for_segment(seg_now)
        txt = font.render(
            f"X={int(player.x)}  Segment={seg_now} Theme={theme_now['name']}  (←→ move / Space jump) stomp=kill + spread",
            True, (203, 213, 225)
        )
        screen.blit(txt, (18, 14))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
