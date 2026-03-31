#!/usr/bin/env python3
"""
Speech Act 零样本分类器

使用 Speech Act Theory 5类对用户查询进行零样本意图分类
无需任何种子数据，基于语言学理论框架

用法:
    python speech_act_classify.py --data processed/banking77_processed.json --output results/speech_act_banking77.json
    python speech_act_classify.py --data processed/clinc150_processed.json --output results/speech_act_clinc150.json
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import os

# 尝试导入 LLM 客户端
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class SpeechActResult:
    """分类结果"""
    text: str
    speech_act: str
    confidence: float
    reason: Optional[str] = None
    original_intent: Optional[str] = None  # 原始意图标签（如果有）


# Speech Act 5类定义
SPEECH_ACT_SCHEMA = {
    "L_ASSERTIVE": {
        "name": "Assertive",
        "name_zh": "陈述",
        "definition": "陈述事实，让听者相信某事为真",
        "keywords": ["is", "are", "was", "were", "what", "where", "when", "who", "which", "how many", "how much", "是", "什么", "多少", "哪里"],
        "patterns": ["what is", "where is", "when did", "who is", "how many", "how much", "tell me about", "什么是", "在哪里"]
    },
    "L_DIRECTIVE": {
        "name": "Directive", 
        "name_zh": "指令",
        "definition": "指令行为，希望听者执行某事",
        "keywords": ["please", "help", "can i", "could you", "how do", "how can", "i need", "i want", "请", "帮", "怎么"],
        "patterns": ["can i", "could you", "how do i", "how can i", "i need to", "i want to", "what can i do", "help me", "请帮我", "怎么做"]
    },
    "L_COMMISSIVE": {
        "name": "Commissive",
        "name_zh": "承诺",
        "definition": "承诺行为，说话者承诺未来行动",
        "keywords": ["will", "promise", "guarantee", "commit", "会", "保证", "承诺"],
        "patterns": ["i will", "i promise", "i guarantee", "我会", "保证"]
    },
    "L_EXPRESSIVE": {
        "name": "Expressive",
        "name_zh": "表达",
        "definition": "表达行为，表达心理状态",
        "keywords": ["thank", "sorry", "great", "love", "hate", "appreciate", "谢谢", "抱歉", "太"],
        "patterns": ["thank you", "thanks", "sorry", "i love", "i hate", "谢谢", "抱歉"]
    },
    "L_DECLARATIVE": {
        "name": "Declarative",
        "name_zh": "宣告",
        "definition": "宣告行为，通过言语改变世界状态",
        "keywords": ["declare", "announce", "appoint", "resign", "fire", "宣布", "任命", "辞职"],
        "patterns": ["i declare", "i announce", "i resign", "我宣布", "任命"]
    }
}


# 分类 Prompt
CLASSIFICATION_PROMPT = """你是一个意图分类专家，基于 Speech Act Theory 分析用户查询的言语行为意图。

Speech Act 分类体系：

1. **Assertive (陈述)**: 陈述或询问事实信息
   - 定义：让听者相信某事为真
   - 例子："今天天气怎么样？"、"什么是X？"、"公司的地址在哪里？"
   - 方向：Words → World（语言描述世界）

2. **Directive (指令)**: 请求帮助、指导或行动
   - 定义：希望听者执行某动作
   - 例子："请帮我..."、"怎么做...？"、"我需要..."
   - 方向：World → Words（希望世界改变）

3. **Commissive (承诺)**: 做出承诺或表达未来行动
   - 定义：说话者承诺未来行动
   - 例子："我会完成的"、"保证没问题"
   - 方向：World → Words（承诺改变世界）

4. **Expressive (表达)**: 表达情感或态度
   - 定义：表达心理状态
   - 例子："谢谢！"、"抱歉打扰"、"太好了"
   - 方向：Null（不改变世界）

5. **Declarative (宣告)**: 执行宣告性操作
   - 定义：通过言语改变世界状态
   - 例子："我宣布..."、"任命..."、"我辞职"
   - 方向：World ↔ Words（言语即行动）

用户查询：{query}

请分析并严格输出以下 JSON 格式（不要输出其他内容）：
{{"speech_act": "ASSERTIVE", "confidence": 0.95, "reason": "简短理由"}}

speech_act 只能是以下之一：ASSERTIVE, DIRECTIVE, COMMISSIVE, EXPRESSIVE, DECLARATIVE
confidence 是 0.0 到 1.0 之间的数值
"""


class ZeroShotClassifier:
    """零样本 Speech Act 分类器"""
    
    def __init__(self, llm_backend: str = "openai", model: str = None):
        """
        Args:
            llm_backend: LLM 后端 ("openai", "bailian", "ollama", "rule")
            model: 模型名称
        """
        self.llm_backend = llm_backend
        self.model = model or self._get_default_model()
        self.schema = SPEECH_ACT_SCHEMA
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        defaults = {
            "openai": "gpt-4o-mini",
            "bailian": "qwen-plus",
            "ollama": "qwen2.5:7b",
            "rule": "rule-based"
        }
        return defaults.get(self.llm_backend, "rule-based")
    
    def classify(self, query: str) -> SpeechActResult:
        """分类单个查询"""
        if self.llm_backend == "rule":
            return self._rule_based_classify(query)
        else:
            return self._llm_classify(query)
    
    def _rule_based_classify(self, query: str) -> SpeechActResult:
        """基于规则的快速分类（作为 fallback 或快速验证）"""
        query_lower = query.lower()
        
        # 优先级顺序：DECLARATIVE > EXPRESSIVE > COMMISSIVE > DIRECTIVE > ASSERTIVE
        # 这样可以避免后面的类型覆盖前面类型
        
        # DECLARATIVE: 宣告性语句
        declarative_patterns = [
            # 英文
            "i hereby", "i declare", "i pronounce", "i sentence", 
            "i appoint", "i resign", "you are fired", "is now in effect",
            "i certify", "is now repealed",
            # 中文 - 宣告类（正式用语）
            "我宣布", "我任命", "我辞职", "我开除", "我判决", "我宣告",
            "即日起", "正式生效", "我认定", "我解除", "我撤销",
            "任命为", "免去", "批准", "不准", "驳回",
        ]
        for pattern in declarative_patterns:
            if pattern in query_lower:
                return SpeechActResult(text=query, speech_act="L_DECLARATIVE", 
                                       confidence=0.9, reason="declarative pattern matched")
        
        # EXPRESSIVE: 表达性语句
        expressive_patterns = [
            # 英文
            "thank", "thanks", "sorry", "apologize", "appreciate",
            "congratulation", "i'm happy", "i'm grateful", "i regret",
            "i'm disappointed", "wonderful", "great news",
            # 中文 - 感谢类
            "谢谢", "感谢", "多谢", "谢了", "辛苦了", "麻烦你了", "劳驾了",
            "谢谢你", "感谢你", "太感谢", "非常感谢",
            # 中文 - 道歉类
            "抱歉", "对不起", "不好意思", "惭愧", "我错了", "是我的错",
            "打扰了", "冒昧", "失礼",
            # 中文 - 赞美/情绪类
            "太好了", "真棒", "厉害", "不错", "很好", "精彩", "太棒了",
            "高兴", "开心", "激动", "欣慰",
            # 中文 - 负面情绪
            "糟糕", "烦人", "讨厌", "可惜", "遗憾", "失望", "难过", "伤心",
        ]
        for pattern in expressive_patterns:
            if pattern in query_lower:
                return SpeechActResult(text=query, speech_act="L_EXPRESSIVE",
                                       confidence=0.9, reason="expressive pattern matched")
        
        # COMMISSIVE: 承诺性语句
        commissive_patterns = [
            # 英文
            "i will", "i promise", "i guarantee", "i commit",
            "i assure", "i'll",
            # 中文 - 承诺类
            "我会", "我保证", "我承诺", "一定", "没问题", "放心",
            "必定", "肯定", "务必", "我会的", "包在我身上",
            "答应你", "我答应", "我确定", "我一定",
        ]
        for pattern in commissive_patterns:
            if pattern in query_lower:
                return SpeechActResult(text=query, speech_act="L_COMMISSIVE",
                                       confidence=0.9, reason="commissive pattern matched")
        
        # DIRECTIVE: 指令性语句
        directive_patterns = [
            # 英文
            "please", "can you", "could you", "help me", "how do i",
            "how can i", "i need to", "i want to", "book me",
            "tell me",
            # 中文 - 请求类（礼貌）
            "请", "麻烦", "劳驾", "请问", "请教",
            # 中文 - 请求类（常用）
            "能不能", "可不可以", "帮我看", "帮我查", "帮我办",
            "帮帮我", "帮我看看", "麻烦帮我", "请问一下",
            # 中文 - 请求类（直接）
            "我要", "我想", "帮我", "给我", "让我",
            "能不能帮我", "可以帮我", "帮我处理", "帮我解决",
            # 中文 - 疑问求助
            "怎么", "如何", "怎么办", "怎么做", "怎样",
            "想问一下", "有个问题", "想请教",
        ]
        for pattern in directive_patterns:
            if pattern in query_lower:
                return SpeechActResult(text=query, speech_act="L_DIRECTIVE",
                                       confidence=0.85, reason="directive pattern matched")
        
        # ASSERTIVE: 默认为陈述性语句
        return SpeechActResult(text=query, speech_act="L_ASSERTIVE",
                               confidence=0.7, reason="default assertive")
    
    def _llm_classify(self, query: str) -> SpeechActResult:
        """使用 LLM 进行分类"""
        prompt = CLASSIFICATION_PROMPT.format(query=query)
        
        try:
            if self.llm_backend == "openai" and HAS_OPENAI:
                response = self._call_openai(prompt)
            elif self.llm_backend == "bailian":
                response = self._call_bailian(prompt)
            else:
                # fallback to rule-based
                return self._rule_based_classify(query)
            
            # 解析响应
            result = self._parse_response(response, query)
            return result
            
        except Exception as e:
            print(f"LLM 调用失败: {e}, 使用规则分类")
            return self._rule_based_classify(query)
    
    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL")
        )
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        return response.choices[0].message.content
    
    def _call_bailian(self, prompt: str) -> str:
        """调用百炼 API"""
        # 百炼 API 调用（简化版）
        url = os.environ.get("BAILIAN_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation")
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        
        if not api_key or not HAS_REQUESTS:
            raise ValueError("百炼 API 未配置")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {"temperature": 0.1}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        return result.get("output", {}).get("text", "")
    
    def _parse_response(self, response: str, query: str) -> SpeechActResult:
        """解析 LLM 响应"""
        import re
        
        # 尝试提取 JSON
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                speech_act = data.get("speech_act", "ASSERTIVE").upper()
                confidence = float(data.get("confidence", 0.8))
                reason = data.get("reason", "")
                
                # 标准化
                intent_id = f"L_{speech_act}"
                if intent_id not in self.schema:
                    intent_id = "L_ASSERTIVE"
                
                return SpeechActResult(
                    text=query,
                    speech_act=intent_id,
                    confidence=min(1.0, max(0.0, confidence)),
                    reason=reason
                )
            except:
                pass
        
        # 解析失败，使用规则
        return self._rule_based_classify(query)
    
    def classify_batch(self, queries: list, show_progress: bool = True) -> list:
        """批量分类"""
        results = []
        total = len(queries)
        
        for i, item in enumerate(queries):
            if isinstance(item, dict):
                query = item.get("text", "")
                original_intent = item.get("intent", None)
            else:
                query = str(item)
                original_intent = None
            
            result = self.classify(query)
            result.original_intent = original_intent
            results.append(result)
            
            if show_progress and (i + 1) % 100 == 0:
                print(f"进度: {i+1}/{total}")
        
        return results


def analyze_results(results: list) -> dict:
    """分析分类结果"""
    # Speech Act 分布
    distribution = {}
    for r in results:
        distribution[r.speech_act] = distribution.get(r.speech_act, 0) + 1
    
    # 与原始意图的映射关系
    intent_mapping = {}
    for r in results:
        if r.original_intent:
            key = f"{r.speech_act}|{r.original_intent}"  # 使用字符串作为key
            intent_mapping[key] = intent_mapping.get(key, 0) + 1
    
    # 置信度统计
    confidences = [r.confidence for r in results]
    
    return {
        "total_samples": len(results),
        "distribution": distribution,
        "distribution_percent": {
            k: round(v / len(results) * 100, 2) 
            for k, v in distribution.items()
        },
        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
        "intent_mapping_sample": dict(list(intent_mapping.items())[:50])  # 只取前50个
    }


def main():
    parser = argparse.ArgumentParser(description="Speech Act 零样本分类")
    parser.add_argument("--data", required=True, help="输入数据文件路径")
    parser.add_argument("--output", required=True, help="输出结果文件路径")
    parser.add_argument("--backend", default="rule", 
                       choices=["openai", "bailian", "ollama", "rule"],
                       help="LLM 后端 (默认 rule-based)")
    parser.add_argument("--model", default=None, help="模型名称")
    parser.add_argument("--limit", type=int, default=None, help="限制处理数量（用于测试）")
    args = parser.parse_args()
    
    # 加载数据
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"错误: 文件不存在 {data_path}")
        return
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 提取查询
    if isinstance(data, list):
        queries = data
    elif isinstance(data, dict) and "queries" in data:
        queries = data["queries"]
    else:
        queries = [{"text": data.get("text", str(data))}]
    
    if args.limit:
        queries = queries[:args.limit]
    
    print(f"加载数据: {len(queries)} 条")
    print(f"使用后端: {args.backend}")
    
    # 初始化分类器
    classifier = ZeroShotClassifier(
        llm_backend=args.backend,
        model=args.model
    )
    
    # 分类
    results = classifier.classify_batch(queries)
    
    # 分析
    analysis = analyze_results(results)
    
    # 保存结果
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "metadata": {
            "source_file": str(data_path),
            "backend": args.backend,
            "model": args.model,
            "total_samples": len(results)
        },
        "analysis": analysis,
        "results": [
            {
                "text": r.text,
                "speech_act": r.speech_act,
                "confidence": r.confidence,
                "reason": r.reason,
                "original_intent": r.original_intent
            }
            for r in results
        ]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print("\n" + "="*50)
    print("Speech Act 分布:")
    print("="*50)
    for act, pct in sorted(analysis["distribution_percent"].items(), key=lambda x: -x[1]):
        print(f"  {act}: {pct}%")
    
    print(f"\n平均置信度: {analysis['avg_confidence']}")
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()