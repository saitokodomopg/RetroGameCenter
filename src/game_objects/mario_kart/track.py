"""コース形状（スタジアム型）・オントラック判定・周回検出。

中心線はスタジアム型（角丸長方形）: 直線区間2本（y = ±R, x∈[-half, half]）と
両端の半円（中心 (±half, 0), 半径 R）で構成される。すべての関数は numpy 配列・
python の float どちらでも動くようにベクトル演算（np.where 等）で書く。
これにより renderer.py の全画面一括計算と、kart.py の1点判定の両方に使い回せる。
"""

import math

import numpy as np

from config import (
    MK_TRACK_STRAIGHT_HALF, MK_TRACK_RADIUS,
    MK_TRACK_ROAD_HALF_WIDTH, MK_TRACK_CURB_WIDTH,
)

SURFACE_ROAD = 0
SURFACE_CURB = 1
SURFACE_GRASS = 2

# フィニッシュライン: 上側の直線区間中央（x=0, y=+R 付近）を通過方向 +x でまたぐ
FINISH_LINE_X = 0.0
FINISH_LINE_Y = MK_TRACK_RADIUS

# centerline_point(t) のセグメント長（周回一周ぶんの弧長）
_TOP_LEN = 2 * MK_TRACK_STRAIGHT_HALF
_ARC_LEN = math.pi * MK_TRACK_RADIUS
TOTAL_LENGTH = 2 * _TOP_LEN + 2 * _ARC_LEN


def distance_to_centerline(x, y):
    """点 (x, y) から中心線までの符号なし距離。x, y は numpy 配列可。"""
    half = MK_TRACK_STRAIGHT_HALF
    r = MK_TRACK_RADIUS

    straight_dist = np.minimum(np.abs(y - r), np.abs(y + r))

    right_dx = x - half
    right_dist = np.abs(np.sqrt(right_dx * right_dx + y * y) - r)

    left_dx = x + half
    left_dist = np.abs(np.sqrt(left_dx * left_dx + y * y) - r)

    return np.where(x > half, right_dist, np.where(x < -half, left_dist, straight_dist))


def classify(x, y):
    """SURFACE_ROAD / SURFACE_CURB / SURFACE_GRASS のいずれかを返す（ベクトル化）。"""
    d = distance_to_centerline(x, y)
    return np.where(
        d <= MK_TRACK_ROAD_HALF_WIDTH, SURFACE_ROAD,
        np.where(d <= MK_TRACK_ROAD_HALF_WIDTH + MK_TRACK_CURB_WIDTH, SURFACE_CURB, SURFACE_GRASS))


def classify_and_param(x, y):
    """classify() と arc_length_param() を一度の計算でまとめて返す（renderer.py の
    毎フレーム全画面計算用。sqrt/arctan2 の重複を避けて負荷を下げる）。
    戻り値: (code, s)
    """
    half = MK_TRACK_STRAIGHT_HALF
    r = MK_TRACK_RADIUS

    straight_dist = np.minimum(np.abs(y - r), np.abs(y + r))

    right_dx = x - half
    right_r = np.sqrt(right_dx * right_dx + y * y)
    right_dist = np.abs(right_r - r)
    right_angle = np.arctan2(y, right_dx)

    left_dx = x + half
    left_r = np.sqrt(left_dx * left_dx + y * y)
    left_dist = np.abs(left_r - r)
    left_angle = np.arctan2(y, left_dx)

    is_right = x > half
    is_left = x < -half

    d = np.where(is_right, right_dist, np.where(is_left, left_dist, straight_dist))
    s = np.where(is_right, r * right_angle, np.where(is_left, r * left_angle, x))

    code = np.where(
        d <= MK_TRACK_ROAD_HALF_WIDTH, SURFACE_ROAD,
        np.where(d <= MK_TRACK_ROAD_HALF_WIDTH + MK_TRACK_CURB_WIDTH, SURFACE_CURB, SURFACE_GRASS))
    return code, s


def is_on_track(x, y):
    """芝生（オフトラック）でなければ True。路面・縁石はどちらもオントラック扱い。"""
    d = distance_to_centerline(x, y)
    return bool(d <= MK_TRACK_ROAD_HALF_WIDTH + MK_TRACK_CURB_WIDTH)


def arc_length_param(x, y):
    """中心線に沿ったおおよその位置（縁石の縞模様の周期に使う近似パラメータ）。"""
    half = MK_TRACK_STRAIGHT_HALF
    r = MK_TRACK_RADIUS
    right_angle = np.arctan2(y, x - half)
    left_angle = np.arctan2(y, x + half)
    return np.where(x > half, r * right_angle, np.where(x < -half, r * left_angle, x))


def centerline_point(t):
    """弧長パラメータ t（0..TOTAL_LENGTH, 進行方向=フィニッシュラインを +x にまたぐ向き）
    に対応する中心線上のワールド座標 (x, y) を返す。CPU オートパイロットの
    目標点算出に使う（フェーズA検証スクリプトのロジックを本実装へ移設）。

    セグメント順: 上直線 → 右カーブ → 下直線 → 左カーブ（時計回り）。
    """
    half = MK_TRACK_STRAIGHT_HALF
    r = MK_TRACK_RADIUS
    t = t % TOTAL_LENGTH

    if t < _TOP_LEN:
        return -half + t, r
    if t < _TOP_LEN + _ARC_LEN:
        a = t - _TOP_LEN
        theta = math.pi / 2 - (a / r)
        return half + r * math.cos(theta), r * math.sin(theta)
    if t < 2 * _TOP_LEN + _ARC_LEN:
        a = t - (_TOP_LEN + _ARC_LEN)
        return half - a, -r
    a = t - (2 * _TOP_LEN + _ARC_LEN)
    theta = -math.pi / 2 - (a / r)
    return -half + r * math.cos(theta), r * math.sin(theta)


def crossed_finish_line(prev_x, prev_y, cur_x, cur_y):
    """前フレーム→今フレームでフィニッシュラインを正方向（+x）にまたいだら True。"""
    if not (prev_x < FINISH_LINE_X <= cur_x):
        return False
    y = cur_y
    return abs(y - FINISH_LINE_Y) <= MK_TRACK_ROAD_HALF_WIDTH
