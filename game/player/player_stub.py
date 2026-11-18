import math


class PlayerStub:
    """統合用の仮プレイヤー。

    - 友達のプレイヤー実装に置き換える前提
    - 描画はしない（キャラ担当に任せる）
    - 敵が狙うために位置と当たり判定だけ持つ
    """

    def __init__(self, *, x=80.0, ground_y=460.0):
        self.w, self.h = 34, 54
        self.x = float(x)
        self.y = float(ground_y - self.h)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self._ground_y = float(ground_y)

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def update(self, dt, keys, *, gravity=1200.0, world_w=5200.0):
        accel = 1600.0
        max_speed = 300.0

        # keysは pygame.key.get_pressed() を想定
        if keys[276]:  # K_LEFT
            self.vx -= accel * dt
        if keys[275]:  # K_RIGHT
            self.vx += accel * dt

        # 摩擦
        self.vx *= math.pow(0.0009, dt)
        self.vx = max(-max_speed, min(max_speed, self.vx))

        # ジャンプ
        if keys[32] and self.on_ground:  # K_SPACE
            self.vy = -520.0
            self.on_ground = False

        # 重力
        self.vy += gravity * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y + self.h >= self._ground_y:
            self.y = self._ground_y - self.h
            self.vy = 0.0
            self.on_ground = True

        self.x = max(0.0, min(world_w - self.w, self.x))

    def draw(self, surf, cam_x):
        return
