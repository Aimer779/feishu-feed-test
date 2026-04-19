import json
import time

from openai import OpenAI

from config import get_env
from contracts import CategoryGroup, RawArticle, validate_category_groups, validate_raw_articles
from logger import get_logger

from .prompt import SYSTEM_PROMPT
from .schema import RESPONSE_SCHEMA

_CONTENT_TRUNCATE = 500

log = get_logger("summarizer")


def _render_user_prompt(articles: list[RawArticle], platform: str) -> str:
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
    articles: list[RawArticle],
    platform: str,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> list[CategoryGroup]:
    """把一批原始文章压缩成 categories 结构。

    articles: fetcher/ 各模块输出的原始文章列表。
    platform: 平台名(如 "X" / "Reddit" / "HackerNews"),会注入到 prompt 与 source 提示中。
    model / base_url / api_key: 不传则从 .env 读 LLM_MODEL / LLM_BASE_URL / LLM_API_KEY。
    返回值可直接作为 card_builder.build_ai_daily_card 的 categories 参数。
    """
    if not articles:
        return []
    articles = validate_raw_articles(articles, source="summarize input")

    client = OpenAI(
        api_key=api_key or get_env("LLM_API_KEY"),
        base_url=base_url or get_env("LLM_BASE_URL"),
    )
    resolved_model = model or get_env("LLM_MODEL", "gpt-4o-mini")

    log.info("LLM call start: model={}, articles={}", resolved_model, len(articles))
    t0 = time.time()
    resp = client.chat.completions.create(
        model=resolved_model,
        response_format={"type": "json_schema", "json_schema": RESPONSE_SCHEMA},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _render_user_prompt(articles, platform)},
        ],
    )
    elapsed = time.time() - t0

    usage = resp.usage
    if usage:
        log.info(
            "LLM call completed in {:.1f}s, tokens: prompt={}, completion={}, total={}",
            elapsed, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    else:
        log.info("LLM call completed in {:.1f}s", elapsed)

    payload = json.loads(resp.choices[0].message.content)
    categories = validate_category_groups(
        payload.get("categories", []),
        source="summarize output",
    )
    return [category for category in categories if category["items"]]
