"""Test import shim for running the plugin from its repository root."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_INIT_FILE = _REPO_ROOT / "__init__.py"

_hermes_root = os.environ.get("HERMES_AGENT_ROOT")
if not _hermes_root:
    home_checkout = pathlib.Path.home() / ".hermes" / "hermes-agent"
    if (home_checkout / "agent").is_dir():
        _hermes_root = str(home_checkout)
if _hermes_root and _hermes_root not in sys.path:
    sys.path.insert(0, _hermes_root)

if "memory_tencentdb" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "memory_tencentdb",
        _INIT_FILE,
        submodule_search_locations=[str(_REPO_ROOT)],
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["memory_tencentdb"] = module
        spec.loader.exec_module(module)
