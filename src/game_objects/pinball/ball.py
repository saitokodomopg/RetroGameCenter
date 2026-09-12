"""ピンボールのボール。位置・速度・重力のみを扱う（pygame 非依存）。"""

import math


class Ball:
    def __init__(self, x, y, radius, max_speed):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = radius
        self.max_speed = max_speed

    @property
    def pos(self):
        return (self.x, self.y)

    def set_pos(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0

    def update(self, dt, gravity):
        self.vy += gravity * dt
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale
        self.x += self.vx * dt
        self.y += self.vy * dt
