# Hermes memory_tencentdb Plugin

Standalone Hermes memory provider adapter for the `memory-tencentdb` Gateway.
The repository root is the Hermes plugin root: it contains the Python provider,
manifest, tests, and installer scripts. The Node.js Gateway/core remains an
external runtime supplied by `@tencentdb-agent-memory/memory-tencentdb` or by a
local source checkout.

## What This Provides

- Hermes `MemoryProvider` named `memory_tencentdb`.
- Python HTTP client and supervisor for the local Node.js Gateway.
- Local-by-default memory storage through the Gateway SQLite/JSONL backend.
- Optional Tencent Cloud VectorDB only when the Gateway is configured for
  `storeBackend: tcvdb`.

This plugin is not TencentDB. TencentDB/TCVDB is a managed cloud vector
database and is not required for local use. Smart extraction still needs an
OpenAI-compatible LLM endpoint, such as OpenRouter or a local Ollama-compatible
server.

## Architecture

```text
Hermes agent
  -> memory_tencentdb Python provider
  -> local memory-tencentdb Gateway
  -> SQLite/JSONL storage by default
  -> optional LLM endpoint for L1/L2/L3 extraction
  -> optional Tencent Cloud VectorDB if explicitly configured
```

Layer mapping is handled by the Gateway: L0 conversation capture, L1 episodic
extraction, L2 scene blocks, and L3 persona synthesis. The Hermes plugin keeps
Hermes integration thin and avoids owning the Gateway data model.

## Repository Layout

```text
__init__.py                  Hermes MemoryProvider entrypoint
client.py                    HTTP client for the Gateway API
supervisor.py                Gateway process supervisor
plugin.yaml                  Hermes plugin manifest
after-install.md             Post-install instructions shown by Hermes
scripts/install.sh           Local symlink installer; optional Gateway install
scripts/memory-tencentdb-ctl.sh
                             Gateway config/control helper
tests/                       Provider contract and lifecycle tests
```

## Install

From a published repository:

```bash
hermes plugins install ukint-vs/hermes-memory-tencentdb-plugin
```

For local development:

```bash
git clone git@github.com:ukint-vs/hermes-memory-tencentdb-plugin.git
cd hermes-memory-tencentdb-plugin
scripts/install.sh
```

The local installer links:

```text
~/.hermes/plugins/memory_tencentdb -> <repo>
```

Install the Gateway runtime from npm when you do not already have a checkout:

```bash
scripts/install.sh --with-gateway
```

By default this installs the Gateway under:

```text
~/.memory-tencentdb/tdai-memory-openclaw-plugin
```

To use an existing Gateway source checkout:

```bash
export TDAI_INSTALL_DIR=/path/to/TencentDB-Agent-Memory
```

## Configure Hermes

Enable the provider in `~/.hermes/config.yaml`:

```yaml
memory:
  provider: memory_tencentdb
```

Configure the Gateway LLM endpoint in the environment that starts Hermes:

```bash
TDAI_LLM_BASE_URL=https://openrouter.ai/api/v1
TDAI_LLM_API_KEY=<openrouter-key>
TDAI_LLM_MODEL=deepseek/deepseek-v4-flash
```

For local Ollama-compatible endpoints:

```bash
TDAI_LLM_BASE_URL=http://127.0.0.1:11434/v1
TDAI_LLM_MODEL=qwen2.5:7b
TDAI_LLM_API_KEY=
```

Leave `storeBackend` unset for local SQLite storage. Only configure
`storeBackend: tcvdb` when you intentionally want Tencent Cloud VectorDB.

## Gateway Discovery

The provider starts the Gateway automatically when it can find
`src/gateway/server.ts`. Discovery order:

1. `MEMORY_TENCENTDB_GATEWAY_CMD`, if set.
2. `$TDAI_INSTALL_DIR/src/gateway/server.ts`.
3. A Gateway checkout found by walking upward from this plugin.
4. `~/.memory-tencentdb/tdai-memory-openclaw-plugin/src/gateway/server.ts`.

Manual Gateway start is also supported:

```bash
cd "$TDAI_INSTALL_DIR"
npx tsx src/gateway/server.ts
```

## Configuration Reference

| Setting | Purpose | Default |
| --- | --- | --- |
| `memory.provider` | Selects this Hermes provider. | none |
| `TDAI_INSTALL_DIR` | Gateway checkout used for auto-discovery. | `~/.memory-tencentdb/tdai-memory-openclaw-plugin` |
| `MEMORY_TENCENTDB_GATEWAY_CMD` | Explicit command used to start the Gateway. | auto-discovered |
| `MEMORY_TENCENTDB_GATEWAY_HOST` | Gateway bind/connect host. | `127.0.0.1` |
| `MEMORY_TENCENTDB_GATEWAY_PORT` | Gateway bind/connect port. | `8420` |
| `TDAI_LLM_BASE_URL` | OpenAI-compatible extraction endpoint. | `http://127.0.0.1:11434/v1` |
| `TDAI_LLM_API_KEY` | LLM API key, if required. | empty |
| `TDAI_LLM_MODEL` | Model used by the Gateway extraction pipeline. | `qwen2.5:7b` |

## Operations

Use the helper script for Gateway-side configuration:

```bash
scripts/memory-tencentdb-ctl.sh status
scripts/memory-tencentdb-ctl.sh config show
scripts/memory-tencentdb-ctl.sh logs
```

Common setup commands:

```bash
scripts/memory-tencentdb-ctl.sh config llm --base-url "$TDAI_LLM_BASE_URL" --model "$TDAI_LLM_MODEL"
scripts/memory-tencentdb-ctl.sh config vdb-off
```

If Hermes cannot list the provider, check that
`~/.hermes/plugins/memory_tencentdb/plugin.yaml` exists and that the symlink
points at this repository.

## Test

Set `HERMES_AGENT_ROOT` if Hermes is not installed at
`~/.hermes/hermes-agent`:

```bash
HERMES_AGENT_ROOT=~/.hermes/hermes-agent python3 -m pytest
```

Gateway integration tests are skipped by default. Enable them explicitly:

```bash
TDAI_E2E_REAL_GATEWAY=1 TDAI_INSTALL_DIR=/path/to/gateway python3 -m pytest
```

Before release, also run:

```bash
python3 -m py_compile __init__.py client.py supervisor.py tests/*.py
bash -n scripts/install.sh
bash -n scripts/memory-tencentdb-ctl.sh
```

## Release Checklist

1. Confirm `plugin.yaml` version and `CHANGELOG.md` match.
2. Run the validation commands above.
3. Install into a temporary `HERMES_HOME` and confirm provider discovery.
4. Push a signed or reviewed commit to `main`.
5. Tag the release when the Gateway runtime compatibility is confirmed.
