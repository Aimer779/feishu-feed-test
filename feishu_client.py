"""飞书 Webhook 传输层。

负责加载 FEISHU_WEBHOOK_URL 与实际发送 payload，card_builder 保持纯函数、不依赖 IO。
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")


def send_card(webhook_url: str, payload: dict) -> dict:
    """发送卡片消息到飞书 webhook。"""
    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
