"""测试用的 mock payload。"""

from datetime import datetime

from .builder import build_ai_daily_card


def mock_payload() -> dict:
    """返回一个示例 AI Daily 卡片 payload。"""
    categories = [
        {
            "name": "大厂&融资",
            "summary": "科技巨头新一轮融资潮涌动",
            "items": [
                {
                    "title": "某 AI 独角兽完成 10 亿美元融资",
                    "summary": "据 [Bloomberg](https://example.com) 报道，估值突破 300 亿美元。",
                },
            ],
        },
        {
            "name": "模型&论文",
            "summary": "长文本推理技术持续突破",
            "items": [
                {
                    "title": "新长文本推理架构论文发布",
                    "summary": "上下文扩展到 400 万 token，[arXiv](https://arxiv.org/abs/xxxx)。",
                },
            ],
        },
    ]
    return build_ai_daily_card(
        categories=categories,
        platform="AI Daily",
        start_time=datetime(2026, 4, 17, 0, 0),
        end_time=datetime(2026, 4, 18, 0, 0),
    )
