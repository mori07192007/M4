import pygame
import random
import math

class CampusBackground:
    def __init__(self, w, h, seed=1):
        self.w = w
        self.h = h
        self.offset = 0.0
        self.rng = random.Random(seed)

        # 鳥（遠景の動く点）
        self.birds = []
        for _ in range(8):
            x = self.rng.randrange(0, w)
            y = self.rng.randrange(30, int(h * 0.28))
            sp = self.rng.uniform(12, 28)
            self.birds.append([x, y, sp])

    def update(self, dt, speed=70.0):
        """speed: 背景のベーススクロール(px/s)"""
        self.offset = (self.offset + speed * dt) % self.w

        # 鳥は逆方向に少し飛ぶ（遠景のアクセント）
        for b in self.birds:
            b[0] = (b[0] - b[2] * dt) % self.w
            b[1] += math.sin(b[0] * 0.02) * 0.12

    def _draw_sky(self, screen):
        w, h = self.w, self.h
        # 空の簡易グラデ（水平線に向けて薄く）
        top = (120, 185, 255)
        mid = (170, 220, 255)
        for y in range(0, int(h * 0.55)):
            t = y / (h * 0.55)
            c = (
                int(top[0] * (1 - t) + mid[0] * t),
                int(top[1] * (1 - t) + mid[1] * t),
                int(top[2] * (1 - t) + mid[2] * t),
            )
            pygame.draw.line(screen, c, (0, y), (w, y))

    def _draw_clouds(self, screen):
        w, h = self.w, self.h
        cloud_col = (245, 250, 255)
        # 遠景：ゆっくり流す
        for i in range(6):
            base_x = i * 220 + 40
            x = base_x - int(self.offset * 0.18)
            x %= w
            y = 45 + (i % 3) * 30
            pygame.draw.ellipse(screen, cloud_col, (x, y, 120, 45))
            pygame.draw.ellipse(screen, cloud_col, (x + 35, y - 18, 90, 40))
            pygame.draw.ellipse(screen, cloud_col, (x + 65, y + 5, 95, 38))

    def _draw_far_buildings(self, screen):
        w, h = self.w, self.h
        horizon = int(h * 0.55)
        col = (115, 140, 165)

        # シルエットをタイル状に（ループ）
        for k in range(-1, 4):
            x0 = k * 360 - int(self.offset * 0.12)
            # 低い棟
            pygame.draw.rect(screen, col, (x0 + 20, horizon - 90, 180, 90))
            # 高い棟
            pygame.draw.rect(screen, col, (x0 + 220, horizon - 140, 120, 140))
            # ちょっと塔
            pygame.draw.rect(screen, col, (x0 + 280, horizon - 190, 40, 190))

    def _draw_main_building(self, screen):
        w, h = self.w, self.h
        ground = int(h * 0.65)

        bcol = (215, 205, 190)   # 校舎の壁
        frame = (160, 150, 135)
        win = (90, 120, 150)

        # 中景：そこそこ流す
        base_x = int(w * 0.08) - int(self.offset * 0.35)
        x = base_x % w
        bw = int(w * 0.62)
        bh = int(h * 0.26)
        y = ground - bh - 35

        # 画面跨ぎ対策：2回描く
        for dx in (0, -w):
            rect = pygame.Rect(x + dx, y, bw, bh)
            pygame.draw.rect(screen, bcol, rect, border_radius=10)
            pygame.draw.rect(screen, frame, rect, 5, border_radius=10)

            # 窓を規則正しく
            cols = 10
            rows = 3
            pad_x = 22
            pad_y = 18
            gap_x = (bw - pad_x * 2) // cols
            gap_y = (bh - pad_y * 2) // rows
            for r in range(rows):
                for c in range(cols):
                    wx = rect.x + pad_x + c * gap_x + 6
                    wy = rect.y + pad_y + r * gap_y + 6
                    ww = int(gap_x * 0.6)
                    wh = int(gap_y * 0.55)
                    pygame.draw.rect(screen, win, (wx, wy, ww, wh), border_radius=3)
                    pygame.draw.rect(screen, (240, 235, 225), (wx, wy, ww, wh), 2, border_radius=3)

            # 正面入口（大学っぽい“門”）
            gate = pygame.Rect(rect.x + int(bw*0.44), rect.y + int(bh*0.55), int(bw*0.12), int(bh*0.40))
            pygame.draw.rect(screen, (190, 180, 165), gate, border_radius=6)
            pygame.draw.rect(screen, frame, gate, 3, border_radius=6)

            # 看板（UNIV）
            sign = pygame.Rect(rect.x + int(bw*0.40), rect.y + 12, int(bw*0.20), 26)
            pygame.draw.rect(screen, (245, 245, 245), sign, border_radius=6)
            pygame.draw.rect(screen, frame, sign, 2, border_radius=6)

            # 文字はフォント環境差があるので線で雰囲気
            pygame.draw.line(screen, (80, 80, 80), (sign.x+10, sign.y+13), (sign.x+sign.w-10, sign.y+13), 2)

    def _draw_trees_and_lamps(self, screen):
        w, h = self.w, self.h
        ground = int(h * 0.65)

        # 近め：よく流す
        for i in range(8):
            base_x = i * 180 + 30
            x = base_x - int(self.offset * 0.65)
            x %= w
            # 木
            trunk = pygame.Rect(x + 18, ground - 85, 14, 55)
            pygame.draw.rect(screen, (110, 80, 50), trunk, border_radius=3)
            pygame.draw.circle(screen, (70, 140, 80), (x + 25, ground - 95), 34)
            pygame.draw.circle(screen, (60, 125, 70), (x + 8, ground - 85), 26)
            pygame.draw.circle(screen, (80, 155, 90), (x + 42, ground - 82), 24)

            # 街灯（木と交互）
            if i % 2 == 1:
                pole_x = x + 95
                pygame.draw.line(screen, (80, 80, 80), (pole_x, ground - 20), (pole_x, ground - 95), 4)
                pygame.draw.circle(screen, (250, 245, 220), (pole_x, ground - 98), 8)
                pygame.draw.circle(screen, (240, 235, 210), (pole_x, ground - 98), 12, 2)

    def _draw_ground(self, screen):
        w, h = self.w, self.h
        grass_y = int(h * 0.55)
        walk_y = int(h * 0.65)

        # 芝生
        pygame.draw.rect(screen, (95, 170, 95), (0, grass_y, w, walk_y - grass_y))
        # 影の境界
        pygame.draw.rect(screen, (75, 150, 80), (0, walk_y - 8, w, 8))

        # 歩道（タイル）
        pygame.draw.rect(screen, (185, 185, 190), (0, walk_y, w, h - walk_y))
        pygame.draw.rect(screen, (160, 160, 168), (0, walk_y, w, 10))

        # タイル線（近景なのでしっかり流す）
        tile = 46
        off = int(self.offset * 0.9) % tile
        for x in range(-tile, w + tile, tile):
            pygame.draw.line(screen, (150, 150, 155), (x - off, walk_y), (x - off, h), 2)
        for y in range(walk_y, h, tile):
            pygame.draw.line(screen, (150, 150, 155), (0, y), (w, y), 2)

        # ベンチ（近景）
        for i in range(3):
            base_x = i * 260 + 120
            x = base_x - int(self.offset * 0.85)
            x %= w
            by = walk_y + 35
            pygame.draw.rect(screen, (120, 80, 50), (x, by, 110, 16), border_radius=4)
            pygame.draw.rect(screen, (120, 80, 50), (x, by - 22, 110, 14), border_radius=4)
            pygame.draw.line(screen, (70, 70, 70), (x + 10, by + 16), (x + 10, by + 42), 4)
            pygame.draw.line(screen, (70, 70, 70), (x + 100, by + 16), (x + 100, by + 42), 4)

    def _draw_birds(self, screen):
        col = (40, 60, 80)
        for x, y, sp in self.birds:
            # 小さいV字で鳥っぽく
            pygame.draw.line(screen, col, (int(x), int(y)), (int(x + 6), int(y + 2)), 2)
            pygame.draw.line(screen, col, (int(x + 6), int(y + 2)), (int(x + 12), int(y)), 2)

    def draw(self, screen):
        self._draw_sky(screen)
        self._draw_clouds(screen)
        self._draw_far_buildings(screen)

        # 地面は建物より後ろだと不自然なので、遠景→建物→樹木→地面の順で
        self._draw_main_building(screen)
        self._draw_trees_and_lamps(screen)
        self._draw_ground(screen)
        self._draw_birds(screen)


# ---- 背景だけ動作確認したい場合 ----
if __name__ == "__main__":
    pygame.init()
    W, H = 960, 540
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    bg = CampusBackground(W, H, seed=3)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        bg.update(dt, speed=85.0)
        bg.draw(screen)
        pygame.display.flip()

    pygame.quit()
