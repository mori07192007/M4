import pygame
import math

from game.enemies.virus_enemy import spawn_for_segment
from game.player.player_stub import PlayerStub

# Backgrounds (drawn at the very back)
# bgStart.py contains multiple start screen implementations.
# Use the latest/active one here.
from game.backgrounds.bgStart import StartScreenNeoFuturistic
from game.backgrounds.bgSea import UnderwaterBackground
from game.backgrounds.bgUniverse import Background as UniverseBackground
from game.backgrounds.bgHappyend import EndRollScreen

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
from game.backgrounds.layer2_3 import SchoolToUniverseTransitionBackground
from game.collision import collision as collision_game


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
    SCENE_TRANSITION_2_3 = "transition_2_3"
    SCENE_UNIVERSE = "universe"
    SCENE_HAPPYEND = "happyend"
    scene = SCENE_START

    # When collision game ends with GAME OVER, wait 3 seconds then go back to START.
    gameover_return_timer = None  # None or seconds remaining
    # When collision game is cleared, wait 3 seconds then go to the layer1->2 transition.
    clear_to_transition_timer = None  # None or seconds remaining
    # When collision game is cleared in stage-2, wait 3 seconds then go to layer2->3 transition.
    clear2_to_transition_timer = None

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
    trans_2_3 = SchoolToUniverseTransitionBackground(
        W,
        H,
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
    school_bg = CampusBackground(W, H, seed=3)
    universe_bg = UniverseBackground(W, H, scroll_dir="left")
    happyend_bg = EndRollScreen(W, H)

    # ---- collision mini-game (runs on top of bgSea) ----
    # collision.py was originally a standalone pygame script.
    # We initialize it for our window size and call step_collision() per-frame.
    collision_game.init_collision(W, H)
    # collision uses an image file for the player sprite.
    # Load it once here (path relative to this file).
    try:
        # Asset is stored at the M4 project root (confirmed: /home/moe7514/M4/player_idle.png)
        player_img_path = Path(__file__).resolve().parents[1] / "player_idle.png"
        collision_game.player_img = pygame.image.load(str(player_img_path))
        collision_game.player_img = pygame.transform.scale(collision_game.player_img, (80, 80))
    except FileNotFoundError:
        # Fallback: simple rect surface if asset is missing.
        surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 220, 60), (0, 0, 80, 80), border_radius=10)
        pygame.draw.circle(surf, (20, 20, 30), (28, 30), 6)
        pygame.draw.circle(surf, (20, 20, 30), (52, 30), 6)
        collision_game.player_img = surf
    collision_game._reset_game_state()

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
            # If we came back from game over, ensure collision game state is reset.
            gameover_return_timer = None
            clear_to_transition_timer = None
            clear2_to_transition_timer = None
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
                    collision_game._reset_game_state()
                    clear_to_transition_timer = None
                    clear2_to_transition_timer = None

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
        # NOTE: If collision game is in GAME OVER countdown, freeze the platformer side
        # (player/enemies/projectiles) but keep drawing it as-is under the overlays.

        # draw (background -> collision game -> characters -> UI)
        # 1) far background (lowest layer)
        #    NOTE: background modules are screen-space, not world-space, so we don't apply cam_x.
        sea_bg.update(dt)
        sea_bg.draw(screen)

        # 2) collision mini-game runs while bgSea is active
        #    (collision draws without clearing the background)
        coll_state = collision_game.step_collision(dt, events, keys, screen, draw_background=False)

        # If collision game is in GAME OVER state, start a 3-second countdown.
        # During the countdown we keep showing the sea background + the game-over overlay.
        if coll_state.get("pc_hp", 1) <= 0:
            if gameover_return_timer is None:
                gameover_return_timer = 3.0

        # If collision game is CLEAR, start a 3-second countdown to the layer1->2 transition.
        if coll_state.get("game_clear"):
            if clear_to_transition_timer is None:
                clear_to_transition_timer = 3.0

        # Freeze platformer side during either countdown.
        platformer_frozen = (gameover_return_timer is not None) or (clear_to_transition_timer is not None)

        if not platformer_frozen:
            player.update(dt, keys, gravity=GRAVITY, world_w=WORLD_W)
            player_x_for_cam = float(player.x)

            cam_x = clamp(player_x_for_cam - W * 0.40, 0, WORLD_W - W)

            seg = segment_index(player_x_for_cam)
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

            # update projectiles
            for b in projectiles:
                b.update(dt, GROUND_Y)
            projectiles = [b for b in projectiles if b.life > 0]
        else:
            # safe defaults for draw/UI if frozen
            player_x_for_cam = float(getattr(player, "x", 0.0))
            cam_x = clamp(player_x_for_cam - W * 0.40, 0, WORLD_W - W)
            seg = segment_index(player_x_for_cam)
            theme = theme_for_segment(seg)

        # While counting down, show a simple overlay and return to start when done.
        if gameover_return_timer is not None:
            gameover_return_timer -= dt
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            msg = font.render(f"Returning to Start in {max(0.0, gameover_return_timer):.1f}s", True, (255, 255, 255))
            screen.blit(msg, (18, 40))
            if gameover_return_timer <= 0:
                scene = SCENE_START
                collision_game._reset_game_state()
                # (optional) also reset platformer-ish state
                player = PlayerStub(x=80.0, ground_y=GROUND_Y)
                enemies = []
                projectiles = []
                spawned_segments = set()
                global_t = 0.0
                # ensure countdown is cleared
                gameover_return_timer = None

        # While counting down after CLEAR, keep the screen as-is and then move to transition.
        if clear_to_transition_timer is not None:
            clear_to_transition_timer -= dt
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 90))
            screen.blit(overlay, (0, 0))
            msg = font.render(
                f"CLEAR! Moving to next stage in {max(0.0, clear_to_transition_timer):.1f}s",
                True,
                (255, 255, 255),
            )
            screen.blit(msg, (18, 66))
            if clear_to_transition_timer <= 0:
                scene = SCENE_TRANSITION_1_2
                trans_1_2.restart()
                clear_to_transition_timer = None

        # NOTE:
        # Transition to layer1-2 is triggered ONLY by the collision mini-game clear now.
        # (We no longer transition when the platformer player reaches the end of the world.)

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
                # After leaving the transition, start stage-2 (bgSchool) and restart collision
                # mini-game from a fresh state.
                collision_game._reset_game_state()
                gameover_return_timer = None
                clear_to_transition_timer = None
                clear2_to_transition_timer = None
                scene = SCENE_SCHOOL

        # -----------------------
        # Scene: SCHOOL (bgSchool)
        # -----------------------
        while running and scene == SCENE_SCHOOL:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            events2 = pygame.event.get()
            for e in events2:
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            # background first (always backmost)
            school_bg.update(dt, speed=85.0)
            school_bg.draw(screen)

            # Run collision mini-game again on top of bgSchool (stage 2)
            keys2 = pygame.key.get_pressed()
            coll_state2 = collision_game.step_collision(dt, events2, keys2, screen, draw_background=False)

            # Stage-2 CLEAR handling: wait 3 seconds, then go to layer2->3 transition.
            if coll_state2.get("game_clear"):
                if clear2_to_transition_timer is None:
                    clear2_to_transition_timer = 3.0

            # Stage-2 GAME OVER handling: wait 3 seconds, then return to START.
            if coll_state2.get("pc_hp", 1) <= 0:
                if gameover_return_timer is None:
                    gameover_return_timer = 3.0

            if gameover_return_timer is not None:
                gameover_return_timer -= dt
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120))
                screen.blit(overlay, (0, 0))
                msg = font.render(
                    f"Returning to Start in {max(0.0, gameover_return_timer):.1f}s",
                    True,
                    (255, 255, 255),
                )
                screen.blit(msg, (18, 40))
                if gameover_return_timer <= 0:
                    scene = SCENE_START
                    collision_game._reset_game_state()
                    # reset platformer-ish state too
                    player = PlayerStub(x=80.0, ground_y=GROUND_Y)
                    enemies = []
                    projectiles = []
                    spawned_segments = set()
                    global_t = 0.0
                    gameover_return_timer = None
                    clear_to_transition_timer = None
                    clear2_to_transition_timer = None

            if clear2_to_transition_timer is not None:
                clear2_to_transition_timer -= dt
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 90))
                screen.blit(overlay, (0, 0))
                msg = font.render(
                    f"CLEAR! Moving to next stage in {max(0.0, clear2_to_transition_timer):.1f}s",
                    True,
                    (255, 255, 255),
                )
                screen.blit(msg, (18, 66))
                if clear2_to_transition_timer <= 0:
                    scene = SCENE_TRANSITION_2_3
                    trans_2_3.restart()
                    # reset collision so it does not keep CLEAR state into the transition
                    collision_game._reset_game_state()
                    gameover_return_timer = None
                    clear_to_transition_timer = None
                    clear2_to_transition_timer = None

            # (optional) keep running the same gameplay on top of bgSchool.
            # For now, just show the stage label.
            txt2 = font.render("STAGE 2 (School) - ESC to quit", True, (15, 15, 20))
            screen.blit(txt2, (18, 14))
            pygame.display.flip()

            # If we switched scenes during this frame, break out of the SCHOOL loop
            # so the START scene can render immediately.
            if scene != SCENE_SCHOOL:
                break

        # -----------------------
        # Scene: TRANSITION 2->3 (layer2-3)
        # -----------------------
        while running and scene == SCENE_TRANSITION_2_3:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            trans_2_3.update(dt)
            trans_2_3.draw(screen)
            pygame.display.flip()

            if trans_2_3.is_done():
                # Start Stage 3 (Universe)
                collision_game._reset_game_state()
                gameover_return_timer = None
                clear_to_transition_timer = None
                clear2_to_transition_timer = None
                scene = SCENE_UNIVERSE

        # -----------------------
        # Scene: UNIVERSE (bgUniverse)
        # -----------------------
        while running and scene == SCENE_UNIVERSE:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            events3 = pygame.event.get()
            for e in events3:
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            universe_bg.update(dt)
            universe_bg.draw(screen)

            keys3 = pygame.key.get_pressed()
            coll_state3 = collision_game.step_collision(dt, events3, keys3, screen, draw_background=False)

            # Universe stage CLEAR -> go to happy end roll
            if coll_state3.get("game_clear"):
                collision_game._reset_game_state()
                gameover_return_timer = None
                clear_to_transition_timer = None
                clear2_to_transition_timer = None
                # restart end roll
                happyend_bg = EndRollScreen(W, H)
                scene = SCENE_HAPPYEND

            # Universe stage GAME OVER -> wait 3 seconds (keep the same screen) -> START
            if coll_state3.get("pc_hp", 1) <= 0:
                if gameover_return_timer is None:
                    gameover_return_timer = 3.0

            if gameover_return_timer is not None:
                gameover_return_timer -= dt
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120))
                screen.blit(overlay, (0, 0))
                msg = font.render(
                    f"Returning to Start in {max(0.0, gameover_return_timer):.1f}s",
                    True,
                    (255, 255, 255),
                )
                screen.blit(msg, (18, 40))
                if gameover_return_timer <= 0:
                    scene = SCENE_START
                    collision_game._reset_game_state()
                    # reset platformer-ish state too
                    player = PlayerStub(x=80.0, ground_y=GROUND_Y)
                    enemies = []
                    projectiles = []
                    spawned_segments = set()
                    global_t = 0.0
                    gameover_return_timer = None
                    clear_to_transition_timer = None
                    clear2_to_transition_timer = None

            txt3 = font.render("STAGE 3 (Universe) - ESC to quit", True, (240, 240, 255))
            screen.blit(txt3, (18, 14))
            pygame.display.flip()

            if scene != SCENE_UNIVERSE:
                break

        # -----------------------
        # Scene: HAPPY END (bgHappyend)
        # -----------------------
        while running and scene == SCENE_HAPPYEND:
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    # allow click to finish immediately
                    running = False

            happyend_bg.update(dt)
            happyend_bg.draw(screen)

            # When end roll finishes, return to START.
            if getattr(happyend_bg, "finished", False):
                running = False

            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
