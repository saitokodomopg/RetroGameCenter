"""ヘビゲーム（SNAKE）のエサ配置。pygame に依存しない。"""

import random


def spawn_food(cols, rows, occupied):
    """occupied に重ならない空きセルをランダムに1つ返す。

    空きがなければ None（盤面を埋め尽くした稀なケース。特別な処理はせず、
    以後エサが出現しないだけに留める＝スコープ外）。
    """
    occupied_set = set(occupied)
    free = [(c, r) for c in range(cols) for r in range(rows) if (c, r) not in occupied_set]
    if not free:
        return None
    return random.choice(free)
