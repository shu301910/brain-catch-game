# ============================================================
# catch_game.py
# 既存のキャッチゲーム（ブロック崩し）本体
# プレイ中・ゲームオーバー・エンディングを担当するGameクラス
# （メニュー画面は menu.py の MenuScreen が担当）
# ============================================================

import random
import math
import pygame

from config import (
    WIDTH, HEIGHT, PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT,
    SIDE_WIDTH, TOP_BAR_HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY, RED, BLUE, GREEN, YELLOW, GOLD,
    SIDEBAR_BG, TOPBAR_BG,
    PLAYER_MAX_HP, BLOCK_WIDTH, BLOCK_HEIGHT,
    MAX_RED_BLUE_BLOCKS, MAX_PURPLE_BLOCKS, HEAL_AMOUNT,
    ENEMY_MAX_HP, ENEMY_DAMAGE, ENEMY_SCORE, ENEMY_KILL_SLOWDOWN,
    DAMAGE_NORMAL,
    YELLOW_DYE_DURATION, GREEN_INVERT_DURATION,
    YELLOW_FLASH_DURATION, YELLOW_BEAM_PENDING,
    LIGHT_BEAM_DURATION, LIGHT_BEAM_DAMAGE,
    ENEMY_X, ENEMY_Y, ENEMY_WIDTH, ENEMY_HEIGHT,
    FIRST_SPAWN_DELAY, BLOCK_SPAWN_MIN, BLOCK_SPAWN_MAX,
    GAMEOVER_SHOW_TOP, MONSTER_DEFS,
    MODE_SOLO1, MODE_SOLO2, MODE_DUO, MODE_PARAMS, MODE_LABELS,
    PURPLE_HITS_SOLO1,
    # 新定数
    SOLO1_INITIAL_BALL_SPEED,
    MAX_INVINCIBLE_BLOCKS, INVINCIBLE_BLOCK_HITS, INVINCIBLE_DURATION,
    INVINCIBLE_BLOCK_COLOR,
    PROJECTILE_DAMAGE, MAX_PROJECTILES,
    RED_SPEED_BOOST_MULT, RED_SPEED_BOOST_DURATION,
    DARK_SLOW_MULT, DARK_SLOW_DURATION,
    BLUE_GRAVITY_DURATION, WATERFALL_PARTICLE_COUNT,
    PLAYER_SLOW_WHITE, PLAYER_SLOW_RED, PLAYER_SLOW_BLUE,
    INVERT_FLASH_DURATION,
    # 金ブロック・プレイヤービーム
    GOLD_BLOCK_COLOR, MAX_GOLD_BLOCKS, GOLD_BLOCK_LIFETIME,
    GOLD_BLOCK_HITS, GOLD_BLOCK_SPAWN_MIN, GOLD_BLOCK_SPAWN_MAX,
    PLAYER_BEAM_TOTAL, PLAYER_BEAM_WIDTH, PLAYER_BEAM_HIT_TIME,
    BEAM_BAR_HEIGHT, BEAM_BAR_BG,
    # 2体モード
    DUAL_ENEMY_TRIGGER,
    ENEMY_LEFT_X, ENEMY_RIGHT_X, ENEMY_DUAL_Y, ENEMY_DUAL_W, ENEMY_DUAL_H,
    # ラスボス
    BOSS_TRIGGER, BOSS_X, BOSS_Y, BOSS_W, BOSS_H,
    BOSS_HP_MULT, BOSS_HP_BARS, BOSS_DAMAGE_MULT,
    BOSS_SPECIAL_INTERVAL_MIN, BOSS_SPECIAL_INTERVAL_MAX,
    BOSS_ATTACK_INTERVAL, BOSS_COLOR,
    # 攻撃力アップ（無敵ブロック破壊時）
    ATTACK_BOOST_MULT, ATTACK_BOOST_DURATION,
    # コンボ
    COMBO_DAMAGE_STEP, COMBO_DAMAGE_MAX, COMBO_SCORE_PER,
    COMBO_MIN_DISPLAY, COMBO_PARTICLE_THRESHOLD,
)
from entities import (
    Player, Ball, Block, Enemy,
    Projectile, Explosion, WaterfallParticle, LightBeam,
    Star, Planet,
    PlayerBeam, BeamImpactRing,
    ComboEffect,
    ShockEffect,
)
from assets import format_time


# ============================================================
# ラスボスクラス（5体合体・全特殊攻撃使用）
# ============================================================
class Boss:
    """9体倒した後に登場するラスボス。全特殊攻撃を持つ。"""
    ALL_SPECIALS = ["speed_boost", "gravity", "dye", "invert", "shuffle"]

    def __init__(self, monster_images, boss_image=None):
        self.name   = "boss"
        self.label  = "FINAL BOSS"
        self.resist = None

        self.ex = BOSS_X
        self.ey = BOSS_Y
        self.ew = BOSS_W
        self.eh = BOSS_H

        # 専用画像があればそれを使う、なければ5体合成
        if boss_image is not None:
            self.image = pygame.transform.smoothscale(
                boss_image, (self.ew, self.eh))
        else:
            self._build_image(monster_images)

        base_hp      = ENEMY_MAX_HP * BOSS_HP_MULT
        self.max_hp  = base_hp
        self.hp      = base_hp

        self.attack_timer  = 0
        self.special_timer = 0
        self.next_special  = random.randint(
            BOSS_SPECIAL_INTERVAL_MIN, BOSS_SPECIAL_INTERVAL_MAX)


    def _build_image(self, monster_images):
        """5体の画像をグリッド状に並べた合成画像を作る"""
        names  = ["red", "blue", "yellow", "green", "dark"]
        imgs   = [monster_images.get(n) for n in names]
        cell_w = self.ew // 3
        cell_h = self.eh // 2
        surf   = pygame.Surface((self.ew, self.eh), pygame.SRCALPHA)

        positions = [
            (0, 0), (cell_w, 0), (cell_w * 2, 0),
            (cell_w // 2, cell_h), (cell_w + cell_w // 2, cell_h),
        ]
        for i, img in enumerate(imgs):
            if img is not None:
                scaled = pygame.transform.smoothscale(img, (cell_w, cell_h))
                surf.blit(scaled, positions[i])
        self.image = surf

    def take_damage(self, ball_color, atk_mult=1.0):
        damage = int(DAMAGE_NORMAL * atk_mult)
        self.hp = max(0, self.hp - damage)

    def update(self, dt):
        actions = {"normal_attack": False, "special_attack": False,
                   "special_types": []}

        self.attack_timer += dt
        if self.attack_timer >= BOSS_ATTACK_INTERVAL:
            self.attack_timer = 0
            actions["normal_attack"] = True

        self.special_timer += dt
        if self.special_timer >= self.next_special:
            self.special_timer = 0
            self.next_special  = random.randint(
                BOSS_SPECIAL_INTERVAL_MIN, BOSS_SPECIAL_INTERVAL_MAX)
            actions["special_attack"] = True

            # 通常は1個ランダム、30%の確率で2個同時（重複なし）
            if random.random() < 0.3:
                chosen = random.sample(self.ALL_SPECIALS, 2)
            else:
                chosen = [random.choice(self.ALL_SPECIALS)]
            actions["special_types"] = chosen

        return actions

    def is_dead(self):
        return self.hp <= 0

    def hp_phase(self):
        """現在のHPフェーズ（0=第3バー、1=第2バー、2=第1バー）"""
        ratio = self.hp / self.max_hp
        if ratio > 2 / 3:
            return 0
        elif ratio > 1 / 3:
            return 1
        else:
            return 2

    def draw(self, surface, font, small_font):
        # 紫の枠線
        pygame.draw.rect(surface, BOSS_COLOR,
                         (self.ex - 5, self.ey - 5,
                          self.ew + 10, self.eh + 10), border_radius=8)
        if self.image is not None:
            surface.blit(self.image, (self.ex, self.ey))
        # ラベル
        lbl = font.render("★ FINAL BOSS ★", True, BOSS_COLOR)
        lbl_rect = lbl.get_rect(
            centerx=self.ex + self.ew // 2, top=self.ey - 32)
        surface.blit(lbl, lbl_rect)


class Game:
    """ゲーム本体（プレイ・ゲームオーバー・エンディング）を管理するクラス。
    メニュー画面は menu.py の MenuScreen が担当する。"""

    def __init__(self, screen, fonts, images, score_manager):
        self.screen        = screen
        self.fonts         = fonts
        self.images        = images
        self.score_manager = score_manager

        # ゲーム本体の状態（"play" / "gameover" / "ending" / "idle"）
        # idle = まだ start() が呼ばれていない初期状態
        self.state     = "idle"
        self.last_rank = None

        # 現在のモード（start()で設定される）
        self.mode = MODE_DUO

        # ゲーム終了→メニューに戻るシグナル（main.pyが監視）
        self.finished = False

        # スタート待機フラグ（SPACE待ち）
        self.waiting_start    = False
        self.countdown_timer = 0

        self.score       = 0
        self.score_timer = 0
        self.elapsed_time = 0

        self.block_spawn_timer  = 0
        self.next_block_spawn   = FIRST_SPAWN_DELAY
        self.first_spawn_done   = False

        self.players   = []
        self.balls     = []
        self.blocks    = []
        self.enemy     = None
        self.enemy_right = None   # 2体モード時の右の敵
        self.dual_mode   = False  # 2体モード中フラグ
        self.boss        = None   # ラスボス
        self.boss_mode   = False  # ラスボス戦フラグ
        self.player_hp = PLAYER_MAX_HP

        # 回復ストック（紫ブロック破壊で+1、SPACEキーで使用、最大2個）
        self.heal_stock     = 0
        self.MAX_HEAL_STOCK = 2
        # 使用時の演出用：ストック消費時の光るアニメ用タイマー
        self.heal_use_flash_timer = 0

        # ENDINGアニメーション用
        self.ending_timer    = 0
        self.ending_stars    = []
        self.ending_phase    = 0   # 0=フラッシュ, 1=星爆発, 2=テキスト表示
        self.ending_time_bonus = 0  # クリアタイムボーナス（エンディングで表示用）

        # 既存の状態異常
        self.dye_timer    = 0
        self.invert_timer = 0
        self.invert_flash_timer   = 0  # 緑逆転演出フラッシュ
        self.invert_pending_timer = 0  # 逆転予告カウント（1秒後に逆転発動）

        # 黄色モンスター光ビーム攻撃
        self.yellow_flash_timer   = 0  # 予告フラッシュ
        self.yellow_beam_pending  = 0  # 発動カウントダウン
        self.yellow_beam_count    = 0  # 発動時のビーム本数
        self.light_beams          = [] # 表示中のビームリスト

        # --------- 新しい状態異常 ---------
        # 赤モンスター特殊攻撃：ボール速度UP
        self.speed_boost_timer = 0
        self._speed_boosted    = False

        # 黒モンスター特殊攻撃：バー速度DOWN
        self.slow_timer  = 0
        self._slowed     = False

        # 青モンスター特殊攻撃：重力（下降が速くなる）
        self.gravity_timer = 0

        # 無敵状態（無敵ブロック破壊で発動）
        self.invincible_timer = 0

        # 金ブロック・プレイヤービーム
        self.gold_spawn_timer  = 0
        self.next_gold_spawn   = random.randint(
            GOLD_BLOCK_SPAWN_MIN, GOLD_BLOCK_SPAWN_MAX)
        self.player_beams      = []   # 発射中のビームリスト
        self.beam_remaining    = {}   # {color_name: 残りms}
        self.beam_active       = {}   # {color_name: 今このフレームで発射中か}
        self.beam_impact_rings = []   # 衝撃波リングエフェクト
        self.beam_objects      = {}   # {color_name: PlayerBeamオブジェクト（永続）}

        # 攻撃力アップ（無敵ブロック破壊で発動）
        self.attack_boost_timer = 0
        self._attack_boosted    = False

        # 落下物リスト（葉っぱ・矢）
        self.projectiles = []

        # 爆発エフェクトリスト
        self.explosions = []

        # 滝パーティクルリスト
        self.waterfall_particles = []

        # コンボエフェクト（COMBO x N表示・パーティクル）
        self.combo_effects = []

        # ビリビリエフェクト（黄色稲妻被弾時のバー演出）
        self.shock_effects = []

        # 背景：星・惑星（ゲーム起動時に一度だけ生成）
        self.stars = [Star() for _ in range(60)]
        self._init_planets()

        # 戦績
        self.defeated_count = {m["name"]: 0 for m in MONSTER_DEFS}
        self.defeated_order = []   # 倒した順序リスト（名前を順番に追記）
        self.last_enemy     = None

        # 背景切替用
        self.total_defeated_bg = 0
        self.bg_flash_timer    = 0
        self.BG_FLASH_DURATION = 600
        self.bg_mode           = "space"
        self.current_surface_img = None

    # ============================================
    # リセット
    # ============================================
    def _init_planets(self):
        """惑星を画像がある分だけ生成（最大3枚）。コード描画は使わない。"""
        planet_imgs = self.images.get("planets", [])
        available   = [i for i, img in enumerate(planet_imgs) if img is not None]

        self.planets = []

        count  = min(len(available), 3)
        chosen = random.sample(available, count)
        for i, idx in enumerate(chosen):
            self.planets.append(Planet(image=planet_imgs[idx], style_index=i))

    # ============================================
    # ゲーム開始・終了の外部API
    # （main.pyから呼ばれる）
    # ============================================
    def start(self, mode):
        """指定モードでゲームをスタートする"""
        self.reset(mode=mode)
        self.state    = "play"
        self.finished = False

    def is_finished(self):
        """ゲームが終了してメニューに戻るべき状態か"""
        return self.finished

    def reset(self, mode=None):
        if mode is not None:
            self.mode = mode

        # スコア・時間
        self.score        = 0
        self.score_timer  = 0
        self.elapsed_time = 0

        # ブロックのスポーンタイマー
        self.block_spawn_timer = 0
        self.next_block_spawn  = FIRST_SPAWN_DELAY
        self.first_spawn_done  = False

        # ゲームオブジェクト
        self.blocks      = []
        self.enemy       = None
        self.enemy_right = None   # 2体モード時の右の敵
        self.dual_mode   = False  # 2体モード中フラグ
        self.boss        = None   # ラスボス
        self.boss_mode   = False  # ラスボス戦フラグ
        self.player_hp   = PLAYER_MAX_HP

        # 回復ストックのリセット
        self.heal_stock = 0
        self.heal_use_flash_timer = 0

        # ゲーム開始待ちフラグ
        self.waiting_start = True
        self.countdown_timer = 0

        # 黄色モンスター：ボールの色を染める効果
        self.dye_timer    = 0
        # 緑モンスター：操作が逆転する効果
        self.invert_timer         = 0
        self.invert_flash_timer   = 0  # 逆転前の画面フラッシュ
        self.invert_pending_timer = 0  # フラッシュから逆転発動までの待機時間

        # 黄色モンスター：光ビーム攻撃
        self.yellow_flash_timer  = 0   # 予告フラッシュ
        self.yellow_beam_pending = 0   # 発動カウントダウン
        self.yellow_beam_count   = 0   # 発動時のビーム本数
        self.light_beams         = []  # 表示中のビームリスト

        # 赤モンスター：ボール速度UP
        self.speed_boost_timer = 0
        self._speed_boosted    = False

        # 黒モンスター：バー速度DOWN
        self.slow_timer  = 0
        self._slowed     = False

        # 青モンスター：下降時に速くなる重力効果
        self.gravity_timer = 0

        # 無敵ブロック破壊時：ダメージ無効
        self.invincible_timer = 0

        # 無敵ブロック破壊時：攻撃力アップ
        self.attack_boost_timer = 0
        self._attack_boosted    = False

        # 落下物・エフェクト
        self.projectiles         = []  # 飛んでくる葉っぱなど
        self.explosions          = []  # 爆発エフェクト
        self.waterfall_particles = []  # 滝エフェクト
        self.combo_effects       = []  # コンボエフェクト
        self.shock_effects       = []  # ビリビリエフェクト

        # 金ブロック・プレイヤービーム
        self.gold_spawn_timer  = 0
        self.next_gold_spawn   = random.randint(
            GOLD_BLOCK_SPAWN_MIN, GOLD_BLOCK_SPAWN_MAX)
        self.player_beams      = []
        self.beam_remaining    = {}
        self.beam_active       = {}
        self.beam_impact_rings = []
        self.beam_objects      = {}

        # ランキング関連
        self.last_rank = None

        # 倒した敵の記録・背景演出
        self.defeated_count      = {m["name"]: 0 for m in MONSTER_DEFS}
        self.defeated_order      = []
        self.last_enemy          = None
        self.total_defeated_bg   = 0
        self.bg_flash_timer      = 0
        self.bg_mode             = "space"
        self.current_surface_img = None

        params         = MODE_PARAMS[self.mode]
        speed_up_mult  = params["speed_up_mult"]

        if self.mode == MODE_SOLO1:
            center_x = PLAY_LEFT + (PLAY_WIDTH // 2) - 55
            self.players = [
                Player(center_x, PLAY_TOP + PLAY_HEIGHT - 50,
                       WHITE, "white", pygame.K_a, pygame.K_d),
            ]
            self.players[0].extra_left_key  = pygame.K_LEFT
            self.players[0].extra_right_key = pygame.K_RIGHT
            self.balls = [
                Ball("white", WHITE, speed_up_mult=speed_up_mult,
                     initial_speed=SOLO1_INITIAL_BALL_SPEED),
            ]
        else:
            # solo2 / duo
            self.players = [
                Player(PLAY_LEFT + 100, PLAY_TOP + PLAY_HEIGHT - 100,
                       RED, "red", pygame.K_a, pygame.K_d),
                Player(PLAY_LEFT + 500, PLAY_TOP + PLAY_HEIGHT - 50,
                       BLUE, "blue", pygame.K_LEFT, pygame.K_RIGHT),
            ]
            # 赤のスピードアップ倍率は青の0.7倍に抑える
            red_speed_up_mult = 1.0 + (speed_up_mult - 1.0) * 0.5

            self.balls = [
                Ball("red",  RED,  speed_up_mult=red_speed_up_mult),
                Ball("blue", BLUE, speed_up_mult=speed_up_mult),
            ]

        # ゲームスタートのたびに惑星をランダムで選び直す
        self._init_planets()



    # ============================================
    # ブロック生成
    # ============================================
    def count_blocks(self):
        red_blue    = sum(1 for b in self.blocks if b.type in ("red", "blue"))
        purple      = sum(1 for b in self.blocks if b.type == "purple")
        invincible  = sum(1 for b in self.blocks if b.type == "invincible")
        gold        = sum(1 for b in self.blocks if b.type == "gold")
        return red_blue, purple, invincible, gold

    def spawn_block(self):
        red_blue, purple, invincible, gold = self.count_blocks()

        def find_position():        # ← 一番上に移動
            """既存ブロックと重ならない座標を探す"""
            for _ in range(30):
                x = random.randint(PLAY_LEFT, WIDTH - BLOCK_WIDTH)
                y = random.randint(PLAY_TOP + 50, PLAY_TOP + PLAY_HEIGHT // 2)
                new_rect = pygame.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
                overlap = False
                for block in self.blocks:
                    if new_rect.colliderect(block.rect.inflate(10, 10)):
                        overlap = True
                        break
                if not overlap:
                    return x, y
            return None

        candidates = []
        if red_blue < MAX_RED_BLUE_BLOCKS:
            candidates.extend(["red", "blue"])
        if purple < MAX_PURPLE_BLOCKS:
            candidates.extend(["purple", "purple", "purple"])

        if candidates:
            block_type = random.choice(candidates)
            pos = find_position()
            if pos:
                x, y = pos
                self.blocks.append(Block(x, y, block_type))

        if invincible < MAX_INVINCIBLE_BLOCKS and random.random() < 0.15:
            pos = find_position()
            if pos:
                x, y = pos
                self.blocks.append(Block(x, y, "invincible"))

        # 金ブロックはupdate_blocks_spawnで管理

    def update_blocks_spawn(self, dt):
        self.block_spawn_timer += dt
        if self.block_spawn_timer >= self.next_block_spawn:
            self.spawn_block()
            if not self.first_spawn_done:
                self.enemy = Enemy(self.images["monsters"])
                self.last_enemy_name = self.enemy.name
                self.first_spawn_done = True
            self.block_spawn_timer = 0
            self.next_block_spawn  = random.randint(
                BLOCK_SPAWN_MIN, BLOCK_SPAWN_MAX)
        
        # 金ブロックのスポーンタイマー
        gold = sum(1 for b in self.blocks if b.type == "gold")
        if gold < MAX_GOLD_BLOCKS:
            self.gold_spawn_timer += dt
            if self.gold_spawn_timer >= self.next_gold_spawn:
                self.gold_spawn_timer = 0
                self.next_gold_spawn  = random.randint(
                    GOLD_BLOCK_SPAWN_MIN, GOLD_BLOCK_SPAWN_MAX)
                # 位置を探して出現
                for _ in range(30):
                    x = random.randint(PLAY_LEFT, WIDTH - BLOCK_WIDTH)
                    y = random.randint(PLAY_TOP + 50, PLAY_TOP + PLAY_HEIGHT // 2)
                    new_rect = pygame.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
                    if not any(new_rect.colliderect(b.rect.inflate(10, 10))
                               for b in self.blocks):
                        self.blocks.append(Block(x, y, "gold"))
                        break

        # 金ブロックの寿命処理（15秒で自然消滅）
        for b in self.blocks[:]:
            if b.type == "gold":
                b.gold_lifetime -= dt
                if b.gold_lifetime <= 0:
                    self.blocks.remove(b)

        # 無敵ブロックの寿命処理（35秒で自然消滅）
        for b in self.blocks[:]:
            if b.type == "invincible":
                b.invincible_lifetime -= dt
                if b.invincible_lifetime <= 0:
                    self.blocks.remove(b)

    # ============================================
    # スコア＆時間
    # ============================================
    def update_score_and_time(self, dt):
        self.elapsed_time += dt
        self.score_timer  += dt
        if self.score_timer >= 1000:
            self.score       += 10
            self.score_timer  = 0

    # ============================================
    # 当たり判定
    # ============================================
    def _bounce_ball_off_block(self, ball, block):
        """ボールがブロックのどの面に当たったかを判定して反射させる"""
        ball_rect  = ball.rect
        block_rect = block.rect

        overlap_top    = ball_rect.bottom - block_rect.top
        overlap_bottom = block_rect.bottom - ball_rect.top
        overlap_left   = ball_rect.right  - block_rect.left
        overlap_right  = block_rect.right - ball_rect.left

        min_overlap = min(overlap_top, overlap_bottom, overlap_left, overlap_right)

        if min_overlap == overlap_top and ball.speed_y > 0:
            ball.speed_y *= -1
        elif min_overlap == overlap_bottom and ball.speed_y < 0:
            ball.speed_y *= -1
        elif min_overlap == overlap_left and ball.speed_x > 0:
            ball.speed_x *= -1
        elif min_overlap == overlap_right and ball.speed_x < 0:
            ball.speed_x *= -1
        else:
            ball.speed_y *= -1

    def check_player_ball_collision(self):
        for player, ball in zip(self.players, self.balls):
            # ビーム発射中はそのボールの当たり判定をスキップ
            if self.beam_active.get(ball.color_name):
                continue
            if player.rect.colliderect(ball.rect):
                ball.bounce_on_player(player)

    def check_block_ball_collision(self):
        for ball in self.balls:
            # ビーム発射中はそのボールの当たり判定をスキップ
            if self.beam_active.get(ball.color_name):
                continue
            for block in self.blocks[:]:
                if not ball.rect.colliderect(block.rect):
                    continue
                if not ball.can_hit_block(block):
                    continue
                if block.type == "purple":
                    self._handle_purple_block(ball, block)
                elif block.type == "invincible":
                    self._handle_invincible_block(ball, block)
                elif block.type == "gold":
                    self._handle_gold_block(ball, block)
                else:
                    self._handle_normal_block(ball, block)

    def _handle_purple_block(self, ball, block):
        ball.register_block_hit(block)
        self._bounce_ball_off_block(ball, block)

        # 当たった時点でコンボカウント（壊れる/壊れないに関わらず）
        self._register_combo_hit(ball, block)

        if ball.color_name == "white":
            block.white_hits += 1
            if block.white_hits >= PURPLE_HITS_SOLO1:
                self.blocks.remove(block)
                # 紫破壊：HPストックを+1（上限を超える分は捨てる）
                if self.heal_stock < self.MAX_HEAL_STOCK:
                    self.heal_stock += 1
            return

        if ball.color_name == "red":
            block.red_hit = True
        elif ball.color_name == "blue":
            block.blue_hit = True
        if block.red_hit and block.blue_hit:
            self.blocks.remove(block)
            # 紫破壊：HPストックを+1（上限を超える分は捨てる）
            if self.heal_stock < self.MAX_HEAL_STOCK:
                self.heal_stock += 1

    def _handle_invincible_block(self, ball, block):
        ball.register_block_hit(block)
        self._bounce_ball_off_block(ball, block)

        # 当たった時点でコンボカウント（壊れる/壊れないに関わらず）
        self._register_combo_hit(ball, block)

        block.invincible_hits_left -= 1
        if block.invincible_hits_left <= 0:
            self.blocks.remove(block)
            self.invincible_timer   = INVINCIBLE_DURATION
            self.attack_boost_timer = INVINCIBLE_DURATION  # 無敵と同じ時間
            self._attack_boosted    = True
            # 発動中の特殊攻撃「効果」をキャンセル（演出フラッシュ系は残す）
            self.dye_timer            = 0
            self.invert_timer         = 0
            self.invert_pending_timer = 0
            self.yellow_beam_pending  = 0
            self.light_beams.clear()
            self.projectiles.clear()
            self._cancel_speed_boost()
            self._cancel_slow()
            self._cancel_gravity()

    

    def _handle_gold_block(self, ball, block):
        ball.register_block_hit(block)
        self._bounce_ball_off_block(ball, block)

        # 当たった時点でコンボカウント（壊れる/壊れないに関わらず）
        self._register_combo_hit(ball, block)

        block.gold_hits_left -= 1
        if block.gold_hits_left <= 0:
            self.blocks.remove(block)
            # ボールの色に合わせてビーム権を付与
            color = ball.color_name
            self.beam_remaining[color] = PLAYER_BEAM_TOTAL

    def _handle_invincible_block_destroyed(self):
        """ビームで無敵ブロックを破壊したときの効果発動"""
        self.invincible_timer   = INVINCIBLE_DURATION
        self.attack_boost_timer = INVINCIBLE_DURATION
        self._attack_boosted    = True
        self.dye_timer            = 0
        self.invert_timer         = 0
        self.invert_pending_timer = 0
        self.yellow_beam_pending  = 0
        self.light_beams.clear()
        self.projectiles.clear()
        self._cancel_speed_boost()
        self._cancel_slow()
        self._cancel_gravity()

    def _register_combo_hit(self, ball, block):
        """ボールがブロックに『当たった』時に呼ぶ（壊した・壊さなかったに関わらず）。
        コンボカウントを進め、スコアボーナスと視覚エフェクトを発生させる。
        ※ダメージ倍率はここでは扱わない（赤・青ブロックを実際に壊した時だけ
          _get_combo_damage_mult() で別途取得する）"""
        ball.combo_count += 1
        combo = ball.combo_count

        # スコアボーナス：combo数 × COMBO_SCORE_PER（1連鎖目はゼロ）
        if combo >= 2:
            self.score += combo * COMBO_SCORE_PER

        # 視覚エフェクト：2連鎖以上で「COMBO x N」を表示
        if combo >= COMBO_MIN_DISPLAY:
            bx = block.rect.centerx
            by = block.rect.centery
            with_particles = combo >= COMBO_PARTICLE_THRESHOLD
            self.combo_effects.append(
                ComboEffect(bx, by, combo, with_particles=with_particles))

    def _get_combo_damage_mult(self, ball):
        """現在のコンボ数から敵への攻撃倍率を取得する。
        ※赤・青ブロックを壊して敵にダメージを与える時だけ呼ぶ。
        ※無敵状態（攻撃力アップ）発動中はコンボ倍率を無効化（二重がけ防止）
        ※上限なし：コンボを繋げば繋ぐほど際限なく倍率が上がる"""
        # 無敵状態中はコンボ倍率は使わない
        if self._attack_boosted:
            return 1.0

        combo = ball.combo_count
        if combo >= 2:
            # 上限を撤廃：コンボを繋げただけ倍率が伸び続ける
            return 1.0 + (combo - 1) * COMBO_DAMAGE_STEP
        return 1.0

    def _handle_normal_block(self, ball, block):
        is_white_match = (ball.color_name == "white"
                          and block.type in ("red", "blue"))
        is_color_match = (
            (block.type == "red"  and ball.color_name == "red")  or
            (block.type == "blue" and ball.color_name == "blue")
        )
        if not (is_white_match or is_color_match):
            return

        self.blocks.remove(block)
        ball.register_block_hit(block)
        self._bounce_ball_off_block(ball, block)

        # コンボを進める（カウント+1、スコアボーナス、視覚エフェクト）
        self._register_combo_hit(ball, block)
        # 倍率を取得（無敵中はコンボ倍率は使わない）
        combo_mult = self._get_combo_damage_mult(ball)

        # 攻撃力アップ中なら倍率を適用
        atk_mult = ATTACK_BOOST_MULT if self._attack_boosted else 1.0
        atk_mult *= combo_mult  # コンボ倍率も乗算（無敵中は1.0なので影響なし）

        # ラスボス戦：どのブロックでもボスにダメージ
        if self.boss_mode and self.boss is not None:
            self.boss.take_damage(ball.color_name, atk_mult)
            if self.boss.is_dead():
                self._start_ending()
        # 2体モード時
        elif self.dual_mode and self.enemy_right is not None:
            if block.type == "red" or (ball.color_name == "white" and block.type == "red"):
                target = self.enemy_right
                target_side = "right"
            else:
                target = self.enemy
                target_side = "left"
            target.take_damage(ball.color_name, atk_mult)
            if target.is_dead():
                self._on_enemy_defeated(target, target_side)
        elif self.enemy is not None:
            self.enemy.take_damage(ball.color_name, atk_mult)
            if self.enemy.is_dead():
                self._on_enemy_defeated(self.enemy, "single")

        if ball.color_name == "white":
            if self.players:
                self.players[0].boost()
        elif block.type == "red":
            self.players[0].boost()
        elif block.type == "blue":
            if len(self.players) >= 2:
                self.players[1].boost()

    # ============================================
    # 敵撃破処理
    # ============================================
    def _on_enemy_defeated(self, enemy, side):
        """敵が倒された時の共通処理"""
        self.defeated_count[enemy.name] += 1
        self.defeated_order.append(enemy.name)   # 倒した順序を記録
        self.score += ENEMY_SCORE
        for b in self.balls:
            b.slow_down(ENEMY_KILL_SLOWDOWN)
        self.dye_timer    = 0
        self.invert_timer = 0
        self._cancel_speed_boost()
        self._cancel_gravity()

        total_defeated = sum(self.defeated_count.values())

        # ▼ 規定数倒したらラスボスへ移行
        if total_defeated >= BOSS_TRIGGER and not self.boss_mode:
            self.boss_mode   = True
            self.dual_mode   = False
            self.enemy       = None
            self.enemy_right = None
            self.boss = Boss(self.images["monsters"],
                             boss_image=self.images.get("boss"))
        # 5体倒したら2体モードへ移行
        elif not self.dual_mode and not self.boss_mode and total_defeated >= DUAL_ENEMY_TRIGGER:
            self.dual_mode = True
            self.enemy = Enemy(
                self.images["monsters"],
                ex=ENEMY_LEFT_X, ey=ENEMY_DUAL_Y,
                ew=ENEMY_DUAL_W, eh=ENEMY_DUAL_H,
            )
            self.enemy_right = Enemy(
                self.images["monsters"],
                exclude_name=self.enemy.name,
                ex=ENEMY_RIGHT_X, ey=ENEMY_DUAL_Y,
                ew=ENEMY_DUAL_W, eh=ENEMY_DUAL_H,
            )
            self.last_enemy_name = self.enemy.name
        elif self.dual_mode:
            if side == "left":
                other_name = self.enemy_right.name if self.enemy_right else None
                self.enemy = Enemy(
                    self.images["monsters"],
                    exclude_name=other_name,
                    ex=ENEMY_LEFT_X, ey=ENEMY_DUAL_Y,
                    ew=ENEMY_DUAL_W, eh=ENEMY_DUAL_H,
                )
            elif side == "right":
                other_name = self.enemy.name if self.enemy else None
                self.enemy_right = Enemy(
                    self.images["monsters"],
                    exclude_name=other_name,
                    ex=ENEMY_RIGHT_X, ey=ENEMY_DUAL_Y,
                    ew=ENEMY_DUAL_W, eh=ENEMY_DUAL_H,
                )
        else:
            prev_name = getattr(self, "last_enemy_name", None)
            self.enemy = Enemy(self.images["monsters"], exclude_name=prev_name)
            self.last_enemy_name = self.enemy.name

        # 3体倒すごとに背景を交互切替
        self.total_defeated_bg += 1
        if self.total_defeated_bg % 3 == 0:
            self.bg_flash_timer = self.BG_FLASH_DURATION
            if self.bg_mode == "space":
                surfaces = self.images.get("surfaces", [])
                if surfaces:
                    self.current_surface_img = random.choice(surfaces)
                    self.bg_mode = "surface"
            else:
                self._init_planets()
                self.current_surface_img = None
                self.bg_mode = "space"

    def _projectile_count(self):
        """モードに応じた落下物（緑の葉っぱ）の本数を返す。1P=3本、2P=2本"""
        return 2 if self.mode == MODE_DUO else 3

    def _yellow_beam_count(self):
        """黄色モンスターの光ビーム本数（毎回 2〜3 本のランダム）"""
        return random.randint(2, 3)

    def _spawn_projectile(self, proj_type, count=1):
        for _ in range(count):
            if len(self.projectiles) >= MAX_PROJECTILES:
                break
            x = random.randint(PLAY_LEFT + 10, WIDTH - 30)
            self.projectiles.append(Projectile(x, proj_type))

    def update_projectiles(self, dt):
        for p in self.projectiles[:]:
            p.move()
            if p.is_out():
                self.projectiles.remove(p)
                continue
            for player in self.players:
                if p.active and player.rect.colliderect(p.rect):
                    p.active = False
                    self.projectiles.remove(p)
                    if self.invincible_timer <= 0:
                        self.player_hp -= PROJECTILE_DAMAGE
                        if self.player_hp < 0:
                            self.player_hp = 0
                    break

    def update_player_beams(self, dt, keys):
        """プレイヤービームの発射・当たり判定・残り時間消費を処理する"""
        self.player_beams = []
        self.beam_active  = {}

        for player in self.players:
            color = player.color_name

            # このプレイヤーにビーム残り時間がなければスキップ
            if self.beam_remaining.get(color, 0) <= 0:
                # ビームオブジェクトも破棄
                self.beam_objects.pop(color, None)
                continue

            # ビームキーが押されているか判定
            if color == "white":
                pressing = keys[pygame.K_w] or keys[pygame.K_UP]
            elif color == "red":
                pressing = keys[pygame.K_w]
            else:  # blue
                pressing = keys[pygame.K_UP]

            if not pressing:
                # キーを離したらhit_timersをリセット（当たりカウントをゼロに戻す）
                if color in self.beam_objects:
                    self.beam_objects[color].hit_timers.clear()
                    self.beam_objects[color].white_hit_done.clear()
                continue

            # ビームオブジェクトを永続的に保持（毎フレーム新規生成しない）
            if color not in self.beam_objects:
                self.beam_objects[color] = PlayerBeam(player)
            beam = self.beam_objects[color]

            self.player_beams.append(beam)
            self.beam_active[color] = True

            # 残り時間を消費
            self.beam_remaining[color] = max(
                0, self.beam_remaining[color] - dt)

            # ブロックとの当たり判定
            for block in self.blocks[:]:
                if not beam.rect.colliderect(block.rect):
                    # 当たっていないブロックのタイマーをリセット
                    block_id = id(block)
                    if block_id in beam.hit_timers:
                        del beam.hit_timers[block_id]
                    continue

                block_id = id(block)

                if block.type == "gold":
                    block.gold_hits_left -= 1
                    if block.gold_hits_left <= 0:
                        self.blocks.remove(block)
                    bx = block.rect.centerx
                    by = block.rect.centery
                    self.beam_impact_rings.append(BeamImpactRing(bx, by, color))

                elif block.type in ("red", "blue", "purple"):
                    # 2秒（2000ms）当たり続けると破壊
                    beam.hit_timers[block_id] = \
                        beam.hit_timers.get(block_id, 0) + dt
                    if int(beam.hit_timers.get(block_id, 0)) % 300 < dt + 16:
                        bx = block.rect.centerx
                        by = block.rect.centery
                        self.beam_impact_rings.append(BeamImpactRing(bx, by, color))
                    if beam.hit_timers[block_id] >= PLAYER_BEAM_HIT_TIME:
                        self.blocks.remove(block)
                        # ビーム発射プレイヤーの色を「攻撃属性」として使用
                        # （白ビームはどちらの色のブロックにも有効）
                        atk_mult = ATTACK_BOOST_MULT if self._attack_boosted else 1.0

                        if block.type == "purple":
                            # 紫ブロック → HPストックを+1（上限を超えたら捨てる）
                            if self.heal_stock < self.MAX_HEAL_STOCK:
                                self.heal_stock += 1
                        else:
                            # 赤・青ブロック → 敵にダメージ
                            # 攻撃属性はブロックの色に対応（赤ブロック→赤攻撃、青ブロック→青攻撃）
                            attack_color = block.type  # "red" or "blue"

                            if self.boss_mode and self.boss is not None:
                                self.boss.take_damage(attack_color, atk_mult)
                                if self.boss.is_dead():
                                    self._start_ending()
                            elif self.dual_mode and self.enemy_right is not None:
                                # 2体モード時：赤ブロックは右の敵、青ブロックは左の敵を攻撃
                                if block.type == "red":
                                    target = self.enemy_right
                                    target_side = "right"
                                else:
                                    target = self.enemy
                                    target_side = "left"
                                target.take_damage(attack_color, atk_mult)
                                if target.is_dead():
                                    self._on_enemy_defeated(target, target_side)
                            elif self.enemy is not None:
                                self.enemy.take_damage(attack_color, atk_mult)
                                if self.enemy.is_dead():
                                    self._on_enemy_defeated(self.enemy, "single")

                elif block.type == "invincible":
                    # 2秒（2000ms）当たり続けると1回分カウント
                    beam.hit_timers[block_id] = \
                        beam.hit_timers.get(block_id, 0) + dt
                    if int(beam.hit_timers.get(block_id, 0)) % 300 < dt + 16:
                        bx = block.rect.centerx
                        by = block.rect.centery
                        self.beam_impact_rings.append(BeamImpactRing(bx, by, color))
                    if beam.hit_timers[block_id] >= PLAYER_BEAM_HIT_TIME:
                        beam.hit_timers[block_id] = 0
                        block.invincible_hits_left -= 1
                        if block.invincible_hits_left <= 0:
                            self.blocks.remove(block)
                            self._handle_invincible_block_destroyed()

                elif block.type == "white":
                    if block_id not in beam.white_hit_done:
                        beam.white_hit_done[block_id] = True
                        block.white_hits += 1
                        if block.white_hits >= PURPLE_HITS_SOLO1:
                            self.blocks.remove(block)
                            # 紫扱い：HPストックを+1（上限を超えたら捨てる）
                            if self.heal_stock < self.MAX_HEAL_STOCK:
                                self.heal_stock += 1


    # ============================================
    # 敵の更新
    # ============================================
    def update_enemy(self, dt):
        # ラスボス戦
        if self.boss_mode and self.boss is not None:
            actions = self.boss.update(dt)
            if actions["normal_attack"] and self.invincible_timer <= 0:
                damage_mult = MODE_PARAMS[self.mode]["damage_mult"]
                damage = int(round(ENEMY_DAMAGE * BOSS_DAMAGE_MULT * damage_mult))
                self.player_hp = max(0, self.player_hp - damage)
            if actions["special_attack"]:
                for special_type in actions["special_types"]:
                    self._trigger_special_attack(special_type)
            return

        for enemy in [self.enemy, self.enemy_right]:
            if enemy is None:
                continue
            actions = enemy.update(dt)

            if actions["normal_attack"]:
                if self.invincible_timer <= 0:
                    damage_mult = MODE_PARAMS[self.mode]["damage_mult"]
                    damage = int(round(ENEMY_DAMAGE * damage_mult))
                    if self.dual_mode:
                        damage = max(1, damage // 2)
                    self.player_hp -= damage
                    if self.player_hp < 0:
                        self.player_hp = 0

            if actions["special_attack"]:
                self._trigger_special_attack(enemy.special_type)

    def _trigger_special_attack(self, special_type):
        n = self._projectile_count()
        invincible = self.invincible_timer > 0

        if special_type == "dye":
            # 演出は常に出す
            self.yellow_flash_timer  = YELLOW_FLASH_DURATION
            self.yellow_beam_pending = YELLOW_BEAM_PENDING
            self.yellow_beam_count   = self._yellow_beam_count()  # 毎回 2〜3 本ランダム
            # 効果（染色）は無敵中はスキップ
            if not invincible:
                self.dye_timer = YELLOW_DYE_DURATION

        elif special_type == "invert":
            # 演出は常に出す
            self.invert_flash_timer = INVERT_FLASH_DURATION
            self._spawn_projectile("leaf", count=n)
            # 効果（逆転）は無敵中はスキップ
            if not invincible:
                self.invert_pending_timer = 1000
            else:
                self.invert_pending_timer = 0

        elif special_type == "shuffle":
            for block in self.blocks:
                block.randomize_position()
            if not invincible:
                self._apply_slow()

        elif special_type == "speed_boost":
            cx = random.randint(PLAY_LEFT + 100, WIDTH - 100)
            cy = random.randint(PLAY_TOP + 50, PLAY_TOP + PLAY_HEIGHT // 2)
            self.explosions.append(Explosion(cx, cy))
            for _ in range(2):
                ex = random.randint(PLAY_LEFT + 50, WIDTH - 50)
                ey = random.randint(PLAY_TOP + 30, PLAY_TOP + PLAY_HEIGHT - 80)
                self.explosions.append(Explosion(ex, ey))
            if not invincible:
                self._apply_speed_boost()

        elif special_type == "gravity":
            if not invincible:
                self._apply_gravity()
            else:
                if not self.waterfall_particles:
                    self.waterfall_particles = [
                        WaterfallParticle()
                        for _ in range(WATERFALL_PARTICLE_COUNT)
                    ]

    # --------- 各状態異常の適用／解除 ---------
    def _fire_light_beams(self, count):
        import random as _r
        used_xs = []
        min_gap  = 80
        for _ in range(count):
            for _attempt in range(20):
                x = _r.randint(PLAY_LEFT + 30, PLAY_LEFT + PLAY_WIDTH - 30)
                if all(abs(x - ux) >= min_gap for ux in used_xs):
                    used_xs.append(x)
                    self.light_beams.append(LightBeam(x))
                    break

    def _apply_speed_boost(self):
        if not self._speed_boosted:
            for ball in self.balls:
                ball.speed   *= RED_SPEED_BOOST_MULT
                ball.speed_x *= RED_SPEED_BOOST_MULT
                ball.speed_y *= RED_SPEED_BOOST_MULT
            self._speed_boosted = True
        self.speed_boost_timer = RED_SPEED_BOOST_DURATION

    def _cancel_speed_boost(self):
        if self._speed_boosted:
            for ball in self.balls:
                ball.speed   /= RED_SPEED_BOOST_MULT
                ball.speed_x /= RED_SPEED_BOOST_MULT
                ball.speed_y /= RED_SPEED_BOOST_MULT
            self._speed_boosted    = False
        self.speed_boost_timer = 0

    def _apply_slow(self):
        if not self._slowed:
            for player in self.players:
                player.apply_slow(DARK_SLOW_MULT)
            self._slowed = True
        self.slow_timer = DARK_SLOW_DURATION

    def _cancel_slow(self):
        if self._slowed:
            for player in self.players:
                player.remove_slow()
            self._slowed = False
        self.slow_timer = 0

    def _apply_gravity(self):
        for ball in self.balls:
            ball.gravity_mode = True
        self.gravity_timer = BLUE_GRAVITY_DURATION
        if not self.waterfall_particles:
            self.waterfall_particles = [
                WaterfallParticle()
                for _ in range(WATERFALL_PARTICLE_COUNT)
            ]

    def _cancel_gravity(self):
        for ball in self.balls:
            ball.gravity_mode = False
        self.gravity_timer       = 0
        self.waterfall_particles = []

    # ============================================
    # 状態異常タイマーの更新
    # ============================================
    def update_status_effects(self, dt):
        if self.dye_timer > 0:
            self.dye_timer = max(0, self.dye_timer - dt)
        if self.invert_timer > 0:
            self.invert_timer = max(0, self.invert_timer - dt)
        if self.invert_flash_timer > 0:
            self.invert_flash_timer = max(0, self.invert_flash_timer - dt)

        if self.invert_pending_timer > 0:
            self.invert_pending_timer = max(0, self.invert_pending_timer - dt)
            if self.invert_pending_timer == 0:
                self.invert_timer = GREEN_INVERT_DURATION

        if self.yellow_flash_timer > 0:
            self.yellow_flash_timer = max(0, self.yellow_flash_timer - dt)

        if self.yellow_beam_pending > 0:
            self.yellow_beam_pending = max(0, self.yellow_beam_pending - dt)
            if self.yellow_beam_pending == 0:
                self._fire_light_beams(self.yellow_beam_count)

        for beam in self.light_beams[:]:
            beam.update(dt)
            if not beam.active:
                self.light_beams.remove(beam)
                continue
            if self.invincible_timer <= 0:
                for player in self.players:
                    if beam.rect.colliderect(player.rect):
                        self.player_hp = max(0,
                            self.player_hp - LIGHT_BEAM_DAMAGE)
                        # ビリビリエフェクトを発生（どのバーが当たったか可視化）
                        self.shock_effects.append(ShockEffect(player))
                        beam.active = False
                        self.light_beams.remove(beam)
                        break

        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)

        # 攻撃力アップタイマー
        if self.attack_boost_timer > 0:
            self.attack_boost_timer = max(0, self.attack_boost_timer - dt)
            if self.attack_boost_timer == 0:
                self._attack_boosted = False

        if self.speed_boost_timer > 0:
            self.speed_boost_timer = max(0, self.speed_boost_timer - dt)
            if self.speed_boost_timer == 0:
                self._cancel_speed_boost()

        if self.slow_timer > 0:
            self.slow_timer = max(0, self.slow_timer - dt)
            if self.slow_timer == 0:
                self._cancel_slow()

        if self.gravity_timer > 0:
            self.gravity_timer = max(0, self.gravity_timer - dt)
            if self.gravity_timer == 0:
                self._cancel_gravity()

        for wp in self.waterfall_particles:
            wp.move()

        if self.bg_flash_timer > 0:
            self.bg_flash_timer = max(0, self.bg_flash_timer - dt)

        if self.heal_use_flash_timer > 0:
            self.heal_use_flash_timer = max(0, self.heal_use_flash_timer - dt)

        for ex in self.explosions[:]:
            ex.update(dt)
            if not ex.active:
                self.explosions.remove(ex)

        # ビリビリエフェクトの更新・完了したものを削除
        for se in self.shock_effects:
            se.update(dt)
        self.shock_effects = [s for s in self.shock_effects if not s.done]

        for star in self.stars:
            star.update()
        for planet in self.planets:
            planet.update()

    def _start_ending(self):
        """ラスボス撃破→ENDING演出開始"""
        self._cancel_speed_boost()
        self._cancel_slow()
        self._cancel_gravity()

        # ボス撃破の達成ボーナス（クリアできた事自体への報酬）
        self.score += 1000

        # クリアタイムボーナス（早ければ早いほど大きい）
        # キー点 (秒, ボーナス) を折れ線で結ぶ：
        #   0分    → 5000点
        #   5分    → 1000点
        #   5分半  →  700点
        #   6分    →  570点
        #   6分半  →  500点
        #   7分    →  350点 ← ここを越えるとゼロ
        BONUS_KEYPOINTS = [
            (0,       5000),
            (300_000, 1000),   # 5:00
            (330_000,  700),   # 5:30
            (360_000,  570),   # 6:00
            (390_000,  500),   # 6:30
            (420_000,  350),   # 7:00
        ]
        elapsed = self.elapsed_time
        # 最後のキー点（7分）を超えたら 0
        if elapsed >= BONUS_KEYPOINTS[-1][0]:
            time_bonus = 0
        else:
            # 該当する2点間を線形補間
            time_bonus = BONUS_KEYPOINTS[0][1]   # 念のため初期値
            for i in range(len(BONUS_KEYPOINTS) - 1):
                t0, b0 = BONUS_KEYPOINTS[i]
                t1, b1 = BONUS_KEYPOINTS[i + 1]
                if t0 <= elapsed <= t1:
                    ratio = (elapsed - t0) / (t1 - t0)
                    time_bonus = int(b0 + (b1 - b0) * ratio)
                    break
        self.score += time_bonus
        # エンディング画面で表示するために保持
        self.ending_time_bonus = time_bonus

        # ボスも1体としてカウント
        total_defeated = sum(self.defeated_count.values()) + 1
        self.score_manager.add_score(
            self.mode, self.score, self.elapsed_time, total_defeated)
        self.ending_timer = 0
        self.ending_phase = 0
        self.ending_stars = [
            {
                "x": random.uniform(PLAY_LEFT, WIDTH),
                "y": random.uniform(PLAY_TOP, HEIGHT),
                "vx": random.uniform(-4, 4),
                "vy": random.uniform(-4, 4),
                "size": random.randint(3, 10),
                "color": random.choice([
                    (255, 215, 0), (255, 100, 100), (100, 200, 255),
                    (200, 100, 255), (100, 255, 150), (255, 255, 255),
                ]),
                "life": random.randint(60, 180),
            }
            for _ in range(200)
        ]
        self.state = "ending"

    def draw_ending(self, dt):
        """ENDING画面の描画・アニメーション更新"""
        self.ending_timer += dt
        screen = self.screen

        screen.fill(BLACK)

        if self.ending_timer < 1500:
            ratio = 1.0 - self.ending_timer / 1500
            alpha = int(255 * ratio)
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            screen.blit(flash, (0, 0))

        for s in self.ending_stars[:]:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["life"] -= 1
            if s["life"] <= 0:
                self.ending_stars.remove(s)
                continue
            alpha = min(255, s["life"] * 3)
            try:
                surf = pygame.Surface((s["size"] * 2, s["size"] * 2),
                                      pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (*s["color"], alpha),
                    (s["size"], s["size"]), s["size"])
                screen.blit(surf, (int(s["x"]), int(s["y"])))
            except Exception:
                pass

        if self.ending_timer >= 1500:
            big_font   = self.fonts["big"]
            font       = self.fonts["font"]
            small_font = self.fonts["small"]

            panel = pygame.Surface((700, 380), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 200))
            panel_rect = panel.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(panel, panel_rect)

            cx = WIDTH // 2
            t1 = big_font.render("CONGRATULATIONS!", True, GOLD)
            screen.blit(t1, t1.get_rect(center=(cx, HEIGHT // 2 - 140)))

            pygame.draw.line(screen, GOLD,
                             (cx - 300, HEIGHT // 2 - 105),
                             (cx + 300, HEIGHT // 2 - 105), 2)

            t2 = font.render("FINAL BOSS DEFEATED!", True, BOSS_COLOR)
            screen.blit(t2, t2.get_rect(center=(cx, HEIGHT // 2 - 75)))

            total_defeated = sum(self.defeated_count.values()) + 1
            t3 = font.render(
                f"Score: {self.score}   Enemies: {total_defeated}",
                True, WHITE)
            screen.blit(t3, t3.get_rect(center=(cx, HEIGHT // 2 - 20)))

            t4 = font.render(
                f"Time: {format_time(self.elapsed_time)}", True, WHITE)
            screen.blit(t4, t4.get_rect(center=(cx, HEIGHT // 2 + 25)))

            # クリアタイムボーナス（早ければ早いほど大きい）
            bonus = self.ending_time_bonus
            if bonus >= 2600:        # 3分以内クリアでPERFECT
                bonus_color = GOLD
                bonus_label = f"⚡ TIME BONUS: +{bonus}  (PERFECT!)"
            elif bonus > 0:
                bonus_color = (255, 180, 60)
                bonus_label = f"⚡ TIME BONUS: +{bonus}"
            else:
                bonus_color = GRAY
                bonus_label = "TIME BONUS: ---"
            t5 = font.render(bonus_label, True, bonus_color)
            screen.blit(t5, t5.get_rect(center=(cx, HEIGHT // 2 + 70)))

            pygame.draw.line(screen, GOLD,
                             (cx - 300, HEIGHT // 2 + 105),
                             (cx + 300, HEIGHT // 2 + 105), 2)

            if (self.ending_timer // 600) % 2 == 0:
                t6 = small_font.render(
                    "Press ENTER or click to exit", True, GRAY)
                screen.blit(t6, t6.get_rect(center=(cx, HEIGHT // 2 + 145)))

    # ============================================
    # ゲームオーバー判定
    # ============================================
    def check_game_over(self):
        for ball in self.balls:
            if ball.is_fallen():
                self._end_game()
                return
        if self.player_hp <= 0:
            self._end_game()

    def _end_game(self):
        self.last_enemy = self.enemy

        self._cancel_speed_boost()
        self._cancel_slow()
        self._cancel_gravity()

        total_defeated = sum(self.defeated_count.values())
        self.last_rank = self.score_manager.add_score(
            self.mode, self.score, self.elapsed_time, total_defeated)

        self.state = "gameover"

    # ============================================
    # 回復ストック使用
    # ============================================
    def _consume_heal_stock(self):
        """SPACEキーで呼ばれる。ストックが1個以上ありHPが満タンでなければ
        ストックを1個消費してHEAL_AMOUNTぶんHPを回復する。"""
        if self.heal_stock <= 0:
            return
        if self.player_hp >= PLAYER_MAX_HP:
            # HP満タン時は消費しない（無駄遣い防止）
            return
        self.heal_stock -= 1
        self.player_hp = min(PLAYER_MAX_HP, self.player_hp + HEAL_AMOUNT)
        # 使用フラッシュ演出（HPバーが緑にピカッと光る）
        self.heal_use_flash_timer = 500   # 0.5秒

    # ============================================
    # 描画 - プレイ画面
    # ============================================
    def draw_play(self):
        screen = self.screen
        screen.fill(BLACK)

        if self.bg_mode == "surface" and self.current_surface_img is not None:
            screen.blit(self.current_surface_img, (0, 0))
        else:
            for star in self.stars:
                star.draw(screen)
            for planet in self.planets:
                planet.draw(screen)

        if self.images["sidebar_bg"] is not None:
            screen.blit(self.images["sidebar_bg"], (0, 0))
        else:
            pygame.draw.rect(screen, SIDEBAR_BG, (0, 0, SIDE_WIDTH, HEIGHT))

        pygame.draw.rect(screen, TOPBAR_BG,
                         (PLAY_LEFT, 0, PLAY_WIDTH, TOP_BAR_HEIGHT))

        self._draw_top_bar()
        self._draw_beam_bar()

        

        for wp in self.waterfall_particles:
            wp.draw(screen)

        dye = YELLOW if self.dye_timer > 0 else None
        for block in self.blocks:
            block.draw(screen, dye_color=dye)

        for beam in self.player_beams:   # ← 追加
            beam.draw(screen)            # ← 追加

        # 衝撃波リングを描画
        for ring in self.beam_impact_rings:
            ring.draw(screen)

        for p in self.projectiles:
            p.draw(screen)

        self._draw_players(screen)

        # ビリビリエフェクトをプレイヤーの上に重ねて描画
        for se in self.shock_effects:
            se.draw(screen)

        for ball in self.balls:
            # ビーム発射中はそのボールを非表示
            if self.beam_active.get(ball.color_name):
                continue
            # 黒モンスターの特殊攻撃中はボールを「元の色 ↔ 黒」で点滅
            override_color = None
            if self.slow_timer > 0:
                # 周期350ms（1秒に≒2.85回点滅）の後半は黒色で描画
                period = 350
                if (self.elapsed_time % period) >= period // 2:
                    override_color = BLACK
            ball.draw(screen, override_color=override_color)

        for ex in self.explosions:
            ex.draw(screen)

        # コンボエフェクト（COMBO x N表示・パーティクル）
        combo_font = self.fonts["font"]
        for ce in self.combo_effects:
            ce.draw(screen, combo_font)

        if self.boss_mode and self.boss is not None:
            self.boss.draw(screen, self.fonts["font"], self.fonts["small"])
            self._draw_boss_hp()
        else:
            if self.enemy is not None:
                self.enemy.draw(screen, self.fonts["font"], self.fonts["small"])
                self._draw_enemy_hp(self.enemy, label="LEFT" if self.dual_mode else "Enemy")
            if self.dual_mode and self.enemy_right is not None:
                self.enemy_right.draw(screen, self.fonts["font"], self.fonts["small"])
                self._draw_enemy_hp(self.enemy_right, label="RIGHT", offset_y=0)

        self._draw_player_hp()
        self._draw_status_effects()

        if self.invincible_timer > 0:
            ratio = self.invincible_timer / INVINCIBLE_DURATION
            alpha = int(80 * ratio)
            glow  = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            glow.fill((100, 100, 255, alpha))
            screen.blit(glow, (PLAY_LEFT, PLAY_TOP))
            pygame.draw.rect(screen, INVINCIBLE_BLOCK_COLOR,
                             (PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT),
                             4)

        if self.invert_flash_timer > 0:
            ratio = self.invert_flash_timer / INVERT_FLASH_DURATION
            alpha = int(120 * ratio)
            flash = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            flash.fill((0, 200, 0, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        if self.yellow_flash_timer > 0:
            ratio = self.yellow_flash_timer / YELLOW_FLASH_DURATION
            alpha = int(140 * ratio)
            flash = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 230, 0, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        for beam in self.light_beams:
            beam.draw(screen)

        if self.invert_timer > 0:
            rev_font = self.fonts["big"]
            rev_text = rev_font.render("REVERSE!", True, (0, 255, 80))
            tw = rev_text.get_width()
            th = rev_text.get_height()
            bg = pygame.Surface((tw + 16, th + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            rx = PLAY_LEFT + PLAY_WIDTH // 2 - tw // 2
            ry = PLAY_TOP + PLAY_HEIGHT // 2 - th // 2
            screen.blit(bg, (rx - 8, ry - 4))
            screen.blit(rev_text, (rx, ry))

        if self.bg_flash_timer > 0:
            ratio = self.bg_flash_timer / self.BG_FLASH_DURATION
            alpha = int(180 * ratio)
            flash = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        if self.waiting_start:
            overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (PLAY_LEFT, PLAY_TOP))
            big_font = self.fonts["big"]
            msg1 = big_font.render("READY?", True, WHITE)
            msg1_rect = msg1.get_rect(center=(PLAY_LEFT + PLAY_WIDTH // 2,
                                              PLAY_TOP + PLAY_HEIGHT // 2 - 40))
            screen.blit(msg1, msg1_rect)
            font = self.fonts["font"]
            msg2 = font.render("Press SPACE to Start", True, (220, 220, 100))
            msg2_rect = msg2.get_rect(center=(PLAY_LEFT + PLAY_WIDTH // 2,
                                              PLAY_TOP + PLAY_HEIGHT // 2 + 20))
            screen.blit(msg2, msg2_rect)
            small_font = self.fonts["small"]
            mode_label = MODE_LABELS.get(self.mode, self.mode)
            msg3 = small_font.render(f"Mode: {mode_label}", True, GRAY)
            msg3_rect = msg3.get_rect(center=(PLAY_LEFT + PLAY_WIDTH // 2,
                                              PLAY_TOP + PLAY_HEIGHT // 2 + 60))
            screen.blit(msg3, msg3_rect)

        # カウントダウン表示（3, 2, 1）
        if self.countdown_timer > 0 and not self.waiting_start:
            overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (PLAY_LEFT, PLAY_TOP))

            # 3 → 2 → 1 の数字
            count_num = int(self.countdown_timer // 1000) + 1
            if count_num > 3:
                count_num = 3

            # 1秒ごとに拡大→縮小するアニメーション
            progress = (self.countdown_timer % 1000) / 1000.0  # 1.0 → 0.0
            scale = 1.0 + progress * 1.5   # 大きい状態から縮んでくる
            alpha = int(255 * (0.3 + 0.7 * progress))  # だんだん薄く

            big_font = self.fonts["big"]
            num_surf = big_font.render(str(count_num), True, (255, 230, 80))
            w, h = num_surf.get_size()
            scaled = pygame.transform.smoothscale(
                num_surf, (int(w * scale), int(h * scale)))
            scaled.set_alpha(alpha)
            rect = scaled.get_rect(center=(PLAY_LEFT + PLAY_WIDTH // 2,
                                        PLAY_TOP + PLAY_HEIGHT // 2))
            screen.blit(scaled, rect)

        # 境界線は全ての描画が終わった最後に上書きで引く（何にも消されない）
        pygame.draw.line(screen, WHITE, (PLAY_LEFT, 0), (PLAY_LEFT, HEIGHT), 2)
        pygame.draw.line(screen, WHITE,
                         (PLAY_LEFT, TOP_BAR_HEIGHT), (WIDTH, TOP_BAR_HEIGHT), 1)
        pygame.draw.line(screen, WHITE,
                         (PLAY_LEFT, PLAY_TOP), (WIDTH, PLAY_TOP), 2)

    def _draw_players(self, screen):
        inverted = self.invert_timer > 0
        slowed   = self._slowed

        for player in self.players:
            if inverted and len(self.players) >= 2:
                override = BLUE if player.color_name == "red" else RED
            elif slowed:
                if player.color_name == "white":
                    override = PLAYER_SLOW_WHITE
                elif player.color_name == "red":
                    override = PLAYER_SLOW_RED
                else:
                    override = PLAYER_SLOW_BLUE
            else:
                override = None
            player.draw(screen, override_color=override)

    def _draw_top_bar(self):
        font = self.fonts["font"]
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (PLAY_LEFT + 30, 12))

        time_text  = font.render(
            f"Time: {format_time(self.elapsed_time)}", True, WHITE)
        time_rect  = time_text.get_rect()
        time_rect.topright = (WIDTH - 30, 12)
        self.screen.blit(time_text, time_rect)

        time_text  = font.render(
            f"Time: {format_time(self.elapsed_time)}", True, WHITE)
        time_rect  = time_text.get_rect()
        time_rect.topright = (WIDTH - 30, 12)
        self.screen.blit(time_text, time_rect)

        # 倒したモンスターのアイコンをスコアの右から順番に表示
        icon_size      = 36
        icon_gap       = 4
        monster_images = self.images.get("monsters", {})
        mini_font      = self.fonts["mini"]

        icon_y   = (TOP_BAR_HEIGHT - icon_size) // 2
        start_x  = PLAY_LEFT + 30 + score_text.get_width() + 16  # スコアテキストの右端から

        for i, name in enumerate(self.defeated_order):
            x   = start_x + i * (icon_size + icon_gap)
            # はみ出したら表示しない（タイムと重ならないよう）
            if x + icon_size > time_rect.left - 10:
                break
            img = monster_images.get(name)
            if img is not None:
                scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                self.screen.blit(scaled, (x, icon_y))
            else:
                pygame.draw.rect(self.screen, GRAY,
                                 (x, icon_y, icon_size, icon_size), border_radius=4)

    def _draw_beam_bar(self):
        """トップバーとプレイエリアの間にビーム残量バーを描画"""
        screen = self.screen
        mini_font = self.fonts["mini"]

        # バーの背景
        pygame.draw.rect(screen, BEAM_BAR_BG,
                        (PLAY_LEFT, TOP_BAR_HEIGHT, PLAY_WIDTH, BEAM_BAR_HEIGHT))
        pygame.draw.line(screen, WHITE,
                        (PLAY_LEFT, TOP_BAR_HEIGHT + BEAM_BAR_HEIGHT),
                        (WIDTH, TOP_BAR_HEIGHT + BEAM_BAR_HEIGHT), 1)

        # プレイヤーごとにビーム残量を表示
        slot_w = PLAY_WIDTH // max(len(self.players), 1)
        for i, player in enumerate(self.players):
            color = player.color_name
            remaining = self.beam_remaining.get(color, 0)
            if remaining <= 0:
                continue

            slot_x = PLAY_LEFT + i * slot_w
            bar_w  = int(slot_w * remaining / PLAYER_BEAM_TOTAL)

            # 発射中は明るく、待機中は暗く
            if self.beam_active.get(color):
                bar_color = player.color
            else:
                # 少し暗くする
                bar_color = tuple(max(0, c // 2) for c in player.color)

            pygame.draw.rect(screen, bar_color,
                            (slot_x, TOP_BAR_HEIGHT + 2,
                            bar_w, BEAM_BAR_HEIGHT - 4),
                            border_radius=3)

            # 残り秒数テキスト
            secs = remaining / 1000
            label = mini_font.render(
                f"BEAM {secs:.1f}s", True, WHITE)
            screen.blit(label, (slot_x + 4, TOP_BAR_HEIGHT + 3))

    def _draw_boss_hp(self):
        screen     = self.screen
        small_font = self.fonts["small"]
        boss       = self.boss

        bar_x = BOSS_X
        bar_y = BOSS_Y + BOSS_H + 10
        bar_w = SIDE_WIDTH - 20   # サイドバー内に収める（390→380）
        bar_h = 14
        gap   = 6

        phase_colors = [
            (255, 80,  80),
            (255, 165,  0),
            (180,  0, 220),
        ]
        total_ratio = boss.hp / boss.max_hp

        for i in range(BOSS_HP_BARS):
            by = bar_y + i * (bar_h + gap)
            phase = BOSS_HP_BARS - 1 - i
            bar_min = phase / BOSS_HP_BARS
            bar_max = (phase + 1) / BOSS_HP_BARS

            if total_ratio >= bar_max:
                fill = 1.0
            elif total_ratio <= bar_min:
                fill = 0.0
            else:
                fill = (total_ratio - bar_min) / (bar_max - bar_min)

            pygame.draw.rect(screen, WHITE,
                             (bar_x - 2, by - 2, bar_w + 4, bar_h + 4),
                             border_radius=4)
            pygame.draw.rect(screen, DARK_GRAY,
                             (bar_x, by, bar_w, bar_h), border_radius=3)
            if fill > 0:
                pygame.draw.rect(screen, phase_colors[i],
                                 (bar_x, by, int(bar_w * fill), bar_h),
                                 border_radius=3)
            # ラベルはバー左端の内側に白文字で配置（はみ出し防止）
            label = small_font.render(f"HP {BOSS_HP_BARS - i}", True, WHITE)
            screen.blit(label, (bar_x + 6, by - 2))

        total_text = small_font.render(
            f"{boss.hp} / {boss.max_hp}", True, WHITE)
        screen.blit(total_text,
                    (bar_x, bar_y + BOSS_HP_BARS * (bar_h + gap) + 2))

    def _draw_enemy_hp(self, enemy, label="Enemy", offset_y=0):
        screen     = self.screen
        small_font = self.fonts["small"]
        bar_x = enemy.ex
        bar_y = enemy.ey + enemy.eh + 8 + offset_y
        bar_w = enemy.ew
        bar_h = 14

        panel = pygame.Surface((bar_w + 20, bar_h + 35), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        screen.blit(panel, (bar_x - 10, bar_y - 5))

        pygame.draw.rect(screen, WHITE,
                         (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4),
                         border_radius=4)
        pygame.draw.rect(screen, GRAY,
                         (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        hp_ratio = enemy.hp / enemy.max_hp
        pygame.draw.rect(screen, RED,
                         (bar_x, bar_y, int(bar_w * hp_ratio), bar_h),
                         border_radius=3)
        text = small_font.render(
            f"{label} HP: {enemy.hp}/{enemy.max_hp}", True, WHITE)
        screen.blit(text, (bar_x, bar_y + bar_h + 3))

    def _draw_player_hp(self):
        screen     = self.screen
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]
        bar_x = ENEMY_X
        bar_w = ENEMY_WIDTH
        bar_h = 18
 
        # ハートサイズ（大きめに）
        heart_size = 28
        heart_gap  = 10
 
        # レイアウト計算（上から順）：
        #   [Your HP ラベル][ハート列]
        #   [HP バー本体]
        #   [HP テキスト 100/100]
        # を1つのパネルに収める
 
        # HPバーの位置をベースに決める（画面下から余裕を持って配置）
        bar_y = HEIGHT - 90
 
        # ハート行のY座標（HPバーの上に配置）
        heart_y = bar_y - heart_size - 12
 
        # ラベル "Your HP" のY座標（ハートと同じ行の左側）
        label_y = heart_y + (heart_size - small_font.get_height()) // 2
 
        # パネル全体の範囲
        panel_top    = heart_y - 8
        panel_bottom = bar_y + bar_h + small_font.get_height() + 10
        panel_h      = panel_bottom - panel_top
        panel = pygame.Surface((bar_w + 20, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        screen.blit(panel, (bar_x - 10, panel_top))
 
        # "Your HP" ラベル
        label = small_font.render("Your HP", True, WHITE)
        screen.blit(label, (bar_x, label_y))
 
        # ハート2個（HPバーの右寄せ）
        total_hearts_w = self.MAX_HEAL_STOCK * heart_size + (self.MAX_HEAL_STOCK - 1) * heart_gap
        hearts_start_x = bar_x + bar_w - total_hearts_w
        for i in range(self.MAX_HEAL_STOCK):
            hx = hearts_start_x + i * (heart_size + heart_gap)
            filled = (i < self.heal_stock)
            self._draw_heart(hx, heart_y, heart_size, filled)
 
        # HPバー本体
        # 使用時フラッシュ：HPバーが緑→白くピカッと光る
        if self.heal_use_flash_timer > 0:
            ratio = self.heal_use_flash_timer / 500
            r = int(0   + (255 - 0)   * ratio)
            g = 255
            b = int(0   + (255 - 0)   * ratio)
            hp_color = (r, g, b)
        else:
            hp_color = INVINCIBLE_BLOCK_COLOR if self.invincible_timer > 0 else GREEN
 
        pygame.draw.rect(screen, WHITE,
                         (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4),
                         border_radius=4)
        pygame.draw.rect(screen, GRAY,
                         (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        hp_ratio = self.player_hp / PLAYER_MAX_HP
        pygame.draw.rect(screen, hp_color,
                         (bar_x, bar_y, int(bar_w * hp_ratio), bar_h),
                         border_radius=3)
        text = small_font.render(
            f"{self.player_hp}/{PLAYER_MAX_HP}", True, WHITE)
        screen.blit(text, (bar_x, bar_y + bar_h + 5))
 
    def _draw_heart(self, x, y, size, filled):
        """ハート型を描画。filled=Trueなら赤、Falseならグレー枠だけ。
        描画範囲は (x, y) から (x+size, y+size) の正方形内に収まる。"""
        screen = self.screen
        s = size
 
        if filled:
            color   = (235, 60, 90)   # 赤
            outline = (255, 255, 255)
        else:
            color   = (40, 40, 50)    # 暗いグレー（空ストック）
            outline = (160, 160, 170)
 
        # ハート形：左右2つの円＋下向き三角の組み合わせ
        # サイズ s の正方形 (x, y)-(x+s, y+s) に綺麗に収まるよう調整
        r = s // 4                        # 上部の丸の半径
        lobe_y = y + r + 2                # 丸の中心Y（少し下げる）
        left_cx  = x + r + 1
        right_cx = x + s - r - 1
 
        # 下の三角（ハートの先端）
        tri_pts = [
            (x + 1,     lobe_y),
            (x + s - 1, lobe_y),
            (x + s // 2, y + s - 1),      # 先端は底辺ギリギリまで
        ]
 
        # 左の丸
        pygame.draw.circle(screen, color, (left_cx,  lobe_y), r)
        # 右の丸
        pygame.draw.circle(screen, color, (right_cx, lobe_y), r)
        # 三角
        pygame.draw.polygon(screen, color, tri_pts)
 
        # 空ストック時は輪郭を描く
        if not filled:
            pygame.draw.circle(screen, outline, (left_cx,  lobe_y), r, 2)
            pygame.draw.circle(screen, outline, (right_cx, lobe_y), r, 2)
            pygame.draw.polygon(screen, outline, tri_pts, 2)
        else:
            # 塗りハートにも軽くハイライト枠で立体感
            pygame.draw.circle(screen, outline, (left_cx,  lobe_y), r, 1)
            pygame.draw.circle(screen, outline, (right_cx, lobe_y), r, 1)
            pygame.draw.polygon(screen, outline, tri_pts, 1)

    def _draw_status_effects(self):
        screen    = self.screen
        mini_font = self.fonts["mini"]
        effects   = []

        if self.dye_timer > 0:
            effects.append((f"DYE: {self.dye_timer // 1000 + 1}s", YELLOW))
        if self.invert_timer > 0:
            effects.append((f"INVERT: {self.invert_timer // 1000 + 1}s", GREEN))
        if self.speed_boost_timer > 0:
            effects.append((f"SPEED UP!: {self.speed_boost_timer // 1000 + 1}s",
                            (255, 120, 0)))
        if self.slow_timer > 0:
            effects.append((f"BAR SLOW: {self.slow_timer // 1000 + 1}s",
                            (180, 180, 255)))
        if self.gravity_timer > 0:
            effects.append((f"GRAVITY: {self.gravity_timer // 1000 + 1}s",
                            (80, 180, 255)))
        if self.invincible_timer > 0:
            effects.append((f"INVINCIBLE: {self.invincible_timer // 1000 + 1}s",
                            INVINCIBLE_BLOCK_COLOR))
        if self.attack_boost_timer > 0:
            effects.append((f"ATK x1.5: {self.attack_boost_timer // 1000 + 1}s",
                            GOLD))

        if not effects:
            return

        y       = HEIGHT - 130 - (len(effects) - 1) * 22
        panel_h = len(effects) * 22 + 8
        panel   = pygame.Surface((155, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        screen.blit(panel, (5, y - 4))

        for i, (msg, color) in enumerate(effects):
            text = mini_font.render(msg, True, color)
            screen.blit(text, (10, y + i * 22))

    # ============================================
    # 描画 - ゲームオーバー画面
    # ============================================
    def draw_gameover(self):
        screen   = self.screen
        big_font = self.fonts["big"]
        font     = self.fonts["font"]
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]

        if self.images["gameover_bg"] is not None:
            screen.blit(self.images["gameover_bg"], (0, 0))
        else:
            screen.fill(BLACK)
            title = big_font.render("GAME OVER", True, (250, 80, 80))
            title_rect = title.get_rect(center=(WIDTH // 2, 200))
            screen.blit(title, title_rect)
            sub = small_font.render("PRESS ENTER TO CONTINUE", True, WHITE)
            sub_rect = sub.get_rect(center=(WIDTH // 2, 260))
            screen.blit(sub, sub_rect)

        self._draw_gameover_score_panel()
        self._draw_defeated_panel()
        self._draw_last_enemy_panel()
        self._draw_gameover_top3()

    def _draw_gameover_score_panel(self):
        screen     = self.screen
        font       = self.fonts["font"]
        small_font = self.fonts["small"]

        panel_center_y = HEIGHT // 2 + 110
        panel_w, panel_h = 320, 120
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        panel_rect = panel.get_rect(center=(WIDTH // 2, panel_center_y))
        screen.blit(panel, panel_rect)

        score_text = font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(
            center=(WIDTH // 2, panel_center_y - 25))
        screen.blit(score_text, score_rect)

        time_text  = font.render(
            f"Time: {format_time(self.elapsed_time)}", True, WHITE)
        time_rect  = time_text.get_rect(
            center=(WIDTH // 2, panel_center_y + 15))
        screen.blit(time_text, time_rect)

        if self.last_rank is not None:
            rank_color = GOLD if self.last_rank <= 3 else WHITE
            rank_text  = small_font.render(
                f"NEW RANK: #{self.last_rank}", True, rank_color)
            rank_rect  = rank_text.get_rect(
                center=(WIDTH // 2, panel_center_y + 45))
            screen.blit(rank_text, rank_rect)

    def _draw_defeated_panel(self):
        screen       = self.screen
        small_font   = self.fonts["small"]
        mini_font    = self.fonts["mini"]
        monster_images = self.images["monsters"]

        panel_x = 20
        panel_y = HEIGHT - 240
        panel_w = 220
        panel_h = 220

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        screen.blit(panel, (panel_x, panel_y))

        title = small_font.render("Defeated Enemies", True, GOLD)
        title_rect = title.get_rect(
            center=(panel_x + panel_w // 2, panel_y + 18))
        screen.blit(title, title_rect)

        item_h    = 30
        start_y   = panel_y + 34
        icon_size = 26

        for i, monster in enumerate(MONSTER_DEFS):
            row_y = start_y + i * item_h
            count = self.defeated_count.get(monster["name"], 0)

            img = monster_images.get(monster["name"])
            if img is not None:
                small_img = pygame.transform.smoothscale(
                    img, (icon_size, icon_size))
                screen.blit(small_img, (panel_x + 15, row_y))
            else:
                color = self._monster_label_color(monster["name"])
                pygame.draw.rect(screen, color,
                                 (panel_x + 15, row_y, icon_size, icon_size))

            label = mini_font.render(monster["label"], True, WHITE)
            screen.blit(label, (panel_x + 50, row_y + 5))

            count_text = small_font.render(f"× {count}", True, WHITE)
            screen.blit(count_text, (panel_x + panel_w - 60, row_y + 3))

        total = sum(self.defeated_count.values())
        total_text = small_font.render(f"Total: {total}", True, GOLD)
        total_rect = total_text.get_rect(
            center=(panel_x + panel_w // 2, panel_y + panel_h - 18))
        screen.blit(total_text, total_rect)

    def _monster_label_color(self, name):
        if name == "red":
            return RED
        if name == "blue":
            return BLUE
        if name == "yellow":
            return YELLOW
        if name == "green":
            return GREEN
        return (80, 60, 50)

    def _draw_last_enemy_panel(self):
        screen     = self.screen
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]

        if self.last_enemy is None:
            return

        panel_w = 220
        panel_h = 220
        panel_x = WIDTH - 20 - panel_w
        panel_y = HEIGHT - 240

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        screen.blit(panel, (panel_x, panel_y))

        title = small_font.render("Defeated By", True, (255, 100, 100))
        title_rect = title.get_rect(
            center=(panel_x + panel_w // 2, panel_y + 18))
        screen.blit(title, title_rect)

        img = self.last_enemy.image
        if img is not None:
            display_size = 120
            small_img    = pygame.transform.smoothscale(
                img, (display_size, display_size))
            img_x = panel_x + (panel_w - display_size) // 2
            img_y = panel_y + 40
            screen.blit(small_img, (img_x, img_y))
        else:
            color = self._monster_label_color(self.last_enemy.name)
            pygame.draw.rect(screen, color,
                             (panel_x + 50, panel_y + 50, 120, 120))

        label = small_font.render(self.last_enemy.label, True, WHITE)
        label_rect = label.get_rect(
            center=(panel_x + panel_w // 2, panel_y + 175))
        screen.blit(label, label_rect)

        if self.last_enemy.resist:
            resist_color = (RED if self.last_enemy.resist == "red" else BLUE)
            resist_text  = mini_font.render(
                f"Resist: {self.last_enemy.resist.upper()}", True, resist_color)
        else:
            resist_text = mini_font.render("Resist: NONE", True, WHITE)
        resist_rect = resist_text.get_rect(
            center=(panel_x + panel_w // 2, panel_y + 200))
        screen.blit(resist_text, resist_rect)

    def _draw_gameover_top3(self):
        screen     = self.screen
        small_font = self.fonts["small"]
        mini_font  = self.fonts["mini"]

        scores = self.score_manager.get_top(self.mode, GAMEOVER_SHOW_TOP)
        if not scores:
            return

        panel_w = 380
        panel_h = 30 + len(scores) * 25 + 22
        panel_x = WIDTH - panel_w - 20
        panel_y = 20

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        screen.blit(panel, (panel_x, panel_y))

        mode_label = MODE_LABELS.get(self.mode, "")
        title = small_font.render(f"TOP 3  ({mode_label})", True, GOLD)
        screen.blit(title, (panel_x + 10, panel_y + 5))

        for i, entry in enumerate(scores):
            rank = i + 1
            if self.last_rank == rank:
                color  = (255, 255, 100)
                marker = "▶ "
            else:
                color  = WHITE
                marker = "  "

            line = (f"{marker}{rank}. "
                    f"Score:{entry['score']:>4}  "
                    f"Time:{format_time(entry['time_ms'])}  "
                    f"Def:{entry['defeated']}")
            text = mini_font.render(line, True, color)
            screen.blit(text, (panel_x + 10, panel_y + 30 + i * 25))

    # ============================================
    # イベント処理
    # ============================================
    def handle_click(self, mouse_pos):
        # gameover / ending 画面でクリックされたら「終了」フラグを立てる
        # （main.py がこれを検知してメニュー画面に戻す）
        if self.state in ("gameover", "ending"):
            self.finished = True

    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.state == "play":
            if self.waiting_start:
                if key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.waiting_start = False
                    self.countdown_timer = 3000   # 3秒(3000ms)カウントダウン
            elif self.countdown_timer <= 0:
                # プレイ中：SPACEで回復ストックを消費
                if key == pygame.K_SPACE:
                    self._consume_heal_stock()

        elif self.state == "gameover":
            if key == pygame.K_RETURN:
                self.finished = True

        elif self.state == "ending":
            if key == pygame.K_RETURN:
                self.finished = True

    # ============================================
    # ゲーム更新
    # ============================================
    def update_play(self, dt, keys):
        if self.waiting_start:
            for star in self.stars:
                star.update()
            for planet in self.planets:
                planet.update()
            return
        
        # ↓ カウントダウン中もボールやプレイヤーは動かさない
        if self.countdown_timer > 0:
            self.countdown_timer = max(0, self.countdown_timer - dt)
            for star in self.stars:
                star.update()
            for planet in self.planets:
                planet.update()
            return

        self.update_score_and_time(dt)
        self.update_status_effects(dt)

        inverted = self.invert_timer > 0
        for player in self.players:
            player.move(keys, inverted=inverted)

        for ball in self.balls:
            # ビーム発射中はそのバー色のボールを停止
            if self.beam_active.get(ball.color_name):
                continue
            ball.move()

        self.update_blocks_spawn(dt)
        self.update_enemy(dt)
        self.update_projectiles(dt)
        self.update_player_beams(dt, keys)
        self.check_player_ball_collision()
        self.check_block_ball_collision()
        self.check_game_over()

        # 衝撃波リングの更新・完了したものを削除
        for ring in self.beam_impact_rings:
            ring.update(dt)
        self.beam_impact_rings = [r for r in self.beam_impact_rings if not r.done]

        # コンボエフェクトの更新・完了したものを削除
        for ce in self.combo_effects:
            ce.update(dt)
        self.combo_effects = [c for c in self.combo_effects if not c.done]