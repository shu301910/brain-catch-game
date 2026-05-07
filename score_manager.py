# ============================================================
# score_manager.py
# ハイスコアの保存・読み込みを担当
# モードごとに別ファイル（scores_solo1.json など）に記録される
# ============================================================

import json
import os
from datetime import datetime
from config import HIGH_SCORE_FILE, MAX_HIGH_SCORES, MODE_SCORE_FILES


class ScoreManager:
    """ハイスコアの管理クラス。
    モードごとに別ファイルへ記録を保存し、トップ10まで保持する"""

    def __init__(self):
        # 起動時に全モードのスコアをまとめて読み込む
        # キー：モード名、値：そのモードのスコアリスト
        self.scores_by_mode = {
            mode: self._load(path)
            for mode, path in MODE_SCORE_FILES.items()
        }

    def _load(self, path):
        """指定ファイルからハイスコアを読み込む。
        ファイルが無い・壊れている場合は空リストを返す"""
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 万一データが想定と違う場合に備えてリストかチェック
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, IOError):
            # ファイルが壊れていたら空リストでスタート
            return []

    def _save(self, mode):
        """指定モードのハイスコアをファイルに保存する"""
        path = MODE_SCORE_FILES[mode]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.scores_by_mode[mode], f,
                          ensure_ascii=False, indent=2)
        except IOError:
            # 保存失敗してもゲームは続行する
            pass

    def add_score(self, mode, score, time_ms, defeated_count):
        """新しいスコアを指定モードに追加。
        トップ10に入った場合のみ保存する。
        戻り値：追加されたスコアの順位（1〜10）。圏外なら None"""
        new_entry = {
            "score": score,
            "time_ms": time_ms,
            "defeated": defeated_count,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        scores = self.scores_by_mode[mode]
        # 全スコアにこのエントリを追加して、降順にソート
        scores.append(new_entry)
        scores.sort(key=lambda x: x["score"], reverse=True)

        # トップ10だけ残す
        self.scores_by_mode[mode] = scores[:MAX_HIGH_SCORES]

        self._save(mode)

        # 追加されたエントリの順位を探して返す
        for i, entry in enumerate(self.scores_by_mode[mode]):
            # 同一オブジェクトかチェック（同じスコアでも別エントリは区別したい）
            if entry is new_entry:
                return i + 1  # 1始まりの順位
        return None  # 圏外

    def get_top(self, mode, n=None):
        """指定モードの上位N件を返す（指定なしなら全件）"""
        scores = self.scores_by_mode.get(mode, [])
        if n is None:
            return scores
        return scores[:n]

    def is_empty(self, mode):
        """指定モードのハイスコアが1件も無いか"""
        return len(self.scores_by_mode.get(mode, [])) == 0