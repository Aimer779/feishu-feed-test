import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contracts import validate_category_groups, validate_raw_articles


class ContractsTestCase(unittest.TestCase):
    def test_validate_raw_articles_rejects_missing_string_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "article\\[0\\]\\.url expected str"):
            validate_raw_articles(
                [
                    {
                        "platform": "X",
                        "title": "Hello",
                        "url": None,
                        "content": "World",
                        "author": "@bot",
                        "published_at": "2026-04-19T08:00:00Z",
                    }
                ],
                source="test raw articles",
            )

    def test_validate_category_groups_rejects_invalid_items_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "category\\[0\\]\\.items expected list"):
            validate_category_groups(
                [
                    {
                        "name": "模型&论文",
                        "summary": "趋势总结",
                        "items": "not-a-list",
                    }
                ],
                source="test category groups",
            )


if __name__ == "__main__":
    unittest.main()
