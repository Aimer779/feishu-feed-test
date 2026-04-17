# 飞书卡片模板实战经验总结

基于注册和发送 `task-report` 卡片的实战过程，总结以下经验：

---

## 1. 外层包装不能少

**问题**：提供的 JSON 可能是纯 `card` 定义。  
**解决**：注册时必须包一层 `msg_type: interactive`，变成完整的 Webhook Payload：

```json
{
  "msg_type": "interactive",
  "card": { ... }
}
```

> `cards/` 目录中的 JSON 文件必须是完整的 Webhook Payload，不能直接将飞书卡片搭建工具导出的纯 `card` 定义放入该目录。

---

## 2. Schema 2.0 对 `collapsible_panel` 有严格限制

**问题**：`collapsible_panel` 使用了 `background_style` 和 `border`，发送时报 `parse card json err`。  
**解决**：飞书 schema 2.0 的 `collapsible_panel` **不支持**以下属性：

- `background_style`
- `border`

应删除这些字段，只保留 `expanded`、`header`、`elements`、`padding` 等标准字段。

---

## 3. 按钮不要用 `action` 包装

**问题**：使用了 `{"tag": "action", "actions": [...]}` 嵌套按钮，报 `unsupported tag action`。  
**解决**：schema 2.0 中按钮应直接作为 `button` 标签放入 `body.elements` 数组，不需要 `action` / `actions` 包装：

```json
{
  "tag": "button",
  "text": { "tag": "plain_text", "content": "查看详情" },
  "type": "primary",
  "url": "https://example.com"
}
```

---

## 4. 飞书 Webhook 有频率限制

**问题**：连续修正后快速重发，触发了 `code: 11232 frequency limited`。  
**解决**：

- 遇到限流不要慌，**等待 1-2 分钟**再重试。
- 频繁调试时，建议每次发送间隔几秒以上。

---

## 5. 注册模板零代码

**经验**：本项目支持动态扫描 `cards/` 目录，新增模板只需：

1. 保存 JSON 文件到 `cards/xxx.json`
2. 运行 `--list` 验证加载
3. 运行 `--template xxx` 发送

无需修改 `send_card.py` 任何代码。

---

## 快速参考：注册新模板 checklist

- [ ] JSON 外层包含 `"msg_type": "interactive"` 和 `"card": { ... }`
- [ ] 未使用 schema 2.0 不支持的标签或属性
- [ ] 按钮直接作为 `button` 标签放入 `elements`，无 `action` 包装
- [ ] JSON 格式合法（无语法错误）
- [ ] 模板变量已静态化（如使用了占位符 `${variable}`，已替换为实际内容）
- [ ] 发送前用 `--list` 检查模板是否能正常加载
