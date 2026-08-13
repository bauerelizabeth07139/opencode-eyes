import base64
import io
import json
import logging
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
logger = logging.getLogger("opencode-eyes")

try:
    from PIL import Image as PILImage
except ImportError:
    logger.error("Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


STEP_API_BASE = "https://api.stepfun.com/step_plan/v1/chat/completions"
STEP_API_KEY = os.environ.get("STEP_API_KEY", "")
STEP_MODEL = os.environ.get("STEP_MODEL", "step-3.7-flash")
STEP_TIMEOUT = int(os.environ.get("STEP_TIMEOUT", "120"))
STEP_MAX_DIMENSION = int(os.environ.get("STEP_MAX_DIMENSION", "2048"))
STEP_JPEG_QUALITY = int(os.environ.get("STEP_JPEG_QUALITY", "85"))

_TOOLS = [
    {
        "name": "describe_image",
        "description": (
            "描述一张图片的内容。使用 StepFun Step-3.7-flash 多模态大模型对输入图片进行理解，"
            "返回详细的图片文字描述。为不具备多模态能力的模型提供'眼睛'。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的绝对或相对路径（例如 /home/user/photo.jpg）",
                },
                "prompt": {
                    "type": "string",
                    "description": "可选的自定义提示词，用于引导图片描述（默认为中文详细描述请求）",
                    "default": "请详细描述这张图片的内容，包括主要物体、场景、颜色、人物活动等。",
                },
            },
            "required": ["image_path"],
        },
    }
]


def _encode_image(image_path: str) -> str:
    """Load an image, downscale to a sane size, and compress to a JPEG base64 string.

    Shrinking the payload dramatically reduces upload + inference latency, which
    keeps the request well under the MCP client timeout (default 5000 ms).
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    img = PILImage.open(str(path))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    if STEP_MAX_DIMENSION > 0:
        img.thumbnail((STEP_MAX_DIMENSION, STEP_MAX_DIMENSION), PILImage.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=STEP_JPEG_QUALITY, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _extract_text(message: dict) -> str:
    """Return assistant text, falling back to reasoning fields when content is empty.

    step-3.7-flash is a reasoning model and sometimes returns the answer in
    `reasoning_content`/`reasoning` with an empty `content`.
    """
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts)
    for key in ("reasoning_content", "reasoning", "reasoning_text"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _call_step_api(image_b64: str, prompt: str) -> str:
    payload = json.dumps({
        "model": STEP_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 2048,
    }).encode("utf-8")

    req = urllib.request.Request(
        STEP_API_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {STEP_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=STEP_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"StepFun API HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"StepFun API connection error: {exc.reason}") from exc

    result = json.loads(raw)
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"No choices in API response: {result}")

    text = _extract_text(choices[0].get("message", {}))
    if not text:
        raise RuntimeError(f"Empty response from {STEP_MODEL}: {result}")
    return text


def _send(message: dict):
    data = json.dumps(message, ensure_ascii=False) + "\n"
    sys.stdout.buffer.write(data.encode("utf-8"))
    sys.stdout.buffer.flush()


def _handle_request(message: dict) -> dict:
    method = message.get("method", "")
    req_id = message.get("id")
    params = message.get("params", {})

    response = {"jsonrpc": "2.0"}
    if req_id is not None:
        response["id"] = req_id

    try:
        if method == "ping":
            response["result"] = {}
        elif method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "opencode-eyes", "version": "1.0.2"},
            }
        elif method == "tools/list":
            response["result"] = {"tools": _TOOLS}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            if tool_name != "describe_image":
                raise ValueError(f"Unknown tool: {tool_name}")

            image_path = arguments.get("image_path", "")
            prompt = arguments.get("prompt", "请详细描述这张图片的内容，包括主要物体、场景、颜色、人物活动等。")

            if not image_path:
                raise ValueError("image_path is required")

            if not STEP_API_KEY:
                raise RuntimeError("STEP_API_KEY environment variable is not set")

            image_b64 = _encode_image(image_path)
            description = _call_step_api(image_b64, prompt)

            response["result"] = {
                "content": [
                    {"type": "text", "text": f"[opencode-eyes] 图片描述:\n{description}"}
                ],
            }
        else:
            response["error"] = {"code": -32601, "message": f"Method not found: {method}"}
    except Exception as exc:
        logger.error("Error handling %s: %s", method, exc, exc_info=True)
        response["error"] = {"code": -32603, "message": str(exc)}

    return response


def main():
    if not STEP_API_KEY:
        logger.warning("STEP_API_KEY is not set. Set it via environment variable.")
    logger.info("opencode-eyes server starting...")

    for raw_line in sys.stdin.buffer:
        line_str = raw_line.decode("utf-8", errors="replace").strip()
        if not line_str:
            continue

        try:
            message = json.loads(line_str)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON: %s", exc)
            continue

        if message.get("method") == "notifications/initialized":
            logger.info("Client initialized notification received")
            continue

        _send(_handle_request(message))


if __name__ == "__main__":
    main()
