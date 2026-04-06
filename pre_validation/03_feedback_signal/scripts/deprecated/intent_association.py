#!/usr/bin/env python3
"""
内容-意图关联数据管理模块

管理 chunk → intents 的关联数据，支持：
- 初始化（从聚类结果）
- 查询
- 更新
- 持久化
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid


class IntentAssociationManager:
    """内容-意图关联数据管理器"""
    
    def __init__(self, storage_path: str = "data/chunk_intent_associations.json"):
        self.storage_path = Path(storage_path)
        self.associations: Dict[str, Dict] = {}
        self.load()
    
    def load(self):
        """从文件加载关联数据"""
        if self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.associations = data.get("associations", {})
        else:
            self.associations = {}
    
    def save(self):
        """保存关联数据到文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "associations": self.associations
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def init_from_clustering(self, clustering_result: Dict):
        """
        从聚类结果初始化关联数据
        
        Args:
            clustering_result: {
                "clusters": [
                    {
                        "cluster_id": "c001",
                        "intent_label": "医疗试验用药申请",
                        "chunks": ["chunk_001", "chunk_002"],
                        "confidence": 0.85
                    },
                    ...
                ]
            }
        """
        for cluster in clustering_result.get("clusters", []):
            intent_id = f"intent_{cluster['intent_label']}"
            confidence = cluster.get("confidence", 0.5)
            
            for chunk_id in cluster.get("chunks", []):
                if chunk_id not in self.associations:
                    self.associations[chunk_id] = {
                        "chunk_id": chunk_id,
                        "linked_intents": [],
                        "intent_vector": [],
                        "total_feedback_count": 0,
                        "created_at": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    }
                
                # 添加初始意图关联
                self.associations[chunk_id]["linked_intents"].append({
                    "intent_id": intent_id,
                    "intent_label": cluster["intent_label"],
                    "confidence": confidence,
                    "source": "cluster_initial",
                    "reward_history": [],
                    "feedback_count": 0
                })
        
        self.save()
    
    def get_chunk_association(self, chunk_id: str) -> Optional[Dict]:
        """获取 chunk 的关联数据"""
        return self.associations.get(chunk_id)
    
    def get_intent_confidence(self, chunk_id: str, intent_id: str) -> Optional[float]:
        """获取 chunk 对特定意图的置信度"""
        association = self.get_chunk_association(chunk_id)
        if not association:
            return None
        
        for intent in association.get("linked_intents", []):
            if intent["intent_id"] == intent_id:
                return intent["confidence"]
        return None
    
    def update_confidence(
        self, 
        chunk_id: str, 
        intent_id: str, 
        reward: float,
        alpha: float = 0.1
    ) -> float:
        """
        更新 chunk-intent 的置信度
        
        confidence_new = confidence_old + α × (R - confidence_old)
        
        Args:
            chunk_id: 内容块ID
            intent_id: 意图ID
            reward: 奖励值
            alpha: 学习率
        
        Returns:
            新的置信度
        """
        association = self.get_chunk_association(chunk_id)
        if not association:
            return 0.0
        
        for intent in association.get("linked_intents", []):
            if intent["intent_id"] == intent_id:
                old_confidence = intent["confidence"]
                new_confidence = old_confidence + alpha * (reward - old_confidence)
                new_confidence = max(0.0, min(1.0, new_confidence))  # 限制范围
                
                intent["confidence"] = new_confidence
                intent["reward_history"].append(reward)
                intent["feedback_count"] += 1
                association["total_feedback_count"] += 1
                association["last_updated"] = datetime.now().isoformat()
                
                self.save()
                return new_confidence
        
        return 0.0
    
    def add_new_intent(
        self,
        chunk_id: str,
        intent_label: str,
        initial_confidence: float = 0.5,
        source: str = "user_feedback"
    ) -> str:
        """
        为 chunk 添加新意图
        
        Args:
            chunk_id: 内容块ID
            intent_label: 意图标签
            initial_confidence: 初始置信度
            source: 来源
        
        Returns:
            新意图ID
        """
        intent_id = f"intent_{intent_label}_{uuid.uuid4().hex[:8]}"
        
        if chunk_id not in self.associations:
            self.associations[chunk_id] = {
                "chunk_id": chunk_id,
                "linked_intents": [],
                "intent_vector": [],
                "total_feedback_count": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        # 检查是否已存在相同意图
        for intent in self.associations[chunk_id]["linked_intents"]:
            if intent["intent_label"] == intent_label:
                return intent["intent_id"]  # 已存在，返回现有ID
        
        # 添加新意图
        self.associations[chunk_id]["linked_intents"].append({
            "intent_id": intent_id,
            "intent_label": intent_label,
            "confidence": initial_confidence,
            "source": source,
            "reward_history": [],
            "feedback_count": 0
        })
        
        self.associations[chunk_id]["last_updated"] = datetime.now().isoformat()
        self.save()
        
        return intent_id
    
    def get_top_intents(self, chunk_id: str, top_k: int = 3) -> List[Dict]:
        """获取 chunk 的 top-k 意图"""
        association = self.get_chunk_association(chunk_id)
        if not association:
            return []
        
        intents = association.get("linked_intents", [])
        sorted_intents = sorted(intents, key=lambda x: x["confidence"], reverse=True)
        return sorted_intents[:top_k]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_chunks = len(self.associations)
        total_intents = sum(
            len(a.get("linked_intents", [])) 
            for a in self.associations.values()
        )
        total_feedback = sum(
            a.get("total_feedback_count", 0) 
            for a in self.associations.values()
        )
        
        return {
            "total_chunks": total_chunks,
            "total_intents": total_intents,
            "total_feedback": total_feedback,
            "avg_intents_per_chunk": total_intents / total_chunks if total_chunks > 0 else 0
        }


def demo():
    """演示用法"""
    manager = IntentAssociationManager("data/chunk_intent_associations.json")
    
    # 模拟初始化
    clustering_result = {
        "clusters": [
            {
                "cluster_id": "c001",
                "intent_label": "医疗试验用药申请",
                "chunks": ["chunk_001", "chunk_002"],
                "confidence": 0.75
            },
            {
                "cluster_id": "c002",
                "intent_label": "原料制备流程",
                "chunks": ["chunk_003"],
                "confidence": 0.68
            }
        ]
    }
    
    manager.init_from_clustering(clustering_result)
    print("初始化完成")
    print(f"统计: {manager.get_stats()}")
    
    # 模拟更新
    print("\n更新 chunk_001 的意图置信度...")
    new_conf = manager.update_confidence("chunk_001", "intent_医疗试验用药申请", 0.85, alpha=0.2)
    print(f"新置信度: {new_conf}")
    
    # 添加新意图
    print("\n添加新意图...")
    manager.add_new_intent("chunk_001", "原料申请审批", initial_confidence=0.6)
    
    # 查看 top 意图
    print("\nTop intents:")
    for intent in manager.get_top_intents("chunk_001"):
        print(f"  {intent['intent_label']}: {intent['confidence']:.2f}")


if __name__ == "__main__":
    demo()