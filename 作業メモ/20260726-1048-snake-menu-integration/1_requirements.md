# ヘビゲーム（SNAKE）— メニュー統合

## 今回やること

前回の作業メモ（`20260726-1010-add-snake`）で実装した `SnakeScene`
（`src/scenes/snake_scene.py`）を、メニューから実際に選んで遊べるようにする。

確認したところ、メニュー側の準備（カード表示・サムネイル）は既に完了していた：

- `src/scenes/menu_scene.py` の `GAMES` に `("SNAKE", None, "snake")` が既にあり、
  サムネイルキー `"snake"` も指定済み（現状はシーンキーが `None` のため「COMING SOON」表示）
- `src/scenes/menu_thumbnails.py` に `_draw_snake` サムネイル描画も実装済み

そのため今回のスコープは非常に小さく、以下の「配線」のみで完了する：

1. `src/main.py` に `SnakeScene` を import し、`register_scene("snake", SnakeScene())` する
2. `src/scenes/menu_scene.py` の `GAMES` の該当行を
   `("SNAKE", None, "snake")` → `("SNAKE", "snake", "snake")` に変更する

## 受け入れ条件

- [x] メニューの SNAKE カードが「COMING SOON」ではなく通常のプレイ可能カードとして表示される
- [x] メニューで SNAKE カードを選択して Enter/Space で `SnakeScene` が開始する
- [x] プレイ中、矢印キー／WASD で操作でき、エサ取得・壁/自己衝突が機能する
- [x] ESC でメニューへ戻れる（`main.py` の既存グローバル処理を利用、追加実装不要）
- [x] ゲームオーバー後、`GameOverScene` → Enter/Space でメニューに戻り、再度 SNAKE を選べる
- [x] 既存の他ゲーム（DK・DK81・テトリス・アイスクライマー）の起動・メニュー表示に影響がない

## やらないこと（スコープ外）

- `SnakeScene` 自体のゲームロジック変更（前回の作業メモの実装をそのまま使う）
- サムネイル・カード表示の見た目調整（既存のものをそのまま使う）

## 変更ファイル

- 変更 `src/main.py` — import 1行 ＋ `register_scene("snake", ...)` 1行
- 変更 `src/scenes/menu_scene.py` — `GAMES` のシーンキーを `None` → `"snake"`

## タスクリスト

- [x] `main.py` に `SnakeScene` を登録
- [x] `menu_scene.py` の `GAMES` のシーンキーを更新
- [x] `python src/main.py` 相当の起動確認（ヘッドレス）：メニュー→SNAKE選択→プレイ→ゲームオーバー→メニュー、の一連の遷移を確認
