# opencode-eyes

**Eyes for models that cannot see.** The image goes to StepFun's
`step-3.7-flash` vision model; the description comes back as tool output.

*给不具备多模态能力的模型一双眼睛:把图片交给 StepFun 多模态模型,拿回文字描述。*

As a DeepSeek Harness plugin: the MCP server ships inside the bundle, so
installing one plugin is the whole setup — no `mcpServers` file to hand-edit.

## Install

**DeepSeek Harness Desktop** — open **Plugins** in the sidebar, choose **Add
plugin**, and enter:

```
https://github.com/bauerelizabeth07139/opencode-eyes
```

Then switch the new **dsh-opencode-eyes** bundle on. The Desktop app boots the
reserved `desktop` profile, so that is where it has to be enabled.

**dsh CLI** — install it into the profile you actually boot:

```sh
dsh plugin --profile web add bauerelizabeth07139/opencode-eyes
```

**No git on the machine?** pnpm resolves a git shorthand with `git ls-remote`,
which fails with `'git' is not recognized` when git is missing. Use the tarball
instead — that path is plain HTTPS:

```sh
dsh plugin --profile web add https://codeload.github.com/bauerelizabeth07139/opencode-eyes/tar.gz/main
```

The same address works in the Desktop **Add plugin** dialog. Replace `main`
with a commit SHA to pin an exact revision (`/tar.gz/<sha>`).

Uninstall with `dsh plugin --profile web remove dsh-opencode-eyes`.

## Requirements

- **Python ≥ 3.8** on `PATH`, or pointed at with `python`.
- **Pillow** in that interpreter — the server's only third-party import
  (`pip install Pillow`).
- **A StepFun API key** in `STEP_API_KEY` (or `config.apiKey`). Without one the
  server still starts and `describe_image` returns a clear error.

## Tools

The server registers `1` tool(s). DSH namespaces them automatically,
so the model calls them as `mcp__opencode_eyes__<tool>`:

| Tool | What it does |
|---|---|
| `describe_image` | Reads an image file, base64-encodes it as JPEG (optionally downscaled) and asks the vision model to describe it. Parameters: `image_path` (required), `prompt` (optional). |

## Configuration

| Key | Environment variable | Default | Meaning |
|---|---|---|---|
| `python` | — | discovered | interpreter that runs the server |
| `apiKey` | `STEP_API_KEY` | *(empty)* | StepFun credential; required by `describe_image` |
| `model` | `STEP_MODEL` | `step-3.7-flash` | model id sent in the request |
| `timeoutSeconds` | `STEP_TIMEOUT` | `120` | the server's own HTTP timeout |
| `maxDimension` | `STEP_MAX_DIMENSION` | `2048` | images are downscaled to this edge length |
| `jpegQuality` | `STEP_JPEG_QUALITY` | `85` | JPEG quality of the re-encoded image |
| `toolCallTimeoutMs` | — | `300000` | DSH's per-call budget; keep it above `timeoutSeconds` |
| `env` | — | `{}` | raw environment passthrough for anything else |

Every field is optional and lives in the loader row. For example, in
`cordis.patch.yml`:

```yaml
- id: dsh-opencode-eyes
  name: 'dsh-opencode-eyes'
  config:
    apiKey: 'sk-...'
    toolCallTimeoutMs: 300000
```

## Notes

- **The API base URL is compiled into the server** (`https://api.stepfun.com/step_plan/v1/chat/completions`);
  there is no `baseUrl` option to point it elsewhere. This plugin exposes only
  what the server actually reads.
- **`src/` layout.** The package is a `src/`-layout Python module, so the
  server must run with the repository's `src` directory as its working
  directory. The plugin does that for you.
- **Timeouts.** The server waits up to `STEP_TIMEOUT` (120 s) for StepFun, which
  is longer than the harness's 60 s default, so the plugin mounts with a 300 s
  per-call budget.

## How it is mounted

`index.js` resolves a Python interpreter (the configured `python`, then
`python3`/`python` on `PATH`), hands the server its argv and working directory,
and mounts it as a stdio MCP server through `@deepseek-ai/dsh-mcp-client` with
`failOnStartupError: true`, so a server that cannot start is a visible error
rather than a silently missing tool.

Credentials are forwarded explicitly. The harness scrubs credential-shaped
variables (`KEY`, `TOKEN`, `SECRET`, `PASSWORD`) out of the environment a child
process inherits, so `config.apiKey` — falling back to the variable the server
documents — is written into the child's environment by the plugin itself. That
means both of these work:

```yaml
config:
  apiKey: '<your key>'
```

```sh
export STEP_API_KEY='<your key>'   # picked up at load time
```

## Development

No build step and no runtime dependencies — `@deepseek-ai/cordis` and
`@deepseek-ai/dsh-mcp-client` are peers supplied by the Harness.

```sh
npm test    # node >= 22: manifest checks + the stdio mount, both Harness-free
```

The mount test loads `index.js` with `@deepseek-ai/dsh-mcp-client` stubbed and
asserts the exact stdio configuration the plugin produces, including the
credential forwarding above.

## Repository layout

| Path | Purpose |
|---|---|
| `index.js` | the DSH plugin: resolves the interpreter and mounts the server |
| `cordis.patch.yml` | the loader row that activates the plugin |
| `locale/{en,zh}.json` | card title and description for the plugin lists |
| `assets/icon.svg` | card artwork |
| `test/` | `npm test`: manifest composition and the mount contract |
| `src/opencode_eyes/` | the MCP server, unchanged |
| `pyproject.toml`, `requirements.txt` | the Python package metadata, unchanged |

## Other hosts (unchanged)

The server is a plain stdio MCP server and still works anywhere else. The
repository's original README is kept verbatim as
[`README.opencode.md`](README.opencode.md), and the launch stanza from it keeps
working:

```json
{
  "mcp": {
    "opencode-eyes": {
      "type": "local",
      "command": ["python", "-m", "opencode_eyes"],
      "enabled": true,
      "timeout": 120000,
      "environment": { "STEP_API_KEY": "你的StepFun API Key" }
    }
  }
}
```

On another host, run the server from the repository's `src` directory (or put
`src` on `PYTHONPATH`) — that is the one thing the plugin adds.

## License

[MIT](LICENSE) — the repository declared MIT in `pyproject.toml` but shipped no licence file; this plugin's release adds one.
