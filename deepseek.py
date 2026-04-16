# -*- coding: utf-8 -*-
"""DeepSeek模块"""
import os
import json
import urllib.request
import urllib.error
import re


def get_env(key, default=None):
    return os.environ.get(key, default)


DEEPSEEK_API_KEY = get_env('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = get_env('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = get_env('DEEPSEEK_MODEL', 'deepseek-chat')


def extract_info(raw_text):
    """调用DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API Key未配置")

    # 确保 raw_text 是字符串
    if isinstance(raw_text, bytes):
        raw_text = raw_text.decode('utf-8', errors='replace')
    else:
        raw_text = str(raw_text)

    prompt = f"""
你是一个专业的财务助手。以下是从报销截图中识别出的原始文字：
{raw_text}

请从中提取关键信息，严格以 JSON 格式返回：
- "date": 支付日期 (YYYY-MM-DD)
- "amount": 金额 (数字)
- "merchant": 收款方/商户全称
- "item": 商品描述/事由
- "order_id": 交易单号
只返回JSON，不要解释。
"""

    url = f"{DEEPSEEK_BASE_URL}/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise Exception(f"DeepSeek失败: {e.code}")

    content = result['choices'][0]['message']['content']
    json_str = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(json_str)
    except:
        match = re.search(r'\{[^{}]*\}', json_str, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise Exception("DeepSeek返回格式错误")
