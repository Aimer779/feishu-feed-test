"""飞书 Webhook 传输层。

负责实际发送 payload 到飞书 webhook，保持纯 IO 函数，不处理业务构建。
"""

import time

import requests

from config import get_env
from logger import get_logger

WEBHOOK_URL = get_env("FEISHU_WEBHOOK_URL", "")

log = get_logger("sender")


def send_card(webhook_url: str, payload: dict) -> dict:
    log.info("Sending card to Feishu webhook")
    t0 = time.time()
    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    log.info("Card sent, status={}, elapsed={:.1f}s", response.status_code, time.time() - t0)
    return result
