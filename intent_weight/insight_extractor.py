# -*- coding: utf-8 -*-
"""
Insight 提取模块（规则层 — 零 LLM 成本）
Insight Extractor (Rule-based — Zero LLM Cost)

从用户纠正消息中提取别名映射等结构化 insight。
Extract structured insights (aliases, etc.) from user correction messages.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger


def load_aliases(alias_path: Path) -> Dict[str, List[str]]:
    """加载别名字典 / Load alias dictionary"""
    if not alias_path.exists():
        return {}
    with open(alias_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_aliases(aliases: Dict[str, List[str]], alias_path: Path):
    """保存别名字典 / Save alias dictionary"""
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    with open(alias_path, "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)
    logger.info(f"Aliases saved: {len(aliases)} entries to {alias_path}")


# 别名提取正则模式
# Alias extraction patterns
ALIAS_PATTERNS = [
    # "A就是B" / "A其实就是B"
    re.compile(r"(.{2,20}?)(?:其实)?就是(.{2,20})", re.UNICODE),
    # "A和B是同一个/一样的"
    re.compile(r"(.{2,20}?)和(.{2,20}?)是(?:同一个|一样的|一回事)", re.UNICODE),
    # "A也叫B" / "A又叫B"
    re.compile(r"(.{2,20}?)(?:也|又)叫(.{2,20})", re.UNICODE),
    # "A即B"
    re.compile(r"(.{2,20}?)即(.{2,20})", re.UNICODE),
    # "A指的是B"
    re.compile(r"(.{2,20}?)指的是(.{2,20})", re.UNICODE),
    # "A is B" / "A is also known as B"
    re.compile(r"(.{2,30}?)\s+is\s+(?:also\s+known\s+as\s+)?(.{2,30})", re.IGNORECASE),
    # "A = B"
    re.compile(r"(.{2,20}?)\s*[=＝]\s*(.{2,20})"),
]


def extract_aliases(user_msg: str) -> List[Tuple[str, str]]:
    """
    从用户消息中提取别名关系
    Extract alias relationships from user message

    Args:
        user_msg: 用户消息

    Returns:
        [(entity, alias)] 列表
    """
    results = []
    for pattern in ALIAS_PATTERNS:
        matches = pattern.findall(user_msg)
        for match in matches:
            a, b = match[0].strip(), match[1].strip()
            # 过滤过短或过长的匹配
            if len(a) < 2 or len(b) < 2 or len(a) > 20 or len(b) > 20:
                continue
            # 过滤明显不是实体的（含标点、问号、逗号等）
            if re.search(r'[，。？！、；：\u201c\u201d\u2018\u2019,.?!;:\[\]()（）]', a + b):
                continue
            if re.match(r'^[\d\s\.\,]+$', a) or re.match(r'^[\d\s\.\,]+$', b):
                continue
            results.append((a, b))

    return results


def merge_alias(aliases: Dict[str, List[str]], entity: str, alias: str) -> bool:
    """
    合并一个别名到字典中
    Merge an alias into the dictionary

    双向合并：如果 A→B 已存在，不重复添加；如果 B 是已有 key，合并到 B。

    Returns:
        True if aliases were updated
    """
    # 检查是否已存在
    for key, values in aliases.items():
        if entity.lower() == key.lower() and alias.lower() in [v.lower() for v in values]:
            return False
        if alias.lower() == key.lower() and entity.lower() in [v.lower() for v in values]:
            return False

    # 尝试找到匹配的 key
    for key in list(aliases.keys()):
        if entity.lower() == key.lower():
            if alias not in aliases[key]:
                aliases[key].append(alias)
            return True
        if alias.lower() == key.lower():
            if entity not in aliases[key]:
                aliases[key].append(entity)
            return True

    # 新建条目
    aliases[entity] = [alias]
    return True


def process_correction(
    user_msg: str,
    alias_path: Path,
) -> List[Tuple[str, str]]:
    """
    处理用户纠正消息，提取并保存 insight
    Process user correction message, extract and save insights

    Args:
        user_msg: 用户纠正消息
        alias_path: 别名文件路径

    Returns:
        提取到的别名列表
    """
    extracted = extract_aliases(user_msg)
    if not extracted:
        return []

    aliases = load_aliases(alias_path)
    updated = False
    for entity, alias in extracted:
        if merge_alias(aliases, entity, alias):
            updated = True
            logger.info(f"Alias extracted: '{entity}' ↔ '{alias}'")

    if updated:
        save_aliases(aliases, alias_path)

    return extracted


def expand_query(query: str, alias_path: Path) -> str:
    """
    用别名字典扩展查询
    Expand query using alias dictionary

    Args:
        query: 原始查询
        alias_path: 别名文件路径

    Returns:
        扩展后的查询
    """
    aliases = load_aliases(alias_path)
    if not aliases:
        return query

    q_lower = query.lower()
    expansions = []

    for term, alias_list in aliases.items():
        # 检查 term 是否在 query 中
        if term.lower() in q_lower:
            expansions.extend(alias_list)
        # 检查 alias 是否在 query 中（反向扩展）
        for alias in alias_list:
            if alias.lower() in q_lower:
                expansions.append(term)

    if expansions:
        # 去重
        expansions = list(set(expansions))
        expanded = query + " " + " ".join(expansions)
        logger.debug(f"Query expanded: '{query}' → '{expanded}'")
        return expanded

    return query
