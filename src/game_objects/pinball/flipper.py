"""ピンボールのフリッパー。ピボット中心の回転する線分として扱う（pygame 非依存）。"""

import math


class Flipper:
    def __init__(self, pivot, length, thickness, rest_angle_deg, active_angle_deg,
                 angular_speed_deg, side):
        self.pivot = pivot
        self.length = length
        self.thickness = thickness
        self.rest_angle = math.radians(rest_angle_deg)
        self.active_angle = math.radians(active_angle_deg)
        self.angular_speed = math.radians(angular_speed_deg)
        self.side = side  # "left" または "right"
        self.angle = self.rest_angle
        self.angular_velocity = 0.0
        self.is_active = False

    def set_active(self, active):
        self.is_active = active

    def update(self, dt):
        target = self.active_angle if self.is_active else self.rest_angle
        prev = self.angle
        if self.angle < target:
            self.angle = min(target, self.angle + self.angular_speed * dt)
        elif self.angle > target:
            self.angle = max(target, self.angle - self.angular_speed * dt)
        self.angular_velocity = (self.angle - prev) / dt if dt > 0 else 0.0

    def direction(self):
        if self.side == "left":
            dx = math.cos(self.angle)
        else:
            dx = -math.cos(self.angle)
        dy = -math.sin(self.angle)
        return (dx, dy)

    def tip(self):
        dx, dy = self.direction()
        return (self.pivot[0] + self.length * dx, self.pivot[1] + self.length * dy)

    def segment(self):
        return self.pivot, self.tip()
