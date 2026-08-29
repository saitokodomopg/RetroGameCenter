"""ワギャンランド — 1 ステージ＋ボス戦。

ワギャンを操作し、音波（ワッ〜ギャー）で敵をしびれさせて足場にしながら
ステージを右へ進む。ゴールへ到達するとボス（Dr.デビル）との知恵比べ
（神経衰弱／しりとりのどちらかがランダム）に突入する。

状態機械:
  intro → play → (dying → play 復帰 | game_over)
                → (ゴール到達で boss_intro → boss へ)
  boss  → (勝敗確定後) → clear | (残機があれば boss を再挑戦) | game_over

横スクロールのみ（縦カメラなし）。cam_x だけでワールド→画面変換する。
"""

import random

import pygame

from scenes.base_scene import BaseScene
from game_objects.wagyan.stage import Stage, ENEMY_DEFS
from game_objects.wagyan.player import Wagyan
from game_objects.wagyan.enemy import Enemy
from game_objects.wagyan.boss_minigame import create_random_minigame
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_YELLOW, COLOR_RED,
    COLOR_GRAY,
    WAGYAN_WORLD_WIDTH, WAGYAN_GROUND_Y, WAGYAN_GOAL_X,
    WAGYAN_START_LIVES, WAGYAN_RESPAWN_INVINCIBLE, WAGYAN_DEATH_TIME,
    WAGYAN_PARALYZE_SCORE, WAGYAN_WAGYANIZER_SCORE, WAGYAN_BOSS_WIN_BONUS,
    WAGYAN_VOICE_LABELS, WAGYAN_COLOR_SKY, WAGYAN_COLOR_WAVE,
    WAGYAN_COLOR_BOSS, WAGYAN_COLOR_BODY,
)

CAM_ANCHOR = 0.36     # プレイヤーを画面のこの割合の位置に置く
FALL_MARGIN = 60       # 画面下端よりこれ以上落ちたらミス


class WagyanLandScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（他ゲームと同方針）

    # --- ライフサイクル ----------------------------------------------
    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 60)
        self.mid_font = pygame.font.Font(None, 38)
        self.sound = SoundBank()

        self.lives = WAGYAN_START_LIVES
        self.score = 0
        self.anim = 0.0
        self.furthest_x = 80

        self.stage = Stage()
        self.enemies = [Enemy(d["x"], d["min_x"], d["max_x"]) for d in ENEMY_DEFS]
        self.minigame = None
        self.boss_result_timer = None

        self._reset_round(full=True)
        self.state = "intro"
        self.intro_timer = 1.6

    def _reset_round(self, full=False):
        start_x = 80 if full else max(80, self.furthest_x - 150)
        # ワギャナイザーは取得済みだと復活しないため、ミス復帰時に音波レベルを
        # 1 へ戻すと詰む恐れがある。ステージ内では到達済みレベルを保持する。
        prev_level = self.player.level if not full else 1
        self.player = Wagyan(start_x, WAGYAN_GROUND_Y)
        self.player.level = prev_level
        self.cam_x = self._target_cam()
        self.invincible = 0.0 if full else WAGYAN_RESPAWN_INVINCIBLE
        self.death_timer = 0.0
        self.state = "play"

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "intro":
            self.state = "play"
            return
        if self.state == "play":
            if event.key in (pygame.K_UP, pygame.K_z):
                if self.player.jump():
                    self.sound.play_se("jump")
            elif event.key == pygame.K_SPACE:
                if self.player.try_fire_voice():
                    self.sound.play_se("voice")
        elif self.state == "boss":
            self.minigame.handle_key(event.key)

    # --- 更新 ---------------------------------------------------------
    def update(self, dt):
        self.anim += dt

        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "play"
            return

        if self.state == "dying":
            self.player.update_dying(dt)
            self.death_timer -= dt
            if self.death_timer <= 0:
                if self.lives <= 0:
                    self._update_high()
                    self.request_scene("game_over", score=self.score)
                else:
                    self._reset_round(full=False)
            return

        if self.state == "clear":
            return

        keys = pygame.key.get_pressed()
        if self.state == "play":
            self._update_play(dt, keys)
        elif self.state == "boss_intro":
            self._update_boss_intro(dt)
        elif self.state == "boss":
            self._update_boss(dt)

    def _update_play(self, dt, keys):
        solid = self.stage.solid_rects() + [
            e.get_world_rect() for e in self.enemies if e.paralyzed
        ]
        self.player.update(dt, keys, solid)

        if self.invincible > 0:
            self.invincible -= dt

        hit_rect = self.player.voice_hitbox()
        if hit_rect:
            for e in self.enemies:
                if not e.paralyzed and hit_rect.colliderect(e.get_world_rect()):
                    e.paralyze(self.player.voice_stun_duration())
                    self.score += WAGYAN_PARALYZE_SCORE
                    self.sound.play_se("paralyze")

        for e in self.enemies:
            e.update(dt)

        got = self.stage.collect_wagyanizer(self.player.get_world_rect())
        if got:
            self.player.level_up()
            self.score += WAGYAN_WAGYANIZER_SCORE
            self.sound.play_se("levelup")

        if self.invincible <= 0:
            pr = self.player.get_world_rect()
            for e in self.enemies:
                if not e.paralyzed and pr.colliderect(e.get_world_rect()):
                    self._player_miss()
                    return

        if self.player.bottom > SCREEN_HEIGHT + FALL_MARGIN:
            self._player_miss()
            return

        self.furthest_x = max(self.furthest_x, self.player.cx)
        self._update_camera(dt)
        self._update_high()

        if self.player.cx >= WAGYAN_GOAL_X:
            self._enter_boss_intro()

    def _player_miss(self):
        self.lives -= 1
        self.state = "dying"
        self.death_timer = WAGYAN_DEATH_TIME
        self.player.start_dying()
        self.sound.play_se("death")

    # --- カメラ -------------------------------------------------------
    def _target_cam(self):
        target = self.player.cx - SCREEN_WIDTH * CAM_ANCHOR
        return max(0, min(WAGYAN_WORLD_WIDTH - SCREEN_WIDTH, target))

    def _update_camera(self, dt):
        target = self._target_cam()
        self.cam_x += (target - self.cam_x) * min(1.0, dt * 8)

    # --- ボス戦 ---------------------------------------------------------
    def _enter_boss_intro(self):
        self.state = "boss_intro"
        self.boss_intro_timer = 1.4

    def _update_boss_intro(self, dt):
        self.boss_intro_timer -= dt
        if self.boss_intro_timer <= 0:
            self.minigame = create_random_minigame(random.Random())
            self.boss_result_timer = None
            self.state = "boss"

    def _update_boss(self, dt):
        self.minigame.update(dt)
        if not self.minigame.finished:
            return
        if self.boss_result_timer is None:
            self.boss_result_timer = 2.0
            self.sound.play_se("clear" if self.minigame.winner == "player" else "wrong")
        else:
            self.boss_result_timer -= dt
            if self.boss_result_timer <= 0:
                self._resolve_boss_result()

    def _resolve_boss_result(self):
        if self.minigame.winner == "player":
            self.score += WAGYAN_BOSS_WIN_BONUS
            self._update_high()
            self.request_scene(
                "clear", score=self.score, title="WAGYAN LAND RECLAIMED!",
                message="YOU OUTWITTED DR. DEVIL!")
            return

        self.lives -= 1
        if self.lives <= 0:
            self._update_high()
            self.request_scene("game_over", score=self.score)
            return
        self.minigame = create_random_minigame(random.Random())
        self.boss_result_timer = None
        self.state = "boss"

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        if self.state in ("boss_intro", "boss"):
            self._draw_boss_scene(screen)
            self._draw_hud(screen)
            return

        screen.fill(WAGYAN_COLOR_SKY)
        self.stage.draw(screen, self.cam_x)
        for e in self.enemies:
            e.draw(screen, self.cam_x)

        wave = self.player.voice_hitbox()
        if wave:
            wr = wave.copy()
            wr.x -= int(self.cam_x)
            pygame.draw.ellipse(screen, WAGYAN_COLOR_WAVE, wr, 3)

        blink = self.invincible > 0 and int(self.invincible * 12) % 2 == 0
        self.player.draw(screen, self.cam_x, blink=blink)

        self._draw_hud(screen)
        self._draw_controls(screen)

        if self.state == "intro":
            self._draw_center(screen, "RECLAIM WAGYAN LAND!", COLOR_YELLOW, self.big_font)
        elif self.state == "dying":
            self._draw_center(screen, "MISS!", COLOR_RED, self.big_font)

    def _draw_boss_scene(self, screen):
        screen.fill((20, 16, 40))
        # 簡易アリーナ床
        pygame.draw.rect(screen, (40, 30, 70), (0, SCREEN_HEIGHT - 90, SCREEN_WIDTH, 90))

        # Dr.デビル（左側に簡易表示）
        bx, by = 110, SCREEN_HEIGHT - 150
        pygame.draw.ellipse(screen, WAGYAN_COLOR_BOSS, (bx - 40, by - 60, 80, 90))
        pygame.draw.circle(screen, (230, 200, 210), (bx, by - 70), 22)
        pygame.draw.polygon(screen, (20, 20, 20),
                            [(bx - 20, by - 90), (bx + 20, by - 90), (bx, by - 60)])

        # ワギャン（右側で静止・こちらを向く）
        wx, wy = SCREEN_WIDTH - 130, SCREEN_HEIGHT - 120
        pygame.draw.ellipse(screen, WAGYAN_COLOR_BODY, (wx - 18, wy - 32, 36, 42))
        pygame.draw.circle(screen, (255, 255, 255), (wx - 8, wy - 20), 5)
        pygame.draw.circle(screen, (20, 20, 20), (wx - 9, wy - 20), 2)

        if self.state == "boss_intro":
            self._draw_center(screen, "DR. DEVIL CHALLENGES YOU!", COLOR_YELLOW, self.mid_font)
            return

        self.minigame.draw(screen)
        if self.minigame.finished:
            result = "YOU WIN!" if self.minigame.winner == "player" else "YOU LOSE..."
            color = COLOR_YELLOW if self.minigame.winner == "player" else COLOR_RED
            self._draw_center(screen, result, color, self.mid_font)

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        high = self.font.render(f"HIGH  {WagyanLandScene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high, (12, 34))

        label = WAGYAN_VOICE_LABELS[self.player.level - 1]
        voice = self.font.render(label, True, WAGYAN_COLOR_WAVE)
        screen.blit(voice, (SCREEN_WIDTH // 2 - voice.get_width() // 2, 10))

        for i in range(self.lives):
            ix = SCREEN_WIDTH - 26 - i * 24
            pygame.draw.ellipse(screen, WAGYAN_COLOR_BODY, (ix, 10, 16, 16))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE   UP/Z: JUMP   SPACE: VOICE ATTACK   ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

    def _draw_center(self, screen, text, color, font):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def _update_high(self):
        if self.score > WagyanLandScene.HIGH_SCORE:
            WagyanLandScene.HIGH_SCORE = self.score
