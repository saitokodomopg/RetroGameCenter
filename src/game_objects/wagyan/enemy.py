"""ワギャンランドの敵。

音波でしびれさせると一定時間その場で気絶し、上に乗って足場として利用できる。
しびれていない間に触れるとプレイヤーはミスになる（scene 側で判定）。

すべて地面（WAGYAN_GROUND_Y）の上に立ち、[min_x, max_x] の範囲を往復する。
"""

import math

import pygame

from config import (
    WAGYAN_ENEMY_W, WAGYAN_ENEMY_H, WAGYAN_ENEMY_SPEED, WAGYAN_GROUND_Y,
    WAGYAN_COLOR_ENEMY, WAGYAN_COLOR_ENEMY_STUNNED,
)

WAKE_WARNING_TIME = 0.6  # しびれ解除前に点滅で予兆を出す時間（秒）


class Enemy:
    def __init__(self, x, min_x, max_x):
        self.width = WAGYAN_ENEMY_W
        self.height = WAGYAN_ENEMY_H
        self.cx = float(x)
        self.min_x = min_x
        self.max_x = max_x
        self.dir = 1
        self.paralyzed = False
        self.stun_timer = 0.0
        self.anim = 0.0

    @property
    def bottom(self):
        return WAGYAN_GROUND_Y

    def get_world_rect(self):
        top = self.bottom - self.height
        return pygame.Rect(int(self.cx - self.width / 2), int(top),
                           self.width, self.height)

    def paralyze(self, duration):
        self.paralyzed = True
        self.stun_timer = duration

    def update(self, dt):
        self.anim += dt
        if self.paralyzed:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.paralyzed = False
            return

        self.cx += self.dir * WAGYAN_ENEMY_SPEED * dt
        if self.cx <= self.min_x:
            self.cx = self.min_x
            self.dir = 1
        elif self.cx >= self.max_x:
            self.cx = self.max_x
            self.dir = -1

    def draw(self, screen, cam_x):
        r = self.get_world_rect()
        r.x -= int(cam_x)
        if r.right < 0 or r.left > 10_000:
            return

        waking = self.paralyzed and self.stun_timer < WAKE_WARNING_TIME
        blink_off = waking and int(self.stun_timer * 10) % 2 == 0
        color = WAGYAN_COLOR_ENEMY_STUNNED if self.paralyzed else WAGYAN_COLOR_ENEMY
        if blink_off:
            color = WAGYAN_COLOR_ENEMY

        pygame.draw.ellipse(screen, color, r)
        pygame.draw.ellipse(screen, (40, 20, 30), r, 2)

        if self.paralyzed:
            # 目を回す（気絶の記号）
            cx, cy = r.centerx, r.top + 7
            for i in range(2):
                ex = cx - 6 + i * 12
                pygame.draw.circle(screen, (255, 255, 255), (ex, cy), 4)
                spin = self.anim * 6 + i * 2
                dx = int(math.cos(spin) * 2)
                dy = int(math.sin(spin) * 2)
                pygame.draw.circle(screen, (20, 20, 20), (ex + dx, cy + dy), 1)
        else:
            eye_x = r.centerx + self.dir * 6
            pygame.draw.circle(screen, (20, 20, 20), (eye_x, r.top + 7), 3)
