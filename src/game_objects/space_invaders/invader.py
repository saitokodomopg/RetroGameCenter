"""インベーダー編隊・敵弾。

編隊全体を InvaderFleet が管理する。個々のマスは生死のみを持ち、実際の画面座標は
Fleet のオフセット（offset_x, offset_y）+ グリッド位置から都度計算する。
これにより原作のような「編隊全体が一体で左右に往復する」動きを再現する。
"""

import random

import pygame

from config import (
    SI_INV_ROWS, SI_INV_COLS, SI_INV_W, SI_INV_H,
    SI_INV_GAP_X, SI_INV_GAP_Y, SI_INV_TOP,
    SI_INV_BASE_SPEED, SI_INV_MAX_SPEED, SI_INV_DROP,
    SI_INV_ROW_SCORES, SI_ENEMY_BULLET_SPEED, SI_ENEMY_BULLET_MAX,
    SI_ENEMY_SHOOT_INTERVAL, SI_ENEMY_BULLET_W, SI_ENEMY_BULLET_H,
    SCREEN_WIDTH,
)

FLEET_WIDTH = SI_INV_COLS * SI_INV_W + (SI_INV_COLS - 1) * SI_INV_GAP_X


class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True

    def update(self, dt):
        self.y += SI_ENEMY_BULLET_SPEED * dt

    def rect(self):
        return pygame.Rect(int(self.x - SI_ENEMY_BULLET_W / 2), int(self.y),
                           SI_ENEMY_BULLET_W, SI_ENEMY_BULLET_H)


class InvaderFleet:
    """編隊全体（生死グリッド＋オフセット移動）を管理する。"""

    def __init__(self):
        self.alive = [[True] * SI_INV_COLS for _ in range(SI_INV_ROWS)]
        self.offset_x = (SCREEN_WIDTH - FLEET_WIDTH) / 2
        self.offset_y = float(SI_INV_TOP)
        self.direction = 1  # 1: 右へ移動中, -1: 左へ移動中
        self.bullets = []
        self.shoot_timer = 0.0
        self.total = SI_INV_ROWS * SI_INV_COLS

    def alive_count(self):
        return sum(1 for row in self.alive for a in row if a)

    def _speed(self):
        remaining = self.alive_count()
        if remaining <= 0:
            return SI_INV_BASE_SPEED
        ratio = 1 - (remaining / self.total)
        return SI_INV_BASE_SPEED + (SI_INV_MAX_SPEED - SI_INV_BASE_SPEED) * ratio

    def _cell_pos(self, row, col):
        x = self.offset_x + col * (SI_INV_W + SI_INV_GAP_X)
        y = self.offset_y + row * (SI_INV_H + SI_INV_GAP_Y)
        return x, y

    def _edge_positions(self):
        """生存している列の左端・右端 x 座標（オフセット込み）を返す。"""
        alive_cols = [c for c in range(SI_INV_COLS)
                      if any(self.alive[r][c] for r in range(SI_INV_ROWS))]
        if not alive_cols:
            return None, None
        left = self.offset_x + min(alive_cols) * (SI_INV_W + SI_INV_GAP_X)
        right = self.offset_x + max(alive_cols) * (SI_INV_W + SI_INV_GAP_X) + SI_INV_W
        return left, right

    def update(self, dt):
        speed = self._speed()
        left, right = self._edge_positions()
        if left is not None:
            hit_edge = (
                (self.direction > 0 and right + speed * dt >= SCREEN_WIDTH - 10) or
                (self.direction < 0 and left - speed * dt <= 10)
            )
            if hit_edge:
                self.offset_y += SI_INV_DROP
                self.direction *= -1
            else:
                self.offset_x += self.direction * speed * dt

        self.shoot_timer += dt
        if self.shoot_timer >= SI_ENEMY_SHOOT_INTERVAL:
            self.shoot_timer = 0.0
            if len(self.bullets) < SI_ENEMY_BULLET_MAX:
                self._try_spawn_bullet()

        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

    def _try_spawn_bullet(self):
        """各列の最前列（最下段）の生存インベーダーからランダムに1体選んで撃たせる。"""
        shooters = []
        for c in range(SI_INV_COLS):
            for r in range(SI_INV_ROWS - 1, -1, -1):
                if self.alive[r][c]:
                    shooters.append((r, c))
                    break
        if not shooters:
            return
        r, c = random.choice(shooters)
        x, y = self._cell_pos(r, c)
        self.bullets.append(EnemyBullet(x + SI_INV_W / 2, y + SI_INV_H))

    def kill(self, row, col):
        if self.alive[row][col]:
            self.alive[row][col] = False
            return SI_INV_ROW_SCORES[row]
        return 0

    def bottom_y(self):
        """生存している中で最も下の段の下端 y。全滅時は 0。"""
        rows_alive = [r for r in range(SI_INV_ROWS) if any(self.alive[r])]
        if not rows_alive:
            return 0
        return self.offset_y + (max(rows_alive) + 1) * (SI_INV_H + SI_INV_GAP_Y) - SI_INV_GAP_Y

    def rects(self):
        """(row, col, rect) のリストを返す（生存分のみ）。"""
        result = []
        for r in range(SI_INV_ROWS):
            for c in range(SI_INV_COLS):
                if self.alive[r][c]:
                    x, y = self._cell_pos(r, c)
                    result.append((r, c, pygame.Rect(int(x), int(y), SI_INV_W, SI_INV_H)))
        return result
