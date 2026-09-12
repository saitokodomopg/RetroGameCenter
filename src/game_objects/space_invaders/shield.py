"""シールド（バンカー）。弾が当たるたびに欠けていく破壊可能な地形。"""

import pygame

from config import SI_SHIELD_CELL, SI_COLOR_SHIELD

# 原作イメージのバンカー形状（1=ブロックあり、0=なし）
_PATTERN = [
    "01111110",
    "11111111",
    "11111111",
    "11111111",
    "11100111",
    "11000011",
]

ROWS = len(_PATTERN)
COLS = len(_PATTERN[0])
WIDTH = COLS * SI_SHIELD_CELL
HEIGHT = ROWS * SI_SHIELD_CELL


class Shield:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.blocks = [[ch == "1" for ch in row] for row in _PATTERN]

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), WIDTH, HEIGHT)

    def _cell_at(self, px, py):
        col = int((px - self.x) // SI_SHIELD_CELL)
        row = int((py - self.y) // SI_SHIELD_CELL)
        if 0 <= row < ROWS and 0 <= col < COLS:
            return row, col
        return None

    def hit(self, rect):
        """rect と衝突する生きたブロックがあれば周辺ごと欠けさせ、True を返す。"""
        if not self.rect().colliderect(rect):
            return False
        cell = self._cell_at(rect.centerx, rect.centery)
        if cell is None or not self.blocks[cell[0]][cell[1]]:
            cell = None
            for px, py in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
                c = self._cell_at(px, py)
                if c is not None and self.blocks[c[0]][c[1]]:
                    cell = c
                    break
        if cell is None:
            return False
        r, c = cell
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < ROWS and 0 <= cc < COLS:
                    self.blocks[rr][cc] = False
        return True

    def draw(self, screen):
        for r in range(ROWS):
            for c in range(COLS):
                if self.blocks[r][c]:
                    rect = pygame.Rect(int(self.x + c * SI_SHIELD_CELL),
                                       int(self.y + r * SI_SHIELD_CELL),
                                       SI_SHIELD_CELL, SI_SHIELD_CELL)
                    pygame.draw.rect(screen, SI_COLOR_SHIELD, rect)
