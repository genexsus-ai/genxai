# OSS vs Enterprise Release Notes

This document outlines how to keep release pipelines separated between the
open‑source **GenXAI core** and the commercial **enterprise** edition.

## OSS Release Pipeline (MIT)

- **Repo**: `genxai` (this repo)
- **Package**: `genxai`
- **Contents**: `genxai/`, `cli/`, `docs/`, `examples/`, `tests/`
- **Publishing**: PyPI (public)

### Checklist

1. Ensure no `enterprise/` files are packaged or referenced by build scripts
2. Run unit tests + lint
3. Build and publish `genxai` to PyPI

## Enterprise Release Pipeline (Commercial)

- **Repo**: `genxai-enterprise` (private)
- **Package**: `genxai-enterprise` (or internal distribution)
- **Contents**: `studio/` + enterprise modules
- **Publishing**: Private registry or internal distribution

### Checklist

1. Ensure enterprise repo includes **commercial LICENSE/EULA**
2. Run Studio frontend/backend build and tests
3. Publish to private registry or deploy internally

## CI/CD Guardrails

- Enforce separate build jobs for OSS vs enterprise repos
- Block any CI job that tries to publish enterprise artifacts from OSS repo
- Keep secrets (enterprise keys, registries) in enterprise repo only