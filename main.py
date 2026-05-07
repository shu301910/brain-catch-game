# ============================================================
# main.py
# ゲームのエントリーポイント
# このファイルを実行するとゲームが起動する
# ============================================================

import os
import sys
import pygame

from config import WIDTH, HEIGHT, FPS
from assets import load_all_images
from score_manager import ScoreManager
from game import Game


def find_japanese_font():
    """OSに応じて日本語フォント名を返す。
    見つからなければNoneを返してデフォルトフォントにフォールバック。"""
    # 試す順番にフォント名を並べる（OS横断で対応）
    candidates = [
        # Windows
        "msgothic",       # MS ゴシック
        "meiryo",         # メイリオ
        "yugothic",       # 游ゴシック
        # Mac
        "hiraginosans",   # ヒラギノ角ゴ
        "hiraginomarugothicpron",
        # Linux
        "notosanscjkjp",  # Noto Sans CJK JP
        "ipagothic",      # IPAゴシック
        "takaogothic",
    ]
    available = pygame.font.get_fonts()  # 利用可能なフォント名リスト（小文字）
    for name in candidates:
        if name in available:
            return name
    return None  # 見つからなかった


def load_decorative_font(size):
    """装飾フォント（Creepster：液体が垂れる風）を読み込む。
    fonts/フォルダに無ければOSのフォント、それも無ければデフォルトに自動フォールバック。"""
    # 1. プロジェクトのfonts/フォルダにあるCreepsterを最優先で使う
    base_dirs = ["fonts", "."]
    candidates = ["Creepster-Regular.ttf"]
    for base in base_dirs:
        for fname in candidates:
            path = os.path.join(base, fname)
            if os.path.exists(path):
                # Creepsterは縦に細長いので、少し大きめのサイズで読み込む
                return pygame.font.Font(path, int(size * 1.2))

    # 2. ファイルが無い場合：OSにある雰囲気のあるフォントを使う
    fallback_candidates = [
        "impact",        # 力強い太字フォント
        "bahnschrift",   # Windows10以降のモダンフォント
        "arial",         # 最終フォールバック
    ]
    available = pygame.font.get_fonts()
    for name in fallback_candidates:
        if name in available:
            return pygame.font.SysFont(name, size, bold=True)

    # 3. それも無ければデフォルト
    return pygame.font.SysFont(None, size, bold=True)


def main():
    """ゲームを実行するメイン関数"""
    # pygame初期化
    pygame.init()

    # ウィンドウ作成
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("脳トレキャッチゲーム")
    clock = pygame.time.Clock()

    # 日本語フォント（タイトル画面の「脳トレキャッチゲーム」用）
    jp_font_name = find_japanese_font()

    # フォントを用意（基本はホラー装飾フォントCreepster、日本語用は別途用意）
    fonts = {
        "font":  load_decorative_font(36),
        "small": load_decorative_font(24),
        "mini":  load_decorative_font(20),
        "big":   load_decorative_font(48),
        # 日本語用（タイトル画面など限定使用）
        "jp_big": pygame.font.SysFont(jp_font_name, 48, bold=True),
    }

    # 画像とハイスコア管理を準備
    images = load_all_images()
    score_manager = ScoreManager()

    # ゲームインスタンス作成
    game = Game(screen, fonts, images, score_manager)

    # メインループ
    while True:
        dt = clock.get_time()

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos)
            if event.type == pygame.KEYDOWN:
                game.handle_keydown(event.key)

        # 状態に応じて更新＆描画
        if game.state == "menu":
            game.draw_menu()
        elif game.state == "mode_select":
            game.draw_mode_select()
        elif game.state == "play":
            keys = pygame.key.get_pressed()
            game.update_play(dt, keys)
            game.draw_play()
        elif game.state == "ranking":
            game.draw_ranking()
        elif game.state == "gameover":
            game.draw_gameover()
        elif game.state == "ending":
            game.draw_ending(dt)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()