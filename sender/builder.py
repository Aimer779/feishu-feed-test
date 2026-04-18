"""动态构建 AI Daily 飞书卡片（纯函数，不触发 IO）。"""

from datetime import datetime

from categories import CATEGORY_EMOJI_MAP, PLATFORM_COLOR_MAP


def format_time_range(start_time: datetime, end_time: datetime) -> str:
    """根据起止时间自动判断是否跨天，生成时间范围字符串。"""
    if start_time.date() == end_time.date():
        return f"{start_time.strftime('%Y.%m.%d %H')} - {end_time.strftime('%H')}"
    else:
        return f"{start_time.strftime('%Y.%m.%d %H')} - {end_time.strftime('%Y.%m.%d %H')}"


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
                    "summary": "据 [Bloomberg](https://bloomberg.com) 报道，估值突破 300 亿美元。",
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
                "template": PLATFORM_COLOR_MAP.get(platform, "orange"),
                "padding": "12px 16px 12px 16px",
            },
            "body": {
                "direction": "vertical",
                "vertical_spacing": "12px",
                "padding": "8px 12px 12px 12px",
                "elements": [],
            },
        },
    }

    for idx, cat in enumerate(categories):
        items = cat.get("items", [])
        if not items:
            continue

        lines = "\n".join([
            f"- **{item['title']}**：{item['summary']}"
            for item in items
        ])

        emoji = CATEGORY_EMOJI_MAP.get(cat["name"], "")
        panel = {
            "tag": "collapsible_panel",
            "expanded": False,
            "header": {
                "title": {
                    "tag": "markdown",
                    "content": f"**{emoji} {cat['name'].replace('&', ' & ')}：{cat['summary'].rstrip('。')}**",
                },
                "icon": {
                    "tag": "standard_icon",
                    "token": "down-round_outlined",
                },
                "icon_position": "right",
                "icon_expanded_angle": -180,
            },
            "vertical_spacing": "10px",
            "padding": "12px 16px",
            "background_color": "grey-50",
            "elements": [
                {"tag": "markdown", "content": lines}
            ],
        }
        card["card"]["body"]["elements"].append(panel)

    return card
