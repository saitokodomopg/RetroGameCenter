"""メニュー用のゲームサムネイルを描画する。

本作の方針どおり画像ファイルは使わず、各ゲームらしいミニ絵を pygame の
プリミティブで Surface に描いて返す。1度作った Surface はキャッシュする。
"""

import pygame
from config import (
    COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW, COLOR_GRAY,
    COLOR_GIRDER, COLOR_LADDER, COLOR_BARREL, COLOR_BARREL_BAND,
    COLOR_DK, COLOR_DK_FACE, COLOR_PAULINE, COLOR_RED,
    DK81_COLOR_OIL_DRUM, DK81_COLOR_OIL_BAND, DK81_COLOR_FLAME,
    DK81_COLOR_FLAME_CORE, DK81_COLOR_SKIN,
    COLOR_T_CYAN, COLOR_T_YELLOW, COLOR_T_PURPLE, COLOR_T_GREEN,
    COLOR_T_RED, COLOR_T_BLUE, COLOR_T_ORANGE, COLOR_T_GRID,
    ICE_COLOR_SKY_TOP, ICE_COLOR_SKY_BOT, ICE_COLOR_ICE, ICE_COLOR_ICE_HI,
    ICE_COLOR_ICE_DARK, ICE_COLOR_POPO, ICE_COLOR_POPO_TRIM,
    ICE_COLOR_POPO_FACE, ICE_COLOR_CONDOR, ICE_COLOR_TOPI, ICE_COLOR_HAMMER_HEAD,
)

_cache = {}


def get_thumbnail(key, size):
    """key に対応するサムネイル Surface を size=(w, h) で返す。"""
    cache_key = (key, size)
    if cache_key not in _cache:
        _cache[cache_key] = _render(key, size)
    return _cache[cache_key]


def _render(key, size):
    w, h = size
    surf = pygame.Surface(size)
    surf.fill(COLOR_BLACK)
    drawer = _DRAWERS.get(key, _draw_coming_soon)
    drawer(surf, w, h)
    return surf


# --- 各ゲームのサムネイル ------------------------------------------------

def _draw_donkey_kong(surf, w, h):
    """斜め鉄骨・はしご・コング・樽・ポーリンのミニ絵。"""
    # 斜めに重なる鉄骨（下から上へ、交互に傾ける）
    rows = 4
    margin = int(w * 0.08)
    girder_h = max(3, int(h * 0.045))
    top = int(h * 0.16)
    bottom = int(h * 0.88)
    gap = (bottom - top) / (rows - 1)
    for i in range(rows):
        y = int(bottom - i * gap)
        tilt = int(h * 0.05) * (1 if i % 2 == 0 else -1)
        if i % 2 == 0:
            p1 = (margin, y + tilt)
            p2 = (w - margin, y - tilt)
        else:
            p1 = (margin, y - tilt)
            p2 = (w - margin, y + tilt)
        pygame.draw.line(surf, COLOR_GIRDER, p1, p2, girder_h)

    # はしご（2 本）
    for lx in (int(w * 0.30), int(w * 0.68)):
        pygame.draw.line(surf, COLOR_LADDER, (lx, top), (lx, bottom), 2)
        pygame.draw.line(surf, COLOR_LADDER, (lx + 8, top), (lx + 8, bottom), 2)
        for ry in range(top, bottom, max(6, int(h * 0.05))):
            pygame.draw.line(surf, COLOR_LADDER, (lx, ry), (lx + 8, ry), 2)

    # コング（左上）
    kx, ky = int(w * 0.24), top - int(h * 0.02)
    kw = int(w * 0.20)
    pygame.draw.rect(surf, COLOR_DK, (kx - kw // 2, ky - kw, kw, kw), border_radius=4)
    fw = int(kw * 0.6)
    pygame.draw.rect(surf, COLOR_DK_FACE, (kx - fw // 2, ky - kw + 3, fw, fw), border_radius=3)

    # ポーリン（右上）
    px, py = int(w * 0.80), top - int(h * 0.04)
    pygame.draw.circle(surf, COLOR_DK_FACE, (px, py), max(2, int(w * 0.03)))
    pygame.draw.rect(surf, COLOR_PAULINE,
                     (px - int(w * 0.03), py, int(w * 0.06), int(h * 0.10)))

    # 転がる樽
    for bx, by in ((int(w * 0.55), int(h * 0.45)), (int(w * 0.40), int(h * 0.72))):
        r = max(3, int(w * 0.045))
        pygame.draw.circle(surf, COLOR_BARREL, (bx, by), r)
        pygame.draw.circle(surf, COLOR_BARREL_BAND, (bx, by), r, 1)


def _draw_donkey_kong_81(surf, w, h):
    """DK と同系だがオイルドラムと炎を加えた '81 版。"""
    _draw_donkey_kong(surf, w, h)
    # 左下にオイルドラム＋炎
    dx = int(w * 0.14)
    dy = int(h * 0.86)
    dw, dh = int(w * 0.10), int(h * 0.14)
    pygame.draw.rect(surf, DK81_COLOR_OIL_DRUM,
                     (dx - dw // 2, dy - dh, dw, dh), border_radius=2)
    pygame.draw.line(surf, DK81_COLOR_OIL_BAND,
                     (dx - dw // 2, dy - dh // 2), (dx + dw // 2, dy - dh // 2), 1)
    # 炎（外炎＋芯）
    fx, fy = dx, dy - dh
    pygame.draw.polygon(surf, DK81_COLOR_FLAME, [
        (fx - dw // 3, fy), (fx, fy - int(h * 0.11)), (fx + dw // 3, fy)])
    pygame.draw.polygon(surf, DK81_COLOR_FLAME_CORE, [
        (fx - dw // 6, fy), (fx, fy - int(h * 0.06)), (fx + dw // 6, fy)])
    # 「'81」バッジ
    font = pygame.font.Font(None, max(14, int(h * 0.18)))
    badge = font.render("'81", True, COLOR_YELLOW)
    surf.blit(badge, badge.get_rect(bottomright=(w - 4, h - 3)))


# T スピン風に並べたテトリミノ盤面（列ごとの積み高さと色）
_TETRIS_STACK = [
    (COLOR_T_BLUE, 2), (COLOR_T_BLUE, 2), (COLOR_T_RED, 3), (COLOR_T_GREEN, 4),
    (COLOR_T_ORANGE, 3), (COLOR_T_ORANGE, 1), (COLOR_T_PURPLE, 2),
]


def _draw_tetris(surf, w, h):
    """積み上がったブロックと落下中のミノ。"""
    cols = len(_TETRIS_STACK)
    pad = int(w * 0.10)
    board_w = w - pad * 2
    board_h = int(h * 0.86)
    cell = min(board_w // cols, board_h // 6)
    board_w = cell * cols
    ox = (w - board_w) // 2
    oy = h - int(h * 0.07) - cell  # 最下段

    # グリッド枠
    rows_shown = 6
    pygame.draw.rect(surf, COLOR_T_GRID,
                     (ox - 2, oy - (rows_shown - 1) * cell - 2,
                      board_w + 4, rows_shown * cell + 4), 2)

    def block(cx, cy, color):
        rect = pygame.Rect(cx, cy, cell, cell)
        pygame.draw.rect(surf, color, rect)
        pygame.draw.rect(surf, COLOR_BLACK, rect, 1)
        hi = pygame.Rect(cx + 2, cy + 2, cell - 4, max(2, cell // 4))
        pygame.draw.rect(surf, COLOR_WHITE, hi, 0)

    # 積みブロック
    for c, (color, height) in enumerate(_TETRIS_STACK):
        for r in range(height):
            block(ox + c * cell, oy - r * cell, color)

    # 落下中の T ミノ（上部中央）
    ty = oy - 5 * cell
    tx = ox + 2 * cell
    for dc, dr in ((0, 0), (1, 0), (2, 0), (1, 1)):
        block(tx + dc * cell, ty + dr * cell, COLOR_T_CYAN)


def _draw_ice_climber(surf, w, h):
    """氷の山を登るポポ・氷ブロック（穴あり）・コンドルのミニ絵。"""
    # 空グラデ
    for y in range(0, h, 3):
        t = y / h
        col = (int(ICE_COLOR_SKY_TOP[0] + (ICE_COLOR_SKY_BOT[0] - ICE_COLOR_SKY_TOP[0]) * t),
               int(ICE_COLOR_SKY_TOP[1] + (ICE_COLOR_SKY_BOT[1] - ICE_COLOR_SKY_TOP[1]) * t),
               int(ICE_COLOR_SKY_TOP[2] + (ICE_COLOR_SKY_BOT[2] - ICE_COLOR_SKY_TOP[2]) * t))
        pygame.draw.rect(surf, col, (0, y, w, 3))

    cell = max(8, int(w * 0.12))
    cols = w // cell
    rows = 3
    top = h - rows * cell - int(h * 0.06)

    def ice_block(bx, by):
        r = pygame.Rect(bx, by, cell, cell)
        pygame.draw.rect(surf, ICE_COLOR_ICE, r)
        pygame.draw.rect(surf, ICE_COLOR_ICE_HI, (bx, by, cell, 3))
        pygame.draw.rect(surf, ICE_COLOR_ICE_DARK, r, 1)

    # 3 段の氷床（各段に穴を 1 つ空ける）
    for row in range(rows):
        by = top + row * cell
        gap = 1 + row  # 段ごとに穴の位置をずらす
        for c in range(cols):
            if c == gap:
                continue  # 穴
            ice_block(c * cell, by)

    # ポポ（下段、ハンマーを振り上げる）
    px = int(w * 0.30)
    py = top + rows * cell - cell
    pw = max(8, int(cell * 0.8))
    pygame.draw.rect(surf, ICE_COLOR_POPO, (px, py, pw, cell), border_radius=3)
    pygame.draw.rect(surf, ICE_COLOR_POPO_TRIM, (px, py, pw, 3))
    pygame.draw.rect(surf, ICE_COLOR_POPO_FACE, (px + 2, py + 3, pw - 4, 4))
    # 振り上げたハンマー
    pygame.draw.rect(surf, ICE_COLOR_HAMMER_HEAD, (px + pw - 2, py - 6, 6, 4))

    # トッピー（上段）
    tx = int(w * 0.66)
    ty = top - int(cell * 0.6)
    pygame.draw.ellipse(surf, ICE_COLOR_TOPI, (tx, ty, int(cell * 0.9), int(cell * 0.6)))

    # コンドル（上空）
    cxp, cyp = int(w * 0.72), int(h * 0.16)
    pygame.draw.ellipse(surf, ICE_COLOR_CONDOR, (cxp - 7, cyp - 3, 14, 8))
    pygame.draw.polygon(surf, ICE_COLOR_CONDOR,
                        [(cxp - 5, cyp), (cxp - 18, cyp - 6), (cxp - 6, cyp + 2)])
    pygame.draw.polygon(surf, ICE_COLOR_CONDOR,
                        [(cxp + 5, cyp), (cxp + 18, cyp - 6), (cxp + 6, cyp + 2)])


def _draw_snake(surf, w, h):
    """暗いグリッド上をS字に這うヘビと赤いエサ。"""
    surf.fill((12, 26, 14))
    cell = max(8, int(min(w, h) * 0.12))
    cols = w // cell
    rows = h // cell
    ox = (w - cols * cell) // 2
    oy = (h - rows * cell) // 2
    # うっすらグリッド
    grid = (24, 46, 28)
    for c in range(cols + 1):
        pygame.draw.line(surf, grid, (ox + c * cell, oy), (ox + c * cell, oy + rows * cell), 1)
    for r in range(rows + 1):
        pygame.draw.line(surf, grid, (ox, oy + r * cell), (ox + cols * cell, oy + r * cell), 1)

    def gcell(c, r, color):
        pad = max(1, cell // 8)
        rect = pygame.Rect(ox + c * cell + pad, oy + r * cell + pad,
                           cell - pad * 2, cell - pad * 2)
        pygame.draw.rect(surf, color, rect, border_radius=max(1, cell // 4))

    mid = rows // 2
    body = [(1, mid), (2, mid), (3, mid), (3, mid - 1),
            (3, mid + 1), (4, mid + 1), (5, mid + 1)]
    snake_body = (60, 200, 90)
    snake_head = (120, 240, 130)
    for (c, r) in body[:-1]:
        if 0 <= c < cols and 0 <= r < rows:
            gcell(c, r, snake_body)
    hc, hr = body[-1]
    if 0 <= hc < cols and 0 <= hr < rows:
        gcell(hc, hr, snake_head)
        # 目
        eye = (10, 20, 10)
        ex = ox + hc * cell + cell // 3
        ey = oy + hr * cell + cell // 3
        pygame.draw.circle(surf, eye, (ex, ey), max(1, cell // 8))

    # エサ（赤リンゴ）
    fc, fr = cols - 2, mid - 1
    if 0 <= fc < cols and 0 <= fr < rows:
        cx = ox + fc * cell + cell // 2
        cy = oy + fr * cell + cell // 2
        pygame.draw.circle(surf, COLOR_RED, (cx, cy), max(2, cell // 3))


def _draw_space_invaders(surf, w, h):
    """星空を背景に隊列を組むインベーダーと自機・弾。"""
    surf.fill((6, 6, 16))
    # 星
    import random as _r
    rng = _r.Random(42)
    for _ in range(int(w * h * 0.004)):
        sx, sy = rng.randint(0, w - 1), rng.randint(0, int(h * 0.9))
        surf.fill((150, 150, 170), (sx, sy, 1, 1))

    green = (60, 230, 90)
    unit = max(6, int(w * 0.12))
    gap = max(2, int(w * 0.03))
    cols = 3
    rows = 2
    grid_w = cols * unit + (cols - 1) * gap
    ox = (w - grid_w) // 2
    oy = int(h * 0.14)

    def invader(bx, by, s):
        # 8x8 風ドットパターンを塗る
        pat = [
            "00100100",
            "00111100",
            "01111110",
            "11011011",
            "11111111",
            "01011010",
            "10000001",
            "01000010",
        ]
        px = max(1, s // 8)
        for ry, line in enumerate(pat):
            for rx, ch in enumerate(line):
                if ch == "1":
                    surf.fill(green, (bx + rx * px, by + ry * px, px, px))

    for r in range(rows):
        for c in range(cols):
            invader(ox + c * (unit + gap), oy + r * (unit + gap), unit)

    # 自機（下部の砲台）
    ship = (90, 210, 255)
    sw = int(w * 0.16)
    sh = int(h * 0.06)
    sx = (w - sw) // 2
    sy = h - sh - int(h * 0.05)
    pygame.draw.rect(surf, ship, (sx, sy + sh // 2, sw, sh // 2), border_radius=2)
    pygame.draw.rect(surf, ship, (sx + sw // 2 - 2, sy, 4, sh))
    # 弾
    pygame.draw.rect(surf, COLOR_WHITE, (w // 2 - 1, int(h * 0.5), 2, int(h * 0.1)))


def _draw_breakout(surf, w, h):
    """カラフルなブロックの列・ボール・下部のパドル。"""
    surf.fill((10, 12, 24))
    rows_colors = [(230, 60, 60), (240, 150, 30), (240, 220, 0), (0, 210, 80)]
    pad = int(w * 0.06)
    top = int(h * 0.12)
    brick_w = (w - pad * 2)
    cols = 5
    cell_w = brick_w // cols
    brick_h = max(6, int(h * 0.09))
    for r, color in enumerate(rows_colors):
        for c in range(cols):
            bx = pad + c * cell_w
            by = top + r * (brick_h + 3)
            rect = pygame.Rect(bx + 1, by, cell_w - 2, brick_h)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, COLOR_BLACK, rect, 1)
            hi = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, max(2, brick_h // 3))
            pygame.draw.rect(surf, COLOR_WHITE, hi)

    # パドル
    paddle = (90, 200, 255)
    pw = int(w * 0.28)
    ph = max(5, int(h * 0.05))
    px = (w - pw) // 2 + int(w * 0.08)
    py = h - ph - int(h * 0.06)
    pygame.draw.rect(surf, paddle, (px, py, pw, ph), border_radius=3)

    # ボール
    bx = px + pw // 3
    by = py - int(h * 0.14)
    pygame.draw.circle(surf, COLOR_WHITE, (bx, by), max(3, int(w * 0.03)))


def _draw_wagyan_land(surf, w, h):
    """明るい空と草地・恐竜キャラ（ワギャン風）と星の弾。"""
    # 空
    for y in range(0, h, 3):
        t = y / h
        col = (int(120 + 60 * t), int(190 + 30 * t), 245)
        pygame.draw.rect(surf, col, (0, y, w, 3))
    # 草地
    ground_y = int(h * 0.78)
    pygame.draw.rect(surf, (70, 190, 90), (0, ground_y, w, h - ground_y))
    pygame.draw.rect(surf, (50, 160, 70), (0, ground_y, w, 4))

    # 雲
    cloud = (250, 250, 255)
    for cxp, cyp, cr in ((int(w * 0.2), int(h * 0.2), int(w * 0.06)),
                         (int(w * 0.78), int(h * 0.28), int(w * 0.07))):
        pygame.draw.circle(surf, cloud, (cxp, cyp), cr)
        pygame.draw.circle(surf, cloud, (cxp + cr, cyp + 2), int(cr * 0.8))
        pygame.draw.circle(surf, cloud, (cxp - cr, cyp + 2), int(cr * 0.8))

    # ワギャン（青い恐竜）
    body = (60, 150, 240)
    belly = (200, 235, 255)
    bx = int(w * 0.32)
    by = ground_y
    bw = int(w * 0.20)
    bh = int(h * 0.34)
    pygame.draw.ellipse(surf, body, (bx - bw // 2, by - bh, bw, bh))
    pygame.draw.ellipse(surf, belly, (bx - bw // 4, by - bh * 0.7, bw // 2, int(bh * 0.55)))
    # 頭
    hr = int(bw * 0.55)
    hx, hy = bx, by - bh
    pygame.draw.circle(surf, body, (hx, hy), hr)
    pygame.draw.circle(surf, COLOR_WHITE, (hx + hr // 3, hy - hr // 4), max(2, hr // 4))
    pygame.draw.circle(surf, COLOR_BLACK, (hx + hr // 3, hy - hr // 4), max(1, hr // 8))

    # 星の弾（必殺技）
    star_c = COLOR_YELLOW
    sx, sy = int(w * 0.68), int(h * 0.5)
    sr = int(w * 0.05)
    _draw_star(surf, sx, sy, sr, star_c)


def _draw_star(surf, cx, cy, r, color):
    import math as _m
    pts = []
    for i in range(10):
        ang = -_m.pi / 2 + i * _m.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * _m.cos(ang), cy + rad * _m.sin(ang)))
    pygame.draw.polygon(surf, color, pts)


def _draw_pinball(surf, w, h):
    """縦長の台・バンパー・フリッパー・ボール。"""
    surf.fill((14, 10, 30))
    # 台の外枠（上部は丸く）
    pad = int(w * 0.1)
    table = pygame.Rect(pad, int(h * 0.06), w - pad * 2, int(h * 0.88))
    pygame.draw.rect(surf, (30, 22, 60), table, border_radius=int(w * 0.15))
    pygame.draw.rect(surf, (120, 100, 200), table, 2, border_radius=int(w * 0.15))

    # バンパー（丸）
    bumpers = [(int(w * 0.38), int(h * 0.30), COLOR_RED),
               (int(w * 0.62), int(h * 0.34), (255, 150, 30)),
               (int(w * 0.5), int(h * 0.5), COLOR_YELLOW)]
    for bx, by, color in bumpers:
        pygame.draw.circle(surf, color, (bx, by), int(w * 0.06))
        pygame.draw.circle(surf, COLOR_WHITE, (bx, by), int(w * 0.06), 2)
        pygame.draw.circle(surf, COLOR_WHITE, (bx, by), int(w * 0.025))

    # フリッパー（下部の左右）
    flip = (90, 200, 255)
    fy = int(h * 0.82)
    pygame.draw.polygon(surf, flip, [
        (int(w * 0.32), fy), (int(w * 0.48), fy + int(h * 0.05)),
        (int(w * 0.34), fy + int(h * 0.06))])
    pygame.draw.polygon(surf, flip, [
        (int(w * 0.68), fy), (int(w * 0.52), fy + int(h * 0.05)),
        (int(w * 0.66), fy + int(h * 0.06))])

    # ボール
    pygame.draw.circle(surf, (220, 220, 235), (int(w * 0.58), int(h * 0.68)), int(w * 0.045))
    pygame.draw.circle(surf, COLOR_WHITE, (int(w * 0.565), int(h * 0.665)), int(w * 0.015))


def _draw_mario_kart(surf, w, h):
    """遠近のあるコースを走るカート（赤・青）とアイテムボックス。"""
    # 空
    pygame.draw.rect(surf, (120, 195, 245), (0, 0, w, int(h * 0.42)))
    # 遠景の丘
    pygame.draw.ellipse(surf, (90, 180, 110), (-int(w * 0.2), int(h * 0.22), int(w * 0.7), int(h * 0.3)))
    pygame.draw.ellipse(surf, (80, 170, 100), (int(w * 0.5), int(h * 0.2), int(w * 0.8), int(h * 0.35)))
    # 草地
    pygame.draw.rect(surf, (70, 180, 85), (0, int(h * 0.42), w, h - int(h * 0.42)))

    # 遠近コース（下に向かって広がる台形）
    road = (70, 70, 80)
    horizon = int(h * 0.42)
    pygame.draw.polygon(surf, road, [
        (int(w * 0.42), horizon), (int(w * 0.58), horizon),
        (w, h), (0, h)])
    # センターライン（破線・遠近）
    line = COLOR_YELLOW
    n = 5
    for i in range(n):
        t0 = i / n
        t1 = (i + 0.5) / n
        y0 = horizon + (h - horizon) * t0
        y1 = horizon + (h - horizon) * t1
        lw0 = 1 + int(6 * t0)
        lw1 = 1 + int(6 * t1)
        pygame.draw.polygon(surf, line, [
            (w // 2 - lw0, y0), (w // 2 + lw0, y0),
            (w // 2 + lw1, y1), (w // 2 - lw1, y1)])

    def kart(cx, cy, s, color):
        pygame.draw.rect(surf, (20, 20, 20), (cx - s, cy, s * 2, int(s * 0.5)))  # タイヤ土台
        pygame.draw.rect(surf, color, (cx - int(s * 0.8), cy - int(s * 0.7),
                                       int(s * 1.6), int(s * 0.9)), border_radius=3)
        # ドライバーの頭
        pygame.draw.circle(surf, (250, 210, 170), (cx, cy - int(s * 0.8)), int(s * 0.4))
        pygame.draw.circle(surf, color, (cx, cy - int(s * 0.95)), int(s * 0.42), 2)

    # 手前の赤カート・奥の青カート
    kart(int(w * 0.40), int(h * 0.82), int(w * 0.09), COLOR_RED)
    kart(int(w * 0.62), int(h * 0.60), int(w * 0.055), (40, 90, 230))

    # アイテムボックス（?）
    ib = pygame.Rect(int(w * 0.72), int(h * 0.48), int(w * 0.1), int(w * 0.1))
    pygame.draw.rect(surf, (0, 200, 220), ib, border_radius=3)
    pygame.draw.rect(surf, COLOR_WHITE, ib, 2, border_radius=3)
    qfont = pygame.font.Font(None, int(w * 0.12))
    q = qfont.render("?", True, COLOR_WHITE)
    surf.blit(q, q.get_rect(center=ib.center))


def _draw_puyo_puyo(surf, w, h):
    """盤面に積まれた色とりどりの目つきぷよ。連鎖しそうな並びにする。"""
    surf.fill((14, 14, 26))
    cell = max(8, int(min(w, h) * 0.17))
    cols = w // cell
    rows = h // cell
    ox = (w - cols * cell) // 2
    oy = h - rows * cell - 2
    # うっすらグリッド
    grid = (32, 32, 48)
    for c in range(cols + 1):
        pygame.draw.line(surf, grid, (ox + c * cell, oy),
                         (ox + c * cell, oy + rows * cell), 1)
    for r in range(rows + 1):
        pygame.draw.line(surf, grid, (ox, oy + r * cell),
                         (ox + cols * cell, oy + r * cell), 1)

    def puyo(c, r, color):
        cx = ox + c * cell + cell // 2
        cy = oy + r * cell + cell // 2
        rad = cell // 2 - max(1, cell // 10)
        pygame.draw.circle(surf, color, (cx, cy), rad)
        dark = tuple(max(0, v - 70) for v in color)
        pygame.draw.circle(surf, dark, (cx, cy), rad, 1)
        light = tuple(min(255, v + 70) for v in color)
        pygame.draw.circle(surf, light, (cx - rad // 3, cy - rad // 3),
                           max(1, rad // 4))
        # 目（ぷよぷよらしさの要）
        er = max(2, rad // 3)
        pr = max(1, er // 2)
        for sx in (-1, 1):
            ex = cx + sx * (rad // 3)
            ey = cy - rad // 8
            pygame.draw.circle(surf, COLOR_WHITE, (ex, ey), er)
            pygame.draw.circle(surf, (20, 20, 30), (ex, ey), pr)

    R, G, B, Y = ((235, 70, 70), (70, 210, 90), (70, 120, 235), (240, 210, 60))
    # 下2段を積み上げ、上に落下中の組ぷよを1組浮かせる
    bottom = rows - 1
    layout = [
        (0, bottom, R), (1, bottom, R), (2, bottom, G), (3, bottom, B),
        (0, bottom - 1, R), (1, bottom - 1, Y), (2, bottom - 1, G),
        (0, bottom - 2, Y),
    ]
    for (c, r, color) in layout:
        if 0 <= c < cols and 0 <= r < rows:
            puyo(c, r, color)
    # 落下中の組ぷよ（縦2個）
    fc = min(cols - 2, 3)
    if rows >= 4:
        puyo(fc, 0, G)
        puyo(fc, 1, G)


def _draw_coming_soon(surf, w, h):
    """準備中ゲーム用のプレースホルダ（?マークと点線枠）。"""
    surf.fill((18, 18, 24))
    # 点線風の枠
    step = max(6, int(w * 0.08))
    for x in range(step, w - step, step):
        pygame.draw.line(surf, COLOR_GRAY, (x, int(h * 0.12)),
                         (x + step // 2, int(h * 0.12)), 2)
        pygame.draw.line(surf, COLOR_GRAY, (x, int(h * 0.88)),
                         (x + step // 2, int(h * 0.88)), 2)
    font = pygame.font.Font(None, int(h * 0.6))
    q = font.render("?", True, COLOR_GRAY)
    surf.blit(q, q.get_rect(center=(w // 2, h // 2)))


_DRAWERS = {
    "donkey_kong": _draw_donkey_kong,
    "donkey_kong_81": _draw_donkey_kong_81,
    "tetris": _draw_tetris,
    "ice_climber": _draw_ice_climber,
    "snake": _draw_snake,
    "puyo_puyo": _draw_puyo_puyo,
    "space_invaders": _draw_space_invaders,
    "breakout": _draw_breakout,
    "wagyan_land": _draw_wagyan_land,
    "pinball": _draw_pinball,
    "mario_kart": _draw_mario_kart,
}
