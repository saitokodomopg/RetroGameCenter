"""ピンボールの盤面。壁・スリングショット・バンパー・フリッパーの当たり判定を
すべてローカル座標（盤面左上を原点 (0,0) とする）でまとめる（pygame 非依存）。
"""

import math

from game_objects.pinball.flipper import Flipper
from config import (
    PINBALL_BOARD_W, PINBALL_BOARD_H, PINBALL_LANE_W, PINBALL_LANE_GAP_TOP,
    PINBALL_FUNNEL_TOP_Y, PINBALL_WALL_RESTITUTION, PINBALL_GRAVITY,
    PINBALL_BUMPER_RADIUS, PINBALL_BUMPER_BOOST, PINBALL_BUMPER_SCORE,
    PINBALL_BUMPER_COOLDOWN,
    PINBALL_SLINGSHOT_BOOST, PINBALL_SLINGSHOT_SCORE, PINBALL_SLINGSHOT_COOLDOWN,
    PINBALL_FLIPPER_LENGTH, PINBALL_FLIPPER_THICKNESS, PINBALL_FLIPPER_REST_ANGLE,
    PINBALL_FLIPPER_ACTIVE_ANGLE, PINBALL_FLIPPER_ANGULAR_SPEED,
    PINBALL_FLIPPER_KICK, PINBALL_FLIPPER_PIVOT_OFFSET, PINBALL_LANE_SETTLE_SPEED,
    PINBALL_FLIPPER_HIT_SCORE, PINBALL_FLIPPER_HIT_COOLDOWN,
)

# 1フレームでの移動量がこれを超えたら、すり抜け防止のためサブステップに分割する
_MAX_STEP_DIST = 6.0
_MAX_SUBSTEPS = 12


def _closest_point_on_segment(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    abx, aby = bx - ax, by - ay
    denom = abx * abx + aby * aby
    if denom == 0:
        return a, 0.0
    t = ((px - ax) * abx + (py - ay) * aby) / denom
    t = max(0.0, min(1.0, t))
    return (ax + abx * t, ay + aby * t), t


class Table:
    """盤面のジオメトリと衝突解決。ボールは1個のみを想定する。"""

    def __init__(self):
        w, h = PINBALL_BOARD_W, PINBALL_BOARD_H
        main_right = w - PINBALL_LANE_W
        center_x = main_right / 2
        flipper_y = h - 70

        # フリッパー（左右対称）
        left_pivot = (center_x - PINBALL_FLIPPER_PIVOT_OFFSET, flipper_y)
        right_pivot = (center_x + PINBALL_FLIPPER_PIVOT_OFFSET, flipper_y)
        self.left_flipper = Flipper(
            left_pivot, PINBALL_FLIPPER_LENGTH, PINBALL_FLIPPER_THICKNESS,
            PINBALL_FLIPPER_REST_ANGLE, PINBALL_FLIPPER_ACTIVE_ANGLE,
            PINBALL_FLIPPER_ANGULAR_SPEED, "left",
        )
        self.right_flipper = Flipper(
            right_pivot, PINBALL_FLIPPER_LENGTH, PINBALL_FLIPPER_THICKNESS,
            PINBALL_FLIPPER_REST_ANGLE, PINBALL_FLIPPER_ACTIVE_ANGLE,
            PINBALL_FLIPPER_ANGULAR_SPEED, "right",
        )
        self.flippers = [self.left_flipper, self.right_flipper]

        left_funnel_end = (left_pivot[0] - 20, h - 30)
        right_funnel_end = (right_pivot[0] + 15, h - 30)

        # 外周・レーンの壁（得点なし、単純反射）
        self.walls = [
            ((0, 60), (60, 0)),                                   # 左上シャンファー
            ((60, 0), (w - 40, 0)),                                # 上壁
            ((w - 40, 0), (w, 40)),                                # 右上シャンファー（レーン側）
            ((w, 40), (w, h)),                                     # レーン右壁（盤面外周）
            ((w, h), (main_right, h)),                             # レーン床
            ((main_right, PINBALL_LANE_GAP_TOP), (main_right, h)),  # レーン仕切り（左壁）
            ((0, 60), (0, PINBALL_FUNNEL_TOP_Y)),                  # 左壁
        ]

        # スリングショット（フリッパー脇。跳ね返しブースト＋得点）
        self.slingshots = [
            {"seg": ((0, PINBALL_FUNNEL_TOP_Y), left_funnel_end), "cooldown": 0.0},
            {"seg": ((main_right, PINBALL_FUNNEL_TOP_Y), right_funnel_end), "cooldown": 0.0},
        ]

        # ポップバンパー（点として扱う＝長さ0のセグメント）
        self.bumpers = [
            {"pos": (center_x, 160), "radius": PINBALL_BUMPER_RADIUS, "cooldown": 0.0},
            {"pos": (center_x - 57, 230), "radius": PINBALL_BUMPER_RADIUS, "cooldown": 0.0},
            {"pos": (center_x + 57, 230), "radius": PINBALL_BUMPER_RADIUS, "cooldown": 0.0},
        ]

        # プランジャーレーンでボールが静止する位置
        lane_center_x = main_right + PINBALL_LANE_W / 2
        self.plunger_rest = (lane_center_x, h - 20)
        self.lane_left_x = main_right  # この x より右がプランジャーレーン

    def set_flipper_input(self, left_active, right_active):
        self.left_flipper.set_active(left_active)
        self.right_flipper.set_active(right_active)

    def is_drained(self, ball):
        return ball.y - ball.radius > PINBALL_BOARD_H

    def is_settled_in_lane(self, ball):
        """打ち上げが弱く盤面まで届かず、レーンへ戻って静止したかどうか。

        フリッパーはレーンまで届かないため、これを検知しないと
        プレイ中のままボールがレーンに取り残されて操作不能になる。
        """
        if ball.x <= self.lane_left_x:
            return False
        return math.hypot(ball.vx, ball.vy) < PINBALL_LANE_SETTLE_SPEED

    def update(self, ball, dt):
        """フリッパー・重力を更新し、ボールとの衝突をすべて解決する。

        高速時に壁をすり抜けないよう、移動量に応じて内部でサブステップに分割し、
        各サブステップで「重力による移動 → 衝突解決」を行う。

        戻り値: このフレームで発生したイベント名と得点のリスト
        （"bumper" / "slingshot" / "flipper"）
        """
        for flipper in self.flippers:
            flipper.update(dt)
        for slingshot in self.slingshots:
            slingshot["cooldown"] = max(0.0, slingshot["cooldown"] - dt)
        for bumper in self.bumpers:
            bumper["cooldown"] = max(0.0, bumper["cooldown"] - dt)

        speed = math.hypot(ball.vx, ball.vy)
        dist = speed * dt
        steps = 1 if dist <= _MAX_STEP_DIST else min(
            _MAX_SUBSTEPS, int(math.ceil(dist / _MAX_STEP_DIST)))
        step_dt = dt / steps

        events = []
        for _ in range(steps):
            ball.update(step_dt, PINBALL_GRAVITY)
            events.extend(self._resolve_collisions(ball))
        return events

    def _resolve_collisions(self, ball):
        events = []

        for a, b in self.walls:
            self._resolve_wall(ball, a, b, PINBALL_WALL_RESTITUTION)

        for slingshot in self.slingshots:
            a, b = slingshot["seg"]
            hit = self._resolve_wall(ball, a, b, PINBALL_WALL_RESTITUTION)
            if hit and slingshot["cooldown"] <= 0.0:
                nx, ny = hit["normal"]
                ball.vx += nx * PINBALL_SLINGSHOT_BOOST
                ball.vy += ny * PINBALL_SLINGSHOT_BOOST
                slingshot["cooldown"] = PINBALL_SLINGSHOT_COOLDOWN
                events.append(("slingshot", PINBALL_SLINGSHOT_SCORE))

        for bumper in self.bumpers:
            pos = bumper["pos"]
            hit = self._resolve_wall(ball, pos, pos, PINBALL_WALL_RESTITUTION,
                                      extra_radius=bumper["radius"])
            if hit and bumper["cooldown"] <= 0.0:
                nx, ny = hit["normal"]
                ball.vx += nx * PINBALL_BUMPER_BOOST
                ball.vy += ny * PINBALL_BUMPER_BOOST
                bumper["cooldown"] = PINBALL_BUMPER_COOLDOWN
                events.append(("bumper", PINBALL_BUMPER_SCORE))

        for flipper in self.flippers:
            pivot, tip = flipper.segment()
            hit = self._resolve_wall(ball, pivot, tip, PINBALL_WALL_RESTITUTION,
                                      extra_radius=flipper.thickness)
            if hit:
                r_len = hit["t"] * flipper.length
                if flipper.side == "left":
                    perp = (-math.sin(flipper.angle), -math.cos(flipper.angle))
                else:
                    perp = (math.sin(flipper.angle), -math.cos(flipper.angle))
                tangential_speed = flipper.angular_velocity * r_len
                ball.vx += perp[0] * tangential_speed * PINBALL_FLIPPER_KICK
                ball.vy += perp[1] * tangential_speed * PINBALL_FLIPPER_KICK
                if flipper.hit_cooldown <= 0.0:
                    flipper.hit_cooldown = PINBALL_FLIPPER_HIT_COOLDOWN
                    events.append(("flipper", PINBALL_FLIPPER_HIT_SCORE))

        return events

    @staticmethod
    def _resolve_wall(ball, a, b, restitution, extra_radius=0.0):
        closest, t = _closest_point_on_segment(ball.pos, a, b)
        dx = ball.x - closest[0]
        dy = ball.y - closest[1]
        dist = math.hypot(dx, dy)
        min_dist = ball.radius + extra_radius
        if dist >= min_dist:
            return None
        if dist < 1e-6:
            nx, ny = 0.0, -1.0
            dist = 0.0
        else:
            nx, ny = dx / dist, dy / dist
        overlap = min_dist - dist
        ball.x += nx * overlap
        ball.y += ny * overlap
        vn = ball.vx * nx + ball.vy * ny
        if vn < 0:
            factor = (1 + restitution) * vn
            ball.vx -= factor * nx
            ball.vy -= factor * ny
        return {"t": t, "normal": (nx, ny), "point": closest}
