# -*- coding: utf-8 -*-
"""
IntentWeight 状态持久化
IntentWeight State Persistence

使用原子写入确保状态文件不会因进程中断而损坏。
Uses atomic writes to prevent state file corruption from process interruption.
"""
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


def save_state(state: Dict, path: Path):
    """
    原子写入状态文件
    Atomically write state to file

    Args:
        state: 要保存的状态字典
        path: 目标文件路径
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # 先写到临时文件，再原子重命名
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, suffix=".tmp", prefix=path.stem
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        logger.debug(f"State saved to {path}")
    except Exception:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_state(path: Path) -> Optional[Dict]:
    """
    加载状态文件
    Load state from file

    Args:
        path: 状态文件路径

    Returns:
        状态字典，文件不存在时返回 None
    """
    if not path.exists():
        logger.debug(f"State file not found: {path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    logger.debug(f"State loaded from {path}")
    return state
