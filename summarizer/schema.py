from typing import Any

from categories import CATEGORY_EMOJI_MAP

CATEGORIES_ENUM = list(CATEGORY_EMOJI_MAP.keys())

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
                                "required": ["title", "summary"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            }
        },
    },
}
