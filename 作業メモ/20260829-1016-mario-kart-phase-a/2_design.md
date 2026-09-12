# 設計: マリオカート フェーズA（Mode7風レンダリング＋運転＋タイム計測）

`1_requirements.md` のスコープを実装するための方針メモ。他ゲームと同じ構造
（`BaseScene` 継承シーン＋ `game_objects/` のロジック分離）に合わせつつ、
本作特有の疑似3D描画エンジンを新設する。

## 1. ファイル構成

| ファイル | 役割 | 新規/変更 |
|----------|------|-----------|
| `src/game_objects/mario_kart/track.py` | コース形状（スタジアム型）・オントラック判定・周回検出 | 新規 |
| `src/game_objects/mario_kart/renderer.py` | Mode7風スキャンライン描画（numpy） | 新規 |
| `src/game_objects/mario_kart/kart.py` | 自機カートの物理（加速・操舵・オフトラック減速） | 新規 |
| `src/scenes/mario_kart_scene.py` | ゲーム進行・入力・HUD・状態機械 | 新規 |
| `src/config.py` | `MK_` 接頭辞で定数追記 | 変更 |
| `src/scenes/menu_scene.py` | 「MARIO KART」のシーンキーを実装済みに変更 | 変更 |
| `src/main.py` | `MarioKartScene` を登録 | 変更 |
| `requirements.txt` | `numpy` を追加 | 変更 |

> レンダリングとロジック（コース判定・物理・周回検出）を分離するのは、
> ヘッドレス・スモークテスト（pygame 描画なし）で座標計算だけを検証しやすくするため。

## 2. 座標系とコース形状（track.py）

ワールド座標はピクセル相当の単位（1 unit ≈ 1cm 換算のイメージ、実寸に意味はない）。

コースは **スタジアム型（角丸長方形）** の中心線 1 本として定義する：

- 直線区間の半長 `MK_TRACK_STRAIGHT_HALF`（中心線の直線部分は `x ∈ [-half, +half]`,
  `y = ±MK_TRACK_RADIUS` の上下2本）
- 両端の半円区間は半径 `MK_TRACK_RADIUS`、中心 `(±half, 0)`
- 路面の半幅 `MK_TRACK_ROAD_HALF_WIDTH`、縁石帯の幅 `MK_TRACK_CURB_WIDTH`

`track.py` は以下を提供する：

```python
def distance_to_centerline(x, y) -> float | ndarray:
    """点 (x, y) から中心線までの符号なし距離。x, y は numpy 配列可（ベクトル化対応）。"""

def surface_at(x, y) -> "road" | "curb" | "grass":
    """distance_to_centerline を road_half_width / (road_half_width+curb_width) で
    しきい値判定して分類する（ベクトル化版は数値コード 0/1/2 を返す）。"""

def arc_length_param(x, y) -> float | ndarray:
    """中心線に沿ったおおよその位置（縁石の縞模様の周期に使う）。
    直線区間は x をそのまま、円弧区間は中心角 × 半径を使う。"""
```

`distance_to_centerline` の実装方針（直線と円弧をベクトル化で場合分け）：

- `|x| <= half`（直線区間の範囲内）: 距離 = `min(|y - R|, |y + R|)`
- `x > half`（右の半円）: 中心 `(half, 0)` までの距離 `r = sqrt((x-half)^2 + y^2)`,
  距離 = `|r - R|`
- `x < -half`（左の半円）: 同様に中心 `(-half, 0)`

numpy では `np.where` で3区分を合成する。

### 周回検出（lap check）

フィニッシュラインは上側の直線区間中央（`x = 0, y = MK_TRACK_RADIUS` 付近）に
垂直な線分として定義する。前フレームと現フレームのカート x 座標の符号が
`x=0` をまたいだ（前 < 0 かつ今 ≥ 0）、かつ `y` がその直線の路面幅内、
かつ進行方向（速度ベクトルと直線区間の進行方向の内積）が正のときのみ
1 周とカウントする（逆走・惰性での誤検出を防ぐ）。

## 3. Mode7風レンダリング（renderer.py）

### 3.1 カメラモデル

- カート位置 `(px, py)`、向き `heading`（ラジアン、+x方向が0）を持つ。
- カメラはカート位置から `heading` の逆方向に `MK_CAM_BACK` だけ引いた位置、
  高さ `MK_CAM_HEIGHT`、向きは `heading` に固定（簡易チェイスカメラ、
  カメラ自身の慣性・追従遅延は持たせない＝フェーズA では簡素化）。

### 3.2 スキャンライン変換

画面下半分（`y ∈ [MK_HORIZON_Y, SCREEN_HEIGHT)`）の各行 `row`（0 = 地平線直下）について：

```
z(row)      = MK_CAM_HEIGHT * MK_PROJ_SCALE / (row + 1)        # 前方距離（遠近の要）
world_w(row)= z(row) * (SCREEN_WIDTH / MK_FOCAL_LENGTH)        # その行で画面に映る横幅
center      = camera_pos + heading_vec * z(row)
left        = center - right_vec * (world_w(row) / 2)
```

行内の各列 `x`（0..SCREEN_WIDTH-1）は `left` から `right = center + right_vec*world_w/2`
への線形補間でワールド座標を得る。これは Mode7 の本質（各走査線が
ワールド平面のアフィン変換になっている）そのもの。

numpy でのベクトル化：`row` と `x` を 2 次元にブロードキャストして
`world_x`, `world_y` を一度に計算し、`track.surface_at` に通して
`road / curb(縞) / grass` の色を割り当て、`pygame.surfarray.blit_array` で転送する。

- 縁石の縞は `track.arc_length_param` を `MK_CURB_STRIPE_LEN` で割った整数部の偶奇で
  2 色を切り替える。
- 遠方ほど薄暗くする簡易フォグ（`row` が小さいほど色を暗く補間）で奥行きの手がかりを足す。
- 空（`y < MK_HORIZON_Y`）は単色〜簡易グラデーションで塗る（他ゲームの空グラデと同系統）。

### 3.3 パフォーマンス

800×600 中、路面描画は概ね下半分（約 800×300 = 240,000 px）。numpy の
ベクトル演算（`np.where` / ブロードキャスト四則演算）で 1 フレームぶんを
一括計算するため、Python ループは行わない。`pygame.surfarray` で
Surface と ndarray を相互変換する。

## 4. カート物理（kart.py）

簡易アーケード物理（ドリフトなし、フェーズA スコープ）：

```python
class Kart:
    x, y: float          # ワールド座標
    heading: float       # ラジアン
    speed: float         # 現在速度（前進+/後退-）

    def update(self, dt, accel_input, steer_input, on_track: bool):
        target_accel = MK_ACCEL if accel_input > 0 else (-MK_BRAKE if accel_input < 0 else 0)
        self.speed += target_accel * dt
        self.speed -= self.speed * MK_DRAG * dt          # 空気抵抗的な減衰
        max_speed = MK_MAX_SPEED if on_track else MK_OFFTRACK_MAX_SPEED
        self.speed = clamp(self.speed, MK_MAX_REVERSE_SPEED, max_speed)
        if not on_track:
            self.speed -= self.speed * MK_OFFTRACK_EXTRA_DRAG * dt  # 芝生の追加減衰

        turn = steer_input * MK_TURN_RATE * dt
        # 停止時は曲がれない（原作寄りの挙動）
        if abs(self.speed) > MK_TURN_MIN_SPEED:
            self.heading += turn * sign(self.speed)

        self.x += cos(self.heading) * self.speed * dt
        self.y += sin(self.heading) * self.speed * dt
```

`on_track` はシーン側が毎フレーム `track.surface_at(kart.x, kart.y) != "grass"` で判定し、
`kart.update` に渡す（kart.py は track.py に依存させない＝役割分離）。

## 5. シーン進行（mario_kart_scene.py）

### 状態

`self.state`: `"race"`（唯一の実質ステート。フェーズA は CPU もミスもないため
dying / game_over 相当は無い）。3周完了で `request_scene("clear", ...)`。

主な属性: `kart`（Kart）、`lap`（現在周回数, 1始まり）、`race_time`（合計経過秒）、
`lap_times`（周回ごとのタイムのリスト）、`best_lap`（クラス変数、実行中のみ保持）。

### 入力・更新

- `pygame.key.get_pressed()` で ↑↓←→ を毎フレーム読み、accel_input / steer_input を作る
  （他ゲームの `keys = pygame.key.get_pressed()` パターンを踏襲）。
- `update(dt)`: `track.surface_at` でオントラック判定 → `kart.update` →
  周回検出 → 3周目完了で `race_time` を確定し `clear` へ遷移。

### 描画

1. `renderer.draw_ground(screen, kart, track)` で地面（Mode7）
2. 自機カートのスプライト（固定位置、画面下部中央寄りに簡易ポリゴンで描画。
   実际の3Dモデルではなく他ゲーム同様 pygame プリミティブ）
3. HUD（ラップ・タイム・ベストラップ）

## 6. config.py への追加（例）

```python
# マリオカート設定（フェーズA）
MK_TRACK_STRAIGHT_HALF = 900
MK_TRACK_RADIUS = 500
MK_TRACK_ROAD_HALF_WIDTH = 260
MK_TRACK_CURB_WIDTH = 40
MK_CURB_STRIPE_LEN = 120

MK_CAM_HEIGHT = 220
MK_CAM_BACK = 260
MK_HORIZON_Y = 260
MK_PROJ_SCALE = 90000
MK_FOCAL_LENGTH = 280

MK_MAX_SPEED = 620
MK_MAX_REVERSE_SPEED = -200
MK_OFFTRACK_MAX_SPEED = 220
MK_ACCEL = 420
MK_BRAKE = 620
MK_DRAG = 0.6
MK_OFFTRACK_EXTRA_DRAG = 2.2
MK_TURN_RATE = 2.6          # rad/sec 相当の係数
MK_TURN_MIN_SPEED = 15

MK_LAPS = 3
```

数値は初期見積りで、実装後に触感を見ながら調整する（受け入れ条件を満たす範囲で
config.py のみの変更として許容）。

## 7. 影響範囲

- 既存ゲームには影響なし。シーンを1つ追加するだけ。
- `menu_scene.py` の `GAMES` 配列は該当行のシーンキーを `None → "mario_kart"` に変更するのみ。
- `requirements.txt` に `numpy` を追加（新規依存）。
- `config.py` は追記のみ（既存定数は変更しない）。

## 8. テスト方針

ヘッドレス（`pygame.display` なし、または dummy ドライバ）で以下を検証する：

1. `track.distance_to_centerline` / `surface_at` が直線区間・円弧区間・境界付近で
   期待どおりの分類を返す（単体テスト的な直接呼び出し）
2. `Kart.update` を1000フレームぶん回し、加速→定常速度収束、オフトラックでの
   減速が発生することを数値で確認
3. `MarioKartScene` を numpy ダミー環境で生成し、周回検出ロジックが
   フィニッシュラインを跨いだ座標更新で `lap` をインクリメントすることを確認
4. `python src/main.py` を dummy ドライバで起動し、メニュー選択 → シーン遷移 →
   数百フレームの `update`/`draw` が例外なく通ることを確認（描画パフォーマンスの
   粗い目安として1フレームの処理時間も計測する）

実際の運転フィーリング・見た目の最終確認はユーザーが実機で行う
（フェーズAでは数値調整の余地が大きいため）。

## 9. 未決事項・known-issues 反映候補

- チェイスカメラに追従遅延・バウンドを持たせていない（フェーズA は簡素化）。
  体感が硬い場合はフェーズB以降で検討。
- 縁石の縞模様は概算の弧長パラメータで近似しており、直線⇔円弧の継ぎ目で
  縞のピッチが僅かにズレる可能性がある。気になれば後日 known-issues に記録する。
- コースは1本のみ、分岐・高低差なし。
