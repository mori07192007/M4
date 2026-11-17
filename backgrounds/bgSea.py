import pygame
import random
import math

# NOTE:
# This file can be executed directly (python backgrounds/bgSea.py).
# It is also launched from backgrounds/bgStart.py via runpy.run_path(...).

class UnderwaterBackground:
    def __init__(self, w, h, seed=1, fish_count=16, jelly_count=6):
        self.w = w
        self.h = h
        self.t = 0.0
        self.rng = random.Random(seed)

        # 浮遊粒子（プランクトン）
        self.particles = []
        for _ in range(140):
            x = self.rng.uniform(0, w)
            y = self.rng.uniform(0, h)
            r = self.rng.choice([1, 1, 1, 2])
            spx = self.rng.uniform(-10, -3)  # 左へ
            spy = self.rng.uniform(-3, 3)
            a = self.rng.uniform(18, 55)
            self.particles.append([x, y, r, spx, spy, a])

        # 魚（右→左、頭は左向き）
        self.fish = []
        for _ in range(fish_count):
            self.fish.append(self._new_fish(spawn_right=False))

        # クラゲ（漂う：やや遅い＋上下）
        self.jelly = []
        for _ in range(jelly_count):
            self.jelly.append(self._new_jelly(spawn_right=False))

        # 光（ゴッドレイ）
        self.light = pygame.Surface((w, h), pygame.SRCALPHA)

        # 地面は「動かさない」ので、描画用に固定の丘を作っておく
        self.sand_hills = []
        sand_y = int(h * 0.78)
        for i in range(6):
            x = self.rng.randrange(-80, w + 80)
            ww = self.rng.randrange(220, 320)
            hh = self.rng.randrange(40, 70)
            self.sand_hills.append((x, sand_y - 26, ww, hh))

        self.rocks = []
        for i in range(5):
            x = self.rng.randrange(40, w - 120)
            y = sand_y - self.rng.randrange(5, 20)
            ww = self.rng.randrange(70, 120)
            hh = self.rng.randrange(40, 70)
            self.rocks.append((x, y, ww, hh))

    def _new_fish(self, spawn_right=True):
        w, h = self.w, self.h
        depth = self.rng.uniform(0.35, 1.0)  # 遠近（見え方＆速度）
        scale = self.rng.uniform(0.55, 1.25) * (0.65 + 0.55 * depth)

        y = self.rng.uniform(h * 0.12, h * 0.70)
        x = w + self.rng.uniform(40, 260) if spawn_right else self.rng.uniform(0, w)

        speed = self.rng.uniform(55, 145) * (0.55 + 0.85 * depth)
        vx = -speed  # 左へ

        amp = self.rng.uniform(8, 26) * (0.6 + 0.8 * depth)
        freq = self.rng.uniform(1.2, 2.8)
        phase = self.rng.uniform(0, math.tau)

        palette = [
            ((220, 230, 235), (110, 170, 205)),
            ((235, 220, 190), (210, 150, 80)),
            ((205, 230, 210), (90, 170, 120)),
            ((230, 215, 235), (165, 120, 195)),
        ]
        body_col, fin_col = self.rng.choice(palette)

        return {
            "x": x,
            "y": y,
            "base_y": y,
            "vx": vx,
            "scale": scale,
            "amp": amp,
            "freq": freq,
            "phase": phase,
            "body": body_col,
            "fin": fin_col,
            "depth": depth,
        }

    def _new_jelly(self, spawn_right=True):
        w, h = self.w, self.h
        depth = self.rng.uniform(0.35, 1.0)
        scale = self.rng.uniform(0.7, 1.35) * (0.65 + 0.55 * depth)

        # クラゲは魚より少し上の層に置くと雰囲気が出る
        y = self.rng.uniform(h * 0.10, h * 0.55)
        x = w + self.rng.uniform(60, 340) if spawn_right else self.rng.uniform(0, w)

        vx = -self.rng.uniform(18, 45) * (0.6 + 0.9 * depth)  # ゆっくり左へ
        amp = self.rng.uniform(10, 28) * (0.7 + 0.7 * depth)
        freq = self.rng.uniform(0.8, 1.7)
        phase = self.rng.uniform(0, math.tau)

        # 半透明の色
        tint = self.rng.choice([
            (210, 245, 255),
            (225, 210, 255),
            (200, 255, 230),
        ])

        return {
            "x": x,
            "y": y,
            "base_y": y,
            "vx": vx,
            "scale": scale,
            "amp": amp,
            "freq": freq,
            "phase": phase,
            "depth": depth,
            "tint": tint,
        }

    def update(self, dt):
        self.t += dt

        # 粒子（地面固定でも、水中の流れは欲しいので粒子だけ流す）
        for p in self.particles:
            p[0] += p[3] * dt
            p[1] += p[4] * dt + math.sin((p[0] + self.t * 30) * 0.02) * 0.15
            if p[0] < -10:
                p[0] = self.w + self.rng.uniform(0, 40)
                p[1] = self.rng.uniform(0, self.h)
            if p[1] < -10:
                p[1] = self.h + 10
            if p[1] > self.h + 10:
                p[1] = -10

        # 魚
        for f in self.fish:
            f["x"] += f["vx"] * dt
            f["y"] = f["base_y"] + math.sin(self.t * f["freq"] + f["phase"]) * f["amp"]

        # 画面外→右端から
        for i, f in enumerate(self.fish):
            if f["x"] < -220:
                self.fish[i] = self._new_fish(spawn_right=True)

        # クラゲ
        for j in self.jelly:
            j["x"] += j["vx"] * dt
            # “脈動”っぽく上下（魚よりゆっくり）
            j["y"] = j["base_y"] + math.sin(self.t * j["freq"] + j["phase"]) * j["amp"]

        for i, j in enumerate(self.jelly):
            if j["x"] < -260:
                self.jelly[i] = self._new_jelly(spawn_right=True)

    # --- 描画 ---
    def _draw_water(self, screen):
        w, h = self.w, self.h
        top = (40, 150, 195)
        mid = (18, 95, 140)
        bot = (8, 40, 75)
        for y in range(h):
            t = y / max(1, h - 1)
            if t < 0.55:
                tt = t / 0.55
                c = (
                    int(top[0] * (1-tt) + mid[0] * tt),
                    int(top[1] * (1-tt) + mid[1] * tt),
                    int(top[2] * (1-tt) + mid[2] * tt),
                )
            else:
                tt = (t - 0.55) / 0.45
                c = (
                    int(mid[0] * (1-tt) + bot[0] * tt),
                    int(mid[1] * (1-tt) + bot[1] * tt),
                    int(mid[2] * (1-tt) + bot[2] * tt),
                )
            pygame.draw.line(screen, c, (0, y), (w, y))

    def _draw_god_rays(self, screen):
        w, h = self.w, self.h
        self.light.fill((0, 0, 0, 0))
        base_a = 26

        # 動かない地面でも、光は揺れると臨場感が出る
        for i in range(6):
            x = (i * 180 + 40) % w
            sway = math.sin(self.t * 0.55 + i) * 18
            top_w = 60
            bot_w = 190
            pts = [
                (x + sway, 0),
                (x + top_w + sway, 0),
                (x + bot_w + sway + 80, int(h * 0.75)),
                (x - 50 + sway, int(h * 0.75)),
            ]
            pygame.draw.polygon(self.light, (200, 245, 255, base_a), pts)

        screen.blit(self.light, (0, 0))

    def _draw_particles(self, screen):
        for x, y, r, spx, spy, a in self.particles:
            pygame.draw.circle(screen, (225, 245, 250, int(a)), (int(x), int(y)), r)

    def _draw_ground_static(self, screen):
        w, h = self.w, self.h
        sand_y = int(h * 0.78)

        # 砂地（固定）
        pygame.draw.rect(screen, (150, 170, 150), (0, sand_y, w, h - sand_y))
        pygame.draw.rect(screen, (135, 160, 140), (0, sand_y, w, 10))

        # 丘（固定）
        for x, y, ww, hh in self.sand_hills:
            pygame.draw.ellipse(screen, (135, 160, 140), (x, y, ww, hh))

        # 岩（固定）
        for x, y, ww, hh in self.rocks:
            pygame.draw.ellipse(screen, (70, 90, 95), (x, y, ww, hh))
            pygame.draw.ellipse(screen, (55, 75, 80), (x + ww * 0.22, y + hh * 0.35, ww * 0.55, hh * 0.42))

    def _draw_one_fish_left(self, screen, f):
        """左向き（頭が左）に見える魚を描く"""
        x = f["x"]
        y = f["y"]
        s = f["scale"]
        depth = f["depth"]

        body = f["body"]
        fin = f["fin"]

        alpha = int(90 + 165 * depth)

        surf = pygame.Surface((220, 140), pygame.SRCALPHA)

        # 左向きにするため、頭（口・目）を左側へ配置する
        bx, by = 120, 70
        bw, bh = int(95 * s), int(40 * s)

        # 体
        pygame.draw.ellipse(surf, (*body, alpha), (bx - bw//2, by - bh//2, bw, bh))

        # 尾びれ（右側に付ける＝頭が左）
        tail_w = int(28 * s)
        tail_h = int(22 * s)
        tail = [
            (bx + bw//2, by),
            (bx + bw//2 + tail_w, by - tail_h),
            (bx + bw//2 + tail_w, by + tail_h),
        ]
        pygame.draw.polygon(surf, (*fin, alpha), tail)

        # 背びれ
        dorsal = [
            (bx + 10, by - bh//2 + 2),
            (bx - 10, by - bh//2 - int(14*s)),
            (bx - 26, by - bh//2 + 6),
        ]
        pygame.draw.polygon(surf, (*fin, int(alpha * 0.9)), dorsal)

        # 目（頭＝左側）
        eye_x = bx - bw // 3
        pygame.draw.circle(surf, (255, 255, 255, alpha), (eye_x, by - int(6*s)), int(5*s))
        pygame.draw.circle(surf, (15, 15, 20, alpha), (eye_x - 1, by - int(6*s)), int(2*s))

        # 口（左端）
        pygame.draw.aaline(
            surf, (20, 20, 25, int(alpha * 0.75)),
            (bx - bw//2 + int(2*s), by + int(3*s)),
            (bx - bw//2 + int(12*s), by)
        )

        # ハイライト
        pygame.draw.ellipse(
            surf, (255, 255, 255, int(alpha * 0.18)),
            (bx - int(30*s), by - int(18*s), int(40*s), int(16*s))
        )

        screen.blit(surf, (int(x - 110), int(y - 70)))

    def _draw_one_jelly(self, screen, j):
        x = j["x"]
        y = j["y"]
        s = j["scale"]
        depth = j["depth"]
        tint = j["tint"]

        alpha = int(65 + 160 * depth)
        surf = pygame.Surface((240, 240), pygame.SRCALPHA)

        cx, cy = 120, 115
        bell_w = int(70 * s)
        bell_h = int(55 * s)

        # 傘（ベル）
        pygame.draw.ellipse(surf, (*tint, alpha), (cx - bell_w, cy - bell_h, bell_w * 2, bell_h * 2))
        # 内側の薄い影
        pygame.draw.ellipse(surf, (255, 255, 255, int(alpha * 0.20)),
                            (cx - int(bell_w*0.65), cy - int(bell_h*0.55), int(bell_w*1.3), int(bell_h*1.1)))

        # フリル（下側の波）
        frill_y = cy + int(bell_h * 0.55)
        for k in range(8):
            px = cx - bell_w + k * (bell_w * 2) / 7
            rr = int(6 * s)
            pygame.draw.circle(surf, (*tint, int(alpha * 0.85)), (int(px), frill_y), rr)

        # 触手（ゆらゆら）
        tent_col = (*tint, int(alpha * 0.7))
        tent_count = 7
        length = int(55 * s)
        wob = math.sin(self.t * 2.0 + j["phase"]) * (6 + 6 * depth)

        for k in range(tent_count):
            tx = cx - int(bell_w * 0.65) + k * int((bell_w * 1.3) / (tent_count - 1))
            points = []
            segs = 6
            for i in range(segs + 1):
                tt = i / segs
                px = tx + wob * (tt ** 1.4) + math.sin(self.t * 2.8 + j["phase"] + tt * 4.0 + k) * 2.5
                py = frill_y + tt * length
                points.append((px, py))
            pygame.draw.lines(surf, tent_col, False, points, max(1, int(2 * s)))

        # ほんのり発光
        pygame.draw.ellipse(surf, (255, 255, 255, int(alpha * 0.12)),
                            (cx - int(bell_w*1.25), cy - int(bell_h*1.25), int(bell_w*2.5), int(bell_h*2.5)))

        screen.blit(surf, (int(x - 120), int(y - 120)))

    def draw(self, screen):
        self._draw_water(screen)
        self._draw_god_rays(screen)
        self._draw_particles(screen)

        # 遠い→近いの順で描くと自然
        for j in sorted(self.jelly, key=lambda d: d["depth"]):
            self._draw_one_jelly(screen, j)

        for f in sorted(self.fish, key=lambda d: d["depth"]):
            self._draw_one_fish_left(screen, f)

        # 地面は固定で最後に描く（魚を“奥”にしたいなら先に描く方が良い）
        self._draw_ground_static(screen)


# 動作確認
if __name__ == "__main__":
    pygame.init()
    W, H = 960, 540
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Sea")
    clock = pygame.time.Clock()
    bg = UnderwaterBackground(W, H, seed=9, fish_count=18, jelly_count=6)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        bg.update(dt)
        bg.draw(screen)
        pygame.display.flip()

    pygame.quit()
