"""collision.py

もともとは単体実行用の pygame スクリプトでしたが、main.py に統合して
「bgSea を動かしている間も collision のゲームロジックを同じウィンドウ上で動かす」
ために、外から呼べる API を追加しました。

主な追加点:
- init_collision(width, height): 外部(=main.py)の画面サイズに合わせて初期化
- step_collision(dt, events, keys, screen): 1フレーム分の更新＆描画

単体実行 (python collision/collision.py) も従来通り動くようにしています。
"""

import random
import pygame
import math


# =========================
# 画面設定（main.py から上書き可能）
# =========================
WIDTH = 1000
HEIGHT = 600

# main.py 側の display を壊さないため、ここでは set_mode しない。
# 単体実行の場合だけ set_mode する。
screen = None

clock = None
font = None
big_font = None

# プレイヤー画像（main.py 側で差し込む）
player_img = None


def init_collision(width: int, height: int):
    """main.py から呼び出す初期化。

    pygame.init() 自体は main 側でも呼ばれる想定ですが、二重 init でも問題は起きづらいので
    ここでも保険で呼びます。
    """
    global WIDTH, HEIGHT, clock, font, big_font
    WIDTH, HEIGHT = int(width), int(height)

    # pygame の各サブシステム初期化（安全のため）
    if not pygame.get_init():
        pygame.init()

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 40)
    big_font = pygame.font.Font(None, 80)

# =========================
# 図形で“絵っぽく”描く関数（画像ファイル不要）
# =========================


def draw_virus(surface, vtype, x, y):
    """ウイルスを図形の組み合わせで描く（中心座標 x,y）"""
    x = int(x)
    y = int(y)

    if vtype == "normal":
        # 赤いトゲトゲ＋目
        body_color = (230, 40, 40)
        spike_color = (170, 0, 0)
        r = 22

        # トゲ（8方向）
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            pygame.draw.line(surface, spike_color, (x, y), (x + dx * (r + 10), y + dy * (r + 10)), 3)

        pygame.draw.circle(surface, body_color, (x, y), r)
        pygame.draw.circle(surface, (255, 200, 200), (x - 6, y - 4), 5)
        pygame.draw.circle(surface, (255, 200, 200), (x + 6, y - 4), 5)
        pygame.draw.circle(surface, (0, 0, 0), (x - 6, y - 4), 2)
        pygame.draw.circle(surface, (0, 0, 0), (x + 6, y - 4), 2)

    elif vtype == "strong":
        # 紫＋装甲っぽいリング
        body_color = (170, 0, 255)
        r = 24
        pygame.draw.circle(surface, body_color, (x, y), r)
        pygame.draw.circle(surface, (80, 0, 120), (x, y), r, 4)
        pygame.draw.circle(surface, (240, 220, 255), (x - 7, y - 5), 5)
        pygame.draw.circle(surface, (240, 220, 255), (x + 7, y - 5), 5)
        pygame.draw.circle(surface, (0, 0, 0), (x - 7, y - 5), 2)
        pygame.draw.circle(surface, (0, 0, 0), (x + 7, y - 5), 2)
        pygame.draw.arc(surface, (0, 0, 0), (x - 10, y - 2, 20, 16), 3.6, 5.8, 2)

    else:
        # boss：黒い本体＋赤いコア
        r = 34
        pygame.draw.circle(surface, (10, 10, 10), (x, y), r)
        pygame.draw.circle(surface, (60, 60, 60), (x, y), r, 4)
        pygame.draw.circle(surface, (255, 30, 30), (x, y), 10)
        pygame.draw.circle(surface, (255, 180, 180), (x - 10, y - 8), 6)
        pygame.draw.circle(surface, (255, 180, 180), (x + 10, y - 8), 6)
        pygame.draw.circle(surface, (0, 0, 0), (x - 10, y - 8), 2)
        pygame.draw.circle(surface, (0, 0, 0), (x + 10, y - 8), 2)


def draw_item(surface, itype, x, y):
    """アイテムを図形の組み合わせで描く（左上座標 x,y）"""
    x = int(x)
    y = int(y)

    # アイテムサイズ（大きめに調整）
    size = 56

    if itype == "patch":
        # 回復：緑のメディカルキット＋白い十字
        pygame.draw.rect(surface, (20, 160, 60), (x, y, size, size), border_radius=10)
        pygame.draw.rect(surface, (10, 120, 45), (x, y, size, size), 3, border_radius=10)
        # 十字
        pygame.draw.rect(surface, (245, 245, 245), (x + size * 0.40, y + size * 0.18, size * 0.20, size * 0.64))
        pygame.draw.rect(surface, (245, 245, 245), (x + size * 0.18, y + size * 0.40, size * 0.64, size * 0.20))

    elif itype == "vaccine":
        # ワクチン：注射器っぽい
        pygame.draw.rect(surface, (250, 250, 250), (x + size * 0.20, y + size * 0.40, size * 0.60, size * 0.22), border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), (x + size * 0.15, y + size * 0.44, size * 0.08, size * 0.14))
        pygame.draw.rect(surface, (200, 200, 200), (x + size * 0.80, y + size * 0.44, size * 0.08, size * 0.14))
        pygame.draw.line(surface, (120, 120, 120), (x + size * 0.90, y + size * 0.51), (x + size * 1.00, y + size * 0.51), 2)
        pygame.draw.circle(surface, (255, 220, 0), (int(x + size * 0.40), int(y + size * 0.51)), 4)

    else:
        # SSD：水色チップ
        pygame.draw.rect(surface, (0, 200, 220), (x, y, size, size), border_radius=8)
        pygame.draw.rect(surface, (0, 120, 140), (x, y, size, size), 3, border_radius=8)
        pygame.draw.rect(surface, (200, 255, 255), (x + size * 0.25, y + size * 0.25, size * 0.50, size * 0.50), border_radius=6)
        for i in range(5):
            pygame.draw.line(
                surface,
                (0, 120, 140),
                (x + size * (0.12 + i * 0.15), y),
                (x + size * (0.12 + i * 0.15), y + size * 0.15),
                2,
            )

            pygame.draw.line(
                surface,
                (0, 120, 140),
                (x + size * (0.12 + i * 0.15), y + size * 0.85),
                (x + size * (0.12 + i * 0.15), y + size),
                2,
            )
def draw_pc(surface, x, y):
    """左端のPC（パソコン）をそれっぽく描く（左上座標 x,y）"""
    x = int(x)
    y = int(y)

    # モニター
    pygame.draw.rect(surface, (30, 30, 30), (x + 10, y, 120, 80), border_radius=6)
    pygame.draw.rect(surface, (200, 240, 255), (x + 18, y + 8, 104, 60), border_radius=4)
    # 画面のキラッと感
    pygame.draw.line(surface, (255, 255, 255), (x + 26, y + 14), (x + 70, y + 14), 2)
    pygame.draw.line(surface, (255, 255, 255), (x + 26, y + 20), (x + 55, y + 20), 2)

    # モニタースタンド
    pygame.draw.rect(surface, (60, 60, 60), (x + 62, y + 78, 16, 18), border_radius=3)
    pygame.draw.rect(surface, (70, 70, 70), (x + 40, y + 94, 60, 10), border_radius=5)

    # 本体（タワー）
    pygame.draw.rect(surface, (80, 80, 80), (x, y + 40, 46, 92), border_radius=6)
    pygame.draw.rect(surface, (40, 40, 40), (x + 6, y + 50, 34, 70), 2, border_radius=4)
    # 電源ボタン
    pygame.draw.circle(surface, (0, 220, 120), (x + 23, y + 60), 5)
    pygame.draw.circle(surface, (20, 60, 40), (x + 23, y + 60), 5, 2)

    # キーボード
    pygame.draw.rect(surface, (160, 160, 160), (x + 54, y + 110, 92, 18), border_radius=6)
    pygame.draw.rect(surface, (110, 110, 110), (x + 58, y + 114, 84, 10), border_radius=4)
    # 簡易キー表現
    for i in range(6):
        pygame.draw.line(surface, (140, 140, 140), (x + 62 + i * 13, y + 114), (x + 62 + i * 13, y + 124), 1)

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
MAX_HP = 100

# PC被弾エフェクト用
pc_hit_timer = 0

# PCに当たった時に表示するダメージ数字（フローティングテキスト）
damage_texts = []  # {"text": str, "x": float, "y": float, "vy": float, "timer": int}

# アイテム取得表示（プレイヤーの上に出す）
pickup_texts = []  # {"text": str, "x": float, "y": float, "vy": float, "timer": int, "color": (r,g,b)}

# =========================
# スコア（表示しないが、内部の進行条件には使う）
# =========================
score = 0

# ステージ用：そのステージで倒した数
stage_kills = 0

# =========================
# 必殺技ゲージ
# =========================
special_gauge = 0
# 必殺技ゲージ（HPのようにバー表示にする）
MAX_GAUGE = 100
GAUGE_GAIN_PER_KILL = 8
GAUGE_GAIN_PER_SECOND = 0.6

special_effect_timer = 0

# =========================
# ウイルス
# =========================
viruses = []
spawn_timer = 0
boss_spawned = False

# ステージ内でボスを出すか（出すなら何体倒したタイミングで出すか）
STAGE2_BOSS_AT_KILLS = 6
STAGE3_BOSS_AT_KILLS = 6

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

# =========================
# スプレー攻撃（連射＋拡散）
# =========================
# スペースを押すと、一定時間「複数の弾」を前方にばら撒く（ショットガン/スプレー風）
# 既存の黄色い攻撃矩形(attack_rect)は当たり判定に使っていたが、
# ここでは弾（projectiles）で当たり判定を行う。
SPRAY_DURATION_FRAMES = 14  # 1回の攻撃の継続フレーム（スペース押下でこの間スプレー）
SPRAY_SHOTS_PER_FRAME = 2  # 1フレームあたりの発射数
# 横に広がる（上下のブレを抑えた）スプレー
# 角度で散らすより、上下方向の速度（vy）を小さくランダムに振る方が「横スプレー」っぽくなる。
SPRAY_SPREAD_DEG = 1.0     # 角度ブレ（ほぼ一直線）
SPRAY_VY_JITTER = 0.4      # 上下ブレ（ほぼ一直線）
SPRAY_SPEED = 14           # 弾速
SPRAY_RADIUS = 6           # 弾の半径

projectiles = []  # {"x","y","vx","vy","r"}

# スプレーが「最初に当たった敵」より奥に届かないようにするための壁（X座標）
spray_block_x = None

# ウイルスがPC(左側)に向かってカーブして寄っていく強さ
VIRUS_CURVE_STRENGTH = 0.08  # 大きいほどY方向に吸い寄せられる

# どのラインを超えたら「PCに向かってカーブ開始」するか
# （= プレイヤーを過ぎたら、という条件）
VIRUS_CURVE_START_X_OFFSET = 30  # player_x + 30 を切ったら追尾開始

# PCがダメージを受けた時の点滅/揺れエフェクト
PC_HIT_EFFECT_FRAMES = 14

# 必殺技エフェクト
SPECIAL_EFFECT_FRAMES = 28

running = True
game_clear = False


def _reset_game_state():
    """ゲーム状態を初期状態に戻す（main.py 統合用）"""
    global player_x, player_y
    global base_speed, player_speed
    global pc_hp, pc_hit_timer
    global damage_texts, pickup_texts
    global score, stage_kills
    global special_gauge, special_effect_timer
    global viruses, spawn_timer, boss_spawned
    global items, item_timer
    global vaccine_mode, vaccine_timer, ssd_timer
    global attack, attack_timer
    global projectiles, spray_block_x
    global stage, game_clear

    player_x, player_y = 200, 250
    base_speed = 6
    player_speed = base_speed

    pc_hp = 100
    pc_hit_timer = 0
    damage_texts = []
    pickup_texts = []

    score = 0
    stage_kills = 0

    special_gauge = 0
    special_effect_timer = 0

    viruses = []
    spawn_timer = 0
    boss_spawned = False

    items = []
    item_timer = 0

    vaccine_mode = False
    vaccine_timer = 0
    ssd_timer = 0

    attack = False
    attack_timer = 0

    projectiles = []
    spray_block_x = None

    stage = 1
    game_clear = False


def step_collision(dt: float, events, keys, target_screen: pygame.Surface, *, draw_background: bool = False):
    """collision の 1フレーム処理。

    - dt: 秒
    - events: main.py で取得したイベント列（pygame.event.get() の結果）
    - keys: main.py で取得した押下状態（pygame.key.get_pressed()）
    - target_screen: main.py の screen
    - draw_background: True の場合のみ collision 側で screen.fill する。
      （今回は bgSea を背景に使うので False 推奨）

    戻り値:
      {"running": bool, "game_clear": bool, "pc_hp": int, "stage": int}
    """
    global screen
    global running, game_clear
    global player_x, player_y, player_speed, base_speed
    global pc_hp, pc_hit_timer
    global damage_texts, pickup_texts
    global score, stage_kills
    global special_gauge, special_effect_timer
    global viruses, spawn_timer, boss_spawned
    global items, item_timer
    global vaccine_mode, vaccine_timer, ssd_timer
    global attack, attack_timer
    global projectiles, spray_block_x
    global stage

    screen = target_screen

    # ---------------------
    # ステージ進行
    # ---------------------
    if stage_kills >= STAGE_TARGET_KILLS:
        if stage < STAGE_MAX:
            stage += 1
            stage_kills = 0
            viruses.clear()
            projectiles.clear()
            items.clear()
            spawn_timer = 0
            item_timer = 0
            boss_spawned = False
        else:
            game_clear = True

    # 難易度上昇（ステージで変化）
    speed_bonus = (stage - 1) * 2

    # ---------------------
    # イベント（main の events を使う）
    # ---------------------
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # 通常攻撃
            if event.key == pygame.K_SPACE:
                attack = True
                attack_timer = SPRAY_DURATION_FRAMES
                spray_block_x = None

            # 必殺技
            if event.key == pygame.K_RETURN:
                if special_gauge >= MAX_GAUGE:
                    viruses.clear()
                    special_gauge = 0
                    special_effect_timer = SPECIAL_EFFECT_FRAMES

    # ---------------------
    # 移動
    # ---------------------
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
    spawn_interval = 70 if stage == 1 else 52 if stage == 2 else 40
    if spawn_timer >= spawn_interval:
        r = random.randint(1, 100)

        boss_at = STAGE2_BOSS_AT_KILLS if stage == 2 else STAGE3_BOSS_AT_KILLS if stage == 3 else None
        if boss_at is not None and (stage_kills >= boss_at) and not boss_spawned:
            viruses.append(
                {
                    "x": WIDTH,
                    "y": HEIGHT // 2,
                    "speed": 3 + speed_bonus,
                    "hp": 4 if stage == 2 else 5,
                    "type": "boss",
                }
            )
            boss_spawned = True
            spawn_timer = 0
        else:
            normal_rate = 82 if stage == 1 else 65 if stage == 2 else 50
            if r <= normal_rate:
                viruses.append(
                    {
                        "x": WIDTH,
                        "y": random.randint(50, 550),
                        "speed": 4 + speed_bonus,
                        "hp": 1,
                        "type": "normal",
                    }
                )
            else:
                viruses.append(
                    {
                        "x": WIDTH,
                        "y": random.randint(50, 550),
                        "speed": 6 + speed_bonus,
                        "hp": 2 if stage < 3 else 3,
                        "type": "strong",
                    }
                )

            spawn_timer = 0

    # ---------------------
    # アイテム生成
    # ---------------------
    item_timer += 1
    if item_timer >= 600:
        item_type = random.choice(["patch", "vaccine", "ssd"])
        items.append({"x": WIDTH, "y": random.randint(50, 550), "type": item_type})
        item_timer = 0

    # ---------------------
    # アイテム移動
    # ---------------------
    player_rect = pygame.Rect(player_x, player_y, 80, 80)
    for item in items[:]:
        item["x"] -= 4
        item_rect = pygame.Rect(item["x"], item["y"], 56, 56)
        if player_rect.colliderect(item_rect):
            if item["type"] == "patch":
                pc_hp = min(MAX_HP, pc_hp + 20)
                got_text = "HEAL +20"
                got_color = (0, 160, 60)
            elif item["type"] == "vaccine":
                vaccine_mode = True
                vaccine_timer = 600
                got_text = "POWER UP!"
                got_color = (200, 120, 0)
            else:
                player_speed = 10
                ssd_timer = 600
                got_text = "SPEED UP!"
                got_color = (0, 120, 220)

            pickup_texts.append({"text": got_text, "x": player_x, "y": player_y - 30, "vy": -0.9, "timer": 45, "color": got_color})
            items.remove(item)

    # ---------------------
    # ウイルス移動
    # ---------------------
    for virus in viruses[:]:
        virus["x"] -= virus["speed"]
        if virus["x"] < player_x + VIRUS_CURVE_START_X_OFFSET:
            pc_target_y = 230 + 60
            dy = pc_target_y - virus["y"]
            virus["y"] += dy * VIRUS_CURVE_STRENGTH
            virus["y"] = max(40, min(virus["y"], HEIGHT - 40))

        if virus["x"] < 70:
            if virus["type"] == "boss":
                dmg = 30
            elif virus["type"] == "strong":
                dmg = 15
            else:
                dmg = 10

            pc_hp = max(0, pc_hp - dmg)
            pc_hit_timer = PC_HIT_EFFECT_FRAMES
            damage_texts.append({"text": f"-{dmg}", "x": 60, "y": 220, "vy": -0.7, "timer": 40})
            viruses.remove(virus)

    # ---------------------
    # 攻撃（スプレー）
    # ---------------------
    if attack:
        attack_timer -= 1
        shots = SPRAY_SHOTS_PER_FRAME + (1 if vaccine_mode else 0)
        spread_deg = SPRAY_SPREAD_DEG + (6 if vaccine_mode else 0)
        speed = SPRAY_SPEED + (2 if vaccine_mode else 0)
        origin_x = player_x + 80
        origin_y = player_y + 40
        for _ in range(shots):
            ang = math.radians(random.uniform(-spread_deg, spread_deg))
            vx = math.cos(ang) * speed
            vy = (math.sin(ang) * speed) + random.uniform(-SPRAY_VY_JITTER, SPRAY_VY_JITTER)
            projectiles.append({"x": origin_x, "y": origin_y, "vx": vx, "vy": vy, "r": SPRAY_RADIUS})

        if attack_timer <= 0:
            attack = False
            spray_block_x = None

    # ---------------------
    # 弾の更新＆当たり判定
    # ---------------------
    for p in projectiles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        if spray_block_x is not None and p["x"] >= spray_block_x:
            projectiles.remove(p)
            continue
        if p["x"] > WIDTH + 50 or p["y"] < -50 or p["y"] > HEIGHT + 50:
            projectiles.remove(p)
            continue

        pr = p["r"]
        bullet_rect = pygame.Rect(int(p["x"] - pr), int(p["y"] - pr), pr * 2, pr * 2)
        hit = False
        for virus in viruses[:]:
            virus_rect = pygame.Rect(virus["x"] - 25, virus["y"] - 25, 50, 50)
            if bullet_rect.colliderect(virus_rect):
                if spray_block_x is None:
                    spray_block_x = virus["x"]
                virus["hp"] -= 1
                hit = True
                if virus["hp"] <= 0:
                    viruses.remove(virus)
                    score += 1
                    stage_kills += 1
                    special_gauge = min(MAX_GAUGE, special_gauge + GAUGE_GAIN_PER_KILL)
                break
        if hit:
            projectiles.remove(p)

    for p in projectiles[:]:
        if p["x"] < -50:
            projectiles.remove(p)

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
    # 描画（背景は main 側 / bgSea を使う）
    # ---------------------
    if draw_background:
        screen.fill((220, 240, 255))

    # 必殺技演出
    if special_effect_timer > 0:
        special_effect_timer -= 1
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(180 * (special_effect_timer / SPECIAL_EFFECT_FRAMES))
        overlay.fill((255, 255, 255, alpha))
        screen.blit(overlay, (0, 0))

        if (special_effect_timer % 4) < 2:
            text = big_font.render("SPECIAL!!", True, (140, 0, 220))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 180))

        for rr in range(40, 300, 40):
            pygame.draw.circle(screen, (200, 140, 255), (WIDTH // 2, HEIGHT // 2), rr, 3)

    # 必殺技ゲージ（時間でもじわじわ貯まる）
    special_gauge = min(MAX_GAUGE, special_gauge + GAUGE_GAIN_PER_SECOND * dt)

    # PC被弾エフェクト
    if pc_hit_timer > 0:
        pc_hit_timer -= 1

    pc_x, pc_y = 20, 230
    if pc_hit_timer > 0:
        pc_x += random.randint(-2, 2)
        pc_y += random.randint(-2, 2)
        flash = pygame.Surface((160, 150), pygame.SRCALPHA)
        alpha = 90 if (pc_hit_timer % 4) < 2 else 40
        flash.fill((255, 60, 60, alpha))
        screen.blit(flash, (pc_x - 8, pc_y - 8))

    draw_pc(screen, pc_x, pc_y)
    screen.blit(player_img, (player_x, player_y))

    if attack:
        pygame.draw.rect(screen, (255, 255, 160), (player_x + 70, player_y + 20, 30, 40), border_radius=8)

    for p in projectiles:
        pygame.draw.circle(screen, (255, 220, 0), (int(p["x"]), int(p["y"])), p["r"])

    for virus in viruses:
        draw_virus(screen, virus["type"], virus["x"], virus["y"])

    for item in items:
        draw_item(screen, item["type"], item["x"], item["y"])

    # HPゲージ
    hp_x, hp_y = 20, 20
    hp_w, hp_h = 240, 22
    pygame.draw.rect(screen, (30, 30, 30), (hp_x - 2, hp_y - 2, hp_w + 4, hp_h + 4), border_radius=6)
    pygame.draw.rect(screen, (220, 220, 220), (hp_x, hp_y, hp_w, hp_h), border_radius=5)
    hp_ratio = max(0.0, min(1.0, pc_hp / MAX_HP))
    fill_w = int(hp_w * hp_ratio)
    hp_color = (0, 200, 90) if hp_ratio >= 0.6 else (255, 180, 0) if hp_ratio >= 0.3 else (255, 70, 70)
    pygame.draw.rect(screen, hp_color, (hp_x, hp_y, fill_w, hp_h), border_radius=5)
    hp_text = font.render(f"HP {pc_hp}/{MAX_HP}", True, (0, 0, 0))
    screen.blit(hp_text, (hp_x + 8, hp_y - 2))

    # ゲージ
    gx, gy = 20, 52
    gw, gh = 240, 16
    pygame.draw.rect(screen, (30, 30, 30), (gx - 2, gy - 2, gw + 4, gh + 4), border_radius=6)
    pygame.draw.rect(screen, (230, 230, 230), (gx, gy, gw, gh), border_radius=5)
    gr = max(0.0, min(1.0, special_gauge / MAX_GAUGE))
    pygame.draw.rect(screen, (170, 90, 255), (gx, gy, int(gw * gr), gh), border_radius=5)
    gtxt = font.render("SPECIAL", True, (0, 0, 0))
    screen.blit(gtxt, (gx + 8, gy - 6))

    # フローティングテキスト
    for dtxt in damage_texts[:]:
        dtxt["y"] += dtxt["vy"] * 60 * dt
        dtxt["timer"] -= 1
        surf = font.render(dtxt["text"], True, (255, 30, 30))
        screen.blit(surf, (int(dtxt["x"]), int(dtxt["y"])))
        if dtxt["timer"] <= 0:
            damage_texts.remove(dtxt)

    for pt in pickup_texts[:]:
        pt["y"] += pt["vy"] * 60 * dt
        pt["timer"] -= 1
        surf = font.render(pt["text"], True, pt.get("color", (0, 0, 0)))
        screen.blit(surf, (int(pt["x"]), int(pt["y"])))
        if pt["timer"] <= 0:
            pickup_texts.remove(pt)

    # クリア/ゲームオーバーの表示（統合時は待機ループに入らず main に返す）
    if game_clear:
        screen.blit(big_font.render("CLEAR!", True, (0, 200, 0)), (WIDTH // 2 - 150, 200))
        screen.blit(font.render("Enter/Clickで終了", True, (0, 0, 0)), (WIDTH // 2 - 140, 280))

    if pc_hp <= 0:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 220, 80, 70))
        screen.blit(overlay, (0, 0))
        screen.blit(big_font.render("INFECTED", True, (0, 130, 0)), (240, 210))
        screen.blit(big_font.render("GAME OVER", True, (255, 0, 0)), (180, 280))
        screen.blit(font.render("Click / Enter to Exit", True, (0, 0, 0)), (340, 350))

    return {"running": bool(running), "game_clear": bool(game_clear), "pc_hp": int(pc_hp), "stage": int(stage)}

# =========================
# ステージ
# =========================
stage = 1
STAGE_MAX = 3
STAGE_TARGET_KILLS = 10

# =========================
# タイトル（ルール説明）画面
# =========================


def draw_multiline_text(surface, text, x, y, font_obj, color=(0, 0, 0), line_gap=8):
    """\n区切りの複数行テキストを描画する"""
    yy = y
    for line in text.split("\n"):
        surface.blit(font_obj.render(line, True, color), (x, yy))
        yy += font_obj.get_height() + line_gap


def show_title_screen():
    """クリックでゲーム開始するルール説明画面"""
    waiting = True
    while waiting:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            # クリック or Enter/Space で開始
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                waiting = False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                waiting = False

        screen.fill((220, 240, 255))

        # タイトル
        title_surf = big_font.render("大西先生 VS ウイルス", True, (0, 40, 120))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 70))

        # ルール説明
        rules = (
            "【操作】\n"
            "・矢印キー：移動\n"
            "・SPACE：攻撃（前方）\n"
            "・ENTER：必殺技（ゲージMAXで全消し）\n"
            "\n"
            "【敵とポイント】\n"
            "・赤ウイルス：HP1 / +1点\n"
            "・紫ウイルス：HP2 / +3点（速い）\n"
            "・BOSS：HP3 / 倒すとCLEAR（出現：ステージ3）\n"
            "※ウイルスが左端（PC）に到達するとHP減少\n"
            "\n"
            "【アイテム効果】\n"
            "・PATCH：HP +20（最大100）\n"
            "・ワクチン：10秒 攻撃範囲が広がる\n"
            "・SSD：10秒 移動速度UP\n"
            "\n"
            "【必殺技】\n"
            "・敵を倒すとゲージ+1（最大5）\n"
            "・ゲージMAXでENTER → 画面上の敵を全消し"
        )
        draw_multiline_text(screen, rules, 110, 170, font, (0, 0, 0), line_gap=6)

        # 開始案内（点滅）
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            msg = font.render("クリックでスタート（Enter/SpaceでもOK）", True, (0, 0, 0))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 520))

        pygame.display.flip()
 

def run_standalone():
    """従来の単体実行モード（背景は collision 側で描画）"""
    global screen, player_img, running

    pygame.init()
    init_collision(WIDTH, HEIGHT)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("大西先生 VS ウイルス")

    _reset_game_state()
    show_title_screen()

    player_img = pygame.image.load("player_attack.png")
    player_img = pygame.transform.scale(player_img, (80, 80))

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        step_collision(dt, events, keys, screen, draw_background=True)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_standalone()


"""---- legacy loop below (kept as reference but disabled) ----

show_title_screen()

player_img = pygame.image.load("player_attack.png")
player_img = pygame.transform.scale(player_img, (80, 80))

while running:
    clock.tick(60)

    # ---------------------
    # ステージ進行
    # ---------------------
    # 各ステージ10体倒したら次へ
    if stage_kills >= STAGE_TARGET_KILLS:
        if stage < STAGE_MAX:
            stage += 1
            stage_kills = 0
            viruses.clear()
            projectiles.clear()
            items.clear()
            spawn_timer = 0
            item_timer = 0
            boss_spawned = False
        else:
            # ステージ3を10体倒したらクリア
            game_clear = True

    # 難易度上昇（ステージで変化）
    # stage=1: 基本
    # stage=2: 少し速い/出現間隔短い
    # stage=3: さらに速い/出現間隔短い
    speed_bonus = (stage - 1) * 2

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
                attack_timer = SPRAY_DURATION_FRAMES
                spray_block_x = None

            # 必殺技
            if event.key == pygame.K_RETURN:
                if special_gauge >= MAX_GAUGE:
                    viruses.clear()
                    special_gauge = 0
                    special_effect_timer = SPECIAL_EFFECT_FRAMES

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

    # ステージが上がるほど出現頻度を上げる
    spawn_interval = 70 if stage == 1 else 52 if stage == 2 else 40
    if spawn_timer >= spawn_interval:
        r = random.randint(1, 100)

        # ステージ2/3は途中でボスを1回だけ出す
        boss_at = STAGE2_BOSS_AT_KILLS if stage == 2 else STAGE3_BOSS_AT_KILLS if stage == 3 else None
        if boss_at is not None and (stage_kills >= boss_at) and not boss_spawned:
            viruses.append(
                {
                    "x": WIDTH,
                    "y": HEIGHT // 2,
                    "speed": 3 + speed_bonus,
                    "hp": 4 if stage == 2 else 5,
                    "type": "boss",
                }
            )
            boss_spawned = True
            spawn_timer = 0
        else:

            # ステージが上がると強い敵が出やすい
            normal_rate = 82 if stage == 1 else 65 if stage == 2 else 50

            if r <= normal_rate:
                viruses.append(
                    {
                        "x": WIDTH,
                        "y": random.randint(50, 550),
                        "speed": 4 + speed_bonus,
                        # 弱：スプレー1回分くらいで倒せる
                        "hp": 1,
                        "type": "normal",
                    }
                )

            else:
                viruses.append(
                    {
                        "x": WIDTH,
                        "y": random.randint(50, 550),
                        "speed": 6 + speed_bonus,
                        # 強：スプレー2回分くらいで倒せる
                        "hp": 2 if stage < 3 else 3,
                        "type": "strong",
                    }
                )

            spawn_timer = 0

    # ---------------------
    # アイテム生成
    # ---------------------
    item_timer += 1

    if item_timer >= 600:
        item_type = random.choice(["patch", "vaccine", "ssd"])

        items.append(
            {
                "x": WIDTH,
                "y": random.randint(50, 550),
                "type": item_type,
            }
        )

        item_timer = 0

    # ---------------------
    # アイテム移動
    # ---------------------
    player_rect = pygame.Rect(player_x, player_y, 80, 80)

    for item in items[:]:
        item["x"] -= 4

        # アイテムサイズを大きめにしたので当たり判定も合わせる
        item_rect = pygame.Rect(item["x"], item["y"], 56, 56)

        if player_rect.colliderect(item_rect):
            if item["type"] == "patch":
                pc_hp = min(MAX_HP, pc_hp + 20)
                got_text = "HEAL +20"
                got_color = (0, 160, 60)

            elif item["type"] == "vaccine":
                vaccine_mode = True
                vaccine_timer = 600
                got_text = "POWER UP!"
                got_color = (200, 120, 0)

            elif item["type"] == "ssd":
                player_speed = 10
                ssd_timer = 600
                got_text = "SPEED UP!"
                got_color = (0, 120, 220)

            # 取得内容をプレイヤーの上に大きく表示
            pickup_texts.append(
                {
                    "text": got_text,
                    "x": player_x,
                    "y": player_y - 30,
                    "vy": -0.9,
                    "timer": 55,
                    "color": got_color,
                }
            )

            items.remove(item)

    # ---------------------
    # ウイルス移動
    # ---------------------
    for virus in viruses[:]:
        virus["x"] -= virus["speed"]

        # 「プレイヤーを過ぎたら」PCに向かってカーブさせる
        # （プレイヤーより左側に入ったら、PC中心へ吸い寄せる）
        if virus["x"] < player_x + VIRUS_CURVE_START_X_OFFSET:
            # PCの中心を狙う：draw_pc(screen, 20, 230) のだいたい中心
            pc_target_y = 230 + 60  # PC全体の中心っぽいY
            dy = pc_target_y - virus["y"]
            virus["y"] += dy * VIRUS_CURVE_STRENGTH
            virus["y"] = max(40, min(virus["y"], HEIGHT - 40))

        if virus["x"] < 70:
            if virus["type"] == "boss":
                dmg = 30
            elif virus["type"] == "strong":
                dmg = 15
            else:
                dmg = 10

            pc_hp = max(0, pc_hp - dmg)
            pc_hit_timer = PC_HIT_EFFECT_FRAMES

            # PC上にダメージ表示
            damage_texts.append(
                {
                    "text": f"-{dmg}",
                    "x": 60,
                    "y": 220,
                    "vy": -0.7,
                    "timer": 40,
                }
            )

            viruses.remove(virus)

    if attack:
        attack_timer -= 1

        # スプレー（扇状にばら撒く）
        # vaccine_mode なら発射数/拡散/弾速を少し強化
        shots = SPRAY_SHOTS_PER_FRAME + (1 if vaccine_mode else 0)
        spread_deg = SPRAY_SPREAD_DEG + (6 if vaccine_mode else 0)
        speed = SPRAY_SPEED + (2 if vaccine_mode else 0)

        # プレイヤーの右側中心から発射
        origin_x = player_x + 80
        origin_y = player_y + 40

        for _ in range(shots):
            # 「横スプレー」：基本は右方向へ。
            # 角度のばらつきは小さく、上下の揺れ(vy)で散らす。
            ang = math.radians(random.uniform(-spread_deg, spread_deg))
            vx = math.cos(ang) * speed
            vy = (math.sin(ang) * speed) + random.uniform(-SPRAY_VY_JITTER, SPRAY_VY_JITTER)
            projectiles.append(
                {
                    "x": origin_x,
                    "y": origin_y,
                    "vx": vx,
                    "vy": vy,
                    "r": SPRAY_RADIUS,
                }
            )

        if attack_timer <= 0:
            attack = False
            spray_block_x = None

    # ---------------------
    # 弾の更新＆当たり判定
    # ---------------------
    for p in projectiles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # スプレーの「壁」より奥へ行かせない（最初に当たった敵で止まる）
        if spray_block_x is not None and p["x"] >= spray_block_x:
            projectiles.remove(p)
            continue

        # 画面外は削除
        if p["x"] > WIDTH + 50 or p["y"] < -50 or p["y"] > HEIGHT + 50:
            projectiles.remove(p)
            continue

        # ウイルスとの当たり判定（簡易：円と四角の当たり）
        pr = p["r"]
        bullet_rect = pygame.Rect(int(p["x"] - pr), int(p["y"] - pr), pr * 2, pr * 2)
        hit = False
        for virus in viruses[:]:
            virus_rect = pygame.Rect(virus["x"] - 25, virus["y"] - 25, 50, 50)
            if bullet_rect.colliderect(virus_rect):
                # この攻撃中は、この敵の手前で弾が止まる（以後の弾は奥に行かない）
                if spray_block_x is None:
                    spray_block_x = virus["x"]

                virus["hp"] -= 1
                hit = True
                if virus["hp"] <= 0:
                    viruses.remove(virus)
                    score += 1
                    stage_kills += 1
                    speed_bonus = score // 5
                    special_gauge = min(MAX_GAUGE, special_gauge + GAUGE_GAIN_PER_KILL)
                break
        if hit:
            # 貫通させない（スプレーっぽく命中で消える）
            projectiles.remove(p)

    # 画面より左に行った弾も消す（後ろに行かないようにする）
    for p in projectiles[:]:
        if p["x"] < -50:
            projectiles.remove(p)


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

    # 必殺技演出（フラッシュ＋文字）
    if special_effect_timer > 0:
        special_effect_timer -= 1
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # 最初は強く、後半は弱く
        alpha = int(180 * (special_effect_timer / SPECIAL_EFFECT_FRAMES))
        overlay.fill((255, 255, 255, alpha))
        screen.blit(overlay, (0, 0))

        if (special_effect_timer % 4) < 2:
            text = big_font.render("SPECIAL!!", True, (140, 0, 220))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 180))

        # 爆風っぽい輪
        for r in range(40, 300, 40):
            pygame.draw.circle(screen, (200, 140, 255), (WIDTH // 2, HEIGHT // 2), r, 3)

    # ---------------------
    # 必殺技ゲージ（時間でもじわじわ貯まる）
    # ---------------------
    special_gauge = min(MAX_GAUGE, special_gauge + GAUGE_GAIN_PER_SECOND / 60.0)

    # PC被弾エフェクト（点滅＋微振動）
    if pc_hit_timer > 0:
        pc_hit_timer -= 1

    pc_x, pc_y = 20, 230
    if pc_hit_timer > 0:
        # 小さく揺らす
        pc_x += random.randint(-2, 2)
        pc_y += random.randint(-2, 2)
        # 赤いフラッシュ（薄い矩形）
        flash = pygame.Surface((160, 150), pygame.SRCALPHA)
        alpha = 90 if (pc_hit_timer % 4) < 2 else 40
        flash.fill((255, 60, 60, alpha))
        screen.blit(flash, (pc_x - 8, pc_y - 8))

    # パソコン（それっぽく）
    draw_pc(screen, pc_x, pc_y)

    # プレイヤー
    screen.blit(player_img, (player_x, player_y))

    # 攻撃（スプレー中の演出：少し光らせる）
    if attack:
        pygame.draw.rect(
            screen,
            (255, 255, 160),
            (player_x + 70, player_y + 20, 30, 40),
            border_radius=8,
        )

    # 弾
    for p in projectiles:
        pygame.draw.circle(screen, (255, 220, 0), (int(p["x"]), int(p["y"])), p["r"])

    # ---------------------
    # ウイルス（図形の組み合わせで描画）
    # ---------------------
    for virus in viruses:
        draw_virus(screen, virus["type"], virus["x"], virus["y"])

    # ---------------------
    # アイテム（図形の組み合わせで描画）
    # ---------------------
    for item in items:
        draw_item(screen, item["type"], item["x"], item["y"])

    # HPゲージ
    hp_x, hp_y = 20, 20
    hp_w, hp_h = 240, 22
    pygame.draw.rect(screen, (30, 30, 30), (hp_x - 2, hp_y - 2, hp_w + 4, hp_h + 4), border_radius=6)
    pygame.draw.rect(screen, (220, 220, 220), (hp_x, hp_y, hp_w, hp_h), border_radius=5)

    hp_ratio = max(0.0, min(1.0, pc_hp / MAX_HP))
    fill_w = int(hp_w * hp_ratio)
    hp_color = (0, 200, 90) if hp_ratio >= 0.6 else (255, 180, 0) if hp_ratio >= 0.3 else (255, 60, 60)
    if fill_w > 0:
        pygame.draw.rect(screen, hp_color, (hp_x, hp_y, fill_w, hp_h), border_radius=5)

    screen.blit(font.render(f"HP {pc_hp}/{MAX_HP}", True, (0, 0, 0)), (hp_x + hp_w + 12, hp_y - 6))
    # SCORE表示は不要とのことなので非表示

    # 残り討伐数（ステージ表記は不要とのことなので消す）
    remain = max(0, STAGE_TARGET_KILLS - stage_kills)
    screen.blit(font.render(f"ENEMIES LEFT: {remain}", True, (0, 0, 0)), (20, 150))

    # 必殺技ゲージ（HPと同じバー表現）
    # ステージ表記を消した分、ゲージを上に詰める
    gauge_x, gauge_y = 20, 70
    gauge_w, gauge_h = 240, 18
    pygame.draw.rect(screen, (30, 30, 30), (gauge_x - 2, gauge_y - 2, gauge_w + 4, gauge_h + 4), border_radius=6)
    pygame.draw.rect(screen, (220, 220, 220), (gauge_x, gauge_y, gauge_w, gauge_h), border_radius=5)
    g_ratio = max(0.0, min(1.0, special_gauge / MAX_GAUGE))
    g_fill = int(gauge_w * g_ratio)
    if g_fill > 0:
        pygame.draw.rect(screen, (120, 90, 255), (gauge_x, gauge_y, g_fill, gauge_h), border_radius=5)
    screen.blit(font.render(f"SPECIAL {int(special_gauge)}/{MAX_GAUGE}", True, (0, 0, 0)), (gauge_x + gauge_w + 12, gauge_y - 10))

    # ゲージがMAXになったら案内を表示
    if special_gauge >= MAX_GAUGE:
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            ready = font.render("PUSH ENTER!", True, (120, 0, 200))
            # ゲージの下に表示
            screen.blit(ready, (gauge_x, gauge_y + 26))

    # ダメージ数字（PCの上に浮かぶ）
    for dt in damage_texts[:]:
        dt["y"] += dt["vy"]
        dt["timer"] -= 1
        # だんだん薄く
        alpha = max(0, min(255, int(255 * (dt["timer"] / 40))))
        # 文字を大きく（既存fontは40なので、スケールして強調）
        surf = font.render(dt["text"], True, (255, 0, 0))
        surf = pygame.transform.smoothscale(
            surf,
            (int(surf.get_width() * 1.6), int(surf.get_height() * 1.6)),
        )
        surf.set_alpha(alpha)
        screen.blit(surf, (int(dt["x"]), int(dt["y"])))
        if dt["timer"] <= 0:
            damage_texts.remove(dt)

    # アイテム取得表示（プレイヤーの上に浮かぶ・大きめ）
    for pt in pickup_texts[:]:
        pt["y"] += pt["vy"]
        pt["timer"] -= 1
        alpha = max(0, min(255, int(255 * (pt["timer"] / 55))))

        surf = big_font.render(pt["text"], True, pt["color"])
        # さらに強調
        surf = pygame.transform.smoothscale(
            surf,
            (int(surf.get_width() * 1.15), int(surf.get_height() * 1.15)),
        )
        surf.set_alpha(alpha)

        # プレイヤーの中心あたりに来るようにXを調整
        x = int(pt["x"] + 40 - surf.get_width() // 2)
        y = int(pt["y"])

        # 縁取り（黒）
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            outline = surf.copy()
            outline.fill((0, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(outline, (x + ox, y + oy))
        screen.blit(surf, (x, y))

        if pt["timer"] <= 0:
            pickup_texts.remove(pt)

    # クリア
    if game_clear:
        if pc_hp == 100:
            rank = "S"
        elif pc_hp >= 70:
            rank = "A"
        elif pc_hp >= 40:
            rank = "B"
        else:
            rank = "C"

        screen.blit(big_font.render("CLEAR!", True, (0, 200, 0)), (300, 200))
        screen.blit(font.render(f"RANK : {rank}", True, (0, 0, 0)), (400, 300))
        screen.blit(font.render("クリック/Enterで終了", True, (0, 0, 0)), (360, 360))

        pygame.display.flip()

        # クリアしたら停止して終了
        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                ):
                    waiting = False
        running = False
        continue

    # ゲームオーバー
    if pc_hp <= 0:
        # 感染っぽい演出（緑のモヤ＋ノイズ＋WARNING）
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 220, 80, 70))
        screen.blit(overlay, (0, 0))

        # PC周辺にランダムな感染スポット
        for _ in range(90):
            rx = random.randint(0, 160)
            ry = random.randint(200, 380)
            r = random.randint(2, 8)
            col = (0, random.randint(150, 255), 0, random.randint(40, 120))
            pygame.draw.circle(screen, col, (rx, ry), r)

        # 画面ノイズ
        for _ in range(120):
            nx = random.randint(0, WIDTH - 1)
            ny = random.randint(0, HEIGHT - 1)
            pygame.draw.rect(screen, (0, 255, 80), (nx, ny, 2, 2))

        screen.blit(big_font.render("INFECTED", True, (0, 130, 0)), (240, 210))
        screen.blit(big_font.render("GAME OVER", True, (255, 0, 0)), (180, 280))
        screen.blit(font.render("Click / Enter to Exit", True, (0, 0, 0)), (340, 350))

        pygame.display.flip()

        # ゲームオーバーで停止して終了
        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                ):
                    waiting = False
        running = False
        continue

    pygame.display.flip()

pygame.quit()
"""