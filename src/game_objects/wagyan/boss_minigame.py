"""ボス（Dr.デビル）との知恵比べミニゲーム。

原作のボス戦は「アクションで倒す」のではなく知恵比べで決着をつける。
今回は次の2種を実装し、ボス戦に入るたびランダムでどちらか一方が選ばれる：

  - ConcentrationGame（神経衰弱）: カードをめくって同じ絵柄のペアを揃える。
    既定ペア数（盤面の半分）を多く取った側が勝ち。
  - ShiritoriGame（しりとり）: 候補（3択）からしりとりが繋がる単語を選ぶ。
    自由入力は行わず、キーボードでの選択式にして判定を単純化している。
    途中で無効な単語を選ぶと即負け。最後まで正解し続けたらプレイヤーの勝ち。

どちらも scene からは同じインターフェースで扱える：
  update(dt) / draw(screen) / handle_key(key) / finished / winner("player"|"boss")
"""

import pygame

from config import (
    SCREEN_WIDTH, COLOR_WHITE, COLOR_YELLOW,
    WAGYAN_COLOR_CARD_BACK, WAGYAN_COLOR_CARD_FRONT, WAGYAN_COLOR_CARD_SYMBOLS,
)

# --- 神経衰弱 ---------------------------------------------------------

GRID_COLS = 4
GRID_ROWS = 3
N_PAIRS = (GRID_COLS * GRID_ROWS) // 2
RESOLVE_DELAY = 0.9      # 2枚めくった後、一致/不一致を見せてから次に進むまでの待ち
CPU_THINK_TIME = 0.6     # ボスが1枚めくるまでの「考える」時間
CPU_MEMORY_RECALL_CHANCE = 0.65  # ボスが記憶を頼りにペアを狙う確率

CARD_W, CARD_H = 100, 70
CARD_GAP = 12
GRID_LEFT = (SCREEN_WIDTH - (GRID_COLS * CARD_W + (GRID_COLS - 1) * CARD_GAP)) // 2
GRID_TOP = 190


class ConcentrationGame:
    def __init__(self, rng):
        self.rng = rng
        self.cards = self._build_cards()
        self.cursor = 0
        self.selected = []
        self.turn = "player"
        self.phase = "player_turn"
        self.timer = 0.0
        self.player_pairs = 0
        self.boss_pairs = 0
        self.cpu_memory = {}
        self.finished = False
        self.winner = None
        self.message = "YOUR TURN"
        self.message_timer = 1.0
        self._pending = None
        self.font = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 22)

    def _build_cards(self):
        symbols = list(range(N_PAIRS)) * 2
        self.rng.shuffle(symbols)
        return [{"symbol": s, "revealed": False, "matched": False} for s in symbols]

    # --- 入力 -----------------------------------------------------------
    def handle_key(self, key):
        if key == pygame.K_LEFT:
            self.move_cursor(-1, 0)
        elif key == pygame.K_RIGHT:
            self.move_cursor(1, 0)
        elif key == pygame.K_UP:
            self.move_cursor(0, -1)
        elif key == pygame.K_DOWN:
            self.move_cursor(0, 1)
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.confirm()

    def move_cursor(self, dx, dy):
        if self.phase != "player_turn":
            return
        row, col = divmod(self.cursor, GRID_COLS)
        row = max(0, min(GRID_ROWS - 1, row + dy))
        col = max(0, min(GRID_COLS - 1, col + dx))
        self.cursor = row * GRID_COLS + col

    def confirm(self):
        if self.phase != "player_turn" or self.finished:
            return
        self._flip(self.cursor, by="player")

    # --- ロジック ---------------------------------------------------------
    def _flip(self, idx, by):
        card = self.cards[idx]
        if card["revealed"] or card["matched"]:
            return
        card["revealed"] = True
        self.cpu_memory[idx] = card["symbol"]
        self.selected.append(idx)
        if len(self.selected) == 2:
            self._resolve_pair(by)

    def _resolve_pair(self, by):
        i0, i1 = self.selected
        if self.cards[i0]["symbol"] == self.cards[i1]["symbol"]:
            self.cards[i0]["matched"] = True
            self.cards[i1]["matched"] = True
            if by == "player":
                self.player_pairs += 1
            else:
                self.boss_pairs += 1
            self._pending = "match"
            self.message = "MATCH!"
        else:
            self._pending = "mismatch"
            self.message = "..."
        self.message_timer = 1.0
        self.phase = "resolve_wait"
        self.timer = RESOLVE_DELAY

    def update(self, dt):
        if self.finished:
            return
        if self.message_timer > 0:
            self.message_timer -= dt

        if self.phase == "resolve_wait":
            self.timer -= dt
            if self.timer <= 0:
                self._finish_resolve()
            return

        if self.phase == "boss_wait":
            self.timer -= dt
            if self.timer <= 0:
                self._boss_take_turn_step()

    def _finish_resolve(self):
        if self._pending == "mismatch":
            for idx in self.selected:
                self.cards[idx]["revealed"] = False
            self.turn = "boss" if self.turn == "player" else "player"
        self.selected = []

        if all(c["matched"] for c in self.cards):
            self._finish_game()
            return

        if self.turn == "player":
            self.phase = "player_turn"
            self.message = "YOUR TURN"
            self.message_timer = 1.0
        else:
            self.phase = "boss_wait"
            self.timer = CPU_THINK_TIME
            self.message = "BOSS'S TURN"
            self.message_timer = 1.0

    def _boss_take_turn_step(self):
        idx = self._boss_pick_card()
        if idx is None:
            self.turn = "player"
            self.phase = "player_turn"
            return
        self._flip(idx, by="boss")
        if len(self.selected) == 1:
            self.phase = "boss_wait"
            self.timer = CPU_THINK_TIME * 0.8

    def _boss_pick_card(self):
        available = [i for i, c in enumerate(self.cards)
                     if not c["matched"] and not c["revealed"]]
        if not available:
            return None
        if self.rng.random() < CPU_MEMORY_RECALL_CHANCE:
            known = {i: s for i, s in self.cpu_memory.items() if i in available}
            by_symbol = {}
            for i, s in known.items():
                by_symbol.setdefault(s, []).append(i)
            if self.selected:
                first_symbol = self.cards[self.selected[0]]["symbol"]
                if first_symbol in by_symbol:
                    return by_symbol[first_symbol][0]
            pair_ready = [s for s, idxs in by_symbol.items() if len(idxs) >= 2]
            if pair_ready:
                s = self.rng.choice(pair_ready)
                return by_symbol[s][0]
        return self.rng.choice(available)

    def _finish_game(self):
        self.finished = True
        self.winner = "player" if self.player_pairs > self.boss_pairs else "boss"

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        title = self.font.render("MEMORY MATCH", True, COLOR_YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        for i, card in enumerate(self.cards):
            row, col = divmod(i, GRID_COLS)
            x = GRID_LEFT + col * (CARD_W + CARD_GAP)
            y = GRID_TOP + row * (CARD_H + CARD_GAP)
            rect = pygame.Rect(x, y, CARD_W, CARD_H)
            if card["matched"]:
                color = WAGYAN_COLOR_CARD_SYMBOLS[card["symbol"]]
                pygame.draw.rect(screen, color, rect, border_radius=6)
                pygame.draw.rect(screen, COLOR_WHITE, rect, 2, border_radius=6)
            elif card["revealed"]:
                pygame.draw.rect(screen, WAGYAN_COLOR_CARD_FRONT, rect, border_radius=6)
                color = WAGYAN_COLOR_CARD_SYMBOLS[card["symbol"]]
                pygame.draw.circle(screen, color, rect.center, 22)
            else:
                pygame.draw.rect(screen, WAGYAN_COLOR_CARD_BACK, rect, border_radius=6)
                pygame.draw.rect(screen, (30, 30, 50), rect, 2, border_radius=6)

            if self.phase == "player_turn" and i == self.cursor:
                pygame.draw.rect(screen, COLOR_YELLOW, rect, 3, border_radius=6)

        score = self.font_small.render(
            f"YOU {self.player_pairs} - {self.boss_pairs} BOSS", True, COLOR_WHITE)
        screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, GRID_TOP - 22)))

        if self.message_timer > 0:
            msg = self.font_small.render(self.message, True, COLOR_YELLOW)
            screen.blit(msg, msg.get_rect(
                center=(SCREEN_WIDTH // 2, GRID_TOP + GRID_ROWS * (CARD_H + CARD_GAP) + 14)))


# --- しりとり ---------------------------------------------------------

START_WORD = "しりとり"
STEPS = [
    {"turn": "player", "options": [("たぬき", False), ("りんご", True), ("みかん", False)]},
    {"turn": "boss", "options": [("ゴリラ", True), ("さくら", False), ("とけい", False)]},
    {"turn": "player", "options": [("いぬ", False), ("ラッパ", True), ("ねこ", False)]},
    {"turn": "boss", "options": [("くも", False), ("パイナップル", True), ("ほし", False)]},
    {"turn": "player", "options": [("たいこ", False), ("ルーレット", True), ("かめ", False)]},
    {"turn": "boss", "options": [("いか", False), ("トマト", True), ("うま", False)]},
]
BOSS_MISTAKE_CHANCE = 0.25
BOSS_THINK_TIME = 1.0


class ShiritoriGame:
    def __init__(self, rng):
        self.rng = rng
        self.shuffled_options = []
        for step in STEPS:
            opts = list(step["options"])
            rng.shuffle(opts)
            self.shuffled_options.append(opts)
        self.index = 0
        self.cursor = 0
        self.current_word = START_WORD
        self.finished = False
        self.winner = None
        first_turn = STEPS[0]["turn"]
        self.phase = "player_turn" if first_turn == "player" else "boss_wait"
        self.timer = 0.0 if first_turn == "player" else BOSS_THINK_TIME
        self.message = "YOUR TURN" if first_turn == "player" else "BOSS'S TURN"
        self.message_timer = 1.0
        self.font = pygame.font.Font(None, 34)
        self.font_small = pygame.font.Font(None, 24)

    # --- 入力 -----------------------------------------------------------
    def handle_key(self, key):
        if key == pygame.K_UP:
            self.move_cursor(-1)
        elif key == pygame.K_DOWN:
            self.move_cursor(1)
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.confirm()

    def move_cursor(self, dy):
        if self.phase != "player_turn":
            return
        n = len(self.shuffled_options[self.index])
        self.cursor = (self.cursor + dy) % n

    def confirm(self):
        if self.phase != "player_turn" or self.finished:
            return
        text, valid = self.shuffled_options[self.index][self.cursor]
        self._resolve(valid, text, by="player")

    # --- ロジック ---------------------------------------------------------
    def update(self, dt):
        if self.finished:
            return
        if self.message_timer > 0:
            self.message_timer -= dt
        if self.phase == "boss_wait":
            self.timer -= dt
            if self.timer <= 0:
                self._boss_move()

    def _boss_move(self):
        opts = self.shuffled_options[self.index]
        correct = next(i for i, (t, v) in enumerate(opts) if v)
        if self.rng.random() < BOSS_MISTAKE_CHANCE:
            pick = self.rng.choice([i for i in range(len(opts)) if i != correct])
        else:
            pick = correct
        text, valid = opts[pick]
        self._resolve(valid, text, by="boss")

    def _resolve(self, valid, text, by):
        if not valid:
            self.finished = True
            self.winner = "boss" if by == "player" else "player"
            self.message = f"{text}... IS WRONG!"
            self.message_timer = 2.0
            return

        self.current_word = text
        self.message = text
        self.message_timer = 1.0
        self.index += 1
        if self.index >= len(STEPS):
            self.finished = True
            self.winner = "player"
            return

        self.cursor = 0
        next_turn = STEPS[self.index]["turn"]
        if next_turn == "player":
            self.phase = "player_turn"
        else:
            self.phase = "boss_wait"
            self.timer = BOSS_THINK_TIME

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        title = self.font.render("SHIRITORI SHOWDOWN", True, COLOR_YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        word = self.font.render(self.current_word, True, COLOR_WHITE)
        screen.blit(word, word.get_rect(center=(SCREEN_WIDTH // 2, 210)))

        turn_label = "YOUR TURN" if self.phase == "player_turn" else "BOSS IS THINKING..."
        turn_surf = self.font_small.render(turn_label, True, COLOR_WHITE)
        screen.blit(turn_surf, turn_surf.get_rect(center=(SCREEN_WIDTH // 2, 250)))

        opts = self.shuffled_options[self.index] if self.index < len(STEPS) else []
        for i, (text, _valid) in enumerate(opts):
            y = 300 + i * 46
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, y, 280, 36)
            pygame.draw.rect(screen, (40, 40, 70), rect, border_radius=6)
            if self.phase == "player_turn" and i == self.cursor:
                pygame.draw.rect(screen, COLOR_YELLOW, rect, 3, border_radius=6)
            label = self.font_small.render(text, True, COLOR_WHITE)
            screen.blit(label, label.get_rect(center=rect.center))

        if self.message_timer > 0 and self.finished:
            msg = self.font.render(self.message, True, COLOR_YELLOW)
            screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 470)))


def create_random_minigame(rng):
    """ボス戦に入るたびランダムでどちらかのミニゲームを生成する。"""
    kind = rng.choice(["concentration", "shiritori"])
    if kind == "concentration":
        return ConcentrationGame(rng)
    return ShiritoriGame(rng)
