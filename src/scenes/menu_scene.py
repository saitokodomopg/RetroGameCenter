"""メニューシーン。各ゲームのイメージ画像つきカードを並べて選択させる。"""

import math
import pygame
from scenes.base_scene import BaseScene
from scenes.menu_thumbnails import get_thumbnail
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE,
    COLOR_YELLOW, COLOR_RED, COLOR_GIRDER, COLOR_GRAY,
)

# (表示名, シーンキー or None=準備中, サムネイルキー)
# シーンキーが None（準備中）でも、サムネイルキーがあれば専用サムネイルを表示する。
GAMES = [
    ("DONKEY KONG", "donkey_kong", "donkey_kong"),
    ("DONKEY KONG '81", "donkey_kong_81", "donkey_kong_81"),
    ("TETRIS", "tetris", "tetris"),
    ("ICE CLIMBER", "ice_climber", "ice_climber"),
    ("PAC-MAN", None, None),
    ("SNAKE", "snake", "snake"),
    ("PUYO PUYO", "puyo_puyo", "puyo_puyo"),
    ("SPACE INVADERS", None, "space_invaders"),
    ("BREAKOUT", None, "breakout"),
    ("WAGYAN LAND", None, "wagyan_land"),
    ("PINBALL", None, "pinball"),
    ("MARIO KART", None, "mario_kart"),
]

# グリッド設定
# カード枚数が増えたため 4 列に変更し、3 行で画面（600px）に収める。
COLS = 4
CARD_W = 178
CARD_H = 112
GAP_X = 16
GAP_Y = 16
GRID_TOP = 208


class MenuScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_title = pygame.font.Font(None, 76)
        self.font_card = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 26)
        self.selected = 0
        self.time = 0.0

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        n = len(GAMES)
        if event.key == pygame.K_RIGHT:
            self.selected = (self.selected + 1) % n
        elif event.key == pygame.K_LEFT:
            self.selected = (self.selected - 1) % n
        elif event.key == pygame.K_DOWN:
            self.selected = min(self.selected + COLS, n - 1)
        elif event.key == pygame.K_UP:
            self.selected = max(self.selected - COLS, 0)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            scene_key = GAMES[self.selected][1]
            if scene_key:
                self.request_scene(scene_key)

    def update(self, dt):
        self.time += dt

    # --- レイアウト ---------------------------------------------------
    def _grid_origin_x(self):
        total_w = COLS * CARD_W + (COLS - 1) * GAP_X
        return (SCREEN_WIDTH - total_w) // 2

    def _card_rect(self, i):
        col = i % COLS
        row = i // COLS
        # 最終行がCOLS未満なら中央寄せ
        row_count = min(COLS, len(GAMES) - row * COLS)
        row_w = row_count * CARD_W + (row_count - 1) * GAP_X
        ox = (SCREEN_WIDTH - row_w) // 2
        x = ox + col * (CARD_W + GAP_X)
        y = GRID_TOP + row * (CARD_H + GAP_Y)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_border(screen)
        cx = SCREEN_WIDTH // 2

        # タイトル（影付き・上下にゆれる）
        bob = int(math.sin(self.time * 2) * 4)
        title = "RETRO GAME CENTER"
        shadow = self.font_title.render(title, True, COLOR_RED)
        main = self.font_title.render(title, True, COLOR_YELLOW)
        screen.blit(shadow, shadow.get_rect(center=(cx + 3, 95 + bob + 3)))
        screen.blit(main, main.get_rect(center=(cx, 95 + bob)))

        sub = self.font_small.render("- SELECT A GAME -", True, COLOR_WHITE)
        screen.blit(sub, sub.get_rect(center=(cx, 155)))

        for i, (name, key, thumb_key) in enumerate(GAMES):
            self._draw_card(screen, i, name, key, thumb_key)

        # 操作説明（点滅）
        if int(self.time * 2) % 2 == 0:
            hint = self.font_small.render(
                "ARROWS: SELECT     ENTER: PLAY", True, COLOR_WHITE)
            screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 26)))

    def _draw_card(self, screen, i, name, key, thumb_key):
        rect = self._card_rect(i)
        selected = (i == self.selected)
        playable = key is not None
        thumb_h = CARD_H - 34  # 下部にタイトル帯

        # サムネイル（準備中でも専用サムネイルがあれば表示）
        thumb = get_thumbnail(thumb_key, (CARD_W - 8, thumb_h - 4))
        if not playable:
            thumb = thumb.copy()
            thumb.set_alpha(150)
        screen.blit(thumb, (rect.x + 4, rect.y + 4))

        # タイトル帯
        band = pygame.Rect(rect.x, rect.bottom - 30, rect.width, 30)
        band_color = (34, 34, 44) if playable else (24, 24, 30)
        pygame.draw.rect(screen, band_color, band)
        label_color = COLOR_YELLOW if selected else (
            COLOR_WHITE if playable else COLOR_GRAY)
        label = self.font_card.render(name, True, label_color)
        if label.get_width() > rect.width - 10:
            label = self.font_small.render(name, True, label_color)
        screen.blit(label, label.get_rect(center=band.center))

        if not playable:
            cs = self.font_small.render("COMING SOON", True, COLOR_YELLOW)
            screen.blit(cs, cs.get_rect(
                center=(rect.centerx, rect.y + 22)))

        # 枠：選択中は点滅発光、それ以外は控えめ
        if selected:
            glow = 120 + int(abs(math.sin(self.time * 4)) * 135)
            color = (glow, glow, 40)
            pygame.draw.rect(screen, color, rect.inflate(8, 8), 4, border_radius=4)
        else:
            pygame.draw.rect(screen, (70, 70, 85), rect, 2, border_radius=4)

    def _draw_border(self, screen):
        pygame.draw.rect(screen, COLOR_GIRDER,
                         (10, 10, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20), 4)
