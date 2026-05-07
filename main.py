# ============================================================
# main.py
# ゲームのエントリーポイント
# このファイルを実行するとゲームが起動する
# ============================================================

import sys
import pygame

from config import WIDTH, HEIGHT, FPS
from assets import load_all_images
from score_manager import ScoreManager
from game import Game


def main():
    """ゲームを実行するメイン関数"""
    # pygame初期化
    pygame.init()

    # ウィンドウ作成
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("脳トレキャッチゲーム")
    clock = pygame.time.Clock()

    # フォントを用意（用途別に4種類）
    fonts = {
        "font": pygame.font.SysFont(None, 36),
        "small": pygame.font.SysFont(None, 24),
        "mini": pygame.font.SysFont(None, 20),
        "big": pygame.font.SysFont(None, 48),
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