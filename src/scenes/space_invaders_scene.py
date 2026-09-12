"""スペースインベーダーシーン。1 ウェーブ（5段×11列編隊）を撃破しきれるか。

状態機械: play → (被弾 → dying → play 復帰 | game_over) / (編隊全滅 → clear)
編隊が最下段（自機の高さ）まで到達した場合は「侵略」として即 game_over。
"""

import pygame

from scenes.base_scene import BaseScene
from game_objects.space_invaders.player import Player
from game_objects.space_invaders.invader import InvaderFleet
from game_objects.space_invaders.shield import Shield, WIDTH as SHIELD_WIDTH
from game_objects.space_invaders.ufo import UFO
from game_objects.collision import check_rect_collision
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW,
    SI_PLAYER_LIVES, SI_RESPAWN_INVINCIBLE, SI_DEATH_TIME,
    SI_SHIELD_Y, SI_SHIELD_COUNT, SI_COLOR_PLAYER, SI_COLOR_BULLET_PLAYER,
    SI_COLOR_BULLET_ENEMY, SI_COLOR_INVADER_ROWS, SI_INV_INVASION_Y,
)


class SpaceInvadersScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（他ゲーム同様）

    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 72)
        self.sound = SoundBank()
        self.lives = SI_PLAYER_LIVES
        self.score = 0
        self._reset_round(full=True)

    def _reset_round(self, full=False):
        """プレイヤー位置をリセット（ミス後の復帰）。full=True で編隊等も初期化。"""
        self.player = Player()
        if full:
            self.fleet = InvaderFleet()
            self.shields = self._make_shields()
            self.ufo = UFO()
        self.invincible = SI_RESPAWN_INVINCIBLE if not full else 0.0
        self.state = "play"
        self.death_timer = 0.0

    def _make_shields(self):
        shields = []
        for i in range(SI_SHIELD_COUNT):
            cx = SCREEN_WIDTH * (i + 1) / (SI_SHIELD_COUNT + 1)
            shields.append(Shield(cx - SHIELD_WIDTH / 2, SI_SHIELD_Y))
        return shields

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "play" and event.key == pygame.K_SPACE:
            if self.player.shoot():
                self.sound.play_se("shoot")

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        if self.state == "dying":
            self.death_timer -= dt
            if self.death_timer <= 0:
                if self.lives <= 0:
                    SpaceInvadersScene.HIGH_SCORE = max(SpaceInvadersScene.HIGH_SCORE, self.score)
                    self.request_scene("game_over", score=self.score)
                else:
                    self._reset_round(full=False)
            return

        if self.state != "play":
            return

        keys = pygame.key.get_pressed()
        self.player.move(dt, keys)
        self.player.update_bullet(dt)
        if self.invincible > 0:
            self.invincible -= dt

        self.fleet.update(dt)
        self.ufo.update(dt)

        self._handle_collisions()
        if self.state != "play":
            return

        if self.fleet.bottom_y() >= SI_INV_INVASION_Y:
            self._invasion()
            return

        if self.fleet.alive_count() == 0:
            SpaceInvadersScene.HIGH_SCORE = max(SpaceInvadersScene.HIGH_SCORE, self.score)
            self.request_scene(
                "clear", score=self.score,
                title="WAVE CLEAR!", message="THE INVASION IS REPELLED!")

    def _handle_collisions(self):
        bullet = self.player.bullet
        if bullet is not None:
            b_rect = bullet.rect()
            for r, c, rect in self.fleet.rects():
                if b_rect.colliderect(rect):
                    self.score += self.fleet.kill(r, c)
                    self.player.bullet = None
                    bullet = None
                    self.sound.play_se("invader_hit")
                    break
            if bullet is not None and self.ufo.active and b_rect.colliderect(self.ufo.rect()):
                self.score += self.ufo.kill()
                self.player.bullet = None
                bullet = None
                self.sound.play_se("ufo_bonus")
            if bullet is not None:
                for shield in self.shields:
                    if shield.hit(b_rect):
                        self.player.bullet = None
                        bullet = None
                        break

        for eb in self.fleet.bullets:
            if not eb.alive:
                continue
            eb_rect = eb.rect()
            hit_shield = False
            for shield in self.shields:
                if shield.hit(eb_rect):
                    eb.alive = False
                    hit_shield = True
                    break
            if hit_shield:
                continue
            if self.invincible <= 0 and check_rect_collision(eb_rect, self.player.rect()):
                eb.alive = False
                self._on_player_hit()
                return

        if self.invincible <= 0:
            player_rect = self.player.rect()
            for _, _, rect in self.fleet.rects():
                if rect.colliderect(player_rect):
                    self._on_player_hit()
                    return

    def _on_player_hit(self):
        self.lives -= 1
        self.state = "dying"
        self.death_timer = SI_DEATH_TIME
        self.sound.play_se("death")

    def _invasion(self):
        self.lives = 0
        self.state = "dying"
        self.death_timer = SI_DEATH_TIME
        self.sound.play_se("death")

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_hud(screen)
        self.ufo.draw(screen)
        for shield in self.shields:
            shield.draw(screen)
        self._draw_invaders(screen)
        for eb in self.fleet.bullets:
            pygame.draw.rect(screen, SI_COLOR_BULLET_ENEMY, eb.rect())
        self._draw_player(screen)
        if self.player.bullet is not None:
            pygame.draw.rect(screen, SI_COLOR_BULLET_PLAYER, self.player.bullet.rect())

    def _draw_invaders(self, screen):
        for r, c, rect in self.fleet.rects():
            color = SI_COLOR_INVADER_ROWS[r % len(SI_COLOR_INVADER_ROWS)]
            pygame.draw.rect(screen, color, rect, border_radius=3)

    def _draw_player(self, screen):
        if self.state == "dying" and self.lives <= 0:
            return
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # 無敵中は点滅
        rect = self.player.rect()
        pygame.draw.rect(screen, SI_COLOR_PLAYER, rect, border_radius=2)
        pygame.draw.rect(screen, SI_COLOR_PLAYER,
                         (rect.centerx - 2, rect.top - 6, 4, 8))

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE {self.score:05d}", True, COLOR_WHITE)
        screen.blit(score, (16, 12))
        hi = self.font.render(
            f"HIGH {max(self.score, SpaceInvadersScene.HIGH_SCORE):05d}",
            True, COLOR_YELLOW)
        screen.blit(hi, hi.get_rect(midtop=(SCREEN_WIDTH // 2, 12)))
        lives = self.font.render(f"LIVES {max(0, self.lives)}", True, COLOR_WHITE)
        screen.blit(lives, lives.get_rect(topright=(SCREEN_WIDTH - 16, 12)))
