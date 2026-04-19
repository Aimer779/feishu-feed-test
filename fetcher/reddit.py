"""Reddit 抓取,基于 Apify trudax/reddit-scraper。"""

from datetime import datetime, timedelta, timezone
from typing import Any

from apify_client import ApifyClient

from config import get_env
from contracts import RawArticle, validate_raw_articles
from logger import get_logger

log = get_logger("fetcher.reddit")

_ACTOR_ID = "trudax/reddit-scraper-lite"
_PLATFORM = "Reddit"

_DEFAULT_SUBREDDITS = [
    "MachineLearning", "LocalLLaMA", "OpenAI", "ClaudeAI",
    "ChatGPT", "singularity", "artificial", "LocalLLM",
]


def fetch_reddit(
    hours: int = 2,
    min_score: int = 30,
    limit: int = 40,
    subreddits: list[str] | None = None,
) -> list[RawArticle]:
    """抓取默认/指定 subreddit 近 N 小时内 score >= min_score 的帖子。"""
    token = get_env("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN 未设置")
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    subs = subreddits or _DEFAULT_SUBREDDITS
    run_input = {
        "startUrls": [{"url": f"https://www.reddit.com/r/{s}/"} for s in subs],
        "maxItems": limit * 2,
        "maxPostCount": limit * 2,
        "maxComments": 0,
        "sort": "new",
        "postDateLimit": since.strftime("%Y-%m-%dT%H:%M:%S"),
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }
    client = ApifyClient(token)
    run = client.actor(_ACTOR_ID).call(run_input=run_input)
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    articles = [_to_article(it) for it in items if _should_keep(it, min_score)]
    articles.sort(key=lambda a: a["published_at"], reverse=True)
    return validate_raw_articles(articles[:limit], source="fetch_reddit output")


def _should_keep(it: dict, min_score: int) -> bool:
    if it.get("dataType") != "post":
        return False
    return (it.get("upVotes") or it.get("score") or 0) >= min_score


def _to_article(it: dict[str, Any]) -> RawArticle:
    body = (it.get("body") or it.get("selftext") or "").strip().replace("\n", " ")
    title = (it.get("title") or "").strip()
    user = it.get("username") or it.get("author") or ""
    return RawArticle(
        platform=_PLATFORM,
        title=title,
        url=it.get("url", ""),
        content=body or title,
        author=f"u/{user}" if user else "",
        published_at=it.get("createdAt", ""),
    )


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    articles = fetch_reddit()
    print(f"Fetched {len(articles)} posts\n")
    for art in articles[:3]:
        print(json.dumps(art, ensure_ascii=False, indent=2))
