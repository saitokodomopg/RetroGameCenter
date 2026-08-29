"""イカジャンプ — 足場（プラットフォーム）。

画面上方向へ手続き的に生成する。3 種類:
  normal  — 通常の固定足場
  moving  — 左右に往復する足場
  crumble — 着地すると一定時間で崩れて消える足場
"""

import random

import pygame

from config import (
    SCREEN_WIDTH,
    IKA_PLATFORM_W, IKA_PLATFORM_H,
    IKA_PLATFORM_GAP_MIN, IKA_PLATFORM_GAP_MAX, IKA_MAX_DX,
    IKA_MOVING_SPEED, IKA_CRUMBLE_TIME,
    IKA_COLOR_PLATFORM_NORMAL, IKA_COLOR_PLATFORM_MOVING,
    IKA_COLOR_PLATFORM_CRUMBLE, IKA_COLOR_PLATFORM_CRUMBLE_BROKEN,
)


class Platform:
    def __init__(self, x, y, kind="normal", width=None):
        self.x = x
        self.y = y  # 足場上面のワールド y
        self.width = width if width is not None else IKA_PLATFORM_W
        self.height = IKA_PLATFORM_H
        self.kind = kind
        self.dir = random.choice((-1, 1))
        self.triggered = False
        self.gone = False
        self.crumble_timer = 0.0

    def update(self, dt):
        if self.kind == "moving":
            self.x += self.dir * IKA_MOVING_SPEED * dt
            if self.x <= 0:
                self.x = 0
                self.dir = 1
            elif self.x + self.width >= SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - self.width
                self.dir = -1
        elif self.kind == "crumble" and self.triggered and not self.gone:
            self.crumble_timer -= dt
            if self.crumble_timer <= 0:
                self.gone = True

    def on_landed(self):
        """着地時に呼ばれる（崩れる足場はここでカウントダウン開始）。"""
        if self.kind == "crumble" and not self.triggered:
            self.triggered = True
            self.crumble_timer = IKA_CRUMBLE_TIME

    def get_world_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, screen, cam_y):
        if self.gone:
            return
        rect = pygame.Rect(int(self.x), int(self.y - cam_y), self.width, self.height)
        if self.kind == "moving":
            color = IKA_COLOR_PLATFORM_MOVING
        elif self.kind == "crumble":
            color = IKA_COLOR_PLATFORM_CRUMBLE_BROKEN if self.triggered else IKA_COLOR_PLATFORM_CRUMBLE
        else:
            color = IKA_COLOR_PLATFORM_NORMAL
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=4)


def choose_kind(altitude):
    """高度（登った距離, px）に応じて足場の種類を確率で選ぶ。"""
    moving_chance = min(0.30, 0.05 + altitude / 6000)
    crumble_chance = min(0.25, altitude / 8000)
    r = random.random()
    if r < crumble_chance:
        return "crumble"
    if r < crumble_chance + moving_chance:
        return "moving"
    return "normal"


def spawn_platform(prev_x, prev_y, altitude):
    """直前の足場を基準に、バウンドで届く範囲内の次の足場を生成する。"""
    gap = random.uniform(IKA_PLATFORM_GAP_MIN, IKA_PLATFORM_GAP_MAX)
    y = prev_y - gap
    dx = random.uniform(-IKA_MAX_DX, IKA_MAX_DX)
    x = max(0, min(SCREEN_WIDTH - IKA_PLATFORM_W, prev_x + dx))
    kind = choose_kind(altitude)
    return Platform(x, y, kind=kind)
