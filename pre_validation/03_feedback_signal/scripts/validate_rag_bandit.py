#!/usr/bin/env python3
"""
完整 RAG + Bandit 验证

流程：
1. RAG 召回层：查询 → 嵌入 → 向量检索 → Top-K 候选
2. Bandit 排序层：候选 → UCB 分数重排 → 最优选择
3. 反馈闭环：用户反馈 → 奖励计算 → Bandit 更新

对比：
- 纯 RAG（只用向量相似度）
- RAG + Bandit（向量召回 + Bandit 精排）
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """知识库内容块"""
    chunk_id: str
    content: str
    intent: str
    embedding: np.ndarray = None


class SimpleVectorStore:
    """
    简单向量存储
    
    用于验证阶段，生产环境可替换为 FAISS/Milvus
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.chunks: Dict[str, Chunk] = {}
        self.embeddings: np.ndarray = None  # [N, D]
        self.chunk_ids: List[str] = []
    
    def add_chunk(self, chunk: Chunk):
        """添加 chunk"""
        if chunk.embedding is None:
            # 如果没有嵌入，生成模拟嵌入
            np.random.seed(hash(chunk.content) % (2**32))
            chunk.embedding = np.random.randn(self.embedding_dim)
            chunk.embedding = chunk.embedding / np.linalg.norm(chunk.embedding)
        
        self.chunks[chunk.chunk_id] = chunk
        self._rebuild_index()
    
    def _rebuild_index(self):
        """重建索引"""
        self.chunk_ids = list(self.chunks.keys())
        self.embeddings = np.array([
            self.chunks[cid].embedding for cid in self.chunk_ids
        ])
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        向量检索
        
        Args:
            query_embedding: 查询嵌入
            top_k: 返回数量
        
        Returns:
            [(chunk_id, similarity), ...]
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # 余弦相似度
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        similarities = np.dot(self.embeddings, query_norm)
        
        # 排序
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            chunk_id = self.chunk_ids[idx]
            sim = similarities[idx]
            results.append((chunk_id, float(sim)))
        
        return results
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """获取 chunk"""
        return self.chunks.get(chunk_id)


class MockEmbeddingModel:
    """
    模拟嵌入模型
    
    验证阶段使用，生产环境替换为 SBERT
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
    
    def encode(self, text: str) -> np.ndarray:
        """
        文本 → 嵌入
        
        模拟语义嵌入，加入关键词特征
        """
        embedding = np.zeros(self.embedding_dim)
        text_lower = text.lower()
        
        # 关键词特征映射
        keyword_features = {
            # chunk_001 特征
            ("原料", "申请", "审批", "原材料"): 0,
            ("试验用药", "原料"): 0,
            
            # chunk_002 特征  
            ("cro", "外包", "供应商"): 50,
            ("临床试验", "外包"): 50,
            
            # chunk_003 特征
            ("制备", "工艺", "流程"): 100,
            ("原料制备", "干燥"): 100,
            
            # chunk_004 特征
            ("临床试验", "方案", "设计"): 150,
            ("纳入排除", "样本量"): 150,
            
            # chunk_005 特征
            ("注册", "申报", "上市"): 200,
            ("药品注册", "审批"): 200,
        }
        
        # 根据关键词设置特征
        for keywords, start_idx in keyword_features.items():
            for kw in keywords:
                if kw in text_lower:
                    embedding[start_idx:start_idx+50] += 0.8
        
        # 加入一些噪声
        np.random.seed(hash(text) % (2**32))
        noise = np.random.randn(self.embedding_dim) * 0.1
        embedding += noise
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding


class RAGBanditSystem:
    """
    完整的 RAG + Bandit 系统
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        exploration_alpha: float = 1.0,
        rag_top_k: int = 5
    ):
        self.embedding_dim = embedding_dim
        self.exploration_alpha = exploration_alpha
        self.rag_top_k = rag_top_k
        
        # 组件
        self.embedding_model = MockEmbeddingModel(embedding_dim)
        self.vector_store = SimpleVectorStore(embedding_dim)
        
        # Bandit 参数（每个 chunk 一个）
        self.bandit_params: Dict[str, Dict] = {}
        
        # 统计
        self.stats = {
            "total_queries": 0,
            "rag_correct": 0,      # 纯 RAG 选对
            "bandit_correct": 0,   # Bandit 选对
            "feedback_count": 0
        }
    
    def add_document(self, chunk_id: str, content: str, intent: str):
        """添加文档到知识库"""
        embedding = self.embedding_model.encode(content)
        chunk = Chunk(
            chunk_id=chunk_id,
            content=content,
            intent=intent,
            embedding=embedding
        )
        self.vector_store.add_chunk(chunk)
        
        # 初始化 Bandit 参数
        self.bandit_params[chunk_id] = {
            "A": np.eye(self.embedding_dim),  # LinUCB A 矩阵
            "b": np.zeros(self.embedding_dim), # LinUCB b 向量
            "pull_count": 0,
            "total_reward": 0.0,
            "avg_reward": 0.5  # 初始置信度
        }
    
    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[str, float]]:
        """
        RAG 召回
        
        Args:
            query: 用户查询
            top_k: 返回数量
        
        Returns:
            [(chunk_id, similarity), ...]
        """
        if top_k is None:
            top_k = self.rag_top_k
        
        query_embedding = self.embedding_model.encode(query)
        return self.vector_store.search(query_embedding, top_k)
    
    def select_with_bandit(
        self, 
        query: str, 
        candidates: List[Tuple[str, float]]
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Bandit 精排
        
        Args:
            query: 用户查询
            candidates: RAG 召回的候选 [(chunk_id, similarity), ...]
        
        Returns:
            (选择的 chunk_id, UCB 分数, 排序后的候选)
        """
        if not candidates:
            return None, 0.0, []
        
        query_embedding = self.embedding_model.encode(query)
        
        # 计算每个候选的 UCB 分数
        scored_candidates = []
        for chunk_id, similarity in candidates:
            if chunk_id not in self.bandit_params:
                # 新 chunk，用相似度作为初始分数
                score = similarity
            else:
                params = self.bandit_params[chunk_id]
                
                # LinUCB 计算
                # θ = A⁻¹b
                theta = np.linalg.solve(params["A"], params["b"])
                
                # UCB = θᵀx + α × √(xᵀA⁻¹x)
                p = np.dot(theta, query_embedding)
                
                A_inv = np.linalg.inv(params["A"])
                uncertainty = np.sqrt(np.dot(query_embedding, np.dot(A_inv, query_embedding)))
                
                ucb_score = p + self.exploration_alpha * uncertainty
                
                # 结合相似度
                score = 0.3 * similarity + 0.7 * (ucb_score / 2)  # 归一化
            
            scored_candidates.append((chunk_id, score))
        
        # 排序
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        selected = scored_candidates[0][0]
        selected_score = scored_candidates[0][1]
        
        return selected, selected_score, scored_candidates
    
    def query(
        self, 
        query: str,
        ground_truth: str = None
    ) -> Dict:
        """
        完整查询流程
        
        Args:
            query: 用户查询
            ground_truth: 正确答案的 chunk_id（用于验证）
        
        Returns:
            {
                "rag_top1": chunk_id,
                "bandit_selected": chunk_id,
                "rag_correct": bool,
                "bandit_correct": bool,
                "candidates": [...]
            }
        """
        self.stats["total_queries"] += 1
        
        # 1. RAG 召回
        candidates = self.retrieve(query, top_k=self.rag_top_k)
        
        if not candidates:
            return {
                "rag_top1": None,
                "bandit_selected": None,
                "rag_correct": False,
                "bandit_correct": False,
                "candidates": []
            }
        
        # 2. RAG Top-1
        rag_top1 = candidates[0][0]
        
        # 3. Bandit 精排
        bandit_selected, bandit_score, ranked = self.select_with_bandit(query, candidates)
        
        # 4. 验证
        rag_correct = (rag_top1 == ground_truth) if ground_truth else None
        bandit_correct = (bandit_selected == ground_truth) if ground_truth else None
        
        if rag_correct:
            self.stats["rag_correct"] += 1
        if bandit_correct:
            self.stats["bandit_correct"] += 1
        
        return {
            "rag_top1": rag_top1,
            "bandit_selected": bandit_selected,
            "rag_correct": rag_correct,
            "bandit_correct": bandit_correct,
            "candidates": ranked
        }
    
    def update_from_feedback(
        self,
        chunk_id: str,
        query: str,
        reward: float
    ):
        """
        根据用户反馈更新 Bandit
        
        Args:
            chunk_id: 被选择的 chunk
            query: 用户查询
            reward: 奖励值
        """
        if chunk_id not in self.bandit_params:
            return
        
        params = self.bandit_params[chunk_id]
        query_embedding = self.embedding_model.encode(query)
        
        # LinUCB 更新
        # A ← A + xxᵀ
        # b ← b + r × x
        params["A"] += np.outer(query_embedding, query_embedding)
        params["b"] += reward * query_embedding
        
        params["pull_count"] += 1
        params["total_reward"] += reward
        params["avg_reward"] = params["total_reward"] / params["pull_count"]
        
        self.stats["feedback_count"] += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats["total_queries"]
        return {
            "total_queries": total,
            "rag_accuracy": self.stats["rag_correct"] / total if total > 0 else 0,
            "bandit_accuracy": self.stats["bandit_correct"] / total if total > 0 else 0,
            "feedback_count": self.stats["feedback_count"]
        }


def create_knowledge_base() -> List[Dict]:
    """
    创建测试知识库
    
    模拟医疗领域的文档
    """
    documents = [
        {
            "chunk_id": "chunk_001",
            "content": "医疗试验用药原材料申请审批流程：首先需要提交原材料申请表，附上原料质量检测报告，经质量部门审核后，提交至临床试验管理部门审批。整个流程约需15个工作日。",
            "intent": "医疗试验用药原材料申请审批"
        },
        {
            "chunk_id": "chunk_002",
            "content": "药物研发CRO外包流程：选择CRO供应商时需评估其资质、经验和报价。签订合同后，CRO负责临床试验方案设计、受试者招募、数据管理等环节。项目管理周期通常为6-12个月。",
            "intent": "药物研发CRO外包"
        },
        {
            "chunk_id": "chunk_003",
            "content": "原料制备工艺流程：原料制备包括原料称量、溶解、过滤、干燥等步骤。需要严格控制温度、pH值和反应时间。制备完成后需进行质量检验，合格后方可入库。",
            "intent": "原料制备工艺"
        },
        {
            "chunk_id": "chunk_004",
            "content": "临床试验方案设计要点：试验方案需明确研究目的、纳入排除标准、样本量计算、随机化方法、盲法设计等。方案需经伦理委员会审批后方可实施。",
            "intent": "临床试验方案设计"
        },
        {
            "chunk_id": "chunk_005",
            "content": "药品注册申报流程：完成临床试验后，整理注册申报资料，包括药学、非临床、临床研究资料。提交至药品监管部门后，需经历审评、现场核查等环节，获得批准后方可上市。",
            "intent": "药品注册申报"
        }
    ]
    return documents


def create_test_queries() -> List[Dict]:
    """
    创建测试查询
    
    每个查询有对应的正确答案和用户反馈场景
    """
    queries = [
        # 查询 1: 匹配 chunk_001
        {
            "query": "试验用药的原料申请要走什么流程？",
            "ground_truth": "chunk_001",
            "scenario": "positive",
            "feedback_reward": 0.85
        },
        # 查询 2: 匹配 chunk_002
        {
            "query": "想找CRO做临床试验外包，流程是怎样的？",
            "ground_truth": "chunk_002",
            "scenario": "positive",
            "feedback_reward": 0.80
        },
        # 查询 3: 匹配 chunk_003
        {
            "query": "原料制备过程中要注意哪些工艺要点？",
            "ground_truth": "chunk_003",
            "scenario": "positive",
            "feedback_reward": 0.90
        },
        # 查询 4: 歧义查询，可能召回错误
        {
            "query": "申请流程是什么？",  # 太泛，可能召回 chunk_001 或 chunk_005
            "ground_truth": "chunk_001",  # 用户实际问的是原料申请
            "scenario": "clarify",
            "feedback_reward": 0.60  # 用户可能需要澄清
        },
        # 查询 5: 匹配 chunk_004
        {
            "query": "临床试验方案怎么设计？有哪些要点？",
            "ground_truth": "chunk_004",
            "scenario": "positive",
            "feedback_reward": 0.88
        },
        # 查询 6: 匹配 chunk_005
        {
            "query": "新药上市需要走什么注册申报流程？",
            "ground_truth": "chunk_005",
            "scenario": "positive",
            "feedback_reward": 0.82
        },
        # 查询 7: 相似但不同意图
        {
            "query": "原材料审批要多久？",
            "ground_truth": "chunk_001",
            "scenario": "positive",
            "feedback_reward": 0.85
        },
        # 查询 8: 负反馈场景
        {
            "query": "CRO供应商选择标准是什么？",
            "ground_truth": "chunk_002",
            "scenario": "negative",  # 用户对答案不满意
            "feedback_reward": 0.35
        }
    ]
    return queries


def run_full_validation():
    """
    完整验证：RAG + Bandit
    """
    
    print("=" * 70)
    print("RAG + Bandit 完整验证")
    print("=" * 70)
    
    # 1. 初始化系统
    print("\n[Step 1] 初始化系统...")
    
    system = RAGBanditSystem(
        embedding_dim=384,
        exploration_alpha=1.0,
        rag_top_k=3
    )
    
    # 添加知识库
    kb = create_knowledge_base()
    for doc in kb:
        system.add_document(
            chunk_id=doc["chunk_id"],
            content=doc["content"],
            intent=doc["intent"]
        )
    
    print(f"  知识库: {len(kb)} 个文档")
    
    # 2. 测试查询
    print("\n[Step 2] 测试查询...")
    
    test_queries = create_test_queries()
    
    results = []
    
    for i, q in enumerate(test_queries):
        print(f"\n--- 查询 {i+1}: {q['query'][:30]}... ---")
        
        # 执行查询
        result = system.query(q["query"], q["ground_truth"])
        
        # 显示结果
        print(f"  RAG Top-1: {result['rag_top1']} {'✅' if result['rag_correct'] else '❌'}")
        print(f"  Bandit 选择: {result['bandit_selected']} {'✅' if result['bandit_correct'] else '❌'}")
        
        # 模拟用户反馈
        if result["bandit_selected"]:
            system.update_from_feedback(
                result["bandit_selected"],
                q["query"],
                q["feedback_reward"]
            )
            print(f"  用户反馈: {q['feedback_reward']:.2f}")
        
        results.append({
            "query": q["query"],
            "ground_truth": q["ground_truth"],
            "rag_top1": result["rag_top1"],
            "bandit_selected": result["bandit_selected"],
            "rag_correct": result["rag_correct"],
            "bandit_correct": result["bandit_correct"],
            "reward": q["feedback_reward"]
        })
    
    # 3. 统计
    print("\n" + "=" * 70)
    print("验证结果")
    print("=" * 70)
    
    stats = system.get_stats()
    
    print(f"\n总查询数: {stats['total_queries']}")
    print(f"RAG 准确率: {stats['rag_accuracy']:.2%}")
    print(f"RAG + Bandit 准确率: {stats['bandit_accuracy']:.2%}")
    print(f"反馈次数: {stats['feedback_count']}")
    
    # 4. 分析改进
    print("\n" + "=" * 70)
    print("改进分析")
    print("=" * 70)
    
    rag_correct_count = sum(1 for r in results if r["rag_correct"])
    bandit_correct_count = sum(1 for r in results if r["bandit_correct"])
    
    # 统计 Bandit 是否纠正了 RAG 的错误
    bandit_fixed = sum(
        1 for r in results 
        if not r["rag_correct"] and r["bandit_correct"]
    )
    
    # 统计 Bandit 是否弄错了 RAG 对的
    bandit_broke = sum(
        1 for r in results 
        if r["rag_correct"] and not r["bandit_correct"]
    )
    
    print(f"\nRAG 正确: {rag_correct_count}")
    print(f"Bandit 正确: {bandit_correct_count}")
    print(f"Bandit 纠正 RAG 错误: {bandit_fixed}")
    print(f"Bandit 弄错 RAG 正确: {bandit_broke}")
    
    # 5. 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
        "results": results,
        "analysis": {
            "rag_correct": rag_correct_count,
            "bandit_correct": bandit_correct_count,
            "bandit_fixed": bandit_fixed,
            "bandit_broke": bandit_broke
        }
    }
    
    report_path = Path("results/rag_bandit_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")
    
    return stats


if __name__ == "__main__":
    run_full_validation()