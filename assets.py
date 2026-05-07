# ============================================================
# assets.py
# 画像読み込み・フォーマット関数などのヘルパー
# ============================================================

import os
import pygame
from config import (
    MONSTER_DEFS, ENEMY_WIDTH, ENEMY_HEIGHT,
    SIDE_WIDTH, WIDTH, HEIGHT
)


def load_monster_images():
    """全モンスター画像を読み込む。
    画像が無くてもエラーにならず、Noneを設定する。"""
    images = {}
    base_dirs = ["images", "."]

    for monster in MONSTER_DEFS:
        loaded = False
        for base in base_dirs:
            path = os.path.join(base, monster["file"])
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(
                    img, (ENEMY_WIDTH, ENEMY_HEIGHT))
                images[monster["name"]] = img
                loaded = True
                break
        if not loaded:
            images[monster["name"]] = None
    return images


def load_image_or_none(filename, target_size):
    """汎用：画像を読み込んで指定サイズにリサイズ。
    画像が無ければNoneを返す。"""
    base_dirs = ["images", "."]
    for base in base_dirs:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            img = pygame.transform.smoothscale(img, target_size)
            return img
    return None


def load_planet_images():
    """惑星画像を読み込む（planet_00.png〜planet_09.png）。
    読み込めなかったものはNoneを設定する。"""
    images = []
    base_dirs = ["images", "."]
    for i in range(10):
        filename = f"planet_{i:02d}.png"
        loaded = False
        for base in base_dirs:
            path = os.path.join(base, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    images.append(img)
                    loaded = True
                    break
                except Exception:
                    pass
        if not loaded:
            images.append(None)
    return images


def load_surface_images():
    """惑星地表背景画像を読み込む（planet_surface_00.png〜）。
    読み込めたものだけリストに追加する。"""
    images = []
    base_dirs = ["images", "."]
    for i in range(20):  # 最大20枚まで探す
        filename = f"planet_surface_{i:02d}.png"
        for base in base_dirs:
            path = os.path.join(base, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
                    images.append(img)
                    break
                except Exception:
                    pass
    return images


def load_all_images():
    """ゲームで使う全画像をまとめて読み込んで返す"""
    return {
        "monsters":  load_monster_images(),
        "planets":   load_planet_images(),
        "surfaces":  load_surface_images(),
        "sidebar_bg": load_image_or_none(
            "planet_scene_vertical.png", (SIDE_WIDTH, HEIGHT)),
        "menu_bg": load_image_or_none(
            "monster_planet_scene.png", (WIDTH, HEIGHT)),
        "gameover_bg": load_image_or_none(
            "game_over.png", (WIDTH, HEIGHT)),
        "boss": load_image_or_none(
            "final_boss.png", (SIDE_WIDTH - 10, HEIGHT - 100)),
    }


def format_time(ms):
    """ミリ秒を MM:SS 形式の文字列に変換する。
    例：155000 → '02:35'"""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"