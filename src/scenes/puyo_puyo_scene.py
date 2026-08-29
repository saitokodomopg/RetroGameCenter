"""ぷよぷよシーン。落下・回転・連鎖・スコア・ゲームオーバーを扱う。

盤面ロジックは game_objects.puyo.PuyoBoard / PuyoPair に分離している。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。

状態機械:
    play  --着地--> vanish --> drop --連鎖あり--> vanish (ループ)
                                    --連鎖なし--> play (次の組ぷよ)
    play  --出現できない--> over
vanish / drop の間は連鎖アニメーション中のため入力を受け付けない。
"""

import random
import pygame
from scenes.base_scene import BaseScene
from game_objects.puyo.puyo_board import PuyoBoard
from game_objects.puyo.puyo_pair import PuyoPair, KINDS, COLORS
from utils.synth_audio import SoundBank
from config import (
    SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_GRAY,
    COLOR_RED, COLOR_YELLOW,
    PUYO_COLS, PUYO_ROWS, PUYO_CELL, PUYO_BOARD_X, PUYO_BOARD_Y,
    PUYO_PANEL_X, PUYO_SPAWN_COL,
    PUYO_BASE_FALL, PUYO_FALL_STEP, PUYO_MIN_FALL, PUYO_SOFT_DROP,
    PUYO_VANISH_TIME, PUYO_DROP_TIME, PUYO_LEVEL_POPS,
    COLOR_PUYO_GRID, COLOR_PUYO_FRAME, COLOR_PUYO_EYE, COLOR_PUYO_PUPIL,
)

# 画面内に常時掲載する操作説明
CONTROLS = [
    "<- -> : MOVE",
    "v (HOLD): DROP",
    "X : ROTATE R",
    "Z : ROTATE L",
    "R : RESTART",
    "ESC : MENU",
]


class PuyoPuyoScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_big = pygame.font.Font(None, 64)
        self.font_mid = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        self.font_label = pygame.font.Font(None, 26)
        self.font_hint = pygame.font.Font(None, 22)
        self.sound = SoundBank()
        self._reset_game()

    def _reset_game(self):
        self.board = PuyoBoard(PUYO_COLS, PUYO_ROWS)
        self.state = "play"
        self.score = 0
        self.chain = 0          # 現在の連鎖数（0 = 連鎖していない）
        self.max_chain = 0
        self.total_popped = 0
        self.level = 1
        self.fall_timer = 0.0
        self.fall_interval = self._calc_fall_interval()
        self.soft_drop_timer = 0.0
        self.anim_timer = 0.0
        self.time = 0.0
        self.vanishing = []     # 消去演出中のセル [(cx, cy), ...]
        # NEXT キュー：[次, その次] の2手先を常に保持する
        self.next_queue = [self._random_pair(), self._random_pair()]
        self.current = None
        self._spawn_pair()

    def _random_pair(self):
        """色をランダムに決めた組ぷよを作る（位置は出現時に設定）。"""
        return PuyoPair(random.choice(KINDS), random.choice(KINDS),
                        PUYO_SPAWN_COL, 0, rot=0)

    def _calc_fall_interval(self):
        return max(PUYO_MIN_FALL,
                   PUYO_BASE_FALL - (self.level - 1) * PUYO_FALL_STEP)

    def _spawn_pair(self):
        """NEXT の先頭を現在の組ぷよにし、キューを補充する。置けなければゲームオーバー。"""
        pair = self.next_queue.pop(0)
        self.next_queue.append(self._random_pair())
        pair.x = PUYO_SPAWN_COL
        pair.y = 0
        pair.rot = 0
        self.current = pair
        self.fall_timer = 0.0
        self.soft_drop_timer = 0.0
        self.anim_timer = 0.0
        # 連鎖アニメーション（vanish / drop）から呼ばれた場合もここで操作可能に戻す
        self.state = "play"
        # 出現位置に置けない＝積み上がってゲームオーバー
        if not self.board.is_valid(pair.cells()):
            self.current = None
            self.state = "over"
            self.sound.play_se("death")

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "over":
            if event.key in (pygame.K_r, pygame.K_RETURN):
                self._reset_game()
            return

        # 連鎖アニメーション中（vanish / drop）は操作を受け付けない
        if self.state != "play":
            return

        if event.key == pygame.K_LEFT:
            if self._try_move(-1, 0):
                self.sound.play_se("move")
        elif event.key == pygame.K_RIGHT:
            if self._try_move(1, 0):
                self.sound.play_se("move")
        elif event.key == pygame.K_DOWN:
            # 押した瞬間に1マス落として即応させる。継続は update が担当。
            if self._try_move(0, 1):
                self.score += 1  # ソフトドロップ加点
                self.fall_timer = 0.0
                self.soft_drop_timer = 0.0
        elif event.key == pygame.K_x:
            if self._try_rotate(1):   # 右回転
                self.sound.play_se("rotate")
        elif event.key == pygame.K_z:
            if self._try_rotate(-1):  # 左回転
                self.sound.play_se("rotate")

    def _try_move(self, dx, dy):
        pair = self.current
        if pair is None:
            return False
        cells = pair.cells(x=pair.x + dx, y=pair.y + dy)
        if self.board.is_valid(cells):
            pair.x += dx
            pair.y += dy
            return True
        return False

    def _try_rotate(self, direction=1):
        """回転する。壁・ぷよに当たる場合は軸を1マスずらして成立させる（壁蹴り）。"""
        pair = self.current
        if pair is None:
            return False
        new_rot = pair.next_rotation(direction)
        # その場 → 子ぷよの反対方向へ軸を1マス押す（壁蹴り）→ 逆側、の順に試す。
        # 子が左右に来る回転で壁際に立っている場合、軸を押し戻せば成立する。
        child_dx = pair.child_cell(rot=new_rot)[0] - pair.x
        kicks = [0]
        for dx in (-child_dx, 1, -1):
            if dx and dx not in kicks:
                kicks.append(dx)
        for dx in kicks:
            cells = pair.cells(rot=new_rot, x=pair.x + dx)
            if self.board.is_valid(cells):
                pair.rot = new_rot
                pair.x += dx
                return True
        return False

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if self.state == "play":
            self._update_play(dt)
        elif self.state == "vanish":
            self._update_vanish(dt)
        elif self.state == "drop":
            self._update_drop(dt)

    def _update_play(self, dt):
        # ソフトドロップ：下キーを押している間、一定間隔で落下し続ける
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            self.soft_drop_timer += dt
            while self.soft_drop_timer >= PUYO_SOFT_DROP:
                self.soft_drop_timer -= PUYO_SOFT_DROP
                if self._try_move(0, 1):
                    self.score += 1
                    self.fall_timer = 0.0
                else:
                    break
        else:
            self.soft_drop_timer = 0.0

        self.fall_timer += dt
        if self.fall_timer >= self.fall_interval:
            self.fall_timer -= self.fall_interval
            if not self._try_move(0, 1):
                self._lock_pair()

    def _lock_pair(self):
        """組ぷよを盤面に固定し、ちぎり落下のあと連鎖判定へ入る。"""
        self.board.lock(self.current.colored_cells())
        self.current = None
        self.sound.play_se("lock")
        # 軸と子が別々に落ちる（ちぎり）
        self.board.apply_gravity()
        self.chain = 0
        if not self._start_vanish_if_any():
            self._spawn_pair()

    def _start_vanish_if_any(self):
        """消えるグループがあれば vanish 状態に入る。入ったら True。"""
        groups = self.board.find_groups()
        if not groups:
            return False
        self.chain += 1
        self.max_chain = max(self.max_chain, self.chain)
        self.vanishing = [cell for group in groups for cell in group]
        self.anim_timer = 0.0
        self.state = "vanish"
        return True

    def _update_vanish(self, dt):
        self.anim_timer += dt
        if self.anim_timer < PUYO_VANISH_TIME:
            return
        # 演出終了 → 実際に消して加点
        groups = self.board.find_groups()
        popped = self.board.pop_groups(groups)
        self.score += PuyoBoard.chain_score(popped, self.chain)
        self.total_popped += popped
        prev_level = self.level
        self.level = self.total_popped // PUYO_LEVEL_POPS + 1
        if self.level != prev_level:
            self.fall_interval = self._calc_fall_interval()
        # 1連鎖は控えめな音、2連鎖以上は派手な音
        self.sound.play_se("levelup" if self.chain >= 2 else "line")
        self.vanishing = []
        self.anim_timer = 0.0
        self.state = "drop"

    def _update_drop(self, dt):
        self.anim_timer += dt
        if self.anim_timer < PUYO_DROP_TIME:
            return
        self.board.apply_gravity()
        # 落下の結果また揃えば連鎖継続、揃わなければ次の組ぷよ
        if not self._start_vanish_if_any():
            self.chain = 0
            self._spawn_pair()

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_board(screen)
        self._draw_locked(screen)
        if self.current is not None and self.state == "play":
            self._draw_current(screen)
        self._draw_side_panel(screen)
        if self.state == "over":
            self._draw_game_over(screen)

    def _cell_rect(self, col, row):
        return pygame.Rect(
            PUYO_BOARD_X + col * PUYO_CELL,
            PUYO_BOARD_Y + row * PUYO_CELL,
            PUYO_CELL, PUYO_CELL,
        )

    def _draw_puyo(self, screen, rect, color, eyes=True):
        """ぷよ1個を円で描く。光沢と目を入れて「ぷよらしさ」を出す。"""
        cx, cy = rect.center
        radius = rect.width // 2 - 2
        pygame.draw.circle(screen, color, (cx, cy), radius)
        # 縁取り（暗い色）
        dark = tuple(max(0, c - 70) for c in color)
        pygame.draw.circle(screen, dark, (cx, cy), radius, 2)
        # 左上の光沢
        light = tuple(min(255, c + 70) for c in color)
        pygame.draw.circle(screen, light,
                           (cx - radius // 3, cy - radius // 3),
                           max(2, radius // 4))
        if not eyes:
            return
        # 目（白目＋瞳）。これがあるだけでぷよぷよらしくなる。
        eye_r = max(3, radius // 4)
        pupil_r = max(1, eye_r // 2)
        for sx in (-1, 1):
            ex = cx + sx * (radius // 3)
            ey = cy - radius // 8
            pygame.draw.circle(screen, COLOR_PUYO_EYE, (ex, ey), eye_r)
            pygame.draw.circle(screen, COLOR_PUYO_PUPIL, (ex, ey), pupil_r)

    def _draw_board(self, screen):
        w = PUYO_COLS * PUYO_CELL
        h = PUYO_ROWS * PUYO_CELL
        for c in range(PUYO_COLS + 1):
            x = PUYO_BOARD_X + c * PUYO_CELL
            pygame.draw.line(screen, COLOR_PUYO_GRID,
                             (x, PUYO_BOARD_Y), (x, PUYO_BOARD_Y + h))
        for r in range(PUYO_ROWS + 1):
            y = PUYO_BOARD_Y + r * PUYO_CELL
            pygame.draw.line(screen, COLOR_PUYO_GRID,
                             (PUYO_BOARD_X, y), (PUYO_BOARD_X + w, y))
        pygame.draw.rect(screen, COLOR_PUYO_FRAME,
                         (PUYO_BOARD_X - 3, PUYO_BOARD_Y - 3, w + 6, h + 6), 3)

    def _draw_locked(self, screen):
        # 消去演出中は該当ぷよを点滅させる
        blink_hidden = (self.state == "vanish" and int(self.time * 20) % 2 == 0)
        for r in range(PUYO_ROWS):
            for c in range(PUYO_COLS):
                kind = self.board.grid[r][c]
                if kind is None:
                    continue
                if blink_hidden and (c, r) in self.vanishing:
                    continue
                self._draw_puyo(screen, self._cell_rect(c, r), COLORS[kind])

    def _draw_current(self, screen):
        for ((cx, cy), kind) in self.current.colored_cells():
            if cy >= 0:
                self._draw_puyo(screen, self._cell_rect(cx, cy), COLORS[kind])

    def _draw_side_panel(self, screen):
        px = PUYO_PANEL_X
        y = PUYO_BOARD_Y

        # NEXT（次）
        label = self.font_label.render("NEXT", True, COLOR_WHITE)
        screen.blit(label, (px, y))
        self._draw_next_pair(screen, self.next_queue[0], px, y + 26, PUYO_CELL)
        y += 26 + PUYO_CELL * 2 + 14

        # NEXT2（その次）— 小さめに描いて優先度の差を示す
        label2 = self.font_hint.render("NEXT2", True, COLOR_GRAY)
        screen.blit(label2, (px, y))
        self._draw_next_pair(screen, self.next_queue[1], px, y + 22, 28)
        y += 22 + 28 * 2 + 16

        # スコア
        t = self.font_label.render("SCORE", True, COLOR_GRAY)
        screen.blit(t, (px, y))
        v = self.font_mid.render(f"{self.score:06d}", True, COLOR_YELLOW)
        screen.blit(v, (px, y + 22))
        y += 66

        # 連鎖表示（連鎖中のみ）
        if self.chain >= 1 and self.state in ("vanish", "drop"):
            ct = self.font_mid.render(f"{self.chain} CHAIN!", True, COLOR_RED)
            screen.blit(ct, (px, y))
        y += 44

        # 操作説明（画面内に常時掲載）。下端から逆算して配置する。
        cy = SCREEN_HEIGHT - 18 - len(CONTROLS) * 22
        title = self.font_label.render("CONTROLS", True, COLOR_WHITE)
        screen.blit(title, (px, cy - 26))
        for line in CONTROLS:
            t = self.font_hint.render(line, True, COLOR_GRAY)
            screen.blit(t, (px, cy))
            cy += 22

    def _draw_next_pair(self, screen, pair, px, py, cell):
        """NEXT 表示。子ぷよが上、軸ぷよが下になるよう縦に並べて描く。"""
        for i, kind in enumerate((pair.child_kind, pair.axis_kind)):
            rect = pygame.Rect(px, py + i * cell, cell, cell)
            self._draw_puyo(screen, rect, COLORS[kind])

    def _draw_game_over(self, screen):
        w = PUYO_COLS * PUYO_CELL
        h = PUYO_ROWS * PUYO_CELL
        cx = PUYO_BOARD_X + w // 2
        cy = PUYO_BOARD_Y + h // 2
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (PUYO_BOARD_X, PUYO_BOARD_Y))

        # 盤面幅（240px）に収まるフォントを選ぶ。font_big のままでは左右にはみ出す。
        title = self.font_mid.render("GAME OVER", True, COLOR_RED)
        if title.get_width() > w - 12:
            title = self.font_small.render("GAME OVER", True, COLOR_RED)
        screen.blit(title, title.get_rect(center=(cx, cy - 40)))
        mc = self.font_small.render(f"MAX CHAIN: {self.max_chain}", True, COLOR_WHITE)
        screen.blit(mc, mc.get_rect(center=(cx, cy + 6)))
        if int(self.time * 2) % 2 == 0:
            # 1行だと盤面幅に収まらないため2行に分ける
            for i, line in enumerate(("R: RESTART", "ESC: MENU")):
                info = self.font_hint.render(line, True, COLOR_WHITE)
                screen.blit(info, info.get_rect(center=(cx, cy + 44 + i * 22)))
