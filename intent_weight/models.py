# -*- coding: utf-8 -*-
"""
IntentRoute 数据模型
IntentRoute Data Models
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """用户反馈请求 / User feedback request"""
    message_id: str
    query: str
    chunk_ids: List[str] = Field(default_factory=list)
    explicit: Optional[str] = None  # "like", "dislike", "correct"
    implicit: Optional[Dict] = None  # {"dwell_time": float, "copy_action": bool, "scroll_depth": float}


class ClusterInfo(BaseModel):
    """聚类信息 / Cluster information"""
    cluster_id: int
    source_files: List[str] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    center_embedding_pca: List[float] = Field(default_factory=list)
    dominant_keywords: List[str] = Field(default_factory=list)
    doc_count: int = 0


class IntentRouteStats(BaseModel):
    """IntentRoute 统计信息 / IntentRoute statistics"""
    enabled: bool = False
    num_clusters: int = 0
    num_documents: int = 0
    total_feedback: int = 0
    cold_start: bool = True
    linucb_alpha: float = 1.0
    arm_stats: List[Dict] = Field(default_factory=list)


# Backward-compatible public name for existing integrations and stored schemas.
IntentWeightStats = IntentRouteStats

__all__ = [
    "ClusterInfo",
    "FeedbackRequest",
    "IntentRouteStats",
    "IntentWeightStats",
]
