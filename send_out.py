import json
import os
from datetime import datetime
from pathlib import Path

from card_builder import build_ai_daily_card
from feishu_client import send_card

# 加载 out.json
data = json.loads(Path("out.json").read_text(encoding="utf-8"))

# 构建并发送卡片
payload = build_ai_daily_card(
    categories=data,
    platform="AI Daily",
    start_time=datetime(2026, 4, 17, 0, 0),
    end_time=datetime(2026, 4, 18, 0, 0),
)

webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "")
if not webhook_url:
    raise ValueError("FEISHU_WEBHOOK_URL not configured")

result = send_card(webhook_url, payload)
print(f"Success: {result}")
