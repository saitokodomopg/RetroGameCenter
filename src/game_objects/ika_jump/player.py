"""イカジャンプ — プレイヤー（イカ）。

着地すると自動でバウンドする（入力不要）。プレイヤーの操作は左右移動のみ。
座標はワールド座標（y は下ほど大きい。登るほど y は小さく・負になる）。
"""

import pygame

from config import (
    SCREEN_WIDTH,
    IKA_PLAYER_W, IKA_PLAYER_H, IKA_PLAYER_SPEED,
    IKA_GRAVITY, IKA_BOUNCE_POWER,
    IKA_COLOR_SQUID, IKA_COLOR_SQUID_DARK, IKA_COLOR_SQUID_EYE,
)


class Squid:
    def __init__(self, center_x, bottom_y):
        self.width = IKA_PLAYER_W
        self.height = IKA_PLAYER_H
        self.x = center_x - self.width / 2
        self.bottom = bottom_y
        self.vel_y = 0.0
        self.facing = 1
        self.anim = 0.0

    @property
    def top(self):
        return self.bottom - self.height

    @property
    def centerx(self):
        return self.x + self.width / 2

    def update(self, dt, keys):
        """1 フレーム分の移動・落下を進める。更新前の bottom を返す（着地判定用）。"""
        self.anim += dt
        move = 0
        if keys[pygame.K_LEFT]:
            move -= 1
        if keys[pygame.K_RIGHT]:
            move += 1
        if move:
            self.facing = move
        self.x += move * IKA_PLAYER_SPEED * dt
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))

        prev_bottom = self.bottom
        self.vel_y += IKA_GRAVITY * dt
        self.bottom += self.vel_y * dt
        return prev_bottom

    def bounce(self):
        self.vel_y = -IKA_BOUNCE_POWER

    def get_world_rect(self):
        return pygame.Rect(int(self.x), int(self.top), self.width, self.height)

    def draw(self, screen, cam_y):
        sx = int(self.x)
        sy = int(self.top - cam_y)
        body_h = self.height - 6
        body = pygame.Rect(sx, sy, self.width, body_h)
        pygame.draw.ellipse(screen, IKA_COLOR_SQUID, body)
        pygame.draw.ellipse(screen, IKA_COLOR_SQUID_DARK, body, 2)

        eye_x = sx + self.width // 2 + (4 if self.facing >= 0 else -4)
        eye_y = sy + body_h // 3
        pygame.draw.circle(screen, IKA_COLOR_SQUID_EYE, (eye_x, eye_y), 3)

        # 触腕（揺れるアニメーション）
        for i in range(4):
            fx = sx + 4 + i * (self.width - 8) // 3
            fy = sy + body_h
            wig = 3 if (int(self.anim * 6) + i) % 2 == 0 else -3
            pygame.draw.line(screen, IKA_COLOR_SQUID, (fx, fy), (fx + wig, fy + 6), 3)
