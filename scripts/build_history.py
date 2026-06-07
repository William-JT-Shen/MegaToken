#!/usr/bin/env python3
"""
从 history/ 文件夹中的每日 pricing.json 快照生成 history.json
history.json 结构为按模型存储的 OHLC 时间序列，供前端绘制 K 线图。
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

HISTORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'history')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'history.json')
PRICING_FILE = os.path.join(os.path.dirname(__file__), '..', 'pricing.json')

def load_all_snapshots():
    """返回排序后的日期列表和对应数据"""
    snaps = []
    if not os.path.exists(HISTORY_DIR):
        print(f"警告: 历史文件夹 {HISTORY_DIR} 不存在")
        return snaps

    files = sorted(os.listdir(HISTORY_DIR))
    if not files:
        print("警告: 历史文件夹为空")
        return snaps

    for fname in files:
        if not fname.endswith('.json'):
            continue
        date_str = fname.replace('.json', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"跳过无效文件名: {fname}")
            continue
        try:
            with open(os.path.join(HISTORY_DIR, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
                models = data.get('models', [])
                snaps.append((date_str, models))
        except Exception as e:
            print(f"读取文件 {fname} 失败: {e}")
    
    return snaps

def build_ohlc(snaps):
    """
    为每个模型构建 OHLC 日线列表。
    返回数据结构：
    {
        "models": {
            "vendor::model": {
                "vendor": "...",
                "model": "...",
                "context": "...",
                "note": "...",
                "input_ohlc": [
                    ["2025-06-01", open, close, low, high],  // 输入价格
                    ...
                ],
                "output_ohlc": [...]  // 输出价格 OHLC
            },
            ...
        },
        "last_updated": "2025-06-01"
    }
    """
    # 按模型聚合所有日期的价格
    timeline = defaultdict(dict)  # model_key -> {date: {"input": x, "output": y}}

    for date_str, models in snaps:
        for m in models:
            key = f"{m['vendor']}::{m['model']}"
            timeline[key][date_str] = {
                "input": m.get("input"),
                "output": m.get("output"),
                "context": m.get("context", ""),
                "note": m.get("note", "")
            }

    result_models = {}

    for key, date_prices in timeline.items():
        vendor, model = key.split('::', 1)
        sorted_dates = sorted(date_prices.keys())
        if not sorted_dates:
            continue

        # 初始化上下文等信息（取第一个快照的值）
        first_entry = date_prices[sorted_dates[0]]
        context = first_entry.get("context", "")
        note = first_entry.get("note", "")

        input_ohlc = []
        output_ohlc = []

        # 填充每一天的 OHLC（包括没有记录的日子用前值填充）
        last_input = None
        last_output = None
        
        # 获取整个日期范围
        start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in date_prices:
                p = date_prices[date_str]
                inp = p["input"]
                out = p["output"]
                # 更新最近价格
                last_input = inp
                last_output = out
            else:
                # 无数据日沿用最近的价格
                inp = last_input
                out = last_output

            # 生成 OHLC 数据（由于是每日快照，开盘=收盘=最高=最低）
            if inp is not None:
                input_ohlc.append([date_str, inp, inp, inp, inp])  # [date, open, close, low, high]
            if out is not None:
                output_ohlc.append([date_str, out, out, out, out])

            current_date += timedelta(days=1)

        result_models[key] = {
            "vendor": vendor,
            "model": model,
            "context": context,
            "note": note,
            "input_ohlc": input_ohlc,   # 每项 [date, open, close, low, high]
            "output_ohlc": output_ohlc
        }

    return {"models": result_models, "last_updated": datetime.now().strftime('%Y-%m-%d')}

import random

def init_sample_history():
    """初始化示例历史数据（用于测试）"""
    print("检测到没有历史快照，正在生成示例历史数据...")
    
    # 创建 history 目录
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # 读取当前定价数据
    if os.path.exists(PRICING_FILE):
        with open(PRICING_FILE, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        current_models = current_data.get('models', [])
    else:
        # 如果没有当前定价数据，使用示例数据
        current_models = [
            {"vendor": "OpenAI", "model": "GPT-4o", "input": 2.5, "output": 10.0, "context": "128K", "note": "多模态"},
            {"vendor": "OpenAI", "model": "GPT-4o mini", "input": 0.15, "output": 0.6, "context": "128K", "note": "多模态"},
            {"vendor": "Anthropic", "model": "Claude 3.5 Sonnet", "input": 3.0, "output": 15.0, "context": "200K", "note": ""},
            {"vendor": "Google", "model": "Gemini 1.5 Pro", "input": 1.25, "output": 2.5, "context": "1M", "note": "长上下文"},
            {"vendor": "Google", "model": "Gemini 1.5 Flash", "input": 0.075, "output": 0.15, "context": "1M", "note": "高效"},
        ]
    
    # 为每个模型生成独立的价格历史
    # 使用随机种子确保可重复性，但每个模型有不同的种子
    model_histories = {}
    for idx, m in enumerate(current_models):
        model_key = f"{m['vendor']}::{m['model']}"
        random.seed(hash(model_key) % 10000)  # 每个模型使用不同的随机种子
        
        # 生成该模型的价格历史（30天）
        input_history = []
        output_history = []
        
        # 初始价格
        current_input = m['input']
        current_output = m['output']
        
        for day in range(30):
            # 模拟真实的价格变动：
            # 1. 小幅随机波动（±5%）
            # 2. 偶尔的价格调整（±15%）
            # 3. 不同模型有不同的波动频率和幅度
            
            # 基础波动率（每个模型不同）
            volatility = 0.02 + (idx % 5) * 0.01  # 2% 到 6% 的基础波动
            
            # 随机决定是否发生价格调整（约10%概率）
            if random.random() < 0.1:
                # 价格调整：较大幅度的变动
                adjustment = random.uniform(-0.15, 0.15)
                current_input *= (1 + adjustment)
                current_output *= (1 + adjustment)
            else:
                # 日常小幅波动
                daily_change = random.uniform(-volatility, volatility)
                current_input *= (1 + daily_change)
                current_output *= (1 + daily_change)
            
            # 确保价格不会变成负数或零
            current_input = max(current_input, 0.001)
            current_output = max(current_output, 0.001)
            
            input_history.append(round(current_input, 4))
            output_history.append(round(current_output, 4))
        
        model_histories[model_key] = {
            'input': input_history,
            'output': output_history,
            'model': m
        }
    
    # 生成过去30天的示例历史数据
    today = datetime.now()
    for i in range(30):
        date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        history_models = []
        
        for m in current_models:
            model_key = f"{m['vendor']}::{m['model']}"
            history = model_histories[model_key]
            
            history_models.append({
                "vendor": m['vendor'],
                "model": m['model'],
                "input": history['input'][i],
                "output": history['output'][i],
                "context": m['context'],
                "note": m['note']
            })
        
        snapshot_data = {
            "last_updated": date_str,
            "models": history_models
        }
        
        with open(os.path.join(HISTORY_DIR, f'{date_str}.json'), 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
    
    print(f"已生成 30 天的示例历史数据，每个模型有独立的价格波动模式")

def main():
    snaps = load_all_snapshots()
    
    # 如果没有历史快照，初始化示例数据
    if not snaps:
        init_sample_history()
        snaps = load_all_snapshots()
    
    if not snaps:
        print("错误: 无法获取历史快照数据")
        sys.exit(1)

    history_data = build_ohlc(snaps)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)
    
    print(f"OK: history.json 已生成，包含 {len(history_data['models'])} 个模型")
    print(f"OK: 数据覆盖日期范围: {snaps[0][0]} 至 {snaps[-1][0]}")

if __name__ == '__main__':
    main()