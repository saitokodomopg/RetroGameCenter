"""ブロック崩しシーン。パドル操作・ボール反射・ブロック破壊・残機を扱う。

ロジックは game_objects.block_breaker の Paddle / Ball / Brick に分離している。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。
"""

import pygame
from scenes.base_scene import BaseScene
from game_objects.block_breaker.paddle import Paddle
from game_objects.block_breaker.ball import Ball
from game_objects.block_breaker.brick import build_bricks
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_RED, COLOR_GRAY,
    BREAKOUT_START_LIVES,
)


class BlockBreakerScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.sound = SoundBank()

        self.lives = BREAKOUT_START_LIVES
        self._reset_round()

    def _reset_round(self):
        """ミス・開始時の共通リセット。残機以外(ブロック配置・スコア・パドル・ボール)を
        初期状態に戻す。"""
        self.score = 0
        self.bricks = build_bricks()
        self.paddle = Paddle()
        self.ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 8)
        self.state = "ready"  # ready / play

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.state == "ready":
                self.state = "play"
                self.ball.launch()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.paddle.update(dt, keys)

        if self.state == "ready":
            self.ball.x = self.paddle.rect.centerx
            self.ball.y = self.paddle.rect.top - self.ball.radius
            return

        self.ball.update(dt)
        self._check_wall_bounce()
        self._check_paddle_bounce()
        self._check_brick_hit()
        self._check_miss()

    def _check_wall_bounce(self):
        before_vx, before_vy = self.ball.vx, self.ball.vy
        self.ball.reflect_walls(SCREEN_WIDTH)
        if (self.ball.vx, self.ball.vy) != (before_vx, before_vy):
            self.sound.play_se("wall_hit")

    def _check_paddle_bounce(self):
        if self.ball.vy > 0 and self.ball.get_rect().colliderect(self.paddle.rect):
            self.ball.bounce_off_paddle(self.paddle)
            self.sound.play_se("paddle_hit")

    def _check_brick_hit(self):
        ball_rect = self.ball.get_rect()
        for brick in self.bricks:
            if not brick.alive:
                continue
            if ball_rect.colliderect(brick.rect):
                brick.alive = False
                self.ball.bounce_off_brick(brick.rect)
                self.score += brick.score
                self.sound.play_se("brick_break")
                break

        if all(not b.alive for b in self.bricks):
            self.sound.play_se("clear")
            self.request_scene(
                "clear", score=self.score,
                title="STAGE CLEAR!", message="ALL BRICKS DESTROYED!",
            )

    def _check_miss(self):
        if self.ball.is_below(SCREEN_HEIGHT):
            self.lives -= 1
            if self.lives <= 0:
                self.sound.play_se("death")
                self.request_scene("game_over", score=self.score)
            else:
                self.sound.play_se("death")
                self._reset_round()

    # --- 描画 --------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        for brick in self.bricks:
            brick.draw(screen)
        self.paddle.draw(screen)
        self.ball.draw(screen)
        self._draw_hud(screen)
        self._draw_controls(screen)

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        for i in range(self.lives):
            ix = SCREEN_WIDTH - 28 - i * 26
            pygame.draw.rect(screen, COLOR_RED, (ix, 12, 18, 12), border_radius=3)

        if self.state == "ready" and int(pygame.time.get_ticks() / 250) % 2 == 0:
            hint = self.font.render("SPACE: LAUNCH", True, COLOR_WHITE)
            screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE PADDLE     SPACE: LAUNCH     ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))
