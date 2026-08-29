"""イカジャンプ — 下からマグマが迫る中、足場を登り続けるハイスコア型ジャンプゲーム。

状態機械:
  intro → play → game_over

座標はワールド（y は下ほど大きい）。cam_y で画面へ落とす。
プレイヤーが上へ進むほど cam_y が小さく（負に）なり、足場が下へ流れる。
カメラは登った高さぶんだけ一方向に進み、後戻りしない（マグマに追われる緊張感のため）。
"""

import math

import pygame

from scenes.base_scene import BaseScene
from game_objects.ika_jump.player import Squid
from game_objects.ika_jump.stage import Platform, spawn_platform
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_RED, COLOR_YELLOW, COLOR_GRAY,
    IKA_MAGMA_START_MARGIN, IKA_MAGMA_BASE_SPEED,
    IKA_MAGMA_SPEED_RAMP, IKA_MAGMA_MAX_SPEED,
    IKA_COLOR_SKY_TOP, IKA_COLOR_SKY_BOT,
    IKA_COLOR_MAGMA_CORE, IKA_COLOR_MAGMA_TOP,
)

CAM_ANCHOR = 0.42
GENERATE_AHEAD = 200  # 画面上端よりこの分上まで足場を用意しておく（px）


class IkaJumpScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（他ゲームと同方針）

    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 60)
        self.sound = SoundBank()

        self.score = 0
        self.max_height = 0.0
        self.anim = 0.0
        self.state = "intro"
        self.intro_timer = 1.5

        ground_y = 0
        ground = Platform(0, ground_y, kind="normal", width=SCREEN_WIDTH)
        self.platforms = [ground]
        self.highest_platform_x = SCREEN_WIDTH / 2
        self.highest_platform_y = ground_y

        self.player = Squid(SCREEN_WIDTH / 2, ground_y)

        self.cam_y = self.player.bottom - SCREEN_HEIGHT * CAM_ANCHOR
        self.magma_y = self.cam_y + SCREEN_HEIGHT + IKA_MAGMA_START_MARGIN
        self.magma_speed = IKA_MAGMA_BASE_SPEED

        self._fill_platforms()

    # --- 入力 ---------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "intro":
            self.state = "play"

    # --- 更新 ---------------------------------------------------------
    def update(self, dt):
        self.anim += dt

        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "play"
            return

        if self.state != "play":
            return

        keys = pygame.key.get_pressed()
        prev_bottom = self.player.update(dt, keys)
        self._check_landing(prev_bottom)
        self._update_platforms(dt)
        self._fill_platforms()
        self._update_camera()
        self._update_magma(dt)
        self._update_score()
        self._check_death()

    def _check_landing(self, prev_bottom):
        if self.player.vel_y <= 0:
            return
        pr = self.player.get_world_rect()
        for p in self.platforms:
            if p.gone:
                continue
            if pr.centerx < p.x or pr.centerx > p.x + p.width:
                continue
            if prev_bottom <= p.y and self.player.bottom >= p.y:
                self.player.bottom = p.y
                self.player.bounce()
                p.on_landed()
                self.sound.play_se("jump")
                break

    def _update_platforms(self, dt):
        for p in self.platforms:
            p.update(dt)
        cull_below = self.cam_y + SCREEN_HEIGHT + 80
        self.platforms = [p for p in self.platforms if p.y < cull_below and not p.gone]

    def _fill_platforms(self):
        top_visible = self.cam_y - GENERATE_AHEAD
        while self.highest_platform_y > top_visible:
            altitude = max(0, -self.highest_platform_y)
            p = spawn_platform(self.highest_platform_x, self.highest_platform_y, altitude)
            self.platforms.append(p)
            self.highest_platform_x = p.x
            self.highest_platform_y = p.y

    def _update_camera(self):
        target = self.player.bottom - SCREEN_HEIGHT * CAM_ANCHOR
        self.cam_y = min(self.cam_y, target)

    def _update_magma(self, dt):
        altitude = max(0, -self.player.bottom)
        self.magma_speed = min(
            IKA_MAGMA_MAX_SPEED,
            IKA_MAGMA_BASE_SPEED + altitude * IKA_MAGMA_SPEED_RAMP,
        )
        self.magma_y -= self.magma_speed * dt

    def _update_score(self):
        height = max(0.0, -self.player.bottom)
        if height > self.max_height:
            self.max_height = height
        self.score = int(self.max_height / 10) * 10

    def _check_death(self):
        if self.player.bottom >= self.magma_y:
            self._update_high()
            self.sound.play_se("death")
            self.state = "game_over"
            self.request_scene("game_over", score=self.score)

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        self._draw_sky(screen)
        self._draw_magma(screen)
        for p in self.platforms:
            p.draw(screen, self.cam_y)
        self.player.draw(screen, self.cam_y)
        self._draw_hud(screen)
        self._draw_controls(screen)

        if self.state == "intro":
            self._draw_center(screen, "ESCAPE THE MAGMA!", COLOR_YELLOW, self.big_font)

    def _draw_sky(self, screen):
        top = IKA_COLOR_SKY_TOP
        bot = IKA_COLOR_SKY_BOT
        h = SCREEN_HEIGHT
        for y in range(0, h, 4):
            t = y / h
            col = (
                int(top[0] + (bot[0] - top[0]) * t),
                int(top[1] + (bot[1] - top[1]) * t),
                int(top[2] + (bot[2] - top[2]) * t),
            )
            pygame.draw.rect(screen, col, (0, y, SCREEN_WIDTH, 4))

    def _draw_magma(self, screen):
        base_sy = self.magma_y - self.cam_y
        if base_sy >= SCREEN_HEIGHT:
            return
        top = max(0, int(base_sy))
        rect = pygame.Rect(0, top, SCREEN_WIDTH, SCREEN_HEIGHT - top)
        pygame.draw.rect(screen, IKA_COLOR_MAGMA_CORE, rect)
        for x in range(0, SCREEN_WIDTH, 16):
            wave = int(math.sin(self.anim * 4 + x * 0.05) * 5)
            y = int(base_sy) + wave
            if 0 <= y < SCREEN_HEIGHT:
                pygame.draw.rect(screen, IKA_COLOR_MAGMA_TOP, (x, y, 16, 6))

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        high = self.font.render(f"HIGH  {IkaJumpScene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high, (12, 34))
        alt = self.font.render(f"{int(self.max_height / 10)} m", True, COLOR_YELLOW)
        screen.blit(alt, (SCREEN_WIDTH - alt.get_width() - 12, 10))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE     ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

    def _draw_center(self, screen, text, color, font):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def _update_high(self):
        if self.score > IkaJumpScene.HIGH_SCORE:
            IkaJumpScene.HIGH_SCORE = self.score
