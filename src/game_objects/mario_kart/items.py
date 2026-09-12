"""アイテムボックス・バナナ・こうら。

バナナはカート後方に設置される静的な障害物、こうらはカート前方へ直進する
弾。どちらも当たったカートを `Kart.hit()` でスピンアウトさせる。
"""

import math
import random

from config import (
    MK_ITEM_BOX_RADIUS, MK_ITEM_BOX_RESPAWN,
    MK_BANANA_HIT_RADIUS, MK_BANANA_LIFETIME, MK_BANANA_DROP_OFFSET,
    MK_SHELL_SPEED, MK_SHELL_HIT_RADIUS, MK_SHELL_LIFETIME, MK_SHELL_SPAWN_OFFSET,
)

ITEM_KINDS = ("banana", "shell")


def random_item_kind():
    return random.choice(ITEM_KINDS)


def _dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


class ItemBox:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.respawn_timer = 0.0

    def update(self, dt):
        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.active = True

    def try_pickup(self, kart_x, kart_y):
        if not self.active:
            return False
        if _dist(self.x, self.y, kart_x, kart_y) <= MK_ITEM_BOX_RADIUS:
            self.active = False
            self.respawn_timer = MK_ITEM_BOX_RESPAWN
            return True
        return False


class Banana:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.lifetime = MK_BANANA_LIFETIME

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def check_hit(self, kart):
        if not self.alive or kart.stunned:
            return False
        if _dist(self.x, self.y, kart.x, kart.y) <= MK_BANANA_HIT_RADIUS:
            self.alive = False
            return True
        return False


class Shell:
    def __init__(self, x, y, heading, owner):
        self.x = x
        self.y = y
        self.heading = heading
        self.owner = owner
        self.alive = True
        self.lifetime = MK_SHELL_LIFETIME
        self._owner_grace = 0.15  # 発射直後は発射者自身に当たらない

    def update(self, dt):
        self.x += math.cos(self.heading) * MK_SHELL_SPEED * dt
        self.y += math.sin(self.heading) * MK_SHELL_SPEED * dt
        self.lifetime -= dt
        if self._owner_grace > 0:
            self._owner_grace -= dt
        if self.lifetime <= 0:
            self.alive = False

    def check_hit(self, kart):
        if not self.alive or kart.stunned:
            return False
        if kart is self.owner and self._owner_grace > 0:
            return False
        if _dist(self.x, self.y, kart.x, kart.y) <= MK_SHELL_HIT_RADIUS:
            self.alive = False
            return True
        return False


def drop_banana(kart):
    hx, hy = kart.heading_vector()
    return Banana(kart.x - hx * MK_BANANA_DROP_OFFSET, kart.y - hy * MK_BANANA_DROP_OFFSET)


def fire_shell(kart):
    hx, hy = kart.heading_vector()
    return Shell(kart.x + hx * MK_SHELL_SPAWN_OFFSET, kart.y + hy * MK_SHELL_SPAWN_OFFSET,
                kart.heading, owner=kart)
