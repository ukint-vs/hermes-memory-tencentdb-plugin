# memory_tencentdb Installed

Enable the provider in `~/.hermes/config.yaml`:

```yaml
memory:
  provider: memory_tencentdb
```

Install or point to the external Node Gateway runtime:

```bash
export TDAI_INSTALL_DIR="$HOME/.memory-tencentdb/tdai-memory-openclaw-plugin"
```

Configure an OpenAI-compatible LLM endpoint for smart extraction:

```bash
TDAI_LLM_BASE_URL=https://openrouter.ai/api/v1
TDAI_LLM_API_KEY=<openrouter-key>
TDAI_LLM_MODEL=deepseek/deepseek-v4-flash
```

For fully local storage, leave the Gateway on its default SQLite backend and do
not configure `storeBackend: tcvdb`. Tencent Cloud VectorDB is optional and only
used when explicitly enabled in the Gateway configuration.
