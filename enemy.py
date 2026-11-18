import math
import random
import sys
import pygame

# =========================================================
# Config
# =========================================================
W, H = 960, 540
FPS = 60

# 表情・揺れ用（簡単なアニメ）
GLOBAL_T = 0.0

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


def lerp(a, b, t: float):
    return a + (b - a) * t


def lerp_col(c1, c2, t: float):
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


# ねねこ画像っぽい配色（厳密寄せのため固定）
VIRUS_STYLE = {
    # ぷち（白〜ピンク）
    "S": {
        "name": "petit",
        "body": (255, 214, 236),
        "shade": (255, 170, 214),
        "outline": (60, 55, 70),
        "cheek": (255, 138, 185),
        "spike": (255, 170, 214),
    },
    # ほのお（紫〜赤紫 + 炎）
    "M": {
        "name": "fire",
        "body": (196, 144, 255),
        "shade": (150, 95, 230),
        "outline": (40, 35, 60),
        "cheek": (255, 150, 190),
        "spike": (150, 95, 230),
        "flame": (255, 120, 40),
        "flame2": (255, 210, 90),
    },
    # ばちばち（ミント〜緑）
    "L": {
        "name": "spark",
        "body": (182, 255, 228),
        "shade": (110, 220, 170),
        "outline": (35, 55, 55),
        "cheek": (255, 160, 190),
        "spike": (110, 220, 170),
        "spark": (255, 240, 160),
        "spark2": (160, 255, 235),
    },
    # ボス（濃い紫〜黒 + 王冠）
    "B": {
        "name": "boss",
        "body": (88, 62, 118),
        "shade": (60, 40, 92),
        "outline": (18, 15, 28),
        "cheek": (220, 120, 180),
        "spike": (40, 25, 60),
        "crown": (255, 214, 70),
        "crown2": (255, 160, 60),
    },
}

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
            # 菌はシンプルに（凝りすぎない）
            self.r = 6
            self.life = 1.7
            self.gravity = 120.0

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

        # 菌は床で少しだけ跳ねる
        if self.typ == "germ" and self.y + self.r > GROUND_Y:
            self.y = GROUND_Y - self.r
            self.vx *= 0.45
            self.vy *= -0.20

    def draw(self, surf, cam_x):
        if self.typ == "flame":
            col = (255, 138, 61)
            pygame.draw.circle(surf, col, (int(self.x - cam_x), int(self.y)), self.r)
            return

        # 菌は単色でOK（テーマがあればそれを使う）
        col = (190, 255, 235)
        if self.palette:
            # どれか1色を使う（種類は持たない）
            col = next(iter(self.palette.values()))

        cx = int(self.x - cam_x)
        cy = int(self.y)

        # 菌：丸＋ハイライトだけ（シンプル）
        pygame.draw.circle(surf, col, (cx, cy), self.r)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 2, cy - 2), max(1, self.r // 3))

# =========================================================
# Virus enemy
# =========================================================
class Virus:
    def __init__(self, x, y_ground, *, tier="S"):
        # ---------------------------------------------------------
        # ねねこの画像（4体）に寄せた敵バリエーション
        #  - tier="S" : ぷちウィルス（弱い）
        #  - tier="M" : ほのおウィルス（中くらい：炎を投げやすい）
        #  - tier="L" : ばちばちウィルス（大きめ：菌弾多め）
        #  - tier="B" : ボスウィルス（強い：HP多め＆散布多め）
        # ---------------------------------------------------------
        self.tier = tier
        tier_size = {"S": 1.0, "M": 1.55, "L": 2.25, "B": 3.10}.get(tier, 1.0)
        self.size = float(tier_size)
        base = 46.0
        self.w = base * self.size
        self.h = base * self.size

        self.x = float(x)
        self.y = float(y_ground - self.h)

        # 大きいほど強い（明確に数値化）
        # - HP: 大きいほど多い（踏むと1減る。HPが0で死亡演出→散布）
        # - 速度: 大きいほど遅い
        # - ばらまき弾数: 大きいほど多い（explode内で反映）
        self.hp = {"S": 1, "M": 2, "L": 3, "B": 10}.get(tier, 1)
        self.touch_damage = {"S": 1, "M": 2, "L": 3, "B": 4}.get(tier, 1)
        self.speed = (78.0 / math.sqrt(self.size))  # big = slower
        self.dir = -1 if random.random() < 0.5 else 1

        self.dead = False
        self.death_timer = 0.0
        self.remove = False

        # アニメ用
        self.anim_phase = random.uniform(0.0, math.tau)
        self.blink_t = random.uniform(0.4, 2.0)  # 次の瞬きまで
        self.blink_len = 0.10  # 瞬き時間
        self.blink_progress = 0.0

        # 見た目バリエーション（同じ見た目にならない）
        self.style = random.choice(["happy", "sleepy", "grin", "wink"])
        self.eye_style = random.choice(["dot", "oval"])  # 目は少なめにして可愛さ安定
        self.float_amp = random.uniform(2.0, 5.0) * (0.7 + 0.4 * self.size)

        # トゲ（控えめ、数と長さを個体差に）
        self.spike_count = random.randint(6, 10)
        self.spike_len = random.uniform(7.0, 12.0) * (0.8 + 0.4 * self.size)
        self.spike_phase = random.uniform(0.0, math.tau)

        # プレイヤーに向けて菌/炎を撃つ（一定間隔）
        self.shot_cd = random.uniform(0.9, 1.8)  # 初回は少しバラす
        # ちょっと投げすぎ感が出ないように間隔を広げる
        self.shot_interval = {"S": 1.95, "M": 1.45, "L": 1.20, "B": 0.85}.get(self.tier, 1.6)

        # 移動範囲（そのへんで反転）
        self.patrol_left = self.x - 140
        self.patrol_right = self.x + 140

    def stomped(self):
        if self.dead:
            return

        # 踏まれるとHPを減らす（大きい敵は複数回踏まないと倒れない）
        self.hp -= 1
        if self.hp <= 0:
            self.dead = True
            self.death_timer = 0.18  # 演出→散布
        else:
            # まだ生きている：短いひるみ（見た目で分かるように）
            self.hurt_timer = 0.12

    def explode(self, projectiles, *, theme=None):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        # 菌（直線弾）
        base_bullets = 4
        # tier/sizeで弾数を増やす
        tier_bonus = {"S": 0, "M": 2, "L": 5, "B": 11}.get(self.tier, 0)
        count = max(2, round(base_bullets * self.size) + tier_bonus)
        spread = (math.pi * 0.70) + (self.size * 0.25)
        center = -math.pi / 2

        for i in range(count):
            t = 0.5 if count == 1 else i / (count - 1)
            a = center - spread / 2 + spread * t + (random.random() - 0.5) * 0.22

            # 菌はシンプルでOK（速度も固定寄り）
            palette = theme.get("palette") if theme else None
            sp = 235 * (0.85 + 0.08 * self.size)

            projectiles.append(Projectile("germ", cx, cy, math.cos(a) * sp, math.sin(a) * sp, palette=palette))

        # 炎（重力あり、数少なめ）
        # ボスだけさらに炎を多めに
        flames = {"S": 1, "M": 2, "L": 2, "B": 5}.get(self.tier, max(1, round(1.2 * self.size)))
        for _ in range(flames):
            a = center + (random.random() - 0.5) * 0.8
            vx = math.cos(a) * 190
            vy = math.sin(a) * 320
            projectiles.append(Projectile("flame", cx, self.y + 10, vx, vy))

    def update(self, dt, projectiles, *, theme=None, player=None):
        # 被弾（踏まれ）ひるみ
        if not hasattr(self, "hurt_timer"):
            self.hurt_timer = 0.0

        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        if self.dead:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.explode(projectiles, theme=theme)
                self.remove = True
            return

        # 瞬き（アニメ）
        if self.blink_progress > 0:
            self.blink_progress = max(0.0, self.blink_progress - dt)
        else:
            self.blink_t -= dt
            if self.blink_t <= 0:
                self.blink_progress = self.blink_len
                self.blink_t = random.uniform(1.2, 3.2)

        # プレイヤーへ向けて発射（生存中のみ）
        if player is not None:
            # 近いと照れる（ほっぺ濃くする）
            self._player_dist = math.hypot(
                (player.x + player.w / 2) - (self.x + self.w / 2),
                (player.y + player.h / 2) - (self.y + self.h / 2),
            )

            self.shot_cd -= dt
            if self.shot_cd <= 0:
                self.shoot_at_player(projectiles, theme=theme, player=player)
                # 次の発射まで（tierで短く）
                self.shot_cd = self.shot_interval + random.uniform(-0.18, 0.22)

        # ひるみ中は動きを少し止める
        if self.hurt_timer <= 0:
            self.x += self.speed * self.dir * dt
        if self.x < self.patrol_left:
            self.x = self.patrol_left
            self.dir = 1
        if self.x + self.w > self.patrol_right:
            self.x = self.patrol_right - self.w
            self.dir = -1

        # 床に置く
        self.y = GROUND_Y - self.h

    def shoot_at_player(self, projectiles, *, theme=None, player=None):
        """生存中に、プレイヤーの方向へ菌 or 炎を発射する。"""
        if player is None:
            return

        cx = self.x + self.w / 2
        cy = self.y + self.h * 0.35

        # プレイヤーの中心に向ける
        px = player.x + player.w / 2
        py = player.y + player.h / 2
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return
        nx = dx / dist
        ny = dy / dist

        # ねねこの画像のニュアンス：
        # - ぷち: ほぼ菌
        # - ほのお: 炎を投げやすい
        # - ばちばち: 菌多め + 炎は少し
        # - ボス: どちらも撃つ
        flame_chance = {"S": 0.06, "M": 0.55, "L": 0.18, "B": 0.45}.get(self.tier, 0.2)
        shoot_flame = random.random() < flame_chance

        if shoot_flame:
            sp = 260.0
            # 炎は少し上向きにして放物線
            projectiles.append(Projectile("flame", cx, cy, nx * sp, ny * sp - 120.0))
            return

        sp = {"S": 255.0, "M": 275.0, "L": 300.0}.get(self.tier, 270.0)
        # 少しばらけさせる
        jitter = 0.10
        ang = math.atan2(ny, nx) + random.uniform(-jitter, jitter)
        vx = math.cos(ang) * sp
        vy = math.sin(ang) * sp
        # 菌はシンプルでOK（テーマ色があればそれを使う）
        palette = theme.get("palette") if theme else None
        projectiles.append(Projectile("germ", cx, cy, vx, vy, palette=palette))

    def draw(self, surf, cam_x):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        # 死亡演出（つぶれ）
        sx, sy = 1.0, 1.0
        if self.dead:
            p = clamp(1 - self.death_timer / 0.18, 0, 1)
            sx = 1 + p * 0.25
            sy = 1 - p * 0.55

        # --- Character-like enemy look (not a real-world clone) ---
        # 丸い“ウイルス”感は減らして、かわいい敵キャラっぽいシルエットにする
        r = min(self.w, self.h) * 0.45

        # --- ねねこの画像っぽい4種に描き分け ---
        st = VIRUS_STYLE.get(self.tier, VIRUS_STYLE["S"])
        body = st["body"]
        outline = st["outline"]
        cheek = st["cheek"]

        # ひるみ中は明るく点滅
        if getattr(self, "hurt_timer", 0.0) > 0:
            body = (min(255, body[0] + 45), min(255, body[1] + 45), min(255, body[2] + 45))

        # ふわふわ（上下） + ぷるぷる
        pulse = 1.0 + math.sin(GLOBAL_T * 2.2 + self.anim_phase) * 0.04
        bob = math.sin(GLOBAL_T * 1.3 + self.anim_phase) * self.float_amp

        px = cx - cam_x
        py = cy + bob

        br = int(r * 1.05)
        rr = int(br * sx * pulse)

        # トゲ（先に外側へ描く）
        spike_col = st.get("spike", (90, 110, 110))
        # ぷちはトゲ少なめ、ボスは多め
        spike_mul = {"S": 0.65, "M": 0.85, "L": 1.0, "B": 1.15}.get(self.tier, 1.0)
        spike_cnt = max(4, int(self.spike_count * spike_mul))
        spike_len = self.spike_len * ({"S": 0.55, "M": 0.85, "L": 1.0, "B": 1.10}.get(self.tier, 1.0))
        for i in range(spike_cnt):
            a = (math.tau * i / spike_cnt) + self.spike_phase + math.sin(GLOBAL_T * 1.1 + self.anim_phase) * 0.05
            x1 = px + math.cos(a) * (rr * 0.76)
            y1 = py + math.sin(a) * (rr * 0.76)
            x2 = px + math.cos(a) * (rr * 0.76 + spike_len)
            y2 = py + math.sin(a) * (rr * 0.76 + spike_len)
            pygame.draw.line(surf, spike_col, (x1, y1), (x2, y2), 3)
            pygame.draw.circle(surf, spike_col, (int(x2), int(y2)), 3)

        # ほのお（M）: 炎っぽい粒
        if self.tier == "M":
            f1 = st.get("flame", (255, 120, 40))
            f2 = st.get("flame2", (255, 210, 90))
            rng = random.Random(int((GLOBAL_T + self.anim_phase) * 10_000))
            for _ in range(7):
                aa = rng.random() * math.tau
                rad = rr * rng.uniform(0.85, 1.25)
                fx = int(px + math.cos(aa) * rad)
                fy = int(py + math.sin(aa) * rad)
                col = f1 if rng.random() < 0.6 else f2
                pygame.draw.circle(surf, col, (fx, fy), rng.randint(2, 4))

        # ばちばち（L）: スパーク（ジグザグ線 + 粒）
        if self.tier == "L":
            s1 = st.get("spark", (255, 240, 160))
            s2 = st.get("spark2", (160, 255, 235))
            rng = random.Random(int((GLOBAL_T * 1000) + self.anim_phase * 10000))
            for _ in range(3):
                aa = rng.random() * math.tau
                r0 = rr * 1.05
                x0 = px + math.cos(aa) * r0
                y0 = py + math.sin(aa) * r0
                # 小さいジグザグ
                pts = []
                steps = 4
                for k in range(steps + 1):
                    t = k / steps
                    off = (rng.random() - 0.5) * rr * 0.25
                    xx = x0 + math.cos(aa) * (rr * 0.35 * t) + math.cos(aa + math.pi / 2) * off
                    yy = y0 + math.sin(aa) * (rr * 0.35 * t) + math.sin(aa + math.pi / 2) * off
                    pts.append((xx, yy))
                pygame.draw.lines(surf, s1, False, pts, 2)
                pygame.draw.circle(surf, s2, (int(pts[-1][0]), int(pts[-1][1])), 3)

        # ボス（B）: 王冠
        if self.tier == "B":
            crown = st.get("crown", (255, 214, 70))
            crown2 = st.get("crown2", (255, 160, 60))
            top_y = py - rr * 1.05
            base_w = rr * 0.95
            base_h = rr * 0.35
            rect = pygame.Rect(int(px - base_w / 2), int(top_y - base_h), int(base_w), int(base_h))
            pygame.draw.rect(surf, crown, rect, border_radius=6)
            # 3つ山
            peaks = [(-0.35, -0.10), (0.0, -0.28), (0.35, -0.10)]
            for xo, yo in peaks:
                tri = [
                    (px + xo * base_w * 0.9 - 10, top_y - base_h),
                    (px + xo * base_w * 0.9 + 10, top_y - base_h),
                    (px + xo * base_w * 0.9, top_y - base_h - rr * 0.28),
                ]
                pygame.draw.polygon(surf, crown2, tri)
            pygame.draw.circle(surf, (255, 90, 120), (int(px), int(top_y - base_h - rr * 0.20)), 4)

        # 本体（丸）
        pygame.draw.circle(surf, outline, (int(px), int(py)), rr + 5)
        pygame.draw.circle(surf, body, (int(px), int(py)), rr)

        # 影/グラデっぽい面（画像寄せ）
        shade = st.get("shade")
        if shade:
            pygame.draw.circle(
                surf,
                lerp_col(shade, body, 0.35),
                (int(px + rr * 0.18), int(py + rr * 0.18)),
                int(rr * 0.78),
            )

        # 内側の模様（個体差）
        if self.style in ("sleepy", "wink"):
            spot = (255, 255, 255)
            pygame.draw.circle(surf, spot, (int(px - rr * 0.25), int(py + rr * 0.15)), max(4, int(rr * 0.18)))
        elif self.style == "grin":
            spot = (230, 255, 245)
            pygame.draw.ellipse(surf, spot, pygame.Rect(int(px - rr * 0.45), int(py - rr * 0.05), int(rr * 0.35), int(rr * 0.22)))

        # 顔（かわいめ）
        face_col = (25, 30, 40)
        ex_off = int(rr * 0.34)
        ey = int(py - rr * 0.12)
        eye_r = max(2, int(2.7 * self.size))

        # 目：瞬き中は線、winkは片目
        left_closed = (self.style == "wink")
        if self.blink_progress > 0:
            left_closed = True
            right_closed = True
        else:
            right_closed = False

        # 左目
        if left_closed:
            pygame.draw.line(surf, face_col, (int(px - ex_off - eye_r), ey), (int(px - ex_off + eye_r), ey), 2)
        else:
            if self.eye_style == "oval":
                pygame.draw.ellipse(surf, face_col, pygame.Rect(int(px - ex_off - 2), ey - 3, 4, 6))
            else:
                pygame.draw.circle(surf, face_col, (int(px - ex_off), ey), eye_r)

        # 右目
        if right_closed:
            pygame.draw.line(surf, face_col, (int(px + ex_off - eye_r), ey), (int(px + ex_off + eye_r), ey), 2)
        else:
            if self.eye_style == "oval":
                pygame.draw.ellipse(surf, face_col, pygame.Rect(int(px + ex_off - 2), ey - 3, 4, 6))
            else:
                pygame.draw.circle(surf, face_col, (int(px + ex_off), ey), eye_r)

        # 口（happy/sleepy/grin）
        mx = int(px)
        my = int(py + rr * 0.18)
        if self.style == "sleepy":
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 7, my, 14, 10), math.pi * 1.10, math.pi * 1.90, 2)
        elif self.style == "grin":
            pygame.draw.line(surf, face_col, (mx - 7, my + 2), (mx + 7, my + 2), 2)
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 8, my - 2, 16, 10), math.pi * 0.10, math.pi * 0.90, 2)
        else:
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 8, my - 2, 16, 10), math.pi * 0.10, math.pi * 0.90, 2)

        # ほっぺ（照れ：近いほど濃く）
        dist = getattr(self, "_player_dist", 9999.0)
        t = clamp(1.0 - (dist / 520.0), 0.0, 1.0) * 0.85
        blush = (
            int(cheek[0]),
            int(cheek[1] * (1.0 - 0.25 * t)),
            int(cheek[2] * (1.0 - 0.30 * t)),
        )
        b_r = max(2, int(2 * self.size))
        pygame.draw.circle(surf, blush, (int(px - rr * 0.58), int(py + rr * 0.05)), b_r)
        pygame.draw.circle(surf, blush, (int(px + rr * 0.58), int(py + rr * 0.05)), b_r)

        # 足は無し（ウイルスなので）

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
        # プレイヤーの見た目は別担当が作る想定なので、ここでは描かない
        return

# =========================================================
# Spawning by segment (画面が変わる=区画が変わる)
# =========================================================
def segment_index(x):
    return int(x // SEGMENT_W)

def spawn_for_segment(seg):
    # 区画ごとに敵を固定で出す（例）
    # ここを増やせば「画面が変わるごとに出現」になる
    # 画面が変わるごとに、S/M/Lの敵を出す
    spawns = {
        # 画像の4種が「最初から分かる」ように各区画へ配置
        0: [(520, "S"), (720, "M"), (880, "L")],
        1: [(SEGMENT_W + 520, "S"), (SEGMENT_W + 760, "M")],
        2: [(SEGMENT_W * 2 + 520, "L"), (SEGMENT_W * 2 + 760, "S"), (SEGMENT_W * 2 + 900, "M")],
        3: [(SEGMENT_W * 3 + 620, "L"), (SEGMENT_W * 3 + 820, "M")],
        # 最後の区画にボス
        4: [(SEGMENT_W * 4 + 760, "B")],
    }

    viruses = []
    for x, tier in spawns.get(seg, []):
        viruses.append(Virus(x, GROUND_Y, tier=tier))
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

    global GLOBAL_T
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1/20)
        GLOBAL_T += dt

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
            v.update(dt, projectiles, theme=theme, player=player)
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
