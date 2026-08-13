# opencode-eyes 👁️

MCP server that provides image description capability using StepFun **Step-3.7-flash** multimodal model.

为不具备多模态能力的模型提供**"眼睛"**。将图片输入，即可获得详细的图片文字描述。

## 功能

| 工具 | 说明 |
|------|------|
| `describe_image` | 描述一张图片的内容，使用 StepFun Step-3.7-flash 多模态大模型 |

**重要：这是纯文本模型读取图片的唯一方法。** 当用户使用不具备视觉能力的纯文本模型并提供/引用图片时，模型必须调用 `describe_image`，绝不把图片字节或 base64 直接塞进上下文/回复。

## 支持的图片来源

`describe_image` 的 `image_path` 参数支持以下形式：

- **本地文件路径**（绝对路径或相对路径，相对路径会基于服务器工作目录解析）
- **http(s) 图片 URL**（自动下载）
- **data URI**：`data:image/png;base64,...`
- **纯 base64 字符串**

所有来源都会被统一缩放（默认最长边 2048px）并压缩为 JPEG 后发送，保证低延迟、不超时。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `STEP_API_KEY` | 是 | — | StepFun API Key |
| `STEP_MODEL` | 否 | `step-3.7-flash` | 使用的模型名称（Step Plan 专用地址 `https://api.stepfun.com/step_plan/v1`） |
| `STEP_TIMEOUT` | 否 | `120` | StepFun API 请求超时（秒） |
| `STEP_MAX_DIMENSION` | 否 | `2048` | 发送前图片最长边缩放到该像素，0 表示不缩放 |
| `STEP_JPEG_QUALITY` | 否 | `85` | 发送前 JPEG 压缩质量（0-100） |

## 更新日志

### v1.0.3

- **修复 Bad Request / 无法正确调用**：`image_path` 现在支持本地路径、http(s) URL、data URI、纯 base64 字符串，纯文本模型无论拿到哪种形式的图片引用都能正确读取，不再因传入 URL/base64 字符串而报错。
- **强化纯文本模型强制使用**：工具描述中明确标注这是纯文本模型读图的唯一方法，引导模型必须调用 `describe_image`，且不得把图片数据塞进上下文。
- 更清晰的错误信息（文件不存在、URL 下载失败、非法图片等）。

### v1.0.2

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
