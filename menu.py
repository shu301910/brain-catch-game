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
    画面の状態は state（menu / mode_select / ranking / how_to_play）で管理する。
    プレイ開始時は selected_mode に決定モードがセットされ、
    main.pyがそれを読み取ってゲームを開始する。"""

    def __init__(self, screen, fonts, images, score_manager):
        self.screen        = screen
        self.fonts         = fonts
        self.images        = images
        self.score_manager = score_manager

        # メニュー画面の状態（"menu" / "mode_select" / "ranking" / "how_to_play"）
        self.state = "menu"

        # 選択肢
        self.mode_options = [MODE_SOLO1, MODE_SOLO2, MODE_DUO, MODE_COSMIC]
        self.ranking_mode = MODE_DUO   # ランキング画面で表示しているモード

        # カーソル位置
        self.menu_cursor = 0   # 0=START, 1=RANKING
        self.mode_cursor = 0   # モード選択のカーソル位置

        # プレイ開始要求：このモードがセットされたら main.py がゲーム開始
        self.selected_mode = None

        # HOW TO PLAY 画面のスクロール位置（コンテンツの top をどれだけ上に動かしたか）
        self.howto_scroll = 0
        # HOW TO PLAY の全コンテンツ高さ（draw時にセットされる）
        self._howto_content_height = 1
        # スクロール可能エリア（draw時にセット）
        self._howto_view_top    = 0
        self._howto_view_height = 1

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
        elif self.state == "how_to_play":
            self.draw_how_to_play()

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

        # 右下に「?」ヘルプボタン
        self._draw_help_button()

    def _help_button_rect(self):
        """右下の?ボタンの矩形を返す。クリック判定でも共用。"""
        size   = 56
        margin = 24
        return pygame.Rect(WIDTH - margin - size, HEIGHT - margin - size,
                           size, size)

    def _draw_help_button(self):
        """右下の?マーク丸ボタン"""
        screen = self.screen
        rect   = self._help_button_rect()
        cx     = rect.centerx
        cy     = rect.centery
        r      = rect.width // 2

        # 半透明の暗い背景円 → 縁取り → ? 文字
        try:
            surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(surf, (40, 40, 70, 220),
                               (r + 4, r + 4), r)
            pygame.draw.circle(surf, GOLD, (r + 4, r + 4), r, 3)
            screen.blit(surf, (cx - r - 4, cy - r - 4))
        except Exception:
            pygame.draw.circle(screen, (40, 40, 70), (cx, cy), r)
            pygame.draw.circle(screen, GOLD,        (cx, cy), r, 3)

        # ? 記号
        q_font = self.fonts["big"]
        q_text = q_font.render("?", True, GOLD)
        q_rect = q_text.get_rect(center=(cx, cy + 2))
        screen.blit(q_text, q_rect)

        # ラベル（小さく下に）
        mini = self.fonts["mini"]
        lbl  = mini.render("HOW TO PLAY", True, GOLD)
        lbl_rect = lbl.get_rect(center=(cx, cy + r + 14))
        screen.blit(lbl, lbl_rect)

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
    # 描画 - HOW TO PLAY 画面（スクロール可能）
    # ============================================
    def _howto_sections(self):
        """HOW TO PLAY 画面で表示する全セクションをデータとして返す。
        各要素は (kind, payload) のタプル：
          kind="title" / "h2" / "p" / "kv" / "block_legend" / "monster_legend"
        セクションは順番に上から積まれていく。"""
        return [
            ("title", "HOW TO PLAY"),

            # --- ゲームのモード ---
            ("h2", "■ GAME MODES"),
            ("kv", ("1P (1 BAR)",
                    "白いバー1本・白いボール1個で遊ぶ最もシンプルなモード。"
                    "ブロック1個壊すごとに敵にダメージ。")),
            ("kv", ("1P (2 BAR 2 Ball)",
                    "1人で赤バー(A/D)と青バー(←/→)の両方を操作する。"
                    "ボールが2個になり難易度が上がる代わりに、攻撃属性を使い分けられる。")),
            ("kv", ("2P",
                    "二人プレイ用。赤バーは1P(A/D)、青バーは2P(←/→)を担当。"
                    "協力して敵を倒そう。")),
            ("kv", ("COSMIC",
                    "宇宙空間でブロックを壊し続けるスコアアタックモード。")),

            # --- ルール ---
            ("h2", "■ RULES"),
            ("p", "敵モンスターを倒し続け、最後のラスボスを倒すとクリア！"),
            ("p", "敵を倒すごとに次の敵が登場し、9体目を倒すとラスボスが出現します。"),
            ("p", "プレイヤーHPが0になるか、ボールを全て落とすとゲームオーバー。"),
            ("p", "クリアタイムが早いほどスコアボーナスが大きくなります。"),

            # --- 操作方法 ---
            ("h2", "■ CONTROLS"),
            ("kv", ("A / D キー",   "赤バー(1P)を左右に動かす")),
            ("kv", ("← / → キー",   "青バー(2P)を左右に動かす")),
            ("kv", ("SPACE",        "READY?画面：ゲームスタート")),
            ("kv", ("W キー",       "[ビーム発射] 赤バーから上に向けてビームを撃つ "
                                    "(金ブロックを壊して入手したストックを消費)")),
            ("kv", ("↑ キー",       "[ビーム発射] 青バーから上に向けてビームを撃つ")),
            ("kv", ("ESC",          "ゲーム終了")),
            ("kv", ("ENTER",        "ゲームオーバー/エンディング画面でメニューに戻る")),

            # --- ブロック説明 ---
            ("h2", "■ BLOCKS"),
            ("block_legend", "red"),
            ("block_legend", "blue"),
            ("block_legend", "purple"),
            ("block_legend", "invincible"),
            ("block_legend", "gold"),

            # --- ビーム ---
            ("h2", "■ BEAM ATTACK"),
            ("p", "金ブロックを5回当てて壊すと、そのボールの色のバーから"
                  "強力なビームを撃てるようになります。"),
            ("p", "ビームは合計10秒間使用可能。発射中はそのボールが一時停止し、"
                  "ビームが画面上のブロックや敵に持続ダメージを与えます。"),
            ("p", "赤バーは W キー、青バーは ↑ キーで発射(押している間だけ出る)。"),

            # --- モンスター ---
            ("h2", "■ MONSTERS"),
            ("p", "各モンスターは独自の特殊攻撃を持っています。"
                  "倒すと次のモンスターが登場し、9体倒すとラスボスが出現。"),
            ("monster_legend", "red"),
            ("monster_legend", "blue"),
            ("monster_legend", "yellow"),
            ("monster_legend", "green"),
            ("monster_legend", "dark"),
            ("monster_legend", "boss"),

            # --- 戻り方 ---
            ("h2", "■ BACK TO MENU"),
            ("p", "BACKSPACE / ENTER / ESC キー、または下の BACK ボタンで戻れます。"),
        ]

    def _block_legend_data(self, key):
        """ブロック凡例のデータを返す。(色, タイトル, 説明)"""
        from config import (RED, BLUE, PURPLE, INVINCIBLE_BLOCK_COLOR,
                            GOLD_BLOCK_COLOR)
        table = {
            "red":   (RED,    "赤ブロック",
                      "赤ボール or 白ボールで壊せる。壊すと赤バーがブースト＆敵に攻撃。"),
            "blue":  (BLUE,   "青ブロック",
                      "青ボール or 白ボールで壊せる。壊すと青バーがブースト＆敵に攻撃。"),
            "purple": (PURPLE, "紫ブロック",
                      "赤と青の両方を当てる(白なら2回)と破壊。"
                      "壊すとHP回復ストックが+1される(最大2個)。"),
            "invincible": (INVINCIBLE_BLOCK_COLOR, "無敵ブロック",
                      "3回当てると破壊。壊すと10秒間無敵＆攻撃力1.5倍。"
                      "35秒経つと自然消滅。"),
            "gold":  (GOLD_BLOCK_COLOR, "金ブロック",
                      "5回当てると破壊。当たったボール色のバーから"
                      "強力なビームを10秒間撃てるようになる。"),
        }
        return table.get(key)

    def _monster_legend_data(self, key):
        """モンスター凡例のデータを返す。(画像キー, タイトル, 説明)"""
        table = {
            "red":    ("red",    "Red Monster",
                       "赤属性に耐性。特殊攻撃：ボール速度UP(4秒間)。"
                       "画面に爆発エフェクトが出たら要注意。"),
            "blue":   ("blue",   "Blue Monster",
                       "青属性に耐性。特殊攻撃：重力強化(6秒間)。"
                       "ボールが下向きの時だけ加速し、滝が画面に流れる。"),
            "yellow": ("yellow", "Yellow Monster",
                       "特殊攻撃：光ビーム(2〜3本)を画面に落とす。"
                       "黄色フラッシュが出たら避けよう。バーに当たるとダメージ。"),
            "green":  ("green",  "Green Monster",
                       "特殊攻撃：左右の操作が一定時間反転(7秒間)。"
                       "緑フラッシュが予告。葉っぱも同時に落ちてくる。"),
            "dark":   ("dark",   "Dark Monster",
                       "特殊攻撃：ブロックの位置をシャッフル＆バー速度を50%に低下(6秒間)。"),
            "boss":   ("boss",   "★ FINAL BOSS",
                       "9体倒すと登場。全モンスターの特殊攻撃を使用。"
                       "HPが通常の3倍。倒せばクリア！"),
        }
        return table.get(key)

    def draw_how_to_play(self):
        """HOW TO PLAY 画面：スクロール可能な縦長の説明画面"""
        screen     = self.screen
        big_font   = self.fonts["big"]
        font       = self.fonts["font"]
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]

        # 背景
        screen.fill((12, 12, 24))

        # 上のヘッダー / 下のフッターは画面に固定
        HEADER_H = 60
        FOOTER_H = 60
        VIEW_TOP = HEADER_H
        VIEW_H   = HEIGHT - HEADER_H - FOOTER_H
        self._howto_view_top    = VIEW_TOP
        self._howto_view_height = VIEW_H

        # ====== コンテンツを「仮想キャンバス」に描いてからクリップして転写 ======
        # まず必要な高さを試算（行高は固定で計算）
        sections = self._howto_sections()
        content_h = self._howto_layout_height(sections)
        self._howto_content_height = content_h

        # スクロール位置を有効範囲にクランプ
        max_scroll = max(0, content_h - VIEW_H)
        if self.howto_scroll < 0:
            self.howto_scroll = 0
        if self.howto_scroll > max_scroll:
            self.howto_scroll = max_scroll

        # 仮想キャンバス
        canvas = pygame.Surface((WIDTH, content_h), pygame.SRCALPHA)
        self._howto_render_content(canvas, sections)

        # ビューポートにクリップして描画
        viewport_rect = pygame.Rect(0, self.howto_scroll, WIDTH, VIEW_H)
        screen.blit(canvas, (0, VIEW_TOP), viewport_rect)

        # ====== ヘッダー（上の帯：タイトル固定） ======
        header_bar = pygame.Surface((WIDTH, HEADER_H), pygame.SRCALPHA)
        header_bar.fill((20, 20, 40, 240))
        screen.blit(header_bar, (0, 0))
        pygame.draw.line(screen, GOLD, (0, HEADER_H), (WIDTH, HEADER_H), 2)

        t1 = big_font.render("HOW TO PLAY", True, GOLD)
        screen.blit(t1, t1.get_rect(midleft=(40, HEADER_H // 2)))

        scroll_hint = mini_font.render(
            "↑↓ / Mouse Wheel : scroll    BACKSPACE / ESC : back",
            True, (180, 180, 180))
        screen.blit(scroll_hint, scroll_hint.get_rect(
            midright=(WIDTH - 40, HEADER_H // 2)))

        # ====== フッター（下の帯：BACKボタン） ======
        footer_bar = pygame.Surface((WIDTH, FOOTER_H), pygame.SRCALPHA)
        footer_bar.fill((20, 20, 40, 240))
        screen.blit(footer_bar, (0, HEIGHT - FOOTER_H))
        pygame.draw.line(screen, GOLD,
                         (0, HEIGHT - FOOTER_H), (WIDTH, HEIGHT - FOOTER_H), 2)

        back_rect = self._howto_back_button_rect()
        pygame.draw.rect(screen, GRAY, back_rect, border_radius=10)
        btext = font.render("BACK", True, BLACK)
        screen.blit(btext, btext.get_rect(center=back_rect.center))

        # ====== スクロールバー（右端） ======
        self._howto_draw_scrollbar(VIEW_TOP, VIEW_H, content_h)

    def _howto_back_button_rect(self):
        FOOTER_H = 60
        w, h = 160, 44
        x = WIDTH // 2 - w // 2
        y = HEIGHT - FOOTER_H + (FOOTER_H - h) // 2
        return pygame.Rect(x, y, w, h)

    def _howto_draw_scrollbar(self, view_top, view_h, content_h):
        if content_h <= view_h:
            return
        screen = self.screen
        bar_x  = WIDTH - 16
        bar_w  = 8
        # 背景レール
        pygame.draw.rect(screen, (40, 40, 60),
                         (bar_x, view_top + 6, bar_w, view_h - 12),
                         border_radius=4)
        # サム（つまみ）
        ratio    = view_h / content_h
        thumb_h  = max(30, int((view_h - 12) * ratio))
        max_off  = (view_h - 12) - thumb_h
        scroll_r = self.howto_scroll / max(1, content_h - view_h)
        thumb_y  = view_top + 6 + int(max_off * scroll_r)
        pygame.draw.rect(screen, GOLD,
                         (bar_x, thumb_y, bar_w, thumb_h),
                         border_radius=4)

    # ----- HOW TO PLAY コンテンツのレイアウト計算と描画 -----
    # 行高さを「セクションの種類」に応じて固定で決める
    _HOWTO_LINE_H = {
        "title":          70,
        "h2":             56,
        "p":              30,
        "kv":             38,
        "block_legend":   54,
        "monster_legend": 92,
        "spacer_after_h2": 8,
    }
    _HOWTO_PAD_X = 60

    def _howto_layout_height(self, sections):
        """全コンテンツの合計高さを返す（描画前の試算用）"""
        h = 20  # 上の余白
        for kind, payload in sections:
            if kind == "title":
                h += self._HOWTO_LINE_H["title"]
            elif kind == "h2":
                h += self._HOWTO_LINE_H["h2"]
            elif kind == "p":
                # 折り返しを試算（文字数ベース。後で描画関数とロジック共有しても良いが軽量化）
                # 1行あたり概ね46文字 → 折り返し2行までと仮定
                lines = max(1, len(payload) // 46 + 1)
                h += self._HOWTO_LINE_H["p"] * lines
            elif kind == "kv":
                h += self._HOWTO_LINE_H["kv"]
            elif kind == "block_legend":
                h += self._HOWTO_LINE_H["block_legend"]
            elif kind == "monster_legend":
                h += self._HOWTO_LINE_H["monster_legend"]
        h += 40  # 下の余白
        return h

    def _howto_render_content(self, canvas, sections):
        """仮想キャンバスにコンテンツを上から順に描く"""
        from config import RED, BLUE, PURPLE, GOLD as GOLD_C
        big_font   = self.fonts["big"]
        font       = self.fonts["font"]
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]
        # 日本語混じりテキスト用（main.py で用意したフォント）
        jp_small   = self.fonts.get("jp_small", small_font)
        jp_mini    = self.fonts.get("jp_mini",  mini_font)
        jp_font_b  = self.fonts.get("jp_font",  font)

        pad_x = self._HOWTO_PAD_X
        y     = 20

        for kind, payload in sections:
            if kind == "title":
                # 既にヘッダーで描いているのでここではスキップ（高さだけ確保）
                y += self._HOWTO_LINE_H["title"]
            elif kind == "h2":
                # 章タイトル（英語なので装飾フォントでOK）
                surf = font.render(payload, True, GOLD)
                canvas.blit(surf, (pad_x, y))
                # 下線
                pygame.draw.line(canvas, (180, 150, 30),
                                 (pad_x, y + surf.get_height() + 4),
                                 (WIDTH - pad_x, y + surf.get_height() + 4), 1)
                y += self._HOWTO_LINE_H["h2"]
            elif kind == "p":
                # 簡易折り返し（46文字程度）
                lines = self._wrap_text_jp(payload, 46)
                for line in lines:
                    surf = jp_small.render(line, True, WHITE)
                    canvas.blit(surf, (pad_x, y))
                    y += self._HOWTO_LINE_H["p"]
            elif kind == "kv":
                k, v = payload
                # キー：英語ベースなので装飾フォントでも問題ないが
                # 統一感のため jp_small を使う
                ksurf = jp_small.render(k, True, (255, 230, 80))
                canvas.blit(ksurf, (pad_x, y))
                # 値：日本語なので jp_small
                vsurf = jp_small.render(v, True, WHITE)
                canvas.blit(vsurf, (pad_x + 220, y))
                y += self._HOWTO_LINE_H["kv"]
            elif kind == "block_legend":
                self._howto_draw_block_legend(canvas, pad_x, y, payload)
                y += self._HOWTO_LINE_H["block_legend"]
            elif kind == "monster_legend":
                self._howto_draw_monster_legend(canvas, pad_x, y, payload)
                y += self._HOWTO_LINE_H["monster_legend"]

    def _wrap_text_jp(self, text, max_chars):
        """日本語混じりテキストを文字数で簡易折り返し"""
        result = []
        line = ""
        for ch in text:
            line += ch
            if len(line) >= max_chars:
                result.append(line)
                line = ""
        if line:
            result.append(line)
        return result if result else [""]

    def _howto_draw_block_legend(self, canvas, x, y, key):
        """ブロックの凡例を1行描画：[色見本] タイトル — 説明"""
        from config import BLOCK_WIDTH, BLOCK_HEIGHT
        data = self._block_legend_data(key)
        if data is None:
            return
        color, title, desc = data

        # 色見本のブロック
        bw, bh = 60, 24
        pygame.draw.rect(canvas, color, (x, y + 8, bw, bh), border_radius=4)
        if key in ("invincible", "gold"):
            pygame.draw.rect(canvas, WHITE, (x, y + 8, bw, bh), 2, border_radius=4)

        # タイトル・説明（日本語フォント）
        jp_small = self.fonts.get("jp_small", self.fonts["small"])
        jp_mini  = self.fonts.get("jp_mini",  self.fonts["mini"])
        title_surf = jp_small.render(title, True, GOLD)
        canvas.blit(title_surf, (x + bw + 16, y + 4))

        desc_surf = jp_mini.render(desc, True, WHITE)
        canvas.blit(desc_surf, (x + bw + 16, y + 28))

    def _howto_draw_monster_legend(self, canvas, x, y, key):
        """モンスターの凡例を描画：[画像] タイトル — 説明（複数行可）"""
        data = self._monster_legend_data(key)
        if data is None:
            return
        img_key, title, desc = data

        # アイコン（モンスター画像 or プレースホルダー）
        icon_size = 64
        monster_imgs = self.images.get("monsters", {})
        boss_img     = self.images.get("boss")

        img = None
        if img_key == "boss":
            img = boss_img
        else:
            img = monster_imgs.get(img_key)

        if img is not None:
            scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
            canvas.blit(scaled, (x, y + 10))
        else:
            # フォールバック：色付き四角
            color_map = {
                "red":    (200, 60, 60),
                "blue":   (60, 100, 220),
                "yellow": (255, 220, 30),
                "green":  (50, 200, 50),
                "dark":   (80, 60, 50),
                "boss":   (180, 0, 220),
            }
            pygame.draw.rect(canvas, color_map.get(img_key, (80, 80, 80)),
                             (x, y + 10, icon_size, icon_size), border_radius=8)

        # タイトル・説明（日本語フォント）
        jp_small = self.fonts.get("jp_small", self.fonts["small"])
        jp_mini  = self.fonts.get("jp_mini",  self.fonts["mini"])
        title_color = GOLD if img_key != "boss" else (220, 100, 255)
        title_surf  = jp_small.render(title, True, title_color)
        canvas.blit(title_surf, (x + icon_size + 18, y + 8))

        # 説明（折り返し）
        lines = self._wrap_text_jp(desc, 50)
        ly = y + 36
        for line in lines:
            line_surf = jp_mini.render(line, True, WHITE)
            canvas.blit(line_surf, (x + icon_size + 18, ly))
            ly += 22

    # ============================================
    # 入力処理
    # ============================================
    def handle_click(self, mouse_pos):
        mx, my   = mouse_pos
        button_x = WIDTH // 2 - 100

        if self.state == "menu":
            # 右下の?ボタン
            if self._help_button_rect().collidepoint(mx, my):
                self.state = "how_to_play"
                self.howto_scroll = 0
                return
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

        elif self.state == "how_to_play":
            # BACKボタン
            if self._howto_back_button_rect().collidepoint(mx, my):
                self.state = "menu"
                return

    def handle_mousewheel(self, dy):
        """マウスホイールでHOW TO PLAY画面をスクロール"""
        if self.state == "how_to_play":
            # dyは上方向で正、下方向で負
            self.howto_scroll -= dy * 40

    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == "how_to_play":
                self.state = "menu"
                return
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
            elif key in (pygame.K_h, pygame.K_QUESTION, pygame.K_SLASH):
                # h / ? でHOW TO PLAY画面へ
                self.state = "how_to_play"
                self.howto_scroll = 0

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
                self.ranking_mode = self.mode_options[3]

        elif self.state == "how_to_play":
            if key in (pygame.K_BACKSPACE, pygame.K_RETURN):
                self.state = "menu"
            elif key == pygame.K_UP:
                self.howto_scroll -= 40
            elif key == pygame.K_DOWN:
                self.howto_scroll += 40
            elif key == pygame.K_PAGEUP:
                self.howto_scroll -= self._howto_view_height - 40
            elif key == pygame.K_PAGEDOWN:
                self.howto_scroll += self._howto_view_height - 40
            elif key == pygame.K_HOME:
                self.howto_scroll = 0
            elif key == pygame.K_END:
                self.howto_scroll = 10**9   # 次のdrawでクランプされる

    def _cycle_ranking_mode(self, delta):
        idx = self.mode_options.index(self.ranking_mode)
        idx = (idx + delta) % len(self.mode_options)
        self.ranking_mode = self.mode_options[idx]