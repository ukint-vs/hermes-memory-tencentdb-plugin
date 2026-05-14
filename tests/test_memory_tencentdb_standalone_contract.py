"""Standalone Hermes plugin contract tests for memory-tencentdb."""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

_THIS_FILE = pathlib.Path(__file__).resolve()
_HERE = _THIS_FILE.parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_hermes_root = os.environ.get("HERMES_AGENT_ROOT")
if not _hermes_root:
    home_checkout = pathlib.Path.home() / ".hermes" / "hermes-agent"
    if (home_checkout / "agent").is_dir():
        _hermes_root = str(home_checkout)
if _hermes_root and _hermes_root not in sys.path:
    sys.path.insert(0, _hermes_root)

try:
    from memory_tencentdb import (
        MemoryTencentdbProvider,
        _discover_gateway_cmd,
        _resolve_gateway_host,
        _resolve_gateway_port,
    )
    from memory_tencentdb.supervisor import GatewaySupervisor
    from memory_tencentdb import supervisor as supervisor_module
except ImportError as e:  # pragma: no cover - environment-dependent
    pytest.skip(
        f"memory_tencentdb provider not importable ({e}); set HERMES_AGENT_ROOT "
        "to a hermes-agent checkout if running from the plugin repo.",
        allow_module_level=True,
    )


def test_config_schema_uses_config_yaml_for_non_secret_fields() -> None:
    schema = MemoryTencentdbProvider().get_config_schema()
    fields = {field["key"]: field for field in schema}
    env_by_key = {key: field.get("env_var") for key, field in fields.items()}

    assert env_by_key["tdai_install_dir"] is None
    assert env_by_key["gateway_cmd"] is None
    assert env_by_key["gateway_host"] is None
    assert env_by_key["gateway_port"] is None
    assert env_by_key["llm_api_key"] == "TDAI_LLM_API_KEY"
    assert env_by_key["llm_base_url"] is None
    assert env_by_key["llm_model"] is None
    assert fields["llm_api_key"]["required"] is False
    assert fields["llm_base_url"]["default"] == "https://openrouter.ai/api/v1"
    assert fields["llm_model"]["default"] == "deepseek/deepseek-v4-flash"


def test_save_config_writes_plugins_section(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "memory:\n  provider: memory_tencentdb\nplugins:\n  enabled:\n  - enzyme\n",
        encoding="utf-8",
    )

    MemoryTencentdbProvider().save_config(
        {
            "tdai_install_dir": "~/.memory-tencentdb/tdai-memory-openclaw-plugin",
            "gateway_host": "127.0.0.1",
            "gateway_port": "8420",
            "llm_base_url": "https://openrouter.ai/api/v1",
            "llm_model": "deepseek/deepseek-v4-flash",
            "llm_api_key": "must-not-be-written",
        },
        str(tmp_path),
    )

    import yaml

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    plugin_config = saved["plugins"]["memory-tencentdb"]

    assert saved["plugins"]["enabled"] == ["enzyme"]
    assert plugin_config["gateway_port"] == "8420"
    assert plugin_config["llm_model"] == "deepseek/deepseek-v4-flash"
    assert "llm_api_key" not in plugin_config


def test_env_overrides_plugin_config_for_runtime_values(monkeypatch) -> None:
    config = {"gateway_host": "configured-host", "gateway_port": "8420"}

    monkeypatch.setenv("MEMORY_TENCENTDB_GATEWAY_HOST", "127.0.0.2")
    monkeypatch.setenv("MEMORY_TENCENTDB_GATEWAY_PORT", "18420")

    assert _resolve_gateway_host(config) == "127.0.0.2"
    assert _resolve_gateway_port(config) == 18420


def test_gateway_auto_discovery_prefers_tdai_install_dir(tmp_path, monkeypatch) -> None:
    install_dir = tmp_path / "tdai install"
    gateway = install_dir / "src" / "gateway" / "server.ts"
    gateway.parent.mkdir(parents=True)
    gateway.write_text("// test gateway\n", encoding="utf-8")

    monkeypatch.setenv("TDAI_INSTALL_DIR", str(install_dir))

    cmd = _discover_gateway_cmd()

    assert cmd is not None
    assert "npx tsx src/gateway/server.ts" in cmd
    assert str(install_dir) in cmd
    assert MemoryTencentdbProvider().is_available() is True


def test_supervisor_bridges_provider_env_to_gateway_env(tmp_path, monkeypatch) -> None:
    captured = {}

    class FakeProcess:
        returncode = None

        def poll(self):
            return None

    def fake_popen(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs["env"]
        return FakeProcess()

    monkeypatch.setenv("MEMORY_TENCENTDB_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("TDAI_LLM_API_KEY", "tdai-key")
    monkeypatch.delenv("MEMORY_TENCENTDB_LLM_API_KEY", raising=False)
    monkeypatch.setattr(supervisor_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(GatewaySupervisor, "is_running", lambda self: False)
    monkeypatch.setattr(GatewaySupervisor, "_wait_for_health", lambda self: True)

    supervisor = GatewaySupervisor(
        host="127.0.0.1",
        port=18420,
        gateway_cmd="node fake-gateway.js",
    )

    assert supervisor.ensure_running() is True
    assert captured["env"]["MEMORY_TENCENTDB_GATEWAY_HOST"] == "127.0.0.1"
    assert captured["env"]["MEMORY_TENCENTDB_GATEWAY_PORT"] == "18420"
    assert captured["env"]["TDAI_GATEWAY_HOST"] == "127.0.0.1"
    assert captured["env"]["TDAI_GATEWAY_PORT"] == "18420"
    assert captured["env"]["TDAI_LLM_API_KEY"] == "tdai-key"
    assert captured["env"]["MEMORY_TENCENTDB_LLM_API_KEY"] == "tdai-key"


def test_supervisor_bridges_legacy_llm_env_to_gateway_env(tmp_path, monkeypatch) -> None:
    captured = {}

    class FakeProcess:
        returncode = None

        def poll(self):
            return None

    monkeypatch.setenv("MEMORY_TENCENTDB_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("MEMORY_TENCENTDB_LLM_API_KEY", "legacy-key")
    monkeypatch.delenv("TDAI_LLM_API_KEY", raising=False)
    monkeypatch.setattr(GatewaySupervisor, "is_running", lambda self: False)
    monkeypatch.setattr(GatewaySupervisor, "_wait_for_health", lambda self: True)

    def capture_popen(argv, **kwargs):
        captured["env"] = kwargs["env"]
        return FakeProcess()

    monkeypatch.setattr(supervisor_module.subprocess, "Popen", capture_popen)

    supervisor = GatewaySupervisor(
        host="127.0.0.1",
        port=18421,
        gateway_cmd="node fake-gateway.js",
    )

    assert supervisor.ensure_running() is True
    assert captured["env"]["TDAI_LLM_API_KEY"] == "legacy-key"
    assert captured["env"]["MEMORY_TENCENTDB_LLM_API_KEY"] == "legacy-key"
