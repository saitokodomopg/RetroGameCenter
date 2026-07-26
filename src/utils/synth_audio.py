"""合成サウンド（SE / BGM）。

numpy 不使用。標準ライブラリ（array / math）でメモリ上に波形を合成し、
pygame.mixer.Sound(buffer=...) として鳴らす。

堅牢性ポリシー（最重要）:
- pygame.mixer.get_init() が None（未初期化・dummy 環境など）の場合、
  すべての play_* は無音の no-op になる。
- 合成・再生のあらゆる例外は握りつぶす。音のせいでゲームを落とさない。

BGM は Milestone A ではスタブ（no-op）。B で簡易シーケンサに拡張する。
音のモチーフはオリジナル（実在楽曲の写しではない）。
"""

import array
import math

import pygame


class SoundBank:
    """合成 SE のバンク。生成に失敗しても無音で動き続ける。"""

    def __init__(self):
        self.enabled = False
        self._sounds = {}
        self._freq = 22050
        self._channels = 2
        try:
            if pygame.mixer.get_init() is None:
                try:
                    pygame.mixer.init()
                except Exception:
                    return
            info = pygame.mixer.get_init()
            if not info:
                return
            freq, size, channels = info
            if abs(int(size)) != 16:
                # 16bit 以外のフォーマットは対象外 → 無音モード
                return
            self._freq = int(freq)
            self._channels = max(1, int(channels))
            self._build_all()
            self.enabled = True
        except Exception:
            self.enabled = False

    # --- 公開 API -----------------------------------------------------
    def play_se(self, name):
        """SE を鳴らす。未知の名前・失敗時は静かに無視。"""
        if not self.enabled:
            return
        try:
            snd = self._sounds.get(name)
            if snd is not None:
                snd.play()
        except Exception:
            pass

    def play_bgm(self, name):
        """BGM 再生（Milestone A ではスタブ＝no-op）。"""
        pass

    def stop_bgm(self):
        """BGM 停止（Milestone A ではスタブ＝no-op）。"""
        pass

    # --- 波形合成 -----------------------------------------------------
    def _build_all(self):
        """全 SE を事前合成する。1 つ失敗してもほかは生かす。"""
        recipes = {
            # ピョン：上昇スイープ
            "jump": ([(300, 640, 0.14)], "square", 0.26),
            # ピロッ：2 音の上がり（+100 獲得）
            "score": ([(880, 880, 0.055), (1320, 1320, 0.09)], "square", 0.24),
            # ヒュ〜…：下降スイープ（ミス）
            "death": ([(620, 90, 0.55)], "triangle", 0.32),
            # タラッタラー：オリジナルの短いファンファーレ（クリア）
            "clear": ([(523, 523, 0.09), (659, 659, 0.09),
                       (784, 784, 0.09), (1047, 1047, 0.22)], "square", 0.26),
            # コッ：ピース左右移動の軽いクリック
            "move": ([(220, 220, 0.03)], "square", 0.16),
            # ピッ：回転の短い上がり
            "rotate": ([(440, 620, 0.05)], "square", 0.20),
            # トッ：ピース設置（着地）の低い音
            "lock": ([(180, 130, 0.07)], "square", 0.22),
            # ピロリン：ライン消去の上昇スイープ
            "line": ([(660, 660, 0.05), (990, 990, 0.05),
                      (1320, 1320, 0.14)], "square", 0.26),
            # ファンッ：レベルアップの上がり2音
            "levelup": ([(784, 784, 0.08), (1175, 1175, 0.16)], "square", 0.26),
            # パキッ：氷を割る短い高音（下降で砕ける感）
            "icebreak": ([(1400, 700, 0.06), (900, 500, 0.05)], "square", 0.22),
            # ポヨン：敵を踏む軽い跳ね音
            "stomp": ([(500, 900, 0.05), (900, 400, 0.06)], "triangle", 0.26),
            # ポン：パドルでボールを打ち返す音
            "paddle_hit": ([(300, 500, 0.045)], "square", 0.24),
            # コツ：壁・天井で跳ね返る軽い音
            "wall_hit": ([(500, 400, 0.035)], "square", 0.18),
            # パリン：ブロックが割れる音
            "brick_break": ([(900, 300, 0.07)], "square", 0.24),
        }
        for name, (segments, wave, vol) in recipes.items():
            try:
                self._sounds[name] = self._synth(segments, wave, vol)
            except Exception:
                pass

    def _synth(self, segments, wave="square", volume=0.3):
        """周波数セグメント列から Sound を合成する。

        segments: [(freq_start, freq_end, duration_sec), ...]
        16bit 符号付きサンプルをチャンネル数分インターリーブして
        Sound(buffer=...) に渡す（mixer のフォーマットに一致させる）。
        """
        sr = self._freq
        amp = int(32767 * volume)
        total = sum(d for _, _, d in segments)
        samples = array.array("h")
        phase = 0.0
        elapsed = 0.0
        two_pi = 2 * math.pi
        for f0, f1, dur in segments:
            n = max(1, int(sr * dur))
            for i in range(n):
                t = i / n
                freq = f0 + (f1 - f0) * t
                phase += two_pi * freq / sr
                if wave == "square":
                    v = 1.0 if math.sin(phase) >= 0 else -1.0
                else:  # triangle
                    v = (2 / math.pi) * math.asin(math.sin(phase))
                # エンベロープ：8ms アタック + 終端へ向けた直線ディケイ
                gt = elapsed + t * dur
                attack = min(1.0, gt / 0.008)
                decay = 1.0 - (gt / total) if total > 0 else 0.0
                val = int(v * attack * decay * amp)
                for _ in range(self._channels):
                    samples.append(val)
            elapsed += dur
        return pygame.mixer.Sound(buffer=samples.tobytes())
