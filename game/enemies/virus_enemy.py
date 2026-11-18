import math
import random
import pygame


class GermProjectile:
    """シンプルな菌弾（丸だけ）"""

    def __init__(self, x, y, vx, vy, color=(190, 255, 235)):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.r = 6
        self.life = 1.7
        self.gravity = 120.0
        self.color = color

    def update(self, dt, ground_y):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.y + self.r > ground_y:
            self.y = ground_y - self.r
            self.vx *= 0.45
            self.vy *= -0.20

    def draw(self, surf, cam_x):
        cx = int(self.x - cam_x)
        cy = int(self.y)
        pygame.draw.circle(surf, self.color, (cx, cy), self.r)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 2, cy - 2), max(1, self.r // 3))


class FlameProjectile:
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.r = 8
        self.life = 1.1
        self.gravity = 900.0

    def update(self, dt, ground_y):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surf, cam_x):
        pygame.draw.circle(surf, (255, 138, 61), (int(self.x - cam_x), int(self.y)), self.r)


class VirusEnemy:
    """かわいいウイルス系（オリジナル）: 丸 + 控えめトゲ + 顔。

    tier: "S" | "M" | "L" でサイズ/HP/散布量が変わる。
    """

    def __init__(self, x, y_ground, *, tier="S"):
        self.tier = tier
        tier_size = {"S": 1.0, "M": 1.55, "L": 2.25}.get(tier, 1.0)
        self.size = float(tier_size)
        base = 46.0
        self.w = base * self.size
        self.h = base * self.size

        self.x = float(x)
        self.y = float(y_ground - self.h)

        self.hp = {"S": 1, "M": 2, "L": 3}.get(tier, 1)
        self.speed = (78.0 / math.sqrt(self.size))
        self.dir = -1 if random.random() < 0.5 else 1

        self.dead = False
        self.death_timer = 0.0
        self.remove = False

        self.anim_phase = random.uniform(0.0, math.tau)
        self.blink_t = random.uniform(0.4, 2.0)
        self.blink_len = 0.10
        self.blink_progress = 0.0

        self.style = random.choice(["happy", "sleepy", "grin", "wink"])
        self.eye_style = random.choice(["dot", "oval"])
        self.float_amp = random.uniform(2.0, 5.0) * (0.7 + 0.4 * self.size)

        # 画像の雰囲気に寄せる：棒トゲではなく「粒トゲ（ノブ）」
        self.spike_count = random.randint(6, 9)
        self.spike_len = random.uniform(10.0, 16.0) * (0.8 + 0.35 * self.size)
        self.spike_phase = random.uniform(0.0, math.tau)
        self.knob_r = random.uniform(3.0, 4.2) * (0.85 + 0.35 * self.size)

        # 体のハイライト（1体ごとに位置を少し変える）
        self.hl_phase = random.uniform(0.0, math.tau)

        self.shot_cd = random.uniform(0.9, 1.8)
        self.shot_interval = {"S": 1.85, "M": 1.55, "L": 1.25}.get(self.tier, 1.6)

        self.patrol_left = self.x - 140
        self.patrol_right = self.x + 140

        self.hurt_timer = 0.0
        self._player_dist = 9999.0

    def stomped(self):
        if self.dead:
            return
        self.hp -= 1
        if self.hp <= 0:
            self.dead = True
            self.death_timer = 0.18
        else:
            self.hurt_timer = 0.12

    def explode(self, projectiles, *, theme_palette=None):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        base_bullets = 4
        tier_bonus = {"S": 0, "M": 2, "L": 5}.get(self.tier, 0)
        count = max(2, round(base_bullets * self.size) + tier_bonus)
        spread = (math.pi * 0.70) + (self.size * 0.25)
        center = -math.pi / 2

        germ_col = (190, 255, 235)
        if theme_palette:
            germ_col = next(iter(theme_palette.values()))

        sp = 235 * (0.85 + 0.08 * self.size)
        for i in range(count):
            t = 0.5 if count == 1 else i / (count - 1)
            a = center - spread / 2 + spread * t + (random.random() - 0.5) * 0.22
            projectiles.append(GermProjectile(cx, cy, math.cos(a) * sp, math.sin(a) * sp, color=germ_col))

        flames = max(1, round(1.2 * self.size))
        for _ in range(flames):
            a = center + (random.random() - 0.5) * 0.8
            projectiles.append(FlameProjectile(cx, self.y + 10, math.cos(a) * 190, math.sin(a) * 320))

    def shoot_at_player(self, projectiles, *, theme_palette=None, player=None):
        if player is None:
            return

        cx = self.x + self.w / 2
        cy = self.y + self.h * 0.35
        px = player.x + player.w / 2
        py = player.y + player.h / 2

        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return
        nx = dx / dist
        ny = dy / dist

        flame_chance = {"S": 0.12, "M": 0.22, "L": 0.40}.get(self.tier, 0.2)
        if random.random() < flame_chance:
            sp = 260.0
            projectiles.append(FlameProjectile(cx, cy, nx * sp, ny * sp - 120.0))
            return

        germ_col = (190, 255, 235)
        if theme_palette:
            germ_col = next(iter(theme_palette.values()))

        sp = {"S": 255.0, "M": 275.0, "L": 300.0}.get(self.tier, 270.0)
        ang = math.atan2(ny, nx) + random.uniform(-0.10, 0.10)
        projectiles.append(GermProjectile(cx, cy, math.cos(ang) * sp, math.sin(ang) * sp, color=germ_col))

    def update(self, dt, projectiles, *, global_t=0.0, theme_palette=None, player=None, ground_y=460):
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        if self.dead:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.explode(projectiles, theme_palette=theme_palette)
                self.remove = True
            return

        # blink
        if self.blink_progress > 0:
            self.blink_progress = max(0.0, self.blink_progress - dt)
        else:
            self.blink_t -= dt
            if self.blink_t <= 0:
                self.blink_progress = self.blink_len
                self.blink_t = random.uniform(1.2, 3.2)

        # shoot
        if player is not None:
            self._player_dist = math.hypot(
                (player.x + player.w / 2) - (self.x + self.w / 2),
                (player.y + player.h / 2) - (self.y + self.h / 2),
            )
            self.shot_cd -= dt
            if self.shot_cd <= 0:
                self.shoot_at_player(projectiles, theme_palette=theme_palette, player=player)
                self.shot_cd = self.shot_interval + random.uniform(-0.18, 0.22)

        if self.hurt_timer <= 0:
            self.x += self.speed * self.dir * dt

        if self.x < self.patrol_left:
            self.x = self.patrol_left
            self.dir = 1
        if self.x + self.w > self.patrol_right:
            self.x = self.patrol_right - self.w
            self.dir = -1

        self.y = ground_y - self.h

    def draw(self, surf, cam_x, *, global_t=0.0):
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        sx, sy = 1.0, 1.0
        if self.dead:
            p = max(0.0, min(1.0, 1 - self.death_timer / 0.18))
            sx = 1 + p * 0.25
            sy = 1 - p * 0.55

        pulse = 1.0 + math.sin(global_t * 2.2 + self.anim_phase) * 0.04
        bob = math.sin(global_t * 1.3 + self.anim_phase) * self.float_amp
        px = (cx - cam_x)
        py = (cy + bob)

        body = {"S": (160, 245, 200), "M": (255, 230, 150), "L": (255, 175, 175)}.get(self.tier, (160, 245, 200))
        outline = (40, 45, 55)
        cheek = (255, 135, 170)
        if self.hurt_timer > 0:
            body = (min(255, body[0] + 45), min(255, body[1] + 45), min(255, body[2] + 45))

        r = min(self.w, self.h) * 0.45
        br = int(r * 1.05)
        rr = int(br * sx * pulse)

        # --- bubble shield (画像上部の泡っぽい感じ) ---
        # 半透明円 + ハイライト
        shield_r = int(rr * 1.15)
        shield = pygame.Surface((shield_r * 2 + 6, shield_r * 2 + 6), pygame.SRCALPHA)
        scx = shield.get_width() // 2
        scy = shield.get_height() // 2
        pygame.draw.circle(shield, (210, 230, 255, 45), (scx, scy), shield_r)
        pygame.draw.circle(shield, (230, 245, 255, 80), (scx - int(shield_r * 0.35), scy - int(shield_r * 0.35)), max(2, int(shield_r * 0.18)))
        pygame.draw.circle(shield, (230, 245, 255, 55), (scx - int(shield_r * 0.15), scy - int(shield_r * 0.48)), max(2, int(shield_r * 0.10)))
        surf.blit(shield, (int(px - scx), int(py - scy)))

        # --- knob spikes (粒トゲ) ---
        spike_col = (85, 95, 100)
        stem_col = (110, 130, 130)
        for i in range(self.spike_count):
            a = (math.tau * i / self.spike_count) + self.spike_phase + math.sin(global_t * 1.1 + self.anim_phase) * 0.05
            # 根本（体側）
            x1 = px + math.cos(a) * (rr * 0.78)
            y1 = py + math.sin(a) * (rr * 0.78)
            # 先端
            x2 = px + math.cos(a) * (rr * 0.78 + self.spike_len)
            y2 = py + math.sin(a) * (rr * 0.78 + self.spike_len)

            pygame.draw.line(surf, stem_col, (x1, y1), (x2, y2), 4)
            pygame.draw.circle(surf, spike_col, (int(x2), int(y2)), int(self.knob_r) + 2)
            pygame.draw.circle(surf, (220, 235, 235), (int(x2 - 1), int(y2 - 1)), max(1, int(self.knob_r // 2)))

        # body (丸)
        pygame.draw.circle(surf, outline, (int(px), int(py)), rr + 5)
        pygame.draw.circle(surf, body, (int(px), int(py)), rr)

        # 本体ハイライト（ツヤ）
        hx = int(px - rr * (0.35 + 0.06 * math.sin(self.hl_phase)))
        hy = int(py - rr * (0.30 + 0.06 * math.cos(self.hl_phase)))
        pygame.draw.circle(surf, (255, 255, 255), (hx, hy), max(3, int(rr * 0.18)))
        pygame.draw.circle(surf, (255, 255, 255), (hx + 2, hy + 2), max(2, int(rr * 0.10)))

        # inner pattern（画像っぽく：小さい粒を数個）
        pat_col = (245, 255, 250)
        rng = random.Random(int(self.anim_phase * 10000))
        for _ in range(3):
            aa = rng.random() * math.tau
            rad = rng.uniform(0.10, 0.45) * rr
            px2 = int(px + math.cos(aa) * rad)
            py2 = int(py + math.sin(aa) * rad)
            pygame.draw.circle(surf, pat_col, (px2, py2), max(3, int(rr * 0.08)))

        # face
        face_col = (25, 30, 40)
        ex_off = int(rr * 0.34)
        ey = int(py - rr * 0.12)
        eye_r = max(2, int(2.7 * self.size))

        left_closed = (self.style == "wink")
        if self.blink_progress > 0:
            left_closed = True
            right_closed = True
        else:
            right_closed = False

        # left eye
        if left_closed:
            pygame.draw.line(surf, face_col, (int(px - ex_off - eye_r), ey), (int(px - ex_off + eye_r), ey), 2)
        else:
            if self.eye_style == "oval":
                pygame.draw.ellipse(surf, face_col, pygame.Rect(int(px - ex_off - 2), ey - 3, 4, 6))
            else:
                pygame.draw.circle(surf, face_col, (int(px - ex_off), ey), eye_r)

        # right eye
        if right_closed:
            pygame.draw.line(surf, face_col, (int(px + ex_off - eye_r), ey), (int(px + ex_off + eye_r), ey), 2)
        else:
            if self.eye_style == "oval":
                pygame.draw.ellipse(surf, face_col, pygame.Rect(int(px + ex_off - 2), ey - 3, 4, 6))
            else:
                pygame.draw.circle(surf, face_col, (int(px + ex_off), ey), eye_r)

        mx = int(px)
        my = int(py + rr * 0.18)
        if self.style == "sleepy":
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 7, my, 14, 10), math.pi * 1.10, math.pi * 1.90, 2)
        elif self.style == "grin":
            pygame.draw.line(surf, face_col, (mx - 7, my + 2), (mx + 7, my + 2), 2)
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 8, my - 2, 16, 10), math.pi * 0.10, math.pi * 0.90, 2)
        else:
            pygame.draw.arc(surf, face_col, pygame.Rect(mx - 8, my - 2, 16, 10), math.pi * 0.10, math.pi * 0.90, 2)

        # blush（薄めで固定寄り：キモさ回避）
        t = max(0.0, min(1.0, 1.0 - (getattr(self, "_player_dist", 9999.0) / 520.0)))
        t = t * 0.45
        blush = (int(cheek[0]), int(cheek[1] * (1.0 - 0.20 * t)), int(cheek[2] * (1.0 - 0.25 * t)))
        b_r = max(2, int(1.6 * self.size))
        pygame.draw.circle(surf, blush, (int(px - rr * 0.55), int(py + rr * 0.08)), b_r)
        pygame.draw.circle(surf, blush, (int(px + rr * 0.55), int(py + rr * 0.08)), b_r)


def spawn_for_segment(seg, *, ground_y):
    spawns = {
        0: [(520, "S"), (780, "M")],
        1: [(960 + 600, "L")],
        2: [(960 * 2 + 520, "S"), (960 * 2 + 700, "S"), (960 * 2 + 860, "L")],
        3: [(960 * 3 + 720, "M"), (960 * 3 + 860, "M")],
        4: [(960 * 4 + 760, "L")],
    }
    enemies = []
    for x, tier in spawns.get(seg, []):
        enemies.append(VirusEnemy(x, ground_y, tier=tier))
    return enemies
