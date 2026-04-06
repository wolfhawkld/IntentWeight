#!/usr/bin/env python3
"""
RL 更新模块

实现基于用户反馈奖励的强化学习更新逻辑。

设计决策：
1. 批量更新：N=5 次对话后触发更新
2. 学习率：奖励相关，高奖励时 α 大
3. 新意图发现：用户澄清后匹配到不同 chunk
4. 矛盾反馈：最新显式反馈优先，阈值 0.7
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from intent_association import IntentAssociationManager


class DialogueSession:
    """对话会话"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[Dict] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.is_complete = False
    
    def add_turn(self, turn: Dict):
        """添加对话轮次"""
        self.turns.append(turn)
    
    def close(self):
        """关闭会话"""
        self.end_time = datetime.now()
        self.is_complete = True
    
    def get_final_chunk(self) -> Optional[str]:
        """获取最终匹配的 chunk"""
        if not self.turns:
            return None
        return self.turns[-1].get("matched_chunk")
    
    def get_final_intent(self) -> Optional[str]:
        """获取最终意图"""
        if not self.turns:
            return None
        return self.turns[-1].get("matched_intent")
    
    def get_total_reward(self) -> float:
        """计算会话总奖励"""
        if not self.turns:
            return 0.0
        # 使用最后一轮的奖励
        return self.turns[-1].get("reward", 0.0)
    
    def has_explicit_feedback(self) -> bool:
        """是否有显式反馈"""
        for turn in self.turns:
            if turn.get("user_actions", {}).get("explicit"):
                return True
        return False
    
    def get_latest_explicit_feedback(self) -> Optional[str]:
        """获取最新的显式反馈"""
        for turn in reversed(self.turns):
            exp = turn.get("user_actions", {}).get("explicit")
            if exp:
                return exp
        return None
    
    def has_clarification_redirect(self) -> bool:
        """是否有澄清后转向（用户澄清后匹配到不同内容）"""
        if len(self.turns) < 2:
            return False
        
        # 检查是否有澄清后的 chunk 变化
        for i in range(1, len(self.turns)):
            prev_chunk = self.turns[i-1].get("matched_chunk")
            curr_chunk = self.turns[i].get("matched_chunk")
            if prev_chunk and curr_chunk and prev_chunk != curr_chunk:
                return True
        return False
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "session_id": self.session_id,
            "turns": self.turns,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_complete": self.is_complete
        }


class RLUpdater:
    """RL 更新器"""
    
    def __init__(
        self,
        association_manager: IntentAssociationManager,
        batch_size: int = 5,
        storage_path: str = "data/pending_sessions.json"
    ):
        self.association_manager = association_manager
        self.batch_size = batch_size
        self.storage_path = Path(storage_path)
        
        # 待处理的会话
        self.pending_sessions: List[Dict] = []
        self.load_pending_sessions()
        
        # 更新历史
        self.update_history: List[Dict] = []
    
    def load_pending_sessions(self):
        """加载待处理的会话"""
        if self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.pending_sessions = json.load(f)
    
    def save_pending_sessions(self):
        """保存待处理的会话"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.pending_sessions, f, ensure_ascii=False, indent=2)
    
    def calculate_alpha(self, reward: float) -> float:
        """
        计算学习率（奖励相关）
        
        高奖励时 α 大，低奖励时 α 小
        
        α = α_base * sigmoid(k * (R - 0.5))
        
        Args:
            reward: 奖励值 [0, 1]
        
        Returns:
            学习率 α
        """
        import math
        
        alpha_base = 0.2  # 基础学习率
        k = 4.0  # 曲线陡峭度
        
        # sigmoid 函数：R 高时 α 大
        sigmoid = 1 / (1 + math.exp(-k * (reward - 0.5)))
        alpha = alpha_base * (0.5 + sigmoid)  # 范围约 [0.1, 0.35]
        
        return alpha
    
    def should_override_with_explicit(
        self, 
        session: DialogueSession,
        threshold: float = 0.7
    ) -> Tuple[bool, Optional[str]]:
        """
        判断是否应该用显式反馈覆盖
        
        Args:
            session: 对话会话
            threshold: 阈值
        
        Returns:
            (是否覆盖, 显式反馈类型)
        """
        explicit = session.get_latest_explicit_feedback()
        if not explicit:
            return False, None
        
        # 计算当前奖励
        reward = session.get_total_reward()
        
        # 如果显式反馈与奖励计算结果矛盾
        if explicit == "like" and reward < threshold:
            return True, "like"
        elif explicit == "dislike" and reward > (1 - threshold):
            return True, "dislike"
        
        return False, None
    
    def process_session(self, session: DialogueSession) -> Dict:
        """
        处理单个会话，计算需要更新的内容
        
        Returns:
            更新指令
        """
        result = {
            "session_id": session.session_id,
            "updates": [],
            "new_intents": [],
            "overrides": []
        }
        
        if not session.is_complete:
            return result
        
        # 获取最终匹配的 chunk 和意图
        final_chunk = session.get_final_chunk()
        final_intent = session.get_final_intent()
        reward = session.get_total_reward()
        
        if not final_chunk or not final_intent:
            return result
        
        # 检查是否需要显式反馈覆盖
        should_override, explicit_type = self.should_override_with_explicit(session)
        
        if should_override and explicit_type:
            # 用显式反馈调整奖励
            if explicit_type == "like":
                reward = max(reward, 0.85)
            elif explicit_type == "dislike":
                reward = min(reward, 0.15)
            
            result["overrides"].append({
                "type": explicit_type,
                "adjusted_reward": reward
            })
        
        # 检查是否有澄清后转向（新意图发现）
        if session.has_clarification_redirect():
            # 用户澄清后匹配到不同 chunk，说明发现了新意图
            result["new_intents"].append({
                "chunk_id": final_chunk,
                "intent_label": final_intent,
                "source": "clarification_redirect",
                "initial_confidence": 0.5 + reward * 0.3  # 基于奖励设置初始置信度
            })
        
        # 计算学习率
        alpha = self.calculate_alpha(reward)
        
        # 生成更新指令
        result["updates"].append({
            "chunk_id": final_chunk,
            "intent_id": final_intent,
            "reward": reward,
            "alpha": alpha,
            "action": "update_confidence"
        })
        
        return result
    
    def add_session(self, session: DialogueSession) -> bool:
        """
        添加会话到待处理队列
        
        Args:
            session: 对话会话
        
        Returns:
            是否触发了批量更新
        """
        self.pending_sessions.append(session.to_dict())
        self.save_pending_sessions()
        
        if len(self.pending_sessions) >= self.batch_size:
            self.batch_update()
            return True
        
        return False
    
    def batch_update(self) -> Dict:
        """
        批量更新
        
        Returns:
            更新结果
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "processed_sessions": len(self.pending_sessions),
            "updates_applied": 0,
            "new_intents_added": 0,
            "details": []
        }
        
        for session_data in self.pending_sessions:
            # 重建会话对象
            session = DialogueSession(session_data["session_id"])
            session.turns = session_data["turns"]
            session.is_complete = session_data["is_complete"]
            
            # 处理会话
            update_result = self.process_session(session)
            results["details"].append(update_result)
            
            # 应用更新
            for update in update_result["updates"]:
                self.association_manager.update_confidence(
                    chunk_id=update["chunk_id"],
                    intent_id=update["intent_id"],
                    reward=update["reward"],
                    alpha=update["alpha"]
                )
                results["updates_applied"] += 1
            
            # 添加新意图
            for new_intent in update_result["new_intents"]:
                self.association_manager.add_new_intent(
                    chunk_id=new_intent["chunk_id"],
                    intent_label=new_intent["intent_label"],
                    initial_confidence=new_intent["initial_confidence"],
                    source=new_intent["source"]
                )
                results["new_intents_added"] += 1
        
        # 清空待处理队列
        self.pending_sessions = []
        self.save_pending_sessions()
        
        # 记录更新历史
        self.update_history.append(results)
        
        return results
    
    def get_pending_count(self) -> int:
        """获取待处理会话数量"""
        return len(self.pending_sessions)
    
    def get_update_history(self, limit: int = 10) -> List[Dict]:
        """获取更新历史"""
        return self.update_history[-limit:]


def create_sample_session(session_id: str, scenario: str) -> DialogueSession:
    """创建示例会话"""
    session = DialogueSession(session_id)
    
    if scenario == "positive_with_clarification":
        # 用户澄清后匹配的场景
        session.add_turn({
            "turn_id": 1,
            "query": "试验用药申请流程是？",
            "matched_chunk": "chunk_001",
            "matched_intent": "intent_医疗试验用药申请",
            "user_actions": {
                "explicit": None,
                "implicit": {"dwell_time": 5, "copy_action": False, "bounce": False}
            }
        })
        session.add_turn({
            "turn_id": 2,
            "query": "原料申请审批",
            "matched_chunk": "chunk_002",  # 匹配到不同 chunk
            "matched_intent": "intent_原料制备流程",
            "user_actions": {
                "explicit": "like",
                "implicit": {"dwell_time": 30, "copy_action": True, "bounce": False}
            },
            "reward": 0.85
        })
    elif scenario == "negative_explicit":
        session.add_turn({
            "turn_id": 1,
            "query": "CRO流程是什么？",
            "matched_chunk": "chunk_003",
            "matched_intent": "intent_CRO流程",
            "user_actions": {
                "explicit": "dislike",
                "implicit": {"dwell_time": 3, "copy_action": False, "bounce": True}
            },
            "reward": 0.15
        })
    
    session.close()
    return session


def demo():
    """演示用法"""
    # 初始化
    manager = IntentAssociationManager("data/chunk_intent_associations.json")
    
    # 模拟聚类初始化
    clustering_result = {
        "clusters": [
            {
                "cluster_id": "c001",
                "intent_label": "医疗试验用药申请",
                "chunks": ["chunk_001"],
                "confidence": 0.75
            },
            {
                "cluster_id": "c002",
                "intent_label": "原料制备流程",
                "chunks": ["chunk_002"],
                "confidence": 0.68
            },
            {
                "cluster_id": "c003",
                "intent_label": "CRO流程",
                "chunks": ["chunk_003"],
                "confidence": 0.70
            }
        ]
    }
    manager.init_from_clustering(clustering_result)
    
    # 创建 RL 更新器
    updater = RLUpdater(manager, batch_size=3)
    
    # 模拟会话
    sessions = [
        create_sample_session("s001", "positive_with_clarification"),
        create_sample_session("s002", "negative_explicit"),
        create_sample_session("s003", "positive_with_clarification"),
    ]
    
    # 添加会话
    for i, session in enumerate(sessions):
        print(f"\n添加会话 {session.session_id}...")
        triggered = updater.add_session(session)
        print(f"  待处理: {updater.get_pending_count()}")
        print(f"  触发批量更新: {triggered}")
        
        if triggered:
            # 查看更新后的状态
            print("\n更新后的 chunk_002 意图:")
            for intent in manager.get_top_intents("chunk_002"):
                print(f"  {intent['intent_label']}: {intent['confidence']:.2f}")
    
    print(f"\n最终统计: {manager.get_stats()}")


if __name__ == "__main__":
    demo()