#!/usr/bin/env python3
"""
CMID 数据预处理脚本
将 CMID 格式转换为统一格式
"""

import json
from pathlib import Path

INPUT_FILE = Path(__file__).parent / "data" / "CMID" / "CMID.json"
OUTPUT_FILE = Path(__file__).parent / "data" / "cmid" / "cmid_processed.json"

def main():
    print("加载 CMID 数据...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"原始数据: {len(raw_data)} 条")
    
    # 转换格式
    processed = []
    for item in raw_data:
        text = item.get('originalText', '')
        label_4 = item.get('label_4class', ['未知'])[0].strip("'\"")
        label_36 = item.get('label_36class', ['未知'])[0].strip("'\"")
        
        if text:
            processed.append({
                'text': text,
                'label_4': label_4,
                'label_36': label_36
            })
    
    print(f"处理后: {len(processed)} 条")
    
    # 保存
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    
    print(f"保存到: {OUTPUT_FILE}")
    
    # 统计
    label_4_dist = {}
    for item in processed:
        l = item['label_4']
        label_4_dist[l] = label_4_dist.get(l, 0) + 1
    
    print("\n4类分布:")
    for k, v in sorted(label_4_dist.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({v/len(processed)*100:.1f}%)")

if __name__ == "__main__":
    main()