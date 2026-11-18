import random
import math
import pygame


class EndRollScreen:
    """A simple movie-like end roll screen.

    - Black background
    - White text
    - Credits scroll from bottom to top
    - Includes a "CONGRATULATIONS" message in the roll

    This is a standalone screen. It doesn't connect to other scenes.
    """

    def __init__(self, w=960, h=540, *, lines=None, speed=85):
        self.w = w
        self.h = h
        self.speed = float(speed)  # px/sec

        # Fireworks (flashy mode)
        self.rng = random.Random(7)
        self.fireworks = []  # list of dicts: {x,y,vx,vy,r,g,b,life,max_life,size}
        self.spawn_timer = 0.0

        if lines is None:
            # Default end roll contents (edit freely)
            lines = [
                " ",
                "CONGRATULATIONS!",
                " ",
                "You completed the game.",
                " ",
                "========================",
                " ",
                "CREDITS",
                " ",
                "Director",
                "MORIKAWA MANA",
                " ",
                "Programmer",
                " ",
                "Player Character : MORITA YUKIKO",
                "Enemy Character : OCHIAI MAKO",
                "Collision : MORIKAWA MANA",
                "Background : NINOMIYA MOE",
                " ",
                "Game Design",
                "OCHIAI MAKO",
                "NINOMIYA MOE",
                "MORIKAWA MANA",
                "MORITA YUKIKO",
                " ",
                "Special Thanks",
                "Everyone who played!",
                " ",
                "========================",
                " ",
                "THE END",
                " ",
            ]

        self.lines = lines

        # Font (uses system default). If you want a pixel font later, we can swap it.
        self.font_title = pygame.font.Font(None, 76)
        self.font_main = pygame.font.Font(None, 44)
        self.font_name = pygame.font.Font(None, 52)  # make names stand out
        self.font_small = pygame.font.Font(None, 30)

        # Pre-render text surfaces for performance and stable layout.
        self.rendered = []
        for s in self.lines:
            st = s.strip()
            if st in ("CONGRATULATIONS!", "CREDITS", "THE END"):
                surf = self.font_title.render(s, True, (255, 255, 255))
                gap = 42
            elif st.startswith("="):
                surf = self.font_small.render(s, True, (255, 255, 255))
                gap = 28
            elif st == "":
                surf = None
                gap = 44
            elif st.isupper() and ":" not in st and st not in ("DIRECTOR", "PROGRAMMER", "GAME DESIGN", "GRAPHICS", "SPECIAL THANKS"):
                # A single uppercase name line (e.g., MORIKAWA MANA)
                surf = self.font_name.render(s, True, (255, 255, 255))
                gap = 36
            else:
                surf = self.font_main.render(s, True, (255, 255, 255))
                gap = 30
            self.rendered.append((surf, gap))

        # Build total scroll height
        total = 0
        for surf, gap in self.rendered:
            if surf is not None:
                total += surf.get_height()
            total += gap
        self.total_height = total

        # Start below the bottom edge
        self.y = float(h + 30)
        self.finished = False

    def update(self, dt):
        if self.finished:
            return

        # --- fireworks update ---
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            # spawn an explosion near the upper half so it doesn't sit behind the hint only
            self._spawn_firework()
            # flashy: frequent fireworks
            self.spawn_timer = self.rng.uniform(0.35, 0.85)

        g = 240.0  # gravity
        alive = []
        for p in self.fireworks:
            p["life"] += dt
            if p["life"] >= p["max_life"]:
                continue
            p["vy"] += g * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            alive.append(p)
        self.fireworks = alive

        self.y -= self.speed * dt
        # If the last line has passed above the screen, mark finished.
        if self.y + self.total_height < -30:
            self.finished = True

    def _spawn_firework(self):
        w, h = self.w, self.h
        cx = self.rng.uniform(w * 0.15, w * 0.85)
        cy = self.rng.uniform(h * 0.10, h * 0.55)

        # bright, saturated palette
        palette = [
            (255, 80, 80),
            (255, 200, 60),
            (120, 255, 120),
            (80, 200, 255),
            (190, 120, 255),
            (255, 120, 220),
        ]
        r, g, b = self.rng.choice(palette)

        # particles
        count = self.rng.randint(90, 150)
        base_speed = self.rng.uniform(140, 260)
        max_life = self.rng.uniform(1.4, 2.3)
        size = self.rng.uniform(1.6, 3.2)

        for i in range(count):
            ang = self.rng.uniform(0.0, 6.283185307179586)
            sp = base_speed * (0.35 + 0.75 * self.rng.random())
            vx = sp * math.cos(ang)
            vy = sp * math.sin(ang)
            # slightly bias upward so it blooms nicely
            vy -= self.rng.uniform(30, 80)

            self.fireworks.append(
                {
                    "x": cx,
                    "y": cy,
                    "vx": vx,
                    "vy": vy,
                    "r": r,
                    "g": g,
                    "b": b,
                    "life": 0.0,
                    "max_life": max_life,
                    "size": size,
                }
            )

        # optional core flash particles (white center)
        for _ in range(16):
            self.fireworks.append(
                {
                    "x": cx,
                    "y": cy,
                    "vx": self.rng.uniform(-60, 60),
                    "vy": self.rng.uniform(-60, 60),
                    "r": 255,
                    "g": 255,
                    "b": 255,
                    "life": 0.0,
                    "max_life": self.rng.uniform(0.5, 0.9),
                    "size": self.rng.uniform(2.4, 4.0),
                }
            )

    def draw(self, screen):
        screen.fill((0, 0, 0))

        # --- draw fireworks behind text ---
        if self.fireworks:
            fx = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            for p in self.fireworks:
                t = p["life"] / max(1e-6, p["max_life"])
                # fade out
                a = int(255 * (1.0 - t) ** 1.8)
                if a <= 0:
                    continue
                # gentle shrink
                s = max(1.0, p["size"] * (1.0 - 0.35 * t))
                col = (p["r"], p["g"], p["b"], a)
                pygame.draw.circle(fx, col, (int(p["x"]), int(p["y"])), int(s))
                # glow ring
                pygame.draw.circle(
                    fx,
                    (p["r"], p["g"], p["b"], max(0, int(a * 0.22))),
                    (int(p["x"]), int(p["y"])),
                    int(s * 3.2),
                    2,
                )

            # additive-ish feel by blitting with alpha surface
            screen.blit(fx, (0, 0))

        y = self.y
        for surf, gap in self.rendered:
            if surf is not None:
                x = (self.w - surf.get_width()) // 2
                screen.blit(surf, (x, int(y)))
                y += surf.get_height()
            y += gap

        # Optional: subtle "Press ESC" hint (static)
        hint = self.font_small.render("ESC: Quit", True, (200, 200, 200))
        screen.blit(hint, (12, self.h - hint.get_height() - 10))


def run(w=960, h=540):
    """Standalone end roll demo."""
    pygame.init()
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("End Roll")
    clock = pygame.time.Clock()

    endroll = EndRollScreen(w, h)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False

        endroll.update(dt)
        endroll.draw(screen)
        pygame.display.flip()

        # If finished, keep showing last frame for a moment, then exit.
        if endroll.finished:
            pygame.time.delay(900)
            running = False

    pygame.quit()


if __name__ == "__main__":
    run()
