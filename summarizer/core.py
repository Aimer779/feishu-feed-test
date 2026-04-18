import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from .fixtures import mock_articles
from .prompt import SYSTEM_PROMPT
from .schema import RESPONSE_SCHEMA

load_dotenv()

_CONTENT_TRUNCATE = 500


def _render_user_prompt(articles: list[dict], platform: str) -> str:
    lines = [f"平台: {platform}", f"文章数: {len(articles)}", "", "以下是本批原始文章(JSON Lines):"]
    for art in articles:
        content = (art.get("content") or "").strip().replace("\n", " ")
        if len(content) > _CONTENT_TRUNCATE:
            content = content[:_CONTENT_TRUNCATE] + "..."
        compact = {
            "title": art.get("title", ""),
            "url": art.get("url", ""),
            "author": art.get("author", ""),
            "published_at": art.get("published_at", ""),
            "content": content,
        }
        lines.append(json.dumps(compact, ensure_ascii=False))
    return "\n".join(lines)


def summarize(
    articles: list[dict],
    platform: str,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """把一批原始文章压缩成 categories 结构。

    articles: fetcher.py 输出的原始文章列表。
    platform: 平台名(如 "X" / "即刻" / "HackerNews"),会注入到 prompt 与 source 提示中。
    model / base_url / api_key: 不传则从 .env 读 LLM_MODEL / LLM_BASE_URL / LLM_API_KEY。
    返回值可直接作为 card_builder.build_ai_daily_card 的 categories 参数。
    """
    if not articles:
        return []

    client = OpenAI(
        api_key=api_key or os.getenv("LLM_API_KEY"),
        base_url=base_url or os.getenv("LLM_BASE_URL"),
    )
    resolved_model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=resolved_model,
        response_format={"type": "json_schema", "json_schema": RESPONSE_SCHEMA},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _render_user_prompt(articles, platform)},
        ],
    )

    payload = json.loads(resp.choices[0].message.content)
    categories = payload.get("categories", [])
    return [c for c in categories if c.get("items")]
