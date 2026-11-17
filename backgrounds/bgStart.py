import sys
import pygame
import math


def _draw_pixel_text(screen, text, x, y, scale=4, color=(255, 255, 255), bg=None):
    """Very small 5x7-ish pixel font (only supports a limited set).

    This keeps the start screen self-contained (no external font files).
    Unsupported characters are treated as spaces.
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

    # Normalize
    text = text.upper()

    px = x
    for ch in text:
        glyph = font.get(ch, font[" "])
        gw = len(glyph[0])
        gh = len(glyph)
        for row in range(gh):
            for col in range(gw):
                if glyph[row][col] == "1":
                    pygame.draw.rect(
                        screen,
                        color,
                        pygame.Rect(px + col * scale, y + row * scale, scale, scale),
                    )
                elif bg is not None:
                    pygame.draw.rect(
                        screen,
                        bg,
                        pygame.Rect(px + col * scale, y + row * scale, scale, scale),
                    )
        px += (gw + 1) * scale


class StartScreenMarioStyle:
    """A Mario-like start screen (sky + hills + blocks) with a title placeholder.

    Clicking starts the game by importing and launching backgrounds/bgSea.py.
    """

    def __init__(self, w=960, h=540):
        self.w = w
        self.h = h
        self.t = 0.0
        self.scroll = 0.0

        self.title_text = ""  # keep empty: user wants an upper-middle space for the title

        self._clouds = [
            [120, 70, 1.0],
            [420, 95, 0.7],
            [760, 60, 0.9],
        ]

    def update(self, dt):
        self.t += dt
        self.scroll = (self.scroll + 45.0 * dt) % self.w

        # slow drifting clouds (loop)
        for c in self._clouds:
            c[0] -= 12.0 * dt * c[2]
            if c[0] < -140:
                c[0] = self.w + 140

    def _draw_sky(self, screen):
        w, h = self.w, self.h
        top = (92, 189, 255)
        bot = (170, 230, 255)
        for y in range(h):
            t = y / max(1, h - 1)
            c = (
                int(top[0] * (1 - t) + bot[0] * t),
                int(top[1] * (1 - t) + bot[1] * t),
                int(top[2] * (1 - t) + bot[2] * t),
            )
            pygame.draw.line(screen, c, (0, y), (w, y))

        # clouds
        for x, y, s in self._clouds:
            cx = int(x)
            cy = int(y)
            col = (255, 255, 255)
            pygame.draw.ellipse(screen, col, (cx, cy, int(120 * s), int(40 * s)))
            pygame.draw.ellipse(screen, col, (cx + int(25 * s), cy - int(18 * s), int(70 * s), int(36 * s)))
            pygame.draw.ellipse(screen, col, (cx + int(60 * s), cy + int(2 * s), int(75 * s), int(32 * s)))

    def _draw_hills_and_ground(self, screen):
        w, h = self.w, self.h
        ground_y = int(h * 0.78)

        # far hills (slower)
        for i in range(-1, 6):
            x = i * 220 - int(self.scroll * 0.35)
            x %= (w + 220)
            x -= 220
            pygame.draw.ellipse(screen, (70, 180, 90), (x, ground_y - 120, 280, 170))
            pygame.draw.ellipse(screen, (55, 155, 75), (x + 25, ground_y - 92, 230, 140))

        # ground
        pygame.draw.rect(screen, (120, 200, 90), (0, ground_y, w, h - ground_y))
        pygame.draw.rect(screen, (80, 160, 65), (0, ground_y, w, 12))

        # simple "dirt" pattern on the ground
        for i in range(0, w, 28):
            pygame.draw.circle(screen, (95, 175, 75), (i + 10, ground_y + 22), 6)

    def _draw_platformer_blocks(self, screen):
        w, h = self.w, self.h
        # brick blocks line (scrolls)
        y = int(h * 0.58)
        block = 40
        off = int(self.scroll * 0.85) % block

        for i in range(-2, (w // block) + 3):
            x = i * block - off
            rect = pygame.Rect(x, y, block, block)
            pygame.draw.rect(screen, (205, 120, 55), rect)
            pygame.draw.rect(screen, (140, 75, 30), rect, 3)
            # inner brick lines
            pygame.draw.line(screen, (150, 85, 40), (x + 6, y + 14), (x + block - 6, y + 14), 2)
            pygame.draw.line(screen, (150, 85, 40), (x + 6, y + 28), (x + block - 6, y + 28), 2)
            pygame.draw.line(screen, (150, 85, 40), (x + block // 2, y + 14), (x + block // 2, y + 28), 2)

        # pipes (static-ish, minimal movement)
        pipe_x = int(w * 0.12)
        pipe_y = int(h * 0.63)
        pygame.draw.rect(screen, (30, 170, 80), (pipe_x, pipe_y, 70, 120), border_radius=6)
        pygame.draw.rect(screen, (20, 120, 55), (pipe_x, pipe_y, 70, 120), 4, border_radius=6)
        pygame.draw.rect(screen, (30, 190, 90), (pipe_x - 8, pipe_y - 20, 86, 26), border_radius=8)
        pygame.draw.rect(screen, (20, 120, 55), (pipe_x - 8, pipe_y - 20, 86, 26), 4, border_radius=8)

    def _draw_title_placeholder(self, screen):
        w, h = self.w, self.h
        # Title safe area (upper-middle)
        area_w = int(w * 0.72)
        area_h = int(h * 0.16)
        area_x = (w - area_w) // 2
        area_y = int(h * 0.12)

        # A soft panel to make the title readable, but still allow empty space
        panel = pygame.Surface((area_w, area_h), pygame.SRCALPHA)
        panel.fill((255, 255, 255, 45))
        screen.blit(panel, (area_x, area_y))
        pygame.draw.rect(screen, (255, 255, 255), (area_x, area_y, area_w, area_h), 2, border_radius=10)

        if self.title_text.strip():
            # simple pixel text center
            text = self.title_text.upper()
            # estimate width
            est_w = len(text) * 6 * 5
            tx = area_x + (area_w - est_w) // 2
            ty = area_y + 18
            _draw_pixel_text(screen, text, tx, ty, scale=5, color=(255, 255, 255))

    def _draw_click_to_start(self, screen):
        w, h = self.w, self.h
        # blinking prompt (pixel font)
        blink = (math.sin(self.t * 3.5) + 1) * 0.5
        if blink > 0.35:
            msg = "CLICK TO START!"
            est_w = len(msg) * 6 * 4
            x = (w - est_w) // 2
            y = int(h * 0.72)
            _draw_pixel_text(screen, msg, x, y, scale=4, color=(255, 255, 255))

    def draw(self, screen):
        self._draw_sky(screen)
        self._draw_hills_and_ground(screen)
        self._draw_platformer_blocks(screen)
        self._draw_title_placeholder(screen)
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

    start = StartScreenMarioStyle(w, h)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Launch the game (bgSea.py)
                # We import and call its __main__ entry by reusing its file as a module.
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
