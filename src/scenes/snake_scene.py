"""ヘビゲーム（SNAKE）シーン。移動・エサ取得・衝突判定・スコア・速度上昇を扱う。

ヘビ本体のロジックは game_objects.snake.snake.Snake / game_objects.snake.food.spawn_food
に分離している（pygame 非依存、ヘッドレステスト可能）。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。
"""

import pygame

from scenes.base_scene import BaseScene
from game_objects.snake.snake import Snake
from game_objects.snake.food import spawn_food
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_GRAY,
    SNAKE_CELL, SNAKE_COLS, SNAKE_ROWS, SNAKE_HUD_HEIGHT, SNAKE_START_LEN,
    SNAKE_FOOD_SCORE, SNAKE_BASE_INTERVAL, SNAKE_SPEED_STEP, SNAKE_MIN_INTERVAL,
    COLOR_SNAKE_HEAD, COLOR_SNAKE_BODY, COLOR_SNAKE_FOOD, COLOR_RED,
)


class SnakeScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（DK81/アイスクライマーと同方針）

    def on_enter(self):
        super().on_enter()
        self.font_label = pygame.font.Font(None, 26)
        self.font_value = pygame.font.Font(None, 30)
        self.sound = SoundBank()
        self._reset_game()

    def _reset_game(self):
        self.state = "play"
        self.score = 0
        self.foods_eaten = 0
        self.move_timer = 0.0
        self.move_interval = SNAKE_BASE_INTERVAL

        start_row = SNAKE_ROWS // 2
        start_col = SNAKE_COLS // 3
        cells = [(start_col - i, start_row) for i in range(SNAKE_START_LEN)]
        self.snake = Snake(cells, (1, 0))
        self.food = spawn_food(SNAKE_COLS, SNAKE_ROWS, self.snake.body)

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state != "play":
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.snake.queue_direction(-1, 0)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.snake.queue_direction(1, 0)
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.snake.queue_direction(0, -1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.snake.queue_direction(0, 1)

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        if self.state != "play":
            return

        self.move_timer += dt
        while self.move_timer >= self.move_interval:
            self.move_timer -= self.move_interval
            self._step()
            if self.state != "play":
                break

    def _step(self):
        new_head = self.snake.next_head()
        hx, hy = new_head
        if not (0 <= hx < SNAKE_COLS and 0 <= hy < SNAKE_ROWS):
            self._game_over()
            return

        grew = self.food is not None and new_head == self.food
        if self.snake.hits_self(new_head, grew):
            self._game_over()
            return

        self.snake.advance(new_head, grew)
        if grew:
            self.score += SNAKE_FOOD_SCORE
            self.foods_eaten += 1
            self.move_interval = max(
                SNAKE_MIN_INTERVAL,
                SNAKE_BASE_INTERVAL - self.foods_eaten * SNAKE_SPEED_STEP,
            )
            self.food = spawn_food(SNAKE_COLS, SNAKE_ROWS, self.snake.body)
            self.sound.play_se("score")

    def _game_over(self):
        self.state = "game_over"
        self.sound.play_se("death")
        if self.score > SnakeScene.HIGH_SCORE:
            SnakeScene.HIGH_SCORE = self.score
        self.request_scene("game_over", score=self.score)

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_hud(screen)
        self._draw_food(screen)
        self._draw_snake(screen)

    def _cell_rect(self, col, row):
        return pygame.Rect(
            col * SNAKE_CELL,
            SNAKE_HUD_HEIGHT + row * SNAKE_CELL,
            SNAKE_CELL, SNAKE_CELL,
        )

    def _draw_hud(self, screen):
        pygame.draw.line(screen, COLOR_GRAY, (0, SNAKE_HUD_HEIGHT), (SCREEN_WIDTH, SNAKE_HUD_HEIGHT))

        label = self.font_label.render("SCORE", True, COLOR_GRAY)
        screen.blit(label, (16, 10))
        value = self.font_value.render(f"{self.score:06d}", True, COLOR_WHITE)
        screen.blit(value, (16 + label.get_width() + 10, 8))

        high_label = self.font_label.render("HIGH", True, COLOR_GRAY)
        high_x = 16 + label.get_width() + 10 + value.get_width() + 40
        screen.blit(high_label, (high_x, 10))
        high_value = self.font_value.render(f"{SnakeScene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high_value, (high_x + high_label.get_width() + 10, 8))

        lv_label = self.font_label.render("LV", True, COLOR_GRAY)
        lv_value = self.font_value.render(str(self.foods_eaten), True, COLOR_WHITE)
        lv_x = SCREEN_WIDTH - 16 - lv_value.get_width()
        screen.blit(lv_value, (lv_x, 8))
        screen.blit(lv_label, (lv_x - lv_label.get_width() - 10, 10))

    def _draw_food(self, screen):
        if self.food is None:
            return
        rect = self._cell_rect(*self.food)
        pygame.draw.rect(screen, COLOR_SNAKE_FOOD, rect)

    def _draw_snake(self, screen):
        for i, cell in enumerate(self.snake.body):
            color = COLOR_SNAKE_HEAD if i == 0 else COLOR_SNAKE_BODY
            rect = self._cell_rect(*cell)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLOR_BLACK, rect, 1)
