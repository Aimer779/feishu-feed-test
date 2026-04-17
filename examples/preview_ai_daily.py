"""AI Daily 卡片预览/调试入口。

运行后会在项目根目录写出多份 preview_ai_daily_*.json，并向 FEISHU_WEBHOOK_URL 发送其中一份示例。
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from card_builder import build_ai_daily_card
from feishu_client import WEBHOOK_URL, send_card


SAMPLE_CATEGORIES = [
    {
        "name": "大厂&融资",
        "summary": "科技巨头新一轮融资潮涌动，AI 赛道估值持续走高",
        "items": [
            {
                "title": "某 AI 独角兽完成 10 亿美元融资",
                "summary": "估值突破 300 亿美元",
                "source": "Bloomberg",
                "url": "https://bloomberg.com",
            },
            {
                "title": "微软追加 OpenAI 投资",
                "summary": "深化云服务与模型训练合作",
                "source": "Reuters",
                "url": "https://reuters.com",
            },
        ],
    },
    {
        "name": "模型&论文",
        "summary": "前沿研究成果密集发布，多模态与推理能力成焦点",
        "items": [
            {
                "title": "新架构显著提升长文本推理效率",
                "summary": "上下文长度扩展至 400 万 token",
                "source": "arXiv",
                "url": "https://arxiv.org",
            },
        ],
    },
    {
        "name": "产品&开源",
        "summary": "多款 AI 工具正式上线，开源社区迎来重磅更新",
        "items": [
            {
                "title": "新一代代码编辑器发布 AI 原生版本",
                "summary": "支持端到端自动重构",
                "source": "Product Hunt",
                "url": "https://producthunt.com",
            },
            {
                "title": "Meta 开源最新多模态大模型",
                "summary": "免费商用授权引发社区热议",
                "source": "GitHub",
                "url": "https://github.com",
            },
            {
                "title": "Stable Diffusion 4 发布预览版",
                "summary": "生成速度提升 3 倍，画质更稳定",
                "source": "Stability AI",
                "url": "https://stability.ai",
            },
        ],
    },
    {
        "name": "独立开发",
        "summary": "一人公司模式兴起，AI 工具链助力快速变现",
        "items": [
            {
                "title": "AI 浏览器插件月收破万美元",
                "summary": "开发者仅用时两周完成 MVP",
                "source": "Indie Hackers",
                "url": "https://indiehackers.com",
            },
        ],
    },
]


def _save_preview(payload: dict, filename: str):
    preview_path = Path(__file__).resolve().parent.parent / filename
    preview_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Preview saved to: {preview_path}")


def main():
    payload_x = build_ai_daily_card(
        SAMPLE_CATEGORIES,
        platform="X",
        start_time=datetime(2026, 4, 17, 16, 0),
        end_time=datetime(2026, 4, 17, 17, 0),
    )
    _save_preview(payload_x, "preview_ai_daily_x.json")

    payload_jike = build_ai_daily_card(
        SAMPLE_CATEGORIES[:3],
        platform="即刻",
        start_time=datetime(2026, 4, 17, 14, 0),
        end_time=datetime(2026, 4, 17, 16, 0),
    )
    _save_preview(payload_jike, "preview_ai_daily_jike.json")

    payload_cross_day = build_ai_daily_card(
        SAMPLE_CATEGORIES[:2],
        platform="即刻",
        start_time=datetime(2026, 4, 17, 23, 0),
        end_time=datetime(2026, 4, 18, 1, 0),
    )
    _save_preview(payload_cross_day, "preview_ai_daily_cross.json")

    payload_hn = build_ai_daily_card(
        SAMPLE_CATEGORIES[1:3],
        platform="HackerNews",
        start_time=datetime(2026, 4, 17, 0, 0),
        end_time=datetime(2026, 4, 18, 0, 0),
    )
    _save_preview(payload_hn, "preview_ai_daily_hn.json")

    payload = payload_hn

    if not WEBHOOK_URL:
        print("\nError: FEISHU_WEBHOOK_URL not configured.")
        return

    print(f"\nSending card to: {WEBHOOK_URL}")
    try:
        result = send_card(WEBHOOK_URL, payload)
        print(f"Success: {result}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
