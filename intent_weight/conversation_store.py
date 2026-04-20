# -*- coding: utf-8 -*-
"""
对话存储模块
Conversation Store Module

SQLite 持久化对话历史，支持 insight 提取和对话分析。
SQLite-based persistent conversation history for insight extraction and analytics.
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class ConversationStore:
    """
    SQLite 对话存储
    SQLite Conversation Store
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表 / Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    feedback TEXT,
                    sources TEXT,
                    agent_action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON conversations(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON conversations(message_id)")
        logger.info(f"ConversationStore initialized at {self.db_path}")

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        feedback: Optional[str] = None,
        sources: Optional[List[str]] = None,
        agent_action: Optional[str] = None,
    ):
        """保存单条消息 / Save a single message"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO conversations
                   (session_id, message_id, role, content, feedback, sources, agent_action)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    message_id,
                    role,
                    content,
                    feedback,
                    json.dumps(sources, ensure_ascii=False) if sources else None,
                    agent_action,
                ),
            )

    def update_feedback(self, message_id: str, feedback: str):
        """更新反馈 / Update feedback for a message"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE conversations SET feedback = ? WHERE message_id = ?",
                (feedback, message_id),
            )

    def get_session(self, session_id: str) -> List[Dict]:
        """获取完整会话 / Get full session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM conversations WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_sessions(self, days: int = 1) -> Dict[str, List[Dict]]:
        """
        获取最近 N 天的会话（按 session_id 分组）
        Get recent sessions grouped by session_id
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM conversations WHERE created_at >= ? ORDER BY created_at",
                (since,),
            ).fetchall()

        sessions: Dict[str, List[Dict]] = {}
        for r in rows:
            d = dict(r)
            sid = d["session_id"]
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(d)
        return sessions

    def get_sessions_with_corrections(self, days: int = 1) -> Dict[str, List[Dict]]:
        """
        获取包含纠正/负面反馈的会话（用于 insight 提取）
        Get sessions with corrections or negative feedback
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # 找到有 refine_search 或 dislike 的 session_id
            sids = conn.execute(
                """SELECT DISTINCT session_id FROM conversations
                   WHERE created_at >= ?
                   AND (agent_action = 'refine_search' OR feedback = 'dislike')""",
                (since,),
            ).fetchall()
            sid_list = [r["session_id"] for r in sids]

        if not sid_list:
            return {}

        # 获取这些 session 的完整对话
        sessions = {}
        for sid in sid_list:
            sessions[sid] = self.get_session(sid)
        return sessions

    def get_stats(self) -> Dict:
        """获取统计信息 / Get statistics"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM conversations").fetchone()[0]
            with_feedback = conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE feedback IS NOT NULL"
            ).fetchone()[0]
            corrections = conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE agent_action = 'refine_search'"
            ).fetchone()[0]
        return {
            "total_messages": total,
            "total_sessions": sessions,
            "messages_with_feedback": with_feedback,
            "correction_count": corrections,
        }
