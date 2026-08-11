"""ぷよぷよの盤面。設置・重力落下・連結判定・消去・得点計算を行う。

描画を一切持たないため、ヘッドレスでロジック検証できる（テトリスの Board と同方針）。
grid の各セルは空きが None、ぷよは色キー（"R"/"G"/"B"/"Y"）を格納する。
"""

from config import (
    PUYO_COLS, PUYO_ROWS, PUYO_SPAWN_COL,
    PUYO_POP_SCORE, PUYO_CHAIN_BONUS,
)

# 同色がつながる方向。上下左右のみ（斜めはつながらない＝原作準拠）
_NEIGHBORS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

# 消えるのに必要な連結数
POP_MIN = 4


class PuyoBoard:
    def __init__(self, cols=PUYO_COLS, rows=PUYO_ROWS):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]

    def reset(self):
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    # --- 判定 -----------------------------------------------------------
    def is_valid(self, cells):
        """セル集合が盤面内かつ空きに収まるか（壁・床・既存ぷよと衝突しないか）。"""
        for (cx, cy) in cells:
            if cx < 0 or cx >= self.cols or cy >= self.rows:
                return False
            # 天井より上（cy < 0）は出現直後の許容として通す
            if cy < 0:
                continue
            if self.grid[cy][cx] is not None:
                return False
        return True

    def is_dead(self):
        """出現位置（最上段の出現列）が埋まっていればゲームオーバー。"""
        return self.grid[0][PUYO_SPAWN_COL] is not None

    # --- 設置 -----------------------------------------------------------
    def lock(self, colored_cells):
        """[(セル, 色キー), ...] を盤面に固定する。範囲外（cy<0）は無視。"""
        for ((cx, cy), kind) in colored_cells:
            if 0 <= cy < self.rows and 0 <= cx < self.cols:
                self.grid[cy][cx] = kind

    # --- 重力（ちぎり） --------------------------------------------------
    def apply_gravity(self):
        """浮いているぷよを下へ詰める。1つでも動いたら True。

        組ぷよ単位ではなく列ごとのセル単位で詰め直すため、軸ぷよと子ぷよが
        別々に落ちる原作の「ちぎり」が特別な処理なしで再現される。
        """
        moved = False
        for col in range(self.cols):
            stack = [self.grid[r][col] for r in range(self.rows)
                     if self.grid[r][col] is not None]
            # 下端から積み直し、上の余りは空にする
            write_r = self.rows - 1
            for kind in reversed(stack):
                if self.grid[write_r][col] != kind:
                    moved = True
                self.grid[write_r][col] = kind
                write_r -= 1
            while write_r >= 0:
                if self.grid[write_r][col] is not None:
                    moved = True
                self.grid[write_r][col] = None
                write_r -= 1
        return moved

    # --- 連結判定・消去 --------------------------------------------------
    def find_groups(self):
        """同色が POP_MIN 個以上つながったグループを列挙する。

        戻り値: [[(cx, cy), ...], ...]（各要素が1グループのセル集合）
        隣接は上下左右の4方向のみ。BFS で連結成分を求める。
        """
        visited = [[False] * self.cols for _ in range(self.rows)]
        groups = []
        for r in range(self.rows):
            for c in range(self.cols):
                if visited[r][c] or self.grid[r][c] is None:
                    continue
                kind = self.grid[r][c]
                group = []
                queue = [(c, r)]
                visited[r][c] = True
                while queue:
                    cx, cy = queue.pop()
                    group.append((cx, cy))
                    for dx, dy in _NEIGHBORS:
                        nx, ny = cx + dx, cy + dy
                        if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                            continue
                        if visited[ny][nx] or self.grid[ny][nx] != kind:
                            continue
                        visited[ny][nx] = True
                        queue.append((nx, ny))
                if len(group) >= POP_MIN:
                    groups.append(group)
        return groups

    def pop_groups(self, groups):
        """グループのセルを消し、消したぷよの総数を返す。"""
        count = 0
        for group in groups:
            for (cx, cy) in group:
                if self.grid[cy][cx] is not None:
                    self.grid[cy][cx] = None
                    count += 1
        return count

    # --- 得点 -----------------------------------------------------------
    @staticmethod
    def chain_score(popped, chain):
        """消したぷよ数と連鎖数（1始まり）から得点を求める。

        連鎖ボーナスは 2 連鎖目で大きく跳ね上がる。テーブル長を超える連鎖は
        最後の値で頭打ちにする。
        """
        if popped <= 0 or chain <= 0:
            return 0
        idx = min(chain, len(PUYO_CHAIN_BONUS)) - 1
        return popped * PUYO_POP_SCORE * PUYO_CHAIN_BONUS[idx]
