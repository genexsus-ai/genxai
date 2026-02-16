# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Documentation
- Documented OSS availability of enterprise-grade runtime features (connectors, triggers, observability, security, CLI extensions, worker queue engine) while keeping Studio enterprise-only.

## [0.1.6] - 2026-02-13
### Added
- LLM-based ranking utility with safe JSON parsing, repair logic, and heuristic fallback scoring.
- Opt-in agent config flag (`enable_llm_ranking`) and runtime tool ranking output (`tool_rankings`).
- Ranking utility tests covering valid JSON, repaired JSON, and heuristic fallback paths.
- Documentation updates and examples for LLM ranking usage and heuristic defaults.
