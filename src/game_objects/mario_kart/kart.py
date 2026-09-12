"""カートの物理（加速・操舵・オフトラック減速・スピンアウト）。
ドリフトなしの簡易アーケード物理。自機・CPU の両方でこのクラスを使い回す。
"""

import math

from config import (
    MK_MAX_SPEED, MK_MAX_REVERSE_SPEED, MK_OFFTRACK_MAX_SPEED,
    MK_ACCEL, MK_BRAKE, MK_DRAG, MK_OFFTRACK_EXTRA_DRAG,
    MK_TURN_RATE, MK_TURN_MIN_SPEED, MK_STUN_DURATION,
)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Kart:
    def __init__(self, x, y, heading=0.0, max_speed_scale=1.0):
        self.x = x
        self.y = y
        self.heading = heading  # ラジアン。0 = +x 方向（上側直線をフィニッシュラインへ向かう向き）
        self.speed = 0.0
        self.max_speed_scale = max_speed_scale  # CPU ごとの最高速のばらつきに使う
        self.stun_timer = 0.0

    @property
    def stunned(self):
        return self.stun_timer > 0.0

    def hit(self):
        """バナナ・こうらに当たったときのスピンアウト処理。"""
        self.stun_timer = MK_STUN_DURATION
        self.speed = 0.0

    def update(self, dt, accel_input, steer_input, on_track):
        if self.stunned:
            self.stun_timer -= dt
            accel_input = 0
            steer_input = 0

        if accel_input > 0:
            self.speed += MK_ACCEL * dt
        elif accel_input < 0:
            self.speed -= MK_BRAKE * dt

        self.speed -= self.speed * MK_DRAG * dt
        if not on_track:
            self.speed -= self.speed * MK_OFFTRACK_EXTRA_DRAG * dt

        max_speed = (MK_MAX_SPEED if on_track else MK_OFFTRACK_MAX_SPEED) * self.max_speed_scale
        self.speed = _clamp(self.speed, MK_MAX_REVERSE_SPEED, max_speed)

        if abs(self.speed) > MK_TURN_MIN_SPEED:
            direction = 1.0 if self.speed > 0 else -1.0
            self.heading += steer_input * MK_TURN_RATE * dt * direction

        self.x += math.cos(self.heading) * self.speed * dt
        self.y += math.sin(self.heading) * self.speed * dt

    def heading_vector(self):
        return math.cos(self.heading), math.sin(self.heading)

    def right_vector(self):
        return -math.sin(self.heading), math.cos(self.heading)
