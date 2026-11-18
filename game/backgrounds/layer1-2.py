import pygame
import random
import math

# NOTE:
# This file is a self-contained transition background.
# - It can be executed directly:  python backgrounds/bgSeaToSchool.py
# - It does NOT depend on any game code.
# - It *can* optionally use the existing stage backgrounds (bgSea/bgSchool)
#   because those are backgrounds-only modules.


def _clamp(x, a, b):
    return a if x < a else b if x > b else x


def _smoothstep(t):
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _ease_in_out(t):
    # slightly steeper than smoothstep
    t = _clamp(t, 0.0, 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _draw_alpha_rect(screen, rgba, rect):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill(rgba)
    screen.blit(s, (rect[0], rect[1]))


def _draw_arrow(screen, x1, y1, x2, y2, color, width=6, head_len=22, head_w=16):
    """Draw a simple 2D arrow."""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return
    ux = dx / dist
    uy = dy / dist

    # shorten shaft so the head doesn't overshoot
    sx2 = x2 - ux * head_len
    sy2 = y2 - uy * head_len

    pygame.draw.line(screen, color, (x1, y1), (sx2, sy2), width)

    # head triangle
    # perpendicular
    px = -uy
    py = ux
    left = (sx2 + px * head_w, sy2 + py * head_w)
    right = (sx2 - px * head_w, sy2 - py * head_w)
    pygame.draw.polygon(screen, color, [(x2, y2), left, right])


def _draw_arrow_with_outline(screen, x1, y1, x2, y2, col_rgba, outline_rgba, width=7, head_len=24, head_w=16):
    """Arrow with an outline for maximum contrast on any background."""
    # outline first
    _draw_arrow(screen, x1, y1, x2, y2, outline_rgba, width=width + 6, head_len=head_len + 6, head_w=head_w + 6)
    _draw_arrow(screen, x1, y1, x2, y2, col_rgba, width=width, head_len=head_len, head_w=head_w)


class _Foam:
    """Simple foam particles used near the 'surface' during transition."""

    def __init__(self, w, h, rng: random.Random):
        self.w = w
        self.h = h
        self.rng = rng
        self.reset(spawn_top=True)

    def reset(self, spawn_top=False):
        self.x = self.rng.uniform(0, self.w)
        self.y = self.rng.uniform(-50, 40) if spawn_top else self.rng.uniform(0, self.h)
        self.r = self.rng.uniform(3, 10)
        self.vx = self.rng.uniform(-25, -8)
        self.vy = self.rng.uniform(10, 55)
        self.a = self.rng.uniform(35, 110)
        self.wob = self.rng.uniform(0.8, 2.2)
        self.ph = self.rng.uniform(0, math.tau)

    def update(self, dt, intensity=1.0):
        self.ph += dt * self.wob
        self.x += self.vx * dt * (0.6 + 0.9 * intensity) + math.sin(self.ph) * 18.0 * dt
        self.y += self.vy * dt * (0.7 + 1.2 * intensity)
        if self.x < -30:
            self.x = self.w + 30
        if self.y > self.h + 60:
            self.reset(spawn_top=True)

    def draw(self, screen):
        col = (245, 250, 255, int(self.a))
        pygame.draw.circle(screen, col, (int(self.x), int(self.y)), int(self.r))
        pygame.draw.circle(screen, (255, 255, 255, int(self.a * 0.55)), (int(self.x - self.r * 0.35), int(self.y - self.r * 0.2)), max(1, int(self.r * 0.35)))


class SeaToSchoolTransitionBackground:
    """Stage1(bgSea) -> Transition -> Stage2(bgSchool) background.

    Interface:
        bg = SeaToSchoolTransitionBackground(w, h)
        bg.update(dt)
        bg.draw(screen)

    The transition is purely visual and does not control stage switching.
    Use bg.is_done() to know when to switch to bgSchool in your game.
    """

    def __init__(
        self,
        w,
        h,
        seed=1,
        duration=4.8,
        show_text=True,
        text="STAGE 2: CAMPUS",
        show_diagram=True,
        diagram_scale=1.25,
        diagram_center=True,
        diagram_hold_mult=3.0,
        diagram_center_y=0.44,
        text_scale=1.25,
    ):
        self.w = w
        self.h = h
        self.duration = float(duration)
        self.show_text = bool(show_text)
        self.text = text
        self.show_diagram = bool(show_diagram)
        self.diagram_scale = float(diagram_scale)
        self.diagram_center = bool(diagram_center)
        self.diagram_hold_mult = float(diagram_hold_mult)
        self.diagram_center_y = float(diagram_center_y)
        self.text_scale = float(text_scale)

        self.t = 0.0
        self.rng = random.Random(seed)

        # Import stage backgrounds (still background-only, so it's safe).
        # When executed directly as a script, relative imports are not available,
        # so we fall back to absolute imports.
        try:
            from .bgSea import UnderwaterBackground
            from .bgSchool import CampusBackground
        except Exception:
            from bgSea import UnderwaterBackground
            from bgSchool import CampusBackground

        self.sea = UnderwaterBackground(w, h, seed=seed, fish_count=14, jelly_count=6)
        self.school = CampusBackground(w, h, seed=seed)

        # overlay surfaces
        self._overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # foam particles for 'surface splash' vibe
        self.foam = [_Foam(w, h, self.rng) for _ in range(32)]

        # arrow flow particles for the transition diagram
        self._flow = []
        for _ in range(18):
            self._flow.append({
                "t": self.rng.random(),
                "spd": self.rng.uniform(0.7, 1.45),
                "r": self.rng.uniform(2.0, 4.5),
                "a": self.rng.uniform(110, 220),
            })

        # Fonts: use pygame system fonts (no external assets)
        try:
            # Scale up a bit to improve readability
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

        # Keep animating both so the cross-fade feels alive.
        self.sea.update(dt)
        # Make campus a little lively during transition
        self.school.update(dt, speed=82.0)

        # flow particles move even if diagram is hidden (cheap)
        for p in self._flow:
            p["t"] = (p["t"] + dt * p["spd"] * 0.85) % 1.0

    def _phase(self):
        """Return phase values used by draw()."""
        # Timeline breakdown (seconds)
        # 0.0 - 2.2 : underwater + 'rise' brightening
        # 2.2 - (2.2+H) : surface sparkle + diagram/message (hold)
        # (2.2+H) - (2.2+H+0.6) : water splash punch + white flash -> crossfade
        # then : campus fade-in
        t = self.t
        d = self.duration
        a = 0.0
        b = 0.0
        c = 0.0
        hold = 1.4 * max(0.5, self.diagram_hold_mult)
        t1 = 2.2
        t2 = t1 + hold
        t3 = t2 + 0.6

        if t <= t1:
            a = _smoothstep(t / t1)              # underwater rise 0..1
        elif t <= t2:
            # Make it appear quickly (readability) then hold.
            #  - first 0.25s: ramp up
            #  - rest: stay near 1
            ramp = 0.25
            if t <= t1 + ramp:
                tt = _clamp((t - t1) / ramp, 0.0, 1.0)
                b = _smoothstep(tt)
            else:
                b = 1.0
        elif t <= t3:
            c = _smoothstep((t - t2) / max(0.001, (t3 - t2)))  # splash/flash/crossfade 0..1
        else:
            pass

        # overall normalized
        n = _clamp(t / max(0.001, d), 0.0, 1.0)
        return a, b, c, n

    def _draw_rise_tint(self, screen, rise_amt):
        """Brighten towards the surface + add slight cyan bloom."""
        rise_amt = _clamp(rise_amt, 0.0, 1.0)
        if rise_amt <= 0.0:
            return
        # Add soft bloom overlay (cyan-ish)
        a = int(30 + 85 * rise_amt)
        _draw_alpha_rect(screen, (200, 245, 255, a), (0, 0, self.w, self.h))
        # Add top haze like surface light
        haze_h = int(self.h * (0.22 + 0.15 * rise_amt))
        haze_a = int(25 + 110 * rise_amt)
        _draw_alpha_rect(screen, (255, 255, 255, haze_a), (0, 0, self.w, haze_h))

    def _draw_surface_fx(self, screen, amt):
        """Foam particles + a moving surface line."""
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return

        # Surface line
        y0 = int(self.h * (0.18 + 0.06 * math.sin(self.t * 2.6)))
        # Two layered lines to look like ripples
        for k in range(3):
            y = y0 + k * 3
            a = int((120 - k * 25) * amt)
            pygame.draw.line(screen, (245, 250, 255, a), (0, y), (self.w, y), 2)

        # Foam particles drifting down
        intensity = 0.6 + 1.2 * amt
        for f in self.foam:
            f.update(1 / 60.0, intensity=intensity)
            # Only draw near the top for 'surface' feel
            if f.y < self.h * 0.45:
                f.draw(screen)

        # A little vignette removal (make it airy)
        a = int(35 * amt)
        _draw_alpha_rect(screen, (255, 255, 255, a), (0, 0, self.w, self.h))

        # Add subtle radial bloom in the upper area (more 'transition' feeling)
        bloom = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        cx = int(self.w * 0.5)
        cy = int(self.h * 0.18)
        for r in (220, 160, 110, 70):
            aa = int((22 + (220 - r) * 0.12) * amt)
            pygame.draw.circle(bloom, (235, 250, 255, aa), (cx, cy), r)
        screen.blit(bloom, (0, 0))

    def _draw_message(self, screen, amt):
        if not self.show_text:
            return
        if self.font is None:
            return
        # For readability, don't fade this in too slowly.
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return

        # snap-ish fade to avoid slow gradient (user request)
        amt = _clamp(amt * 1.8, 0.0, 1.0)

        # panel (bigger for readability)
        panel_w = int(self.w * 0.72)
        panel_h = int(self.h * 0.18)
        x = (self.w - panel_w) // 2
        # If the diagram is centered (main focus), move the message down
        # so it doesn't overlap.
        y = int(self.h * (0.68 if self.diagram_center else 0.40))

        alpha = int(230 * amt)
        border_a = int(220 * amt)
        # Slightly darker panel than pure white to reduce glare and improve contrast
        _draw_alpha_rect(screen, (240, 248, 255, alpha), (x, y, panel_w, panel_h))
        pygame.draw.rect(screen, (70, 95, 120, border_a), (x, y, panel_w, panel_h), 3, border_radius=14)

        # text
        col = (20, 35, 55)
        txt = self.font.render(self.text, True, col)
        tx = x + (panel_w - txt.get_width()) // 2
        ty = y + int(panel_h * 0.22)
        # subtle shadow
        shadow = self.font.render(self.text, True, (255, 255, 255))
        shadow.set_alpha(int(140 * amt))
        screen.blit(shadow, (tx + 2, ty + 2))
        screen.blit(txt, (tx, ty))

        if self.font_small is not None:
            sub = self.font_small.render("CLEARED!", True, (20, 35, 55))
            sub.set_alpha(int(235 * amt))
            screen.blit(sub, (x + 22, y + int(panel_h * 0.62)))

    def _draw_transition_diagram(self, screen, amt):
        """Draw a simple visual diagram: [SEA] -> [CAMPUS] with an arrow."""
        if not self.show_diagram:
            return
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return

        # snap-ish fade to avoid slow gradient (user request)
        amt = _clamp(amt * 1.8, 0.0, 1.0)

        w, h = self.w, self.h

        # Place the diagram (optionally centered; user requested main focus).
        s = max(0.7, self.diagram_scale)
        cy = int(h * _clamp(self.diagram_center_y, 0.20, 0.70)) if self.diagram_center else int(h * 0.315)
        box_w = int(w * 0.22 * s)
        box_h = int(h * 0.105 * s)
        gap = int(w * 0.055 * s)
        total_w = box_w * 2 + gap
        x0 = (w - total_w) // 2

        sea_rect = pygame.Rect(x0, cy - box_h // 2, box_w, box_h)
        sch_rect = pygame.Rect(x0 + box_w + gap, cy - box_h // 2, box_w, box_h)

        # panel style matches Campus palette (slate border)
        panel_a = int(235 * amt)
        border_a = int(220 * amt)
        border = (70, 95, 120, border_a)

        # sea box
        _draw_alpha_rect(screen, (235, 250, 255, panel_a), (sea_rect.x, sea_rect.y, sea_rect.w, sea_rect.h))
        pygame.draw.rect(screen, border, sea_rect, 3, border_radius=12)
        # small icon-ish wave
        wave_col = (30, 135, 190, int(235 * amt))
        for i in range(3):
            y = sea_rect.y + int(sea_rect.h * (0.55 + i * 0.12))
            pygame.draw.arc(
                screen,
                wave_col,
                (sea_rect.x + 16, y - 10, sea_rect.w - 32, 20),
                math.pi,
                math.tau,
                3,
            )

        # school box
        _draw_alpha_rect(screen, (235, 250, 255, panel_a), (sch_rect.x, sch_rect.y, sch_rect.w, sch_rect.h))
        pygame.draw.rect(screen, border, sch_rect, 3, border_radius=12)
        # small building icon
        bcol = (115, 140, 165, int(230 * amt))
        bx = sch_rect.x + 18
        by = sch_rect.y + 18
        pygame.draw.rect(screen, bcol, (bx, by + 10, sch_rect.w - 36, sch_rect.h - 34), border_radius=6)
        pygame.draw.polygon(
            screen,
            bcol,
            [(bx, by + 12), (bx + sch_rect.w - 36, by + 12), (bx + (sch_rect.w - 36) / 2, by - 2)],
        )

        # arrow between boxes (make it bolder / high-contrast)
        ax1 = sea_rect.right + 8
        ay = sea_rect.centery
        ax2 = sch_rect.left - 8
        # animate arrow 'flow'
        pulse = 0.55 + 0.45 * math.sin(self.t * 8.0)
        arrow_a = int((190 + 65 * pulse) * amt)
        # bright arrow with dark outline
        arrow_col = (255, 255, 255, arrow_a)
        outline = (10, 20, 35, int(210 * amt))
        _draw_arrow_with_outline(screen, ax1, ay, ax2, ay, arrow_col, outline, width=8, head_len=26, head_w=18)

        # particles flowing along the arrow (makes the transition feel obvious)
        for p in self._flow:
            tt = p["t"]
            # slight bobbing
            y = ay + math.sin(self.t * 9.0 + tt * math.tau) * 5.0
            x = ax1 + (ax2 - ax1) * tt
            a = int(p["a"] * amt)
            # outlined particles
            pygame.draw.circle(screen, (10, 20, 35, int(a * 0.95)), (int(x), int(y)), int(p["r"] + 2))
            pygame.draw.circle(screen, (255, 255, 255, a), (int(x), int(y)), int(p["r"]))
            pygame.draw.circle(screen, (200, 245, 255, int(a * 0.55)), (int(x - 2), int(y - 1)), max(1, int(p["r"] * 0.7)))

        # labels if font exists
        if self.font_small is not None:
            lbl_a = int(240 * amt)
            sea_lbl = self.font_small.render("SEA", True, (20, 35, 55))
            sea_lbl.set_alpha(lbl_a)
            screen.blit(sea_lbl, (sea_rect.centerx - sea_lbl.get_width() // 2, sea_rect.centery - sea_lbl.get_height() // 2))

            sch_lbl = self.font_small.render("CAMPUS", True, (20, 35, 55))
            sch_lbl.set_alpha(lbl_a)
            screen.blit(sch_lbl, (sch_rect.centerx - sch_lbl.get_width() // 2, sch_rect.centery - sch_lbl.get_height() // 2))

    def _draw_splash_punch(self, screen, amt):
        """Big, obvious water splash overlay used right before switching to campus."""
        amt = _clamp(amt, 0.0, 1.0)
        if amt <= 0.0:
            return

        w, h = self.w, self.h

        # Centered near top third (like breaking the surface)
        cx = int(w * 0.5)
        cy = int(h * 0.20)

        splash = pygame.Surface((w, h), pygame.SRCALPHA)

        # expanding rings
        for i, base in enumerate((40, 85, 135, 190, 250)):
            r = int(base * (0.6 + 1.25 * amt))
            a = int((180 - i * 28) * (1.0 - 0.15 * i) * amt)
            a = _clamp(a, 0, 255)
            pygame.draw.circle(splash, (245, 250, 255, a), (cx, cy), r, 8)

        # big droplets (arcs of circles)
        drop_n = 22
        for k in range(drop_n):
            ang = -math.pi + (k / (drop_n - 1)) * math.pi
            spread = 1.0 + 0.3 * math.sin(self.t * 14.0 + k)
            rr = self.rng.uniform(3.0, 7.0) * (1.0 + 1.6 * amt)
            dist = (95 + 190 * amt) * spread
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist * 0.65
            a = int(210 * amt)
            pygame.draw.circle(splash, (255, 255, 255, a), (int(x), int(y)), int(rr))

        # a horizontal 'surface tear'
        tear_y = cy + int(30 + 18 * math.sin(self.t * 18.0))
        for k in range(5):
            aa = int((140 - k * 22) * amt)
            pygame.draw.line(splash, (255, 255, 255, aa), (0, tear_y + k * 2), (w, tear_y + k * 2), 4)

        screen.blit(splash, (0, 0))

    def draw(self, screen):
        # Phase values
        rise_amt, surface_amt, flash_amt, n = self._phase()

        # Always start from sea background
        self.sea.draw(screen)
        self._draw_rise_tint(screen, rise_amt)

        # Surface effects and message during mid
        self._draw_surface_fx(screen, surface_amt)

        # If diagram should be the main focus, dim the background behind it.
        if self.diagram_center and surface_amt > 0.0:
            # stronger dim for readability
            dim = int(155 * surface_amt)
            _draw_alpha_rect(screen, (0, 0, 0, dim), (0, 0, self.w, self.h))

        self._draw_transition_diagram(screen, surface_amt)
        self._draw_message(screen, surface_amt)

        # Flash + crossfade into campus
        # flash_amt (0..1): at 0 we are still sea; at 1 we are ready to show campus.
        if flash_amt > 0.0:
            # Big, obvious splash punch before the flash (visual cue)
            self._draw_splash_punch(screen, flash_amt)

            # White flash peak around the middle
            peak = math.sin(math.pi * _clamp(flash_amt, 0.0, 1.0))  # 0..1..0
            a = int(245 * peak)
            _draw_alpha_rect(screen, (255, 255, 255, a), (0, 0, self.w, self.h))

            # Stronger transition punch: quick zoom + slight shake during the flash
            punch = peak
            zoom = 1.0 + 0.04 * punch
            if zoom > 1.0:
                tmp = pygame.transform.smoothscale(screen, (int(self.w * zoom), int(self.h * zoom)))
                sx = (tmp.get_width() - self.w) // 2
                sy = (tmp.get_height() - self.h) // 2
                # shake
                shx = int(math.sin(self.t * 70.0) * 4.0 * punch)
                shy = int(math.cos(self.t * 63.0) * 3.0 * punch)
                screen.blit(tmp, (-sx + shx, -sy + shy))

            # Crossfade
            # draw campus onto overlay then blend
            self._overlay.fill((0, 0, 0, 0))
            self.school.draw(self._overlay)
            blend = _ease_in_out(flash_amt)
            self._overlay.set_alpha(int(255 * blend))
            screen.blit(self._overlay, (0, 0))

        # Final campus settle (extra fade-in after crossfade)
        # n near end: add a small fade-in from dark to normal
        if n > 0.70:
            settle = _smoothstep((n - 0.70) / 0.30)
            a = int((1.0 - settle) * 90)
            _draw_alpha_rect(screen, (0, 0, 0, a), (0, 0, self.w, self.h))


def run_demo(w=960, h=540):
    pygame.init()
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Sea -> School Transition")
    clock = pygame.time.Clock()

    # Make duration long enough to include the diagram hold.
    bg = SeaToSchoolTransitionBackground(
        w,
        h,
        seed=7,
        duration=9.0,
        show_text=True,
        diagram_center=True,
        diagram_center_y=0.44,
        diagram_hold_mult=3.0,
        diagram_scale=1.25,
        text_scale=1.35,
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

        # When used inside your game, you would switch to the stage-2 background
        # once this transition is done. For the standalone demo, show the campus
        # background after completion so the end state is obvious.
        if bg.is_done():
            # draw campus only for a short while then loop
            # (keeps the demo self-running)
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

                bg.school.update(ddt, speed=85.0)
                bg.school.draw(screen)
                pygame.display.flip()

            bg.restart()

    pygame.quit()


if __name__ == "__main__":
    run_demo()
