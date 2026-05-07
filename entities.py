# ============================================================
# entities.py
# ゲーム内オブジェクトのクラス定義
# Player, Ball, Block, Enemy, Projectile
# ============================================================

import random
import math
import pygame
from config import (
    PLAY_LEFT, PLAY_TOP, PLAY_HEIGHT, PLAY_WIDTH, WIDTH, HEIGHT,
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED, MAX_BOOST,
    BALL_SIZE, INITIAL_BALL_SPEED, SPEED_UP, MAX_BOUNCE_ANGLE,
    BLOCK_WIDTH, BLOCK_HEIGHT,
    RED, BLUE, PURPLE, WHITE, DARK_GRAY, GREEN, YELLOW,
    ENEMY_X, ENEMY_Y, ENEMY_WIDTH, ENEMY_HEIGHT,
    ENEMY_MAX_HP, DAMAGE_NORMAL, DAMAGE_RESIST,
    ENEMY_ATTACK_INTERVAL, SPECIAL_INTERVAL_MIN, SPECIAL_INTERVAL_MAX,
    MONSTER_DEFS,
    INVINCIBLE_BLOCK_COLOR, INVINCIBLE_BLOCK_HITS, INVINCIBLE_BLOCK_LIFETIME,
    PROJECTILE_SPEED, PROJECTILE_WIDTH, PROJECTILE_HEIGHT,
    BLUE_GRAVITY_MULT,
    LIGHT_BEAM_DURATION, LIGHT_BEAM_WIDTH,
    GOLD_BLOCK_COLOR, GOLD_BLOCK_HITS, GOLD_BLOCK_LIFETIME,  # ← 追加
    PLAYER_BEAM_WIDTH,
)


# ============================================================
# プレイヤークラス
# ============================================================
class Player:
    def __init__(self, x, y, color, color_name, left_key, right_key):
        self.x = x
        self.y = y
        self.color = color
        self.color_name = color_name
        self.left_key = left_key
        self.right_key = right_key
        self.speed = PLAYER_SPEED
        self.boost_count = 0
        self.dx = 0
        # 速度ダウン中フラグ（黒モンスター特殊攻撃）
        self._slowed = False
        self._base_speed = PLAYER_SPEED  # ブースト込みの本来の速度を記憶

    def move(self, keys, inverted=False):
        prev_x = self.x

        left  = self.right_key if inverted else self.left_key
        right = self.left_key  if inverted else self.right_key

        if keys[left]:
            self.x -= self.speed
        if keys[right]:
            self.x += self.speed

        extra_left  = getattr(self, "extra_left_key",  None)
        extra_right = getattr(self, "extra_right_key", None)
        if extra_left is not None and extra_right is not None:
            el = extra_right if inverted else extra_left
            er = extra_left  if inverted else extra_right
            if keys[el]:
                self.x -= self.speed
            if keys[er]:
                self.x += self.speed

        self.x = max(PLAY_LEFT, min(WIDTH - PLAYER_WIDTH, self.x))
        self.dx = self.x - prev_x

    def boost(self):
        if self.boost_count < MAX_BOOST:
            self._base_speed += 1
            self.boost_count  += 1
            # スロー中でなければ実際の速度にも反映
            if not self._slowed:
                self.speed = self._base_speed

    def apply_slow(self, mult):
        """速度ダウンを適用する（黒モンスター特殊攻撃）"""
        self._slowed    = True
        self._base_speed = self.speed  # 現在の速度を記憶
        self.speed = max(1, int(self.speed * mult))

    def remove_slow(self):
        """速度ダウンを解除する"""
        self._slowed = False
        self.speed   = self._base_speed

    def draw(self, surface, override_color=None):
        color = override_color if override_color else self.color
        pygame.draw.rect(surface, color, self.rect)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)


# ============================================================
# ボールクラス
# ============================================================
class Ball:
    def __init__(self, color_name, color, speed_up_mult=1.0,
                 initial_speed=None):
        self.color_name    = color_name
        self.color         = color
        self.speed_up_mult = speed_up_mult
        self._initial_speed = initial_speed if initial_speed else INITIAL_BALL_SPEED
        # 青モンスター特殊攻撃（下降時だけ速くなる）
        self.gravity_mode  = False
        self.reset()

    def reset(self):
        self.x = random.randint(PLAY_LEFT, WIDTH - BALL_SIZE)
        self.y = PLAY_TOP + 50
        self.speed   = self._initial_speed
        angle = math.radians(random.randint(30, 150))
        self.speed_x = self.speed * math.cos(angle)
        self.speed_y = self.speed * math.sin(angle)
        # 直前に衝突したブロックのidを記憶して連続ヒットを防ぐ
        self._hit_block_id  = None
        self._hit_cooldown  = 0   # フレーム数カウント

    def move(self):
        # ブロック衝突クールダウンを毎フレーム減らす
        if self._hit_cooldown > 0:
            self._hit_cooldown -= 1
            if self._hit_cooldown == 0:
                self._hit_block_id = None

        # 青モンスター特殊：下降中（speed_y > 0）は速度倍率を掛ける
        if self.gravity_mode and self.speed_y > 0:
            vx = self.speed_x * BLUE_GRAVITY_MULT
            vy = self.speed_y * BLUE_GRAVITY_MULT
        else:
            vx = self.speed_x
            vy = self.speed_y

        self.x += vx
        self.y += vy

        if self.x <= PLAY_LEFT:
            self.speed_x *= -1
            self.x = PLAY_LEFT
        if self.x >= WIDTH - BALL_SIZE:
            self.speed_x *= -1
            self.x = WIDTH - BALL_SIZE
        if self.y <= PLAY_TOP:
            self.speed_y *= -1
            self.y = PLAY_TOP

    def bounce_on_player(self, player):
        new_speed_x = self.speed_x
        new_speed_y = -abs(self.speed_y)

        if player.dx != 0 and new_speed_x * player.dx < 0:
            compression  = min(abs(player.dx) / (PLAYER_SPEED + MAX_BOOST), 1.0)
            keep_ratio   = 1.0 - 0.4 * compression
            new_speed_x  = new_speed_x * keep_ratio

        new_speed_x += player.dx * 0.15

        self.speed  += SPEED_UP * self.speed_up_mult
        magnitude    = math.hypot(new_speed_x, new_speed_y)
        if magnitude > 0:
            self.speed_x = new_speed_x / magnitude * self.speed
            self.speed_y = new_speed_y / magnitude * self.speed
        else:
            self.speed_x = 0
            self.speed_y = -self.speed

        self.y = player.y - BALL_SIZE

    def can_hit_block(self, block):
        """このフレームにそのブロックに当たれるか（連続ヒット防止）"""
        return self._hit_block_id != id(block)

    def register_block_hit(self, block):
        """ブロック衝突を登録し、クールダウンをセット"""
        self._hit_block_id = id(block)
        self._hit_cooldown = 8  # 8フレーム（約0.13秒）は同じブロックに当たらない

    def slow_down(self, amount):
        new_speed = max(self._initial_speed, self.speed - amount)
        if self.speed > 0:
            ratio        = new_speed / self.speed
            self.speed_x *= ratio
            self.speed_y *= ratio
        self.speed = new_speed

    def is_fallen(self):
        return self.y > HEIGHT

    def draw(self, surface):
        center_x = int(self.x + BALL_SIZE / 2)
        center_y = int(self.y + BALL_SIZE / 2)
        radius   = BALL_SIZE // 2
        pygame.draw.circle(surface, self.color, (center_x, center_y), radius)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, BALL_SIZE, BALL_SIZE)


# ============================================================
# ブロッククラス
# ============================================================
class Block:
    def __init__(self, x, y, block_type):
        self.x = x
        self.y = y
        self.type = block_type
        # 紫ブロック専用
        self.red_hit   = False
        self.blue_hit  = False
        self.white_hits = 0
        # 無敵ブロック専用：残り耐久回数・寿命
        self.invincible_hits_left = INVINCIBLE_BLOCK_HITS
        self.invincible_lifetime  = INVINCIBLE_BLOCK_LIFETIME  # 残り寿命（ms）
        # 金ブロック専用
        self.gold_hits_left = GOLD_BLOCK_HITS   # 残り耐久時間
        self.gold_lifetime   = GOLD_BLOCK_LIFETIME  # 残り寿命（ms)


    @property
    def color(self):
        if self.type == "red":
            return RED
        if self.type == "blue":
            return BLUE
        if self.type == "invincible":
            return INVINCIBLE_BLOCK_COLOR
        if self.type == "gold":
            return GOLD_BLOCK_COLOR
        return PURPLE

    def randomize_position(self):
        self.x = random.randint(PLAY_LEFT, WIDTH - BLOCK_WIDTH)
        self.y = random.randint(PLAY_TOP + 50, PLAY_TOP + PLAY_HEIGHT // 2)

    def draw(self, surface, dye_color=None):
        if self.type == "invincible":
            # 無敵ブロック：枠付きで描画、残り耐久に応じて輝度変化
            ratio = self.invincible_hits_left / INVINCIBLE_BLOCK_HITS
            r = int(180 + 75 * ratio)
            g = int(180 + 75 * ratio)
            b = 255
            pygame.draw.rect(surface, (r, g, b), self.rect, border_radius=4)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
            return
        if self.type == "gold":
            ratio = self.gold_hits_left / GOLD_BLOCK_HITS
            r = 255
            g = int(180 + 35 * ratio)
            b = 0
            pygame.draw.rect(surface, (r, g, b), self.rect, border_radius=4)
            pygame.draw.rect(surface, (255, 255, 200), self.rect, 2, border_radius=4)
            return
        color = dye_color if dye_color else self.color
        pygame.draw.rect(surface, color, self.rect)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, BLOCK_WIDTH, BLOCK_HEIGHT)



# ============================================================
# プレイヤービームクラス
# ============================================================
class PlayerBeam:
    def __init__(self, player):
        self.player      = player        # どのバーから出るか
        self.color_name  = player.color_name
        self.active      = True          # ビームが出ているか
        # ブロックごとの当たり継続時間を記録｛block_id: 当たり続けたms}
        self.hit_timers = {}
        # 白ブロックへの当たり判定済みフラグ｛block_id: True｝
        self.white_hit_done = {}

    @property
    def rect(self):
        """ビームの当たり判定：バーの中央から上に向かって伸びる"""
        cx = self.player.x + PLAYER_WIDTH // 2 - PLAYER_BEAM_WIDTH // 2
        return pygame.Rect(cx, PLAY_TOP, PLAYER_BEAM_WIDTH,
                           self.player.y - PLAY_TOP)
    
    def draw(self, surface):
        cx = self.player.x + PLAYER_WIDTH // 2
        top    = PLAY_TOP
        bottom = self.player.y

        height = bottom - top
        if height <= 0:
            return

        # バーの色に応じてコアカラーとグロウカラーを決める
        if self.color_name == "red":
            core_color = (255, 120, 120)
            glow_color = (255,  40,  40)
        elif self.color_name == "blue":
            core_color = (150, 180, 255)
            glow_color = ( 40,  80, 255)
        else:  # white（solo1）
            core_color = (255, 255, 255)
            glow_color = (160, 200, 255)

        try:
            # --- グロウ層（外側・半透明・幅広） ---
            glow_layers = [
                (PLAYER_BEAM_WIDTH + 16, 40),
                (PLAYER_BEAM_WIDTH +  8, 80),
                (PLAYER_BEAM_WIDTH +  2, 130),
            ]
            for glow_w, base_alpha in glow_layers:
                glow_surf = pygame.Surface((glow_w, height), pygame.SRCALPHA)
                for i in range(height):
                    ratio = i / height
                    alpha = int(base_alpha * (1.0 - ratio * 0.5))
                    pygame.draw.line(glow_surf,
                                     (glow_color[0], glow_color[1], glow_color[2], alpha),
                                     (0, i), (glow_w, i))
                surface.blit(glow_surf, (cx - glow_w // 2, top))

            # --- コア層（中心・明るい） ---
            core_w = max(4, PLAYER_BEAM_WIDTH // 2)
            core_surf = pygame.Surface((core_w, height), pygame.SRCALPHA)
            for i in range(height):
                ratio = i / height
                alpha = int(240 - 60 * ratio)
                pygame.draw.line(core_surf,
                                 (core_color[0], core_color[1], core_color[2], alpha),
                                 (0, i), (core_w, i))
            surface.blit(core_surf, (cx - core_w // 2, top))

            # --- 白い中心線（最前面） ---
            white_w = max(2, PLAYER_BEAM_WIDTH // 5)
            white_surf = pygame.Surface((white_w, height), pygame.SRCALPHA)
            for i in range(height):
                ratio = i / height
                alpha = int(255 - 100 * ratio)
                pygame.draw.line(white_surf, (255, 255, 255, alpha),
                                 (0, i), (white_w, i))
            surface.blit(white_surf, (cx - white_w // 2, top))

        except Exception:
            pass






# ============================================================
# 衝撃波リングクラス（ビームがブロックに当たった時の演出）
# ============================================================
class BeamImpactRing:
    """ビームがブロックに当たり続けている間、波紋を広げるエフェクト"""
    DURATION = 400  # ms

    def __init__(self, x, y, color_name):
        self.x          = x
        self.y          = y
        self.color_name = color_name
        self.timer      = 0
        self.done       = False

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.DURATION:
            self.done = True

    def draw(self, surface):
        ratio  = self.timer / self.DURATION  # 0.0 → 1.0
        radius = int(6 + 28 * ratio)
        alpha  = int(255 * (1.0 - ratio))

        if self.color_name == "red":
            color = (255, 80, 80)
        elif self.color_name == "blue":
            color = (80, 120, 255)
        else:
            color = (200, 220, 255)

        ring_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*color, alpha),
                           (radius + 2, radius + 2), radius, 2)
        surface.blit(ring_surf, (self.x - radius - 2, self.y - radius - 2))


# ============================================================
# 落下物クラス（葉っぱ・光の矢）
# ============================================================
class Projectile:
    """モンスターが落とす落下攻撃オブジェクト"""

    def __init__(self, x, proj_type):
        """
        x         : 出現X座標
        proj_type : "leaf"（緑・葉っぱ）or "arrow"（黄色・光の矢）
        """
        self.x    = x
        self.y    = PLAY_TOP + 10
        self.type = proj_type
        self.speed = PROJECTILE_SPEED
        self.active = True

    def move(self):
        self.y += self.speed

    def is_out(self):
        return self.y > HEIGHT

    def draw(self, surface):
        if self.type == "leaf":
            self._draw_leaf(surface)
        elif self.type == "mud":
            self._draw_arrow(surface)
        else:
            self._draw_arrow(surface)

    def _draw_leaf(self, surface):
        """葉っぱ：緑の楕円＋茎"""
        cx = int(self.x + PROJECTILE_WIDTH / 2)
        cy = int(self.y + PROJECTILE_HEIGHT / 2)
        # 葉の楕円
        leaf_rect = pygame.Rect(cx - 10, cy - 6, 20, 12)
        pygame.draw.ellipse(surface, (30, 160, 30), leaf_rect)
        pygame.draw.ellipse(surface, (20, 220, 20), leaf_rect, 1)
        # 中央の葉脈
        pygame.draw.line(surface, (20, 100, 20),
                         (cx - 8, cy), (cx + 8, cy), 1)
        # 茎
        pygame.draw.line(surface, (100, 60, 20),
                         (cx, cy + 6), (cx, cy + 12), 2)

    def _draw_arrow(self, surface):
        """泥ビーム：上から落ちてくる茶色い泥の柱"""
        cx = int(self.x + PROJECTILE_WIDTH / 2)
        cy = int(self.y)

        # ビームの幅と長さ
        beam_w = 10
        beam_h = 28

        # ビーム本体（半透明の茶色い柱）
        try:
            beam = pygame.Surface((beam_w, beam_h), pygame.SRCALPHA)
            # 内側：明るい泥色
            pygame.draw.rect(beam, (139, 90, 43, 200),
                             pygame.Rect(2, 0, beam_w - 4, beam_h))
            # 外側：暗い縁
            pygame.draw.rect(beam, (80, 45, 10, 220),
                             pygame.Rect(0, 0, beam_w, beam_h), 2)
            # 中央のハイライト（ぬめり感）
            pygame.draw.rect(beam, (180, 130, 60, 160),
                             pygame.Rect(3, 2, 4, beam_h - 4))
            surface.blit(beam, (cx - beam_w // 2, cy))
        except Exception:
            pass

        # 先端の泥玉（しずく形）
        try:
            tip_r = 7
            tip_surf = pygame.Surface((tip_r * 2 + 2, tip_r * 2 + 6),
                                      pygame.SRCALPHA)
            # 丸い泥玉
            pygame.draw.circle(tip_surf, (110, 65, 20, 230),
                               (tip_r + 1, tip_r + 1), tip_r)
            # 光沢
            pygame.draw.circle(tip_surf, (180, 130, 60, 150),
                               (tip_r - 1, tip_r - 1), 3)
            # しずくの尾
            tail_points = [
                (tip_r + 1, tip_r * 2 - 1),
                (tip_r - 3, tip_r * 2 + 4),
                (tip_r + 5, tip_r * 2 + 4),
            ]
            pygame.draw.polygon(tip_surf, (110, 65, 20, 200), tail_points)
            surface.blit(tip_surf,
                         (cx - tip_r - 1, cy + beam_h - tip_r))
        except Exception:
            pass

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y,
                           PROJECTILE_WIDTH, PROJECTILE_HEIGHT)


# ============================================================
# 爆発エフェクトクラス（赤モンスター特殊攻撃）
# ============================================================
class Explosion:
    """画面上で一定時間表示される爆発エフェクト"""

    def __init__(self, cx, cy):
        self.cx       = cx
        self.cy       = cy
        self.timer    = 0
        self.duration = 600   # ミリ秒
        self.active   = True
        # ランダムな火花
        self.sparks = [
            {
                "angle": random.uniform(0, math.pi * 2),
                "dist":  random.randint(10, 60),
                "size":  random.randint(3, 8),
                "color": random.choice([
                    (255, 80,  0), (255, 200, 0),
                    (255, 255, 100), (255, 120, 0)
                ]),
            }
            for _ in range(18)
        ]

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        ratio = self.timer / self.duration   # 0.0 → 1.0
        alpha = int(255 * (1.0 - ratio))
        scale = 0.4 + 1.6 * ratio            # 小→大

        for s in self.sparks:
            d  = s["dist"] * scale
            px = int(self.cx + math.cos(s["angle"]) * d)
            py = int(self.cy + math.sin(s["angle"]) * d)
            r  = max(1, int(s["size"] * (1.0 - ratio * 0.6)))
            col = s["color"]
            # アルファ付き円を描画
            try:
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*col, alpha), (r, r), r)
                surface.blit(surf, (px - r, py - r))
            except Exception:
                pass

        # 中央の閃光
        core_r = max(1, int(30 * (1.0 - ratio)))
        try:
            core = pygame.Surface((core_r * 2, core_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(core, (255, 255, 200, alpha),
                               (core_r, core_r), core_r)
            surface.blit(core, (self.cx - core_r, self.cy - core_r))
        except Exception:
            pass


# ============================================================
# 滝エフェクトクラス（青モンスター特殊攻撃）
# ============================================================
class WaterfallParticle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x     = random.randint(PLAY_LEFT + 5, WIDTH - 5)
        self.y     = PLAY_TOP + random.randint(0, PLAY_HEIGHT)
        self.speed = random.uniform(2.0, 5.0)
        self.size  = random.randint(2, 5)
        alpha_val  = random.randint(80, 200)
        blue_val   = random.randint(180, 255)
        self.color = (30, 100, blue_val, alpha_val)

    def move(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.reset()
            self.y = PLAY_TOP

    def draw(self, surface):
        try:
            s = pygame.Surface((self.size * 2, self.size * 4),
                               pygame.SRCALPHA)
            pygame.draw.ellipse(s, self.color,
                                s.get_rect())
            surface.blit(s, (int(self.x), int(self.y)))
        except Exception:
            pass


# ============================================================
# 光ビームクラス（黄色モンスター特殊攻撃）
# 画面上端から下端まで瞬時に出現し、一定時間表示される
# ============================================================
class LightBeam:
    """黄色モンスターが放つ縦一直線の光ビーム。
    生成時にX座標を受け取り、プレイエリア上端→下端まで瞬時に描画。
    LIGHT_BEAM_DURATION ミリ秒後に消える。当たり判定は細いRect。"""

    def __init__(self, x):
        # ビームの中心X（プレイエリア内にクランプ）
        self.cx     = max(PLAY_LEFT + LIGHT_BEAM_WIDTH,
                          min(x, PLAY_LEFT + PLAY_WIDTH - LIGHT_BEAM_WIDTH))
        self.timer  = 0          # 経過時間（ms）
        self.active = True

    @property
    def rect(self):
        """当たり判定：プレイエリア全体の高さ × ビーム幅"""
        return pygame.Rect(
            self.cx - LIGHT_BEAM_WIDTH // 2,
            PLAY_TOP,
            LIGHT_BEAM_WIDTH,
            HEIGHT - PLAY_TOP,
        )

    def update(self, dt):
        self.timer += dt
        if self.timer >= LIGHT_BEAM_DURATION:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        # 発動直後ほど明るく、フェードアウトしていく
        ratio = self.timer / LIGHT_BEAM_DURATION   # 0.0→1.0
        bright = int(255 * (1.0 - ratio * 0.7))   # 255→76

        try:
            # --- コア：極細の白芯 ---
            core_w = max(2, LIGHT_BEAM_WIDTH // 4)
            core = pygame.Surface((core_w, HEIGHT - PLAY_TOP), pygame.SRCALPHA)
            core.fill((255, 255, bright, bright))
            surface.blit(core, (self.cx - core_w // 2, PLAY_TOP))

            # --- 中間：黄白のグロー ---
            mid_w = LIGHT_BEAM_WIDTH
            mid = pygame.Surface((mid_w, HEIGHT - PLAY_TOP), pygame.SRCALPHA)
            mid.fill((255, 245, 100, int(bright * 0.6)))
            surface.blit(mid, (self.cx - mid_w // 2, PLAY_TOP))

            # --- 外縁：黄色の淡いオーラ ---
            outer_w = LIGHT_BEAM_WIDTH * 3
            outer = pygame.Surface((outer_w, HEIGHT - PLAY_TOP), pygame.SRCALPHA)
            outer.fill((255, 220, 0, int(bright * 0.25)))
            surface.blit(outer, (self.cx - outer_w // 2, PLAY_TOP))

            # --- 上端のフレア（発動感） ---
            flare_r = int((LIGHT_BEAM_WIDTH * 2) * (1.0 - ratio * 0.8))
            if flare_r > 0:
                flare = pygame.Surface((flare_r * 2, flare_r * 2),
                                       pygame.SRCALPHA)
                pygame.draw.circle(flare, (255, 255, 200, int(bright * 0.7)),
                                   (flare_r, flare_r), flare_r)
                surface.blit(flare,
                             (self.cx - flare_r, PLAY_TOP - flare_r + 4))
        except Exception:
            pass


# ============================================================
# 敵クラス
# ============================================================
class Enemy:
    def __init__(self, monster_images, exclude_name=None,
                 ex=None, ey=None, ew=None, eh=None):
        candidates = [m for m in MONSTER_DEFS if m["name"] != exclude_name]
        if not candidates:
            candidates = MONSTER_DEFS
        self.definition   = random.choice(candidates)
        self.name         = self.definition["name"]
        self.label        = self.definition["label"]
        self.resist       = self.definition["resist"]
        self.special_type = self.definition["special"]

        # 描画位置・サイズ（省略時はconfig定数を使う）
        self.ex = ex if ex is not None else ENEMY_X
        self.ey = ey if ey is not None else ENEMY_Y
        self.ew = ew if ew is not None else ENEMY_WIDTH
        self.eh = eh if eh is not None else ENEMY_HEIGHT

        # 画像をサイズに合わせてリサイズ
        raw = monster_images.get(self.name)
        if raw is not None:
            self.image = pygame.transform.smoothscale(raw, (self.ew, self.eh))
        else:
            self.image = None

        self.max_hp = self.definition.get("max_hp", ENEMY_MAX_HP)
        self.hp     = self.max_hp
        # 通常攻撃タイミングをランダムにずらす（2体が同時にならないように）
        self.attack_timer  = random.randint(0, ENEMY_ATTACK_INTERVAL // 2)
        self.special_timer = 0
        self.next_special  = random.randint(
            SPECIAL_INTERVAL_MIN, SPECIAL_INTERVAL_MAX)

    def take_damage(self, ball_color, atk_mult=1.0):
        if self.resist is not None and ball_color == self.resist:
            damage = DAMAGE_RESIST
        else:
            damage = DAMAGE_NORMAL
        damage = int(damage * atk_mult)
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    def update(self, dt):
        actions = {"normal_attack": False, "special_attack": False}

        self.attack_timer += dt
        if self.attack_timer >= ENEMY_ATTACK_INTERVAL:
            self.attack_timer = 0
            actions["normal_attack"] = True

        if self.special_type is not None:
            self.special_timer += dt
            if self.special_timer >= self.next_special:
                self.special_timer = 0
                # 緑と黄色は次の間隔をずらして交互にならないようにする
                if self.special_type in ("invert", "dye"):
                    self.next_special = random.randint(
                        SPECIAL_INTERVAL_MIN + 3000,
                        SPECIAL_INTERVAL_MAX + 5000)
                else:
                    self.next_special = random.randint(
                        SPECIAL_INTERVAL_MIN, SPECIAL_INTERVAL_MAX)
                actions["special_attack"] = True

        return actions

    def is_dead(self):
        return self.hp <= 0

    def draw(self, surface, font, small_font):
        ex, ey, ew, eh = self.ex, self.ey, self.ew, self.eh
        if self.resist == "red":
            border_color = RED
        elif self.resist == "blue":
            border_color = BLUE
        else:
            border_color = (100, 100, 100)
        pygame.draw.rect(
            surface, border_color,
            (ex - 5, ey - 5, ew + 10, eh + 10), border_radius=8)

        if self.image is not None:
            surface.blit(self.image, (ex, ey))
        else:
            pygame.draw.rect(surface, DARK_GRAY, (ex, ey, ew, eh))
            text = font.render("ENEMY", True, (255, 255, 255))
            text_rect = text.get_rect(center=(ex + ew // 2, ey + eh // 2))
            surface.blit(text, text_rect)

        if self.resist is None:
            resist_text = small_font.render("Resist: NONE", True, (255, 255, 255))
        else:
            color = RED if self.resist == "red" else BLUE
            resist_text = small_font.render(
                f"Resist: {self.resist.upper()}", True, color)

        text_w = resist_text.get_width()
        text_h = resist_text.get_height()
        panel  = pygame.Surface((text_w + 12, text_h + 6), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        surface.blit(panel, (ex - 6, ey - 31))
        surface.blit(resist_text, (ex, ey - 28))


# ============================================================
# 星クラス（背景の星空）
# ============================================================
class Star:
    def __init__(self):
        self.x     = random.randint(PLAY_LEFT, WIDTH)
        self.y     = random.randint(PLAY_TOP, HEIGHT)
        self.size  = random.randint(1, 3)
        self.alpha = random.randint(100, 255)
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.01, 0.04)

    def update(self):
        self.phase += self.speed
        self.alpha = int(140 + 115 * math.sin(self.phase))
        self.alpha = max(60, min(255, self.alpha))

    def draw(self, surface):
        try:
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, self.alpha),
                               (self.size, self.size), self.size)
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))
        except Exception:
            pass


# ============================================================
# 惑星クラス（画像あり→画像で描画、なし→コード描画にフォールバック）
# ============================================================
class Planet:
    PLANET_STYLES = [
        {"base": (180, 100, 60),  "stripe": (220, 140, 80),
         "ring": True,  "ring_color": (200, 160, 80)},
        {"base": (60,  100, 200), "stripe": (80,  140, 230),
         "ring": False, "ring_color": None},
        {"base": (200, 80,  60),  "stripe": (230, 120, 90),
         "ring": False, "ring_color": None},
        {"base": (150, 100, 200), "stripe": (180, 130, 220),
         "ring": True,  "ring_color": (170, 120, 210)},
        {"base": (60,  180, 160), "stripe": (90,  210, 190),
         "ring": False, "ring_color": None},
    ]

    def __init__(self, image=None, style_index=0):
        """
        image       : pygame.Surface or None（Noneならコード描画）
        style_index : コード描画時のスタイル番号
        """
        self.radius = random.randint(50, 100)
        self.x  = float(random.randint(PLAY_LEFT + self.radius + 20,
                                        WIDTH - self.radius - 20))
        self.y  = float(random.randint(PLAY_TOP + self.radius + 20,
                                        HEIGHT - self.radius - 20))
        self.vx = random.uniform(-0.15, 0.15)
        self.vy = random.uniform(-0.10, 0.10)
        # ゆっくり回転（画像をrotozoomで回転させる）
        self.angle     = random.uniform(0, 360)
        self.rot_speed = random.uniform(0.02, 0.06)
        self.alpha     = random.randint(160, 210)

        # 画像があればリサイズして保持
        if image is not None:
            size = self.radius * 2
            self._orig_image = pygame.transform.smoothscale(image, (size, size))
            self._use_image  = True
        else:
            self._use_image  = False
            style = self.PLANET_STYLES[style_index % len(self.PLANET_STYLES)]
            self.base_color   = style["base"]
            self.stripe_color = style["stripe"]
            self.has_ring     = style["ring"]
            self.ring_color   = style["ring_color"]

    def update(self):
        self.x     += self.vx
        self.y     += self.vy
        self.angle  = (self.angle + self.rot_speed) % 360

        r = self.radius + 10
        if self.x < PLAY_LEFT + r or self.x > WIDTH - r:
            self.vx *= -1
            self.x = max(PLAY_LEFT + r, min(WIDTH - r, self.x))
        if self.y < PLAY_TOP + r or self.y > HEIGHT - r:
            self.vy *= -1
            self.y = max(PLAY_TOP + r, min(HEIGHT - r, self.y))

    def draw(self, surface):
        cx = int(self.x)
        cy = int(self.y)
        try:
            if self._use_image:
                # 画像を回転させて半透明で描画
                rotated = pygame.transform.rotozoom(
                    self._orig_image, self.angle, 1.0)
                rotated.set_alpha(self.alpha)
                rect = rotated.get_rect(center=(cx, cy))
                surface.blit(rotated, rect)
            else:
                self._draw_code(surface, cx, cy)
        except Exception:
            pass

    def _draw_code(self, surface, cx, cy):
        """画像なし時のコード描画（フォールバック）"""
        r = self.radius
        diam = (r + 10) * 2 + 20
        ps   = pygame.Surface((diam, diam), pygame.SRCALPHA)
        ox = oy = diam // 2

        pygame.draw.circle(ps, (*self.base_color, self.alpha), (ox, oy), r)
        for i in range(-r + 6, r, 12):
            cos_val = max(-1.0, min(1.0, i / r))
            sh = max(2, int(8 * math.cos(math.asin(cos_val))))
            pygame.draw.ellipse(ps, (*self.stripe_color, self.alpha),
                                (ox - r, oy + i, r * 2, sh))
        pygame.draw.circle(ps, (255, 255, 255, min(self.alpha, 50)),
                           (ox - r // 3, oy - r // 3), r // 3)
        surface.blit(ps, (cx - ox, cy - oy))

        if self.has_ring and self.ring_color:
            rs = pygame.Surface((r * 4, r * 2), pygame.SRCALPHA)
            rcx, rcy = r * 2, r
            pygame.draw.ellipse(rs, (*self.ring_color, max(0, self.alpha - 10)),
                                (rcx - r * 2, rcy - r // 3, r * 4, r * 2 // 3), 4)
            surface.blit(rs, (cx - r * 2, cy - r))