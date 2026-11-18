import pygame
import math

from game.enemies.virus_enemy import spawn_for_segment
from game.player.player_stub import PlayerStub

# Backgrounds (drawn at the very back)
# bgStart.py contains multiple start screen implementations.
# Use the latest/active one here.
from game.backgrounds.bgStart import StartScreenNeoFuturistic
from game.backgrounds.bgSea import UnderwaterBackground

# NOTE:
# The original flow was:
#   Start screen (bgStart) -> click -> Sea background (bgSea)
# This project now wants:
#   Start screen (bgStart) -> click -> Rule/How-to screen (ru-ru)
#
# ru-ru.py is not a valid Python module name to import directly (because of the hyphen),
# so we load it via runpy and call its run() function.
import runpy
from pathlib import Path
from game.backgrounds.bgSchool import CampusBackground
from game.backgrounds.layer1_2 import SeaToSchoolTransitionBackground


# ---- shared config ----
W, H = 960, 540
FPS = 60

GROUND_Y = 460
GRAVITY = 1200.0
WORLD_W = 5200
SEGMENT_W = 960


THEMES = [
    {
        "name": "Pastel",
        "palette": {
            "cute": (255, 150, 220),
            "evil": (190, 120, 255),
            "spore": (170, 255, 240),
        },
    },
    {
        "name": "Toxic",
        "palette": {
            "cute": (255, 210, 120),
            "evil": (120, 255, 120),
            "spore": (60, 220, 160),
        },
    },
    {
        "name": "DeepSea",
        "palette": {
            "cute": (140, 200, 255),
            "evil": (80, 120, 255),
            "spore": (120, 255, 220),
        },
    },
    {
        "name": "Candy",
        "palette": {
            "cute": (255, 120, 160),
            "evil": (255, 110, 255),
            "spore": (255, 220, 140),
        },
    },
]


def theme_for_segment(seg: int):
    return THEMES[seg % len(THEMES)]


def clamp(v, a, b):
    return max(a, min(b, v))


def segment_index(x):
    return int(x // SEGMENT_W)


def aabb(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Integrated Game (player+enemy+bg)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    # ---- scenes ----
    SCENE_START = "start"
    SCENE_RULES = "rules"
    SCENE_SEA = "sea"
    SCENE_TRANSITION_1_2 = "transition_1_2"
    SCENE_SCHOOL = "school"
    scene = SCENE_START

    # ---- background instances (lowest layer) ----
    # NOTE:
    # If you edit bgStart.py while the game is running, Python may keep the old
    # module in memory. Restart the program to see changes.
    # (VS Code/terminal run sessions sometimes look like it's "not reflected".)
    start_screen = StartScreenNeoFuturistic(W, H)
    # Sea background (used after closing the rules screen)
    sea_bg = UnderwaterBackground(W, H, seed=9, fish_count=18, jelly_count=6)
    trans_1_2 = SeaToSchoolTransitionBackground(
        W,
        H,
        seed=7,
        duration=9.0,
        show_text=True,
        diagram_center=True,
        diagram_center_y=0.44,
        diagram_hold_mult=3.0,
        diagram_scale=1.25,
        text_scale=1.35,
    )
    school_bg = CampusBackground(W, H, seed=3)

    player = PlayerStub(x=80.0, ground_y=GROUND_Y)
    enemies = []
    projectiles = []
    spawned_segments = set()

    global_t = 0.0
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 20)
        global_t += dt

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # -----------------------
        # Scene: START (bgStart)
        # -----------------------
        if scene == SCENE_START:
            # Start screen updates/draws only. No player/enemy updates.
            start_screen.update(dt)

            # Click to start => show rules screen (ru-ru.py)
            # IMPORTANT: We must not call pygame.event.get() twice in the same frame,
            # otherwise the first get() consumes events and clicks may be lost.
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    scene = SCENE_RULES
                    # reset some game state on start
                    player = PlayerStub(x=80.0, ground_y=GROUND_Y)
                    enemies = []
                    projectiles = []
                    spawned_segments = set()
                    global_t = 0.0

            # draw
            start_screen.draw(screen)
            pygame.display.flip()
            continue

        # -----------------------
        # Scene: RULES (ru-ru)
        # -----------------------
        if scene == SCENE_RULES:
            # Launch ru-ru.py (standalone screen). When it finishes, continue into SEA.
            rr_path = Path(__file__).resolve().parent / "backgrounds" / "ru-ru.py"
            rr_globals = runpy.run_path(str(rr_path))
            rr_run = rr_globals.get("run")
            if callable(rr_run):
                rr_run()
            else:
                raise RuntimeError("ru-ru.py does not define a callable run()")

            # Restore main window (ru-ru changes the display mode/title).
            screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption("Integrated Game (player+enemy+bg)")

            # When rules screen closes (ESC / window close), continue into SEA.
            scene = SCENE_SEA
            continue

        # -----------------------
        # Scene: SEA (bgSea)
        # -----------------------
        player.update(dt, keys, gravity=GRAVITY, world_w=WORLD_W)

        cam_x = clamp(player.x - W * 0.40, 0, WORLD_W - W)

        seg = segment_index(player.x)
        theme = theme_for_segment(seg)

        if seg not in spawned_segments:
            spawned_segments.add(seg)
            enemies.extend(spawn_for_segment(seg, ground_y=GROUND_Y))

        # update enemies
        for en in enemies:
            en.update(
                dt,
                projectiles,
                global_t=global_t,
                theme_palette=theme.get("palette"),
                player=player,
                ground_y=GROUND_Y,
            )
        enemies = [e for e in enemies if not e.remove]

        # stomp collision
        px, py, pw, ph = player.rect()
        for en in enemies:
            if en.dead:
                continue
            if not aabb(px, py, pw, ph, en.x, en.y, en.w, en.h):
                continue

            player_falling = player.vy > 0
            enemy_top = en.y
            player_bottom_prev = (player.y - player.vy * (1/60.0)) + player.h
            stomped = player_falling and player_bottom_prev <= enemy_top + 12

            if stomped:
                en.stomped()
                player.vy = -360.0
            else:
                player.vx = (-1 if player.x < en.x else 1) * 260.0
                player.vy = -260.0

        # update projectiles
        for b in projectiles:
            b.update(dt, GROUND_Y)
        projectiles = [b for b in projectiles if b.life > 0]

        # draw (background -> characters -> UI)
        # 1) far background (lowest layer)
        #    NOTE: background modules are screen-space, not world-space, so we don't apply cam_x.
        sea_bg.update(dt)
        sea_bg.draw(screen)

        # ---- stage clear condition (temporary) ----
        # PlayerStub does not have built-in clear/gameover rules.
        # For now, we treat reaching the end of the world as "clear".
        if player.x >= WORLD_W - player.w - 2:
            scene = SCENE_TRANSITION_1_2
            trans_1_2.restart()

        # 2) (optional) debug overlay
        # If you want debug segment/grid lines back, re-enable this block.
        # for i in range(0, WORLD_W + 1, SEGMENT_W):
        #     x = int(i - cam_x)
        #     pygame.draw.line(screen, (30, 40, 60), (x, 0), (x, H), 1)

        for en in enemies:
            en.draw(screen, cam_x, global_t=global_t)
        for b in projectiles:
            b.draw(screen, cam_x)
        player.draw(screen, cam_x)

        txt = font.render(
            f"Scene={scene} Segment={seg} Theme={theme['name']}",
            True,
            (203, 213, 225),
        )
        screen.blit(txt, (18, 14))

        pygame.display.flip()

        # -----------------------
        # Scene: TRANSITION 1->2 (layer1-2)
        # -----------------------
        while running and scene == SCENE_TRANSITION_1_2:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            trans_1_2.update(dt)
            trans_1_2.draw(screen)
            pygame.display.flip()

            if trans_1_2.is_done():
                scene = SCENE_SCHOOL

        # -----------------------
        # Scene: SCHOOL (bgSchool)
        # -----------------------
        while running and scene == SCENE_SCHOOL:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            # background first (always backmost)
            school_bg.update(dt, speed=85.0)
            school_bg.draw(screen)

            # (optional) keep running the same gameplay on top of bgSchool.
            # For now, just show the stage label.
            txt2 = font.render("STAGE 2 (School) - ESC to quit", True, (15, 15, 20))
            screen.blit(txt2, (18, 14))
            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
