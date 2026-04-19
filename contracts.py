"""Shared runtime contracts for the fetcher -> summarizer -> builder pipeline."""

from __future__ import annotations

from typing import TypedDict, cast


class RawArticle(TypedDict):
    platform: str
    title: str
    url: str
    content: str
    author: str
    published_at: str


class CategoryItem(TypedDict):
    title: str
    summary: str


class CategoryGroup(TypedDict):
    name: str
    summary: str
    items: list[CategoryItem]


_RAW_ARTICLE_FIELDS = (
    "platform",
    "title",
    "url",
    "content",
    "author",
    "published_at",
)
_CATEGORY_ITEM_FIELDS = ("title", "summary")


def validate_raw_articles(articles: object, source: str) -> list[RawArticle]:
    if not isinstance(articles, list):
        raise ValueError(f"{source}: expected list[RawArticle], got {type(articles).__name__}")

    normalized: list[RawArticle] = []
    for index, article in enumerate(articles):
        if not isinstance(article, dict):
            raise ValueError(
                f"{source}: article[{index}] expected dict, got {type(article).__name__}"
            )
        normalized.append(cast(RawArticle, _normalize_string_dict(article, _RAW_ARTICLE_FIELDS, source, f"article[{index}]")))
    return normalized


def validate_category_groups(categories: object, source: str) -> list[CategoryGroup]:
    if not isinstance(categories, list):
        raise ValueError(
            f"{source}: expected list[CategoryGroup], got {type(categories).__name__}"
        )

    normalized: list[CategoryGroup] = []
    for group_index, category in enumerate(categories):
        if not isinstance(category, dict):
            raise ValueError(
                f"{source}: category[{group_index}] expected dict, got {type(category).__name__}"
            )

        group_fields = _normalize_string_dict(
            category,
            ("name", "summary"),
            source,
            f"category[{group_index}]",
        )
        raw_items = category.get("items")
        if not isinstance(raw_items, list):
            raise ValueError(
                f"{source}: category[{group_index}].items expected list, got "
                f"{type(raw_items).__name__}"
            )

        items: list[CategoryItem] = []
        for item_index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{source}: category[{group_index}].items[{item_index}] expected dict, got "
                    f"{type(item).__name__}"
                )
            items.append(
                cast(
                    CategoryItem,
                    _normalize_string_dict(
                        item,
                        _CATEGORY_ITEM_FIELDS,
                        source,
                        f"category[{group_index}].items[{item_index}]",
                    ),
                )
            )

        normalized.append(
            CategoryGroup(
                name=group_fields["name"],
                summary=group_fields["summary"],
                items=items,
            )
        )
    return normalized


def _normalize_string_dict(
    payload: dict,
    required_fields: tuple[str, ...],
    source: str,
    label: str,
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for field in required_fields:
        value = payload.get(field)
        if not isinstance(value, str):
            raise ValueError(
                f"{source}: {label}.{field} expected str, got {type(value).__name__}"
            )
        normalized[field] = value.strip()
    return normalized
