# ダックハント風ガンシューティング — 実装方針

`1_requirements.md` の受け入れ条件を満たすための設計。
既存ゲームと同じ「描画を持たないロジック層」＋「シーン層」の2層構成を踏襲する。

---

## 1. 全体構成

| レイヤ | ファイル | 責務 | pygame 依存 |
|--------|----------|------|-------------|
| ロジック | `game_objects/gun/target.py` | 的の種類・移動・生存管理・当たり判定・得点 | **なし**（座標計算のみ） |
| シーン | `scenes/duck_hunt_scene.py` | ラウンド進行の状態機械・マウス入力・描画・SE・HUD | あり |

`target.py` を pygame 非依存にし、ヘッドレスのデバッグスクリプトで
出現・移動・命中判定・得点計算を検証できるようにする（他ゲームと同方針）。

---

## 2. 的（`target.py`）

### 種類（MVP は2種、後で増やしやすい設計にする）

| 種類 | 移動パターン | 速度 | 得点 | 特徴 |
|------|--------------|------|------|------|
| `BIRD` | 画面下端の左右どちらかから斜め上へ直線移動＋小さな上下の揺れ（サイン波） | 遅め | 100 | 出現頻度が高い基本の的 |
| `UFO`  | 画面左右どちらかの端から水平に高速移動＋小さな上下ボビング | 速め | 300 | 当てにくい高得点の的 |

`kind` 文字列で種別を持ち、`GUN_TARGET_TABLE`（`config.py`）から
速度・得点・半径・寿命を引く（テトリスの `TETROMINO_SHAPES` と同様、
データテーブル方式でパラメータ調整をしやすくする）。

### 状態

```python
class Target:
    kind: str            # "BIRD" / "UFO"
    x, y: float          # 中心座標
    vx, vy: float        # 速度（px/秒）
    radius: float         # 当たり判定半径
    score: int
    age: float            # 経過時間（サイン波・寿命判定に使用）
    lifetime: float        # この時間を過ぎたら「逃した」扱いで消える
```

| メソッド | 内容 |
|----------|------|
| `update(dt)` | `age` 加算、`kind` に応じた移動式で `x, y` を更新 |
| `is_expired()` | `age >= lifetime` または画面外に完全に出たら `True` |
| `hit_test(px, py)` | `(px-x)^2+(py-y)^2 <= (radius+GUN_AIM_ASSIST)^2` |
| `contains reticle assist` | 小さい的でも遊びやすいよう半径に `GUN_AIM_ASSIST`（数px）を加算して判定を甘くする |

移動式（例）：

```python
# BIRD: 斜め直線 + サイン波の上下揺れ
x = x0 + vx * age
y = y0 + vy * age + sin(age * 6) * 6

# UFO: 水平直線 + 緩いボビング
x = x0 + vx * age
y = y0 + sin(age * 3) * 10
```

---

## 3. ラウンド進行の状態機械（`duck_hunt_scene.py`）

```
   ┌────────────────────────────────────────────┐
   │                                              │
   v                                              │
[intro] --1秒経過--> [play] --ラウンド終了条件--> [result]
                        │                            │
                        │                     クリア │  未クリア
                        │                            v      v
                        │                        [intro]  [over]
                        │（次ラウンド）
                        └── 出現待ちの的がなくなり時間・弾も残っている
                            場合は次の的を自動でスポーン（プレイ継続）
```

| 状態 | 内容 | 入力 |
|------|------|------|
| `intro` | 「ROUND N」を1秒程度表示してからプレイ開始 | 無視 |
| `play` | 的が出現しては消える。マウスで狙って撃つ | マウス移動・クリック |
| `result` | ラウンド終了。CLEAR / FAILED を一瞬表示 | 無視 |
| `over` | ゲームオーバー。オーバーレイ表示 | `R` のみ |

**MVP は同時出現数 1体**（撃たれる／逃げられるまで次は出さない）。
複数体同時出現は難易度を上げる余地として `known-issues.md` に残す。

### ラウンド終了条件（いずれか先に成立）

1. その回のラウンドで出す予定の的（`GUN_TARGETS_PER_ROUND`）を全て出し切り、
   最後の的が解決（命中 or 逃した）した
2. 残弾（`ammo`）が 0 になった
3. 残り時間（`time_left`）が 0 になった

### クリア判定

```
hits >= GUN_TARGETS_PER_ROUND * GUN_CLEAR_RATIO  → クリア（次ラウンドへ）
それ未満                                          → ゲームオーバー
```

---

## 4. マウス入力

`handle_input(event)` で以下を処理する：

```python
if event.type == pygame.MOUSEMOTION:
    self.aim_x, self.aim_y = event.pos
elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    if self.state == "play":
        self._fire(event.pos)
elif event.type == pygame.KEYDOWN:
    if event.key == pygame.K_r and self.state == "over":
        self._reset_game()
```

`_fire(pos)` は残弾を1消費し、現在出現中の的に対して `hit_test` を行う。
命中していれば的を消してスコア加算・SE `hit`、外れなら SE `miss` のみ
（残弾はどちらにしても減る＝原作のダックハントと同じ「撃てば弾が減る」仕様）。

照準（レティクル）はカーソル位置に十字マークを描画し、`pygame.mouse.set_visible(False)`
で標準カーソルを隠す（`on_exit` で `True` に戻す＝メニューに戻ったら通常カーソルに戻す）。

---

## 5. 難易度スケーリング（ラウンド番号 `round_no` に応じて）

```python
speed_mult   = 1.0 + (round_no - 1) * 0.15   # 的の速度倍率
lifetime     = max(GUN_MIN_LIFETIME, GUN_BASE_LIFETIME - (round_no - 1) * 0.1)
targets      = min(GUN_MAX_TARGETS, GUN_BASE_TARGETS + (round_no - 1))  # 出題数
time_limit   = max(GUN_MIN_TIME, GUN_BASE_TIME - (round_no - 1) * 2)
ammo         = targets + GUN_AMMO_MARGIN   # ミス許容ぶんの余剰弾
```

ラウンドが進むほど「速い・寿命が短い・数が多い・時間が短い」の複合で難しくなる。

---

## 6. 得点計算

```
命中スコア = target.score（種類ごとの基礎点）
ラウンドクリアボーナス = 100 * round_no（クリア時に加算、やり込み要素を後押し）
```

---

## 7. HUD・画面レイアウト

```
┌──────────────────────────────────────────────────────┐ 800
│ SCORE 001200        AMMO ●●●○○        TIME 00:23     │  <- 上部帯（40px）
│                                                        │
│                  （空・草原などのドット絵背景）          │
│                                                        │
│                     🦆  ← 的（移動中）                  │
│                                                        │
│                                              [+]  ← 照準│
│                                                        │
│ ROUND 3   HITS 4/6                                    │
│ CONTROLS: MOUSE MOVE : AIM / CLICK : SHOOT / R : RESTART / ESC : MENU
└──────────────────────────────────────────────────────┘ 600
```

- 上部帯にスコア・残弾（●○のドット表示）・残り時間
- 下部帯にラウンド数・命中数/ノルマ、操作説明（常時表示）
- 背景は空色の単色＋簡単な雲・草原ドット絵（プリミティブ描画。画像ファイルは使わない）

---

## 8. `config.py` に追加する定数（`GUN_` 接頭辞）

```python
GUN_BASE_TARGETS = 6            # 1ラウンドの基本出題数
GUN_MAX_TARGETS = 14            # 出題数の上限
GUN_CLEAR_RATIO = 0.6           # クリアに必要な命中率
GUN_AMMO_MARGIN = 3             # 出題数に対する弾の余剰
GUN_BASE_TIME = 40.0            # 基本制限時間（秒）
GUN_MIN_TIME = 18.0             # 制限時間の下限
GUN_BASE_LIFETIME = 2.4         # 的の基本寿命（秒）
GUN_MIN_LIFETIME = 1.1          # 的の寿命の下限
GUN_AIM_ASSIST = 6              # 当たり判定の甘さ（px）
GUN_INTRO_TIME = 1.0            # ラウンド開始演出の時間（秒）
GUN_SPAWN_DELAY = 0.5           # 的が消えてから次が出るまでの間隔（秒）

GUN_TARGET_TABLE = {
    "BIRD": {"speed": 160, "score": 100, "radius": 22, "weight": 3},
    "UFO":  {"speed": 260, "score": 300, "radius": 18, "weight": 1},
}
# weight: 出現時の抽選重み（BIRD が出やすく、UFO はたまに高得点チャンスとして出る）

COLOR_GUN_SKY, COLOR_GUN_GROUND, COLOR_GUN_RETICLE, ...  # 背景・照準用の色
```

---

## 9. SE（`synth_audio.py`）

既存 SE を可能な範囲で再利用しつつ、銃声だけ新規追加する。

| 場面 | SE | 備考 |
|------|----|----|
| 発射 | `shoot`（**新規追加**） | 短いノイズ的な破裂音。既存に近い音がないため追加 |
| 命中 | `score`（既存再利用） | ピロッという上昇音をそのまま流用 |
| 外れ | `lock`（既存再利用） | 低い音で「外した」感を出す |
| ラウンドクリア | `clear`（既存再利用） | 既存のファンファーレを流用 |
| ゲームオーバー | `death`（既存再利用） | 既存の下降音を流用 |

`shoot` は `_build_all()` の recipes に1行追加するのみ（他 SE と同じ仕組みに乗せる）。

---

## 10. メニューサムネイル

`menu_thumbnails.py` に `_draw_duck_hunt(surf, w, h)` を追加し `_DRAWERS` に登録。
空色背景＋鳥のシルエット数羽＋照準の十字マークを描く（プリミティブのみ、既存踏襲）。

---

## 11. 影響範囲

既存ゲームのコードには一切手を入れない。変更は以下の追記のみ：

| ファイル | 変更内容 | リスク |
|----------|----------|--------|
| `config.py` | `GUN_` 定数を末尾に追記 | なし（接頭辞で衝突回避） |
| `synth_audio.py` | `recipes` に `"shoot"` を1行追加 | なし（追加のみ） |
| `menu_scene.py` | `GAMES` に1行追加（13件目） | 低。4列×4行目1枚になるレイアウトを目視確認する |
| `menu_thumbnails.py` | 描画関数1つ＋登録1行 | なし |
| `main.py` | import 1行＋`register_scene` 1行 | なし |

> マウス入力は `main.py` の既存イベントループがそのまま全イベントを転送するため、
> `main.py` 自体の変更は不要（import・登録の2行のみ）。

---

## 12. 検証方法

1. **ヘッドレス検証**（scratchpad にデバッグスクリプトを置く）
   - `Target.update` で座標が式通りに変化すること
   - `hit_test` が半径内 / 半径外で正しく True/False を返すこと（アシスト込み）
   - `is_expired` が寿命超過・画面外で正しく True になること
   - ラウンドクリア判定（`hits >= targets * ratio`）が境界値で正しいこと
2. **実起動確認**：`python src/main.py` でメニュー → DUCK HUNT → プレイ →
   ラウンドクリア → 難易度上昇の体感 → 意図的に外し続けてゲームオーバー →
   `R` リスタート → `ESC` メニューの流れを目視確認
