# Licensing and Edition Boundaries

This repository contains the **MIT‑licensed GenXAI core framework**.

## OSS vs Enterprise Summary

- **OSS core (MIT)**: `genxai/`, `examples/`, `docs/`, `tests/`, `scripts/`
- **Enterprise (commercial)**: everything under `enterprise/` (Studio, CLI, connectors, triggers,
  security, observability, metrics)

## Open‑Source (MIT) Scope

The following paths are part of the OSS core and are licensed under **MIT**:

- `genxai/` (core graph/agent/runtime, tools, flows, llm)
- `examples/`
- `docs/`
- `tests/`
- `scripts/`
- Project root metadata (e.g., `pyproject.toml`, `README.md`, `LICENSE`)

## Enterprise (Commercial) Scope

The following paths are staged for the **enterprise repository** and are **not**
covered by the MIT license once extracted into the commercial repo:

- `enterprise/studio/` (Studio UI + backend)
- `enterprise/cli/`
- `enterprise/genxai/security/`
- `enterprise/genxai/observability/`
- `enterprise/genxai/connectors/`
- `enterprise/genxai/triggers/`

If additional enterprise modules are added later (e.g., SSO/RBAC, advanced audit,
compliance packs, proprietary connectors), they should live under `enterprise/`.

## Notes

- This file is informational and does not replace the official license texts.
- For the enterprise edition, use a commercial license (EULA) in the enterprise repo.