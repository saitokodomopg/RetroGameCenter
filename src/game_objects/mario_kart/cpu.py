"""CPU オートパイロット。コース中心線上の少し先の点を追いかける単純な追従制御。

フェーズA の検証スクリプトで使ったロジック（目標点への角度誤差から操舵、
誤差が大きいときはアクセルを緩める）を本実装へ移設したもの。
"""

import math

from game_objects.mario_kart import track
from config import (
    MK_CPU_LOOKAHEAD_BASE, MK_CPU_STEER_GAIN, MK_CPU_ACCEL_ANGLE_LIMIT,
)


def _normalize_angle(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


class CpuDriver:
    def __init__(self, kart, start_progress):
        self.kart = kart
        self.lookahead_t = start_progress

    def control(self, dt):
        """(accel_input, steer_input) を返す。kart.update() にそのまま渡せる形式。"""
        self.lookahead_t += MK_CPU_LOOKAHEAD_BASE * self.kart.max_speed_scale * dt
        tx, ty = track.centerline_point(self.lookahead_t)
        desired_heading = math.atan2(ty - self.kart.y, tx - self.kart.x)
        err = _normalize_angle(desired_heading - self.kart.heading)

        steer_input = max(-1.0, min(1.0, err / MK_CPU_STEER_GAIN))
        accel_input = 1 if abs(err) < MK_CPU_ACCEL_ANGLE_LIMIT else 0
        return accel_input, steer_input
