import math
import random
import pygame

WIDTH, HEIGHT = 960, 540
FPS = 60


def clamp(x, a, b):
    return a if x < a else b if x > b else x


class StarfieldLayer:
    """星のレイヤー（奥行きごとに速度・サイズが違う）"""

    def __init__(self, count, speed, size_range, color, seed=None):
        self.rng = random.Random(seed)
        self.speed = float(speed)
        self.color = color
        self.size_min, self.size_max = size_range
        self.stars = []
        for _ in range(count):
            x = self.rng.randrange(0, WIDTH)
            y = self.rng.randrange(0, HEIGHT)
            r = self.rng.randint(self.size_min, self.size_max)
            self.stars.append([x, y, r])

    def update(self, dt, *, scroll_dir="down"):
        """scroll_dir: 'down' or 'left'"""
        if scroll_dir == "left":
            vx = -self.speed * dt
            for s in self.stars:
                s[0] += vx
                if s[0] < 0:
                    s[0] = WIDTH
                    s[1] = random.randrange(0, HEIGHT)
                    s[2] = random.randint(self.size_min, self.size_max)
        else:
            vy = self.speed * dt
            for s in self.stars:
                s[1] += vy
                if s[1] >= HEIGHT:
                    s[0] = random.randrange(0, WIDTH)
                    s[1] = 0
                    s[2] = random.randint(self.size_min, self.size_max)

    def draw(self, surf):
        for x, y, r in self.stars:
            pygame.draw.circle(surf, self.color, (int(x), int(y)), r)


class NebulaField:
    """疑似的な星雲（手続きノイズを軽量にそれっぽく見せる）"""

    def __init__(self, w, h, seed=1234):
        self.w = w
        self.h = h
        self.seed = seed
        self.rng = random.Random(seed)
        self.base = pygame.Surface((w, h), pygame.SRCALPHA)
        self._generate()

        self.offset = 0.0

    def _value_noise(self, x, y):
        def hash2(ix, iy):
            n = ix * 374761393 + iy * 668265263 + self.seed * 362437
            n = (n ^ (n >> 13)) * 1274126177
            n = n ^ (n >> 16)
            return (n & 0xFFFFFFFF) / 0xFFFFFFFF

        ix = int(math.floor(x))
        iy = int(math.floor(y))
        fx = x - ix
        fy = y - iy

        v00 = hash2(ix, iy)
        v10 = hash2(ix + 1, iy)
        v01 = hash2(ix, iy + 1)
        v11 = hash2(ix + 1, iy + 1)

        sx = fx * fx * (3 - 2 * fx)
        sy = fy * fy * (3 - 2 * fy)

        a = v00 * (1 - sx) + v10 * sx
        b = v01 * (1 - sx) + v11 * sx
        return a * (1 - sy) + b * sy

    def _fbm(self, x, y, octaves=4):
        value = 0.0
        amp = 1.0
        freq = 1.0
        norm = 0.0
        for _ in range(octaves):
            value += amp * self._value_noise(x * freq, y * freq)
            norm += amp
            amp *= 0.5
            freq *= 2.0
        return value / norm

    def _generate(self):
        self.base.fill((0, 0, 0, 0))

        low_w, low_h = self.w // 4, self.h // 4
        low = pygame.Surface((low_w, low_h), pygame.SRCALPHA)

        for y in range(low_h):
            for x in range(low_w):
                nx = x / low_w
                ny = y / low_h

                v = self._fbm(nx * 3.0, ny * 3.0, octaves=5)

                cx = nx - 0.5
                cy = ny - 0.5
                radial = math.exp(-(cx * cx + cy * cy) * 2.2)

                d = clamp((v * 0.9 + radial * 0.6) - 0.55, 0.0, 1.0)

                r = int(30 + 110 * (d**1.6))
                g = int(20 + 70 * (d**1.4))
                b = int(60 + 180 * (d**1.2))
                a = int(255 * (d**1.15) * 0.55)

                low.set_at((x, y), (r, g, b, a))

        scaled = pygame.transform.smoothscale(low, (self.w, self.h))
        self.base.blit(scaled, (0, 0))

    def update(self, dt, *, scroll_dir="down"):
        # 背景の流れる向き（ゲームが右→左スクロールなら left が自然）
        if scroll_dir == "left":
            self.offset = (self.offset + 18.0 * dt) % self.w
        else:
            self.offset = (self.offset + 18.0 * dt) % self.h

    def draw(self, surf, *, scroll_dir="down"):
        if scroll_dir == "left":
            x = int(self.offset)
            surf.blit(self.base, (-x, 0))
            surf.blit(self.base, (self.w - x, 0))
        else:
            y = int(self.offset)
            surf.blit(self.base, (0, -y))
            surf.blit(self.base, (0, self.h - y))


class DriftingBody:
    """控えめに流れる天体（流星/小惑星っぽい）"""

    def __init__(self, w, h, rng: random.Random):
        self.w, self.h = w, h
        self.rng = rng
        self.active = False

        # パフォーマンス＆目立ちすぎ防止のため、生成済みSurfaceを使い回す
        self.sprite = None
        self.trail = None

        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0.0
        self.max_life = 0.0
        self.alpha = 0

    def _make_sprite(self, radius, color_rgb, alpha):
        size = radius * 4 + 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        cy = size // 2
        # 中心が明るい小天体（ぼかし円を重ねる）
        for i in range(radius, 0, -1):
            a = int(alpha * (i / radius) ** 2)
            pygame.draw.circle(s, (*color_rgb, a), (cx, cy), i)
        return s

    def _make_trail(self, length, thickness, color_rgb, alpha):
        # 右→左に流れる前提で、右側に薄い尾を作る
        w = max(8, int(length))
        h = max(2, int(thickness))
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            t = x / (w - 1) if w > 1 else 1.0
            a = int(alpha * (1.0 - t) ** 2)
            pygame.draw.line(s, (*color_rgb, a), (x, 0), (x, h - 1))
        return s

    def spawn(self):
        # 目立ちすぎない：小さめ、薄め、速度はそこそこ
        radius = self.rng.randint(3, 5)
        base_alpha = self.rng.randint(130, 175)

        # ほんの少し青白い
        color = (
            self.rng.randint(200, 235),
            self.rng.randint(210, 245),
            self.rng.randint(230, 255),
        )

        self.sprite = self._make_sprite(radius, color, base_alpha)
        self.trail = self._make_trail(
            length=self.rng.uniform(80, 130),
            thickness=self.rng.uniform(2, 4),
            color_rgb=color,
            alpha=int(base_alpha * 0.90),
        )

        # 右端の外から出て左へ。上下位置は上寄り〜中寄りが自然で邪魔になりにくい
        self.x = self.w + self.rng.uniform(10, 180)
        self.y = self.rng.uniform(10, self.h * 0.60)

        # 右→左。少しだけ斜め下/上
        self.vx = -self.rng.uniform(380, 620)
        self.vy = self.rng.uniform(-40, 60)

        self.life = 0.0
        self.max_life = self.rng.uniform(0.8, 1.4)
        self.active = True

    def update(self, dt):
        if not self.active:
            return

        self.life += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # フェードイン→維持→フェードアウト
        t = self.life / self.max_life
        if t < 0.15:
            k = t / 0.15
        elif t > 0.80:
            k = clamp((1.0 - t) / 0.20, 0.0, 1.0)
        else:
            k = 1.0

        self.alpha = int(255 * k)

        if self.life >= self.max_life or self.x < -200 or self.y < -80 or self.y > self.h + 80:
            self.active = False

    def draw(self, surf):
        if not self.active:
            return

        # trail
        if self.trail is not None:
            trail = self.trail.copy()
            trail.set_alpha(int(self.alpha * 0.70))
            surf.blit(trail, (int(self.x), int(self.y)))

        # body
        if self.sprite is not None:
            spr = self.sprite.copy()
            spr.set_alpha(self.alpha)
            surf.blit(spr, (int(self.x) - spr.get_width() // 2, int(self.y) - spr.get_height() // 2))


class Background:
    def __init__(self, w, h, *, scroll_dir="left"):
        self.w, self.h = w, h
        self.scroll_dir = scroll_dir

        self.nebula = NebulaField(w, h, seed=2026)

        # 奥ほど遅い（横スクロールに変更するときは“速度＝左方向の速度”として扱う）
        self.stars_far = StarfieldLayer(count=140, speed=18, size_range=(1, 1), color=(160, 170, 190), seed=1)
        self.stars_mid = StarfieldLayer(count=90, speed=36, size_range=(1, 2), color=(190, 200, 220), seed=2)
        self.stars_near = StarfieldLayer(count=55, speed=62, size_range=(2, 3), color=(230, 235, 255), seed=3)

        # 画面上にうっすら“光学ノイズ”と“スキャンライン”を入れるためのオーバーレイ
        self.overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        self.scan_phase = 0.0

        # たまに流れる天体
        self.rng = random.Random(777)
        self.bodies = [DriftingBody(w, h, self.rng) for _ in range(3)]
        self.spawn_timer = 0.0
        self.spawn_interval = self.rng.uniform(2.8, 6.5)  # 「たまに」

    def update(self, dt):
        self.nebula.update(dt, scroll_dir=self.scroll_dir)
        self.stars_far.update(dt, scroll_dir=self.scroll_dir)
        self.stars_mid.update(dt, scroll_dir=self.scroll_dir)
        self.stars_near.update(dt, scroll_dir=self.scroll_dir)
        self.scan_phase += dt * 2.3

        for b in self.bodies:
            b.update(dt)

        # 一度にたくさん出さない（邪魔にならないように最大1体だけ稼働させがちにする）
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn_interval = self.rng.uniform(2.8, 7.2)

            active_count = sum(1 for b in self.bodies if b.active)
            if active_count == 0 and self.rng.random() < 0.85:
                # 空いてる1体をspawn
                for b in self.bodies:
                    if not b.active:
                        b.spawn()
                        break

    def _build_overlay(self):
        self.overlay.fill((0, 0, 0, 0))

        # スキャンライン（うっすら横線）
        for y in range(0, self.h, 3):
            a = 10
            pygame.draw.line(self.overlay, (0, 0, 0, a), (0, y), (self.w, y))

        # ビネット（端を暗く）
        vignette = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(0, 10):
            alpha = int(18 * (i / 10))
            rect = pygame.Rect(-i * 24, -i * 18, self.w + i * 48, self.h + i * 36)
            pygame.draw.ellipse(vignette, (0, 0, 0, alpha), rect, width=18)

        self.overlay.blit(vignette, (0, 0))

        flicker = int(6 + 6 * (0.5 + 0.5 * math.sin(self.scan_phase)))
        pygame.draw.rect(self.overlay, (255, 255, 255, flicker), (0, 0, self.w, self.h), width=0)

    def draw(self, surf):
        # 背景の黒
        surf.fill((2, 4, 10))

        # 星雲
        self.nebula.draw(surf, scroll_dir=self.scroll_dir)

        # 星（パララックス）
        self.stars_far.draw(surf)
        self.stars_mid.draw(surf)
        self.stars_near.draw(surf)

        # たまに流れる天体（星より手前、UIより奥に）
        for b in self.bodies:
            b.draw(surf)

        # オーバーレイ
        self._build_overlay()
        surf.blit(self.overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Shooter Background Demo")
    clock = pygame.time.Clock()

    # 敵が右→左なら背景も左スクロールが自然
    bg = Background(WIDTH, HEIGHT, scroll_dir="left")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        bg.update(dt)
        bg.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
