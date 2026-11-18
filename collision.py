import pygame
from pygame import Rect

pygame.init()

W, H = 960, 540
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Platformer (LEFT/RIGHT move, UP jump) - flat stage")
clock = pygame.time.Clock()

# --- 定数（調整しやすい） ---
G = 2400.0
MOVE_ACC = 6200.0
AIR_ACC = 4200.0
MAX_SPEED = 420.0
FRICTION = 7200.0
JUMP_V = 860.0

COYOTE = 0.08
JUMP_BUFFER = 0.10

# --- レベル（床/足場） ---
solids = [
    # 平らな床だけ（穴・足場なし）
    Rect(-6000, 460, 12000, 200),
]

spikes = []

# ゴールは一旦なし

# --- プレイヤ ---
player = Rect(-750, 200, 32, 42)
vx, vy = 0.0, 0.0
on_ground = False
coyote_timer = 0.0
jumpbuf_timer = 0.0
prev_jump = False
prev_attack = False

# float座標（当たり判定Rectに代入する前の“真の位置”）
px_f = float(player.x)
py_f = float(player.y)

camera_x = 0.0

cleared = False  # 互換のため残す（ゴールは一旦なし）

# スコアや制限時間は一旦なし


# --- プレイヤ画像（停止/移動/ジャンプ/攻撃） ---
# collision.py と同じフォルダに以下を置いてください（透過PNG推奨）
#   player_idle.png
#   player_run.png
#   player_jump.png
try:
    img_idle = pygame.image.load("player_idle.png").convert_alpha()
    img_run = pygame.image.load("player_run.png").convert_alpha()
    img_jump = pygame.image.load("player_jump.png").convert_alpha()
    img_attack = pygame.image.load("player_attack.png").convert_alpha()
except Exception as ex:
    raise SystemExit(
        "player_idle.png / player_run.png / player_jump.png / player_attack.png が読み込めません。\n"
        "collision.py と同じフォルダに4つのPNGを置いてから起動してください。\n"
        f"詳細: {ex}"
    )

def fit_to_box(img: pygame.Surface, box_w: int, box_h: int) -> pygame.Surface:
    """画像の縦横比を維持したまま、当たり判定サイズの箱に収まるようにリサイズする。"""
    iw, ih = img.get_width(), img.get_height()
    if iw <= 0 or ih <= 0:
        return pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    scale = min(box_w / iw, box_h / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    return pygame.transform.smoothscale(img, (nw, nh))


def blit_center(dst: pygame.Surface, img: pygame.Surface, x: int, y: int, box_w: int, box_h: int):
    """(x,y,box_w,box_h) の箱の中央に画像を描画する。"""
    dst.blit(img, (x + (box_w - img.get_width()) // 2, y + (box_h - img.get_height()) // 2))


# 縦横比維持でフィット（停止画像だけ横長でも潰れない）
PLAYER_SCALE = 1.35  # プレイヤを大きくする倍率（好みで調整）

# Rectサイズを変えると位置がズレるので、中心を保ったまま拡大する
_cx, _cy = player.center
player.w = int(round(player.w * PLAYER_SCALE))
player.h = int(round(player.h * PLAYER_SCALE))
player.center = (_cx, _cy)

img_idle = fit_to_box(img_idle, player.w, player.h)
img_run = fit_to_box(img_run, player.w, player.h)
img_jump = fit_to_box(img_jump, player.w, player.h)
img_attack = fit_to_box(img_attack, player.w, player.h)

facing_right = True

# ジャンプ画像が「接地/非接地」の判定揺れで点滅しないように、
# ジャンプ開始～着地までを明示的に管理するフラグ
is_jumping = False

# 攻撃状態
is_attacking = False
attack_timer = 0.0
ATTACK_DURATION = 0.18  # 攻撃画像を出す時間（秒）
ATTACK_HITBOX_W = 24
ATTACK_HITBOX_H = 22

def reset():
    global vx, vy, on_ground, coyote_timer, jumpbuf_timer, camera_x, cleared
    global facing_right
    global prev_jump, is_jumping
    global prev_attack, is_attacking, attack_timer
    global px_f, py_f
    player.x, player.y = -750, 200
    px_f = float(player.x)
    py_f = float(player.y)
    vx, vy = 0.0, 0.0
    on_ground = False
    coyote_timer = 0.0
    jumpbuf_timer = 0.0
    prev_jump = False
    prev_attack = False
    camera_x = player.x - W * 0.35
    cleared = False
    facing_right = True
    is_jumping = False
    is_attacking = False
    attack_timer = 0.0

def clamp(x, a, b):
    return a if x < a else b if x > b else x

def move_and_collide_player(dt):
    """プレイヤの軸分離衝突解決"""
    global vx, vy, on_ground, px_f, py_f
    on_ground = False

    # X
    px_f += vx * dt
    player.x = int(round(px_f))
    for s in solids:
        if player.colliderect(s):
            if vx > 0:
                player.right = s.left
            elif vx < 0:
                player.left = s.right
            vx = 0.0
            px_f = float(player.x)

    # Y
    py_f += vy * dt
    player.y = int(round(py_f))
    for s in solids:
        if player.colliderect(s):
            if vy > 0:
                player.bottom = s.top
                vy = 0.0
                on_ground = True
                py_f = float(player.y)
            elif vy < 0:
                player.top = s.bottom
                vy = 0.0
                py_f = float(player.y)



reset()

running = True
font = pygame.font.SysFont(None, 26)

while running:
    dt = min(0.02, clock.tick(60) / 1000.0)

    # NOTE: このファイルはトップレベルで変数を更新しているため global 宣言は不要

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_r]:
        reset()

    if not cleared:

        left  = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]
        jump  = keys[pygame.K_UP]   # ジャンプは上矢印

        # 攻撃（Zキー）
        attack = keys[pygame.K_z]

        # 攻撃の「押した瞬間」検出
        attack_pressed = attack and not prev_attack
        prev_attack = attack

        # 攻撃開始
        if attack_pressed and not is_attacking:
            is_attacking = True
            attack_timer = ATTACK_DURATION

        # 攻撃タイマー更新
        if is_attacking:
            attack_timer -= dt
            if attack_timer <= 0:
                is_attacking = False
                attack_timer = 0.0

        # ジャンプの「押した瞬間」だけ検出（押しっぱなしで状態が揺れにくくする）
        jump_pressed = jump and not prev_jump
        prev_jump = jump

        # 向き更新（入力があるときだけ更新）
        if left and not right:
            facing_right = False
        elif right and not left:
            facing_right = True

        # ジャンプバッファ
        if jump_pressed:
            jumpbuf_timer = JUMP_BUFFER
        else:
            jumpbuf_timer = max(0.0, jumpbuf_timer - dt)

        # コヨーテ
        if on_ground:
            coyote_timer = COYOTE
        else:
            coyote_timer = max(0.0, coyote_timer - dt)

        # 左右加速
        ax = MOVE_ACC if on_ground else AIR_ACC
        if left and not right:
            vx -= ax * dt
        if right and not left:
            vx += ax * dt

        # 摩擦（地上＆入力なし）
        if on_ground and not left and not right:
            if abs(vx) <= FRICTION * dt:
                vx = 0.0
            else:
                vx -= (FRICTION * dt) * (1 if vx > 0 else -1)

        vx = clamp(vx, -MAX_SPEED, MAX_SPEED)

        # 重力
        vy += G * dt

        # ジャンプ成立
        if jumpbuf_timer > 0.0 and coyote_timer > 0.0:
            vy = -JUMP_V
            jumpbuf_timer = 0.0
            coyote_timer = 0.0
            on_ground = False
            is_jumping = True

        # プレイヤ移動
        move_and_collide_player(dt)

        # 着地したらジャンプ状態を解除
        if on_ground:
            is_jumping = False

        # 落下死
        if player.y > 1200:
            reset()

        # トゲ
        for sp in spikes:
            if player.colliderect(sp):
                reset()

        # カメラ
        target = player.x - W * 0.35
        camera_x += (target - camera_x) * min(1.0, 8.0 * dt)

    # --- 描画 ---
    screen.fill((27, 59, 122))
    pygame.draw.rect(screen, (30, 140, 200), Rect(0, 0, W, H))

    # 足場
    for s in solids:
        sx = s.x - int(camera_x)
        pygame.draw.rect(screen, (91, 58, 29), Rect(sx, s.y, s.w, s.h))
        pygame.draw.rect(screen, (122, 75, 34), Rect(sx, s.y, s.w, 6))

    # トゲ
    for sp in spikes:
        sx = sp.x - int(camera_x)
        pygame.draw.rect(screen, (196, 59, 59), Rect(sx, sp.y, sp.w, sp.h))

    # プレイヤ
    px = player.x - int(camera_x)

    # 状態に応じて画像を切り替え
    if cleared:
        img = img_idle
    else:
        # 攻撃中は攻撃画像を優先
        if is_attacking:
            img = img_attack
        # is_jumping を優先することで、接地判定の揺れによる点滅を防ぐ
        elif is_jumping:
            img = img_jump
        else:
            img = img_run if abs(vx) > 40.0 else img_idle

    if not facing_right:
        img = pygame.transform.flip(img, True, False)

    # サイズがRectと一致しない（縦横比維持で縮小されている）場合があるので中央に配置
    blit_center(screen, img, px, player.y, player.w, player.h)

    # 攻撃判定の見える化（デバッグ用）
    # Z攻撃中に、プレイヤ前方に赤い当たり判定を表示
    if is_attacking and not cleared:
        hit_w = ATTACK_HITBOX_W
        hit_h = ATTACK_HITBOX_H
        hit_y = player.y + (player.h - hit_h) // 2
        if facing_right:
            hit_x = (player.x - int(camera_x)) + player.w
        else:
            hit_x = (player.x - int(camera_x)) - hit_w
        pygame.draw.rect(screen, (255, 60, 60), Rect(hit_x, hit_y, hit_w, hit_h), 2)

    # HUD
    hud = "Move: LEFT/RIGHT   Jump: UP   Attack: Z   R: reset"
    msg = font.render(hud, True, (255, 255, 255))
    screen.blit(msg, (12, 12))

    pygame.display.flip()

pygame.quit()
