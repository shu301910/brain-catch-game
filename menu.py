# ============================================================
# menu.py
# メニュー・モード選択・ランキング画面を担当するMenuScreenクラス
# ============================================================

import pygame

from config import (
    WIDTH, HEIGHT, PLAY_LEFT,
    BLACK, WHITE, GRAY, GOLD,
    MODE_SOLO1, MODE_SOLO2, MODE_DUO, MODE_COSMIC,
    MODE_LABELS,
)
from assets import format_time


class MenuScreen:
    """メニュー・モード選択・ランキング画面の表示と入力処理を担当。
    画面の状態は state（menu / mode_select / ranking）で管理する。
    プレイ開始時は selected_mode に決定モードがセットされ、
    main.pyがそれを読み取ってゲームを開始する。"""

    def __init__(self, screen, fonts, images, score_manager):
        self.screen        = screen
        self.fonts         = fonts
        self.images        = images
        self.score_manager = score_manager

        # メニュー画面の状態（"menu" / "mode_select" / "ranking"）
        self.state = "menu"

        # 選択肢
        self.mode_options = [MODE_SOLO1, MODE_SOLO2, MODE_DUO, MODE_COSMIC]
        self.ranking_mode = MODE_DUO   # ランキング画面で表示しているモード

        # カーソル位置
        self.menu_cursor = 0   # 0=START, 1=RANKING
        self.mode_cursor = 0   # モード選択のカーソル位置

        # プレイ開始要求：このモードがセットされたら main.py がゲーム開始
        self.selected_mode = None

    # ============================================
    # 状態管理
    # ============================================
    def reset_to_menu(self):
        """ゲーム終了後にメニュー画面へ戻る時に呼ぶ"""
        self.state = "menu"
        self.menu_cursor = 0
        self.selected_mode = None

    def is_play_requested(self):
        """プレイ開始が要求されているか（モードが選ばれた状態）"""
        return self.selected_mode is not None

    def consume_play_request(self):
        """プレイ要求を消費する（main.pyがゲーム開始時に呼ぶ）"""
        mode = self.selected_mode
        self.selected_mode = None
        return mode

    # ============================================
    # 描画ディスパッチ
    # ============================================
    def draw(self):
        """現在の state に応じた画面を描画する"""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "mode_select":
            self.draw_mode_select()
        elif self.state == "ranking":
            self.draw_ranking()

    # ============================================
    # 描画 - メニュー画面
    # ============================================
    def draw_menu(self):
        screen   = self.screen
        big_font = self.fonts["big"]
        font     = self.fonts["font"]

        if self.images["menu_bg"] is not None:
            screen.blit(self.images["menu_bg"], (0, 0))
        else:
            screen.fill(BLACK)

        # 日本語タイトルは専用フォント（Creepsterは日本語非対応のため）
        jp_big_font = self.fonts.get("jp_big", big_font)
        title = jp_big_font.render("脳トレキャッチゲーム", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 90))
        screen.blit(title, title_rect)

        sub = font.render(
            "↑↓ to select   ENTER to decide", True, (220, 220, 220))
        sub_rect = sub.get_rect(center=(WIDTH // 2, 135))
        screen.blit(sub, sub_rect)

        button_x = WIDTH // 2 - 100
        start_y = HEIGHT - 200
        start_color = GOLD if self.menu_cursor == 0 else GRAY
        pygame.draw.rect(screen, start_color,
                         (button_x, start_y, 200, 70), border_radius=10)
        text = font.render("START", True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, start_y + 35))
        screen.blit(text, text_rect)

        rank_btn_y = HEIGHT - 110
        rank_color = GOLD if self.menu_cursor == 1 else GRAY
        pygame.draw.rect(screen, rank_color,
                         (button_x, rank_btn_y, 200, 70), border_radius=10)
        rtext = font.render("RANKING", True, BLACK)
        rtext_rect = rtext.get_rect(center=(WIDTH // 2, rank_btn_y + 35))
        screen.blit(rtext, rtext_rect)

    # ============================================
    # 描画 - モード選択画面
    # ============================================
    def _mode_button_rects(self):
        button_w = 320
        button_h = 70
        button_x = WIDTH // 2 - button_w // 2
        first_y  = 220
        gap      = 90
        rects    = []
        for i, mode in enumerate(self.mode_options):
            rect = pygame.Rect(button_x, first_y + i * gap, button_w, button_h)
            rects.append((mode, rect))
        return rects

    def draw_mode_select(self):
        screen   = self.screen
        big_font = self.fonts["big"]
        font     = self.fonts["font"]
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]

        if self.images["menu_bg"] is not None:
            screen.blit(self.images["menu_bg"], (0, 0))
        else:
            screen.fill(BLACK)

        title = big_font.render("SELECT MODE", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 90))
        screen.blit(title, title_rect)

        sub = font.render(
            "↑↓ to select   ENTER to decide   ( ESC : quit )", True, (220, 220, 220))
        sub_rect = sub.get_rect(center=(WIDTH // 2, 135))
        screen.blit(sub, sub_rect)

        descriptions = {
            MODE_SOLO1: "1 bar / 1 white ball",
            MODE_SOLO2: "2 bars / 2 balls (easier)",
            MODE_DUO:   "2 bars / 2 balls (2 players)",
            MODE_COSMIC: "Cosmic score attack mode",
        }

        for i, (mode, rect) in enumerate(self._mode_button_rects()):
            btn_color = GOLD if i == self.mode_cursor else GRAY
            pygame.draw.rect(screen, btn_color, rect, border_radius=10)
            label = MODE_LABELS.get(mode, mode)
            text  = font.render(label, True, BLACK)
            text_rect = text.get_rect(center=(rect.centerx, rect.y + 25))
            screen.blit(text, text_rect)
            desc = mini_font.render(descriptions.get(mode, ""), True, (60, 60, 60))
            desc_rect = desc.get_rect(center=(rect.centerx, rect.y + 50))
            screen.blit(desc, desc_rect)

        back_hint = small_font.render("BACKSPACE : back to menu", True, GRAY)
        back_rect = back_hint.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(back_hint, back_rect)

    # ============================================
    # 描画 - ランキング画面
    # ============================================
    def draw_ranking(self):
        screen   = self.screen
        big_font = self.fonts["big"]
        font     = self.fonts["font"]
        small_font = self.fonts["small"]

        screen.fill((10, 10, 25))

        tab_w  = 160
        tab_h  = 40
        tab_y  = 10
        tab_gap = 10
        total_tab_w = len(self.mode_options) * tab_w + (len(self.mode_options) - 1) * tab_gap
        tab_start_x = WIDTH // 2 - total_tab_w // 2

        for i, mode in enumerate(self.mode_options):
            tx    = tab_start_x + i * (tab_w + tab_gap)
            trect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            is_active = (mode == self.ranking_mode)
            tab_color = (80, 80, 160) if is_active else (40, 40, 80)
            pygame.draw.rect(screen, tab_color, trect, border_radius=8)
            if is_active:
                pygame.draw.rect(screen, GOLD, trect, 2, border_radius=8)

            label_text = small_font.render(
                MODE_LABELS.get(mode, mode), True,
                GOLD if is_active else GRAY)
            label_rect = label_text.get_rect(center=trect.center)
            screen.blit(label_text, label_rect)

        hint = self.fonts["mini"].render(
            "< / > or 1/2/3/4 to switch mode", True, GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, 62))
        screen.blit(hint, hint_rect)

        title = big_font.render(f"RANKING", True, GOLD)
        title_rect = title.get_rect(center=(WIDTH // 2, 95))
        screen.blit(title, title_rect)

        scores = self.score_manager.get_top(self.ranking_mode)

        if not scores:
            msg = font.render(
                "No records yet. Play to set the first score!", True, WHITE)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(msg, msg_rect)
        else:
            col_centers = {
                "rank":     WIDTH // 2 - 320,
                "score":    WIDTH // 2 - 200,
                "time":     WIDTH // 2 - 60,
                "defeated": WIDTH // 2 + 90,
                "date":     WIDTH // 2 + 250,
            }

            header_y = 135
            headers  = [
                ("rank",     "RANK"),
                ("score",    "SCORE"),
                ("time",     "TIME"),
                ("defeated", "DEFEATED"),
                ("date",     "DATE"),
            ]
            for col_key, label in headers:
                text = small_font.render(label, True, GRAY)
                rect = text.get_rect(center=(col_centers[col_key], header_y))
                screen.blit(text, rect)

            pygame.draw.line(screen, (60, 60, 100),
                             (PLAY_LEFT // 2, 148),
                             (WIDTH - PLAY_LEFT // 2, 148), 1)

            for i, entry in enumerate(scores):
                y    = 170 + i * 38
                rank = i + 1

                if rank == 1:
                    color = GOLD
                elif rank == 2:
                    color = (192, 192, 192)
                elif rank == 3:
                    color = (205, 127, 50)
                else:
                    color = WHITE

                cells = [
                    ("rank",     str(rank)),
                    ("score",    str(entry["score"])),
                    ("time",     format_time(entry["time_ms"])),
                    ("defeated", str(entry["defeated"])),
                    ("date",     entry["date"]),
                ]
                for col_key, value in cells:
                    text = font.render(value, True, color)
                    rect = text.get_rect(center=(col_centers[col_key], y))
                    screen.blit(text, rect)

        button_x = WIDTH // 2 - 100
        button_y = HEIGHT - 80
        pygame.draw.rect(screen, GRAY,
                         (button_x, button_y, 200, 60), border_radius=10)
        btext      = font.render("BACK", True, BLACK)
        btext_rect = btext.get_rect(center=(WIDTH // 2, button_y + 30))
        screen.blit(btext, btext_rect)

    # ============================================
    # 入力処理
    # ============================================
    def handle_click(self, mouse_pos):
        mx, my   = mouse_pos
        button_x = WIDTH // 2 - 100

        if self.state == "menu":
            start_y = HEIGHT - 200
            if (button_x <= mx <= button_x + 200
                    and start_y <= my <= start_y + 70):
                self.state = "mode_select"
                return
            rank_y = HEIGHT - 110
            if (button_x <= mx <= button_x + 200
                    and rank_y <= my <= rank_y + 70):
                self.state = "ranking"
                return

        elif self.state == "mode_select":
            for i, (mode, rect) in enumerate(self._mode_button_rects()):
                if rect.collidepoint(mx, my):
                    self.mode_cursor = i
                    self.selected_mode = mode
                    return

        elif self.state == "ranking":
            tab_w   = 200
            tab_h   = 40
            tab_y   = 10
            tab_gap = 10
            total_tab_w  = len(self.mode_options) * tab_w + (len(self.mode_options) - 1) * tab_gap
            tab_start_x  = WIDTH // 2 - total_tab_w // 2
            for i, mode in enumerate(self.mode_options):
                tx    = tab_start_x + i * (tab_w + tab_gap)
                trect = pygame.Rect(tx, tab_y, tab_w, tab_h)
                if trect.collidepoint(mx, my):
                    self.ranking_mode = mode
                    return

            back_y = HEIGHT - 80
            if (button_x <= mx <= button_x + 200
                    and back_y <= my <= back_y + 60):
                self.state = "menu"
                return

    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.state == "menu":
            if key == pygame.K_UP:
                self.menu_cursor = (self.menu_cursor - 1) % 2
            elif key == pygame.K_DOWN:
                self.menu_cursor = (self.menu_cursor + 1) % 2
            elif key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.menu_cursor == 0:
                    self.state = "mode_select"
                else:
                    self.state = "ranking"
            elif key == pygame.K_r:
                self.state = "ranking"

        elif self.state == "mode_select":
            if key == pygame.K_UP:
                self.mode_cursor = (self.mode_cursor - 1) % len(self.mode_options)
            elif key == pygame.K_DOWN:
                self.mode_cursor = (self.mode_cursor + 1) % len(self.mode_options)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.selected_mode = self.mode_options[self.mode_cursor]
            elif key == pygame.K_1:
                self.selected_mode = self.mode_options[0]
            elif key == pygame.K_2:
                self.selected_mode = self.mode_options[1]
            elif key == pygame.K_3:
                self.selected_mode = self.mode_options[2]
            elif key == pygame.K_4:
                self.selected_mode = self.mode_options[3]
            elif key == pygame.K_BACKSPACE:
                self.state = "menu"

        elif self.state == "ranking":
            if key in (pygame.K_RETURN, pygame.K_BACKSPACE):
                self.state = "menu"
            elif key == pygame.K_LEFT:
                self._cycle_ranking_mode(-1)
            elif key == pygame.K_RIGHT:
                self._cycle_ranking_mode(1)
            elif key == pygame.K_1:
                self.ranking_mode = self.mode_options[0]
            elif key == pygame.K_2:
                self.ranking_mode = self.mode_options[1]
            elif key == pygame.K_3:
                self.ranking_mode = self.mode_options[2]
            elif key == pygame.K_4:
                self.selected_mode = self.mode_options[3]

    def _cycle_ranking_mode(self, delta):
        idx = self.mode_options.index(self.ranking_mode)
        idx = (idx + delta) % len(self.mode_options)
        self.ranking_mode = self.mode_options[idx]