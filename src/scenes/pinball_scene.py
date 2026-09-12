"""ピンボールシーン。プランジャー発射・フリッパー操作・盤面判定・残機管理を扱う。

盤面のジオメトリと衝突解決は game_objects.pinball.table.Table
（pygame 非依存、ヘッドレステスト可能）に分離している。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。
"""

import pygame

from scenes.base_scene import BaseScene
from game_objects.pinball.ball import Ball
from game_objects.pinball.table import Table
from utils.synth_audio import SoundBank
from config import (
    COLOR_BLACK, COLOR_WHITE, COLOR_GRAY, COLOR_YELLOW,
    PINBALL_BOARD_X, PINBALL_BOARD_Y, PINBALL_BOARD_W, PINBALL_BOARD_H,
    PINBALL_BALL_RADIUS, PINBALL_MAX_SPEED,
    PINBALL_LAUNCH_MIN_SPEED, PINBALL_LAUNCH_MAX_SPEED, PINBALL_LAUNCH_CHARGE_TIME,
    PINBALL_START_BALLS, PINBALL_COLOR_BG, PINBALL_COLOR_WALL, PINBALL_COLOR_BALL,
    PINBALL_COLOR_FLIPPER, PINBALL_COLOR_BUMPER, PINBALL_COLOR_BUMPER_HIT,
    PINBALL_COLOR_SLINGSHOT, PINBALL_BUMPER_COOLDOWN, PINBALL_SLINGSHOT_COOLDOWN,
    PINBALL_COLOR_LANE_BG,
)

_EVENT_SE = {"bumper": "stomp", "slingshot": "invader_hit"}


class PinballScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（他ゲームと同方針）

    def on_enter(self):
        super().on_enter()
        self.font_label = pygame.font.Font(None, 26)
        self.font_value = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 22)
        self.sound = SoundBank()
        self._reset_game()

    def _reset_game(self):
        self.table = Table()
        self.ball = Ball(*self.table.plunger_rest, PINBALL_BALL_RADIUS, PINBALL_MAX_SPEED)
        self.state = "ready"
        self.score = 0
        self.balls_left = PINBALL_START_BALLS
        self.charging = False
        self.charge = 0.0
        self.prev_left = False
        self.prev_right = False

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        pass

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        keys = pygame.key.get_pressed()
        left_pressed = keys[pygame.K_LEFT]
        right_pressed = keys[pygame.K_RIGHT]
        self.table.set_flipper_input(left_pressed, right_pressed)

        if left_pressed and not self.prev_left:
            self.sound.play_se("move")
        if right_pressed and not self.prev_right:
            self.sound.play_se("move")
        self.prev_left = left_pressed
        self.prev_right = right_pressed

        if self.state == "ready":
            self._update_launch_charge(dt, keys)

        events = self.table.update(self.ball, dt)
        for kind, points in events:
            self.score += points
            self.sound.play_se(_EVENT_SE.get(kind, "score"))

        if self.state == "play":
            if self.table.is_drained(self.ball):
                self._handle_drain()
            elif self.table.is_settled_in_lane(self.ball):
                # 打ち上げが弱くレーンへ戻ってきた場合は、ミス扱いにせず再発射させる
                self.ball.stop()
                self.state = "ready"

    def _update_launch_charge(self, dt, keys):
        if keys[pygame.K_DOWN]:
            self.charging = True
            self.charge = min(PINBALL_LAUNCH_CHARGE_TIME, self.charge + dt)
        elif self.charging:
            ratio = self.charge / PINBALL_LAUNCH_CHARGE_TIME
            speed = PINBALL_LAUNCH_MIN_SPEED + (
                PINBALL_LAUNCH_MAX_SPEED - PINBALL_LAUNCH_MIN_SPEED) * ratio
            self.ball.vx = 0.0
            self.ball.vy = -speed
            self.charging = False
            self.charge = 0.0
            self.state = "play"
            self.sound.play_se("shoot")

    def _handle_drain(self):
        self.balls_left -= 1
        self.sound.play_se("death")
        if self.balls_left <= 0:
            if self.score > PinballScene.HIGH_SCORE:
                PinballScene.HIGH_SCORE = self.score
            self.request_scene("game_over", score=self.score)
        else:
            self.ball.set_pos(*self.table.plunger_rest)
            self.ball.stop()
            self.state = "ready"

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        board_rect = pygame.Rect(PINBALL_BOARD_X, PINBALL_BOARD_Y,
                                  PINBALL_BOARD_W, PINBALL_BOARD_H)
        pygame.draw.rect(screen, PINBALL_COLOR_BG, board_rect)
        self._draw_lane_background(screen)

        self._draw_walls(screen)
        self._draw_slingshots(screen)
        self._draw_bumpers(screen)
        self._draw_flippers(screen)
        self._draw_ball(screen)
        pygame.draw.rect(screen, PINBALL_COLOR_WALL, board_rect, 3)

        self._draw_side_panel(screen)

    def _to_screen(self, point):
        return (point[0] + PINBALL_BOARD_X, point[1] + PINBALL_BOARD_Y)

    def _draw_lane_background(self, screen):
        lane_rect = pygame.Rect(
            self.table.lane_left_x, 0,
            PINBALL_BOARD_W - self.table.lane_left_x, PINBALL_BOARD_H,
        )
        lane_rect.move_ip(PINBALL_BOARD_X, PINBALL_BOARD_Y)
        pygame.draw.rect(screen, PINBALL_COLOR_LANE_BG, lane_rect)

    def _draw_walls(self, screen):
        for a, b in self.table.walls:
            pygame.draw.line(screen, PINBALL_COLOR_WALL,
                              self._to_screen(a), self._to_screen(b), 4)

    def _draw_slingshots(self, screen):
        for slingshot in self.table.slingshots:
            a, b = slingshot["seg"]
            flash = slingshot["cooldown"] > 0.0
            color = COLOR_WHITE if flash else PINBALL_COLOR_SLINGSHOT
            pygame.draw.line(screen, color, self._to_screen(a), self._to_screen(b), 5)

    def _draw_bumpers(self, screen):
        for bumper in self.table.bumpers:
            flash = bumper["cooldown"] > PINBALL_BUMPER_COOLDOWN * 0.5
            color = PINBALL_COLOR_BUMPER_HIT if flash else PINBALL_COLOR_BUMPER
            pygame.draw.circle(screen, color, self._to_screen(bumper["pos"]), bumper["radius"])
            pygame.draw.circle(screen, COLOR_BLACK, self._to_screen(bumper["pos"]),
                                bumper["radius"], 2)

    def _draw_flippers(self, screen):
        for flipper in self.table.flippers:
            pivot, tip = flipper.segment()
            pygame.draw.line(screen, PINBALL_COLOR_FLIPPER,
                              self._to_screen(pivot), self._to_screen(tip),
                              flipper.thickness * 2)
            pygame.draw.circle(screen, PINBALL_COLOR_FLIPPER, self._to_screen(pivot),
                                flipper.thickness)

    def _draw_ball(self, screen):
        pygame.draw.circle(screen, PINBALL_COLOR_BALL,
                            self._to_screen(self.ball.pos), self.ball.radius)

    def _draw_side_panel(self, screen):
        panel_x = PINBALL_BOARD_X + PINBALL_BOARD_W + 30

        label = self.font_label.render("SCORE", True, COLOR_GRAY)
        screen.blit(label, (panel_x, 40))
        value = self.font_value.render(f"{self.score:06d}", True, COLOR_WHITE)
        screen.blit(value, (panel_x, 64))

        high_label = self.font_label.render("HIGH", True, COLOR_GRAY)
        screen.blit(high_label, (panel_x, 108))
        high_value = self.font_value.render(f"{PinballScene.HIGH_SCORE:06d}", True, COLOR_YELLOW)
        screen.blit(high_value, (panel_x, 132))

        ball_label = self.font_label.render("BALL", True, COLOR_GRAY)
        screen.blit(ball_label, (panel_x, 176))
        ball_value = self.font_value.render(str(max(0, self.balls_left)), True, COLOR_WHITE)
        screen.blit(ball_value, (panel_x, 200))

        if self.state == "ready":
            ratio = self.charge / PINBALL_LAUNCH_CHARGE_TIME
            meter_label = self.font_label.render("LAUNCH", True, COLOR_GRAY)
            screen.blit(meter_label, (panel_x, 244))
            meter_rect = pygame.Rect(panel_x, 268, 90, 14)
            pygame.draw.rect(screen, COLOR_GRAY, meter_rect, 1)
            fill_rect = pygame.Rect(panel_x, 268, int(90 * ratio), 14)
            pygame.draw.rect(screen, COLOR_YELLOW, fill_rect)

        controls_y = 330
        controls_label = self.font_label.render("CONTROLS", True, COLOR_GRAY)
        screen.blit(controls_label, (panel_x, controls_y))
        lines = [
            "DOWN(HOLD/",
            "RELEASE): LAUNCH",
            "<- : LEFT FLIP",
            "-> : RIGHT FLIP",
            "ESC : MENU",
        ]
        for i, line in enumerate(lines):
            text = self.font_small.render(line, True, COLOR_WHITE)
            screen.blit(text, (panel_x, controls_y + 26 + i * 22))
