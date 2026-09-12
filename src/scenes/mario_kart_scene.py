"""マリオカート フェーズB＋C — CPU対戦＋アイテム。

自機 + CPU 3台でスタジアム型コースを走る。CPU はコース中心線上の少し先の点を
追いかける単純なオートパイロット（cpu.CpuDriver）。順位はコース中心からの
進行角度を毎フレーム積算した値（周回をまたいでも連続的に増える）で決める。
アイテムボックスからバナナ／こうらを取得し、スペースキーで使用する。

状態機械: race → (自機が MK_LAPS 周 → finished → Clear シーンへ)
本フェーズにもミス／ライフの概念は無いため GameOver は使わない。
"""

import math
import random

import pygame

from scenes.base_scene import BaseScene
from game_objects.mario_kart.kart import Kart
from game_objects.mario_kart.cpu import CpuDriver
from game_objects.mario_kart import track
from game_objects.mario_kart import renderer
from game_objects.mario_kart import items
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_YELLOW,
    MK_TRACK_RADIUS, MK_TRACK_STRAIGHT_HALF, MK_LAPS,
    MK_COLOR_KART_BODY, MK_COLOR_KART_TRIM, MK_COLOR_CPU,
    MK_COLOR_ITEMBOX, MK_COLOR_BANANA, MK_COLOR_SHELL,
    MK_KART_WORLD_SIZE, MK_ITEMBOX_WORLD_SIZE, MK_BANANA_WORLD_SIZE, MK_SHELL_WORLD_SIZE,
    MK_CPU_COUNT, MK_CPU_START_GAP, MK_CPU_SPEED_SCALE_MIN, MK_CPU_SPEED_SCALE_MAX,
    MK_ITEM_BOX_COUNT, MK_CPU_ITEM_USE_DELAY_MIN, MK_CPU_ITEM_USE_DELAY_MAX,
    MK_LAP_MIN_PROGRESS_RATIO,
)

START_X = -200.0
START_Y = MK_TRACK_RADIUS
LAP_MIN_PROGRESS = MK_LAP_MIN_PROGRESS_RATIO * 2 * math.pi


def _normalize_angle(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


class _Racer:
    """自機・CPU 共通のレース状態（カート＋アイテム所持＋順位計算用の進行度）。"""

    def __init__(self, kart, is_player, color, cpu_driver=None):
        self.kart = kart
        self.is_player = is_player
        self.color = color
        self.cpu_driver = cpu_driver
        self.held_item = None
        self.cpu_use_timer = None
        self.progress_prev_angle = math.atan2(kart.y, kart.x)
        self.progress_accum = 0.0
        self.progress_at_last_lap = 0.0

    def update_progress(self):
        angle = math.atan2(self.kart.y, self.kart.x)
        delta = _normalize_angle(angle - self.progress_prev_angle)
        self.progress_accum -= delta  # 本コースは時計回りに進むほど angle が減るため符号反転
        self.progress_prev_angle = angle


class MarioKartScene(BaseScene):
    BEST_LAP = None  # 実行中のみ保持（他ゲームの HIGH_SCORE と同方針）

    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)

        player_kart = Kart(START_X, START_Y, heading=0.0)
        self.racers = [_Racer(player_kart, True, MK_COLOR_KART_BODY)]
        self.player = self.racers[0]

        for i in range(MK_CPU_COUNT):
            scale = random.uniform(MK_CPU_SPEED_SCALE_MIN, MK_CPU_SPEED_SCALE_MAX)
            back = MK_CPU_START_GAP * (i + 1)
            lateral = 70 if i % 2 == 0 else -70
            kart = Kart(START_X - back, START_Y + lateral, heading=0.0, max_speed_scale=scale)
            start_progress = kart.x + MK_TRACK_STRAIGHT_HALF + 250.0
            driver = CpuDriver(kart, start_progress)
            color = MK_COLOR_CPU[i % len(MK_COLOR_CPU)]
            self.racers.append(_Racer(kart, False, color, cpu_driver=driver))

        self.item_boxes = self._make_item_boxes()
        self.bananas = []
        self.shells = []

        self.laps_completed = 0
        self.race_time = 0.0
        self.lap_times = []
        self.state = "race"

    def _make_item_boxes(self):
        boxes = []
        for i in range(MK_ITEM_BOX_COUNT):
            t = (i + 0.5) / MK_ITEM_BOX_COUNT * track.TOTAL_LENGTH
            x, y = track.centerline_point(t)
            boxes.append(items.ItemBox(x, y))
        return boxes

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == "race":
            self._use_item(self.player)

    def _use_item(self, racer):
        if racer.held_item is None:
            return
        if racer.held_item == "banana":
            self.bananas.append(items.drop_banana(racer.kart))
        else:
            self.shells.append(items.fire_shell(racer.kart))
        racer.held_item = None

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        if self.state != "race":
            return

        keys = pygame.key.get_pressed()

        for racer in self.racers:
            kart = racer.kart
            if racer.is_player:
                accel_input = 0
                if keys[pygame.K_UP]:
                    accel_input = 1
                elif keys[pygame.K_DOWN]:
                    accel_input = -1
                steer_input = 0
                if keys[pygame.K_LEFT]:
                    steer_input = -1
                elif keys[pygame.K_RIGHT]:
                    steer_input = 1
            else:
                accel_input, steer_input = racer.cpu_driver.control(dt)

            on_track = track.is_on_track(kart.x, kart.y)
            prev_x, prev_y = kart.x, kart.y
            kart.update(dt, accel_input, steer_input, on_track)
            racer.update_progress()

            if (racer.is_player
                    and track.crossed_finish_line(prev_x, prev_y, kart.x, kart.y)
                    and racer.progress_accum - racer.progress_at_last_lap >= LAP_MIN_PROGRESS):
                racer.progress_at_last_lap = racer.progress_accum
                lap_time = self.race_time - sum(self.lap_times)
                self.lap_times.append(lap_time)
                if MarioKartScene.BEST_LAP is None or lap_time < MarioKartScene.BEST_LAP:
                    MarioKartScene.BEST_LAP = lap_time
                self.laps_completed += 1
                if self.laps_completed >= MK_LAPS:
                    self.state = "finished"

            if racer.held_item is None:
                for box in self.item_boxes:
                    if box.try_pickup(kart.x, kart.y):
                        racer.held_item = items.random_item_kind()
                        if not racer.is_player:
                            racer.cpu_use_timer = random.uniform(
                                MK_CPU_ITEM_USE_DELAY_MIN, MK_CPU_ITEM_USE_DELAY_MAX)
                        break

            if not racer.is_player and racer.held_item is not None and racer.cpu_use_timer is not None:
                racer.cpu_use_timer -= dt
                if racer.cpu_use_timer <= 0:
                    self._use_item(racer)
                    racer.cpu_use_timer = None

        self.race_time += dt

        for box in self.item_boxes:
            box.update(dt)
        for b in self.bananas:
            b.update(dt)
        for s in self.shells:
            s.update(dt)

        for racer in self.racers:
            kart = racer.kart
            for b in self.bananas:
                if b.check_hit(kart):
                    kart.hit()
            for s in self.shells:
                if s.check_hit(kart):
                    kart.hit()

        self.bananas = [b for b in self.bananas if b.alive]
        self.shells = [s for s in self.shells if s.alive]

        if self.state == "finished":
            rank = self._player_rank()
            self.request_scene(
                "clear", title="RACE COMPLETE!",
                message=f"TIME {self.race_time:.2f}s   RANK {rank}/{len(self.racers)}")

    def _player_rank(self):
        ordered = sorted(self.racers, key=lambda r: r.progress_accum, reverse=True)
        return ordered.index(self.player) + 1

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        cam_kart = self.player.kart
        renderer.draw_sky(screen)
        renderer.draw_ground(screen, cam_kart)

        billboards = []
        for box in self.item_boxes:
            if box.active:
                billboards.append((box.x, box.y, MK_ITEMBOX_WORLD_SIZE, MK_COLOR_ITEMBOX, "rect"))
        for b in self.bananas:
            billboards.append((b.x, b.y, MK_BANANA_WORLD_SIZE, MK_COLOR_BANANA, "circle"))
        for s in self.shells:
            billboards.append((s.x, s.y, MK_SHELL_WORLD_SIZE, MK_COLOR_SHELL, "circle"))
        for racer in self.racers:
            if racer.is_player:
                continue
            billboards.append((racer.kart.x, racer.kart.y, MK_KART_WORLD_SIZE, racer.color, "rect"))

        hx, hy = cam_kart.heading_vector()

        def depth_key(item):
            wx, wy = item[0], item[1]
            return -((wx - cam_kart.x) * hx + (wy - cam_kart.y) * hy)

        billboards.sort(key=depth_key)
        for wx, wy, size, color, shape in billboards:
            if shape == "rect":
                renderer.draw_billboard_rect(screen, cam_kart, wx, wy, size, color)
            else:
                renderer.draw_billboard_circle(screen, cam_kart, wx, wy, size, color)

        self._draw_kart_sprite(screen)
        self._draw_hud(screen)

    def _draw_kart_sprite(self, screen):
        cx = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 90
        body = pygame.Rect(cx - 40, y, 80, 50)
        pygame.draw.rect(screen, MK_COLOR_KART_BODY, body, border_radius=8)
        pygame.draw.rect(screen, MK_COLOR_KART_TRIM, (cx - 40, y, 80, 10), border_radius=4)
        pygame.draw.rect(screen, (20, 20, 20), (cx - 48, y + 34, 14, 20), border_radius=3)
        pygame.draw.rect(screen, (20, 20, 20), (cx + 34, y + 34, 14, 20), border_radius=3)

    def _draw_hud(self, screen):
        lap_text = f"LAP {min(self.laps_completed + 1, MK_LAPS)}/{MK_LAPS}"
        t = self.font.render(lap_text, True, COLOR_WHITE)
        screen.blit(t, (16, 12))

        time_text = f"TIME {self.race_time:.2f}"
        t2 = self.font.render(time_text, True, COLOR_WHITE)
        screen.blit(t2, t2.get_rect(midtop=(SCREEN_WIDTH // 2, 12)))

        rank = self._player_rank()
        rank_text = f"{rank}/{len(self.racers)}"
        t3 = self.font.render(rank_text, True, COLOR_YELLOW)
        screen.blit(t3, t3.get_rect(topright=(SCREEN_WIDTH - 16, 12)))

        best = MarioKartScene.BEST_LAP
        best_text = f"BEST {best:.2f}" if best is not None else "BEST --"
        t4 = self.font_small.render(best_text, True, COLOR_YELLOW)
        screen.blit(t4, t4.get_rect(topright=(SCREEN_WIDTH - 16, 40)))

        item = self.player.held_item
        item_text = f"ITEM: {item.upper()}" if item else "ITEM: --"
        t5 = self.font_small.render(item_text, True, COLOR_WHITE)
        screen.blit(t5, (16, SCREEN_HEIGHT - 30))
