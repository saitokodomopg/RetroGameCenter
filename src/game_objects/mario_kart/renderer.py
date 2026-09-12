"""Mode7風スキャンライン描画。画面下半分の各行をワールド平面のアフィン変換として
一括計算し（numpy）、路面・縁石・芝生を塗り分ける。

各行 row（0 = 地平線直下、大きいほど画面下＝カメラに近い）について：
    z(row)       = カメラ高さ * スケール / (row + 1)   … 前方距離（遠近の要）
    world_w(row) = z(row) * (画面幅 / 焦点距離)         … その行で画面に映る横幅
行内の各列は、中心点から左右に world_w/2 ずつ広がる線形補間でワールド座標を得る。

パフォーマンスのため、実際の計算は `_RENDER_SCALE` 分の1に間引いた解像度で行い、
`pygame.transform.scale` で画面サイズへ拡大する（レトロなドット感とも相性が良い）。
"""

import numpy as np
import pygame

from game_objects.mario_kart import track
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    MK_CAM_HEIGHT, MK_CAM_BACK, MK_HORIZON_Y, MK_PROJ_SCALE, MK_FOCAL_LENGTH,
    MK_CURB_STRIPE_LEN,
    MK_COLOR_SKY_TOP, MK_COLOR_SKY_BOTTOM, MK_COLOR_ROAD, MK_COLOR_ROAD_DARK,
    MK_COLOR_CURB_A, MK_COLOR_CURB_B, MK_COLOR_GRASS, MK_COLOR_GRASS_DARK,
    MK_BILLBOARD_MIN_Z, MK_BILLBOARD_MAX_Z,
)

_RENDER_SCALE = 3  # 実計算は画面解像度の 1/3 で行い、最後に拡大する

_ROW_COUNT = SCREEN_HEIGHT - MK_HORIZON_Y
_SMALL_ROWS_N = (_ROW_COUNT + _RENDER_SCALE - 1) // _RENDER_SCALE
_SMALL_W = (SCREEN_WIDTH + _RENDER_SCALE - 1) // _RENDER_SCALE

# 実際の行番号（0=地平線直下）を間引いたインデックスから復元する
_ROWS = (np.arange(_SMALL_ROWS_N, dtype=np.float32) * _RENDER_SCALE)
_COLS_T = np.linspace(-0.5, 0.5, _SMALL_W, dtype=np.float32)

_Z = (MK_CAM_HEIGHT * MK_PROJ_SCALE / (_ROWS + 1.0)).astype(np.float32)      # (R,)
_WORLD_W = (_Z * (SCREEN_WIDTH / MK_FOCAL_LENGTH)).astype(np.float32)        # (R,)

# 地平線付近ほど霧で空色に溶け込ませる（遠方のエイリアシングを隠す）
_DEPTH_T = _ROWS / max(1, _ROW_COUNT - 1)
_FOG = np.clip(_DEPTH_T ** 0.25, 0.0, 1.0).astype(np.float32)[:, None, None]  # (R,1,1)

_ROAD = np.array(MK_COLOR_ROAD, dtype=np.float32)
_ROAD_DARK = np.array(MK_COLOR_ROAD_DARK, dtype=np.float32)
_CURB_A = np.array(MK_COLOR_CURB_A, dtype=np.float32)
_CURB_B = np.array(MK_COLOR_CURB_B, dtype=np.float32)
_GRASS = np.array(MK_COLOR_GRASS, dtype=np.float32)
_GRASS_DARK = np.array(MK_COLOR_GRASS_DARK, dtype=np.float32)
_SKY_BOTTOM = np.array(MK_COLOR_SKY_BOTTOM, dtype=np.float32)


def draw_sky(screen):
    for y in range(0, MK_HORIZON_Y, 4):
        t = y / MK_HORIZON_Y
        col = tuple(int(MK_COLOR_SKY_TOP[i] + (MK_COLOR_SKY_BOTTOM[i] - MK_COLOR_SKY_TOP[i]) * t)
                   for i in range(3))
        pygame.draw.rect(screen, col, (0, y, SCREEN_WIDTH, 4))


def draw_ground(screen, kart):
    """kart（game_objects.mario_kart.kart.Kart）視点で地面を描画する。"""
    hx, hy = kart.heading_vector()
    rx, ry = kart.right_vector()
    cam_x = np.float32(kart.x - hx * MK_CAM_BACK)
    cam_y = np.float32(kart.y - hy * MK_CAM_BACK)
    hx, hy, rx, ry = np.float32(hx), np.float32(hy), np.float32(rx), np.float32(ry)

    center_x = cam_x + hx * _Z
    center_y = cam_y + hy * _Z

    world_x = center_x[:, None] + rx * _WORLD_W[:, None] * _COLS_T[None, :]
    world_y = center_y[:, None] + ry * _WORLD_W[:, None] * _COLS_T[None, :]

    surf_code, s = track.classify_and_param(world_x, world_y)

    road_checker = (np.floor(s / 200.0).astype(np.int32) % 2 == 0)[..., None]
    road_color = np.where(road_checker, _ROAD, _ROAD_DARK)

    stripe = (np.floor(s / MK_CURB_STRIPE_LEN).astype(np.int32) % 2 == 0)[..., None]
    curb_color = np.where(stripe, _CURB_A, _CURB_B)

    grass_checker = (
        (np.floor(world_x / 150.0).astype(np.int32) +
         np.floor(world_y / 150.0).astype(np.int32)) % 2 == 0
    )[..., None]
    grass_color = np.where(grass_checker, _GRASS, _GRASS_DARK)

    colors = np.where(
        (surf_code == track.SURFACE_ROAD)[..., None], road_color,
        np.where((surf_code == track.SURFACE_CURB)[..., None], curb_color, grass_color))

    colors = colors * _FOG + _SKY_BOTTOM * (1.0 - _FOG)
    colors = np.clip(colors, 0, 255).astype(np.uint8)

    small_surf = pygame.surfarray.make_surface(np.transpose(colors, (1, 0, 2)))
    ground_surf = pygame.transform.scale(small_surf, (SCREEN_WIDTH, _ROW_COUNT))
    screen.blit(ground_surf, (0, MK_HORIZON_Y))


def project_billboard(camera_kart, world_x, world_y, world_size):
    """camera_kart の視点から見た (world_x, world_y) の位置に、ワールドサイズ
    world_size の看板（ビルボード）を置いたときの画面投影情報を返す。
    画面外・カメラの後方・描画距離外なら None。

    戻り値: (screen_x, ground_y, pixel_size, z) — ground_y は接地面（下端）の y 座標。
    """
    hx, hy = camera_kart.heading_vector()
    rx, ry = camera_kart.right_vector()
    cam_x = camera_kart.x - hx * MK_CAM_BACK
    cam_y = camera_kart.y - hy * MK_CAM_BACK

    dx = world_x - cam_x
    dy = world_y - cam_y
    z = dx * hx + dy * hy
    if z < MK_BILLBOARD_MIN_Z or z > MK_BILLBOARD_MAX_Z:
        return None
    lateral = dx * rx + dy * ry

    world_w_at_z = z * (SCREEN_WIDTH / MK_FOCAL_LENGTH)
    screen_x = SCREEN_WIDTH / 2 + (lateral / world_w_at_z) * SCREEN_WIDTH
    if screen_x < -200 or screen_x > SCREEN_WIDTH + 200:
        return None

    row = MK_CAM_HEIGHT * MK_PROJ_SCALE / z - 1.0
    row = max(0.0, min(_ROW_COUNT - 1.0, row))
    ground_y = MK_HORIZON_Y + row

    pixel_size = world_size * (SCREEN_WIDTH / MK_FOCAL_LENGTH) / z
    return screen_x, ground_y, pixel_size, z


def draw_billboard_rect(screen, camera_kart, world_x, world_y, world_size, color):
    proj = project_billboard(camera_kart, world_x, world_y, world_size)
    if proj is None:
        return
    screen_x, ground_y, size, _z = proj
    if size < 2:
        return
    rect = pygame.Rect(0, 0, int(size), int(size))
    rect.midbottom = (int(screen_x), int(ground_y))
    pygame.draw.rect(screen, color, rect, border_radius=max(1, int(size * 0.18)))


def draw_billboard_circle(screen, camera_kart, world_x, world_y, world_size, color):
    proj = project_billboard(camera_kart, world_x, world_y, world_size)
    if proj is None:
        return
    screen_x, ground_y, size, _z = proj
    if size < 2:
        return
    radius = max(1, int(size / 2))
    pygame.draw.circle(screen, color, (int(screen_x), int(ground_y - radius)), radius)
