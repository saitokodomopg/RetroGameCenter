"""ブロック崩しのブロック（レンガ）。固定レイアウトを 1 パターン生成する。"""

import pygame
from config import (
    SCREEN_WIDTH,
    BREAKOUT_ROWS, BREAKOUT_COLS, BREAKOUT_BRICK_W, BREAKOUT_BRICK_H,
    BREAKOUT_BRICK_GAP, BREAKOUT_BRICK_TOP,
    BREAKOUT_ROW_COLORS, BREAKOUT_ROW_SCORES,
)


class Brick:
    def __init__(self, x, y, w, h, color, score):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.score = score
        self.alive = True

    def draw(self, screen):
        if not self.alive:
            return
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 1)


def build_bricks():
    """BREAKOUT_ROWS × BREAKOUT_COLS の固定レイアウトを生成する。

    行ごとに BREAKOUT_ROW_COLORS / BREAKOUT_ROW_SCORES を上から適用
    （上の行ほど高得点）。横方向は画面中央に寄せて配置する。
    """
    total_w = (BREAKOUT_COLS * BREAKOUT_BRICK_W
               + (BREAKOUT_COLS - 1) * BREAKOUT_BRICK_GAP)
    left = (SCREEN_WIDTH - total_w) // 2

    bricks = []
    for row in range(BREAKOUT_ROWS):
        y = BREAKOUT_BRICK_TOP + row * (BREAKOUT_BRICK_H + BREAKOUT_BRICK_GAP)
        color = BREAKOUT_ROW_COLORS[row]
        score = BREAKOUT_ROW_SCORES[row]
        for col in range(BREAKOUT_COLS):
            x = left + col * (BREAKOUT_BRICK_W + BREAKOUT_BRICK_GAP)
            bricks.append(Brick(x, y, BREAKOUT_BRICK_W, BREAKOUT_BRICK_H, color, score))
    return bricks
