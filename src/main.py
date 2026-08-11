import sys
import os

# src を import パスに追加（どこから実行しても動くように）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BLACK
from scene_manager import SceneManager
from scenes.menu_scene import MenuScene
from scenes.donkey_kong_scene import DonkeyKongScene
from scenes.tetris_scene import TetrisScene
from scenes.donkey_kong_81_scene import DonkeyKong81Scene
from scenes.ice_climber_scene import IceClimberScene
from scenes.snake_scene import SnakeScene
from scenes.puyo_puyo_scene import PuyoPuyoScene
from scenes.game_over_scene import GameOverScene
from scenes.clear_scene import ClearScene


class GameManager:
    """ゲーム全体を管理する。"""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene_manager = SceneManager()
        self.scene_manager.register_scene("menu", MenuScene())
        self.scene_manager.register_scene("donkey_kong", DonkeyKongScene())
        self.scene_manager.register_scene("tetris", TetrisScene())
        self.scene_manager.register_scene("game_over", GameOverScene())
        self.scene_manager.register_scene("clear", ClearScene())
        self.scene_manager.register_scene("donkey_kong_81", DonkeyKong81Scene())
        self.scene_manager.register_scene("ice_climber", IceClimberScene())
        self.scene_manager.register_scene("snake", SnakeScene())
        self.scene_manager.register_scene("puyo_puyo", PuyoPuyoScene())
        self.scene_manager.change_scene("menu")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ゲーム中は ESC でメニューへ戻る
                self.scene_manager.change_scene("menu")
            else:
                self.scene_manager.handle_input(event)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # フレーム落ち時の物理暴走を防ぐ

            self.handle_events()
            self.scene_manager.update(dt)

            # シーンからの遷移要求を処理
            req = self.scene_manager.current_scene.next_scene
            if req:
                name, kwargs = req
                self.scene_manager.current_scene.next_scene = None
                self.scene_manager.change_scene(name, **kwargs)

            self.screen.fill(COLOR_BLACK)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameManager().run()
