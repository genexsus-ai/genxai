# Licensing and Edition Boundaries

This repository contains the **MIT‑licensed GenXAI core framework**.

## OSS vs Enterprise Summary

- **OSS core (MIT)**: everything in this repository — `genxai/` (including
  connectors, triggers, security, and observability), `applications/`,
  `examples/`, `docs/`, `tests/`, `scripts/`
  - Includes the OSS CLI at `genxai/cli`
- **Enterprise (commercial)**: the Studio UI and Studio-only assets, planned
  for a separate commercial repository. No enterprise code is included in
  this repository.

## Open‑Source (MIT) Scope

The following paths are part of the OSS core and are licensed under **MIT**:

- `genxai/` (core graph/agent/runtime, tools, flows, llm, connectors,
  triggers, security, observability, CLI)
- `applications/`
- `examples/`
- `docs/`
- `tests/`
- `scripts/`
- Project root metadata (e.g., `pyproject.toml`, `README.md`, `LICENSE`)

## Enterprise (Commercial) Scope

The following are **planned** for a separate commercial repository and will
**not** be covered by the MIT license:

- Studio UI + backend (visual workflow builder)
- Enterprise-only CLI command groups
- Any future enterprise modules (e.g., SSO, compliance packs, proprietary
  connectors)

None of these exist in this repository today.

## Notes

- This file is informational and does not replace the official license texts.
- For the enterprise edition, use a commercial license (EULA) in the enterprise repo.
