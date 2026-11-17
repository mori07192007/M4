import pygame
import math
import random

class ClassroomBackground:
    def __init__(self, w, h, seed=1):
        self.w = w
        self.h = h
        self.offset = 0.0
        self.rng = random.Random(seed)

        # チョーク粉（粒子）を固定生成（毎フレーム位置だけ流す）
        self.dust = []
        for _ in range(60):
            x = self.rng.randrange(0, w)
            y = self.rng.randrange(0, h // 2)
            r = self.rng.choice([1, 1, 2])
            sp = self.rng.uniform(0.1, 0.35)
            self.dust.append([x, y, r, sp])

    def update(self, dt, speed=80.0):
        """dt: 秒。speed: 背景が左へ流れる速度(px/s)"""
        self.offset = (self.offset + speed * dt) % self.w

        # チョーク粉もゆっくり流す
        for p in self.dust:
            p[0] = (p[0] - p[3] * speed * dt) % self.w
            # ふわふわ
            p[1] += math.sin(p[0] * 0.02) * 0.05

    def draw(self, screen):
        w, h = self.w, self.h

        # ---- base colors ----
        wall = (235, 233, 228)
        floor = (168, 126, 86)
        floor_dark = (146, 108, 73)
        line = (120, 90, 60)

        screen.fill(wall)

        # ---- floor ----
        floor_y = int(h * 0.68)
        pygame.draw.rect(screen, floor, (0, floor_y, w, h - floor_y))
        pygame.draw.rect(screen, floor_dark, (0, floor_y, w, 10))

        # 木目ライン（スクロール）
        for i in range(0, w + 60, 60):
            x = i - int(self.offset * 0.8)
            pygame.draw.line(screen, line, (x, floor_y + 10), (x + 30, h), 2)

        # ---- blackboard (far layer) ----
        board_rect = pygame.Rect(int(w * 0.07), int(h * 0.12), int(w * 0.55), int(h * 0.32))
        pygame.draw.rect(screen, (30, 80, 55), board_rect, border_radius=8)
        pygame.draw.rect(screen, (90, 60, 30), board_rect.inflate(10, 10), 6, border_radius=10)

        # 黒板のチョーク跡
        for i in range(10):
            x = board_rect.x + 20 + i * 45
            y = board_rect.y + 25 + (i % 3) * 30
            pygame.draw.line(screen, (210, 230, 220), (x, y), (x + 25, y + 3), 2)

        # ---- bulletin board / posters ----
        for i in range(3):
            px = int(w * 0.68) + i * 75
            py = int(h * 0.13) + (i % 2) * 40
            rect = pygame.Rect(px, py, 55, 75)
            pygame.draw.rect(screen, (245, 245, 245), rect)
            pygame.draw.rect(screen, (120, 120, 120), rect, 2)
            pygame.draw.line(screen, (180, 60, 60), (px+8, py+15), (px+45, py+15), 3)

        # ---- windows (parallax slow) ----
        win_top = int(h * 0.10)
        win_h = int(h * 0.28)
        for i in range(4):
            base_x = int(w * 0.10) + i * 160
            x = base_x - int(self.offset * 0.25)
            x = (x + w) % w
            rect = pygame.Rect(x, win_top, 120, win_h)
            pygame.draw.rect(screen, (200, 235, 255), rect)
            pygame.draw.rect(screen, (120, 140, 150), rect, 4)
            pygame.draw.line(screen, (120, 140, 150), (x + 60, win_top), (x + 60, win_top + win_h), 3)

            # 外の空（簡易グラデ）
            pygame.draw.circle(screen, (255, 255, 255), (x + 90, win_top + 60), 18)

        # ---- desks (mid layer) ----
        # パースっぽく：上の列ほど小さく、手前ほど大きく
        row_count = 4
        col_count = 4
        base_y = int(h * 0.40)
        for r in range(row_count):
            t = r / (row_count - 1) if row_count > 1 else 1
            y = int(base_y + t * (h * 0.28))
            scale = 0.55 + t * 0.75
            desk_w = int(120 * scale)
            desk_h = int(55 * scale)
            gap = int(40 * scale)

            for c in range(col_count):
                bx = int(w * 0.15) + c * (desk_w + gap)
                x = bx - int(self.offset * (0.55 + t * 0.15))
                x = (x + w) % w

                top = pygame.Rect(x, y, desk_w, desk_h)
                pygame.draw.rect(screen, (180, 140, 90), top, border_radius=6)
                pygame.draw.rect(screen, (120, 90, 60), top, 3, border_radius=6)

                # 脚
                leg_y = y + desk_h
                pygame.draw.line(screen, (70, 70, 70), (x + 12, leg_y), (x + 12, leg_y + int(35 * scale)), 4)
                pygame.draw.line(screen, (70, 70, 70), (x + desk_w - 12, leg_y), (x + desk_w - 12, leg_y + int(35 * scale)), 4)

        # ---- foreground edge (near layer) ----
        # 画面手前の机のフチ（近景）を入れると奥行きが出る
        fg_y = int(h * 0.83)
        pygame.draw.rect(screen, (120, 90, 60), (0, fg_y, w, int(h * 0.05)))
        pygame.draw.rect(screen, (160, 120, 80), (0, fg_y + 6, w, int(h * 0.05)))

        # ---- chalk dust particles ----
        for x, y, r, sp in self.dust:
            pygame.draw.circle(screen, (245, 245, 245), (int(x), int(y)), r)


# ---- 簡単な動作例（背景だけ確認したい時） ----
if __name__ == "__main__":
    pygame.init()
    W, H = 960, 540
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    bg = ClassroomBackground(W, H, seed=2)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        bg.update(dt, speed=90.0)
        bg.draw(screen)

        pygame.display.flip()

    pygame.quit()
