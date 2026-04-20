# -*- coding: utf-8 -*-
"""
用户信誉评分模块
User Credibility Scoring Module

根据用户反馈历史评估其可信度，高信誉用户的反馈对 LinUCB 影响更大，
低信誉用户的反馈权重被抑制，防止系统被投毒。
Score user credibility based on feedback history. High-credibility users
have more impact on LinUCB updates; low-credibility users are suppressed.
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from loguru import logger


class UserCredibilityStore:
    """
    用户信誉存储（SQLite）
    User Credibility Store (SQLite)

    当前基于 session_id 评分（等 SSO 接入后切换到 user_id）。
    Currently scores by session_id (switch to user_id after SSO integration).
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    user_id TEXT PRIMARY KEY,
                    score REAL DEFAULT 0.5,
                    feedback_count INTEGER DEFAULT 0,
                    positive_count INTEGER DEFAULT 0,
                    negative_count INTEGER DEFAULT 0,
                    consistency_rate REAL DEFAULT 0.5,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def get_credibility(self, user_id: str) -> float:
        """
        获取用户信誉分（0.1 ~ 1.0）
        Get user credibility score

        新用户返回 0.5（中性）。
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT score FROM user_scores WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        return row[0] if row else 0.5

    def update_credibility(
        self,
        user_id: str,
        feedback_aligned: bool,
        engagement_depth: float = 0.5,
    ):
        """
        更新用户信誉分
        Update user credibility score

        Args:
            user_id: 用户 ID（当前为 session_id）
            feedback_aligned: 该次反馈是否与系统预期一致
                - True: 点赞好答案 / 点踩差答案 → 信誉上升
                - False: 点赞差答案 / 点踩好答案 → 信誉下降
            engagement_depth: 参与深度 (0~1)，多轮深入对话=高，随意点击=低
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT score, feedback_count, positive_count, negative_count FROM user_scores WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if row:
                score, count, pos, neg = row
            else:
                score, count, pos, neg = 0.5, 0, 0, 0

            count += 1
            if feedback_aligned:
                pos += 1
            else:
                neg += 1

            # 衰减学习率：早期快速调整，后期稳定
            alpha = 1.0 / (count + 10)

            # 目标值：一致性 + 参与深度加权
            target = (1.0 if feedback_aligned else 0.0) * 0.7 + engagement_depth * 0.3
            score += alpha * (target - score)

            # 限制在 [0.1, 1.0]
            score = max(0.1, min(1.0, score))

            consistency = pos / max(1, count)

            conn.execute("""
                INSERT INTO user_scores (user_id, score, feedback_count, positive_count, negative_count, consistency_rate, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    score = ?, feedback_count = ?, positive_count = ?,
                    negative_count = ?, consistency_rate = ?, last_updated = ?
            """, (
                user_id, score, count, pos, neg, consistency, datetime.now().isoformat(),
                score, count, pos, neg, consistency, datetime.now().isoformat(),
            ))

            logger.debug(f"User {user_id[:8]}... credibility: {score:.3f} "
                        f"(count={count}, consistency={consistency:.2f})")

    def get_all_scores(self) -> list:
        """获取所有用户评分 / Get all user scores"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM user_scores ORDER BY score DESC"
            ).fetchall()
        return [dict(r) for r in rows]
