"""
信息总结器 (Summarizer)
================================================================================

把 fetcher.py 抓到的原始文章列表交给 LLM 做主题分类 + 摘要 + 去重,
输出 card_builder.build_ai_daily_card() 期望的 categories 结构。

后端: OpenAI 兼容 API (base_url 可指向 OpenAI / DeepSeek / 通义 / 本地 vLLM)
结构化输出: chat.completions + response_format=json_schema (strict=True)
调用策略: 单轮整批 —— 一个平台一批数据一次性交给 LLM

================================================================================

【上游】fetcher.py 输出的原始文章列表,每条含:
    platform / title / url / content / author / published_at

【下游】card_builder.build_ai_daily_card 期望的 categories,每条含:
    name (属于 7 个预设主题) / summary / items[title/summary/source/url]

================================================================================
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from card_builder import CATEGORY_EMOJI_MAP

load_dotenv()

CATEGORIES_ENUM = list(CATEGORY_EMOJI_MAP.keys())

_CONTENT_TRUNCATE = 500

SYSTEM_PROMPT = f"""你是一名资讯编辑,负责把一批来自同一平台的原始信息整理成结构化的 AI Daily 卡片数据。

【主题枚举】只允许使用以下 7 个主题之一,name 字段必须严格匹配:
- 大厂&融资:科技巨头动态、投融资、并购、估值、IPO
- 模型&论文:新模型发布、benchmark、论文、训练/推理技术突破
- 产品&开源:AI 产品/工具上线、开源项目、重要版本更新
- 编程&架构:编程语言、框架、系统设计、基础设施、工程实践
- 增长&自媒体:流量打法、内容营销、社媒运营、品牌增长
- 独立开发:一人公司、Indie Hacker、小团队变现、副业
- 观点&争议:行业观点、争议话题、讨论、预测

【分类与合并规则】
1. 每条输入尽量归入最合适的一个主题;如果确实无法归类,直接丢弃。
2. 若多条内容讲同一件事,合并为一个 item;title 用最完整的那条,summary 用分号串联补充要点,url 选最权威的一个。
3. 某主题下若最终没有 item,该主题不得出现在输出的 categories 中。

【字段规则】
1. item.title:简洁的主谓结构,不超过 40 字,不要带表情或 hashtag。
2. item.summary:一句话(20~50 字)点明关键事实或数字,不要与 title 重复。
3. item.source:使用平台名或原站点名(例如 "X"、"即刻"、"HackerNews"、"Bloomberg"、"arXiv"),不要放 URL。
4. item.url:必须是有效的外链。
5. category.summary:对本批该主题的整体趋势做一句话点评(15~40 字),不要是 items 的简单堆砌。

【输出】严格遵循给定的 JSON Schema,不要输出任何额外文本。
主题枚举取值: {CATEGORIES_ENUM}
"""

RESPONSE_SCHEMA: dict[str, Any] = {
    "name": "ai_daily_categories",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["categories"],
        "properties": {
            "categories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "summary", "items"],
                    "properties": {
                        "name": {"type": "string", "enum": CATEGORIES_ENUM},
                        "summary": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["title", "summary", "source", "url"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "source": {"type": "string"},
                                    "url": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            }
        },
    },
}


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


def _mock_articles() -> list[dict]:
    return [
        {
            "platform": "X",
            "title": "某 AI 独角兽完成 10 亿美元 C 轮融资",
            "url": "https://example.com/a1",
            "content": "估值突破 300 亿美元,领投方为红杉与软银,资金将用于下一代基础模型训练。",
            "author": "@techcrunch",
            "published_at": "2026-04-17T15:30:00",
        },
        {
            "platform": "X",
            "title": "红杉、软银领投,AI 独角兽估值达 300 亿美元",
            "url": "https://example.com/a2",
            "content": "同一起融资的另一家媒体报道,细节相同。",
            "author": "@bloomberg",
            "published_at": "2026-04-17T15:45:00",
        },
        {
            "platform": "X",
            "title": "新长文本推理架构论文发布",
            "url": "https://arxiv.org/abs/xxxx",
            "content": "上下文扩展到 400 万 token,推理速度提升 2 倍,作者来自 DeepMind。",
            "author": "@arxiv",
            "published_at": "2026-04-17T14:00:00",
        },
        {
            "platform": "X",
            "title": "某独立开发者 AI 浏览器插件月收破万美元",
            "url": "https://example.com/a4",
            "content": "开发者用 2 周完成 MVP,主打会议自动总结,已在 Product Hunt 登顶。",
            "author": "@indiehackers",
            "published_at": "2026-04-17T13:00:00",
        },
        {
            "platform": "X",
            "title": "讨论:大模型到底会不会取代初级程序员",
            "url": "https://example.com/a5",
            "content": "多位从业者给出截然相反的观点,争论持续升温。",
            "author": "@hn",
            "published_at": "2026-04-17T12:00:00",
        },
    ]


if __name__ == "__main__":
    mock = _mock_articles()
    categories = summarize(mock, platform="X")
    print(json.dumps(categories, ensure_ascii=False, indent=2))
