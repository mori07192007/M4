import math
import random
import pygame


def _draw_pixel_text(screen, text, x, y, scale=4, color=(255, 255, 255), bg=None):
    """Very small 5x7-ish pixel font (limited glyphs).

    Start画面を外部フォント無しで完結させるための簡易描画。
    対応していない文字はスペース扱いになります。
    """

    font = {
        "A": [
            "01110",
            "10001",
            "10001",
            "11111",
            "10001",
            "10001",
            "10001",
        ],
        "C": [
            "01111",
            "10000",
            "10000",
            "10000",
            "10000",
            "10000",
            "01111",
        ],
        "E": [
            "11111",
            "10000",
            "10000",
            "11110",
            "10000",
            "10000",
            "11111",
        ],
        "I": [
            "11111",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
            "11111",
        ],
        "K": [
            "10001",
            "10010",
            "10100",
            "11000",
            "10100",
            "10010",
            "10001",
        ],
        "L": [
            "10000",
            "10000",
            "10000",
            "10000",
            "10000",
            "10000",
            "11111",
        ],
        "N": [
            "10001",
            "11001",
            "10101",
            "10011",
            "10001",
            "10001",
            "10001",
        ],
        "O": [
            "01110",
            "10001",
            "10001",
            "10001",
            "10001",
            "10001",
            "01110",
        ],
        "P": [
            "11110",
            "10001",
            "10001",
            "11110",
            "10000",
            "10000",
            "10000",
        ],
        "R": [
            "11110",
            "10001",
            "10001",
            "11110",
            "10100",
            "10010",
            "10001",
        ],
        "S": [
            "01111",
            "10000",
            "10000",
            "01110",
            "00001",
            "00001",
            "11110",
        ],
        "T": [
            "11111",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
        ],
        "U": [
            "10001",
            "10001",
            "10001",
            "10001",
            "10001",
            "10001",
            "01110",
        ],
        "V": [
            "10001",
            "10001",
            "10001",
            "10001",
            "01010",
            "01010",
            "00100",
        ],
        "Y": [
            "10001",
            "10001",
            "01010",
            "00100",
            "00100",
            "00100",
            "00100",
        ],
        "!": [
            "00100",
            "00100",
            "00100",
            "00100",
            "00100",
            "00000",
            "00100",
        ],
        ".": [
            "00000",
            "00000",
            "00000",
            "00000",
            "00000",
            "00000",
            "00100",
        ],
        "-": [
            "00000",
            "00000",
            "00000",
            "11111",
            "00000",
            "00000",
            "00000",
        ],
        " ": [
            "00000",
            "00000",
            "00000",
            "00000",
            "00000",
            "00000",
            "00000",
        ],
    }

    text = text.upper()
    px = int(x)
    for ch in text:
        glyph = font.get(ch, font[" "])
        gw = len(glyph[0])
        gh = len(glyph)

        if bg is not None:
            pygame.draw.rect(screen, bg, (px, y, (gw + 1) * scale, (gh + 1) * scale))

        for row in range(gh):
            for col in range(gw):
                if glyph[row][col] == "1":
                    pygame.draw.rect(
                        screen,
                        color,
                        (px + col * scale, int(y) + row * scale, scale, scale),
                    )
        px += (gw + 1) * scale


def _pixel_text_width(text, scale=4):
    """_draw_pixel_text と同じロジックで文字列幅(px)を見積もる。

    文字種によっては未定義→スペース扱いになるので、len(text)ベースより正確。
    """
    # glyph is 5px wide and we keep 1px spacing => 6 "cells" per character
    # (スペースや未定義文字も同じ幅として扱う)
    return len(text) * 6 * scale


class StartScreenNeoFuturistic:
    """近未来っぽいシューティング用のスタート背景。

    - ダークな縦グラデーション + ビネット
    - 斜め方向に流れる“データライン”
    - ワイヤーフレームのパースグリッド（床）
    - 光るHUDパネル + タイトル表示 + クリック促し
    """

    def __init__(self, w, h, *, title_text="Virus Shootting Game"):
        self.w = int(w)
        self.h = int(h)
        self.title_text = title_text

        self.t = 0.0
        self.rng = random.Random(42)

        # 背景要素
        self.star_count = max(90, (self.w * self.h) // 9000)
        self.stars = []
        for _ in range(self.star_count):
            x = self.rng.randrange(0, self.w)
            y = self.rng.randrange(0, self.h)
            sp = self.rng.uniform(25.0, 110.0)
            r = self.rng.choice([1, 1, 1, 2])
            self.stars.append([x, y, sp, r])

        # 斜めのデータライン（長い線分が流れる）
        self.lines = []
        for _ in range(26):
            x = self.rng.uniform(-self.w * 0.2, self.w * 1.2)
            y = self.rng.uniform(-self.h * 0.4, self.h * 1.2)
            length = self.rng.uniform(60, 260)
            speed = self.rng.uniform(110, 320)
            width = self.rng.choice([1, 1, 2])
            hue = self.rng.random()
            self.lines.append([x, y, length, speed, width, hue])

        # スキャンライン
        self.scan_phase = 0.0

        # キャッシュサーフェス（解像度依存）
        self._grad = None
        self._vignette = None
        self._noise = None

        # Center character image (optional)
        # NOTE: 現状のリポジトリ内では /home/moe7514/Mana/test/player_run.png に存在していました。
        # もし今後場所を移す場合は、このパスを調整してください。
        self.player_image_path = "/home/moe7514/Mana/test/player_run.png"
        self.player_img = None
        self.player_img_glow = None
        self._load_player_image()
        self._rebuild_static_surfaces()

        # Use a normal font for title to avoid "missing glyph" gaps in the tiny pixel font.
        # (Pixel font is intentionally limited and doesn't include letters like G/H, etc.)
        try:
            self.title_font = pygame.font.Font(None, int(self.h * 0.095))  # ~50px on 540p
            self.sub_font = pygame.font.Font(None, int(self.h * 0.050))
        except Exception:
            # In rare cases pygame font might not be initialized yet; fallback later in draw.
            self.title_font = None
            self.sub_font = None

    def _load_player_image(self):
        """player_run.png を読み込み、描画用に少し加工したサーフェスを用意する。"""
        try:
            img = pygame.image.load(self.player_image_path)
            # convert_alpha は display.set_mode 前だと失敗することがあるので安全側で try。
            try:
                img = img.convert_alpha()
            except Exception:
                pass

            # 画面中央に置いたときに大きすぎないよう縮小（高さの 38% を上限に）
            max_h = int(self.h * 0.38)
            if img.get_height() > max_h:
                scale = max_h / img.get_height()
                new_w = max(1, int(img.get_width() * scale))
                new_h = max(1, int(img.get_height() * scale))
                img = pygame.transform.smoothscale(img, (new_w, new_h))

            self.player_img = img

            # 簡易グロー（同じ画像を拡大して薄い色を乗せる）
            glow_scale = 1.18
            gw = max(1, int(img.get_width() * glow_scale))
            gh = max(1, int(img.get_height() * glow_scale))
            glow = pygame.transform.smoothscale(img, (gw, gh))

            # 色味をHUD寄り（シアン）に寄せた透明サーフェス
            glow_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
            glow_surf.blit(glow, (0, 0))
            # 乗算で色を寄せる（白い部分ほどシアンになる）
            tint = pygame.Surface((gw, gh), pygame.SRCALPHA)
            tint.fill((0, 220, 255, 95))
            glow_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            self.player_img_glow = glow_surf
        except Exception:
            # 画像が無い/読めない場合は何もしない
            self.player_img = None
            self.player_img_glow = None

    def _rebuild_static_surfaces(self):
        # 背景の縦グラデ（暗いネイビー→黒）
        self._grad = pygame.Surface((self.w, self.h))
        top = (6, 14, 34)
        mid = (4, 8, 18)
        bot = (2, 2, 6)
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            if t < 0.55:
                u = t / 0.55
                c = (
                    int(top[0] * (1 - u) + mid[0] * u),
                    int(top[1] * (1 - u) + mid[1] * u),
                    int(top[2] * (1 - u) + mid[2] * u),
                )
            else:
                u = (t - 0.55) / 0.45
                c = (
                    int(mid[0] * (1 - u) + bot[0] * u),
                    int(mid[1] * (1 - u) + bot[1] * u),
                    int(mid[2] * (1 - u) + bot[2] * u),
                )
            pygame.draw.line(self._grad, c, (0, y), (self.w, y))

        # ビネット（端を暗く）
        self._vignette = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(14):
            a = int(10 + 10 * (i / 13))
            rect = pygame.Rect(-i * 22, -i * 16, self.w + i * 44, self.h + i * 32)
            pygame.draw.ellipse(self._vignette, (0, 0, 0, a), rect, width=20)

        # 微細ノイズ（うっすら）
        self._noise = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._noise.fill((0, 0, 0, 0))
        for _ in range((self.w * self.h) // 1800):
            x = self.rng.randrange(0, self.w)
            y = self.rng.randrange(0, self.h)
            a = self.rng.randrange(8, 22)
            self._noise.set_at((x, y), (255, 255, 255, a))

    def update(self, dt):
        self.t += float(dt)
        self.scan_phase += dt * 2.1

        # stars: 下方向に流す（シューティングっぽい）
        for s in self.stars:
            s[1] += s[2] * dt
            if s[1] >= self.h:
                s[0] = self.rng.randrange(0, self.w)
                s[1] = -self.rng.randrange(0, int(self.h * 0.2))

        # data lines: 右下へ流す
        for ln in self.lines:
            ln[0] += ln[3] * dt
            ln[1] += ln[3] * dt * 0.58
            if ln[0] > self.w * 1.25 or ln[1] > self.h * 1.25:
                ln[0] = self.rng.uniform(-self.w * 0.35, -self.w * 0.05)
                ln[1] = self.rng.uniform(-self.h * 0.35, self.h * 0.6)
                ln[2] = self.rng.uniform(60, 260)
                ln[3] = self.rng.uniform(110, 320)
                ln[4] = self.rng.choice([1, 1, 2])
                ln[5] = self.rng.random()

    def _hud_color(self, hue, a=255):
        # hue: 0..1 を シアン〜パープルに寄せる
        # ざっくり: hue<0.5 はシアン寄り, >0.5 はマゼンタ寄り
        if hue < 0.5:
            t = hue / 0.5
            c0 = (0, 220, 255)
            c1 = (110, 255, 220)
        else:
            t = (hue - 0.5) / 0.5
            c0 = (110, 255, 220)
            c1 = (210, 80, 255)
        return (
            int(c0[0] * (1 - t) + c1[0] * t),
            int(c0[1] * (1 - t) + c1[1] * t),
            int(c0[2] * (1 - t) + c1[2] * t),
            int(a),
        )

    def _draw_starfield(self, screen):
        for x, y, sp, r in self.stars:
            # speedに応じて明るさを変える
            a = int(120 + 120 * min(1.0, sp / 110.0))
            col = (210, 225, 255, a)
            if r <= 1:
                screen.set_at((int(x), int(y)), col)
            else:
                pygame.draw.circle(screen, col, (int(x), int(y)), r)

    def _draw_data_lines(self, screen):
        # additive風に見せるためにαサーフェスに描いて足す
        fx = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for x, y, length, speed, width, hue in self.lines:
            col = self._hud_color(hue, a=120)
            # 斜め線分
            x2 = x + length
            y2 = y + length * 0.58
            pygame.draw.line(fx, col, (int(x), int(y)), (int(x2), int(y2)), width)

            # たまに端に小さな“ノード”
            if int((x + y) * 0.01) % 7 == 0:
                pygame.draw.circle(fx, self._hud_color(hue, a=140), (int(x2), int(y2)), 2)

        screen.blit(fx, (0, 0))

    def _draw_wire_grid(self, screen):
        # ワイヤーフレーム床: 消失点を上側中央寄りに
        w, h = self.w, self.h
        vp_x = w * 0.5
        vp_y = h * 0.38
        base_y = h * 0.92
        top_y = h * 0.55

        # 色（シアン系）
        pulse = 0.5 + 0.5 * math.sin(self.t * 1.7)
        line_col = (0, int(140 + 70 * pulse), int(220 + 20 * pulse), 140)

        grid = pygame.Surface((w, h), pygame.SRCALPHA)

        # 縦の放射線（床の奥行き）
        rays = 18
        for i in range(-rays, rays + 1):
            # 画面下の幅を広く
            bx = vp_x + i * (w * 0.045)
            pygame.draw.line(grid, line_col, (bx, base_y), (vp_x, vp_y), 1)

        # 横線（奥へ行くほど間隔が狭く）
        for k in range(1, 18):
            t = k / 18
            # 非線形で奥に詰める
            y = base_y + (top_y - base_y) * (t * t)
            # 左右端はパースで絞る
            half = (w * 0.58) * (1 - t) + (w * 0.06) * t
            pygame.draw.line(grid, (0, line_col[1], line_col[2], 90), (vp_x - half, y), (vp_x + half, y), 1)

        # ほんのりグロー（太い線を薄いαで重ねる）
        glow_col = (0, line_col[1], line_col[2], 28)
        for k in range(1, 9):
            y = base_y + (top_y - base_y) * ((k / 9) ** 2)
            half = (w * 0.58) * (1 - k / 9) + (w * 0.06) * (k / 9)
            pygame.draw.line(grid, glow_col, (vp_x - half, y), (vp_x + half, y), 3)

        screen.blit(grid, (0, 0))

    def _draw_hud_panels(self, screen):
        w, h = self.w, self.h

        panel = pygame.Surface((w, h), pygame.SRCALPHA)

        # 中央パネル（タイトル）
        area_w = int(w * 0.78)
        area_h = int(h * 0.17)
        area_x = (w - area_w) // 2
        area_y = int(h * 0.10)

        # パネル塗り + 枠
        pygame.draw.rect(panel, (0, 0, 0, 90), (area_x, area_y, area_w, area_h), border_radius=14)
        pygame.draw.rect(panel, (0, 220, 255, 170), (area_x, area_y, area_w, area_h), 2, border_radius=14)

        # 角のL字装飾
        corner = (0, 220, 255, 220)
        s = 18
        lw = 3
        # tl
        pygame.draw.line(panel, corner, (area_x + 10, area_y + 10), (area_x + 10 + s, area_y + 10), lw)
        pygame.draw.line(panel, corner, (area_x + 10, area_y + 10), (area_x + 10, area_y + 10 + s), lw)
        # tr
        pygame.draw.line(panel, corner, (area_x + area_w - 10, area_y + 10), (area_x + area_w - 10 - s, area_y + 10), lw)
        pygame.draw.line(panel, corner, (area_x + area_w - 10, area_y + 10), (area_x + area_w - 10, area_y + 10 + s), lw)
        # bl
        pygame.draw.line(panel, corner, (area_x + 10, area_y + area_h - 10), (area_x + 10 + s, area_y + area_h - 10), lw)
        pygame.draw.line(panel, corner, (area_x + 10, area_y + area_h - 10), (area_x + 10, area_y + area_h - 10 - s), lw)
        # br
        pygame.draw.line(panel, corner, (area_x + area_w - 10, area_y + area_h - 10), (area_x + area_w - 10 - s, area_y + area_h - 10), lw)
        pygame.draw.line(panel, corner, (area_x + area_w - 10, area_y + area_h - 10), (area_x + area_w - 10, area_y + area_h - 10 - s), lw)

        # 左下ステータス風パネル
        p2_w = int(w * 0.32)
        p2_h = int(h * 0.12)
        p2_x = int(w * 0.06)
        p2_y = int(h * 0.76)
        pygame.draw.rect(panel, (0, 0, 0, 85), (p2_x, p2_y, p2_w, p2_h), border_radius=12)
        pygame.draw.rect(panel, (210, 80, 255, 140), (p2_x, p2_y, p2_w, p2_h), 2, border_radius=12)

        # 右下ミニマップ風パネル
        p3_w = int(w * 0.22)
        p3_h = int(h * 0.16)
        p3_x = int(w * 0.72)
        p3_y = int(h * 0.70)
        pygame.draw.rect(panel, (0, 0, 0, 85), (p3_x, p3_y, p3_w, p3_h), border_radius=12)
        pygame.draw.rect(panel, (0, 220, 255, 140), (p3_x, p3_y, p3_w, p3_h), 2, border_radius=12)

        # パネル内の飾りライン
        for i in range(5):
            yy = p2_y + 14 + i * 14
            pygame.draw.line(panel, (0, 220, 255, 70), (p2_x + 12, yy), (p2_x + p2_w - 12, yy), 1)

        # ミニマップの格子
        for i in range(6):
            xx = p3_x + 12 + i * ((p3_w - 24) / 5)
            pygame.draw.line(panel, (0, 220, 255, 45), (xx, p3_y + 12), (xx, p3_y + p3_h - 12), 1)
        for i in range(5):
            yy = p3_y + 12 + i * ((p3_h - 24) / 4)
            pygame.draw.line(panel, (0, 220, 255, 45), (p3_x + 12, yy), (p3_x + p3_w - 12, yy), 1)

        # 画面に合成
        screen.blit(panel, (0, 0))

        # タイトル
        if self.title_text.strip():
            # ---- normal font title (no weird spaces) ----
            if self.title_font is None:
                self.title_font = pygame.font.Font(None, int(self.h * 0.095))

            title_surf = self.title_font.render(self.title_text, True, (240, 250, 255))

            # Soft glow behind title
            glow = pygame.Surface((title_surf.get_width() + 24, title_surf.get_height() + 16), pygame.SRCALPHA)
            glow.fill((0, 0, 0, 0))
            gcol = (0, 220, 255, 55)
            pygame.draw.ellipse(glow, gcol, glow.get_rect())
            gx = area_x + (area_w - glow.get_width()) // 2
            gy = area_y + 10
            screen.blit(glow, (gx, gy))

            tx = area_x + (area_w - title_surf.get_width()) // 2
            ty = area_y + 12
            screen.blit(title_surf, (tx, ty))

        # ちょい小さいサブ
        sub = "NEO FUTURISTIC START"
        if self.sub_font is None:
            self.sub_font = pygame.font.Font(None, int(self.h * 0.050))
        sub_surf = self.sub_font.render(sub, True, (170, 230, 255))
        sx = area_x + (area_w - sub_surf.get_width()) // 2
        sy = area_y + area_h - sub_surf.get_height() - 10
        screen.blit(sub_surf, (sx, sy))

    def _draw_center_player(self, screen):
        """スタート画面の中央に player_run.png を表示する。"""
        if self.player_img is None:
            return

        w, h = self.w, self.h
        img = self.player_img

        # 中央（タイトルパネルの下〜ワイヤ床の上くらい）
        cx = w // 2
        cy = int(h * 0.54)

        # 少し上下にゆらす（浮遊感）
        bob = int(math.sin(self.t * 2.4) * 8)
        cy += bob

        x = cx - img.get_width() // 2
        y = cy - img.get_height() // 2

        # グロー→本体の順
        if self.player_img_glow is not None:
            g = self.player_img_glow
            gx = cx - g.get_width() // 2
            gy = cy - g.get_height() // 2
            screen.blit(g, (gx, gy))

        screen.blit(img, (x, y))

    def _draw_scanlines(self, screen):
        # うっすらスキャンライン + 上下に流れるライト
        w, h = self.w, self.h
        ol = pygame.Surface((w, h), pygame.SRCALPHA)

        # スキャンライン
        for y in range(0, h, 3):
            ol.fill((0, 0, 0, 18), (0, y, w, 1))

        # 流れるライトバー
        bar_y = int((0.5 + 0.5 * math.sin(self.scan_phase)) * (h * 0.85))
        pygame.draw.rect(ol, (0, 220, 255, 18), (0, bar_y, w, 18))
        pygame.draw.rect(ol, (210, 80, 255, 10), (0, max(0, bar_y - 22), w, 10))

        screen.blit(ol, (0, 0))

    def _draw_click_to_start(self, screen):
        w, h = self.w, self.h
        blink = (math.sin(self.t * 3.8) + 1) * 0.5
        if blink > 0.25:
            msg = "CLICK TO START!"
            est_w = len(msg) * 6 * 4
            x = (w - est_w) // 2
            y = int(h * 0.80)
            _draw_pixel_text(screen, msg, x, y, scale=4, color=(0, 220, 255))

        # もう一段: ESC
        hint = "ESC - QUIT"
        est_w2 = len(hint) * 6 * 3
        _draw_pixel_text(
            screen,
            hint,
            (w - est_w2) // 2,
            int(h * 0.86),
            scale=3,
            color=(190, 200, 220),
        )

    def draw(self, screen):
        # base
        screen.blit(self._grad, (0, 0))

        # stars and streaks
        self._draw_starfield(screen)
        self._draw_data_lines(screen)

        # floor wire grid
        self._draw_wire_grid(screen)

        # overlays
        screen.blit(self._noise, (0, 0))
        screen.blit(self._vignette, (0, 0))
        self._draw_scanlines(screen)

        # center character
        self._draw_center_player(screen)

        # hud UI
        self._draw_hud_panels(screen)
        self._draw_click_to_start(screen)


def run(w=960, h=540):
    """Start screen main loop.

    - Close window: quit.
    - Click anywhere: launch backgrounds/bgSea.py.
    """

    pygame.init()
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Start")
    clock = pygame.time.Clock()

    start = StartScreenNeoFuturistic(w, h, title_text="Virus Shootting Game")

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                import runpy

                pygame.quit()
                runpy.run_path("/home/moe7514/M4/backgrounds/bgSea.py", run_name="__main__")
                return

        start.update(dt)
        start.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()
