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
| `STEP_MODEL` | 否 | `step-3.7-flash` | 使用的模型名称（Step Plan 专用地址 `https://api.stepfun.com/step_plan/v1`） |
| `STEP_TIMEOUT` | 否 | `120` | StepFun API 请求超时（秒） |
| `STEP_MAX_DIMENSION` | 否 | `2048` | 发送前图片最长边缩放到该像素，0 表示不缩放 |
| `STEP_JPEG_QUALITY` | 否 | `85` | 发送前 JPEG 压缩质量（0-100） |

## 更新日志 (v1.0.2)

- **修复 MCP -32001 Request timed out**：发送前将图片缩放/压缩为 JPEG，大幅减小 payload、降低 API 延迟，避免超过 MCP 客户端默认 5s 超时。
- **修复空描述**：`step-3.7-flash` 有时把答案放在 `reasoning_content`/`reasoning` 而 `content` 为空，现已自动回退。
- **修复 Windows 中文乱码**：stdout/stdin 改为 UTF-8 字节读写。
- 新增 `ping` 方法支持，更健壮的 MCP 握手。

> 注意：opencode 的 MCP 请求超时默认为 5000ms。若仍需更宽松的超时，可在 opencode 配置中为该 MCP 设置 `"timeout": 120000`，或全局设置 `"experimental": { "mcp_timeout": 120000 }`。

## 安装

```bash
pip install Pillow
```

## 运行

```bash
# 设置环境变量
set STEP_API_KEY=你的StepFun API Key

# 启动服务
python -m opencode_eyes
```

## 在 OpenCode 中配置

```json
{
  "mcp": {
    "opencode-eyes": {
      "type": "local",
      "command": ["python", "-m", "opencode_eyes"],
      "enabled": true,
      "timeout": 120000,
      "environment": {
        "STEP_API_KEY": "你的StepFun API Key"
      }
    }
  }
}
```

## License

MIT
