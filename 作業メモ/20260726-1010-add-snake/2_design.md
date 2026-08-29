# 設計: ヘビゲーム（SNAKE）

`1_requirements.md` のスコープ（ゲーム単体のみ、メニュー／`main.py` 統合は対象外）を
実装するための方針メモ。既存のテトリス・アイスクライマーと同じ構造
（`BaseScene` 継承シーン ＋ `game_objects/` の純粋ロジック）に合わせる。

## 1. ファイル構成

| ファイル | 役割 | 新規/変更 |
|----------|------|-----------|
| `src/game_objects/snake/__init__.py` | パッケージ化 | 新規 |
| `src/game_objects/snake/snake.py` | ヘビ本体（`Snake` クラス：移動・方向転換・自己衝突判定）。pygame 非依存 | 新規 |
| `src/game_objects/snake/food.py` | エサの配置関数（`spawn_food`）。pygame 非依存 | 新規 |
| `src/scenes/snake_scene.py` | ゲーム進行・入力・スコア・描画（`SnakeScene`） | 新規 |
| `src/config.py` | `SNAKE_` 定数を追記 | 変更 |

> ロジックをシーンから分離するのは、ヘッドレス・スモークテスト（pygame 描画なし）で
> 移動・衝突・成長判定を検証しやすくするため（テトリスの `Board`/`Tetromino` と同方針）。

**今回スコープ外につき触らないファイル**: `src/main.py`、`src/scenes/menu_scene.py`、
`src/scenes/menu_thumbnails.py`、`src/scenes/game_over_scene.py`、`src/utils/synth_audio.py`

- `game_over_scene.py` は既に汎用実装（タイトル固定「GAME OVER」＋ `kwargs["score"]` のみ）で、
  ゲーム名に依存しないため変更不要（`clear_scene.py` のような `title`/`message` の
  差し替え機構はそもそも持っていない＝そのままスコープ外で使える）。
- `synth_audio.py` の `SoundBank` は既存の汎用 SE
  （エサ取得 → `"score"`、壁/自己衝突ミス → `"death"`）をそのまま再利用する。
  スネーク専用の音色を追加するかどうかはユーザー判断次第なので、まずは既存音を使い、
  気になれば別作業で `"snake_eat"` 等を追加する（`known-issues.md` 候補）。

## 2. データ構造

### `Snake`（snake.py）

グリッド座標 `(col, row)` のリストで体を表現する。`body[0]` が頭。

```python
class Snake:
    def __init__(self, cells, direction):
        self.body = list(cells)          # [(col,row), ...] 先頭が頭
        self.direction = direction        # (dx, dy) 現在の実移動方向
        self.pending_direction = direction  # 次ステップで適用する方向

    def queue_direction(self, dx, dy):
        """入力方向を予約する。直近の実移動方向の真反対は無視する。"""
        cur_dx, cur_dy = self.direction
        if (dx, dy) == (-cur_dx, -cur_dy):
            return
        self.pending_direction = (dx, dy)

    def next_head(self):
        """pending_direction を確定させ、次に進むセルを返す（まだ体は動かさない）。"""
        self.direction = self.pending_direction
        dx, dy = self.direction
        hx, hy = self.body[0]
        return (hx + dx, hy + dy)

    def hits_self(self, new_head, grew):
        """new_head が自分の体に重なるか。grew=True なら尻尾は動かないので含める。"""
        check_body = self.body if grew else self.body[:-1]
        return new_head in check_body

    def advance(self, new_head, grew):
        """体を1マス進める。grew=True なら尻尾を切らず伸ばす。"""
        self.body.insert(0, new_head)
        if not grew:
            self.body.pop()
```

**方向転換のバグ回避について**: `queue_direction` は「直近の**実移動方向**（`self.direction`）」
とだけ比較し、`pending_direction` とは比較しない。理由：1ステップの間に複数回キー入力が
あっても（例: 短時間で ↑ → ← と連打）、`next_head()` が呼ばれて `self.direction` が
更新されるまでは常に「最後に確定した移動方向」を基準に反転判定するため、
「一瞬で反転して自分の首にぶつかる」というスネーク系ゲームの定番バグを避けられる。

### `spawn_food`（food.py）

```python
def spawn_food(cols, rows, occupied):
    """occupied（Snake.body など）に重ならない空きセルをランダムに1つ返す。
    空きがなければ None（盤面を埋め尽くした稀なケース。今回は「詰み＝これ以上進行不可」
    として扱い、特別なクリア処理はしない＝スコープ外）。
    """
    free = [(c, r) for c in range(cols) for r in range(rows) if (c, r) not in occupied]
    if not free:
        return None
    return random.choice(free)
```

盤面全マス埋まる（40×28=1120マス）は現実的な到達難度ではないため、`None` になった場合の
挙動は「新しいエサが出ない＝以後スコアが増えない」程度の扱いに留める。

## 3. ゲーム進行（snake_scene.py）

### 状態

`self.state`: `"play"` / `"game_over"`

主な属性: `snake`(Snake), `food`(cell or None), `score`, `foods_eaten`,
`move_timer`, `move_interval`。

### 入力（handle_input: KEYDOWN）

| キー | 動作 |
|------|------|
| ← / A | `snake.queue_direction(-1, 0)` |
| → / D | `snake.queue_direction(1, 0)` |
| ↑ / W | `snake.queue_direction(0, -1)` |
| ↓ / S | `snake.queue_direction(0, 1)` |

`state == "game_over"` の間は方向入力を無視する（リスタート操作は今回スコープに含めない、
ESC でメニューへ戻る前提。R キー等でのリスタートは `やらないこと` に準じ実装しない）。

> ESC は `main.py` の共通処理が担当するため、シーン側では扱わない（`1_requirements.md` 参照）。

### 更新（update: dt）

```
state == "play" のとき:
    move_timer += dt
    while move_timer >= move_interval:       # フレーム落ち対策で while
        move_timer -= move_interval
        _step()
        if state != "play":
            break
```

`_step()`:

```
new_head = snake.next_head()
if not (0 <= new_head[0] < SNAKE_COLS and 0 <= new_head[1] < SNAKE_ROWS):
    → ミス（壁）
grew = (food is not None and new_head == food)
if snake.hits_self(new_head, grew):
    → ミス（自己衝突）
snake.advance(new_head, grew)
if grew:
    score += SNAKE_FOOD_SCORE
    foods_eaten += 1
    move_interval = max(SNAKE_MIN_INTERVAL,
                         SNAKE_BASE_INTERVAL - foods_eaten * SNAKE_SPEED_STEP)
    food = spawn_food(SNAKE_COLS, SNAKE_ROWS, snake.body)
    sound.play_se("score")
```

ミス時共通処理: `sound.play_se("death")` → `state = "game_over"` →
`request_scene("game_over", score=self.score)`（`GameOverScene` は既存のまま利用）。

## 4. スコア・速度の計算式

- **エサ取得**: `SNAKE_FOOD_SCORE = 10` 点/個（シンプルな固定値、レベル係数なし）
- **移動間隔（速度）**:
  `move_interval = max(SNAKE_MIN_INTERVAL, SNAKE_BASE_INTERVAL - foods_eaten * SNAKE_SPEED_STEP)`
  - `SNAKE_BASE_INTERVAL = 0.14`（開始時、約7マス/秒）
  - `SNAKE_SPEED_STEP = 0.004`（エサ1個ごとに短縮）
  - `SNAKE_MIN_INTERVAL = 0.06`（上限速度、約16.7マス/秒）
  - 上限到達まで約 (0.14-0.06)/0.004 = 20 個のエサが必要

## 5. 描画レイアウト（800×600）

- セルサイズ `SNAKE_CELL = 20`px、`SNAKE_COLS = 40`、`SNAKE_ROWS = 28`
  → プレイフィールドは 800×560px
- 上部 `SNAKE_HUD_HEIGHT = 40`px を HUD 帯として確保し、プレイフィールドは
  その下（y: 40〜600）に配置。グリッド座標 `(col, row)` → 画面座標は
  `(col * SNAKE_CELL, SNAKE_HUD_HEIGHT + row * SNAKE_CELL)`
- HUD: 左に `SCORE`、右に `LV`（`foods_eaten` を簡易的なレベル表示として使う）
- ヘビ: 頭とそれ以外で色を変える（頭を少し明るく）、エサは別色の四角
- ゲームオーバー時の画面遷移は `GameOverScene` に任せるため、`snake_scene.py` 側は
  ゲームオーバー専用の描画を持たない（状態が `game_over` になった時点で即座に
  `request_scene` するため、`draw()` は常に `play` 中の画面のみを描く）

## 6. config.py への追加（例）

```python
# ヘビゲーム（SNAKE）設定
SNAKE_CELL = 20
SNAKE_COLS = 40
SNAKE_ROWS = 28
SNAKE_HUD_HEIGHT = 40
SNAKE_FOOD_SCORE = 10
SNAKE_BASE_INTERVAL = 0.14
SNAKE_SPEED_STEP = 0.004
SNAKE_MIN_INTERVAL = 0.06
SNAKE_START_LEN = 3
COLOR_SNAKE_HEAD = (90, 230, 110)
COLOR_SNAKE_BODY = (40, 170, 70)
COLOR_SNAKE_FOOD = (230, 70, 70)
```

## 7. 影響範囲

- 既存ゲーム（DK・テトリス・DK81・アイスクライマー）には一切影響なし。新規ファイル追加と
  `config.py` への追記のみ（既存定数は変更しない）。
- `main.py` / `menu_scene.py` / `menu_thumbnails.py` は今回変更しない
  （別担当者が `register_scene("snake", SnakeScene())` 等を行う前提。シーンID名は
  `"snake"` を推奨として本メモに残すが、実際の命名・登録は別作業）。

## 8. テスト方針

ヘッドレス（`pygame.display` を使わない）で `Snake` / `spawn_food` を直接検証する
デバッグスクリプトを一時ファイルとして作成し実行する:

1. 初期状態から前進すると `body` が正しく1マス移動する（伸びない＝尻尾が動く）
2. `queue_direction` で直近の実移動方向の真反対を指定しても無視される
3. エサに重なる `next_head` で `advance(grew=True)` すると body が1マス伸びる
4. 自分の体に重なる `next_head` で `hits_self` が True を返す
5. グリッド範囲外に出る `next_head` を境界チェックで検出できる（シーン側ロジック相当を
   関数化してテストするか、範囲チェックをテストコード側で明示的に行う）
6. `spawn_food` が `occupied` と重ならない座標を返す（複数回試行して確認）

`pygame` 依存部分（`SnakeScene` の描画・SE 再生・実際のキー入力）は自動テスト対象外とし、
最終確認はユーザーが実機で行う（`main.py` 統合後、別担当者と合わせて）。

## 9. 未決事項 / 設計判断メモ

- リスタート操作（例: R キー）は持たせない。ミス後は ESC でメニューへ戻る前提
  （`GameOverScene` 自体がリスタート機能を持たず、Enter/Space でメニューに戻るのみ＝
  他ゲームと同じ挙動）。
- 専用 SE を追加せず既存の `"score"` / `"death"` を再用する判断は、シンプルさ優先の
  ため。気になるようであれば `known-issues.md` に記録するか、追加作業で
  `synth_audio.py` に `"snake_eat"` 等を新設する。
- 盤面を完全に埋めた場合（`spawn_food` が `None`）の特別な「完全クリア」処理は持たない
  （スコープ外、`1_requirements.md` の「やらないこと」参照）。
