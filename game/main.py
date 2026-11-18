import pygame
import math

from game.enemies.virus_enemy import spawn_for_segment
from game.player.player_stub import PlayerStub


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

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
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

        # draw
        screen.fill((11, 18, 32))
        pygame.draw.rect(screen, (12, 42, 27), pygame.Rect(0, GROUND_Y, W, H - GROUND_Y))
        pygame.draw.line(screen, (31, 107, 69), (0, GROUND_Y), (W, GROUND_Y), 2)

        for i in range(0, WORLD_W + 1, SEGMENT_W):
            x = int(i - cam_x)
            pygame.draw.line(screen, (30, 40, 60), (x, 0), (x, H), 1)

        for en in enemies:
            en.draw(screen, cam_x, global_t=global_t)
        for b in projectiles:
            b.draw(screen, cam_x)
        player.draw(screen, cam_x)

        txt = font.render(
            f"Segment={seg} Theme={theme['name']} (player is hidden stub)",
            True,
            (203, 213, 225),
        )
        screen.blit(txt, (18, 14))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
