# ============================================================
# cosmic_game.py
# 宇宙空間 避けゲーモード
# 上から降ってくるブロックを左右上下に避けつつ、色ブロックに体当たりして
# 変身する。同色を3個取るとストック+1（最大3）。スペースキーで現在の
# モンスターの特殊能力を発動。岩ブロックに当たるとHP-1、紫ブロックで+1。
# 時間が経つほど岩の落下速度が上がる。
# ============================================================

import math
import random
import pygame

from config import (
    WIDTH, HEIGHT, FPS,
    BLACK, WHITE, GOLD, GRAY, RED, BLUE, YELLOW, GREEN,
    MODE_COSMIC,
)


# ============================================================
# レイアウト
# ============================================================
# 画面全体は config.WIDTH x HEIGHT (1200 x 650)
# その中で、上バー / 左サイド / プレイエリア / 右サイド の4ブロックに分ける
TOP_BAR_H        = 50                              # 上の細い情報バー
LEFT_PANEL_W     = 400                             # 左サイドバー（HP/モンスター/ストック）
RIGHT_PANEL_W    = 400                             # 右サイドバー（背景アニメ）
PLAY_LEFT        = LEFT_PANEL_W                    # プレイエリアの左端 = 400
PLAY_TOP         = TOP_BAR_H                       # プレイエリアの上端 = 50
PLAY_W           = WIDTH - LEFT_PANEL_W - RIGHT_PANEL_W   # プレイエリアの幅 = 400
PLAY_H           = HEIGHT - TOP_BAR_H              # プレイエリアの高さ = 600
PLAY_RIGHT       = PLAY_LEFT + PLAY_W              # プレイエリアの右端 = 800
PLAY_BOTTOM      = PLAY_TOP + PLAY_H               # プレイエリアの下端 = 650
PLAY_CX          = PLAY_LEFT + PLAY_W // 2         # プレイエリアの中心x = 600
PLAY_CY          = PLAY_TOP  + PLAY_H // 2         # プレイエリアの中心y = 350

# 右サイドバーの中心（背景アニメの中心点）
RIGHT_PANEL_CX   = PLAY_RIGHT + RIGHT_PANEL_W // 2  # 1000
RIGHT_PANEL_CY   = HEIGHT // 2                      # 325


# ============================================================
# 定数
# ============================================================

# プレイヤー
PLAYER_MAX_HP    = 5
PLAYER_HP_CAP    = 9            # 紫で増やせる上限
PLAYER_SIZE      = 60           # 縦長画面なのでやや小さめ
PLAYER_SPEED     = 5

# ブロックの種類
BLOCK_NORMAL     = "normal"     # 白：当たっても害なし、ただ通り過ぎる
BLOCK_ROCK       = "rock"       # 茶：当たるとHP-1
BLOCK_PURPLE     = "purple"     # 紫：当たるとHP+1
BLOCK_SPEED      = "speed"      # シアン：プレイヤーの移動速度UP（時限）
BLOCK_SHIELD     = "shield"     # 金色：岩のダメージを無効化（時限）
BLOCK_RED        = "red"
BLOCK_BLUE       = "blue"
BLOCK_YELLOW     = "yellow"
BLOCK_GREEN      = "green"
BLOCK_DARK       = "dark"

COLOR_BLOCK_TYPES = [BLOCK_RED, BLOCK_BLUE, BLOCK_YELLOW, BLOCK_GREEN, BLOCK_DARK]

# 表示色
BLOCK_COLORS = {
    BLOCK_NORMAL: (235, 235, 235),
    BLOCK_ROCK:   (130,  85,  50),
    BLOCK_PURPLE: (180,  90, 220),
    BLOCK_SPEED:  ( 80, 230, 240),   # シアン：スピードアップブロック
    BLOCK_SHIELD: (255, 215,  90),   # 金色：シールドブロック
    BLOCK_RED:    (240,  70,  70),
    BLOCK_BLUE:   ( 70, 130, 240),
    BLOCK_YELLOW: (245, 220,  60),
    BLOCK_GREEN:  ( 80, 220, 120),
    BLOCK_DARK:   ( 60,  60,  75),
}

# スピードアップブロックの効果
SPEED_BOOST_DURATION = 6000     # 持続時間（ms）
SPEED_BOOST_MULT     = 1.6      # 速度倍率
# シールドブロックの効果
SHIELD_DURATION      = 6000     # 岩無効化の持続時間（ms）
# 色ブロックが出現し始めるまでの猶予時間（ms）
COLOR_BLOCK_GRACE_MS = 5000

# モンスター名 ↔ ブロック色
MONSTER_FOR_BLOCK = {
    BLOCK_RED:    "red",
    BLOCK_BLUE:   "blue",
    BLOCK_YELLOW: "yellow",
    BLOCK_GREEN:  "green",
    BLOCK_DARK:   "dark",
}

# スコア
SCORE_DODGE_PER_SEC  = 5     # 生存ボーナス（毎秒）
SCORE_BREAK_BLOCK    = 10    # ブロックを壊した（能力使用）

# ブロック生成
BLOCK_SIZE         = 22      # 六角形ブロックの大きさ
BLOCK_SPEED_BASE   = 1.1     # 初期落下速度（少し落とした）
BLOCK_SPEED_RAMP   = 0.018   # 1秒ごとに上がる量
BLOCK_SPEED_MAX    = 6.5     # （未使用：落下速度の上限はなし）
BLOCK_SPAWN_INTERVAL_START = 900   # 最初のスポーン間隔（ms） 少し緩める
BLOCK_SPAWN_INTERVAL_MIN   = 280   # 最小スポーン間隔（ms）
BLOCK_SPAWN_INTERVAL_RAMP  = 5     # 1秒ごとに減る量（ms）

# 出現確率（相対重み）
# 時間経過で岩の比率が上がる：BLOCK_WEIGHTS_START から BLOCK_WEIGHTS_LATE へ
# WEIGHT_RAMP_SEC かけて線形補間する。
# 色ブロックは COLOR_BLOCK_GRACE_MS 経過後にのみ出現する（_current_block_weights で制御）。
BLOCK_WEIGHTS_START = {
    BLOCK_ROCK:   30,   # 初期は少なめ：プレイヤーが慣れる時間を確保
    BLOCK_NORMAL: 12,   # 白：ストック源なので多め
    BLOCK_PURPLE: 1.5,  # 回復、レア
    BLOCK_SPEED:   2,   # スピードアップ、ややレア
    BLOCK_SHIELD:  1,   # シールド、レア
    BLOCK_RED:   0.4,   # 色ブロックは控えめ（解禁後）
    BLOCK_BLUE:  0.4,
    BLOCK_YELLOW:0.4,
    BLOCK_GREEN: 0.4,
    BLOCK_DARK:  0.4,
}

BLOCK_WEIGHTS_LATE = {
    BLOCK_ROCK:   55,   # 後半はメインの障害物
    BLOCK_NORMAL: 15,   # 白はやや減るがストック源として維持
    BLOCK_PURPLE: 1.5,
    BLOCK_SPEED:   2,
    BLOCK_SHIELD:  1,
    BLOCK_RED:   0.6,
    BLOCK_BLUE:  0.6,
    BLOCK_YELLOW:0.6,
    BLOCK_GREEN: 0.6,
    BLOCK_DARK:  0.6,
}

# この秒数かけて START → LATE へ遷移
WEIGHT_RAMP_SEC = 90

# 同色ブロックを取った回数のうち、何個でストック+1か
COLOR_CHARGES_PER_STOCK = 1
MAX_STOCKS              = 3

# 能力パラメータ
# 赤：爆弾
RED_BOMB_FUSE_MS    = 1000           # 1秒で爆発
RED_BOMB_RADIUS     = 100             # 爆発半径
RED_BOMB_SPEED      = 6              # 投擲初速
RED_SPEED_MULT      = 1.5            # 移動速度UP（ストックがあるあいだ）
# 赤：爆竹（プレイヤー周囲の連続爆発）
RED_FIRECRACKER_DURATION = 2000      # 持続時間（ms）
RED_FIRECRACKER_RADIUS   = 100        # 各小爆発が当たる範囲（プレイヤー中心）
RED_FIRECRACKER_INTERVAL = 55        # 小爆発の発生間隔（ms）
RED_FIRECRACKER_BLOCK_HIT_RADIUS = 30 # 個々の小爆発がブロックを巻き込む半径


# 青：上方向の水流（押し流す）
BLUE_STREAM_MS       = 2500          # 持続時間
BLUE_STREAM_WIDTH    = 80            # 水流の幅
BLUE_PUSH_SPEED      = 4.5           # ブロックを上に押す速度（px/frame）

# 黄：雷（ストック1消費でランダム3発）
YELLOW_BOLT_COUNT    = 3
YELLOW_BOLT_DELAY    = 150           # 各ボルトの間隔（ms）
YELLOW_BOLT_RADIUS   = 35            # 雷が壊す範囲

# 緑：前方向に放つ風の渦（ブロックを巻き込んで壊す）
GREEN_WIND_SPEED     = 7              # 渦の進行速度（px/frame）※初速
GREEN_WIND_SPEED_MIN_RATIO = 0.15     # 終端での速度（初速に対する比率）。小さいほどフェードアウトが顕著
GREEN_WIND_LIFE_MS   = 750           # 持続時間
GREEN_WIND_RADIUS_START = 27          # 初期半径
GREEN_WIND_RADIUS_END   = 65          # 終端半径（成長する）
GREEN_WIND_MAX_DISTANCE = 270         # 最大飛距離（px）。発射位置からこの距離進むと消滅
GREEN_SPEED_MULT     = 1.35

# 黒：周囲のブロックがスロー、岩は2秒で破壊
DARK_SLOW_RADIUS     = 130
DARK_SLOW_FACTOR     = 0.3           # 速度をこの倍率に落とす
DARK_ROCK_BREAK_MS   = 1000          # 岩がスロー圏内に居続けると壊れる時間
DARK_DURATION        = 6000          # 黒能力の持続時間（ms）

# エフェクト
PARTICLE_LIFETIME   = 600

# 背景（右サイドバーで流す）
STAR_COUNT          = 80
PLANET_COUNT        = 2


# ============================================================
# 背景：流れる星と惑星
# ============================================================
class WarpStar:
    """右サイドバーの中で中心から外側に流れる星"""

    def __init__(self):
        self.reset(initial=True)

    def reset(self, initial=False):
        cx = RIGHT_PANEL_CX
        cy = RIGHT_PANEL_CY
        angle = random.uniform(0, 2 * math.pi)
        max_r = max(RIGHT_PANEL_W, HEIGHT) // 2
        radius = (random.uniform(20, max_r)
                  if initial else random.uniform(5, 30))
        self.x = cx + math.cos(angle) * radius
        self.y = cy + math.sin(angle) * radius
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)
        self.speed = random.uniform(0.6, 2.0)
        self.size_base = random.uniform(0.6, 1.8)
        c = random.randint(180, 255)
        self.color = (c, c, min(255, c + 20))

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.speed *= 1.012
        # 右サイドバーの範囲外に出たらリセット
        if (self.x < PLAY_RIGHT - 20 or self.x > WIDTH + 20 or
                self.y < -20 or self.y > HEIGHT + 20):
            self.reset()

    def draw(self, surface):
        cx = RIGHT_PANEL_CX
        cy = RIGHT_PANEL_CY
        dist = math.hypot(self.x - cx, self.y - cy)
        size = max(0.5, self.size_base + dist / 200)
        tail_x = self.x - self.dx * size * 2
        tail_y = self.y - self.dy * size * 2
        try:
            pygame.draw.line(
                surface, self.color,
                (tail_x, tail_y), (self.x, self.y),
                max(1, int(size * 0.8)))
        except Exception:
            pass


class WarpPlanet:
    """右サイドバー内をゆっくり流れる惑星"""

    def __init__(self, image):
        self.image = image
        self.reset(initial=True)

    def reset(self, initial=False):
        cx = RIGHT_PANEL_CX
        cy = RIGHT_PANEL_CY
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(50, 200) if initial else random.uniform(10, 40)
        self.x = cx + math.cos(angle) * radius
        self.y = cy + math.sin(angle) * radius
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)
        self.speed = random.uniform(0.3, 0.6)
        self.size = random.randint(20, 40) if initial else random.randint(15, 25)
        self.max_size = random.randint(100, 160)
        self.grow_rate = random.uniform(0.3, 0.6)

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.speed *= 1.008
        self.size += self.grow_rate
        if (self.size > self.max_size or
            self.x < PLAY_RIGHT - self.size or self.x > WIDTH + self.size or
            self.y < -self.size or self.y > HEIGHT + self.size):
            self.reset()

    def draw(self, surface):
        if self.image is None:
            return
        s = max(8, int(self.size))
        try:
            scaled = pygame.transform.smoothscale(self.image, (s, s))
            surface.blit(scaled, (int(self.x - s / 2), int(self.y - s / 2)))
        except Exception:
            pass


# ============================================================
# パーティクル（破壊エフェクト）
# ============================================================
class BlockParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = PARTICLE_LIFETIME
        self.max_life = PARTICLE_LIFETIME
        self.color = color
        self.size = random.uniform(2, 4)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        alpha = int(255 * ratio)
        s = max(1, int(self.size * ratio))
        try:
            surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (s, s), s)
            surface.blit(surf, (int(self.x - s), int(self.y - s)))
        except Exception:
            pass

    def is_dead(self):
        return self.life <= 0


# ============================================================
# 爆弾の破片（赤の能力の派手エフェクト用）
# ============================================================
class ExplosionShard:
    """爆発で飛び散る破片。発光しながら回転して飛ぶ"""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 500
        self.max_life = 500
        self.size = random.uniform(2.5, 5)
        self.rot = random.uniform(0, 2 * math.pi)
        self.rot_speed = random.uniform(-0.3, 0.3)
        # 火っぽい色（赤〜オレンジ〜黄）からランダム
        self.color = random.choice([
            (255, 240, 150),
            (255, 200,  80),
            (255, 150,  50),
            (255,  90,  40),
        ])

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.vy += 0.15      # 軽い重力
        self.rot += self.rot_speed
        self.life -= dt

    def is_dead(self):
        return self.life <= 0

    def draw(self, surface):
        ratio = max(0.0, self.life / self.max_life)
        alpha = int(255 * ratio)
        s = max(1, int(self.size * (0.5 + 0.5 * ratio)))
        try:
            # 発光する小さな四角（回転させた点の近似でOK）
            surf = pygame.Surface((s * 2 + 4, s * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(
                surf, (*self.color, alpha), (s + 2, s + 2), s)
            # 中央の白い芯
            pygame.draw.circle(
                surf, (255, 255, 240, min(255, alpha + 30)),
                (s + 2, s + 2), max(1, s - 1))
            surface.blit(
                surf, (int(self.x - s - 2), int(self.y - s - 2)))
        except Exception:
            pass


# ============================================================
# 爆弾（赤の能力）
# ============================================================
class Bomb:
    """投擲後に重力で落ち、一定時間後に爆発する"""
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.fuse = RED_BOMB_FUSE_MS
        self.exploded = False
        self.explosion_anim = 0
        self.explosion_max = 500       # 爆発エフェクトを長めに
        self.shards = []               # 飛び散る破片
        self.shock_rings = []           # 衝撃の輪（複数）

    def update(self, dt):
        if not self.exploded:
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.10              # 重力
            self.fuse -= dt
            if self.fuse <= 0:
                self.exploded = True
                self.explosion_anim = self.explosion_max
                # 破片を一気に生成
                for _ in range(28):
                    self.shards.append(
                        ExplosionShard(self.x, self.y))
                # 衝撃のリングを段階的に
                self.shock_rings = [
                    {"life": 500, "max": 500, "max_r": RED_BOMB_RADIUS * 1.0,
                     "color": (255, 220, 120)},
                    {"life": 400, "max": 400, "max_r": RED_BOMB_RADIUS * 1.4,
                     "color": (255, 140,  60)},
                    {"life": 320, "max": 320, "max_r": RED_BOMB_RADIUS * 1.7,
                     "color": (255,  80,  30)},
                ]
        else:
            self.explosion_anim -= dt
            for shard in self.shards[:]:
                shard.update(dt)
                if shard.is_dead():
                    self.shards.remove(shard)
            for ring in self.shock_rings:
                ring["life"] = max(0, ring["life"] - dt)

    def is_dead(self):
        return (self.exploded and self.explosion_anim <= 0
                and not self.shards)

    def draw(self, surface):
        if not self.exploded:
            # 点滅する爆弾本体
            blink = (self.fuse // 100) % 2 == 0
            color = (250, 80, 80) if blink else (255, 200, 60)
            # ヒューズが短くなるほど大きく脈動
            fuse_ratio = max(0.0, self.fuse / RED_BOMB_FUSE_MS)
            pulse_r = 8 + int(4 * (1 - fuse_ratio))
            # 周囲のグロー（危険感）
            try:
                glow_r = pulse_r + 8
                glow = pygame.Surface(
                    (glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
                glow_a = int(120 * (1 - fuse_ratio) + 40)
                pygame.draw.circle(
                    glow, (255, 100, 80, glow_a),
                    (glow_r + 1, glow_r + 1), glow_r)
                surface.blit(
                    glow,
                    (int(self.x - glow_r - 1), int(self.y - glow_r - 1)))
            except Exception:
                pass
            pygame.draw.circle(surface, color,
                               (int(self.x), int(self.y)), pulse_r)
            pygame.draw.circle(surface, (40, 0, 0),
                               (int(self.x), int(self.y)), pulse_r, 2)
            # 上のヒューズ（小さな黄色いポチ）
            pygame.draw.circle(
                surface, (255, 240, 100),
                (int(self.x), int(self.y - pulse_r - 2)), 2)
        else:
            # 1. 衝撃のリング（複数、時間差で広がる）
            try:
                for ring in self.shock_rings:
                    if ring["life"] <= 0:
                        continue
                    r_ratio = 1.0 - (ring["life"] / ring["max"])
                    rr = int(ring["max_r"] * r_ratio)
                    if rr < 2:
                        continue
                    alpha = int(220 * (1 - r_ratio))
                    ring_surf = pygame.Surface(
                        (rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
                    # 太いリングと細いリングで二重に
                    pygame.draw.circle(
                        ring_surf, (*ring["color"], alpha),
                        (rr + 2, rr + 2), rr, 4)
                    pygame.draw.circle(
                        ring_surf, (255, 255, 255, alpha // 2),
                        (rr + 2, rr + 2), rr, 1)
                    surface.blit(
                        ring_surf, (int(self.x - rr - 2), int(self.y - rr - 2)))
            except Exception:
                pass

            # 2. 中心の発光球（時間で縮む）
            ratio = max(0.0, self.explosion_anim / self.explosion_max)
            try:
                r = int(RED_BOMB_RADIUS * ratio * 0.9)
                if r > 1:
                    # 多層グラデーション風
                    surf = pygame.Surface(
                        (r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                    # 外側：赤
                    pygame.draw.circle(
                        surf, (255, 80, 40, int(200 * ratio)),
                        (r + 1, r + 1), r)
                    # 中：オレンジ
                    inner_r1 = int(r * 0.7)
                    if inner_r1 > 0:
                        pygame.draw.circle(
                            surf, (255, 180, 60, int(220 * ratio)),
                            (r + 1, r + 1), inner_r1)
                    # 芯：白
                    inner_r2 = int(r * 0.35)
                    if inner_r2 > 0:
                        pygame.draw.circle(
                            surf, (255, 255, 240, int(240 * ratio)),
                            (r + 1, r + 1), inner_r2)
                    surface.blit(
                        surf, (int(self.x - r - 1), int(self.y - r - 1)))
            except Exception:
                pass

            # 3. 飛び散る破片
            for shard in self.shards:
                shard.draw(surface)


# ============================================================
# 雷（黄の能力）
# ============================================================
class LightningBolt:
    """ランダムなx位置に上から下に走る雷。
    ジャグドな本線、分岐する稲妻、衝撃の光輪、地面のフラッシュからなる。
    """
    def __init__(self, x):
        self.x = float(x)
        self.life = 500
        self.max_life = 500
        # 本線（縦方向のジャグドな点列）を生成
        self.main_segments = self._build_jagged_line()
        # 分岐（本線から横にはみ出す稲妻）
        self.branches = self._build_branches()
        # 各フレームで微妙に揺らすためのオフセット
        self.flicker = random.uniform(0, math.pi * 2)

    def _build_jagged_line(self):
        """縦方向にジャグドに走る点列を作る"""
        pts = []
        y = 0
        # ステップを細かくして、よりギザギザに
        while y < PLAY_H:
            # 縦の各位置でジャグドな振れ幅
            jitter = random.randint(-14, 14)
            pts.append((jitter, y))
            y += random.randint(10, 22)
        pts.append((random.randint(-6, 6), PLAY_H))
        return pts

    def _build_branches(self):
        """本線から横に枝分かれする小さな稲妻を生成"""
        branches = []
        # 何本か分岐させる
        branch_count = random.randint(3, 6)
        if len(self.main_segments) < 3:
            return branches
        for _ in range(branch_count):
            # 本線の途中から枝分かれ
            idx = random.randint(1, len(self.main_segments) - 2)
            start_x, start_y = self.main_segments[idx]
            # 左右どちらかへ伸びる
            direction = random.choice([-1, 1])
            branch_pts = [(start_x, start_y)]
            cur_x = start_x
            cur_y = start_y
            seg_count = random.randint(3, 6)
            for _ in range(seg_count):
                cur_x += direction * random.randint(6, 14)
                cur_y += random.randint(4, 14)
                # ランダムにジグザグ
                cur_x += random.randint(-4, 4)
                branch_pts.append((cur_x, cur_y))
                if cur_y >= PLAY_H:
                    break
            branches.append(branch_pts)
        return branches

    def update(self, dt):
        self.life -= dt
        self.flicker += dt / 30

    def is_dead(self):
        return self.life <= 0

    def draw(self, surface):
        ratio = max(0.0, self.life / self.max_life)
        # 序盤は明るく強く、後半でフェード
        if ratio > 0.75:
            fade = (1.0 - ratio) / 0.25     # 0→1 のフェードイン（瞬間的）
        else:
            fade = ratio / 0.75              # 1→0 のフェードアウト
        fade = max(0.0, min(1.0, fade))

        # 全体のちらつき（強→弱を高速に繰り返す）
        flicker_intensity = 0.7 + 0.3 * math.sin(self.flicker)
        intensity = fade * flicker_intensity

        # 雷の幅（点列用の Surface 幅）。本線+分岐で広め
        surf_w = 120
        try:
            surf = pygame.Surface((surf_w, PLAY_H), pygame.SRCALPHA)
            cx = surf_w // 2

            # 1. 外側のグロー（広い青白い光の柱）
            # 縦に走る発光柱を半透明で重ねる
            glow_alpha = int(60 * intensity)
            if glow_alpha > 0:
                for gw in (38, 26, 16):
                    pygame.draw.line(
                        surf, (140, 180, 255, glow_alpha // 2),
                        (cx, 0), (cx, PLAY_H), gw)

            # 2. 分岐の稲妻（本線より暗め、細め）
            branch_alpha = int(200 * intensity)
            if branch_alpha > 0:
                for branch in self.branches:
                    pts = [(cx + bx, by) for (bx, by) in branch]
                    if len(pts) >= 2:
                        # 太めの青白いグロー
                        pygame.draw.lines(
                            surf, (180, 210, 255, branch_alpha // 2),
                            False, pts, 4)
                        # 細い白い芯
                        pygame.draw.lines(
                            surf, (255, 255, 255, branch_alpha),
                            False, pts, 2)

            # 3. 本線：3層重ねで「コア」を作る
            main_pts = [(cx + jx, jy) for (jx, jy) in self.main_segments]
            if len(main_pts) >= 2:
                # 外側：青白い太いグロー
                pygame.draw.lines(
                    surf, (130, 170, 255, int(180 * intensity)),
                    False, main_pts, 10)
                # 中：明るい白
                pygame.draw.lines(
                    surf, (220, 230, 255, int(220 * intensity)),
                    False, main_pts, 5)
                # 芯：真っ白に近い細い線（クッキリ感）
                pygame.draw.lines(
                    surf, (255, 255, 255, int(255 * intensity)),
                    False, main_pts, 2)

            # 4. 各セグメントの端点に小さな光の粒（ノード）
            node_alpha = int(220 * intensity)
            for (jx, jy) in self.main_segments[::3]:
                pygame.draw.circle(
                    surf, (255, 255, 255, node_alpha),
                    (cx + jx, jy), 2)

            surface.blit(surf, (int(self.x - surf_w // 2), PLAY_TOP))

            # 5. 落雷地点（最下端）に円形の衝撃光を別途描画
            impact_alpha = int(220 * intensity)
            if impact_alpha > 0 and self.main_segments:
                last_jx, last_jy = self.main_segments[-1]
                impact_x = int(self.x + last_jx)
                impact_y = PLAY_TOP + int(last_jy)
                # 衝撃のリング（複数）
                imp_r = int(20 + (1 - ratio) * 25)
                imp_surf = pygame.Surface(
                    (imp_r * 2 + 4, imp_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    imp_surf, (200, 220, 255, impact_alpha // 2),
                    (imp_r + 2, imp_r + 2), imp_r)
                pygame.draw.circle(
                    imp_surf, (255, 255, 255, impact_alpha),
                    (imp_r + 2, imp_r + 2), max(2, imp_r // 2))
                surface.blit(
                    imp_surf, (impact_x - imp_r - 2, impact_y - imp_r - 2))

            # 6. 序盤の明るい全体フラッシュ（最初の数フレームのみ）
            if ratio > 0.85:
                flash_alpha = int(60 * (ratio - 0.85) / 0.15)
                flash = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
                flash.fill((220, 230, 255, flash_alpha))
                surface.blit(flash, (PLAY_LEFT, PLAY_TOP))
        except Exception:
            pass


# ============================================================
# 風の渦（緑の能力）
# ============================================================
class WindVortex:
    """前方向（上方向）に進む風の渦。
    成長しながら進み、内側に入ったブロックを巻き込んで壊す。
    """
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.start_y = float(y)              # 発射位置（飛距離計算用）
        self.vy = -GREEN_WIND_SPEED          # 上方向に進む
        self.life = GREEN_WIND_LIFE_MS
        self.max_life = GREEN_WIND_LIFE_MS
        self.radius = GREEN_WIND_RADIUS_START
        self.rotation = 0.0                  # 渦の回転角（描画用）
        # 巻き込んだブロックの一覧（描画でグルグル回す）
        # 各要素: {"x", "y", "color", "angle", "dist", "spiral_in"}
        self.captured = []

    def update(self, dt):
        # 進度（0.0 → 1.0）
        progress = 1.0 - max(0.0, self.life / self.max_life)
        # 速度の減衰：序盤は初速を維持、後半でスッと遅くなる
        # ease-in cubic を使って後半に減速が集中するカーブを作る
        ease = progress ** 3
        speed_ratio = 1.0 - (1.0 - GREEN_WIND_SPEED_MIN_RATIO) * ease
        self.vy = -GREEN_WIND_SPEED * speed_ratio

        self.y += self.vy
        self.life -= dt
        # 半径を時間とともに大きくする（拡散する渦）
        self.radius = (GREEN_WIND_RADIUS_START
                       + (GREEN_WIND_RADIUS_END - GREEN_WIND_RADIUS_START)
                       * progress)
        # 回転を速める
        self.rotation += dt * 0.015

        # 巻き込んだブロックを内側に吸い込む
        for cap in self.captured:
            cap["angle"] += dt * 0.018
            cap["dist"] = max(0, cap["dist"] - dt * 0.12)

    def is_dead(self):
        # 飛距離（発射位置からの移動量）が最大値を超えたら消滅
        traveled = self.start_y - self.y
        return (self.life <= 0 or
                self.y < PLAY_TOP - self.radius or
                traveled >= GREEN_WIND_MAX_DISTANCE)

    def contains(self, bx, by):
        """ブロック (bx, by) が渦の範囲内にあるか"""
        d = math.hypot(bx - self.x, by - self.y)
        return d < self.radius + BLOCK_SIZE * 0.6

    def capture(self, bx, by, color):
        """ブロックを巻き込む（見た目用に保持）"""
        angle = math.atan2(by - self.y, bx - self.x)
        dist = math.hypot(bx - self.x, by - self.y)
        self.captured.append({
            "color": color,
            "angle": angle,
            "dist": max(8.0, dist),
        })

    def draw(self, surface):
        # 渦本体：複数のリング + 螺旋ライン
        r = int(self.radius)
        if r < 2:
            return
        try:
            size = r * 2 + 12
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx_s = size // 2
            cy_s = size // 2

            life_ratio = max(0.0, self.life / self.max_life)
            # フェードイン・アウト
            fade = 1.0
            if life_ratio > 0.85:
                fade = (1.0 - life_ratio) / 0.15
            elif life_ratio < 0.2:
                fade = life_ratio / 0.2
            fade = max(0.0, min(1.0, fade))

            # 1. 外側のうっすら緑がかった円（ふんわり風圧）
            for i in range(3):
                rr = r - i * 6
                if rr <= 0:
                    continue
                alpha = int(50 * fade * (1 - i * 0.3))
                pygame.draw.circle(
                    surf, (140, 240, 180, alpha),
                    (cx_s, cy_s), rr)

            # 2. 螺旋ライン（3本）が回転して見える
            for spiral_i in range(3):
                points = []
                phase = self.rotation + spiral_i * (math.pi * 2 / 3)
                steps = 22
                for j in range(steps):
                    t = j / (steps - 1)
                    spiral_r = r * (0.15 + 0.85 * t)
                    a = phase + t * math.pi * 2.2
                    px = cx_s + math.cos(a) * spiral_r
                    py = cy_s + math.sin(a) * spiral_r
                    points.append((px, py))
                if len(points) >= 2:
                    # 外側ほど薄く
                    pygame.draw.lines(
                        surf, (200, 255, 220, int(180 * fade)),
                        False, points, 3)
                    # 中央付近のハイライト
                    if len(points) >= 8:
                        pygame.draw.lines(
                            surf, (255, 255, 255, int(220 * fade)),
                            False, points[:8], 2)

            # 3. 中心の白い目（風の目）
            eye_r = max(2, int(r * 0.2))
            pygame.draw.circle(
                surf, (240, 255, 245, int(220 * fade)),
                (cx_s, cy_s), eye_r)

            # 4. 巻き込まれたブロックの破片（小さく回転）
            for cap in self.captured:
                px = cx_s + math.cos(cap["angle"]) * cap["dist"]
                py = cy_s + math.sin(cap["angle"]) * cap["dist"]
                col = cap["color"]
                alpha = int(220 * fade)
                pygame.draw.circle(
                    surf, (*col, alpha),
                    (int(px), int(py)), 4)

            surface.blit(surf, (int(self.x - cx_s), int(self.y - cy_s)))
        except Exception:
            pass


# ============================================================
# ゲーム本体
# ============================================================
class CosmicGame:
    """避けゲー版コズミックモード"""

    def __init__(self, screen, fonts, images, score_manager):
        self.screen = screen
        self.fonts = fonts
        self.images = images
        self.score_manager = score_manager

        self.state = "idle"
        self.finished = False
        self.mode = MODE_COSMIC

        # 背景演出
        self.warp_stars = [WarpStar() for _ in range(STAR_COUNT)]
        self.warp_planets = self._make_planets()

        self._reset_game_state()

    def _make_planets(self):
        planet_imgs = self.images.get("planets", []) if self.images else []
        available = [img for img in planet_imgs if img is not None]
        planets = []
        for _ in range(PLANET_COUNT):
            if available:
                planets.append(WarpPlanet(random.choice(available)))
        return planets

    def _reset_game_state(self):
        self.score = 0
        self.elapsed_time = 0
        self.score_tick = 0

        # プレイヤー（プレイエリアの中央下寄り）
        self.player_x = PLAY_CX
        self.player_y = PLAY_BOTTOM - 100
        self.player_size = PLAYER_SIZE
        self.player_hp = PLAYER_MAX_HP
        # 最初のモンスターはランダム
        self.player_monster = random.choice(
            [MONSTER_FOR_BLOCK[b] for b in COLOR_BLOCK_TYPES])
        self.player_dx = 0
        self.player_dy = 0
        self.invincible_timer = 0
        # スピードアップブロックの効果残り時間
        self.speed_boost_timer = 0
        # シールドブロックの効果残り時間（岩を無効化）
        self.shield_timer = 0

        # ストック
        self.color_count = 0
        self.stocks = 0

        # ブロック
        self.blocks = []
        self.block_spawn_timer = 0

        # 能力の状態
        self.bombs = []
        self.blue_stream_timer = 0
        self.pending_bolts = []
        self.bolts = []
        self.wind_vortices = []          # 緑：風の渦
        self.dark_timer = 0
        self.dark_rock_timers = {}
        # 赤：爆竹（プレイヤー周囲の連続爆発）
        self.firecracker_timer = 0
        self.firecracker_spawn_tick = 0
        # 爆竹の小爆発（描画用）：{"x","y","life","max"}
        self.firecracker_pops = []

        # エフェクト
        self.particles = []
        self.damage_flash_timer = 0
        self.heal_flash_timer = 0
        # スピードブロック取得時の小さな演出
        self.speed_flash_timer = 0
        # シールドブロック取得時の小さな演出
        self.shield_flash_timer = 0

        self.score_saved = False

    # ============================================
    # 外部API
    # ============================================
    def start(self, mode):
        self.mode = mode
        self.state = "play"
        self.finished = False
        self._reset_game_state()

    def is_finished(self):
        return self.finished

    # ============================================
    # 更新
    # ============================================
    def update_play(self, dt, keys):
        self.elapsed_time += dt

        for star in self.warp_stars:
            star.update()
        for planet in self.warp_planets:
            planet.update()

        # 生存スコア
        self.score_tick += dt
        while self.score_tick >= 1000:
            self.score_tick -= 1000
            self.score += SCORE_DODGE_PER_SEC

        self._update_player(keys)
        self._update_blocks(dt)
        self._update_abilities(dt)
        self._check_player_block_collision()

        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)
        if self.damage_flash_timer > 0:
            self.damage_flash_timer = max(0, self.damage_flash_timer - dt)
        if self.heal_flash_timer > 0:
            self.heal_flash_timer = max(0, self.heal_flash_timer - dt)
        if self.speed_flash_timer > 0:
            self.speed_flash_timer = max(0, self.speed_flash_timer - dt)
        if self.blue_stream_timer > 0:
            self.blue_stream_timer = max(0, self.blue_stream_timer - dt)
        if self.dark_timer > 0:
            self.dark_timer = max(0, self.dark_timer - dt)
        if self.firecracker_timer > 0:
            self.firecracker_timer = max(0, self.firecracker_timer - dt)
        if self.speed_boost_timer > 0:
            self.speed_boost_timer = max(0, self.speed_boost_timer - dt)
        if self.shield_timer > 0:
            self.shield_timer = max(0, self.shield_timer - dt)
        if self.shield_flash_timer > 0:
            self.shield_flash_timer = max(0, self.shield_flash_timer - dt)

        for p in self.particles[:]:
            p.update(dt)
            if p.is_dead():
                self.particles.remove(p)

        if self.player_hp <= 0:
            self._end_game()

    # --- プレイヤー -----------------------------------------
    def _update_player(self, keys):
        speed = PLAYER_SPEED
        if self.player_monster == "red" and self.stocks > 0:
            speed = int(PLAYER_SPEED * RED_SPEED_MULT)
        elif self.player_monster == "green" and self.stocks > 0:
            speed = int(PLAYER_SPEED * GREEN_SPEED_MULT)
        # スピードアップブロック効果（モンスター能力に重ねがけ）
        if self.speed_boost_timer > 0:
            speed = int(speed * SPEED_BOOST_MULT)

        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += speed

        self.player_dx = dx
        self.player_dy = dy
        self.player_x += dx
        self.player_y += dy

        half = self.player_size // 2
        # プレイエリアの境界で止まる
        if self.player_x < PLAY_LEFT + half:
            self.player_x = PLAY_LEFT + half
        elif self.player_x > PLAY_RIGHT - half:
            self.player_x = PLAY_RIGHT - half
        if self.player_y < PLAY_TOP + half:
            self.player_y = PLAY_TOP + half
        elif self.player_y > PLAY_BOTTOM - half:
            self.player_y = PLAY_BOTTOM - half

    # --- ブロック -------------------------------------------
    def _current_fall_speed(self):
        # 上限なし：時間が経つほど無限に速くなる（過酷化）
        secs = self.elapsed_time / 1000.0
        return BLOCK_SPEED_BASE + BLOCK_SPEED_RAMP * secs

    def _current_spawn_interval(self):
        secs = self.elapsed_time / 1000.0
        return max(BLOCK_SPAWN_INTERVAL_MIN,
                   BLOCK_SPAWN_INTERVAL_START - BLOCK_SPAWN_INTERVAL_RAMP * secs)

    def _update_blocks(self, dt):
        self.block_spawn_timer += dt
        if self.block_spawn_timer >= self._current_spawn_interval():
            self.block_spawn_timer = 0
            self._spawn_block()

        base_speed = self._current_fall_speed()
        dark_active = (self.player_monster == "dark" and self.dark_timer > 0)

        for block in self.blocks[:]:
            slow_factor = 1.0
            in_dark_area = False
            if dark_active:
                d = math.hypot(block["x"] - self.player_x,
                               block["y"] - self.player_y)
                if d < DARK_SLOW_RADIUS:
                    slow_factor = DARK_SLOW_FACTOR
                    in_dark_area = True

            block["y"] += base_speed * slow_factor

            # 横方向の速度（緑の風で弾かれた時のみ非ゼロ）
            vx = block.get("vx", 0.0)
            if vx != 0.0:
                block["x"] += vx
                # 摩擦で減衰（毎フレーム少しずつ弱まる）
                block["vx"] = vx * 0.94
                if abs(block["vx"]) < 0.05:
                    block["vx"] = 0.0

            bid = id(block)
            if dark_active and in_dark_area and block["type"] == BLOCK_ROCK:
                self.dark_rock_timers[bid] = self.dark_rock_timers.get(bid, 0) + dt
                if self.dark_rock_timers[bid] >= DARK_ROCK_BREAK_MS:
                    self._spawn_particles(block["x"], block["y"],
                                          BLOCK_COLORS[BLOCK_ROCK], count=10)
                    self.blocks.remove(block)
                    self.dark_rock_timers.pop(bid, None)
                    self.score += SCORE_BREAK_BLOCK
                    continue
            else:
                self.dark_rock_timers.pop(bid, None)

            # プレイエリアの下端を超えたら消す
            if block["y"] - BLOCK_SIZE > PLAY_BOTTOM:
                self.blocks.remove(block)
                self.dark_rock_timers.pop(bid, None)
                continue
            # 横方向にプレイエリアから出たら消す（緑の風で弾き出された場合）
            if (block["x"] + BLOCK_SIZE < PLAY_LEFT or
                    block["x"] - BLOCK_SIZE > PLAY_RIGHT):
                self.blocks.remove(block)
                self.dark_rock_timers.pop(bid, None)

    def _current_block_weights(self):
        """経過時間に応じてブロック種類の出現重みを線形補間で求める。
        ただし COLOR_BLOCK_GRACE_MS 未満は色ブロックを出現させない。"""
        secs = self.elapsed_time / 1000.0
        t = min(1.0, secs / WEIGHT_RAMP_SEC)   # 0.0〜1.0
        result = {}
        color_allowed = self.elapsed_time >= COLOR_BLOCK_GRACE_MS
        # 両セットに必ず同じキーがある前提
        for key in BLOCK_WEIGHTS_START:
            start = BLOCK_WEIGHTS_START[key]
            late  = BLOCK_WEIGHTS_LATE.get(key, start)
            w = start + (late - start) * t
            # 序盤は色ブロックを完全に抑制
            if not color_allowed and key in COLOR_BLOCK_TYPES:
                w = 0
            result[key] = w
        return result

    def _spawn_block(self):
        margin = BLOCK_SIZE + 6
        # プレイエリアの幅内でスポーン
        x = random.randint(PLAY_LEFT + margin, PLAY_RIGHT - margin)
        # プレイエリアの上端より少し上から落とす
        y = PLAY_TOP - margin
        weights_map = self._current_block_weights()
        types = list(weights_map.keys())
        weights = list(weights_map.values())
        block_type = random.choices(types, weights=weights, k=1)[0]
        self.blocks.append({
            "type": block_type,
            "x": float(x),
            "y": float(y),
        })

    # --- 衝突 -----------------------------------------------
    def _check_player_block_collision(self):
        p_half = self.player_size // 2
        b_radius = BLOCK_SIZE
        for block in self.blocks[:]:
            closest_x = max(self.player_x - p_half,
                            min(block["x"], self.player_x + p_half))
            closest_y = max(self.player_y - p_half,
                            min(block["y"], self.player_y + p_half))
            ddx = block["x"] - closest_x
            ddy = block["y"] - closest_y
            if ddx * ddx + ddy * ddy >= b_radius * b_radius:
                continue
            self._on_player_hit_block(block)

    def _on_player_hit_block(self, block):
        btype = block["type"]
        bx, by = block["x"], block["y"]
        color = BLOCK_COLORS[btype]

        if btype == BLOCK_ROCK:
            if self.invincible_timer > 0:
                return
            # シールド中：HPを減らさず、岩だけ砕いて派手にエフェクト
            if self.shield_timer > 0:
                self._spawn_particles(bx, by, color, count=10)
                # シールドの金色火花も足す
                self._spawn_particles(
                    bx, by, BLOCK_COLORS[BLOCK_SHIELD], count=8)
                self.blocks.remove(block)
                self.dark_rock_timers.pop(id(block), None)
                return
            self.player_hp -= 1
            self.damage_flash_timer = 300
            self.invincible_timer = 600
            self._spawn_particles(bx, by, color, count=12)
            self.blocks.remove(block)
            self.dark_rock_timers.pop(id(block), None)

        elif btype == BLOCK_PURPLE:
            if self.player_hp < PLAYER_HP_CAP:
                self.player_hp += 1
            self.heal_flash_timer = 300
            self._spawn_particles(bx, by, color, count=14)
            self.blocks.remove(block)

        elif btype == BLOCK_SPEED:
            # スピードアップブロック：移動速度を一時的にアップ
            self.speed_boost_timer = SPEED_BOOST_DURATION
            self.speed_flash_timer = 300
            self._spawn_particles(bx, by, color, count=14)
            # ホワイトで爽快感を足す
            self._spawn_particles(bx, by, (220, 250, 255), count=6)
            self.blocks.remove(block)

        elif btype == BLOCK_SHIELD:
            # シールドブロック：岩のダメージを一時的に無効化
            self.shield_timer = SHIELD_DURATION
            self.shield_flash_timer = 300
            self._spawn_particles(bx, by, color, count=14)
            # 白い光も少し足す
            self._spawn_particles(bx, by, (255, 250, 220), count=6)
            self.blocks.remove(block)

        elif btype in COLOR_BLOCK_TYPES:
            # 色ブロック：その色のモンスターに変身（ストックは増えない）
            self._change_monster(btype)
            self._spawn_particles(bx, by, color, count=10)
            self.blocks.remove(block)

        elif btype == BLOCK_NORMAL:
            # 白ブロック：ストック+1（現在のモンスターのエネルギー）
            if self.stocks < MAX_STOCKS:
                self.stocks += 1
                # 軽い吸収エフェクト：白を多めに飛ばす
                self._spawn_particles(bx, by, (255, 255, 255), count=12)
            else:
                # ストック満タンなら普通に消えるだけ
                self._spawn_particles(bx, by, color, count=6)
            self.blocks.remove(block)

        else:
            # その他（念のための保険）
            self._spawn_particles(bx, by, color, count=6)
            self.blocks.remove(block)

    # --- 色ブロック取得 / 変身 -----------------------------
    def _change_monster(self, block_type):
        """色ブロックに当たった時：そのモンスターに変身。
        ストックは維持する（白で貯めたエネルギーが新しい形態で使える）。
        ただし、別の色に変わる場合は進行中の状態系能力を停止する。"""
        monster = MONSTER_FOR_BLOCK[block_type]
        if self.player_monster != monster:
            self._end_current_ability()
            self.player_monster = monster
            # ストックはあえて維持（取った瞬間に使える形態に切り替えるイメージ）

    def _end_current_ability(self):
        """色変えに伴って状態系の能力を止める"""
        self.blue_stream_timer = 0
        self.dark_timer = 0
        self.dark_rock_timers.clear()
        self.firecracker_timer = 0
        self.firecracker_spawn_tick = 0

    # --- スペースキー：能力発動 ----------------------------
    def _trigger_ability(self):
        if self.stocks <= 0:
            return
        if self.player_monster == "red":
            self._ability_red()
        elif self.player_monster == "blue":
            self._ability_blue()
        elif self.player_monster == "yellow":
            self._ability_yellow()
        elif self.player_monster == "green":
            self._ability_green()
        elif self.player_monster == "dark":
            self._ability_dark()
        else:
            return
        self.stocks -= 1

    def _ability_red(self):
        # 爆弾を投擲
        self.bombs.append(Bomb(
            self.player_x, self.player_y - self.player_size // 2,
            vx=0, vy=-RED_BOMB_SPEED))
        # 同時にプレイヤー周囲で爆竹がスタート
        self.firecracker_timer = RED_FIRECRACKER_DURATION
        self.firecracker_spawn_tick = 0

    def _ability_blue(self):
        self.blue_stream_timer = BLUE_STREAM_MS

    def _ability_yellow(self):
        for i in range(YELLOW_BOLT_COUNT):
            self.pending_bolts.append({
                "delay": YELLOW_BOLT_DELAY * (i + 1),
                "x": random.randint(PLAY_LEFT + 20, PLAY_RIGHT - 20),
            })

    def _ability_green(self):
        # 前方向（プレイヤーの上方向）に風の渦を一発放つ
        self.wind_vortices.append(
            WindVortex(self.player_x,
                       self.player_y - self.player_size // 2))

    def _ability_dark(self):
        self.dark_timer = DARK_DURATION

    # --- 能力の進行更新 ------------------------------------
    def _update_abilities(self, dt):
        # 爆弾
        for bomb in self.bombs[:]:
            was_exploded = bomb.exploded
            bomb.update(dt)
            if (not was_exploded) and bomb.exploded:
                self._explode_at(bomb.x, bomb.y, RED_BOMB_RADIUS)
            if bomb.is_dead():
                self.bombs.remove(bomb)

        # 赤：爆竹（プレイヤー周囲の連続爆発）
        if self.firecracker_timer > 0:
            self.firecracker_spawn_tick += dt
            while self.firecracker_spawn_tick >= RED_FIRECRACKER_INTERVAL:
                self.firecracker_spawn_tick -= RED_FIRECRACKER_INTERVAL
                self._spawn_firecracker_pop()
        # 既存の小爆発を更新（描画用にライフを減らすだけ）
        for pop in self.firecracker_pops[:]:
            pop["life"] -= dt
            if pop["life"] <= 0:
                self.firecracker_pops.remove(pop)

        # 青：水流（破壊ではなく押し流す）
        # 水流の範囲内のブロックは上に押し戻される。
        # プレイヤーの少し上以降のy範囲（プレイエリア上端〜プレイヤー上端）にあるブロックが対象。
        if self.blue_stream_timer > 0:
            stream_left = self.player_x - BLUE_STREAM_WIDTH / 2
            stream_right = self.player_x + BLUE_STREAM_WIDTH / 2
            top_y = self.player_y - self.player_size // 2
            push = BLUE_PUSH_SPEED
            for block in self.blocks[:]:
                if (stream_left <= block["x"] <= stream_right and
                        block["y"] < top_y):
                    # 上方向に押す
                    block["y"] -= push
                    # 画面上端を超えたら破壊判定
                    # 「上端に当たった」＝完全に飛び出すまで押し続けた場合
                    if block["y"] + BLOCK_SIZE < PLAY_TOP:
                        # 上端で破壊：軽くスコア（避ける用途中心のため通常より低め）
                        self._spawn_particles(
                            block["x"], PLAY_TOP,
                            BLOCK_COLORS.get(block["type"], WHITE), count=6)
                        # 飛び散る水しぶき
                        self._spawn_particles(
                            block["x"], PLAY_TOP,
                            (180, 230, 255), count=8)
                        self.blocks.remove(block)
                        self.score += SCORE_BREAK_BLOCK // 2

        # 黄：保留中の雷を発火
        for pb in self.pending_bolts[:]:
            pb["delay"] -= dt
            if pb["delay"] <= 0:
                bolt = LightningBolt(pb["x"])
                self.bolts.append(bolt)
                self._lightning_hit(bolt.x)
                self.pending_bolts.remove(pb)

        for bolt in self.bolts[:]:
            bolt.update(dt)
            if bolt.is_dead():
                self.bolts.remove(bolt)

        # 緑：風の渦（プレイエリアを縦断しながら、当たったブロックを左右に弾く）
        # ブロックは破壊しない。渦の中心より右にあるブロックは右へ、左にあるブロックは左へ。
        for vortex in self.wind_vortices[:]:
            vortex.update(dt)
            for block in self.blocks[:]:
                if vortex.contains(block["x"], block["y"]):
                    # 渦中心からブロックの相対位置で弾く向きを決める
                    dx = block["x"] - vortex.x
                    if dx == 0:
                        # 真上にいる場合はランダムに左右どちらかへ
                        dx = random.choice([-1.0, 1.0])
                    direction = 1.0 if dx > 0 else -1.0
                    # 既存の vx に加算（複数渦に押されたらより強く弾かれる）
                    current_vx = block.get("vx", 0.0)
                    # 弾き速度はランダムで少しばらつかせる
                    kick = direction * random.uniform(3.0, 5.0)
                    block["vx"] = current_vx + kick
                    # 弾かれた瞬間の小さな視覚効果
                    self._spawn_particles(
                        block["x"], block["y"],
                        (180, 240, 200), count=3)
            if vortex.is_dead():
                self.wind_vortices.remove(vortex)

    def _explode_at(self, cx, cy, radius):
        for block in self.blocks[:]:
            d = math.hypot(block["x"] - cx, block["y"] - cy)
            if d < radius:
                # 通常より派手にパーティクルを生成
                self._spawn_particles(
                    block["x"], block["y"],
                    BLOCK_COLORS.get(block["type"], WHITE), count=12)
                # オレンジの火花も追加
                self._spawn_particles(
                    block["x"], block["y"], (255, 180, 60), count=4)
                self.blocks.remove(block)
                self.score += SCORE_BREAK_BLOCK
        # 爆発本体の火花を大幅増量
        for _ in range(40):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius * 0.9)
            # 火っぽい色をランダムに
            col = random.choice([
                (255, 230, 150),
                (255, 180,  60),
                (255, 120,  40),
                (255,  70,  30),
            ])
            self._spawn_particles(
                cx + math.cos(ang) * dist,
                cy + math.sin(ang) * dist,
                col, count=1)

    def _spawn_firecracker_pop(self):
        """プレイヤー周囲に小さな爆発を1つ発生させる。
        範囲内に当たったブロックは破壊する（岩・色ブロック関係なく）。
        """
        # 半径80px の円の中のランダムな位置
        ang = random.uniform(0, 2 * math.pi)
        # 中心寄りはやや少なく、外側寄りに出やすく（リング状の感じ）
        dist = random.uniform(RED_FIRECRACKER_RADIUS * 0.3,
                              RED_FIRECRACKER_RADIUS)
        px = self.player_x + math.cos(ang) * dist
        py = self.player_y + math.sin(ang) * dist
        # プレイエリア内に収める
        px = max(PLAY_LEFT + 4, min(PLAY_RIGHT - 4, px))
        py = max(PLAY_TOP + 4, min(PLAY_BOTTOM - 4, py))
        # 描画用に登録
        life = random.randint(180, 280)
        self.firecracker_pops.append({
            "x": float(px),
            "y": float(py),
            "life": life,
            "max":  life,
            "r":    random.randint(14, 22),
            # ランダムな火っぽい色
            "color": random.choice([
                (255, 230, 120),
                (255, 180,  60),
                (255, 120,  40),
            ]),
        })
        # 火花
        for _ in range(6):
            self._spawn_particles(
                px, py,
                random.choice([
                    (255, 230, 150),
                    (255, 180,  60),
                    (255, 120,  40),
                ]),
                count=1)
        # 範囲内のブロックを破壊
        for block in self.blocks[:]:
            d = math.hypot(block["x"] - px, block["y"] - py)
            if d < RED_FIRECRACKER_BLOCK_HIT_RADIUS:
                self._spawn_particles(
                    block["x"], block["y"],
                    BLOCK_COLORS.get(block["type"], WHITE), count=8)
                self.blocks.remove(block)
                self.score += SCORE_BREAK_BLOCK

    def _lightning_hit(self, x):
        for block in self.blocks[:]:
            if abs(block["x"] - x) < YELLOW_BOLT_RADIUS:
                self._spawn_particles(
                    block["x"], block["y"],
                    BLOCK_COLORS.get(block["type"], WHITE), count=8)
                self.blocks.remove(block)
                self.score += SCORE_BREAK_BLOCK

    # --- パーティクル --------------------------------------
    def _spawn_particles(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(BlockParticle(x, y, color))

    # --- ゲームオーバー ------------------------------------
    def _end_game(self):
        if self.score_saved:
            return
        self.score_saved = True
        try:
            self.score_manager.add_score(
                self.mode, self.score, self.elapsed_time, 0)
        except Exception:
            pass
        self.state = "gameover"

    # ============================================
    # 描画
    # ============================================
    def draw_play(self):
        screen = self.screen
        screen.fill(BLACK)

        # ----------------------------------------
        # 1. 右サイドバー：背景アニメ（流れる星と惑星）
        # ----------------------------------------
        # 右パネル全体を背景色で塗る
        right_panel_rect = pygame.Rect(PLAY_RIGHT, 0, RIGHT_PANEL_W, HEIGHT)
        pygame.draw.rect(screen, (8, 8, 20), right_panel_rect)
        # 右パネルだけにクリッピングして星と惑星を描く
        screen.set_clip(right_panel_rect)
        for planet in self.warp_planets:
            planet.draw(screen)
        for star in self.warp_stars:
            star.draw(screen)
        screen.set_clip(None)

        # ----------------------------------------
        # 2. 左サイドバー：HP・モンスター情報・ストック
        # ----------------------------------------
        self._draw_left_panel()

        # ----------------------------------------
        # 3. 上部バー：スコアと時間
        # ----------------------------------------
        self._draw_top_bar()

        # ----------------------------------------
        # 4. プレイエリア（中央）
        # ----------------------------------------
        play_rect = pygame.Rect(PLAY_LEFT, PLAY_TOP, PLAY_W, PLAY_H)
        # プレイエリアの背景（少し明るくして領域がわかるように）
        pygame.draw.rect(screen, (15, 15, 25), play_rect)

        # ここから先はプレイエリア内にクリッピング
        screen.set_clip(play_rect)

        # 黒能力のスロー圏可視化
        if self.player_monster == "dark" and self.dark_timer > 0:
            try:
                ring = pygame.Surface(
                    (DARK_SLOW_RADIUS * 2, DARK_SLOW_RADIUS * 2),
                    pygame.SRCALPHA)
                a = int(40 + 20 * math.sin(self.elapsed_time / 200))
                pygame.draw.circle(ring, (140, 80, 220, a),
                                   (DARK_SLOW_RADIUS, DARK_SLOW_RADIUS),
                                   DARK_SLOW_RADIUS)
                pygame.draw.circle(ring, (180, 120, 240, 100),
                                   (DARK_SLOW_RADIUS, DARK_SLOW_RADIUS),
                                   DARK_SLOW_RADIUS, 2)
                screen.blit(ring,
                            (int(self.player_x - DARK_SLOW_RADIUS),
                             int(self.player_y - DARK_SLOW_RADIUS)))
            except Exception:
                pass

        # 青の水流（プレイエリアの上端から下端まで）
        if self.blue_stream_timer > 0:
            self._draw_water_stream(screen)

        # ブロック
        for block in self.blocks:
            self._draw_block(block)

        # 爆弾
        for bomb in self.bombs:
            bomb.draw(screen)

        # 雷
        for bolt in self.bolts:
            bolt.draw(screen)

        # 風の渦（緑）
        for vortex in self.wind_vortices:
            vortex.draw(screen)

        # 赤：爆竹の小爆発（プレイヤーの周りでポンポン光る）
        self._draw_firecracker_pops(screen)

        # パーティクル
        for p in self.particles:
            p.draw(screen)

        # プレイヤー
        self._draw_player()

        # ダメージフラッシュ（プレイエリア内だけ）
        if self.damage_flash_timer > 0:
            ratio = self.damage_flash_timer / 300
            alpha = int(120 * ratio)
            flash = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
            flash.fill((255, 0, 0, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        # 回復フラッシュ
        if self.heal_flash_timer > 0:
            ratio = self.heal_flash_timer / 300
            alpha = int(100 * ratio)
            flash = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
            flash.fill((180, 90, 220, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        # スピードブロック取得フラッシュ
        if self.speed_flash_timer > 0:
            ratio = self.speed_flash_timer / 300
            alpha = int(90 * ratio)
            flash = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
            flash.fill((80, 230, 240, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        # シールドブロック取得フラッシュ
        if self.shield_flash_timer > 0:
            ratio = self.shield_flash_timer / 300
            alpha = int(90 * ratio)
            flash = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
            flash.fill((255, 215, 90, alpha))
            screen.blit(flash, (PLAY_LEFT, PLAY_TOP))

        screen.set_clip(None)

        # プレイエリアの枠線
        pygame.draw.rect(screen, (60, 60, 90), play_rect, 2)

        # 操作ヒント（プレイエリア下端外）
        mini_font = self.fonts["mini"]
        hint = mini_font.render(
            "WASD/Arrows  SPACE: ability", True, GRAY)
        hint_rect = hint.get_rect(center=(PLAY_CX, HEIGHT - 12))
        screen.blit(hint, hint_rect)

    def _draw_block(self, block):
        color = BLOCK_COLORS.get(block["type"], WHITE)
        x, y = block["x"], block["y"]

        if block["type"] == BLOCK_ROCK:
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, (60, 40, 25), 2)
            for dx, dy in [(-4, -2), (3, 3), (-1, -6)]:
                pygame.draw.circle(
                    self.screen, (90, 60, 35),
                    (int(x + dx), int(y + dy)), 2)
        elif block["type"] == BLOCK_PURPLE:
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, WHITE, 2)
            pygame.draw.line(self.screen, WHITE,
                             (x - 6, y), (x + 6, y), 3)
            pygame.draw.line(self.screen, WHITE,
                             (x, y - 6), (x, y + 6), 3)
        elif block["type"] == BLOCK_SPEED:
            # スピードブロック：シアンの六角形に稲妻マーク
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, WHITE, 2)
            # 中央に稲妻（>>＞ のような矢印）
            bolt = [
                (x - 2, y - 8),
                (x + 4, y - 1),
                (x + 0, y + 0),
                (x + 3, y + 8),
                (x - 4, y + 1),
                (x + 0, y + 0),
                (x - 2, y - 8),
            ]
            try:
                pygame.draw.polygon(self.screen, WHITE, bolt)
            except Exception:
                pass
        elif block["type"] == BLOCK_SHIELD:
            # シールドブロック：金色の六角形に盾マーク
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, WHITE, 2)
            # 中央に盾の形（上が平らで下が尖る五角形）
            shield_pts = [
                (x - 6, y - 7),
                (x + 6, y - 7),
                (x + 6, y + 1),
                (x + 0, y + 8),
                (x - 6, y + 1),
            ]
            try:
                pygame.draw.polygon(self.screen, WHITE, shield_pts)
                # 盾の中の小さな線（飾り）
                pygame.draw.line(self.screen, color,
                                 (x, y - 4), (x, y + 4), 2)
            except Exception:
                pass
        elif block["type"] in COLOR_BLOCK_TYPES:
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            outline = WHITE if block["type"] != BLOCK_DARK else (200, 200, 220)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, outline, 2)
            pygame.draw.circle(self.screen, WHITE,
                               (int(x), int(y)), 3)
        else:
            self._draw_hexagon(x, y, BLOCK_SIZE, color)
            self._draw_hexagon_outline(x, y, BLOCK_SIZE, (170, 170, 170), 2)

    def _draw_hexagon(self, cx, cy, radius, color):
        points = []
        for i in range(6):
            angle = math.radians(-90 + i * 60)
            points.append((cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle)))
        pygame.draw.polygon(self.screen, color, points)

    def _draw_hexagon_outline(self, cx, cy, radius, color, width):
        points = []
        for i in range(6):
            angle = math.radians(-90 + i * 60)
            points.append((cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle)))
        pygame.draw.polygon(self.screen, color, points, width)

    def _draw_firecracker_pops(self, screen):
        """爆竹の小爆発を描く。
        プレイヤー周辺で短い時間だけ光る小さな円＋発光のグロー＋外側のリング。
        さらに、爆竹発動中はプレイヤーの周囲にうっすらしたオレンジオーラ。
        """
        # 1. 爆竹発動中の周囲オーラ（active な間ずっと表示）
        if self.firecracker_timer > 0:
            try:
                ratio = self.firecracker_timer / RED_FIRECRACKER_DURATION
                # 残り時間が少ない時に脈動を速める
                pulse_speed = 100 if ratio > 0.3 else 50
                pulse = 0.5 + 0.5 * math.sin(
                    self.elapsed_time / pulse_speed)
                aura_size = RED_FIRECRACKER_RADIUS * 2 + 20
                aura = pygame.Surface(
                    (aura_size, aura_size), pygame.SRCALPHA)
                center = aura_size // 2
                # 内側の暖色オーラ
                inner_alpha = int(35 + 25 * pulse)
                pygame.draw.circle(
                    aura, (255, 140, 60, inner_alpha),
                    (center, center), aura_size // 2 - 10)
                # 外周の縁
                edge_alpha = int(120 + 60 * pulse)
                pygame.draw.circle(
                    aura, (255, 200, 100, edge_alpha),
                    (center, center), aura_size // 2 - 10, 2)
                screen.blit(aura,
                            (int(self.player_x - center),
                             int(self.player_y - center)))
            except Exception:
                pass

        # 2. 個別の小爆発
        for pop in self.firecracker_pops:
            try:
                life_ratio = max(0.0, pop["life"] / pop["max"])
                # 出現直後は小さく光って広がり、消える直前にフェード
                if life_ratio > 0.7:
                    grow = 1.0 - (life_ratio - 0.7) / 0.3  # 0→1
                else:
                    grow = life_ratio / 0.7                # 1→0
                grow = max(0.0, min(1.0, grow))
                r = max(2, int(pop["r"] * grow))
                size = r * 2 + 6
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                c = pop["color"]
                cs = size // 2
                # 外側のグロー（淡い）
                pygame.draw.circle(
                    surf, (*c, int(120 * grow)),
                    (cs, cs), r)
                # 内側の発光（明るめ）
                inner_r = max(1, int(r * 0.65))
                pygame.draw.circle(
                    surf, (255, 230, 180, int(220 * grow)),
                    (cs, cs), inner_r)
                # 中央の白い芯
                core_r = max(1, int(r * 0.3))
                pygame.draw.circle(
                    surf, (255, 255, 240, int(255 * grow)),
                    (cs, cs), core_r)
                # 外側にチラつくリング（爆竹っぽさ）
                if r > 5 and grow > 0.5:
                    pygame.draw.circle(
                        surf, (*c, int(180 * grow)),
                        (cs, cs), r, 1)
                screen.blit(
                    surf,
                    (int(pop["x"] - cs), int(pop["y"] - cs)))
            except Exception:
                pass

    def _draw_water_stream(self, screen):
        """青の水流エフェクト。
        構成：
          1. 中央が明るく外側に向かって薄れるグラデーション柱
          2. ゆっくり上下にうねる輪郭線
          3. 縦に上昇していく泡（複数サイズ）
          4. プレイヤー上端での水の輝き（着水点の光）
        """
        # 全体のフェード係数（出現直後と消える直前は薄く）
        ratio = self.blue_stream_timer / BLUE_STREAM_MS
        # フェードイン・アウト用：両端で薄くなるカーブ
        fade = 1.0
        if ratio > 0.9:
            fade = (1.0 - ratio) / 0.1
        elif ratio < 0.15:
            fade = ratio / 0.15
        fade = max(0.0, min(1.0, fade))

        # 描画位置
        w = BLUE_STREAM_WIDTH
        top_y = PLAY_TOP
        bottom_y = self.player_y - self.player_size // 2
        height = max(1, bottom_y - top_y)
        cx_screen = int(self.player_x)
        t = self.elapsed_time  # 時間（ms）

        try:
            stream = pygame.Surface((w + 40, height), pygame.SRCALPHA)
            sw, sh = stream.get_size()
            cx = sw // 2

            # ----------------------------------------
            # 1. グラデーション柱（横方向に色の濃淡）
            # ----------------------------------------
            # 中心から外に向かって透明度を下げる
            # 縦方向は上に行くほど少しだけ細くなる（噴き上がる感）
            for offset in range(-w // 2 - 18, w // 2 + 18):
                # 中心からの距離（0〜1）
                dx = abs(offset) / (w // 2 + 18)
                if dx > 1:
                    continue
                # 中心ほど不透明、外側ほど透明
                # 中心：明るい白寄り / 外：青
                alpha = int(180 * (1 - dx ** 1.5) * fade)
                if alpha <= 0:
                    continue
                # 色を中心からの距離で混ぜる
                if dx < 0.3:
                    color = (200, 240, 255, alpha)   # 中心：白に近い水色
                elif dx < 0.6:
                    color = (120, 200, 255, alpha)
                else:
                    color = (60, 140, 240, alpha)    # 外側：濃い青
                pygame.draw.line(stream, color,
                                 (cx + offset, 0),
                                 (cx + offset, sh))

            # ----------------------------------------
            # 2. うねる輪郭線（左右の波形）
            # ----------------------------------------
            line_alpha = int(200 * fade)
            if line_alpha > 0:
                left_points = []
                right_points = []
                for y in range(0, sh, 4):
                    # 時間と位置で揺らす
                    wave_l = math.sin((y + t * 0.4) / 22.0) * 6
                    wave_r = math.sin((y + t * 0.4) / 22.0 + math.pi / 3) * 6
                    left_points.append((cx - w // 2 + wave_l, y))
                    right_points.append((cx + w // 2 + wave_r, y))
                if len(left_points) >= 2:
                    pygame.draw.lines(
                        stream, (180, 230, 255, line_alpha),
                        False, left_points, 2)
                if len(right_points) >= 2:
                    pygame.draw.lines(
                        stream, (180, 230, 255, line_alpha),
                        False, right_points, 2)

            # ----------------------------------------
            # 3. 上昇する泡（時間で位置を計算）
            # ----------------------------------------
            # 13個の泡。各泡は速度・サイズ・横位置がパラメータで決まり、
            # y位置 = (時間 * 速度) mod 高さ で循環する
            bubble_count = 13
            for i in range(bubble_count):
                # 各泡固有のパラメータ（iで決定論的に決める）
                speed = 0.15 + (i % 5) * 0.05         # 0.15〜0.35 px/ms
                size = 2 + (i % 4)                    # 2〜5 px
                x_base = ((i * 37) % (w - 16)) - (w // 2 - 8)
                # 横方向にちょっと揺れる
                x_wave = math.sin((t + i * 200) / 300) * 4
                # y は下から上へ循環
                cycle = sh + 20
                y = (cycle - ((t * speed + i * 90) % cycle)) - 10
                # 中心に近い泡は不透明
                dist_from_center = abs(x_base) / (w // 2)
                a = int(220 * (1 - dist_from_center * 0.8) * fade)
                if a <= 0:
                    continue
                # 泡：白い円＋細い縁
                bx = int(cx + x_base + x_wave)
                by = int(y)
                if 0 <= by < sh:
                    pygame.draw.circle(stream, (220, 240, 255, a),
                                       (bx, by), size)
                    if size >= 3:
                        # 中央のハイライト
                        pygame.draw.circle(
                            stream, (255, 255, 255, min(255, a + 40)),
                            (bx - 1, by - 1), max(1, size - 2))

            # 全体を画面に貼る
            screen.blit(stream, (cx_screen - sw // 2, top_y))

            # ----------------------------------------
            # 4. 着水点の光（プレイヤー直上で光る）
            # ----------------------------------------
            glow_r = 30
            glow_a = int(180 * fade * (0.7 + 0.3 * math.sin(t / 150)))
            if glow_a > 0:
                glow = pygame.Surface((glow_r * 2, glow_r * 2),
                                      pygame.SRCALPHA)
                pygame.draw.circle(glow, (180, 230, 255, glow_a),
                                   (glow_r, glow_r), glow_r)
                pygame.draw.circle(glow, (240, 250, 255, glow_a),
                                   (glow_r, glow_r), glow_r // 2)
                screen.blit(glow,
                            (cx_screen - glow_r, bottom_y - glow_r))
        except Exception:
            pass

    def _draw_player(self):
        # 無敵中は点滅
        if self.invincible_timer > 0:
            if (self.invincible_timer // 80) % 2 != 0:
                return  # この瞬間は描画スキップ

        # スピードブースト中のスピードライン（後方に流す）
        if self.speed_boost_timer > 0:
            try:
                half = self.player_size // 2
                # 移動方向に応じて反対側に短いラインを描く
                ratio = self.speed_boost_timer / SPEED_BOOST_DURATION
                line_alpha = int(180 * min(1.0, ratio * 2))
                # 後方（プレイヤーの周囲ランダム）に光の筋
                for _ in range(4):
                    ox = random.randint(-half, half)
                    oy = random.randint(-half, half)
                    length = random.randint(8, 18)
                    sx = self.player_x + ox
                    sy = self.player_y + oy
                    # 上方向に伸びる線（移動感）
                    pygame.draw.line(
                        self.screen, (160, 240, 250),
                        (int(sx), int(sy)),
                        (int(sx), int(sy + length)), 2)
                # 縁取りの淡い円
                aura_size = self.player_size + 18
                aura = pygame.Surface(
                    (aura_size, aura_size), pygame.SRCALPHA)
                a = int(60 + 30 * math.sin(self.elapsed_time / 100))
                pygame.draw.circle(
                    aura, (120, 230, 250, a),
                    (aura_size // 2, aura_size // 2),
                    aura_size // 2, 2)
                self.screen.blit(
                    aura,
                    (int(self.player_x - aura_size // 2),
                     int(self.player_y - aura_size // 2)))
            except Exception:
                pass

        # シールド中：プレイヤーの周囲に金色のバリア
        if self.shield_timer > 0:
            try:
                ratio = self.shield_timer / SHIELD_DURATION
                shield_size = self.player_size + 30
                surf = pygame.Surface(
                    (shield_size, shield_size), pygame.SRCALPHA)
                center = shield_size // 2
                # 残り時間が少ないほど明滅を速く
                pulse_speed = 120 if ratio > 0.3 else 60
                pulse = 0.5 + 0.5 * math.sin(
                    self.elapsed_time / pulse_speed)
                # 残り時間が少ない時は半透明で点滅
                visible = True
                if ratio < 0.25:
                    # 残り少なくなったら点滅で警告
                    visible = (self.elapsed_time // 100) % 2 == 0
                if visible:
                    # 内側：金色の半透明円
                    inner_alpha = int(70 + 50 * pulse)
                    pygame.draw.circle(
                        surf, (255, 215, 90, inner_alpha),
                        (center, center), shield_size // 2 - 4)
                    # 外側：明るい縁
                    edge_alpha = int(180 + 60 * pulse)
                    pygame.draw.circle(
                        surf, (255, 240, 180, min(255, edge_alpha)),
                        (center, center), shield_size // 2, 3)
                    # 六角形の格子模様（バリアっぽさ）を少しだけ
                    for i in range(6):
                        ang = math.radians(self.elapsed_time / 8 + i * 60)
                        px = center + math.cos(ang) * (shield_size // 2 - 8)
                        py = center + math.sin(ang) * (shield_size // 2 - 8)
                        pygame.draw.circle(
                            surf, (255, 255, 220, 220),
                            (int(px), int(py)), 2)
                    self.screen.blit(
                        surf,
                        (int(self.player_x - center),
                         int(self.player_y - center)))
            except Exception:
                pass

        # ストックがあれば変身モンスターのオーラ
        if self.stocks > 0:
            try:
                aura_color = BLOCK_COLORS.get(self.player_monster, WHITE)
                aura_size = self.player_size + 28
                aura = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
                alpha = int(70 + 40 * math.sin(self.elapsed_time / 120))
                pygame.draw.circle(aura, (*aura_color, alpha),
                                   (aura_size // 2, aura_size // 2),
                                   aura_size // 2)
                self.screen.blit(aura,
                                 (int(self.player_x - aura_size // 2),
                                  int(self.player_y - aura_size // 2)))
            except Exception:
                pass

        monster_img = (self.images.get("monsters", {}) or {}).get(
            self.player_monster)
        if monster_img is None:
            color = BLOCK_COLORS.get(self.player_monster, (180, 0, 220))
            pygame.draw.rect(
                self.screen, color,
                (self.player_x - self.player_size // 2,
                 self.player_y - self.player_size // 2,
                 self.player_size, self.player_size))
        else:
            scaled = pygame.transform.smoothscale(
                monster_img, (self.player_size, self.player_size))
            half = self.player_size // 2
            self.screen.blit(scaled,
                             (self.player_x - half, self.player_y - half))

    def _draw_top_bar(self):
        """画面上部の細い情報バー。時間とスコアを左右に並べる"""
        screen = self.screen
        small_font = self.fonts["small"]
        mini_font = self.fonts["mini"]

        # 背景
        bar_rect = pygame.Rect(0, 0, WIDTH, TOP_BAR_H)
        pygame.draw.rect(screen, (20, 20, 35), bar_rect)
        pygame.draw.line(screen, (60, 60, 90),
                         (0, TOP_BAR_H), (WIDTH, TOP_BAR_H), 2)

        # 左：時間
        secs = self.elapsed_time // 1000
        mins = secs // 60
        secs = secs % 60
        time_label = mini_font.render("TIME", True, GRAY)
        screen.blit(time_label, (15, 6))
        time_text = small_font.render(
            f"{mins:02d}:{secs:02d}", True, WHITE)
        screen.blit(time_text, (15, 22))

        # 右：スコア
        score_label = mini_font.render("SCORE", True, GRAY)
        score_text = small_font.render(f"{self.score}", True, GOLD)
        score_label_rect = score_label.get_rect(topright=(WIDTH - 15, 6))
        score_rect = score_text.get_rect(topright=(WIDTH - 15, 22))
        screen.blit(score_label, score_label_rect)
        screen.blit(score_text, score_rect)

        # 中央：タイトル風の表示
        title = mini_font.render("- COSMIC -", True, (120, 120, 160))
        title_rect = title.get_rect(center=(WIDTH // 2, TOP_BAR_H // 2))
        screen.blit(title, title_rect)

    def _draw_left_panel(self):
        """左サイドバー：HP・モンスター情報・ストック・色カウンタ"""
        screen = self.screen
        small_font = self.fonts["small"]
        mini_font = self.fonts["mini"]

        # 背景
        panel_rect = pygame.Rect(0, TOP_BAR_H, LEFT_PANEL_W, HEIGHT - TOP_BAR_H)
        pygame.draw.rect(screen, (18, 18, 28), panel_rect)
        pygame.draw.line(screen, (60, 60, 90),
                         (LEFT_PANEL_W, TOP_BAR_H),
                         (LEFT_PANEL_W, HEIGHT), 2)

        # レイアウト：上から HP セクション → モンスター情報 → ストック
        y = TOP_BAR_H + 20
        margin_x = 20

        # ----- HP セクション -----
        hp_title = small_font.render("HP", True, WHITE)
        screen.blit(hp_title, (margin_x, y))
        y += 32

        # HPゲージ：横一列のハート風バー
        hp_bar_w = LEFT_PANEL_W - margin_x * 2
        max_per_row = 10
        cell_w = hp_bar_w // max_per_row
        cell_h = 22
        for i in range(PLAYER_HP_CAP):
            row = i // max_per_row
            col = i % max_per_row
            x = margin_x + col * cell_w
            yy = y + row * (cell_h + 4)
            if i < self.player_hp:
                pygame.draw.rect(screen, (80, 220, 120),
                                 (x, yy, cell_w - 3, cell_h), border_radius=3)
                pygame.draw.rect(screen, WHITE,
                                 (x, yy, cell_w - 3, cell_h), 1, border_radius=3)
            else:
                pygame.draw.rect(screen, (35, 35, 50),
                                 (x, yy, cell_w - 3, cell_h), border_radius=3)
                pygame.draw.rect(screen, (70, 70, 90),
                                 (x, yy, cell_w - 3, cell_h), 1, border_radius=3)
        # HPの数値表記
        hp_text = mini_font.render(
            f"{self.player_hp} / {PLAYER_HP_CAP}", True, GRAY)
        hp_text_rect = hp_text.get_rect(
            topright=(LEFT_PANEL_W - margin_x, y - 26))
        screen.blit(hp_text, hp_text_rect)
        y += (cell_h + 4) * ((PLAYER_HP_CAP + max_per_row - 1) // max_per_row) + 25

        # ----- 区切り線 -----
        pygame.draw.line(screen, (50, 50, 70),
                         (margin_x, y), (LEFT_PANEL_W - margin_x, y), 1)
        y += 20

        # ----- 現在のモンスター -----
        mon_title = small_font.render("MONSTER", True, WHITE)
        screen.blit(mon_title, (margin_x, y))
        y += 32

        # モンスター画像（大きめに表示）
        mon_img = (self.images.get("monsters", {}) or {}).get(
            self.player_monster)
        mon_img_size = 110
        mon_img_x = LEFT_PANEL_W // 2 - mon_img_size // 2
        mon_img_y = y
        mon_color = BLOCK_COLORS.get(self.player_monster, WHITE)

        # モンスターの背景円
        try:
            bg_size = mon_img_size + 20
            bg_surf = pygame.Surface((bg_size, bg_size), pygame.SRCALPHA)
            pulse = int(80 + 30 * math.sin(self.elapsed_time / 250))
            pygame.draw.circle(bg_surf, (*mon_color, pulse),
                               (bg_size // 2, bg_size // 2), bg_size // 2)
            screen.blit(bg_surf, (mon_img_x - 10, mon_img_y - 10))
        except Exception:
            pass

        if mon_img is not None:
            try:
                scaled = pygame.transform.smoothscale(
                    mon_img, (mon_img_size, mon_img_size))
                screen.blit(scaled, (mon_img_x, mon_img_y))
            except Exception:
                pygame.draw.rect(screen, mon_color,
                                 (mon_img_x, mon_img_y,
                                  mon_img_size, mon_img_size))
        else:
            pygame.draw.rect(screen, mon_color,
                             (mon_img_x, mon_img_y,
                              mon_img_size, mon_img_size))

        # モンスター名
        name_text = small_font.render(
            self.player_monster.upper(), True, mon_color)
        name_rect = name_text.get_rect(
            center=(LEFT_PANEL_W // 2, mon_img_y + mon_img_size + 22))
        screen.blit(name_text, name_rect)

        y = mon_img_y + mon_img_size + 50

        # 能力の短い説明
        desc = self._ability_description(self.player_monster)
        desc_lines = desc.split("\n")
        for line in desc_lines:
            line_text = mini_font.render(line, True, (180, 180, 200))
            line_rect = line_text.get_rect(center=(LEFT_PANEL_W // 2, y))
            screen.blit(line_text, line_rect)
            y += 20

        y += 15

        # ----- 区切り線 -----
        pygame.draw.line(screen, (50, 50, 70),
                         (margin_x, y), (LEFT_PANEL_W - margin_x, y), 1)
        y += 20

        # ----- ストック -----
        stock_title = small_font.render("STOCK", True, WHITE)
        screen.blit(stock_title, (margin_x, y))
        # 「SPACE」のヒント
        space_hint = mini_font.render("SPACE to use", True, GRAY)
        space_rect = space_hint.get_rect(
            topright=(LEFT_PANEL_W - margin_x, y + 6))
        screen.blit(space_hint, space_rect)
        y += 36

        # ストックの大きい丸
        stock_circle_r = 22
        gap = 16
        total_w = MAX_STOCKS * (stock_circle_r * 2) + (MAX_STOCKS - 1) * gap
        start_x = LEFT_PANEL_W // 2 - total_w // 2
        for i in range(MAX_STOCKS):
            cx = start_x + i * (stock_circle_r * 2 + gap) + stock_circle_r
            cy = y + stock_circle_r
            if i < self.stocks:
                # アクティブストック：脈動
                pulse = int(180 + 70 * math.sin(
                    self.elapsed_time / 150 + i * 0.5))
                pygame.draw.circle(screen, mon_color, (cx, cy), stock_circle_r)
                pygame.draw.circle(screen, (255, 255, 255, pulse),
                                   (cx, cy), stock_circle_r, 3)
            else:
                pygame.draw.circle(screen, (35, 35, 50),
                                   (cx, cy), stock_circle_r)
                pygame.draw.circle(screen, (70, 70, 90),
                                   (cx, cy), stock_circle_r, 2)
        y += stock_circle_r * 2 + 18

        # ----- 色カウンタ（COLOR_CHARGES_PER_STOCK > 1 のときだけ表示） -----
        if COLOR_CHARGES_PER_STOCK > 1:
            charge_title = mini_font.render(
                f"NEXT STOCK: {self.color_count}/{COLOR_CHARGES_PER_STOCK}",
                True, GRAY)
            charge_rect = charge_title.get_rect(center=(LEFT_PANEL_W // 2, y))
            screen.blit(charge_title, charge_rect)
            y += 22

            # 進捗バー
            bar_w = LEFT_PANEL_W - margin_x * 2
            bar_h = 12
            bar_x = margin_x
            pygame.draw.rect(screen, (35, 35, 50),
                             (bar_x, y, bar_w, bar_h), border_radius=4)
            fill_w = int(bar_w * self.color_count / COLOR_CHARGES_PER_STOCK)
            if fill_w > 0:
                pygame.draw.rect(screen, mon_color,
                                 (bar_x, y, fill_w, bar_h), border_radius=4)
            pygame.draw.rect(screen, (70, 70, 90),
                             (bar_x, y, bar_w, bar_h), 1, border_radius=4)
        else:
            # 1個で即ストックなので、軽い案内だけ
            hint = mini_font.render(
                "Touch color block to stock", True, (130, 130, 160))
            hint_rect = hint.get_rect(center=(LEFT_PANEL_W // 2, y))
            screen.blit(hint, hint_rect)

    def _ability_description(self, monster):
        """各モンスターの能力を短く説明"""
        return {
            "red":    "Bomb + Firecracker\nBig explosion + close pops",
            "blue":   "Water stream pushes\nblocks upward",
            "yellow": "Drop 3 lightning bolts\nat random spots",
            "green":  "Forward wind vortex\nKnocks blocks aside",
            "dark":   "Slow nearby blocks\nRocks break in 2s",
        }.get(monster, "No ability yet")

    # ============================================
    # ゲームオーバー画面
    # ============================================
    def draw_gameover(self):
        screen = self.screen
        big_font = self.fonts["big"]
        font = self.fonts["font"]
        small_font = self.fonts["small"]

        screen.fill(BLACK)
        # 右パネル：背景アニメ
        right_panel_rect = pygame.Rect(PLAY_RIGHT, 0, RIGHT_PANEL_W, HEIGHT)
        pygame.draw.rect(screen, (8, 8, 20), right_panel_rect)
        screen.set_clip(right_panel_rect)
        for planet in self.warp_planets:
            planet.draw(screen)
        for star in self.warp_stars:
            star.draw(screen)
        screen.set_clip(None)

        # 左パネルとプレイエリアと上バーは暗い色で塗りつぶす
        pygame.draw.rect(screen, (15, 15, 25),
                         (0, 0, PLAY_RIGHT, HEIGHT))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # プレイエリアを基準に配置
        cx = PLAY_CX
        cy = PLAY_CY

        title = big_font.render("GAME OVER", True, (250, 80, 80))
        title_rect = title.get_rect(center=(cx, cy - 130))
        screen.blit(title, title_rect)

        panel_w = min(PLAY_W - 20, 380)
        panel_h = 180
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        panel_rect = panel.get_rect(center=(cx, cy))
        screen.blit(panel, panel_rect)
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        score_text = font.render(f"SCORE: {self.score}", True, GOLD)
        screen.blit(score_text, score_text.get_rect(center=(cx, cy - 40)))

        secs = self.elapsed_time // 1000
        mins = secs // 60
        secs = secs % 60
        time_text = font.render(f"TIME: {mins:02d}:{secs:02d}", True, WHITE)
        screen.blit(time_text, time_text.get_rect(center=(cx, cy + 10)))

        try:
            top_scores = self.score_manager.get_top(self.mode)
        except Exception:
            top_scores = []
        my_rank = None
        for i, entry in enumerate(top_scores):
            if entry["score"] == self.score:
                my_rank = i + 1
                break
        if my_rank is not None and my_rank <= 3:
            rank_text = font.render(
                f"NEW RANK: #{my_rank}", True, GOLD)
            screen.blit(rank_text,
                        rank_text.get_rect(center=(cx, cy + 55)))

        hint = small_font.render(
            "Press ENTER or click to return", True, GRAY)
        hint_rect = hint.get_rect(center=(cx, PLAY_BOTTOM - 30))
        screen.blit(hint, hint_rect)

    def draw_ending(self, dt):
        self.draw_gameover()

    # ============================================
    # 入力
    # ============================================
    def handle_click(self, mouse_pos):
        if self.state == "gameover":
            self.finished = True

    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        if self.state == "play":
            if key == pygame.K_SPACE:
                self._trigger_ability()
        elif self.state == "gameover":
            if key == pygame.K_RETURN:
                self.finished = True