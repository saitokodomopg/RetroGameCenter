"""組ぷよ（2個1組で落ちてくるぷよ）の座標計算・回転を扱う。

テトリミノのような形状テーブルは持たず、軸ぷよの位置 (x, y) と
子ぷよの向き rot（0=上, 1=右, 2=下, 3=左）から子の座標を計算する。
描画・衝突判定は持たない（衝突は Board 側に委ねる）ためヘッドレスで検証できる。
"""

from config import (
    COLOR_PUYO_R, COLOR_PUYO_G, COLOR_PUYO_B, COLOR_PUYO_Y,
)

# 色キー → RGB
COLORS = {
    "R": COLOR_PUYO_R,
    "G": COLOR_PUYO_G,
    "B": COLOR_PUYO_B,
    "Y": COLOR_PUYO_Y,
}

KINDS = ["R", "G", "B", "Y"]

# rot に対応する「軸から見た子ぷよの相対位置」。0=上, 1=右, 2=下, 3=左
OFFSETS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class PuyoPair:
    """落下中の組ぷよ。軸ぷよ＋子ぷよの2個で1組。"""

    def __init__(self, axis_kind, child_kind, x, y, rot=0):
        self.axis_kind = axis_kind
        self.child_kind = child_kind
        self.x = x
        self.y = y
        self.rot = rot

    def axis_cell(self, x=None, y=None):
        """軸ぷよの絶対セル座標 (gx, gy)。"""
        ox = self.x if x is None else x
        oy = self.y if y is None else y
        return (ox, oy)

    def child_cell(self, rot=None, x=None, y=None):
        """子ぷよの絶対セル座標 (gx, gy)。"""
        r = self.rot if rot is None else rot
        ox = self.x if x is None else x
        oy = self.y if y is None else y
        dx, dy = OFFSETS[r % 4]
        return (ox + dx, oy + dy)

    def cells(self, rot=None, x=None, y=None):
        """[軸, 子] の絶対セル座標リスト。衝突判定に渡す用。"""
        return [self.axis_cell(x, y), self.child_cell(rot, x, y)]

    def colored_cells(self, rot=None, x=None, y=None):
        """[(セル, 色キー), ...] を返す。盤面への固定・描画に使う。"""
        return [
            (self.axis_cell(x, y), self.axis_kind),
            (self.child_cell(rot, x, y), self.child_kind),
        ]

    def next_rotation(self, direction=1):
        """回転後の向き。direction=1 で右回転（X）、-1 で左回転（Z）。"""
        return (self.rot + direction) % 4
