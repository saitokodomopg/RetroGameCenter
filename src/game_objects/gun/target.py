"""ダックハント風ガンシューティングの的（ターゲット）ロジック。

pygame に依存しない座標計算のみを持つ（ヘッドレスで検証できるようにするため）。
描画・SE・入力判定は scenes.duck_hunt_scene 側の責務。
"""

import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GUN_TOP_BAR_H, GUN_BOTTOM_BAR_H,
    GUN_TARGET_TABLE, GUN_AIM_ASSIST,
    GUN_BASE_LIFETIME, GUN_MIN_LIFETIME, GUN_LIFETIME_STEP,
    GUN_SPEED_STEP, GUN_HIT_FLASH_TIME,
)

PLAY_TOP = GUN_TOP_BAR_H
PLAY_BOTTOM = SCREEN_HEIGHT - GUN_BOTTOM_BAR_H

# 画面外に完全に出たとみなす余裕（px）。この分だけ余分に飛んでから消える。
_OFFSCREEN_MARGIN = 60


class Target:
    """1体の的。座標は左上原点・中心座標で管理する。"""

    def __init__(self, kind, x0, y0, vx, vy, radius, score, lifetime):
        self.kind = kind
        self.x0 = x0
        self.y0 = y0
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.score = score
        self.lifetime = lifetime
        self.age = 0.0
        self.x = x0
        self.y = y0
        self.resolved = False  # 命中 or 逃した処理が済んだら True
        self.hit = False       # 命中演出中か
        self.hit_timer = 0.0

    def mark_hit(self):
        """命中演出を開始する。以後 update() では位置を動かさず点滅させる。"""
        self.hit = True
        self.hit_timer = 0.0

    def is_hit_done(self):
        return self.hit and self.hit_timer >= GUN_HIT_FLASH_TIME

    def update(self, dt):
        if self.hit:
            self.hit_timer += dt
            return
        self.age += dt
        if self.kind == "UFO":
            self.x = self.x0 + self.vx * self.age
            self.y = self.y0 + math.sin(self.age * 3) * 10
        else:  # BIRD（デフォルト）
            self.x = self.x0 + self.vx * self.age
            self.y = self.y0 + self.vy * self.age + math.sin(self.age * 6) * 6

    def is_expired(self):
        """寿命切れ、または画面外に完全に出たら True（＝逃した扱い）。"""
        if self.age >= self.lifetime:
            return True
        if self.x < -_OFFSCREEN_MARGIN or self.x > SCREEN_WIDTH + _OFFSCREEN_MARGIN:
            return True
        if self.y < -_OFFSCREEN_MARGIN or self.y > SCREEN_HEIGHT + _OFFSCREEN_MARGIN:
            return True
        return False

    def hit_test(self, px, py):
        """(px, py) がこの的に当たっているか（アシスト込みの判定）。"""
        dx = px - self.x
        dy = py - self.y
        reach = self.radius + GUN_AIM_ASSIST
        return dx * dx + dy * dy <= reach * reach


def _round_speed_mult(round_no):
    return 1.0 + (round_no - 1) * GUN_SPEED_STEP


def _round_lifetime(round_no):
    return max(GUN_MIN_LIFETIME, GUN_BASE_LIFETIME - (round_no - 1) * GUN_LIFETIME_STEP)


def _pick_kind(rng):
    kinds = list(GUN_TARGET_TABLE.keys())
    weights = [GUN_TARGET_TABLE[k]["weight"] for k in kinds]
    return rng.choices(kinds, weights=weights, k=1)[0]


def make_target(round_no, rng=None):
    """round_no のラウンド用に的を1体生成する。

    左右どちらかの端から出現し、画面の反対側へ向かって飛ぶ。
    速度はラウンドが進むほど `_round_speed_mult` で速くなる。
    """
    rng = rng or random
    kind = _pick_kind(rng)
    params = GUN_TARGET_TABLE[kind]
    speed = params["speed"] * _round_speed_mult(round_no)
    lifetime = _round_lifetime(round_no)

    from_left = rng.random() < 0.5
    y0 = rng.uniform(PLAY_TOP + 30, PLAY_BOTTOM - 30)

    if from_left:
        x0 = -_OFFSCREEN_MARGIN * 0.5
        vx = speed
    else:
        x0 = SCREEN_WIDTH + _OFFSCREEN_MARGIN * 0.5
        vx = -speed

    if kind == "BIRD":
        # ゆるい斜め方向（上下どちらかへ緩やかに移動しつつ左右へ進む）
        vy = rng.choice([-1, 1]) * speed * 0.35
    else:
        vy = 0.0

    return Target(kind, x0, y0, vx, vy, params["radius"], params["score"], lifetime)
