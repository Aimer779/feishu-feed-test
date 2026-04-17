# Feishu Card Sender

通过飞书 Webhook 发送多种类型的卡片消息。支持模板化管理和命令行快速发送。

## 已实现功能

- **多模板卡片发送**：内置文本、Markdown、模板卡片、旅游推荐、AI 资讯等多种卡片
- **动态模板加载**：所有卡片模板存放于 `cards/` 目录，程序启动时自动扫描加载，无需修改代码即可增删模板
- **灵活的命令行参数**：支持选择模板、加载外部 JSON、自定义 Webhook、简单变量覆盖等
- **虚拟环境管理**：使用 `uv` 进行 Python 虚拟环境创建和依赖安装

## 环境准备

项目使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境和依赖。

```powershell
# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板：
   ```powershell
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入真实的飞书 Webhook 地址：
   ```text
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
   ```

3. 也可以通过环境变量直接覆盖：

```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
.venv\Scripts\python.exe send_card.py
```

## 使用方法

### 发送卡片

```powershell
# 使用默认模板（从 .env 读取 webhook）
.venv\Scripts\python.exe send_card.py

# 使用指定模板
.venv\Scripts\python.exe send_card.py --template travel

# 从外部 JSON 文件加载
.venv\Scripts\python.exe send_card.py --file my-card.json

# 临时覆盖 webhook 地址
.venv\Scripts\python.exe send_card.py --template text --webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
```

### 查看所有可用模板

```powershell
.venv\Scripts\python.exe send_card.py --list
```

### 覆盖模板变量

```powershell
.venv\Scripts\python.exe send_card.py --template text --var "text=自定义消息内容"
```

> 注：`--var` 目前仅支持对 `payload` 顶层、`card` 层或 `content` 层的字符串值进行简单替换。

## 内置模板

| 模板名 | 说明 |
|--------|------|
| `default` | 原始模板卡片（`template_id: <你的模板ID>`） |
| `text` | 纯文本消息 |
| `markdown` | Markdown 富文本卡片 |
| `travel` | 西湖旅游推荐卡片 |
| `feishu-card` | 五条 AI Daily 资讯卡片（静态内容版） |

## 新增模板注意事项

1. **必须是完整的 Webhook Payload**
   - `cards/` 目录中的 JSON 文件最外层必须包含 `msg_type` 和 `card`，例如：
     ```json
     {
       "msg_type": "interactive",
       "card": {
         "schema": "2.0",
         ...
       }
     }
     ```
   - 不能直接将飞书卡片搭建工具导出的纯 `card` 定义放入该目录，否则会导致发送失败或内容解析异常。

2. **模板变量需提前静态化**
   - 如果卡片中使用了 `${variable}` 或 `repeat` 组件，直接通过 Webhook 发送时变量区域会显示**空白**或原始占位符。
   - 建议先在 JSON 中填充为静态内容，再注册到 `cards/` 目录。

3. **文件名即模板名**
   - 文件名将直接作为 `--template` 的参数名（不含 `.json` 后缀）。
   - 建议使用英文小写、短横线连接，如 `daily-report.json`。

4. **确保 JSON 格式合法**
   - 启动时若某个 `.json` 解析失败，程序会直接报错退出。
   - 新增后建议先用 `--list` 检查是否能正常加载。

5. **图片资源需有效**
   - 若模板中引用了 `img_key`，请确保图片已上传到该机器人/应用所在的飞书租户，否则图片区域会显示裂图。

## 项目结构

```text
.
├── cards/                  # 卡片模板目录
│   ├── default.json
│   ├── feishu-card.json
│   ├── markdown.json
│   ├── text.json
│   └── travel.json
├── .venv/                  # Python 虚拟环境（由 uv 创建）
├── requirements.txt        # 项目依赖
├── send_card.py            # 主程序：CLI 卡片发送器
└── README.md               # 本文件
```
