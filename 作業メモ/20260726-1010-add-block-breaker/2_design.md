# 設計: ブロック崩し

`1_requirements.md` のスコープを実装するための方針メモ。既存のドンキーコング／
アイスクライマーと同じ構造（`BaseScene` 継承シーン ＋ `game_objects/` のロジック分離、
残機制で共通の `game_over` / `clear` シーンへ `request_scene` する）に合わせる。
メニュー統合（`menu_scene.py` / `menu_thumbnails.py`）は対象外。

## 1. ファイル構成

| ファイル | 役割 | 新規/変更 |
|----------|------|-----------|
| `src/game_objects/block_breaker/brick.py` | ブロック 1 個の矩形・色・得点・生存フラグ、`Brick` クラス、行配置の生成関数 | 新規 |
| `src/game_objects/block_breaker/paddle.py` | パドルの位置・移動・反射角計算、`Paddle` クラス | 新規 |
| `src/game_objects/block_breaker/ball.py` | ボールの位置・速度・壁/パドル/ブロック反射、`Ball` クラス | 新規 |
| `src/game_objects/block_breaker/__init__.py` | パッケージ化 | 新規 |
| `src/scenes/block_breaker_scene.py` | ゲーム進行・入力・スコア・残機・描画（`BlockBreakerScene`） | 新規 |
| `src/config.py` | `BREAKOUT_` 定数群を追記 | 変更 |
| `src/main.py` | `BlockBreakerScene` を `register_scene("block_breaker", ...)` | 変更 |
| `src/utils/synth_audio.py` | 不足 SE（`paddle_hit` / `wall_hit` / `brick_break`）を `recipes` に追記 | 変更 |

> 衝突ロジック（パドル反射角・ブロック反射軸判定）を `Ball`/`Paddle`/`Brick` に閉じ込め、
> シーンからは「今フレームの状態で判定を呼ぶだけ」にする。ヘッドレスでの
> スモークテストをしやすくするため。

## 2. データ構造

### ブロック（brick.py）

```python
class Brick:
    def __init__(self, x, y, w, h, color, score):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.score = score
        self.alive = True

def build_bricks():
    """BREAKOUT_ROWS × BREAKOUT_COLS の固定レイアウトを 1 パターン生成して返す。
    行ごとに ROW_COLORS / ROW_SCORES を上から適用（上の行ほど高得点）。
    """
```

- 座標計算はブロック単体の生成時に確定させ、`Brick.rect` を Ball 側の
  `colliderect` 判定にそのまま使う。

### パドル（paddle.py）

`class Paddle`:
- 属性: `rect`（`pygame.Rect`）、移動速度 `BREAKOUT_PADDLE_SPEED`
- `update(dt, keys)`: 左右キーで `rect.x` を更新し、画面端でクランプ
- `bounce_offset(ball_cx) -> float`: パドル中心からのズレを `-1.0〜1.0` に
  正規化して返す（左端 = -1、中央 = 0、右端 = +1）。反射角計算は Ball 側で行う。

### ボール（ball.py）

`class Ball`:
- 属性: `x, y`（中心座標・float）、`vx, vy`（速度）、`radius`
- `update(dt)`: 位置更新のみ（衝突はシーン側で `Ball` のメソッドを呼んで処理）
- `reflect_walls(screen_width)`: 左右壁で `vx` 反転、天井で `vy` 反転
- `bounce_off_paddle(paddle)`: `paddle.bounce_offset()` を使い、
  角度 = `offset * BREAKOUT_MAX_BOUNCE_ANGLE` として `vx, vy` を再計算
  （速度の大きさ `BREAKOUT_BALL_SPEED` は一定に保つ）
- `bounce_off_brick(brick_rect)`: ボール中心とブロック矩形の重なりの
  縦横の浸透量を比較し、小さい方の軸を反転する簡易処理
  （角当たりの完全な物理再現はしない＝スコープ簡素化）
- `is_below(y_limit) -> bool`: 画面下端を超えたか（ミス判定用）

## 3. ゲーム進行（block_breaker_scene.py）

### 状態

`self.state`: `"ready"`（ボールがパドルに乗って発射待ち） / `"play"`（ボール動作中）

主な属性: `paddle`, `ball`, `bricks`（`Brick` のリスト）, `score`, `lives`。

### 入力（handle_input: KEYDOWN）

| キー | 動作 |
|------|------|
| スペース | `state == "ready"` のときボールを発射（`state = "play"`、初速を上方向にセット） |

> ← → はキー押しっぱなし想定のため `update` 内で `pygame.key.get_pressed()` を見る
> （テトリスの移動処理と同様）。Esc によるメニュー復帰は `main.py` の共通処理が担当。

### 更新（update: dt）

- `ready` 時: パドルのみ更新し、ボールはパドル中心上に追従させる。
- `play` 時:
  1. `paddle.update(dt, keys)`
  2. `ball.update(dt)`
  3. 壁・天井反射 → SE `wall_hit`
  4. パドルと衝突していれば `bounce_off_paddle` → SE `paddle_hit`
  5. 生存ブロックそれぞれと当たり判定 → 当たったブロックは `alive = False`、
     `bounce_off_brick`、`score += brick.score`、SE `brick_break`
  6. 全ブロック `alive == False` になったら
     `self.request_scene("clear", score=self.score, title="STAGE CLEAR!", message="...")`
  7. `ball.is_below(SCREEN_HEIGHT)` なら `lives -= 1`。
     `lives <= 0` なら `self.request_scene("game_over", score=self.score)`、
     そうでなければパドル・ボールを初期位置に戻して `state = "ready"`

### ブロック衝突の判定順序について

同一フレームで複数ブロックに同時衝突する可能性は低い前提で、
「最初に重なりが見つかったブロック 1 個のみ」を処理する簡易実装とする
（貫通・複数個同時破壊はスコープ外、気になれば known-issues へ）。

## 4. 得点表（例・config で調整可能）

| 行（上から） | 色 | 得点 |
|------|------|------|
| 1〜2 行目 | 赤 | 50 |
| 3〜4 行目 | 黄 | 30 |
| 5〜6 行目 | 緑 | 10 |

## 5. 描画レイアウト（800×600）

- ブロック領域: 上部 `y: 60〜240` あたりに `BREAKOUT_ROWS=6 × BREAKOUT_COLS=10`
  を配置（ブロック幅 `72px` × 高さ `24px`、隙間 `4px`、左右マージンで中央寄せ）
- パドル: `y = 560` 付近、幅 `90px` × 高さ `14px`
- ボール: 半径 `8px`
- HUD: 左上に `SCORE`、右上に残機アイコン（DK の頭アイコンと同様の簡易図形）
- `ready` 時: 画面下部に「SPACE: LAUNCH」ヒントを点滅表示

## 6. config.py への追加（例）

```python
# ブロック崩し設定
BREAKOUT_ROWS = 6
BREAKOUT_COLS = 10
BREAKOUT_BRICK_W = 72
BREAKOUT_BRICK_H = 24
BREAKOUT_BRICK_GAP = 4
BREAKOUT_BRICK_TOP = 60
BREAKOUT_PADDLE_W = 90
BREAKOUT_PADDLE_H = 14
BREAKOUT_PADDLE_Y = 560
BREAKOUT_PADDLE_SPEED = 340       # pixels/sec
BREAKOUT_BALL_RADIUS = 8
BREAKOUT_BALL_SPEED = 320         # pixels/sec（一定値を維持）
BREAKOUT_MAX_BOUNCE_ANGLE = 60    # 度（パドル端で跳ね返る最大角）
BREAKOUT_START_LIVES = 3

# 行ごとの色・得点（上から）
BREAKOUT_ROW_COLORS = [COLOR_RED, COLOR_RED, COLOR_YELLOW, COLOR_YELLOW, COLOR_GREEN, COLOR_GREEN]
BREAKOUT_ROW_SCORES = [50, 50, 30, 30, 10, 10]
```

## 7. 影響範囲

- 既存ゲームには影響なし。シーンを追加するだけ。
- `main.py` に import 1行 ＋ register 1行（メニュー統合は別担当のため対象外）。
- `config.py` は追記のみ（既存定数は変更しない）。
- `clear_scene.py` / `game_over_scene.py` は既存の kwargs（`score` / `title` / `message`）
  だけで対応可能なため変更不要（アイスクライマーで汎用化済み）。

## 8. テスト方針

ヘッドレス（`pygame.display` を使わない）で `Ball` / `Paddle` / `Brick` を
直接検証するスモークテストを一時スクリプトで実行する:

1. ボールが左右壁・天井で正しく反転する
2. パドル中心で当たると真上（`vx ≈ 0`）、端で当たると斜めに反射する
3. ブロックに当てると `alive = False` になり、スコアが加算される
4. 全ブロックを破壊すると「クリア」条件が真になる
5. ボールが画面下端を越えると「ミス」条件が真になる

`python src/main.py` でシーン起動 → ヘッドレス自動プレイ（パドルをボールに追従させる
単純な AI）で 1 ステージ通しクリアを確認する。描画・実操作の最終確認はユーザーが実機で行う。

## 9. 未決事項 / 設計判断メモ

- ブロックとボールの衝突は簡易軸判定（浸透量の小さい軸を反転）。角当たりの
  完全な物理再現はしない。気になる挙動が出たら `known-issues.md` へ記録する。
- ボール速度は一定値を維持する方針（テトリスのようなレベルアップ加速は今回はなし）。
