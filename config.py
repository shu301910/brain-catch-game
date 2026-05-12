# ============================================================
# config.py
# 定数・色・各種設定値をまとめたファイル
# ============================================================

import pygame

# =========================
# 画面サイズの設定
# =========================
PLAY_WIDTH = 800
PLAY_HEIGHT = 600
TOP_BAR_HEIGHT = 50
SIDE_WIDTH = 400          # 2体モードのため300→400に拡張

WIDTH = PLAY_WIDTH + SIDE_WIDTH        # 1200
HEIGHT = PLAY_HEIGHT + TOP_BAR_HEIGHT  # 650

PLAY_LEFT = SIDE_WIDTH                 # プレイエリアの左端 = 400
BEAM_BAR_HEIGHT = 20
PLAY_TOP = TOP_BAR_HEIGHT + BEAM_BAR_HEIGHT  # プレイエリアの上端 = 70
PLAY_BOTTOM = PLAY_TOP + PLAY_HEIGHT   # プレイエリアの下端 = 650

FPS = 60

# =========================
# 色設定（RGB）
# =========================
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (200, 200, 200)
DARK_GRAY  = (60, 60, 60)
RED        = (250, 0, 0)
BLUE       = (0, 60, 255)
PURPLE     = (128, 0, 128)
GREEN      = (50, 200, 50)
YELLOW     = (255, 220, 30)
GOLD       = (255, 215, 0)
GOLD_BLOCK_COLOR = (255, 200, 0)   # ← ここに追加
BEAM_BAR_BG      = (20, 20, 35)   # ← ここに追加
SIDEBAR_BG = (25, 25, 40)
TOPBAR_BG  = (30, 30, 50)


# バー速度ダウン中の色（黒モンスター特殊攻撃）
PLAYER_SLOW_WHITE = (130, 130, 130)   # 白 → グレー
PLAYER_SLOW_RED   = (180, 0, 100)     # 赤 → 赤紫
PLAYER_SLOW_BLUE  = (0, 80, 200)      # 青 → 青紫

# =========================
# プレイヤー設定
# =========================
PLAYER_WIDTH  = 110
PLAYER_HEIGHT = 20
PLAYER_SPEED  = 7
MAX_BOOST     = 2
PLAYER_MAX_HP = 100

# =========================
# ボール設定
# =========================
BALL_SIZE           = 15
INITIAL_BALL_SPEED  = 4
SPEED_UP            = 0.15
MAX_BOUNCE_ANGLE    = 60
ENEMY_KILL_SLOWDOWN = 2

# ソロ1モード用：初期ボール速度を少し高く
SOLO1_INITIAL_BALL_SPEED = 5

# =========================
# ブロック設定
# =========================
BLOCK_WIDTH         = 40
BLOCK_HEIGHT        = 20
MAX_RED_BLUE_BLOCKS = 3
MAX_PURPLE_BLOCKS   = 2          # 紫ブロック上限を2に増加（出現率UP）
HEAL_AMOUNT         = 30

# 無敵ブロック設定
MAX_INVINCIBLE_BLOCKS  = 1
INVINCIBLE_BLOCK_HITS  = 3
INVINCIBLE_DURATION    = 10000
INVINCIBLE_BLOCK_COLOR = (220, 220, 255)
INVINCIBLE_BLOCK_LIFETIME = 35000  # 35秒で自然消滅

# ↓これを追加
ATTACK_BOOST_MULT     = 1.5    # 無敵中の攻撃力倍率
ATTACK_BOOST_DURATION = 10000  # 持続時間（無敵と同じ10秒）

# 金ブロック設定
MAX_GOLD_BLOCKS = 1
GOLD_BLOCK_LIFETIME  = 15000   # 15秒で自然消滅
GOLD_BLOCK_HITS      = 5       # 5回当たると破壊
GOLD_BLOCK_SPAWN_MIN = 15000   # 出現間隔最小
GOLD_BLOCK_SPAWN_MAX = 30000   # 出現間隔最大

# プレイヤービーム設定
PLAYER_BEAM_TOTAL    = 10000   # 合計使用可能時間（ms）
PLAYER_BEAM_WIDTH    = 24      # ビームの幅（px）
PLAYER_BEAM_HIT_TIME = 2000    # 赤・青・紫ブロックを壊す当たり時間（ms）



# =========================
# 敵設定
# =========================
ENEMY_MAX_HP          = 100
ENEMY_DAMAGE          = 20
ENEMY_ATTACK_INTERVAL = 15000
DAMAGE_NORMAL         = 30
DAMAGE_RESIST         = 20
ENEMY_SCORE           = 50

SPECIAL_INTERVAL_MIN = 15000
SPECIAL_INTERVAL_MAX = 20000

YELLOW_DYE_DURATION   = 10000
GREEN_INVERT_DURATION = 7000

# 黄色モンスター光ビーム攻撃
YELLOW_FLASH_DURATION    = 400   # 予告フラッシュの長さ（ms）
YELLOW_BEAM_PENDING      = 1000  # 予告から発動までの時間（ms）
LIGHT_BEAM_DURATION      = 600   # ビームが表示される時間（ms）
LIGHT_BEAM_WIDTH         = 18    # ビームの幅（px）
LIGHT_BEAM_DAMAGE        = 30    # バーに当たった時のダメージ

# 落下物（葉っぱ・光の矢）の設定
PROJECTILE_SPEED   = 4.5      # 落下速度（px/frame）
PROJECTILE_DAMAGE  = 20     # バーに当たった時のダメージ
PROJECTILE_WIDTH   = 20
PROJECTILE_HEIGHT  = 20
MAX_PROJECTILES    = 5      # 画面上の最大同時落下数

# 赤モンスター特殊攻撃（ボール速度UP）
RED_SPEED_BOOST_MULT     = 1.8   # 速度倍率
RED_SPEED_BOOST_DURATION = 4000  # 持続ミリ秒

# 黒モンスター特殊攻撃（バー速度DOWN）
DARK_SLOW_MULT     = 0.5   # 速度倍率（通常の55%）：少し緩和
DARK_SLOW_DURATION = 6000   # 持続ミリ秒（1秒延長）

# 緑モンスター逆転演出：画面フラッシュの持続時間
INVERT_FLASH_DURATION = 400  # ミリ秒

# 青モンスター特殊攻撃（下降時のみ速くなる）
BLUE_GRAVITY_MULT      = 1.5    # 下降時の速度倍率
BLUE_GRAVITY_DURATION  = 6000   # 持続ミリ秒
WATERFALL_PARTICLE_COUNT = 30   # 滝エフェクトのパーティクル数

# 敵の表示位置・サイズ（1体モード：サイドバー400px中央寄り）
ENEMY_X      = 125   # (400 - 150) / 2 = 125
ENEMY_Y      = 140
ENEMY_WIDTH  = 150
ENEMY_HEIGHT = 150

# =========================
# タイミング
# =========================
FIRST_SPAWN_DELAY = 5000
BLOCK_SPAWN_MIN   = 3000
BLOCK_SPAWN_MAX   = 7000

# =========================
# ハイスコア設定
# =========================
HIGH_SCORE_FILE   = "scores.json"
MAX_HIGH_SCORES   = 10   # トップ10まで保存
GAMEOVER_SHOW_TOP = 3    # ゲームオーバー時はトップ3を表示

# =========================
# ゲームモード
# =========================
MODE_SOLO1 = "solo1"  # 一人用：バー１個・ボール１個（白）
MODE_SOLO2 = "solo2"  # 一人用：バー２個・ボール２個
MODE_DUO   = "duo"    # 二人用：バー２個・ボール２個
MODE_COSMIC = "cosmic"  # コズミックモード：宇宙空間でブロックを壊すスコアアタック

# モード別のスコアファイル（solo1とsolo2を別ファイルに修正）
MODE_SCORE_FILES = {
    MODE_SOLO1: "score_solo1.json",
    MODE_SOLO2: "score_solo2.json",
    MODE_DUO:   "score_duo.json",
    MODE_COSMIC: "score_cosmic.json",
}

# モード別の表示ラベル
MODE_LABELS = {
    MODE_SOLO1: "1P( 1 BAR)",
    MODE_SOLO2: "1P( 2 BAR 2 Ball)",
    MODE_DUO:   "2P",
    MODE_COSMIC: "COSMIC",
}

# モード別パラメーター
MODE_PARAMS = {
    MODE_SOLO1: {"speed_up_mult": 1.0, "damage_mult": 1.0},
    MODE_SOLO2: {"speed_up_mult": 0.6, "damage_mult": 0.7},
    MODE_DUO:   {"speed_up_mult": 1.5, "damage_mult": 1.0},
    MODE_COSMIC: {"speed_up_mult": 1.0, "damage_mult": 1.0},
}

# 紫ブロックを白ボール（ソロ1モード）で何回当てたら割れるか
PURPLE_HITS_SOLO1 = 2

# =========================
# コンボ設定
# =========================
# コンボ：バーで跳ね返ったボールが連続でブロックを破壊するごとにカウントアップ。
# バーに当たるとリセット。
COMBO_DAMAGE_STEP   = 0.2   # コンボ1段ごとの追加ダメージ倍率（2連鎖で+0.2＝×1.2）
COMBO_DAMAGE_MAX    = 2.5   # ダメージ倍率の上限
COMBO_SCORE_PER     = 5     # スコアボーナス：combo数 × COMBO_SCORE_PER
COMBO_MIN_DISPLAY   = 3     # この連鎖数以上で「COMBO」表示エフェクトを出す
COMBO_PARTICLE_THRESHOLD = 4   # この連鎖数以上で派手なパーティクルを出す
COMBO_TEXT_DURATION = 800   # 「COMBO x N」テキストが表示される時間（ms）

# =========================
# 2体モード設定
# =========================
DUAL_ENEMY_TRIGGER = 5   # 何体倒したら2体モードになるか
BOSS_TRIGGER       = 9   # 何体倒したらラスボスになるか（9体倒した後=10体目）

# 2体モード時の敵の表示位置（左・右）
# サイドバー400px内に2体を並べる
ENEMY_DUAL_W  = 150   # 2体モード時の幅
ENEMY_DUAL_H  = 150   # 2体モード時の高さ
ENEMY_DUAL_Y  = 120   # 両方共通のY座標
ENEMY_LEFT_X  = 15    # 左の敵X座標
ENEMY_RIGHT_X = 220   # 右の敵X座標（15 + 150 + 55 = 220）

# =========================
# ラスボス設定
# =========================
BOSS_X           = 5              # サイドバー左端から少し内側
BOSS_Y           = 55             # 上部バー直下
BOSS_W           = 390            # サイドバーいっぱい（400 - 余白10）
BOSS_H           = 390            # 正方形で大きく
BOSS_HP_MULT     = 3              # 通常の3倍HP
BOSS_HP_BARS     = 3              # HPバーを3本に分割
BOSS_DAMAGE_MULT = 1.5            # 通常攻撃ダメージ倍率
BOSS_SPECIAL_INTERVAL_MIN = 8000  # 特殊攻撃間隔（短め）
BOSS_SPECIAL_INTERVAL_MAX = 12000
BOSS_ATTACK_INTERVAL      = 10000 # 通常攻撃間隔（短め）
BOSS_COLOR       = (180, 0, 220)  # 紫色（合体ボスのイメージ）

# =========================
# モンスター定義
# =========================
# 赤・青の特殊攻撃をそれぞれ speed_boost / gravity に変更
MONSTER_DEFS = [
    {"name": "red",    "file": "monster_02_red.png",
     "resist": "red",    "special": "speed_boost", "label": "Red",
     "max_hp": ENEMY_MAX_HP},
    {"name": "blue",   "file": "monster_03_blue.png",
     "resist": "blue",   "special": "gravity",     "label": "Blue",
     "max_hp": ENEMY_MAX_HP},
    {"name": "yellow", "file": "monster_01_yellow.png",
     "resist": None,     "special": "dye",         "label": "Yellow",
     "max_hp": ENEMY_MAX_HP},
    {"name": "green",  "file": "monster_04_green.png",
     "resist": None,     "special": "invert",      "label": "Green",
     "max_hp": ENEMY_MAX_HP},
    {"name": "dark",   "file": "monster_05_dark.png",
     "resist": None,     "special": "shuffle",     "label": "Dark",
     "max_hp": ENEMY_MAX_HP},
]