"""Capability catalog: the grounded inventory the planner crew may use.

Aggregates what the framework can actually execute — registered tools and
flow patterns, plus caller-injected sections (e.g. the Workflow Studio's
connector catalog, MCP tools, or node palette) — into one object that renders
as compact prompt context and validates capability names in generated plans.
"""

from __future__ import annotations

import re
import textwrap
from typing import Any

from pydantic import BaseModel, Field

from genxai.flows import FLOW_TYPES
from genxai.tools.registry import ToolRegistry

# One-line guidance per flow pattern, mirroring genxai/flows docstrings.
_FLOW_DESCRIPTIONS: dict[str, str] = {
    "round_robin": "Agents take turns responding in a fixed order.",
    "parallel": "All agents work on the task concurrently.",
    "auction": "Each agent bids on the task; the highest bidder executes it.",
    "coordinator_worker": "First agent plans the work; the rest execute it in parallel.",
    "critic_review": "First agent drafts, second critiques; loops until accepted.",
    "delegator_worker": (
        "First agent routes typed work packets to the other agents by worker "
        "tag; packets run in dependency waves."
    ),
    "ensemble_voting": "All agents answer independently; the majority answer wins.",
    "map_reduce": "All agents but the last work in parallel; the last combines results.",
    "p2p": "Agents exchange messages peer-to-peer until convergence.",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _relevance(request_tokens: set[str], entry: CapabilityEntry) -> float:
    """Token overlap between a request and an entry's name + description."""
    entry_tokens = _tokens(f"{entry.name} {entry.description}")
    if not request_tokens or not entry_tokens:
        return 0.0
    return len(request_tokens & entry_tokens) / len(request_tokens)


class CapabilityEntry(BaseModel):
    """One usable capability (tool, flow pattern, connector action, ...)."""

    name: str
    kind: str = Field(..., description="Section kind: tool, flow, connector, mcp, ...")
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_prompt_line(self) -> str:
        """Render as one compact line for LLM prompt context."""
        params = ", ".join(
            f"{name}*" if name in self.required else name for name in self.parameters
        )
        suffix = f" — params: {params}" if params else ""
        description = " ".join(self.description.split()) or "(no description)"
        return f"- {self.name}: {description}{suffix}"


class CapabilityCatalog(BaseModel):
    """Sections of capabilities, renderable as prompt context."""

    sections: dict[str, list[CapabilityEntry]] = Field(default_factory=dict)

    def names(self, kind: str | None = None) -> set[str]:
        """All capability names, optionally restricted to one section."""
        result: set[str] = set()
        for section, entries in self.sections.items():
            if kind and section != kind:
                continue
            result.update(entry.name for entry in entries)
        return result

    def unknown_capabilities(self, requested: set[str] | list[str]) -> set[str]:
        """Requested capability names that do not exist in the catalog."""
        return set(requested) - self.names()

    def to_prompt_context(
        self,
        max_chars: int | None = None,
        *,
        request: str | None = None,
        section_limit: int | None = None,
    ) -> str:
        """Render the catalog as compact text for planner/worker prompts.

        With ``request`` and ``section_limit``, oversized sections show only
        the entries most relevant to the request (token-overlap ranking) so
        prompt size stays flat as the catalog grows — grounding via
        :meth:`names` still sees the full catalog. With ``max_chars``, the
        final text is truncated with a note so the model knows the inventory
        is partial.
        """
        request_tokens = _tokens(request) if request else set()
        blocks: list[str] = []
        for section, entries in self.sections.items():
            shown = entries
            header = f"## Available {section} capabilities ({len(entries)})"
            if request_tokens and section_limit is not None and len(entries) > section_limit:
                ranked = sorted(
                    entries,
                    key=lambda entry: (-_relevance(request_tokens, entry), entry.name),
                )
                shown = sorted(ranked[:section_limit], key=lambda entry: entry.name)
                header = (
                    f"## Available {section} capabilities "
                    f"(showing the {section_limit} of {len(entries)} most relevant)"
                )
            lines = [header]
            lines.extend(entry.to_prompt_line() for entry in shown)
            blocks.append("\n".join(lines))
        text = "\n\n".join(blocks)

        if max_chars is not None and len(text) > max_chars:
            truncated = text[:max_chars]
            cut = truncated.rfind("\n")
            if cut > 0:
                truncated = truncated[:cut]
            text = truncated + "\n(... catalog truncated; more capabilities exist)"
        return text

    def summary(self) -> dict[str, int]:
        """Entry counts per section."""
        return {section: len(entries) for section, entries in self.sections.items()}


def _tool_entries() -> list[CapabilityEntry]:
    bundle = ToolRegistry.export_schema_bundle()
    entries: list[CapabilityEntry] = []
    for schema in bundle.get("tools", []):
        parameters = schema.get("parameters", {})
        entries.append(
            CapabilityEntry(
                name=schema.get("name", ""),
                kind="tool",
                description=schema.get("description", ""),
                parameters=parameters.get("properties", {}),
                required=parameters.get("required", []),
                metadata={"category": schema.get("category", "")},
            )
        )
    return sorted(entries, key=lambda entry: entry.name)


def _flow_entries() -> list[CapabilityEntry]:
    entries: list[CapabilityEntry] = []
    for name, flow_cls in FLOW_TYPES.items():
        description = _FLOW_DESCRIPTIONS.get(name) or textwrap.shorten(
            (flow_cls.__doc__ or "").strip(), width=120
        )
        entries.append(CapabilityEntry(name=name, kind="flow", description=description))
    return sorted(entries, key=lambda entry: entry.name)


def build_capability_catalog(
    *,
    include_tools: bool = True,
    include_flows: bool = True,
    extra_sections: dict[str, list[dict[str, Any]]] | None = None,
) -> CapabilityCatalog:
    """Build the catalog from the live registries plus caller-provided sections.

    ``extra_sections`` maps a section name (e.g. "connector", "mcp") to entry
    dicts accepted by :class:`CapabilityEntry` — this is how applications such
    as the Workflow Studio inject their connector/MCP/node inventories without
    the library importing application code.
    """
    sections: dict[str, list[CapabilityEntry]] = {}
    if include_tools:
        sections["tool"] = _tool_entries()
    if include_flows:
        sections["flow"] = _flow_entries()
    for section, entries in (extra_sections or {}).items():
        sections[section] = [
            (
                CapabilityEntry(kind=section, **entry)
                if "kind" not in entry
                else CapabilityEntry(**entry)
            )
            for entry in entries
        ]
    return CapabilityCatalog(sections=sections)
