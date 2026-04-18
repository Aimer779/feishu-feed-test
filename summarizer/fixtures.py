def mock_articles() -> list[dict]:
    return [
        {
            "title": "某 AI 独角兽完成 10 亿美元 C 轮融资",
            "url": "https://example.com/a1",
            "content": "估值突破 300 亿美元,领投方为红杉与软银,资金将用于下一代基础模型训练。",
            "author": "@techcrunch",
            "published_at": "2026-04-17T15:30:00",
        },
        {
            "title": "红杉、软银领投,AI 独角兽估值达 300 亿美元",
            "url": "https://example.com/a2",
            "content": "同一起融资的另一家媒体报道,细节相同。",
            "author": "@bloomberg",
            "published_at": "2026-04-17T15:45:00",
        },
        {
            "title": "新长文本推理架构论文发布",
            "url": "https://arxiv.org/abs/xxxx",
            "content": "上下文扩展到 400 万 token,推理速度提升 2 倍,作者来自 DeepMind。",
            "author": "@arxiv",
            "published_at": "2026-04-17T14:00:00",
        },
        {
            "title": "某独立开发者 AI 浏览器插件月收破万美元",
            "url": "https://example.com/a4",
            "content": "开发者用 2 周完成 MVP,主打会议自动总结,已在 Product Hunt 登顶。",
            "author": "@indiehackers",
            "published_at": "2026-04-17T13:00:00",
        },
        {
            "title": "讨论:大模型到底会不会取代初级程序员",
            "url": "https://example.com/a5",
            "content": "多位从业者给出截然相反的观点,争论持续升温。",
            "author": "@hn",
            "published_at": "2026-04-17T12:00:00",
        },
    ]
