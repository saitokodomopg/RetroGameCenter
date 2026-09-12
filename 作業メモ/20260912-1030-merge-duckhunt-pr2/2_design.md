# PR #2 マージ — コンフリクト解消方針

7 ファイルすべてが「main 側の追記」と「PR 側の追記」が同じ場所に来たことによる衝突。
**原則は「両方を残す（併記）」**。main 側で後から入ったゲーム（イカジャンプ・マリオカート・
スペースインベーダー等）を絶対に削らないことを最優先とする。

---

## 1. ファイルごとの解消方針

| ファイル | 衝突の中身 | 解消方針 |
|----------|-----------|----------|
| `src/config.py` | 末尾に main=`IKA_` 定数群 / PR=`GUN_` 定数群 | **両方残す**。IKA_ ブロックの後に GUN_ ブロックを続ける |
| `src/main.py` | import 行と register_scene 行 | **両方残す**。IkaJumpScene と DuckHuntScene の両方を import・登録 |
| `src/scenes/menu_thumbnails.py` | import と描画関数、`_DRAWERS` 登録 | **両方残す**。`_draw_ika_jump` と `_draw_duck_hunt` を両方定義し両方登録 |
| `src/utils/synth_audio.py` | `shoot` の定義が衝突（後述） | **main 側を採用**し、PR の銃声は別名で追加 |
| `src/scenes/menu_scene.py` | GAMES リスト（後述） | ユーザー指示に従い DONKEY KONG を外し DUCK HUNT を入れる |
| `設計/concept.md` | Phase 3+ の進捗欄 | main 側の記法を維持しつつ「ダックハント」を追記 |
| `設計/known-issues.md` | No.7 以降の採番が両側でずれている | main 側（No.1〜19）を土台に、PR のダックハント3件を No.20〜22 として採番し直す |

---

## 2. `shoot` SE の名前衝突（要注意点）

main には既にスペースインベーダーの自機弾用 `shoot` がある：

```python
"shoot": ([(900, 300, 0.10)], "square", 0.20),      # main：ピュン（自機弾）
"shoot": ([(1200, 80, 0.05), (400, 60, 0.04)], "square", 0.30),  # PR：パンッ（銃声）
```

同じキーなので、PR 側をそのまま採ると**スペースインベーダーの発射音まで銃声に変わってしまう**。

**方針**：main の `shoot` はそのまま残し、PR の銃声を **`gun_shot`** という別名で追加する。
`duck_hunt_scene.py` の `self.sound.play_se("shoot")` を `play_se("gun_shot")` に変更する。

---

## 3. GAMES リスト（メニュー枠の調整）

ユーザー指示：**DONKEY KONG（先頭）を削除し、その枠に DUCK HUNT を追加する。**

PR 側のリストは 8/29 時点のもので SPACE INVADERS / BREAKOUT / WAGYAN LAND が
`None`（準備中）になっている。これを採ると main で実装済みのゲームが起動不能になるため、
**main 側のリストを土台にして 2 箇所だけ編集する**。

```
(削除) ("DONKEY KONG", "donkey_kong", "donkey_kong"),
(追加) ("DUCK HUNT", "duck_hunt", "duck_hunt"),
```

DUCK HUNT の挿入位置は、削除した DONKEY KONG と同じ**先頭**とはせず、
同系統（近年追加したもの）が並ぶ IKA JUMP の隣に置く。結果：

```
DONKEY KONG '81 / TETRIS / ICE CLIMBER / PAC-MAN
SNAKE / PUYO PUYO / IKA JUMP / DUCK HUNT
SPACE INVADERS / BREAKOUT / WAGYAN LAND / PINBALL
MARIO KART
```

13 件のままなので `COLS=4` × 3 行 + 最終行 1 件（中央寄せ）の既存レイアウトが
そのまま成立し、**グリッド定数の変更は不要**。4 行目も発生しない。

`donkey_kong_scene.py` とサムネイル `_draw_donkey_kong` は削除しない
（メニューから外すだけ。シーン登録も main.py に残す＝害がなく、復活も容易）。

---

## 4. 取り込まないもの

- `tmp/yoshida.md`（「コミットの練習」コミットの残骸。1 行だけの無意味なファイル）
  → マージ後に削除してからコミットする

---

## 5. 影響範囲

| 変更 | リスク | 確認方法 |
|------|--------|----------|
| `GUN_` 定数追記 | なし（接頭辞で衝突回避） | import エラーが出ないこと |
| `gun_shot` SE 追加 | なし（追加のみ）。既存 `shoot` は不変 | スペースインベーダーの発射音が変わっていないこと |
| GAMES から DONKEY KONG 削除 | 低。選択インデックスは実行時に決まるため副作用なし | メニューに 13 枚並び 4 行目が出ないこと |
| DuckHuntScene 登録 | なし（追加のみ） | 他ゲームが従来どおり起動すること |

---

## 6. 検証方法

1. 起動して**メニューを目視**：カード 13 枚・DONKEY KONG が無い・DUCK HUNT がある・
   画面内に収まっている
2. **DUCK HUNT を実プレイ**：的が出る／撃って当たる／命中演出／外すと残弾が減る／
   ラウンドクリア／ゲームオーバー／R リスタート／ESC でメニュー復帰
3. **既存ゲームの回帰確認**：イカジャンプ・マリオカート・スペースインベーダーが起動し、
   特にスペースインベーダーの**発射音が従来どおり**であること
4. 全シーンの import・登録が通ることをヘッドレスでも確認（起動時例外の早期検出）
