"""卡片数据结构定义。"""

from typing import TypedDict


class CardItem(TypedDict, total=False):
    title: str
    summary: str
    source: str
    url: str


class CardCategory(TypedDict, total=False):
    name: str
    summary: str
    items: list[CardItem]


class CardPayload(TypedDict, total=False):
    msg_type: str
    card: dict
