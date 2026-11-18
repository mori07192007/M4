import pygame
import random
import math

# NOTE:
# Transition background (self-contained): Stage2(bgSchool) -> Stage3(bgUniverse)
# - Execute directly: python backgrounds/bgSchoolToUniverse.py
# - No dependency on game code.


def _clamp(x, a, b):
    return a if x < a else b if x > b else x


def _smoothstep(t):
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _ease_in_out(t):
    t = _clamp(t, 0.0, 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _draw_alpha_rect(screen, rgba, rect):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill(rgba)
    screen.blit(s, (rect[0], rect[1]))


def _draw_arrow(screen, x1, y1, x2, y2, color, width=6, head_len=22, head_w=16):
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return
    ux = dx / dist
    uy = dy / dist

    sx2 = x2 - ux * head_len
    sy2 = y2 - uy * head_len
    pygame.draw.line(screen, color, (x1, y1), (sx2, sy2), width)

    px = -uy
    py = ux
    left = (sx2 + px * head_w, sy2 + py * head_w)
    right = (sx2 - px * head_w, sy2 - py * head_w)
    pygame.draw.polygon(screen, color, [(x2, y2), left, right])


def _draw_arrow_with_outline(screen, x1, y1, x2, y2, col_rgba, outline_rgba, width=8, head_len=26, head_w=18):
    _draw_arrow(screen, x1, y1, x2, y2, outline_rgba, width=width + 6, head_len=head_len + 6, head_w=head_w + 6)
    _draw_arrow(screen, x1, y1, x2, y2, col_rgba, width=width, head_len=head_len, head_w=head_w)


class _WarpStar:
    """A star used for the warp/tunnel effect."""

    def __init__(self, w, h, rng: random.Random):
        self.w = w
        self.h = h
        self.rng = rng
        self.reset()

    def reset(self):
        # star in normalized coords around center
        ang = self.rng.uniform(0, math.tau)
        rad = self.rng.uniform(0.02, 1.0)
        self.x = math.cos(ang) * rad
        self.y = math.sin(ang) * rad
        self.z = self.rng.uniform(0.05, 1.0)
        self.size = self.rng.uniform(1.0, 2.8)

    def update(self, dt, speed=1.0):
        # z decreases => star moves towards camera
        self.z -= dt * (0.65 + 1.8 * speed)
        if self.z <= 0.03:
            self.reset()
            self.z = 1.0

    def draw(self, screen, cx, cy, amt):
        # project
        k = (1.0 / max(0.05, self.z))
        px = cx + self.x * k * cx
        py = cy + self.y * k * cy

        # motion streak from previous position
        k2 = (1.0 / max(0.05, self.z + 0.15))
        px2 = cx + self.x * k2 * cx
        py2 = cy + self.y * k2 * cy

        a = int(210 * amt)
        col = (255, 255, 255, a)
        pygame.draw.line(screen, col, (px2, py2), (px, py), int(1 + 2 * amt))
        pygame.draw.circle(screen, col, (int(px), int(py)), int(self.size + 1.5 * amt))


class SchoolToUniverseTransitionBackground:
    """Stage2(bgSchool) -> transition -> Stage3(bgUniverse) background."""

    def __init__(
        self,
        w,
        h,
        seed=1,
        duration=9.0,
        show_text=True,
        text="STAGE 3: SPACE",
        show_diagram=True,
        diagram_scale=1.25,
        diagram_center=True,
        diagram_center_y=0.44,
        diagram_hold_mult=3.0,
        text_scale=1.35,
        diagram_simple=True,
    ):
        self.w = w
        self.h = h
        self.duration = float(duration)
        self.t = 0.0

        self.show_text = bool(show_text)
        self.text = text
        self.show_diagram = bool(show_diagram)
        self.diagram_scale = float(diagram_scale)
        self.diagram_center = bool(diagram_center)
        self.diagram_center_y = float(diagram_center_y)
        self.diagram_hold_mult = float(diagram_hold_mult)
        self.text_scale = float(text_scale)
        self.diagram_simple = bool(diagram_simple)

        self.rng = random.Random(seed)

        # Import stage backgrounds (relative when package, absolute when executed).
        try:
            from .bgSchool import CampusBackground
            from .bgUniverse import Background as UniverseBackground
        except Exception:
            from bgSchool import CampusBackground
            from bgUniverse import Background as UniverseBackground

        self.school = CampusBackground(w, h, seed=seed)
        # Universe background uses its own global WIDTH/HEIGHT, but its internal
        # surfaces are built from w/h passed here.
        self.universe = UniverseBackground(w, h, scroll_dir="left")

        self._overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # diagram flow particles
        self._flow = []
        for _ in range(18):
            self._flow.append({
                "t": self.rng.random(),
                "spd": self.rng.uniform(0.7, 1.45),
                "r": self.rng.uniform(2.0, 4.5),
                "a": self.rng.uniform(110, 220),
            })

        # warp stars (tunnel)
        self.warp = [_WarpStar(w, h, self.rng) for _ in range(150)]

        # fonts
        try:
            base_big = int(46 * max(0.8, self.text_scale))
            base_small = int(30 * max(0.8, self.text_scale))
            self.font = pygame.font.SysFont(None, base_big)
            self.font_small = pygame.font.SysFont(None, base_small)
        except Exception:
            self.font = None
            self.font_small = None

    def is_done(self):
        return self.t >= self.duration

    def restart(self):
        self.t = 0.0

    def update(self, dt):
        self.t += dt

        # keep both alive for crossfade
        self.school.update(dt, speed=85.0)
        self.universe.update(dt)

        for p in self._flow:
            p["t"] = (p["t"] + dt * p["spd"] * 0.85) % 1.0

        # warp stars are updated during warp phase (cheap to update always)
        for s in self.warp:
            s.update(dt, speed=1.0)

    def _phase(self):
        # 0.0 - t1 : campus normal
        # t1 - t2  : diagram/message hold (quick show then hold)
        # t2 - t3  : warp tunnel + flash + crossfade
        # after    : space fade-in settle
        t = self.t
        d = self.duration

        hold = 1.4 * max(0.5, self.diagram_hold_mult)
        t1 = 1.0
        t2 = t1 + hold
        t3 = t2 + 0.9

        show = 0.0
        warp = 0.0
        if t <= t1:
            show = 0.0
        elif t <= t2:
            ramp = 0.25
            if t <= t1 + ramp:
                show = _smoothstep((t - t1) / ramp)
            else:
                show = 1.0
        elif t <= t3:
            warp = _smoothstep((t - t2) / max(0.001, (t3 - t2)))

        n = _clamp(t / max(0.001, d), 0.0, 1.0)
        return show, warp, n

    def _draw_message(self, screen, amt):
        if not self.show_text:
            return
        if self.font is None:
            return
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return

        amt = _clamp(amt * 1.8, 0.0, 1.0)

        panel_w = int(self.w * 0.72)
        panel_h = int(self.h * 0.18)
        x = (self.w - panel_w) // 2
        y = int(self.h * (0.68 if self.diagram_center else 0.40))

        alpha = int(230 * amt)
        border_a = int(220 * amt)
        _draw_alpha_rect(screen, (240, 248, 255, alpha), (x, y, panel_w, panel_h))
        pygame.draw.rect(screen, (70, 95, 120, border_a), (x, y, panel_w, panel_h), 3, border_radius=14)

        col = (20, 35, 55)
        txt = self.font.render(self.text, True, col)
        tx = x + (panel_w - txt.get_width()) // 2
        ty = y + int(panel_h * 0.22)
        shadow = self.font.render(self.text, True, (255, 255, 255))
        shadow.set_alpha(int(140 * amt))
        screen.blit(shadow, (tx + 2, ty + 2))
        screen.blit(txt, (tx, ty))

        if self.font_small is not None:
            sub = self.font_small.render("CLEARED!", True, (20, 35, 55))
            sub.set_alpha(int(235 * amt))
            screen.blit(sub, (x + 22, y + int(panel_h * 0.62)))

    def _draw_transition_diagram(self, screen, amt):
        if not self.show_diagram:
            return
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return
        amt = _clamp(amt * 1.8, 0.0, 1.0)

        w, h = self.w, self.h
        s = max(0.7, self.diagram_scale)
        cy = int(h * _clamp(self.diagram_center_y, 0.20, 0.70)) if self.diagram_center else int(h * 0.315)
        box_w = int(w * 0.22 * s)
        box_h = int(h * 0.105 * s)
        gap = int(w * 0.055 * s)
        total_w = box_w * 2 + gap
        x0 = (w - total_w) // 2

        left = pygame.Rect(x0, cy - box_h // 2, box_w, box_h)
        right = pygame.Rect(x0 + box_w + gap, cy - box_h // 2, box_w, box_h)

        panel_a = int(235 * amt)
        border_a = int(220 * amt)
        border = (70, 95, 120, border_a)

        # left/right boxes: keep them simple (no busy icons) for readability
        _draw_alpha_rect(screen, (235, 250, 255, panel_a), (left.x, left.y, left.w, left.h))
        pygame.draw.rect(screen, border, left, 3, border_radius=12)

        _draw_alpha_rect(screen, (235, 250, 255, panel_a), (right.x, right.y, right.w, right.h))
        pygame.draw.rect(screen, border, right, 3, border_radius=12)

        # arrow (bold, high-contrast)
        ax1 = left.right + 8
        ay = left.centery
        ax2 = right.left - 8
        pulse = 0.55 + 0.45 * math.sin(self.t * 8.0)
        arrow_a = int((190 + 65 * pulse) * amt)
        arrow_col = (255, 255, 255, arrow_a)
        outline = (10, 20, 35, int(210 * amt))
        _draw_arrow_with_outline(screen, ax1, ay, ax2, ay, arrow_col, outline, width=8, head_len=26, head_w=18)

        # particles flowing on arrow (optional; disable when simple)
        if not self.diagram_simple:
            for p in self._flow:
                tt = p["t"]
                y = ay + math.sin(self.t * 9.0 + tt * math.tau) * 5.0
                x = ax1 + (ax2 - ax1) * tt
                a = int(p["a"] * amt)
                pygame.draw.circle(screen, (10, 20, 35, int(a * 0.95)), (int(x), int(y)), int(p["r"] + 2))
                pygame.draw.circle(screen, (255, 255, 255, a), (int(x), int(y)), int(p["r"]))

        if self.font_small is not None:
            lbl_a = int(250 * amt)
            # Render big, clean labels with a tiny outline (pseudo-bold) for clarity.
            def blit_outlined(text, centerx, centery):
                fg = self.font_small.render(text, True, (20, 35, 55))
                fg.set_alpha(lbl_a)
                # outline
                ol = self.font_small.render(text, True, (255, 255, 255))
                ol.set_alpha(int(lbl_a * 0.75))
                x = centerx - fg.get_width() // 2
                y = centery - fg.get_height() // 2
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    screen.blit(ol, (x + ox, y + oy))
                screen.blit(fg, (x, y))

            blit_outlined("CAMPUS", left.centerx, left.centery)
            blit_outlined("SPACE", right.centerx, right.centery)

    def _draw_warp_tunnel(self, screen, amt):
        # strong darken first
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return
        cx = self.w // 2
        cy = int(self.h * 0.40)

        # dark veil
        _draw_alpha_rect(screen, (0, 0, 0, int(210 * amt)), (0, 0, self.w, self.h))

        # tunnel stars
        for s in self.warp:
            s.draw(screen, cx, cy, amt)

        # a few concentric rings to amplify the warp feeling
        rings = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(7):
            r = int((60 + i * 55) * (0.55 + 1.0 * amt))
            a = int((140 - i * 16) * amt)
            pygame.draw.circle(rings, (200, 245, 255, a), (cx, cy), r, 3)
        screen.blit(rings, (0, 0))

    def draw(self, screen):
        show_amt, warp_amt, n = self._phase()

        # base: school
        self.school.draw(screen)

        # show diagram/text phase
        if show_amt > 0.0:
            # dim background behind UI
            dim = int(155 * show_amt)
            _draw_alpha_rect(screen, (0, 0, 0, dim), (0, 0, self.w, self.h))
            self._draw_transition_diagram(screen, show_amt)
            self._draw_message(screen, show_amt)

        # warp and crossfade
        if warp_amt > 0.0:
            self._draw_warp_tunnel(screen, warp_amt)

            # flash peak for punch
            peak = math.sin(math.pi * _clamp(warp_amt, 0.0, 1.0))
            _draw_alpha_rect(screen, (255, 255, 255, int(235 * peak)), (0, 0, self.w, self.h))

            # crossfade to universe
            self._overlay.fill((0, 0, 0, 0))
            self.universe.draw(self._overlay)
            blend = _ease_in_out(warp_amt)
            self._overlay.set_alpha(int(255 * blend))
            screen.blit(self._overlay, (0, 0))

        # settle
        if n > 0.70:
            settle = _smoothstep((n - 0.70) / 0.30)
            _draw_alpha_rect(screen, (0, 0, 0, int((1.0 - settle) * 80)), (0, 0, self.w, self.h))


def run_demo(w=960, h=540):
    pygame.init()
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("School -> Universe Transition")
    clock = pygame.time.Clock()

    bg = SchoolToUniverseTransitionBackground(
        w,
        h,
        seed=5,
        duration=10.0,
        diagram_hold_mult=3.0,
        diagram_center=True,
        diagram_center_y=0.44,
        text_scale=1.35,
        diagram_scale=1.25,
        show_text=True,
        show_diagram=True,
        diagram_simple=True,
    )

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_r:
                    bg.restart()

        bg.update(dt)
        bg.draw(screen)
        pygame.display.flip()

        # For standalone demo: show final universe clearly then loop.
        if bg.is_done():
            done_timer = 0.0
            while done_timer < 2.0:
                ddt = clock.tick(60) / 1000.0
                done_timer += ddt
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                        done_timer = 999
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                        running = False
                        done_timer = 999

                bg.universe.update(ddt)
                bg.universe.draw(screen)
                pygame.display.flip()
            bg.restart()

    pygame.quit()


if __name__ == "__main__":
    run_demo()
