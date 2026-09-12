"""ブロック崩しのパドル。"""

import pygame
from config import (
    SCREEN_WIDTH, BREAKOUT_PADDLE_W, BREAKOUT_PADDLE_H, BREAKOUT_PADDLE_Y,
    BREAKOUT_PADDLE_SPEED,
)


class Paddle:
    def __init__(self):
        x = (SCREEN_WIDTH - BREAKOUT_PADDLE_W) // 2
        self.rect = pygame.Rect(x, BREAKOUT_PADDLE_Y, BREAKOUT_PADDLE_W, BREAKOUT_PADDLE_H)

    def update(self, dt, keys):
        dx = 0
        if keys[pygame.K_LEFT]:
            dx -= BREAKOUT_PADDLE_SPEED * dt
        if keys[pygame.K_RIGHT]:
            dx += BREAKOUT_PADDLE_SPEED * dt
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x + dx))

    def bounce_offset(self, ball_cx):
        """パドル中心からのズレを -1.0（左端）〜 1.0（右端）に正規化して返す。"""
        offset = (ball_cx - self.rect.centerx) / (self.rect.width / 2)
        return max(-1.0, min(1.0, offset))

    def draw(self, screen):
        pygame.draw.rect(screen, (230, 230, 230), self.rect, border_radius=4)
