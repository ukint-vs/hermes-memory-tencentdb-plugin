# Repository Guidelines

## Project Structure & Module Organization

This repository is itself the Hermes plugin root. `__init__.py` exposes the
`MemoryTencentdbProvider`, `client.py` wraps the Gateway HTTP API, and
`supervisor.py` manages the optional local Gateway process. `plugin.yaml`
contains the Hermes manifest, `after-install.md` contains post-install
instructions, `scripts/` contains local install and Gateway control helpers,
and `tests/` contains provider contract, recovery, and shutdown tests.

## Build, Test, and Development Commands

Use `scripts/install.sh` to symlink this checkout into
`~/.hermes/plugins/memory_tencentdb`. Add `--with-gateway` to install the
external Node Gateway runtime into `~/.memory-tencentdb/tdai-memory-openclaw-plugin`.
Run `python3 -m pytest` for the standard test suite. Run
`python3 -m py_compile __init__.py client.py supervisor.py tests/*.py` before
publishing to catch syntax errors. Validate shell scripts with
`bash -n scripts/install.sh` and `bash -n scripts/memory-tencentdb-ctl.sh`.

## Coding Style & Naming Conventions

Keep Python compatible with 3.10+. Use four-space indentation, type hints for
public helpers, and `snake_case` for functions, variables, and config keys.
Provider-facing classes use `PascalCase`; environment variables stay uppercase
and should preserve the existing `TDAI_*` and `MEMORY_TENCENTDB_*` names. Keep
the plugin root flat unless Hermes changes its user-plugin loader contract.

## Testing Guidelines

Tests use `pytest` plus `unittest` for lifecycle-heavy cases. Name new tests
`test_*.py` and prefer fake HTTP Gateways unless the behavior requires the real
Node Gateway. Real Gateway tests must remain opt-in behind
`TDAI_E2E_REAL_GATEWAY=1` and should accept `TDAI_INSTALL_DIR`.

## Commit & Pull Request Guidelines

Use short imperative commit messages, for example
`Document standalone plugin setup`. Pull requests should explain the Hermes
behavior changed, list validation commands run, and call out any Gateway
compatibility assumptions. Include screenshots only for UI-facing changes; this
plugin is normally CLI and agent-runtime focused.

## Architecture Notes

The plugin should stay a thin Hermes adapter. Do not duplicate Gateway memory
logic in Python. Local SQLite storage is the default path; Tencent Cloud
VectorDB support belongs in Gateway configuration and must remain optional.
