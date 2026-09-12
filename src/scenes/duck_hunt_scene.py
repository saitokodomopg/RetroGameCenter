"""ダックハント風ガンシューティングシーン。

的のロジックは game_objects.gun.target.Target / make_target に分離している。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。

状態機械:
    intro --GUN_INTRO_TIME経過--> play --ラウンド終了条件--> result
    result --クリア--> intro（次ラウンド）
    result --未クリア--> over
    over --R--> intro（ラウンド1から再開）

ラウンド終了条件（play 中、いずれか先に成立）:
    - 予定の的（targets_total）を全て出し切り、最後の的が解決した
    - 残弾（ammo）が 0 になった
    - 残り時間（time_left）が 0 になった
"""

import math
import pygame
from scenes.base_scene import BaseScene
from game_objects.gun.target import make_target
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_RED,
    COLOR_YELLOW, COLOR_GRAY,
    GUN_BASE_TARGETS, GUN_MAX_TARGETS, GUN_CLEAR_RATIO, GUN_AMMO_MARGIN,
    GUN_BASE_TIME, GUN_MIN_TIME, GUN_TIME_STEP,
    GUN_INTRO_TIME, GUN_RESULT_TIME, GUN_SPAWN_DELAY, GUN_HIT_FLASH_TIME,
    GUN_ROUND_CLEAR_BONUS, GUN_TOP_BAR_H, GUN_BOTTOM_BAR_H,
    COLOR_GUN_SKY, COLOR_GUN_SKY_HORIZON, COLOR_GUN_GROUND, COLOR_GUN_CLOUD,
    COLOR_GUN_RETICLE, COLOR_GUN_BIRD, COLOR_GUN_BIRD_WING,
    COLOR_GUN_UFO, COLOR_GUN_UFO_DOME,
)

# 画面内に常時掲載する操作説明
CONTROLS_TEXT = "MOUSE: AIM   CLICK: SHOOT   R: RESTART   ESC: MENU"

_GROUND_HEIGHT = 90


class DuckHuntScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_big = pygame.font.Font(None, 64)
        self.font_mid = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 26)
        self.font_hint = pygame.font.Font(None, 22)
        self.sound = SoundBank()
        self.time = 0.0
        self.aim_x = SCREEN_WIDTH // 2
        self.aim_y = SCREEN_HEIGHT // 2
        pygame.mouse.set_visible(False)
        self._reset_game()

    def on_exit(self):
        pygame.mouse.set_visible(True)

    def _reset_game(self):
        self.round_no = 1
        self.score = 0
        self.last_result = None
        self._start_round()

    def _start_round(self):
        self.targets_total = min(
            GUN_MAX_TARGETS, GUN_BASE_TARGETS + (self.round_no - 1))
        self.quota = math.ceil(self.targets_total * GUN_CLEAR_RATIO)
        self.ammo = self.targets_total + GUN_AMMO_MARGIN
        self.time_left = max(
            GUN_MIN_TIME, GUN_BASE_TIME - (self.round_no - 1) * GUN_TIME_STEP)
        self.hits = 0
        self.spawned = 0
        self.current_target = None
        self.spawn_timer = 0.0
        self.state = "intro"
        self.state_timer = GUN_INTRO_TIME

    def _end_round(self):
        if self.hits >= self.quota:
            self.last_result = "CLEAR"
            self.score += GUN_ROUND_CLEAR_BONUS * self.round_no
            self.sound.play_se("clear")
        else:
            self.last_result = "FAILED"
            self.sound.play_se("death")
        self.current_target = None
        self.state = "result"
        self.state_timer = GUN_RESULT_TIME

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.aim_x, self.aim_y = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.aim_x, self.aim_y = event.pos
            if self.state == "play":
                self._fire(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.state == "over":
                self._reset_game()

    def _fire(self, pos):
        if self.ammo <= 0:
            return
        self.ammo -= 1
        self.sound.play_se("gun_shot")
        px, py = pos
        target = self.current_target
        if target is not None and not target.hit and target.hit_test(px, py):
            self.hits += 1
            self.score += target.score
            self.sound.play_se("score")
            target.mark_hit()  # 即座には消さず、点滅させてから消す
        else:
            self.sound.play_se("lock")

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        self.time += dt

        if self.state == "intro":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "play"
            return

        if self.state == "result":
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.last_result == "CLEAR":
                    self.round_no += 1
                    self._start_round()
                else:
                    self.state = "over"
            return

        if self.state == "over":
            return

        # --- play ---
        self.time_left = max(0.0, self.time_left - dt)

        if self.current_target is None:
            if self.spawned < self.targets_total:
                self.spawn_timer += dt
                if self.spawn_timer >= GUN_SPAWN_DELAY:
                    self.current_target = make_target(self.round_no)
                    self.spawned += 1
                    self.spawn_timer = 0.0
        else:
            self.current_target.update(dt)
            if self.current_target.hit:
                if self.current_target.is_hit_done():
                    self.current_target = None
                    self.spawn_timer = 0.0
            elif self.current_target.is_expired():
                self.current_target = None
                self.spawn_timer = 0.0

        # 命中演出（点滅）の途中でラウンドを打ち切らないよう、演出中は終了判定を待つ
        playing_hit_effect = self.current_target is not None and self.current_target.hit
        all_resolved = self.spawned >= self.targets_total and self.current_target is None
        if not playing_hit_effect and (self.ammo <= 0 or self.time_left <= 0 or all_resolved):
            self._end_round()

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_background(screen)
        if self.current_target is not None and self.state == "play":
            self._draw_target(screen, self.current_target)
        self._draw_top_bar(screen)
        self._draw_bottom_bar(screen)
        self._draw_reticle(screen)

        if self.state == "intro":
            self._draw_center_text(screen, f"ROUND {self.round_no}", COLOR_YELLOW)
        elif self.state == "result":
            color = COLOR_YELLOW if self.last_result == "CLEAR" else COLOR_RED
            label = "ROUND CLEAR!" if self.last_result == "CLEAR" else "FAILED..."
            self._draw_center_text(screen, label, color)
        elif self.state == "over":
            self._draw_game_over(screen)

    def _play_area(self):
        top = GUN_TOP_BAR_H
        bottom = SCREEN_HEIGHT - GUN_BOTTOM_BAR_H
        return top, bottom

    def _draw_background(self, screen):
        top, bottom = self._play_area()
        ground_y = bottom - _GROUND_HEIGHT
        # 空（上を濃い空色、地平線付近を明るく）
        pygame.draw.rect(screen, COLOR_GUN_SKY, (0, top, SCREEN_WIDTH, ground_y - top))
        horizon_h = 40
        pygame.draw.rect(
            screen, COLOR_GUN_SKY_HORIZON,
            (0, ground_y - horizon_h, SCREEN_WIDTH, horizon_h))
        # 雲（ゆっくり右へ流れる）
        drift = (self.time * 12) % (SCREEN_WIDTH + 160)
        for i, cy in enumerate((top + 40, top + 80, top + 55)):
            cx = (drift + i * 260) % (SCREEN_WIDTH + 160) - 80
            self._draw_cloud(screen, cx, cy)
        # 地面
        pygame.draw.rect(screen, COLOR_GUN_GROUND, (0, ground_y, SCREEN_WIDTH, bottom - ground_y))

    def _draw_cloud(self, screen, cx, cy):
        for dx, r in ((-18, 14), (0, 20), (20, 15), (10, 12)):
            pygame.draw.circle(screen, COLOR_GUN_CLOUD, (int(cx + dx), int(cy)), r)

    def _draw_target(self, screen, t):
        x, y = int(t.x), int(t.y)

        # 命中演出中は高速点滅させ、点数ポップアップを重ねて表示する
        visible = True
        if t.hit:
            visible = int(t.hit_timer * 16) % 2 == 0

        if visible:
            if t.kind == "UFO":
                pygame.draw.ellipse(
                    screen, COLOR_GUN_UFO,
                    (x - t.radius, y - t.radius * 0.55, t.radius * 2, t.radius))
                pygame.draw.ellipse(
                    screen, COLOR_GUN_UFO_DOME,
                    (x - t.radius * 0.5, y - t.radius, t.radius, t.radius * 0.8))
            else:  # BIRD
                # 定番の「M字」シルエット。翼の高さを羽ばたきで上下させる。
                lift = math.sin(t.age * 10) * t.radius * 0.5
                pygame.draw.lines(screen, COLOR_GUN_BIRD_WING, False, [
                    (x - t.radius * 1.6, y - lift),
                    (x, y + t.radius * 0.4),
                    (x + t.radius * 1.6, y - lift),
                ], 4)
                pygame.draw.circle(screen, COLOR_GUN_BIRD, (x, y), int(t.radius * 0.35))

        if t.hit:
            self._draw_score_popup(screen, t)

    def _draw_score_popup(self, screen, t):
        """命中位置から上へ少し浮かび上がる「+得点」表示。"""
        progress = min(1.0, t.hit_timer / GUN_HIT_FLASH_TIME)
        popup_y = t.y - t.radius - 10 - progress * 22
        # 上部 HUD 帯の裏に隠れないよう、帯のすぐ下に収める
        popup_y = max(GUN_TOP_BAR_H + 12, popup_y)
        text = self.font_small.render(f"+{t.score}", True, COLOR_YELLOW)
        screen.blit(text, text.get_rect(center=(int(t.x), int(popup_y))))

    def _draw_top_bar(self, screen):
        pygame.draw.rect(screen, COLOR_BLACK, (0, 0, SCREEN_WIDTH, GUN_TOP_BAR_H))
        score_t = self.font_small.render(f"SCORE {self.score:06d}", True, COLOR_YELLOW)
        screen.blit(score_t, (16, 10))

        ammo_t = self.font_small.render(f"AMMO {self.ammo:02d}", True, COLOR_WHITE)
        screen.blit(ammo_t, ammo_t.get_rect(center=(SCREEN_WIDTH // 2, 20)))

        secs = max(0, int(math.ceil(self.time_left)))
        time_t = self.font_small.render(
            f"TIME {secs // 60:02d}:{secs % 60:02d}", True, COLOR_WHITE)
        screen.blit(time_t, time_t.get_rect(topright=(SCREEN_WIDTH - 16, 10)))

    def _draw_bottom_bar(self, screen):
        y = SCREEN_HEIGHT - GUN_BOTTOM_BAR_H
        pygame.draw.rect(screen, COLOR_BLACK, (0, y, SCREEN_WIDTH, GUN_BOTTOM_BAR_H))
        info = self.font_small.render(
            f"ROUND {self.round_no}   HITS {self.hits}/{self.quota}", True, COLOR_WHITE)
        screen.blit(info, (16, y + 4))
        hint = self.font_hint.render(CONTROLS_TEXT, True, COLOR_GRAY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, y + 34)))

    def _draw_reticle(self, screen):
        x, y = self.aim_x, self.aim_y
        r = 12
        pygame.draw.circle(screen, COLOR_GUN_RETICLE, (x, y), r, 2)
        pygame.draw.line(screen, COLOR_GUN_RETICLE, (x - r - 6, y), (x - 4, y), 2)
        pygame.draw.line(screen, COLOR_GUN_RETICLE, (x + 4, y), (x + r + 6, y), 2)
        pygame.draw.line(screen, COLOR_GUN_RETICLE, (x, y - r - 6), (x, y - 4), 2)
        pygame.draw.line(screen, COLOR_GUN_RETICLE, (x, y + 4), (x, y + r + 6), 2)

    def _draw_center_text(self, screen, text, color):
        top, bottom = self._play_area()
        cy = (top + bottom) // 2
        shadow = self.font_big.render(text, True, COLOR_BLACK)
        main = self.font_big.render(text, True, color)
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, cy + 3)))
        screen.blit(main, main.get_rect(center=(SCREEN_WIDTH // 2, cy)))

    def _draw_game_over(self, screen):
        top, bottom = self._play_area()
        overlay = pygame.Surface((SCREEN_WIDTH, bottom - top), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, top))

        cy = (top + bottom) // 2
        title = self.font_big.render("GAME OVER", True, COLOR_RED)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, cy - 40)))
        score_t = self.font_mid.render(f"SCORE {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score_t, score_t.get_rect(center=(SCREEN_WIDTH // 2, cy)))
        if int(self.time * 2) % 2 == 0:
            info = self.font_small.render("R: RESTART   ESC: MENU", True, COLOR_WHITE)
            screen.blit(info, info.get_rect(center=(SCREEN_WIDTH // 2, cy + 40)))
