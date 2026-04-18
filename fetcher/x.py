"""X (Twitter) 抓取,基于 Apify apidojo/tweet-scraper。"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

_ACTOR_ID = "apidojo/tweet-scraper"
_PLATFORM = "X"

_DEFAULT_HANDLES = [
    "sama", "karpathy", "AndrewYng", "OfficialLoganK",
    "ylecun", "AnthropicAI", "OpenAI", "demishassabis",
    "miramurati", "polynoamial", "_philschmid", "drjimfan",
    "simonw", "swyx", "tszzl",
]


def fetch_x(
    hours: int = 1,
    min_favorites: int = 20,
    limit: int = 50,
    handles: list[str] | None = None,
) -> list[dict]:
    """抓取指定 X 账号近 N 小时内点赞 >= min_favorites 的推文。"""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN 未设置")
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    run_input = {
        "twitterHandles": handles or _DEFAULT_HANDLES,
        "maxItems": limit,
        "sort": "Latest",
        "start": since.strftime("%Y-%m-%d"),
        "tweetLanguage": "en",
    }
    client = ApifyClient(token)
    run = client.actor(_ACTOR_ID).call(run_input=run_input)
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    articles = [_to_article(it) for it in items if _should_keep(it, since, min_favorites)]
    return articles[:limit]


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
