"""HackerNews 抓取,基于 Algolia HN Search API(一次请求支持时间窗+分数过滤)。"""

import time
from typing import Any

import requests

_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
_HN_ITEM_URL = "https://news.ycombinator.com/item?id={id}"
_PLATFORM = "HackerNews"


def fetch_hn(
    hours: int = 24,
    min_score: int = 50,
    limit: int = 30,
) -> list[dict]:
    """抓取 HackerNews 近 N 小时内分数 >= min_score 的热门 story。

    返回 summarizer.summarize() 期望的原始文章格式:
    [{platform, title, url, content, author, published_at}]。
    """
    since = int(time.time()) - hours * 3600
    params = {
        "tags": "story",
        "numericFilters": f"points>={min_score},created_at_i>{since}",
        "hitsPerPage": limit,
    }
    resp = requests.get(_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    return [_to_article(h) for h in hits]


def _to_article(hit: dict[str, Any]) -> dict:
    url = hit.get("url") or _HN_ITEM_URL.format(id=hit["objectID"])
    title = hit.get("title", "")
    return {
        "platform": _PLATFORM,
        "title": title,
        "url": url,
        "content": title,
        "author": hit.get("author", ""),
        "published_at": hit.get("created_at", ""),
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    articles = fetch_hn()
    print(f"Fetched {len(articles)} articles\n")
    for art in articles[:3]:
        print(json.dumps(art, ensure_ascii=False, indent=2))
