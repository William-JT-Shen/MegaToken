#!/usr/bin/env python3
"""
使用 Playwright 从各大 AI 厂商网站抓取最新 token 价格。
如果某些网站抓取失败，保留原有价格并标记。
自动保存每日快照到 history/ 文件夹，供后续生成 K 线图。
"""

import asyncio
import json
import os
import re
from datetime import date

from playwright.async_api import async_playwright

PRICING_FILE = os.path.join(os.path.dirname(__file__), '..', 'pricing.json')
HISTORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'history')

# 确保历史文件夹存在
os.makedirs(HISTORY_DIR, exist_ok=True)

async def safe_fetch(vendor_name, fetch_func, page):
    """包装抓取函数，捕获全部异常并返回空列表"""
    try:
        models = await fetch_func(page)
        return vendor_name, models
    except Exception as e:
        print(f"{vendor_name} 抓取失败: {type(e).__name__}: {e}")
        return vendor_name, []

# 模型数据格式：{vendor, model, input, output, context, note}
async def fetch_openai(page):
    """OpenAI API 定价页"""
    models = []
    try:
        await page.goto('https://openai.com/api/pricing/', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model_name = await cells[0].inner_text()
                input_text = await cells[1].inner_text()
                output_text = await cells[2].inner_text()
                input_price = extract_price(input_text)
                output_price = extract_price(output_text)
                if model_name and input_price is not None:
                    models.append({
                        "vendor": "OpenAI",
                        "model": model_name.strip(),
                        "input": input_price,
                        "output": output_price,
                        "context": "",
                        "note": ""
                    })
    except Exception as e:
        print(f"OpenAI 抓取失败: {e}")
    return models

async def fetch_anthropic(page):
    """Anthropic 定价页"""
    models = []
    try:
        await page.goto('https://www.anthropic.com/pricing', wait_until='domcontentloaded', timeout=30000)
        elements = await page.query_selector_all('[data-testid="pricing-card"]')
        for el in elements:
            text = await el.inner_text()
            match = re.search(r'(Claude [\d.]+ \w+).*?\$?([\d.]+).*?million.*?\$?([\d.]+)', text, re.DOTALL)
            if match:
                models.append({
                    "vendor": "Anthropic",
                    "model": match.group(1).strip(),
                    "input": float(match.group(2)),
                    "output": float(match.group(3)),
                    "context": "",
                    "note": ""
                })
    except Exception as e:
        print(f"Anthropic 抓取失败: {e}")
    return models

async def fetch_google(page):
    """Google AI Studio 定价页"""
    models = []
    try:
        await page.goto('https://ai.google.dev/pricing', wait_until='domcontentloaded', timeout=30000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model = (await cells[0].inner_text()).strip()
                input_price = extract_price(await cells[1].inner_text())
                output_price = extract_price(await cells[2].inner_text())
                if model and input_price is not None:
                    models.append({
                        "vendor": "Google",
                        "model": model,
                        "input": input_price,
                        "output": output_price,
                        "context": "",
                        "note": ""
                    })
    except Exception as e:
        print(f"Google 抓取失败: {e}")
    return models

async def fetch_deepseek(page):
    """DeepSeek 开放平台"""
    models = []
    try:
        await page.goto('https://platform.deepseek.com/api-docs/pricing', wait_until='domcontentloaded', timeout=30000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model = (await cells[0].inner_text()).strip()
                input_text = await cells[1].inner_text()
                output_text = await cells[2].inner_text()
                input_price = extract_price(input_text)
                output_price = extract_price(output_text)
                if model and input_price is not None:
                    models.append({
                        "vendor": "DeepSeek",
                        "model": model,
                        "input": input_price,
                        "output": output_price,
                        "context": "",
                        "note": ""
                    })
    except Exception as e:
        print(f"DeepSeek 抓取失败: {e}")
    return models

async def fetch_microsoft(page):
    """Microsoft Azure OpenAI 定价页"""
    models = []
    try:
        await page.goto('https://azure.microsoft.com/zh-cn/pricing/details/cognitive-services/openai-service/', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model_name = await cells[0].inner_text()
                input_text = await cells[1].inner_text()
                output_text = await cells[2].inner_text() if len(cells) > 2 else ''
                input_price = extract_price(input_text)
                output_price = extract_price(output_text) if output_text else None
                if model_name and input_price is not None:
                    models.append({
                        "vendor": "Microsoft",
                        "model": model_name.strip(),
                        "input": input_price,
                        "output": output_price if output_price else input_price * 4,  # 默认输出价格是输入的4倍
                        "context": "",
                        "note": "Azure OpenAI"
                    })
    except Exception as e:
        print(f"Microsoft Azure 抓取失败: {e}")
    return models

async def fetch_aws(page):
    """AWS Bedrock 定价页"""
    models = []
    try:
        await page.goto('https://aws.amazon.com/bedrock/pricing/', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model_name = await cells[0].inner_text()
                input_text = await cells[1].inner_text()
                output_text = await cells[2].inner_text() if len(cells) > 2 else ''
                input_price = extract_price(input_text)
                output_price = extract_price(output_text) if output_text else None
                if model_name and input_price is not None:
                    models.append({
                        "vendor": "AWS",
                        "model": model_name.strip(),
                        "input": input_price,
                        "output": output_price if output_price else input_price * 5,
                        "context": "",
                        "note": "Bedrock"
                    })
    except Exception as e:
        print(f"AWS Bedrock 抓取失败: {e}")
    return models

async def fetch_cohere(page):
    """Cohere 定价页"""
    models = []
    try:
        await page.goto('https://cohere.com/pricing', wait_until='domcontentloaded', timeout=30000)
        elements = await page.query_selector_all('.pricing-table')
        for el in elements:
            text = await el.inner_text()
            match = re.search(r'(Command [Rr][+]?).*?\$?([\d.]+).*?\/.*?token', text, re.DOTALL)
            if match:
                models.append({
                    "vendor": "Cohere",
                    "model": match.group(1).strip(),
                    "input": float(match.group(2)),
                    "output": float(match.group(2)) * 3,
                    "context": "",
                    "note": ""
                })
    except Exception as e:
        print(f"Cohere 抓取失败: {e}")
    return models

async def fetch_mistral(page):
    """Mistral AI 定价页"""
    models = []
    try:
        await page.goto('https://mistral.ai/pricing/', wait_until='domcontentloaded', timeout=30000)
        rows = await page.query_selector_all('table tbody tr')
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                model_name = await cells[0].inner_text()
                input_text = await cells[1].inner_text()
                output_text = await cells[2].inner_text() if len(cells) > 2 else ''
                input_price = extract_price(input_text)
                output_price = extract_price(output_text) if output_text else None
                if model_name and input_price is not None:
                    models.append({
                        "vendor": "Mistral",
                        "model": model_name.strip(),
                        "input": input_price,
                        "output": output_price if output_price else input_price * 3,
                        "context": "",
                        "note": ""
                    })
    except Exception as e:
        print(f"Mistral AI 抓取失败: {e}")
    return models

def extract_price(text):
    """从文本中提取第一个美元价格，例如 '$0.15 / 1M tokens'"""
    match = re.search(r'\$?([\d.]+)\s*/\s*(?:1M|million)?', text.replace(',', ''))
    if match:
        return float(match.group(1))
    match_cny = re.search(r'¥\s*([\d.]+)', text)
    if match_cny:
        return float(match_cny.group(1))
    return None

def save_daily_snapshot(data):
    """保存每日快照到 history/ 文件夹"""
    today = date.today().strftime('%Y-%m-%d')
    snapshot_file = os.path.join(HISTORY_DIR, f'{today}.json')
    
    # 如果当天已有快照，先读取并合并
    if os.path.exists(snapshot_file):
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        # 合并新数据（新数据优先）
        existing_models = {f"{m['vendor']}::{m['model']}": m for m in existing.get('models', [])}
        new_models = {f"{m['vendor']}::{m['model']}": m for m in data.get('models', [])}
        existing_models.update(new_models)
        data['models'] = list(existing_models.values())
    
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ 每日快照已保存到 history/{today}.json")

async def main():
    today = date.today().strftime('%Y-%m-%d')
    existing = {"models": [], "last_updated": today}
    
    # 读取现有数据作为后备
    if os.path.exists(PRICING_FILE):
        with open(PRICING_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    proxy_server = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    proxy_config = None
    if proxy_server:
        proxy_config = {"server": proxy_server}
        print(f"使用代理: {proxy_server}")

    all_models = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            proxy=proxy_config
        )
        page = await context.new_page()

        # 并发执行抓取任务
        tasks = [
            safe_fetch("OpenAI", fetch_openai, page),
            safe_fetch("Anthropic", fetch_anthropic, page),
            safe_fetch("Google", fetch_google, page),
            safe_fetch("DeepSeek", fetch_deepseek, page),
            safe_fetch("Microsoft Azure", fetch_microsoft, page),
            safe_fetch("AWS Bedrock", fetch_aws, page),
            safe_fetch("Cohere", fetch_cohere, page),
            safe_fetch("Mistral", fetch_mistral, page),
        ]
        results = await asyncio.gather(*tasks)

        # 处理抓取结果
        for vendor_name, models_list in results:
            if models_list:
                print(f"✓ {vendor_name}: 获取到 {len(models_list)} 个模型")
                all_models.extend(models_list)
            else:
                print(f"✗ {vendor_name}: 未获取到数据")

        await browser.close()

    # 如果抓取到新数据，更新现有数据
    if all_models:
        seen = set()
        final = []
        for m in all_models:
            key = (m['vendor'], m['model'])
            if key not in seen:
                seen.add(key)
                final.append(m)
        existing['models'] = final
        print(f"成功抓取 {len(final)} 个模型")
    else:
        print("抓取未获得新模型，保留旧数据。")

    # 更新最后更新时间
    existing['last_updated'] = today

    # 保存主定价文件
    with open(PRICING_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"✓ 定价数据已保存到 pricing.json")

    # 保存每日快照
    save_daily_snapshot(existing)

    # 自动构建历史数据
    print("\n正在自动构建历史数据...")
    build_history()

def build_history():
    """调用 build_history.py 的逻辑来生成 history.json"""
    from collections import defaultdict
    from datetime import datetime, timedelta
    
    HISTORY_DIR_ = os.path.join(os.path.dirname(__file__), '..', 'history')
    OUTPUT_FILE_ = os.path.join(os.path.dirname(__file__), '..', 'history.json')
    
    def load_all_snapshots():
        snaps = []
        if not os.path.exists(HISTORY_DIR_):
            return snaps
        for fname in sorted(os.listdir(HISTORY_DIR_)):
            if not fname.endswith('.json'):
                continue
            date_str = fname.replace('.json', '')
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue
            with open(os.path.join(HISTORY_DIR_, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
                models = data.get('models', [])
                snaps.append((date_str, models))
        return snaps
    
    snaps = load_all_snapshots()
    if not snaps:
        print("没有历史快照，跳过生成 history.json")
        return
    
    timeline = defaultdict(dict)
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
        
        first_entry = date_prices[sorted_dates[0]]
        context = first_entry.get("context", "")
        note = first_entry.get("note", "")
        
        input_ohlc = []
        output_ohlc = []
        last_input = None
        last_output = None
        
        start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in date_prices:
                p = date_prices[date_str]
                inp = p["input"]
                out = p["output"]
                last_input = inp
                last_output = out
            else:
                inp = last_input
                out = last_output
            
            if inp is not None:
                input_ohlc.append([date_str, inp, inp, inp, inp])
            if out is not None:
                output_ohlc.append([date_str, out, out, out, out])
            
            current_date += timedelta(days=1)
        
        result_models[key] = {
            "vendor": vendor,
            "model": model,
            "context": context,
            "note": note,
            "input_ohlc": input_ohlc,
            "output_ohlc": output_ohlc
        }
    
    history_data = {"models": result_models, "last_updated": date.today().strftime('%Y-%m-%d')}
    with open(OUTPUT_FILE_, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)
    print(f"✓ history.json 已生成，包含 {len(result_models)} 个模型")

if __name__ == '__main__':
    asyncio.run(main())