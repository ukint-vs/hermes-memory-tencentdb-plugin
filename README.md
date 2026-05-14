# Hermes memory_tencentdb Plugin

Hermes memory provider for the `memory-tencentdb` Gateway from TencentDB Agent
Memory. The plugin gives Hermes a four-layer memory pipeline: raw conversation
capture, episodic extraction, scene grouping, and persona synthesis.

This repo contains the Hermes adapter only. The Node.js Gateway/runtime comes
from the upstream package or source checkout.

## Requirements

- Hermes Agent installed.
- Node.js 22 or newer for the Gateway runtime.
- An OpenAI-compatible LLM endpoint for smart extraction. OpenRouter works well.
- No Tencent Cloud VectorDB account is required. Local SQLite/JSONL storage is
  the default unless you configure the upstream Gateway for `storeBackend: tcvdb`.

## Install

Install the Hermes plugin:

```bash
hermes plugins install ukint-vs/hermes-memory-tencentdb-plugin
```

Install the Gateway runtime if you do not already have it:

```bash
~/.hermes/plugins/memory_tencentdb/scripts/install.sh --with-gateway
```

For local development, clone this repo and link it into Hermes:

```bash
git clone git@github.com:ukint-vs/hermes-memory-tencentdb-plugin.git
cd hermes-memory-tencentdb-plugin
scripts/install.sh --with-gateway
```

The installer links the plugin here:

```text
~/.hermes/plugins/memory_tencentdb
```

It installs or expects the Gateway here:

```text
~/.memory-tencentdb/tdai-memory-openclaw-plugin
```

If you use a TencentDB Agent Memory source checkout instead, set:

```bash
TDAI_INSTALL_DIR=/path/to/TencentDB-Agent-Memory
```

## Configure Hermes

Use Hermes' memory setup wizard:

```bash
hermes memory setup
```

Choose `memory_tencentdb`. The setup flow stores non-secret plugin settings in
`~/.hermes/config.yaml` and stores the LLM API key in `~/.hermes/.env`.
Explicit environment variables still override config values.

Expected config shape:

```yaml
memory:
  provider: memory_tencentdb

plugins:
  memory-tencentdb:
    tdai_install_dir: ~/.memory-tencentdb/tdai-memory-openclaw-plugin
    gateway_host: 127.0.0.1
    gateway_port: '8420'
    llm_base_url: https://openrouter.ai/api/v1
    llm_model: deepseek/deepseek-v4-flash
```

Expected `.env` entry:

```bash
TDAI_LLM_API_KEY=<your-openrouter-api-key>
```

Manual setup is also fine:

```bash
hermes config set memory.provider memory_tencentdb
TDAI_LLM_BASE_URL=https://openrouter.ai/api/v1
TDAI_LLM_API_KEY=<your-openrouter-api-key>
TDAI_LLM_MODEL=deepseek/deepseek-v4-flash
```

If Hermes already has `OPENROUTER_API_KEY`, use the same value for the setup
wizard's `llm_api_key` prompt. Restart Hermes or run `/reload` in an existing
session so the new environment values load.

For local Ollama-compatible endpoints:

```bash
TDAI_LLM_BASE_URL=http://127.0.0.1:11434/v1
TDAI_LLM_MODEL=qwen2.5:7b
TDAI_LLM_API_KEY=
```

## Verify

Check that Hermes sees the provider:

```bash
hermes memory status
```

Expected result:

```text
Provider:  memory_tencentdb
Plugin:    installed
Status:    available
```

Start Hermes normally and send a message. The provider starts the Gateway on
first use. Check Gateway health:

```bash
curl -fsS http://127.0.0.1:8420/health
```

A healthy local setup returns JSON with `status: "ok"`. Logs live under:

```text
~/.hermes/logs/memory_tencentdb/
```

To confirm smart extraction is using your model, inspect the Gateway logs:

```bash
grep -i "standalone-runner" ~/.hermes/logs/memory_tencentdb/gateway.stdout.log
```

You should see `model=deepseek/deepseek-v4-flash` or your configured model.

## Useful Commands

```bash
~/.hermes/plugins/memory_tencentdb/scripts/memory-tencentdb-ctl.sh status
~/.hermes/plugins/memory_tencentdb/scripts/memory-tencentdb-ctl.sh config show
~/.hermes/plugins/memory_tencentdb/scripts/memory-tencentdb-ctl.sh logs
```

Switch Gateway storage back to local SQLite:

```bash
~/.hermes/plugins/memory_tencentdb/scripts/memory-tencentdb-ctl.sh config vdb-off
```

## Troubleshooting

Provider is not listed: check that `~/.hermes/plugins/memory_tencentdb` exists
and contains `plugin.yaml`.

Gateway is not reachable: check whether port `8420` is already in use:

```bash
lsof -nP -iTCP:8420 -sTCP:LISTEN
```

Smart extraction is not running: confirm `TDAI_LLM_API_KEY` exists in
`~/.hermes/.env` and `llm_base_url` / `llm_model` exist under
`plugins.memory-tencentdb` in `~/.hermes/config.yaml`. The plugin passes these
values to the Gateway subprocess when it starts.

Search works but vector search is disabled: the Gateway can still capture L0
and extract L1 memories. Without an embedding service it falls back to text
search.

## Upstream

- TencentDB Agent Memory: <https://github.com/Tencent/TencentDB-Agent-Memory>
- Runtime package: <https://www.npmjs.com/package/@tencentdb-agent-memory/memory-tencentdb>

The upstream project owns the Gateway, memory pipeline, OpenClaw integration,
local storage engine, and optional Tencent Cloud VectorDB integration. This
repo only packages the Hermes adapter.
