"""X (Twitter) 抓取,基于 Apify apidojo/tweet-scraper。"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

_ACTOR_ID = "apidojo/tweet-scraper"
_PLATFORM = "X"

# 官方账号 + 技术大牛（发推频率相对较低，但内容权威）
_OFFICIAL_HANDLES = [
    "sama",           # OpenAI CEO
    "karpathy",       # 前 Tesla AI Director
    "AndrewYng",      # 吴恩达
    "ylecun",         # Meta Chief AI Scientist
    "lexfridman",     # MIT 研究员 / 播客
    "demishassabis",  # DeepMind CEO
    "AnthropicAI",    # Anthropic 官方
    "claudeai",       # Claude 官方
    "OpenAI",         # OpenAI 官方
    "OpenAIDevs",     # OpenAI 开发者官方
    "xai",            # xAI 官方
    "grok",           # Grok 官方
    "cursor_ai",      # Cursor 官方
    "Kimi_Moonshot",  # Kimi 官方
    "MiniMax__AI",    # MiniMax 官方
    "Alibaba_Qwen",   # 通义千问官方
    "googleaidevs",   # Google AI 开发者官方
    "GoogleAIStudio", # Google AI Studio 官方
    "GoogleDeepMind", # Google DeepMind 官方
    "OfficialLoganK", # OpenAI 开发者关系
    "bcherny",        # 工程师 / 投资人
]

# 博主 / 自媒体 / 中文 AI 圈（发推频率高，覆盖面广）
_BLOGGER_HANDLES = [
    "HiTw93",         # 程序员 / 产品博主
    "thsottiaux",     # AI 博主
    "dotey",          # 中文 AI 博主
    "op7418",         # 中文 AI 博主
    "vista8",         # 中文技术博主
    "turingou",       # 中文开发者
    "oran_ge",        # 中文 AI 博主
    "lifesinger",     # 前端大佬 / 博主
    "mranti",         # 中文科技评论
    "hylarucoder",    # 中文开发者
    "Pluvio9yte",     # 中文 AI 博主
    "Jimmy_JingLv",   # 中文 AI 博主
    "blackanger",     # 中文开发者
    "wquguru",        # 中文技术博主
    "yetone",         # 中文开发者 / AI 博主
    "Yangyixxxx",     # 中文 AI 博主
    "dongxi_nlp",     # NLP 博主
    "xiaohu",         # 中文 AI 博主
    "RookieRicardoR", # 中文开发者
    "9hills",         # 中文技术博主
    "onevcat",        # iOS 大佬 / 博主
    "lxfater",        # 中文 AI 博主
    "real_kai42",     # 中文开发者
    "waylybaye",      # 中文开发者
]

_DEFAULT_HANDLES = _OFFICIAL_HANDLES + _BLOGGER_HANDLES


def fetch_x(
    hours: int = 48,
    min_favorites: int = 0,
    search_min_favorites: int = 20,
    limit: int = 100,
    handles: list[str] | None = None,
    search_terms: list[str] | None = None,
    handle_type: str = "all",
) -> list[dict]:
    """抓取指定 X 账号或关键词搜索近 N 小时内的推文。

    Args:
        handles: 指定账号列表（优先级最高，传了就用这个）。
            - 不传（None）→ 使用 handle_type 对应的默认列表
            - 传空列表 [] → 不抓账号时间线
        search_terms: 关键词搜索列表。
            - 支持 Twitter 高级搜索语法，如 "Claude min_faves:50"
            - 搜索时自动启用 onlyVerifiedUsers，过滤机器人/小号
        min_favorites: handles 来源的最低点赞门槛。
        search_min_favorites: search_terms 来源的最低点赞门槛（默认更高）。
        handle_type: 默认列表类型，仅当 handles=None 时生效。
            - "official" → 官方 + 技术大牛
            - "blogger" → 博主 / 自媒体
            - "all" → 两者合并（默认）
    """
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN 未设置")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_str = since.strftime("%Y-%m-%d")

    # 决定 handles 列表
    if handles is not None:
        handles_list = handles
    elif handle_type == "official":
        handles_list = _OFFICIAL_HANDLES
    elif handle_type == "blogger":
        handles_list = _BLOGGER_HANDLES
    else:
        handles_list = _DEFAULT_HANDLES

    all_articles: list[dict] = []

    # 1. 抓 handles 时间线（不加认证限制，保留所有关注账号）
    if handles_list:
        run_input = {
            "twitterHandles": handles_list,
            "maxItems": limit,
            "sort": "Latest",
            "start": since_str,
        }
        items = _run_actor(token, run_input)
        articles = [_to_article(it) for it in items if _should_keep(it, since, min_favorites)]
        all_articles.extend(articles)

    # 2. 抓关键词搜索（认证用户 + 独立配额 + 更高赞门槛）
    if search_terms:
        run_input = {
            "searchTerms": search_terms,
            "maxItems": limit,
            "sort": "Latest",
            "start": since_str,
            "onlyVerifiedUsers": True,  # 过滤机器人/小号/营销号
        }
        items = _run_actor(token, run_input)
        articles = [_to_article(it) for it in items if _should_keep(it, since, search_min_favorites)]
        all_articles.extend(articles)

    # 去重 + 截断
    seen_urls = set()
    deduped = []
    for art in all_articles:
        if art["url"] not in seen_urls:
            seen_urls.add(art["url"])
            deduped.append(art)
    return deduped[:limit]


def _run_actor(token: str, run_input: dict) -> list[dict]:
    """运行 Apify Actor 并返回原始 items 列表。"""
    client = ApifyClient(token)
    run = client.actor(_ACTOR_ID).call(run_input=run_input)
    return client.dataset(run["defaultDatasetId"]).list_items().items


def _should_keep(it: dict, since: datetime, min_favorites: int) -> bool:
    if (it.get("likeCount") or 0) < min_favorites:
        return False
    created = it.get("createdAt")
    if not created:
        return False
    try:
        dt = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
        return dt >= since
    except ValueError:
        return False


def _to_article(it: dict[str, Any]) -> dict:
    text = (it.get("text") or "").strip().replace("\n", " ")
    author = (it.get("author") or {}).get("userName", "")
    return {
        "platform": _PLATFORM,
        "title": text[:60] + ("..." if len(text) > 60 else ""),
        "url": it.get("url", ""),
        "content": text,
        "author": f"@{author}" if author else "",
        "published_at": it.get("createdAt", ""),
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    articles = fetch_x()
    print(f"Fetched {len(articles)} tweets\n")
    for art in articles[:3]:
        print(json.dumps(art, ensure_ascii=False, indent=2))
