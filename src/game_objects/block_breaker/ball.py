"""ブロック崩しのボール。壁・パドル・ブロックとの反射を扱う。"""

import math
import pygame
from config import BREAKOUT_BALL_RADIUS, BREAKOUT_BALL_SPEED, BREAKOUT_MAX_BOUNCE_ANGLE


class Ball:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = BREAKOUT_BALL_RADIUS
        self.vx = 0.0
        self.vy = 0.0

    def launch(self):
        """パドル発射時の初速（ほぼ真上、わずかに傾ける）。"""
        angle_deg = 12
        angle = math.radians(angle_deg)
        self.vx = BREAKOUT_BALL_SPEED * math.sin(angle)
        self.vy = -BREAKOUT_BALL_SPEED * math.cos(angle)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def get_rect(self):
        r = self.radius
        return pygame.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)

    def reflect_walls(self, screen_width):
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius >= screen_width:
            self.x = screen_width - self.radius
            self.vx = -abs(self.vx)
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = abs(self.vy)

    def bounce_off_paddle(self, paddle):
        offset = paddle.bounce_offset(self.x)
        angle = math.radians(offset * BREAKOUT_MAX_BOUNCE_ANGLE)
        self.vx = BREAKOUT_BALL_SPEED * math.sin(angle)
        self.vy = -BREAKOUT_BALL_SPEED * math.cos(angle)
        self.y = paddle.rect.top - self.radius

    def bounce_off_brick(self, brick_rect):
        """ボールとブロックの重なりの浸透量が小さい軸を反転する簡易処理。"""
        ball_rect = self.get_rect()
        overlap_x = min(ball_rect.right, brick_rect.right) - max(ball_rect.left, brick_rect.left)
        overlap_y = min(ball_rect.bottom, brick_rect.bottom) - max(ball_rect.top, brick_rect.top)
        if overlap_x < overlap_y:
            self.vx = -self.vx
        else:
            self.vy = -self.vy

    def is_below(self, y_limit):
        return self.y - self.radius > y_limit

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
