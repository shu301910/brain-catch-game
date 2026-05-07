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


def main():
    """ゲームを実行するメイン関数"""
    # pygame初期化
    pygame.init()

    # ウィンドウ作成
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("脳トレキャッチゲーム")
    clock = pygame.time.Clock()

    # 日本語フォントを探す（OS問わず動くように）
    jp_font = find_japanese_font()

    # フォントを用意（用途別に4種類）
    fonts = {
        "font":  pygame.font.SysFont(jp_font, 36),
        "small": pygame.font.SysFont(jp_font, 24),
        "mini":  pygame.font.SysFont(jp_font, 20),
        "big":   pygame.font.SysFont(jp_font, 48),
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