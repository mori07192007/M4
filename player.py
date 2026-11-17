import pygame
import random

pygame.init()

# =========================
# 画面設定
# =========================
WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("大西先生 VS ウイルス")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 40)
big_font = pygame.font.Font(None, 80)

# =========================
# プレイヤー
# =========================
player_x = 200
player_y = 250

base_speed = 6
player_speed = base_speed

# =========================
# HP
# =========================
pc_hp = 100

# =========================
# スコア
# =========================
score = 0

# =========================
# 必殺技ゲージ
# =========================
special_gauge = 0
MAX_GAUGE = 5

# =========================
# ウイルス
# =========================
viruses = []

spawn_timer = 0

boss_spawned = False

# =========================
# アイテム
# =========================
items = []

item_timer = 0

vaccine_mode = False
vaccine_timer = 0

ssd_timer = 0

# =========================
# 攻撃
# =========================
attack = False
attack_timer = 0

running = True
game_clear = False

while running:

    clock.tick(60)

    # 難易度上昇
    game_time = pygame.time.get_ticks() // 1000

    speed_bonus = game_time // 60

    # ---------------------
    # イベント
    # ---------------------
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # 通常攻撃
            if event.key == pygame.K_SPACE:
                attack = True
                attack_timer = 10

            # 必殺技
            if event.key == pygame.K_RETURN:

                if special_gauge >= MAX_GAUGE:

                    viruses.clear()
                    special_gauge = 0

    # ---------------------
    # 移動
    # ---------------------
    keys = pygame.key.get_pressed()

    if keys[pygame.K_UP]:
        player_y -= player_speed

    if keys[pygame.K_DOWN]:
        player_y += player_speed

    if keys[pygame.K_LEFT]:
        player_x -= player_speed

    if keys[pygame.K_RIGHT]:
        player_x += player_speed

    player_x = max(0, min(player_x, WIDTH - 80))
    player_y = max(0, min(player_y, HEIGHT - 80))

    # ---------------------
    # ウイルス生成
    # ---------------------
    spawn_timer += 1

    if spawn_timer >= 60:

        r = random.randint(1, 100)

        if score >= 15 and not boss_spawned:

            viruses.append({
                "x": WIDTH,
                "y": HEIGHT // 2,
                "speed": 3,
                "hp": 10,
                "type": "boss"
            })

            boss_spawned = True

        elif r <= 75:

            viruses.append({
                "x": WIDTH,
                "y": random.randint(50, 550),
                "speed": 4 + speed_bonus,
                "hp": 1,
                "type": "normal"
            })

        else:

            viruses.append({
                "x": WIDTH,
                "y": random.randint(50, 550),
                "speed": 6 + speed_bonus,
                "hp": 2,
                "type": "strong"
            })

        spawn_timer = 0

    # ---------------------
    # アイテム生成
    # ---------------------
    item_timer += 1

    if item_timer >= 600:

        item_type = random.choice(
            ["patch", "vaccine", "ssd"]
        )

        items.append({
            "x": WIDTH,
            "y": random.randint(50, 550),
            "type": item_type
        })

        item_timer = 0

    # ---------------------
    # アイテム移動
    # ---------------------
    player_rect = pygame.Rect(
        player_x,
        player_y,
        80,
        80
    )

    for item in items[:]:

        item["x"] -= 4

        item_rect = pygame.Rect(
            item["x"],
            item["y"],
            40,
            40
        )

        if player_rect.colliderect(item_rect):

            if item["type"] == "patch":
                pc_hp = min(100, pc_hp + 20)

            elif item["type"] == "vaccine":
                vaccine_mode = True
                vaccine_timer = 600

            elif item["type"] == "ssd":
                player_speed = 10
                ssd_timer = 600

            items.remove(item)

    # ---------------------
    # ウイルス移動
    # ---------------------
    for virus in viruses[:]:

        virus["x"] -= virus["speed"]

        if virus["x"] < 70:

            if virus["type"] == "boss":
                pc_hp -= 30
            elif virus["type"] == "strong":
                pc_hp -= 15
            else:
                pc_hp -= 10

            viruses.remove(virus)

    # ---------------------
    # 攻撃
    # ---------------------
    if attack:

        attack_timer -= 1

        attack_width = 300 if vaccine_mode else 150

        attack_rect = pygame.Rect(
            player_x + 80,
            player_y,
            attack_width,
            80
        )

        for virus in viruses[:]:

            virus_rect = pygame.Rect(
                virus["x"] - 25,
                virus["y"] - 25,
                50,
                50
            )

            if attack_rect.colliderect(virus_rect):

                virus["hp"] -= 1

                if virus["hp"] <= 0:

                    if virus["type"] == "normal":
                        score += 1

                    elif virus["type"] == "strong":
                        score += 3

                    elif virus["type"] == "boss":
                        game_clear = True

                    viruses.remove(virus)

                    special_gauge = min(
                        MAX_GAUGE,
                        special_gauge + 1
                    )

        if attack_timer <= 0:
            attack = False

    # ワクチン終了
    if vaccine_mode:

        vaccine_timer -= 1

        if vaccine_timer <= 0:
            vaccine_mode = False

    # SSD終了
    if player_speed > base_speed:

        ssd_timer -= 1

        if ssd_timer <= 0:
            player_speed = base_speed

    # ---------------------
    # 描画
    # ---------------------
    screen.fill((220, 240, 255))

    # パソコン
    pygame.draw.rect(
        screen,
        (80, 80, 80),
        (20, 250, 60, 80)
    )

    # プレイヤー
    pygame.draw.rect(
        screen,
        (0, 100, 255),
        (player_x, player_y, 80, 80)
    )

    # 攻撃
    if attack:

        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (
                player_x + 80,
                player_y,
                300 if vaccine_mode else 150,
                80
            )
        )

    # ウイルス
    for virus in viruses:

        if virus["type"] == "normal":
            color = (255, 0, 0)

        elif virus["type"] == "strong":
            color = (180, 0, 255)

        else:
            color = (0, 0, 0)

        pygame.draw.circle(
            screen,
            color,
            (int(virus["x"]), int(virus["y"])),
            20
        )

    # アイテム
    for item in items:

        if item["type"] == "patch":
            color = (0, 255, 0)

        elif item["type"] == "vaccine":
            color = (255, 255, 0)

        else:
            color = (0, 255, 255)

        pygame.draw.rect(
            screen,
            color,
            (item["x"], item["y"], 40, 40)
        )

    screen.blit(
        font.render(f"HP: {pc_hp}", True, (0,0,0)),
        (20,20)
    )

    screen.blit(
        font.render(f"SCORE: {score}", True, (0,0,0)),
        (20,60)
    )

    screen.blit(
        font.render(
            f"GAUGE: {special_gauge}/{MAX_GAUGE}",
            True,
            (0,0,0)
        ),
        (20,100)
    )

    # クリア
    if game_clear or score >= 20:

        if pc_hp == 100:
            rank = "S"
        elif pc_hp >= 70:
            rank = "A"
        elif pc_hp >= 40:
            rank = "B"
        else:
            rank = "C"

        screen.blit(
            big_font.render(
                "CLEAR!",
                True,
                (0,200,0)
            ),
            (300,200)
        )

        screen.blit(
            font.render(
                f"RANK : {rank}",
                True,
                (0,0,0)
            ),
            (400,300)
        )

    # ゲームオーバー
    if pc_hp <= 0:

        screen.blit(
            big_font.render(
                "GAME OVER",
                True,
                (255,0,0)
            ),
            (180,250)
        )

    pygame.display.flip()

pygame.quit()