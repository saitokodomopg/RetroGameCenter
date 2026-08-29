"""ヘビゲーム（SNAKE）本体のロジック。pygame に依存しない。

グリッド座標 (col, row) のリストで体を表現する。body[0] が頭。
"""


class Snake:
    def __init__(self, cells, direction):
        self.body = list(cells)
        self.direction = direction
        self.pending_direction = direction

    def queue_direction(self, dx, dy):
        """入力方向を予約する。直近の実移動方向の真反対は無視する。

        pending_direction ではなく direction（直近に確定した移動方向）とだけ
        比較することで、1ステップの間に複数回入力があっても
        「一瞬で反転して自分の首にぶつかる」バグを避ける。
        """
        cur_dx, cur_dy = self.direction
        if (dx, dy) == (-cur_dx, -cur_dy):
            return
        self.pending_direction = (dx, dy)

    def next_head(self):
        """pending_direction を確定させ、次に進むセルを返す（体はまだ動かさない）。"""
        self.direction = self.pending_direction
        dx, dy = self.direction
        hx, hy = self.body[0]
        return (hx + dx, hy + dy)

    def hits_self(self, new_head, grew):
        """new_head が自分の体に重なるか。grew=True なら尻尾は動かないので含める。"""
        check_body = self.body if grew else self.body[:-1]
        return new_head in check_body

    def advance(self, new_head, grew):
        """体を1マス進める。grew=True なら尻尾を切らずに伸ばす。"""
        self.body.insert(0, new_head)
        if not grew:
            self.body.pop()
