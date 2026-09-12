"""ボーナス UFO。画面上部をランダムな間隔で横切る。"""

import random

import pygame

from config import (
    SCREEN_WIDTH, SI_UFO_W, SI_UFO_H, SI_UFO_Y, SI_UFO_SPEED,
    SI_UFO_MIN_INTERVAL, SI_UFO_MAX_INTERVAL, SI_UFO_SCORES, SI_COLOR_UFO,
)


class UFO:
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.direction = 1
        self.score = 0
        self.timer = random.uniform(SI_UFO_MIN_INTERVAL, SI_UFO_MAX_INTERVAL)

    def rect(self):
        return pygame.Rect(int(self.x), SI_UFO_Y, SI_UFO_W, SI_UFO_H)

    def update(self, dt):
        if not self.active:
            self.timer -= dt
            if self.timer <= 0:
                self._spawn()
            return
        self.x += self.direction * SI_UFO_SPEED * dt
        if self.x < -SI_UFO_W - 10 or self.x > SCREEN_WIDTH + 10:
            self.active = False
            self.timer = random.uniform(SI_UFO_MIN_INTERVAL, SI_UFO_MAX_INTERVAL)

    def _spawn(self):
        self.active = True
        self.direction = random.choice((1, -1))
        self.x = -SI_UFO_W if self.direction > 0 else float(SCREEN_WIDTH)
        self.score = random.choice(SI_UFO_SCORES)

    def kill(self):
        """撃墜されたときの得点を返し、非アクティブに戻す。"""
        self.active = False
        self.timer = random.uniform(SI_UFO_MIN_INTERVAL, SI_UFO_MAX_INTERVAL)
        return self.score

    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.ellipse(screen, SI_COLOR_UFO, self.rect())
        dome = pygame.Rect(int(self.x + SI_UFO_W * 0.3), SI_UFO_Y - 6,
                           int(SI_UFO_W * 0.4), 8)
        pygame.draw.ellipse(screen, SI_COLOR_UFO, dome)
