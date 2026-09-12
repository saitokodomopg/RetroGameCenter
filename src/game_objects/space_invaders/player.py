"""自機・自弾。"""

import pygame

from config import (
    SCREEN_WIDTH, SI_PLAYER_W, SI_PLAYER_H, SI_PLAYER_Y, SI_PLAYER_SPEED,
    SI_BULLET_W, SI_BULLET_H, SI_BULLET_SPEED,
)


class PlayerBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True

    def update(self, dt):
        self.y -= SI_BULLET_SPEED * dt
        if self.y + SI_BULLET_H < 0:
            self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - SI_BULLET_W / 2), int(self.y),
                           SI_BULLET_W, SI_BULLET_H)


class Player:
    def __init__(self):
        self.x = (SCREEN_WIDTH - SI_PLAYER_W) / 2
        self.y = SI_PLAYER_Y
        self.bullet = None

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), SI_PLAYER_W, SI_PLAYER_H)

    def move(self, dt, keys):
        if keys[pygame.K_LEFT]:
            self.x -= SI_PLAYER_SPEED * dt
        if keys[pygame.K_RIGHT]:
            self.x += SI_PLAYER_SPEED * dt
        self.x = max(4, min(SCREEN_WIDTH - SI_PLAYER_W - 4, self.x))

    def shoot(self):
        """自弾は画面内に同時1発まで（原作準拠）。発射できたら True を返す。"""
        if self.bullet is not None and self.bullet.alive:
            return False
        self.bullet = PlayerBullet(self.x + SI_PLAYER_W / 2, self.y - SI_BULLET_H)
        return True

    def update_bullet(self, dt):
        if self.bullet is not None:
            self.bullet.update(dt)
            if not self.bullet.alive:
                self.bullet = None
