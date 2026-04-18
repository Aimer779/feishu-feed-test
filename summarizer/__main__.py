import json
import sys

from .core import summarize
from .fixtures import mock_articles

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    articles = mock_articles()
    categories = summarize(articles, platform="X")
    print(json.dumps(categories, ensure_ascii=False, indent=2))
