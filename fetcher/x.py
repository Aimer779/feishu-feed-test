"""X (Twitter) 抓取,基于 Apify apidojo/tweet-scraper。"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

_ACTOR_ID = "apidojo/tweet-scraper"
_PLATFORM = "X"

# 核心官方账号（精简到 10 个，作为搜索的兜底补充）
_CORE_HANDLES = [
    "karpathy",       
    "AnthropicAI",    
    "claudeai",
    "OpenAI",         
    "dotey", 
    "sama",          
    "AndrewYng",      
    "OpenAIDevs",     
    "ylecun",        
    "GoogleDeepMind", 
    "cursor_ai",   
    "demishassabis",  
]

# 默认搜索词（覆盖中英文 AI 核心领域）
_BASE_SEARCH_TERMS = [
    # 英文：模型、公司、技术与创业
    # 不用 lang:en（会漏掉未标语言的英文推），靠 onlyVerifiedUsers + min_favorites 过滤噪声
    "AI OR LLM OR GPT OR OpenAI OR Claude OR Anthropic OR Gemini OR xAI OR Cursor OR \"artificial intelligence\" OR \"machine learning\" OR transformer",
    # 中文：AI 核心与创业
    "大模型 OR 人工智能 OR Claude OR GPT OR OpenAI OR 智谱 OR 通义千问 OR Kimi OR 独立开发 OR AI创业 OR 开源 OR 融资",
]


def fetch_x(
    hours: int = 24,
    since: datetime | None = None,
    until: datetime | None = None,
    min_favorites: int = 5,
    search_min_favorites: int = 25,
    handle_limit: int = 50,
    search_limit: int = 200,
    handles: list[str] | None = None,
    search_terms: list[str] | None = None,
) -> list[dict]:
    """抓取指定 X 账号时间线或关键词搜索近 N 小时内的推文。

    Args:
        hours: 抓取时间窗口（小时），仅在 since/until 未传入时生效。
            默认 24 小时，便于小时级推送时纳入更早但仍值得发送的信息。
        since: 起始时间（UTC），传入则覆盖 hours 计算。
        until: 结束时间（UTC），传入则覆盖 hours 计算。
        handles: 指定账号列表。
            - 不传（None）→ 使用 _CORE_HANDLES
            - 传空列表 [] → 不抓账号时间线
        search_terms: 关键词搜索列表。
            - 不传（None）→ 使用 _BASE_SEARCH_TERMS
            - 传空列表 [] → 不抓搜索
            - 支持 Twitter 高级搜索语法，会自动拼接 since/until 时间窗口
        min_favorites: handles 来源的最低点赞门槛（默认 5，官方号公告初期赞可能不多）。
        search_min_favorites: search_terms 来源的最低点赞门槛（默认 15）。
        handle_limit: handles 模式的最大返回条数。
        search_limit: 每个搜索词的最大返回条数。
    """
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN 未设置")

    now = datetime.now(timezone.utc)
    if since is None:
        since = now - timedelta(hours=hours)
    if until is None:
        until = now

    # 日期级字符串给 start/end 参数做备用兜底
    since_date_str = since.strftime("%Y-%m-%d")
    until_date_str = until.strftime("%Y-%m-%d")

    # 决定 handles 列表
    if handles is not None:
        handles_list = handles
    else:
        handles_list = _CORE_HANDLES

    # 决定搜索词列表
    if search_terms is not None:
        search_terms_list = search_terms
    else:
        search_terms_list = _build_search_queries(_BASE_SEARCH_TERMS, since, until)

    all_articles: list[dict] = []

    # 1. 抓 handles 时间线（不加认证限制，保留所有关注账号）
    if handles_list:
        run_input = {
            "twitterHandles": handles_list,
            "maxItems": handle_limit,
            "sort": "Latest",
        }
        items = _run_actor(token, run_input)
        articles = [_to_article(it) for it in items if _should_keep(it, since, until, min_favorites)]
        all_articles.extend(articles)
        print(f"  [handles] fetched {len(items)} raw, kept {len(articles)} after filter")

    # 2. 抓关键词搜索（认证用户 + 独立配额 + 更高赞门槛）
    if search_terms_list:
        run_input = {
            "searchTerms": search_terms_list,
            "maxItems": search_limit,
            "sort": "Latest",
            "start": since_date_str,
            "end": until_date_str,
            "onlyVerifiedUsers": True,  # 过滤机器人/小号/营销号
        }
        items = _run_actor(token, run_input)
        articles = [_to_article(it) for it in items if _should_keep(it, since, until, search_min_favorites)]
        all_articles.extend(articles)
        print(f"  [search] fetched {len(items)} raw, kept {len(articles)} after filter")

    # 去重 + 截断
    seen_urls = set()
    deduped = []
    for art in all_articles:
        if art["url"] not in seen_urls:
            seen_urls.add(art["url"])
            deduped.append(art)
    return deduped


def _build_search_queries(base_terms: list[str], since: datetime, until: datetime) -> list[str]:
    """将基础搜索词与 since/until 时间窗口拼接为 Twitter 高级搜索语法。"""
    since_str = since.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    until_str = until.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    return [f"{term} since:{since_str} until:{until_str}" for term in base_terms]


def _run_actor(token: str, run_input: dict) -> list[dict]:
    """运行 Apify Actor 并返回原始 items 列表。"""
    client = ApifyClient(token)
    run = client.actor(_ACTOR_ID).call(run_input=run_input)
    return client.dataset(run["defaultDatasetId"]).list_items().items


def _should_keep(it: dict, since: datetime, until: datetime, min_favorites: int) -> bool:
    """判断单条推文是否满足时间和点赞门槛。"""
    if (it.get("likeCount") or 0) < min_favorites:
        return False
    created = it.get("createdAt")
    if not created:
        return False
    try:
        dt = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
        return since <= dt <= until
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
    print(f"\nTotal fetched {len(articles)} tweets\n")
    for art in articles[:5]:
        print(json.dumps(art, ensure_ascii=False, indent=2))
        print()
