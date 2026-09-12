# ゲーム全体の定数・設定値

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Retro Game Center"

# 物理
GRAVITY = 1200          # pixels/sec^2（落下加速度）
JUMP_POWER = 430        # pixels/sec（ジャンプ初速）

# プレイヤー（マリオ）設定
PLAYER_WIDTH = 26
PLAYER_HEIGHT = 32
PLAYER_SPEED = 135      # pixels/sec（左右移動）
CLIMB_SPEED = 95        # pixels/sec（はしご昇降）
RESPAWN_INVINCIBLE = 1.5  # 復帰後の無敵時間（秒）

# 樽（バレル）設定
BARREL_RADIUS = 13
BARREL_SPEED = 105      # pixels/sec（鉄骨を転がる速度）
BARREL_LADDER_CHANCE = 0.35  # はしごを降りる確率
BARREL_SPAWN_INTERVAL = 2.2  # 生成間隔（秒）

# スコア・ライフ
START_LIVES = 3
JUMP_BONUS = 100        # 樽を飛び越えた時の得点
CLEAR_BONUS_START = 5000  # ボーナス（時間で減少、クリア時に加算）
CLEAR_BONUS_DRAIN = 100   # ボーナス減少量（毎秒）

# 色定義（RGB）
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (228, 0, 0)
COLOR_GREEN = (0, 220, 60)
COLOR_BLUE = (40, 90, 230)
COLOR_GRAY = (128, 128, 128)
COLOR_YELLOW = (255, 216, 0)
COLOR_GIRDER = (236, 70, 90)     # 鉄骨（赤ピンク）
COLOR_GIRDER_DARK = (150, 30, 50)
COLOR_LADDER = (90, 200, 230)    # はしご（水色）
COLOR_BARREL = (170, 100, 40)    # 樽（茶）
COLOR_BARREL_BAND = (90, 50, 15)
COLOR_DK = (120, 72, 40)         # ドンキーコング（茶）
COLOR_DK_FACE = (210, 170, 120)
COLOR_PAULINE = (240, 90, 160)   # ポーリン（ピンク）

# テトリス設定
TETRIS_COLS = 10
TETRIS_ROWS = 20
TETRIS_CELL = 26
TETRIS_BASE_FALL = 0.8     # レベル1の落下間隔（秒）
TETRIS_FALL_STEP = 0.07    # レベルごとの短縮量
TETRIS_MIN_FALL = 0.08     # 落下間隔の下限
TETRIS_BOARD_X = 210       # 盤面左上 X
TETRIS_BOARD_Y = 40        # 盤面左上 Y

# テトリミノ色（7種）
COLOR_T_CYAN   = (0, 220, 230)   # I
COLOR_T_YELLOW = (240, 220, 0)   # O
COLOR_T_PURPLE = (170, 70, 220)  # T
COLOR_T_GREEN  = (0, 210, 80)    # S
COLOR_T_RED    = (230, 60, 60)   # Z
COLOR_T_BLUE   = (50, 90, 230)   # J
COLOR_T_ORANGE = (240, 150, 30)  # L
COLOR_T_GRID   = (40, 40, 55)    # 盤面のグリッド線
COLOR_T_FRAME  = (120, 130, 170) # 盤面の枠

# パス
MAPS_DIR = "assets/maps"
TILESETS_DIR = "assets/tilesets"
SPRITES_DIR = "assets/sprites"

# ==========================================================================
# ドンキーコング '81（DK81）設定 — 本作専用。既存定数と衝突しないよう DK81_ 接頭辞
# ==========================================================================

# スコア・進行
DK81_START_LIVES = 3
DK81_JUMP_BONUS = 100          # 樽を飛び越えた時の得点
DK81_SMASH_BONUS = 500         # ハンマーで破壊した時の得点（Milestone B）
DK81_BONUS_START = 5000        # ボーナスタイマー初期値
DK81_BONUS_DRAIN = 100         # ボーナス減少量（毎秒）

# プレイヤー
DK81_PLAYER_WIDTH = 24
DK81_PLAYER_HEIGHT = 30
DK81_PLAYER_SPEED = 130        # pixels/sec（左右移動）
DK81_CLIMB_SPEED = 90          # pixels/sec（はしご昇降）
DK81_JUMP_POWER = 420          # pixels/sec（ジャンプ初速）
DK81_RESPAWN_INVINCIBLE = 1.5  # 復帰後の無敵時間（秒）
DK81_DEATH_TIME = 1.6          # やられ演出の時間（秒）
DK81_HAMMER_TIME = 9.0         # ハンマー効果時間（秒・Milestone B）

# 樽
DK81_BARREL_RADIUS = 12
DK81_BARREL_SPEED = 110        # pixels/sec（鉄骨を転がる速度）
DK81_BARREL_LADDER_CHANCE = 0.3   # はしごを降りる確率
DK81_BARREL_SPAWN_INTERVAL = 2.5  # 生成間隔（秒）

# 演出
DK81_INTRO_TIME = 1.6          # イントロ表示時間（秒・任意キーでスキップ可）

# 色（DK81 専用）
DK81_COLOR_OIL_DRUM = (40, 70, 190)       # オイルドラム（青）
DK81_COLOR_OIL_BAND = (120, 160, 240)
DK81_COLOR_FLAME = (255, 140, 30)         # 炎（オレンジ）
DK81_COLOR_FLAME_CORE = (255, 220, 80)    # 炎の芯（黄）
DK81_COLOR_SKIN = (245, 200, 150)         # 肌色
DK81_COLOR_HAMMER = (200, 160, 60)        # ハンマー（Milestone B）

# ==========================================================================
# アイスクライマー（ICE）設定 — 本作専用。ICE_ 接頭辞で既存定数と衝突を避ける
# ==========================================================================

# セル・ステージ寸法
ICE_CELL = 32                  # 氷ブロック 1 マスの辺（px）
ICE_COLS = 25                  # 山の横幅（セル数, 25*32=800）
ICE_FLOOR_GAP = 3              # 段と段の垂直間隔（セル数）
ICE_FLOORS = 8                 # 氷の床の段数（1 ステージ）
ICE_GROUND_Y = 560             # 最下段の床「上面」の画面 y（開始時の見え）

# プレイヤー（ポポ）
ICE_PLAYER_W = 26
ICE_PLAYER_H = 30
ICE_PLAYER_SPEED = 155         # pixels/sec（左右移動）
# ジャンプは「1 段（ICE_FLOOR_GAP セル=96px）を越えて上段に乗れる」高さが必要。
# 到達高 ≒ v^2/(2g)。v=560, g=1350 で ≒116px（96px+余裕）。
ICE_JUMP_POWER = 560           # pixels/sec（ジャンプ初速）
ICE_GRAVITY = 1350             # pixels/sec^2（落下加速度・やや重め）
ICE_AIR_CONTROL = 0.9          # 空中での左右操作の効き（0〜1）
ICE_RESPAWN_INVINCIBLE = 1.6   # 復帰後の無敵時間（秒）
ICE_DEATH_TIME = 1.4           # やられ演出の時間（秒）

# スコア・ライフ
ICE_START_LIVES = 3
ICE_ICE_BREAK_SCORE = 10       # 氷ブロックを 1 個割った得点
ICE_TOPI_SCORE = 300           # トッピー撃破の得点
ICE_ICICLE_DODGE = 0           # （つらら回避は加点なし）
ICE_SUMMIT_TIME = 12.0         # 山頂ボーナスの制限時間（秒）
ICE_CONDOR_BONUS = 3000        # コンドルを掴んだ時のボーナス

# 敵（トッピー）
ICE_TOPI_SPEED = 55            # pixels/sec（床を歩く速度）
ICE_TOPI_SPAWN_INTERVAL = 3.4  # 生成間隔（秒）
ICE_TOPI_MAX = 3               # 同時出現の上限
ICE_TOPI_REPAIR_TIME = 1.1     # 穴を 1 マス塞ぐのにかける時間（秒）

# つらら
ICE_ICICLE_SPAWN_INTERVAL = 2.8   # 生成間隔（秒）
ICE_ICICLE_FALL = 360             # pixels/sec（落下速度）
ICE_ICICLE_WARN = 0.7             # 落下前の予兆（震え）時間（秒）

# 色（ICE 専用）
ICE_COLOR_SKY_TOP = (30, 40, 90)      # 空グラデ上
ICE_COLOR_SKY_BOT = (70, 120, 190)    # 空グラデ下
ICE_COLOR_SUMMIT_SKY = (18, 24, 60)   # 山頂の夜空
ICE_COLOR_ICE = (170, 220, 245)       # 氷ブロック（水色）
ICE_COLOR_ICE_HI = (225, 245, 255)    # 氷ハイライト
ICE_COLOR_ICE_DARK = (110, 165, 205)  # 氷の陰
ICE_COLOR_GROUND = (120, 140, 165)    # 割れない土台の岩
ICE_COLOR_GROUND_HI = (160, 180, 205)
ICE_COLOR_POPO = (40, 90, 220)        # ポポの服（青）
ICE_COLOR_POPO_TRIM = (245, 245, 255) # ポポの縁取り（白）
ICE_COLOR_POPO_FACE = (250, 215, 170) # 顔
ICE_COLOR_HAMMER_HEAD = (210, 175, 70)   # ハンマー頭（金）
ICE_COLOR_TOPI = (240, 240, 250)      # トッピー（白）
ICE_COLOR_TOPI_DARK = (180, 185, 205)
ICE_COLOR_ICICLE = (200, 235, 250)    # つらら
ICE_COLOR_CONDOR = (60, 55, 70)       # コンドル（黒紫）
ICE_COLOR_CLOUD = (235, 240, 250)     # 山頂の雲足場

# ==========================================================================
# スペースインベーダー（SI）設定 — 本作専用。SI_ 接頭辞で既存定数と衝突を避ける
# ==========================================================================

# 自機
SI_PLAYER_W = 36
SI_PLAYER_H = 18
SI_PLAYER_Y = 540              # 自機の上端 y
SI_PLAYER_SPEED = 240           # pixels/sec（左右移動）
SI_PLAYER_LIVES = 3
SI_RESPAWN_INVINCIBLE = 1.5     # 復帰後の無敵時間（秒）
SI_DEATH_TIME = 1.2             # やられ演出の時間（秒）

# 自弾
SI_BULLET_W = 3
SI_BULLET_H = 14
SI_BULLET_SPEED = 640           # pixels/sec（上方向）

# インベーダー編隊
SI_INV_ROWS = 5
SI_INV_COLS = 11
SI_INV_W = 32
SI_INV_H = 22
SI_INV_GAP_X = 16
SI_INV_GAP_Y = 16
SI_INV_TOP = 80                 # 編隊の初期 y（最上段の上端）
SI_INV_BASE_SPEED = 40          # pixels/sec（残数が多いときの横移動速度）
SI_INV_MAX_SPEED = 260          # pixels/sec（残り1体のときの速度上限）
SI_INV_DROP = 12                # 端に到達したときの下降量（px）
SI_INV_INVASION_Y = SI_PLAYER_Y - 40  # ここまで下降したら侵略＝即ゲームオーバー
SI_INV_ROW_SCORES = [30, 20, 20, 10, 10]  # 上段から順（原作準拠のイメージ）

# 敵弾
SI_ENEMY_BULLET_W = 3
SI_ENEMY_BULLET_H = 14
SI_ENEMY_BULLET_SPEED = 260     # pixels/sec（下方向）
SI_ENEMY_BULLET_MAX = 3         # 画面内に同時に存在できる敵弾数の上限
SI_ENEMY_SHOOT_INTERVAL = 0.55  # 敵弾を撃つか判定する間隔（秒）

# シールド（バンカー）
SI_SHIELD_CELL = 8              # シールド1ブロックの辺（px）
SI_SHIELD_Y = SI_PLAYER_Y - 110  # シールド上端の y
SI_SHIELD_COUNT = 4

# UFO（ボーナス）
SI_UFO_W = 40
SI_UFO_H = 18
SI_UFO_Y = 50
SI_UFO_SPEED = 130              # pixels/sec
SI_UFO_MIN_INTERVAL = 12.0      # 出現間隔（秒・最短）
SI_UFO_MAX_INTERVAL = 22.0      # 出現間隔（秒・最長）
SI_UFO_SCORES = [50, 100, 150, 300]

# 色（SI 専用）
SI_COLOR_PLAYER = (90, 210, 255)
SI_COLOR_BULLET_PLAYER = (255, 255, 255)
SI_COLOR_BULLET_ENEMY = (255, 210, 80)
SI_COLOR_INVADER_ROWS = [
    (255, 90, 120),   # 1段目（最上段・高得点）
    (255, 180, 60),
    (255, 180, 60),
    (90, 230, 120),
    (90, 230, 120),
]
SI_COLOR_SHIELD = (90, 220, 110)
SI_COLOR_UFO = (230, 80, 220)

# ==========================================================================
# マリオカート（MK）設定 — 本作専用。MK_ 接頭辞で既存定数と衝突を避ける
# フェーズA：Mode7風レンダリング＋運転＋タイム計測（CPU・アイテムなし）
# ==========================================================================

# コース形状（スタジアム型）
MK_TRACK_STRAIGHT_HALF = 900     # 直線区間の半長
MK_TRACK_RADIUS = 500            # 両端の半円半径（中心線基準）
MK_TRACK_ROAD_HALF_WIDTH = 260   # 路面の半幅
MK_TRACK_CURB_WIDTH = 40         # 縁石帯の幅
MK_CURB_STRIPE_LEN = 120         # 縁石の縞の周期（弧長パラメータ基準）
MK_LAPS = 3                      # レースの周回数
MK_LAP_MIN_PROGRESS_RATIO = 0.85  # 直前のラップ判定からこの割合(×2π)以上
                                   # 進行角度が進んでいないと1周と認めない
                                   # （スタート地点近くでの偽1周カウント防止）

# カメラ・投影
MK_CAM_HEIGHT = 220              # カメラの高さ
MK_CAM_BACK = 260                # カートから後方に引く距離
MK_HORIZON_Y = 260               # 地平線の画面 y 座標
MK_PROJ_SCALE = 464              # 疑似遠近スケール（最前列 z ≈ 300 になるよう逆算）
MK_FOCAL_LENGTH = 280            # 画角相当の焦点距離

# カート物理
MK_MAX_SPEED = 620               # pixels/sec（世界座標上の最高速度）
MK_MAX_REVERSE_SPEED = -200      # pixels/sec（後退の最高速度）
MK_OFFTRACK_MAX_SPEED = 220      # コースアウト時の速度上限
MK_ACCEL = 420                   # pixels/sec^2（加速）
MK_BRAKE = 620                   # pixels/sec^2（ブレーキ）
MK_DRAG = 0.6                    # 速度に比例する空気抵抗係数（毎秒）
MK_OFFTRACK_EXTRA_DRAG = 2.2     # コースアウト時に追加される減衰係数（毎秒）
MK_TURN_RATE = 2.6               # 操舵の角速度係数（rad/sec 相当）
MK_TURN_MIN_SPEED = 15           # この速度未満では操舵が効かない

# 色（MK 専用）
MK_COLOR_SKY_TOP = (110, 180, 240)
MK_COLOR_SKY_BOTTOM = (200, 225, 250)
MK_COLOR_ROAD = (70, 70, 78)
MK_COLOR_ROAD_DARK = (60, 60, 68)
MK_COLOR_CURB_A = (220, 60, 60)
MK_COLOR_CURB_B = (240, 240, 240)
MK_COLOR_GRASS = (60, 170, 80)
MK_COLOR_GRASS_DARK = (50, 150, 70)
MK_COLOR_KART_BODY = (220, 40, 40)
MK_COLOR_KART_TRIM = (250, 220, 60)

# ==========================================================================
# マリオカート フェーズB＋C：CPU対戦・アイテム
# ==========================================================================

# ビルボード投影（他カート・アイテム類を疑似3Dの平面スプライトとして描画）
MK_BILLBOARD_MIN_Z = 40          # これより近い（≒背後含む）と描画しない
MK_BILLBOARD_MAX_Z = 6000        # これより遠いと描画しない
MK_KART_WORLD_SIZE = 140         # カート1台の見かけ上のワールドサイズ
MK_ITEMBOX_WORLD_SIZE = 90
MK_BANANA_WORLD_SIZE = 50
MK_SHELL_WORLD_SIZE = 55

# CPU
MK_CPU_COUNT = 3
MK_CPU_LOOKAHEAD_BASE = 260.0    # 目標点を進めるペースの基準（world units/sec）
MK_CPU_STEER_GAIN = 0.6          # 操舵角の正規化係数（小さいほど敏感）
MK_CPU_ACCEL_ANGLE_LIMIT = 1.0   # この角度誤差(rad)を超えたらアクセルを緩める
MK_CPU_SPEED_SCALE_MIN = 0.82    # CPUごとの最高速のばらつき（下限）
MK_CPU_SPEED_SCALE_MAX = 1.00    # CPUごとの最高速のばらつき（上限）
MK_CPU_START_GAP = 120           # グリッドスタートでのカート間隔（後方へ）

# アイテムボックス
MK_ITEM_BOX_COUNT = 4
MK_ITEM_BOX_RADIUS = 60          # 取得判定半径
MK_ITEM_BOX_RESPAWN = 6.0        # 再出現までの秒数

# バナナ
MK_BANANA_HIT_RADIUS = 45
MK_BANANA_LIFETIME = 20.0        # 使われず放置される場合の寿命（秒、安全策）
MK_BANANA_DROP_OFFSET = 70       # カート後方の設置距離

# こうら
MK_SHELL_SPEED = 780.0           # pixels/sec
MK_SHELL_HIT_RADIUS = 40
MK_SHELL_LIFETIME = 4.0          # 秒（何にも当たらなければ消える）
MK_SHELL_SPAWN_OFFSET = 70       # カート前方の発射位置オフセット（自分に当たらないように）

# スピンアウト
MK_STUN_DURATION = 1.4           # 操作不能になる時間（秒）

# CPU のアイテム使用
MK_CPU_ITEM_USE_DELAY_MIN = 0.4
MK_CPU_ITEM_USE_DELAY_MAX = 2.0

# 色
MK_COLOR_CPU = [
    (60, 120, 230),
    (60, 190, 90),
    (230, 170, 40),
]
MK_COLOR_ITEMBOX = (240, 200, 40)
MK_COLOR_BANANA = (235, 210, 40)
MK_COLOR_SHELL = (60, 200, 90)

# ==========================================================================
# ワギャンランド（WAGYAN）設定 — 本作専用。WAGYAN_ 接頭辞で既存定数と衝突を避ける
# ==========================================================================

# ワールド・地形
WAGYAN_WORLD_WIDTH = 3200      # ステージ全体の横幅（px）
WAGYAN_GROUND_Y = 520          # 地面の上面 y（画面座標・縦スクロールなし）
WAGYAN_GOAL_X = 3040           # ゴール（ボス戦への入口）の x 座標

# プレイヤー（ワギャン）
WAGYAN_PLAYER_W = 30
WAGYAN_PLAYER_H = 32
WAGYAN_PLAYER_SPEED = 150       # pixels/sec（左右移動）
WAGYAN_JUMP_POWER = 480         # pixels/sec（ジャンプ初速）
WAGYAN_GRAVITY = 1300           # pixels/sec^2（落下加速度）
WAGYAN_RESPAWN_INVINCIBLE = 1.5  # 復帰後の無敵時間（秒）
WAGYAN_DEATH_TIME = 1.4         # やられ演出の時間（秒）
WAGYAN_START_LIVES = 3

# 音波攻撃（レベル 1〜4 = ワッ・ギャ・ガー・ギャー）
WAGYAN_VOICE_LABELS = ["WA!", "GYA!", "GAA!", "GYAA!"]
WAGYAN_VOICE_RANGE = [130, 170, 210, 260]     # レベルごとの届く距離（px）
WAGYAN_VOICE_STUN = [2.0, 2.6, 3.4, 4.4]      # レベルごとのしびれ時間（秒）
WAGYAN_VOICE_COOLDOWN = 0.35    # 音波の連射間隔（秒）
WAGYAN_VOICE_ACTIVE_TIME = 0.15  # 音波の判定が有効な時間（秒）

# 敵
WAGYAN_ENEMY_W = 30
WAGYAN_ENEMY_H = 26
WAGYAN_ENEMY_SPEED = 50         # pixels/sec（歩行速度）

# スコア
WAGYAN_PARALYZE_SCORE = 150     # 敵をしびれさせた時の得点
WAGYAN_WAGYANIZER_SCORE = 300   # ワギャナイザー取得時の得点
WAGYAN_BOSS_WIN_BONUS = 3000    # ボス戦勝利ボーナス

# 色（ワギャン専用）
WAGYAN_COLOR_SKY = (60, 150, 200)          # 空（水色）
WAGYAN_COLOR_GROUND = (90, 160, 70)        # 地面（草・緑）
WAGYAN_COLOR_GROUND_DARK = (60, 110, 45)   # 地面の土（陰）
WAGYAN_COLOR_PLATFORM = (200, 150, 90)     # 浮遊足場（木）
WAGYAN_COLOR_PLATFORM_DARK = (150, 105, 55)
WAGYAN_COLOR_BODY = (60, 190, 90)          # ワギャンの体（緑）
WAGYAN_COLOR_BODY_DARK = (30, 140, 60)
WAGYAN_COLOR_BELLY = (230, 230, 150)       # ワギャンのお腹（黄緑白）
WAGYAN_COLOR_ENEMY = (200, 70, 90)         # 敵（赤紫）
WAGYAN_COLOR_ENEMY_STUNNED = (150, 150, 170)  # しびれ中（グレー）
WAGYAN_COLOR_WAVE = (255, 220, 60)         # 音波（黄）
WAGYAN_COLOR_WAGYANIZER = (210, 210, 220)  # ワギャナイザー（拡声器・銀）
WAGYAN_COLOR_GOAL = (240, 90, 60)          # ゴール旗

# ボス戦（知恵比べミニゲーム）
WAGYAN_COLOR_BOSS = (110, 60, 150)         # Dr.デビル（紫）
WAGYAN_COLOR_CARD_BACK = (70, 80, 130)     # 神経衰弱：裏面
WAGYAN_COLOR_CARD_FRONT = (235, 235, 245)  # 神経衰弱：表面
WAGYAN_COLOR_CARD_SYMBOLS = [
    (230, 60, 60), (60, 190, 90), (60, 120, 230), (240, 200, 40),
    (230, 120, 200), (60, 200, 200),
]

# ==========================================================================
# ヘビゲーム（SNAKE）設定 — 本作専用。SNAKE_ 接頭辞で既存定数と衝突を避ける
# ==========================================================================

# グリッド・レイアウト
SNAKE_CELL = 20                 # 1 マスの辺（px）
SNAKE_COLS = 40                 # 横マス数（40*20=800）
SNAKE_ROWS = 28                 # 縦マス数（28*20=560）
SNAKE_HUD_HEIGHT = 40           # 上部 HUD 帯の高さ（px、560+40=600）
SNAKE_START_LEN = 3             # 開始時の体長

# スコア・速度
SNAKE_FOOD_SCORE = 10           # エサ 1 個の得点
SNAKE_BASE_INTERVAL = 0.14      # 開始時の移動間隔（秒/マス）
SNAKE_SPEED_STEP = 0.004        # エサ 1 個ごとの短縮量
SNAKE_MIN_INTERVAL = 0.06       # 移動間隔の下限（最高速度）

# 色（SNAKE 専用）
COLOR_SNAKE_HEAD = (90, 230, 110)   # ヘビの頭（明るい緑）
COLOR_SNAKE_BODY = (40, 170, 70)    # ヘビの胴（緑）
COLOR_SNAKE_FOOD = (230, 70, 70)    # エサ（赤）

# ==========================================================================
# ぷよぷよ（PUYO）設定 — 本作専用。PUYO_ 接頭辞で既存定数と衝突を避ける
# ==========================================================================

# 盤面・レイアウト（6列×12行は原作準拠）
PUYO_COLS = 6                  # 盤面の列数
PUYO_ROWS = 12                 # 盤面の行数
PUYO_CELL = 40                 # 1マスの辺（px）→ 240×480px
PUYO_BOARD_X = 60              # 盤面左上 X（右パネル幅を確保するため左寄せ）
PUYO_BOARD_Y = 60              # 盤面左上 Y
PUYO_PANEL_X = 340             # 右サイドパネルの左端 X
PUYO_SPAWN_COL = 2             # 組ぷよの出現列（0始まり＝3列目）

# 落下・演出
PUYO_BASE_FALL = 0.7           # レベル1の落下間隔（秒）
PUYO_FALL_STEP = 0.05          # レベルごとの短縮量
PUYO_MIN_FALL = 0.10           # 落下間隔の下限
PUYO_SOFT_DROP = 0.04          # ソフトドロップ間隔（秒）
PUYO_VANISH_TIME = 0.45        # 消去演出（点滅）の時間（秒）
PUYO_DROP_TIME = 0.18          # 連鎖中の落下演出の時間（秒）
PUYO_LEVEL_POPS = 30           # このぷよ数を消すごとにレベルアップ

# スコア
PUYO_POP_SCORE = 10            # ぷよ1個あたりの基礎点
# 連鎖ボーナス倍率。2連鎖目で一気に跳ね上がるのが原作の手応え。
# テーブル長を超える連鎖は最後の値で頭打ちにする。
PUYO_CHAIN_BONUS = [1, 8, 16, 32, 64, 96, 128, 160]

# 色（PUYO 専用・4色）
COLOR_PUYO_R = (235, 70, 70)     # 赤
COLOR_PUYO_G = (70, 210, 90)     # 緑
COLOR_PUYO_B = (70, 120, 235)    # 青
COLOR_PUYO_Y = (240, 210, 60)    # 黄
COLOR_PUYO_GRID = (38, 38, 52)   # 盤面のグリッド線
COLOR_PUYO_FRAME = (120, 130, 170)  # 盤面の枠
COLOR_PUYO_EYE = (255, 255, 255)    # 目の白目
COLOR_PUYO_PUPIL = (20, 20, 30)     # 目の瞳
