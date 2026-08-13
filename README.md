# opencode-eyes 👁️

MCP server that provides image description capability using StepFun **Step-3.7-flash** multimodal model.

为不具备多模态能力的模型提供**"眼睛"**。将图片输入，即可获得详细的图片文字描述。

## 功能

| 工具 | 说明 |
|------|------|
| `describe_image` | 描述一张图片的内容，使用 StepFun Step-3.7-flash 多模态大模型 |

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `STEP_API_KEY` | 是 | — | StepFun API Key |
| `STEP_MODEL` | 否 | `step-3.7-flash` | 使用的模型名称 |

## 安装

```bash
pip install mcp httpx Pillow
```

## 运行

```bash
# 设置环境变量
set STEP_API_KEY=2L5DXp5JijQW9a4tiL5d4SjqCT6iGrYTA5DoSRRx5VzwHKjmn0YxmM8eul8ehWJ1x

# 启动服务
python -m opencode_eyes
```

## 在 OpenCode / Claude Desktop 中配置

```json
{
  "mcpServers": {
    "opencode-eyes": {
      "command": "python",
      "args": ["-m", "opencode_eyes"],
      "env": {
        "STEP_API_KEY": "你的StepFun API Key"
      }
    }
  }
}
```

## License

MIT
