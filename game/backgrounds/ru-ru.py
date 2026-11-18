import pygame
import math
import os


# ============================================================
# ルール説明用 背景（単体で実行OK）
# - check/collision.py の敵・アイテムの「絵」をそのまま図形で表示
# - 文章は日本語で大きめ、読みやすく、はっきり
# - 他コードとの依存なし（このファイル単体で動く）
# ============================================================


def draw_virus(surface, vtype, x, y):
    """check/collision.py と同じ見た目のウイルス（中心座標 x,y）"""
    x = int(x)
    y = int(y)

    if vtype == "normal":
        body_color = (230, 40, 40)
        spike_color = (170, 0, 0)
        r = 22
        for dx, dy in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 1),
        ]:
            pygame.draw.line(
                surface,
                spike_color,
                (x, y),
                (x + dx * (r + 10), y + dy * (r + 10)),
                3,
            )
        pygame.draw.circle(surface, body_color, (x, y), r)
        pygame.draw.circle(surface, (255, 200, 200), (x - 6, y - 4), 5)
        pygame.draw.circle(surface, (255, 200, 200), (x + 6, y - 4), 5)
        pygame.draw.circle(surface, (0, 0, 0), (x - 6, y - 4), 2)
        pygame.draw.circle(surface, (0, 0, 0), (x + 6, y - 4), 2)

    elif vtype == "strong":
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
        r = 34
        pygame.draw.circle(surface, (10, 10, 10), (x, y), r)
        pygame.draw.circle(surface, (60, 60, 60), (x, y), r, 4)
        pygame.draw.circle(surface, (255, 30, 30), (x, y), 10)
        pygame.draw.circle(surface, (255, 180, 180), (x - 10, y - 8), 6)
        pygame.draw.circle(surface, (255, 180, 180), (x + 10, y - 8), 6)
        pygame.draw.circle(surface, (0, 0, 0), (x - 10, y - 8), 2)
        pygame.draw.circle(surface, (0, 0, 0), (x + 10, y - 8), 2)


def draw_item(surface, itype, x, y):
    """check/collision.py と同じ見た目のアイテム（左上 x,y / 40x40）"""
    x = int(x)
    y = int(y)

    if itype == "patch":
        pygame.draw.rect(surface, (20, 160, 60), (x, y, 40, 40), border_radius=8)
        pygame.draw.rect(surface, (10, 120, 45), (x, y, 40, 40), 3, border_radius=8)
        pygame.draw.rect(surface, (245, 245, 245), (x + 16, y + 8, 8, 24))
        pygame.draw.rect(surface, (245, 245, 245), (x + 8, y + 16, 24, 8))

    elif itype == "vaccine":
        pygame.draw.rect(surface, (250, 250, 250), (x + 8, y + 18, 24, 12), border_radius=4)
        pygame.draw.rect(surface, (180, 180, 180), (x + 6, y + 20, 4, 8))
        pygame.draw.rect(surface, (200, 200, 200), (x + 32, y + 20, 4, 8))
        pygame.draw.line(surface, (120, 120, 120), (x + 36, y + 24), (x + 40, y + 24), 2)
        pygame.draw.circle(surface, (255, 220, 0), (x + 16, y + 24), 3)

    else:
        pygame.draw.rect(surface, (0, 200, 220), (x, y, 40, 40), border_radius=6)
        pygame.draw.rect(surface, (0, 120, 140), (x, y, 40, 40), 3, border_radius=6)
        pygame.draw.rect(surface, (200, 255, 255), (x + 10, y + 10, 20, 20), border_radius=4)
        for i in range(5):
            pygame.draw.line(surface, (0, 120, 140), (x + 6 + i * 7, y), (x + 6 + i * 7, y + 6), 2)
            pygame.draw.line(
                surface,
                (0, 120, 140),
                (x + 6 + i * 7, y + 34),
                (x + 6 + i * 7, y + 40),
                2,
            )


def _wrap_text(text, font, max_width):
    """日本語の長文を、指定幅で自動改行して行リストにする"""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
            continue

        buf = ""
        for ch in paragraph:
            test = buf + ch
            if font.size(test)[0] <= max_width:
                buf = test
            else:
                lines.append(buf)
                buf = ch
        if buf:
            lines.append(buf)

    return lines


def _fit_font_size(font_path, base_size, min_size, test_lines, max_width):
    """枠内に収まるように、フォントサイズを自動で下げる。

    - test_lines: 1行ずつ採寸したい文字列のリスト
    - max_width: この幅を超えない最大サイズを探す
    """
    size = base_size
    while size >= min_size:
        f = pygame.font.Font(font_path, size) if font_path else pygame.font.SysFont(None, size)
        ok = True
        for line in test_lines:
            if f.size(line)[0] > max_width:
                ok = False
                break
        if ok:
            return f
        size -= 1
    # 最小サイズでも無理なら最小を返す
    return pygame.font.Font(font_path, min_size) if font_path else pygame.font.SysFont(None, min_size)


def _fit_body_font_to_height(
    font_path,
    base_size,
    min_size,
    blocks,
    max_width,
    max_height,
    line_gap,
    reserved_bottom=0,
):
    """文章ブロック群が「縦方向も」枠内に収まるように本文フォントを自動で下げる。

    blocks: [(text, is_heading_bool), ...]
      - is_heading_bool=True の行は、本文とは別の見出しフォントで描く前提なので、
        ここでは採寸にだけ使う（見出しは別途 fit する）。

    戻り値: (body_font, chosen_size)
    """

    size = base_size
    while size >= min_size:
        bf = pygame.font.Font(font_path, size) if font_path else pygame.font.SysFont(None, size)
        total_h = 0
        for text, is_heading in blocks:
            if text.strip() == "":
                total_h += bf.get_height() + line_gap
                continue
            # 見出しも一応同じ幅で折返しして採寸（実際は別フォントだが、安全側で）
            lines = _wrap_text(text, bf, max_width)
            for _ in lines:
                total_h += bf.get_height() + line_gap
        if total_h + reserved_bottom <= max_height:
            return bf, size
        size -= 1
    bf = pygame.font.Font(font_path, min_size) if font_path else pygame.font.SysFont(None, min_size)
    return bf, min_size


def _draw_text_columns(screen, rect, font, color, text, max_cols=2, line_gap=4, pad=22):
    """文章を枠内に収めるため、必要なら2段組（最大 max_cols）で描画する。

    - まず1段で収まるか計算し、収まらなければ2段組にする。
    - 返り値: (used_cols, bottom_y)
    """
    x0 = rect.x + pad
    y0 = rect.y + pad
    w = rect.width - pad * 2
    h = rect.height - pad * 2

    cols = 1
    col_w = w
    lines = _wrap_text(text, font, col_w)
    needed_h = len(lines) * (font.get_height() + line_gap)
    if needed_h > h and max_cols >= 2:
        cols = 2
        col_w = (w - 24) // 2
        lines = _wrap_text(text, font, col_w)

    # 描画
    col = 0
    yy = y0
    for ln in lines:
        # 空行
        if ln == "":
            yy += font.get_height() + line_gap
        else:
            s = font.render(ln, True, color)
            screen.blit(s, (x0 + col * (col_w + 24), yy))
            yy += font.get_height() + line_gap

        if yy + font.get_height() > y0 + h and cols >= 2 and col == 0:
            # 次の列へ
            col = 1
            yy = y0
        elif yy + font.get_height() > y0 + h and col == 1:
            # 2列でも溢れる場合は打ち切り
            break

    return cols, rect.bottom - pad


def _font_point_size(font_obj):
    """pygame.font.Font から point size を直接は取れないので、近似として高さを返す。"""
    return max(10, int(font_obj.get_height() * 0.85))


def _draw_panel(screen, rect, alpha=210):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((255, 255, 255, alpha))
    screen.blit(panel, (rect.x, rect.y))
    pygame.draw.rect(screen, (20, 40, 70), rect, 4, border_radius=18)


def _find_japanese_font_path():
    """よくある日本語フォントをOS内から探してパスを返す（なければ None）。

    - ここで見つかったパスを pygame.font.Font(path, size) に渡すと文字化けを回避できる。
    - なるべく Linux でよく入っている候補を優先。
    """

    candidates = [
        # Noto (推奨)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
        # IPA
        "/usr/share/fonts/truetype/ipaexg/ipaexg.ttf",
        "/usr/share/fonts/truetype/ipaexg/ipaexm.ttf",
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
        # Takao / VL
        "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-PGothic-Regular.ttf",
    ]

    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _make_fonts():
    """日本語が確実に出るフォントを優先して生成。"""
    font_path = _find_japanese_font_path()

    # ここでは「基準サイズ」を返すだけ（実際の最終サイズ調整は run() の枠サイズを見て行う）
    if font_path:
        return (
            pygame.font.Font(font_path, 64),
            pygame.font.Font(font_path, 40),
            pygame.font.Font(font_path, 28),
            pygame.font.Font(font_path, 24),
            font_path,
        )

    return (
        pygame.font.SysFont(None, 64),
        pygame.font.SysFont(None, 40),
        pygame.font.SysFont(None, 28),
        pygame.font.SysFont(None, 24),
        None,
    )


def run(w=1000, h=600):
    # NOTE:
    # This screen is used both as a standalone script and as a scene launched
    # from the integrated game.
    #
    # Therefore we must NOT call pygame.quit() when leaving this screen,
    # otherwise we would shut down the whole game.
    # We also avoid re-calling pygame.init() if pygame is already initialized.
    if not pygame.get_init():
        pygame.init()

    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("ルール説明（背景単体）")
    clock = pygame.time.Clock()

    # 日本語フォントを探して明示指定（文字化け対策）
    title_font, head_font, body_font, small_font, font_path = _make_fonts()

    t = 0.0
    page = 1  # 1: ルール説明 / 2: 敵・アイテム図鑑
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_RETURN:
                    page = 2 if page == 1 else 1
                elif e.key == pygame.K_SPACE:
                    running = False

        # -------------------------
        # 背景（軽い動き：グラデ + うっすらスキャン線）
        # -------------------------
        top = (210, 235, 255)
        mid = (235, 250, 255)
        for y in range(h):
            u = y / max(1, (h - 1))
            c = (
                int(top[0] * (1 - u) + mid[0] * u),
                int(top[1] * (1 - u) + mid[1] * u),
                int(top[2] * (1 - u) + mid[2] * u),
            )
            pygame.draw.line(screen, c, (0, y), (w, y))

        # スキャン線（ほぼ静止、ちょい動く）
        scan_y = int((t * 55) % 12)
        for y in range(scan_y, h, 12):
            pygame.draw.line(screen, (180, 205, 230), (0, y), (w, y), 1)

        # -------------------------
        # パネル配置
        # -------------------------
        margin = 26

        # ページ構成
        # - ページ1：大パネル1枚（全文ルール）
        # - ページ2：大パネル1枚（敵・アイテム図鑑：文章の中に絵を入れる）
        main_rect = pygame.Rect(margin, margin, w - margin * 2, h - margin * 2)
        _draw_panel(screen, main_rect, alpha=215)
        left_rect = main_rect
        right_rect = None

        # フォント警告（日本語フォントが見つからないときだけ表示）
        # 画面の邪魔にならないよう、右下に小さく表示
        if not font_path:
            warn = "※日本語フォントが見つからないため、環境によっては文字化けします（Noto/IPA等を導入）"
            wf = _fit_font_size(font_path, 20, 12, [warn], w - margin * 2)
            s = wf.render(warn, True, (140, 0, 0))
            screen.blit(s, (w - margin - s.get_width(), h - margin - s.get_height()))

        # 画面共通：枠幅
        text_area_w = left_rect.width - 36

        # 共通：見出し/本文フォントは「枠に入る」こと優先
        head_font_fit = _fit_font_size(font_path, 30, 14, ["操作", "目的", "注意", "必殺技（ゲージ）", "敵", "アイテム"], text_area_w)
        body_font_fit = _fit_font_size(
            font_path,
            24,
            12,
            [
                "・矢印キー：移動",
                "・SPACE：スプレー攻撃（右方向に連射）",
                "・ENTER：必殺技（ゲージMAXのときだけ発動）",
                "左側のPCをウイルスから守ろう。",
                "スコアが15を超えるとBOSSが出現。BOSSを倒せばクリア。",
                "ウイルスが左端（PC）に到達するとHPが減る。",
                "敵を倒すたびにゲージが+1（最大5）。",
                "ワクチン：10秒 攻撃が強化（弾が増える/広がる）",
            ],
            text_area_w,
        )

        # 操作ヒント（小さく右下、重ならないように）
        hint = "Enter:ページ切替 / Space:閉じる / Esc:閉じる"
        hint_max_w = (w - margin * 2 - 18)
        hint_font = _fit_font_size(font_path, 20, 12, [hint], hint_max_w)
        hint_s = hint_font.render(hint, True, (0, 0, 0))
        hx = left_rect.right - 18 - hint_s.get_width()
        hy = left_rect.bottom - 14 - hint_s.get_height()
        screen.blit(hint_s, (hx, hy))

        # -------------------------
        # ページ1：ルール説明
        # -------------------------
        if page == 1:
            title = "ルール説明"
            title_font_fit = _fit_font_size(font_path, 64, 30, [title], text_area_w)
            title_s = title_font_fit.render(title, True, (0, 45, 120))
            screen.blit(title_s, (left_rect.x + 18, left_rect.y + 16))

            # ページ1：要望に合わせて「左=目的+注意」「右=操作」
            # すべて箇条書きにする
            body_top = left_rect.y + 16 + title_s.get_height() + 14
            body_h = left_rect.bottom - 26 - body_top - 46
            body_w = left_rect.width - 44
            body_x = left_rect.x + 22

            gap = 26
            col_w = (body_w - gap) // 2
            left_col = pygame.Rect(body_x, body_top, col_w, body_h)
            right_col = pygame.Rect(body_x + col_w + gap, body_top, col_w, body_h)

            # 見出しは小さめに
            head_font_p1 = _fit_font_size(font_path, 26, 12, ["目的", "注意", "操作"], col_w)
            body_font_p1 = _fit_font_size(
                font_path,
                22,
                11,
                [
                    "・左側のPCをウイルスから守る",
                    "・ウイルスを倒してスコアを稼ぐ",
                    "・スコア15でBOSS出現 → 倒すとクリア",
                    "・左端（PC）に到達するとHPが減る",
                    "・HPが0でゲームオーバー",
                    "・矢印キー：移動",
                    "・SPACE：スプレー攻撃（右方向）",
                    "・ENTER：必殺技（ゲージMAXで全消し）",
                ],
                col_w,
            )
            line_gap = 4

            def draw_bullets(block_title, bullets, rect):
                y = rect.y
                # 見出し
                hs = head_font_p1.render(block_title, True, (20, 40, 70))
                screen.blit(hs, (rect.x, y))
                y += hs.get_height() + 8
                # 箇条書き
                for b in bullets:
                    for ln in _wrap_text(b, body_font_p1, rect.width):
                        s = body_font_p1.render(ln, True, (0, 0, 0))
                        screen.blit(s, (rect.x + 4, y))
                        y += s.get_height() + line_gap
                    y += 2
                return y

            # 左：目的 + 注意
            yL = draw_bullets(
                "目的",
                [
                    "・左側のPCをウイルスから守る",
                    "・ウイルスを倒してスコアを稼ぐ",
                    "・スコア15でBOSS出現 → 倒すとクリア",
                ],
                left_col,
            )
            yL += 14
            # 注意ブロックは、残り高さが足りない場合に備え、見出しを詰めて描画
            left_col2 = pygame.Rect(left_col.x, yL, left_col.width, left_col.bottom - yL)
            draw_bullets(
                "注意",
                [
                    "・ウイルスが左端（PC）に到達するとHPが減る",
                    "・HPが0でゲームオーバー",
                    "・敵を倒すとゲージ+1（最大5）",
                ],
                left_col2,
            )

            # 右：操作
            draw_bullets(
                "操作",
                [
                    "・矢印キー：移動",
                    "・SPACE：スプレー攻撃（右方向）",
                    "・ENTER：必殺技（ゲージMAXで全消し）",
                ],
                right_col,
            )

        # -------------------------
        # ページ2：敵・アイテム図鑑
        # -------------------------
        else:
            title = "敵・アイテム図鑑"
            title_font_fit = _fit_font_size(font_path, 64, 30, [title], text_area_w)
            title_s = title_font_fit.render(title, True, (0, 45, 120))
            screen.blit(title_s, (left_rect.x + 18, left_rect.y + 16))

            y = left_rect.y + 16 + title_s.get_height() + 14

            # ページ2：確実に下まで入りきり、下に空白が残るように強めに縮小
            # - 見出し/本文をさらに小さく
            # - アイコン枠も縮小
            # - 行間も詰める
            head_font_fit = _fit_font_size(font_path, 22, 11, ["敵（ウイルス）", "アイテム"], text_area_w)
            body_font_fit = _fit_font_size(
                font_path,
                20,
                10,
                [
                    "赤ウイルス：HP1 / 倒すと +1点",
                    "紫ウイルス：HP2 / 倒すと +3点（速い）",
                    "BOSS：HP10 / スコア15で出現。倒すとクリア",
                    "PATCH：HP +20（最大100）",
                    "ワクチン：10秒 攻撃強化（弾が増える/広がる）",
                    "SSD：10秒 移動速度UP",
                ],
                text_area_w - 140,
            )
            row_gap = 2
            # ページ2：1枚パネルで、文章の中に「絵（アイコン）」を並べて説明
            # レイアウト：左にアイコン、右に説明文
            col_icon_x = left_rect.x + 26
            col_text_x = col_icon_x + 66
            content_w = left_rect.right - 18 - col_text_x

            # 見出し
            enemy_h = head_font_fit.render("敵（ウイルス）", True, (20, 40, 70))
            screen.blit(enemy_h, (left_rect.x + 18, y))
            y += enemy_h.get_height() + 6

            def draw_row_virus(vtype, text, y0):
                box = pygame.Rect(col_icon_x - 6, y0 - 2, 48, 48)
                pygame.draw.rect(screen, (230, 235, 245), box, border_radius=10)
                pygame.draw.rect(screen, (160, 175, 195), box, 2, border_radius=10)

                # ウイルス絵は小さく描く（別サーフェスに描いて縮小）
                icon = pygame.Surface((48, 48), pygame.SRCALPHA)
                draw_virus(icon, vtype, 24, 24)
                # さらに少し縮めて余白を作る
                icon = pygame.transform.smoothscale(icon, (42, 42))
                screen.blit(icon, (col_icon_x - 3, y0 + 1))

                yy = y0 + 3
                for ln in _wrap_text(text, body_font_fit, content_w):
                    s = body_font_fit.render(ln, True, (0, 0, 0))
                    screen.blit(s, (col_text_x, yy))
                    yy += s.get_height() + 3
                return max(y0 + 52, yy + 2)

            y = draw_row_virus("normal", "赤ウイルス：HP1 / 倒すと +1点", y)
            y += row_gap
            y = draw_row_virus("strong", "紫ウイルス：HP2 / 倒すと +3点（速い）", y)
            y += row_gap
            y = draw_row_virus("boss", "BOSS：HP10 / スコア15で出現。倒すとクリア", y)
            y += 8

            item_h = head_font_fit.render("アイテム", True, (20, 40, 70))
            screen.blit(item_h, (left_rect.x + 18, y))
            y += item_h.get_height() + 6

            def draw_row_item(itype, text, y0):
                box = pygame.Rect(col_icon_x - 6, y0 - 2, 48, 48)
                pygame.draw.rect(screen, (230, 235, 245), box, border_radius=10)
                pygame.draw.rect(screen, (160, 175, 195), box, 2, border_radius=10)

                # アイテム絵も縮小（別サーフェス→縮小）
                icon = pygame.Surface((48, 48), pygame.SRCALPHA)
                # 元の draw_item は 40x40 想定なので、中央寄せ
                draw_item(icon, itype, 4, 4)
                icon = pygame.transform.smoothscale(icon, (42, 42))
                screen.blit(icon, (col_icon_x - 3, y0 + 1))

                yy = y0 + 3
                for ln in _wrap_text(text, body_font_fit, content_w):
                    s = body_font_fit.render(ln, True, (0, 0, 0))
                    screen.blit(s, (col_text_x, yy))
                    yy += s.get_height() + 3
                return max(y0 + 52, yy + 2)

            y = draw_row_item("patch", "PATCH：HP +20（最大100）", y)
            y += row_gap
            y = draw_row_item("vaccine", "ワクチン：10秒 攻撃強化（弾が増える/広がる）", y)
            y += row_gap
            y = draw_row_item("ssd", "SSD：10秒 移動速度UP", y)

            # 念のため、下に空白を確保するための目安ライン（デバッグしたい場合は有効化）
            # pygame.draw.line(screen, (220, 80, 80), (left_rect.x + 18, left_rect.bottom - 70), (left_rect.right - 18, left_rect.bottom - 70), 1)

            # 右下に戻り案内

        # ※操作ヒントは右下に常時表示（上の hint 部分）

        pygame.display.flip()

    # IMPORTANT:
    # When used from the integrated game, we must NOT call pygame.quit() nor
    # pygame.display.quit(). Both will de-initialize the video subsystem and the
    # main game loop will crash on the next pygame.event.get().
    #
    # So we simply return here. If this file is executed standalone, the process
    # ends anyway, so no explicit quit is required.
    return


if __name__ == "__main__":
    run()
