#!/usr/bin/env bash
set -euo pipefail

# Install this repository as a Hermes user memory plugin.
#
# By default this links this repository into:
#   $HERMES_HOME/plugins/memory_tencentdb
#
# Pass --with-gateway to also install the Node Gateway/core runtime from npm
# into $TDAI_INSTALL_DIR. The Gateway remains an external runtime dependency;
# this repository intentionally contains only the Hermes adapter.

PLUGIN_NAME="memory_tencentdb"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_SRC="$REPO_ROOT"

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_DST="$HERMES_HOME/plugins/$PLUGIN_NAME"
MEMORY_TENCENTDB_ROOT="${MEMORY_TENCENTDB_ROOT:-$HOME/.memory-tencentdb}"
TDAI_INSTALL_DIR="${TDAI_INSTALL_DIR:-$MEMORY_TENCENTDB_ROOT/tdai-memory-openclaw-plugin}"
NPM_PACKAGE="${NPM_PACKAGE:-@tencentdb-agent-memory/memory-tencentdb@latest}"

WITH_GATEWAY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-gateway) WITH_GATEWAY=1; shift ;;
    -h|--help)
      cat <<EOF
Usage: scripts/install.sh [--with-gateway]

Environment:
  HERMES_HOME              default: $HOME/.hermes
  MEMORY_TENCENTDB_ROOT    default: $HOME/.memory-tencentdb
  TDAI_INSTALL_DIR         default: \$MEMORY_TENCENTDB_ROOT/tdai-memory-openclaw-plugin
  NPM_PACKAGE              default: @tencentdb-agent-memory/memory-tencentdb@latest
EOF
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$PLUGIN_SRC/__init__.py" || ! -f "$PLUGIN_SRC/plugin.yaml" ]]; then
  echo "Plugin source is incomplete: $PLUGIN_SRC" >&2
  exit 1
fi

mkdir -p "$HERMES_HOME/plugins"
if [[ -e "$PLUGIN_DST" && ! -L "$PLUGIN_DST" ]]; then
  echo "Refusing to replace non-symlink plugin directory: $PLUGIN_DST" >&2
  echo "Move it aside first, or install manually." >&2
  exit 1
fi

ln -sfn "$PLUGIN_SRC" "$PLUGIN_DST"
echo "Linked Hermes plugin: $PLUGIN_DST -> $PLUGIN_SRC"

if [[ "$WITH_GATEWAY" -eq 1 ]]; then
  command -v npm >/dev/null 2>&1 || {
    echo "npm is required for --with-gateway" >&2
    exit 127
  }

  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT

  echo "Installing Gateway runtime from $NPM_PACKAGE ..."
  npm install --prefix "$tmp" "$NPM_PACKAGE" --omit=dev --package-lock=false

  pkg_dir="$tmp/node_modules/@tencentdb-agent-memory/memory-tencentdb"
  if [[ ! -f "$pkg_dir/src/gateway/server.ts" ]]; then
    echo "Downloaded package does not contain src/gateway/server.ts: $pkg_dir" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$TDAI_INSTALL_DIR")"
  rm -rf "$TDAI_INSTALL_DIR"
  mkdir -p "$TDAI_INSTALL_DIR"
  cp -R "$pkg_dir"/. "$TDAI_INSTALL_DIR"/
  (cd "$TDAI_INSTALL_DIR" && npm install --omit=dev --package-lock=false)
  echo "Installed Gateway runtime: $TDAI_INSTALL_DIR"
fi

cat <<EOF

Next steps:
  1. Set Hermes memory provider in $HERMES_HOME/config.yaml:

       memory:
         provider: memory_tencentdb

  2. Configure the Gateway LLM endpoint in the Hermes process environment,
     for example in $HERMES_HOME/.env:

       TDAI_LLM_BASE_URL=https://openrouter.ai/api/v1
       TDAI_LLM_API_KEY=<openrouter-key>
       TDAI_LLM_MODEL=deepseek/deepseek-v4-flash

  3. Ensure the Gateway runtime is installed at:

       $TDAI_INSTALL_DIR

     If not, rerun this installer with --with-gateway or set
     MEMORY_TENCENTDB_GATEWAY_CMD to an explicit server command.
EOF
