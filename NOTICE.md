# Notice

This repository contains a standalone Hermes adapter extracted and adapted from
the `memory_tencentdb` integration work around TencentDB Agent Memory.

Original upstream project:

<https://github.com/Tencent/TencentDB-Agent-Memory>

Runtime package:

<https://www.npmjs.com/package/@tencentdb-agent-memory/memory-tencentdb>

The Hermes plugin code is distributed under the MIT license included in
`LICENSE`. The external Node.js Gateway/core is not vendored in this repository;
install it from the upstream package or point `TDAI_INSTALL_DIR` at a compatible
source checkout.

Tencent Cloud VectorDB is optional. The default documented path uses the
Gateway local SQLite/JSONL backend.
