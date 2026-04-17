import json
import os
from datetime import datetime
from pathlib import Path

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


def format_time_range(start_time: datetime, end_time: datetime) -> str:
    """根据起止时间自动判断是否跨天，生成时间范围字符串。"""
    if start_time.date() == end_time.date():
        return f"{start_time.strftime('%Y.%m.%d %H')} - {end_time.strftime('%H')}"
    else:
        return f"{start_time.strftime('%Y.%m.%d %H')} - {end_time.strftime('%Y.%m.%d %H')}"


CATEGORY_EMOJI_MAP = {
    "大厂&融资": "🏢",
    "模型&论文": "🧠",
    "产品&开源": "🛠️",
    "编程&架构": "💻",
    "增长&自媒体": "📈",
    "独立开发": "🚀",
    "观点&争议": "💬",
}


def build_ai_daily_card(
    categories: list[dict],
    platform: str = "AI Daily",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    """
    动态构建 AI Daily 卡片。

    categories 格式示例：
    [
        {
            "name": "大厂&融资",
            "summary": "科技巨头新一轮融资潮涌动，AI 赛道估值持续走高",
            "items": [
                {
                    "title": "某 AI 独角兽完成 10 亿美元融资",
                    "summary": "估值突破 300 亿美元",
                    "source": "Bloomberg",
                    "url": "https://bloomberg.com"
                },
            ]
        },
    ]

    platform: 平台名，如 "X"、"即刻"
    start_time: 抓取开始时间
    end_time: 抓取结束时间

    emoji 会根据主题名从 CATEGORY_EMOJI_MAP 中自动映射，无需上游传入。
    """
    if start_time is None:
        start_time = datetime.now()
    if end_time is None:
        end_time = datetime.now()

    time_range = format_time_range(start_time, end_time)
    total_items = sum(len(c.get("items", [])) for c in categories)

    card = {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{platform} | {total_items} 条 | {time_range}",
                },
                "subtitle": {"tag": "plain_text", "content": ""},
                "template": "orange",
                "padding": "12px 16px 12px 16px",
            },
            "body": {
                "direction": "vertical",
                "elements": [],
            },
        },
    }

    for idx, cat in enumerate(categories):
        items = cat.get("items", [])
        if not items:
            continue

        lines = "\n".join([
            f"- **{item['title']}**：{item['summary']} [{item['source']}]({item['url']})"
            for item in items
        ])

        emoji = CATEGORY_EMOJI_MAP.get(cat["name"], "")
        panel = {
            "tag": "collapsible_panel",
            "expanded": idx == 0,
            "header": {
                "title": {
                    "tag": "markdown",
                    "content": f"**{emoji}{cat['name']}：{cat['summary']}**",
                },
                "icon": {
                    "tag": "standard_icon",
                    "token": "down-small-ccm_outlined",
                },
                "icon_position": "right",
                "icon_expanded_angle": -180,
            },
            "vertical_spacing": "8px",
            "padding": "8px 12px",
            "elements": [
                {"tag": "markdown", "content": lines}
            ],
        }
        card["card"]["body"]["elements"].append(panel)

    return card


def main():
    # 示例数据：只有 4 个主题，每个主题子信息数不同（注意：不再包含 emoji）
    sample_categories = [
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

    # 示例 1：X 平台，1 小时抓取间隔（同一天）
    payload_x = build_ai_daily_card(
        sample_categories,
        platform="X",
        start_time=datetime(2026, 4, 17, 16, 0),
        end_time=datetime(2026, 4, 17, 17, 0),
    )
    _send_preview(payload_x, "preview_ai_daily_x.json")

    # 示例 2：即刻平台，2 小时抓取间隔（同一天）
    payload_jike = build_ai_daily_card(
        sample_categories[:3],  # 只有 3 个主题，5 条信息
        platform="即刻",
        start_time=datetime(2026, 4, 17, 14, 0),
        end_time=datetime(2026, 4, 17, 16, 0),
    )
    _send_preview(payload_jike, "preview_ai_daily_jike.json")

    # 示例 3：跨天抓取场景
    payload_cross_day = build_ai_daily_card(
        sample_categories[:2],
        platform="即刻",
        start_time=datetime(2026, 4, 17, 23, 0),
        end_time=datetime(2026, 4, 18, 1, 0),
    )
    _send_preview(payload_cross_day, "preview_ai_daily_cross.json")

    # 示例 4：HackerNews，一天抓一次
    payload_hn = build_ai_daily_card(
        sample_categories[1:3],  # 2 个主题
        platform="HackerNews",
        start_time=datetime(2026, 4, 17, 0, 0),
        end_time=datetime(2026, 4, 18, 0, 0),
    )
    _send_preview(payload_hn, "preview_ai_daily_hn.json")

    # 这里默认发送 HackerNews 示例卡片做演示
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


def _send_preview(payload: dict, filename: str):
    preview_path = Path(__file__).parent / filename
    preview_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Preview saved to: {preview_path}")


if __name__ == "__main__":
    main()
