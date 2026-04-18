"""飞书 Webhook 传输层。

负责实际发送 payload 到飞书 webhook，保持纯 IO 函数，不处理业务构建。
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
