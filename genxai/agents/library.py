"""Curated library of reusable role agents.

Battle-tested agent definitions — tuned role, goal, backstory, temperature,
agent type, and default tools — for the roles most workflows need. Use them
three ways:

- Python: ``from genxai.agents import researcher; agent = researcher(tools=["web_scraper"])``
- YAML: ``export_library_yaml(path)`` writes an ``agents_ref``-compatible
  file for no-code workflow definitions
- Generation: ``render_library_for_prompt()`` feeds the definitions to the
  crew's agent designer as quality exemplars

Every factory accepts overrides, so the library is a starting point, not a
cage: ``researcher(id="market_researcher", goal="Research fintech rivals")``.

Default tools reference built-in tool names; they apply when those tools are
registered in the runtime's ToolRegistry and are otherwise inert.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genxai.core.agent.base import Agent, AgentFactory

AGENT_LIBRARY: dict[str, dict[str, Any]] = {
    "researcher": {
        "role": "Research Specialist",
        "goal": "Gather accurate, current, well-sourced information on the topic",
        "backstory": (
            "A meticulous investigator who cross-checks every claim against "
            "multiple sources and always cites where facts came from."
        ),
        "llm_temperature": 0.4,
        "agent_type": "deliberative",
        "tools": ["web_scraper", "http_client", "rss_reader"],
    },
    "summarizer": {
        "role": "Summarization Specialist",
        "goal": "Distill the input into its essential points without losing meaning",
        "backstory": (
            "A veteran editor of executive briefings who ruthlessly cuts filler "
            "while preserving every decision-relevant fact."
        ),
        "llm_temperature": 0.3,
        "tools": [],
    },
    "writer": {
        "role": "Content Writer",
        "goal": "Produce clear, engaging prose tailored to the requested audience and format",
        "backstory": (
            "A professional writer fluent in many formats — articles, emails, "
            "reports — who adapts tone to the audience and never pads."
        ),
        "llm_temperature": 0.7,
        "tools": [],
    },
    "editor": {
        "role": "Editor and Critic",
        "goal": "Critique drafts against the brief and demand concrete, actionable fixes",
        "backstory": (
            "An exacting editor who approves nothing that misses the brief, "
            "and whose feedback always names the problem and the fix."
        ),
        "llm_temperature": 0.2,
        "agent_type": "deliberative",
        "tools": [],
    },
    "classifier": {
        "role": "Classification Specialist",
        "goal": "Assign the input to exactly one of the given categories with a confidence note",
        "backstory": (
            "A precise triage specialist who always answers with a category "
            "label first and keeps justifications to one sentence."
        ),
        "llm_temperature": 0.1,
        "tools": [],
    },
    "extractor": {
        "role": "Data Extraction Specialist",
        "goal": "Pull the requested fields out of unstructured input as clean structured data",
        "backstory": (
            "A careful parser who returns exactly the requested fields, marks "
            "missing values explicitly, and never invents data."
        ),
        "llm_temperature": 0.1,
        "tools": ["text_analyzer", "json_processor"],
    },
    "data_analyst": {
        "role": "Data Analyst",
        "goal": "Analyze the data and surface the trends, outliers, and takeaways that matter",
        "backstory": (
            "A data scientist who shows the numbers behind every claim and "
            "flags uncertainty rather than hiding it."
        ),
        "llm_temperature": 0.2,
        "agent_type": "deliberative",
        "tools": ["csv_processor", "json_processor", "calculator", "data_transformer"],
    },
    "translator": {
        "role": "Translator",
        "goal": "Translate the input faithfully, preserving tone, register, and formatting",
        "backstory": (
            "A professional translator who favors natural phrasing in the "
            "target language over word-for-word literalism."
        ),
        "llm_temperature": 0.3,
        "tools": [],
    },
    "qa_reviewer": {
        "role": "Quality Reviewer",
        "goal": "Verify the work meets every stated requirement and list any gaps found",
        "backstory": (
            "A QA lead who checks deliverables item by item against the "
            "requirements and reports pass/fail with evidence."
        ),
        "llm_temperature": 0.2,
        "agent_type": "deliberative",
        "tools": [],
    },
    "task_planner": {
        "role": "Task Planner",
        "goal": "Break the objective into ordered, unambiguous steps with clear dependencies",
        "backstory": (
            "A project lead who decomposes fuzzy goals into concrete tasks, "
            "each with an owner-ready definition of done."
        ),
        "llm_temperature": 0.3,
        "agent_type": "deliberative",
        "tools": [],
    },
    "support_responder": {
        "role": "Support Responder",
        "goal": "Resolve the customer's issue with an accurate, empathetic, actionable reply",
        "backstory": (
            "A senior support engineer who answers the actual question, links "
            "the fix, and never blames the customer."
        ),
        "llm_temperature": 0.4,
        "tools": [],
    },
    "escalation_handler": {
        "role": "Escalation Handler",
        "goal": "Summarize the urgent issue with impact, evidence, and a recommended next action",
        "backstory": (
            "An incident commander who writes escalations a responder can act "
            "on in sixty seconds: what broke, who is affected, what to do."
        ),
        "llm_temperature": 0.3,
        "tools": [],
    },
}


def library_agent_names() -> list[str]:
    """Names of all library agents."""
    return sorted(AGENT_LIBRARY)


def create_library_agent(name: str, id: str | None = None, **overrides: Any) -> Agent:
    """Instantiate a library agent, optionally overriding any config field."""
    if name not in AGENT_LIBRARY:
        raise KeyError(
            f"Unknown library agent '{name}'. Available: {', '.join(library_agent_names())}"
        )
    config = {**AGENT_LIBRARY[name], **overrides}
    return AgentFactory.create_agent(id=id or name, **config)


def researcher(id: str = "researcher", **overrides: Any) -> Agent:
    return create_library_agent("researcher", id=id, **overrides)


def summarizer(id: str = "summarizer", **overrides: Any) -> Agent:
    return create_library_agent("summarizer", id=id, **overrides)


def writer(id: str = "writer", **overrides: Any) -> Agent:
    return create_library_agent("writer", id=id, **overrides)


def editor(id: str = "editor", **overrides: Any) -> Agent:
    return create_library_agent("editor", id=id, **overrides)


def classifier(id: str = "classifier", **overrides: Any) -> Agent:
    return create_library_agent("classifier", id=id, **overrides)


def extractor(id: str = "extractor", **overrides: Any) -> Agent:
    return create_library_agent("extractor", id=id, **overrides)


def data_analyst(id: str = "data_analyst", **overrides: Any) -> Agent:
    return create_library_agent("data_analyst", id=id, **overrides)


def translator(id: str = "translator", **overrides: Any) -> Agent:
    return create_library_agent("translator", id=id, **overrides)


def qa_reviewer(id: str = "qa_reviewer", **overrides: Any) -> Agent:
    return create_library_agent("qa_reviewer", id=id, **overrides)


def task_planner(id: str = "task_planner", **overrides: Any) -> Agent:
    return create_library_agent("task_planner", id=id, **overrides)


def support_responder(id: str = "support_responder", **overrides: Any) -> Agent:
    return create_library_agent("support_responder", id=id, **overrides)


def escalation_handler(id: str = "escalation_handler", **overrides: Any) -> Agent:
    return create_library_agent("escalation_handler", id=id, **overrides)


def export_library_yaml(path: str | Path) -> Path:
    """Write the library as an ``agents_ref``-compatible YAML file."""
    from genxai.core.agent.config_io import export_agents_yaml

    target = Path(path)
    export_agents_yaml([create_library_agent(name) for name in library_agent_names()], target)
    return target


def render_library_for_prompt(names: list[str] | None = None) -> str:
    """Render library agents as design exemplars for LLM prompts."""
    selected = names or library_agent_names()
    lines = ["Proven agent designs to draw on (match this level of specificity):"]
    for name in selected:
        spec = AGENT_LIBRARY[name]
        lines.append(
            f"- {spec['role']} (temperature {spec['llm_temperature']}): "
            f"goal: {spec['goal']}; backstory: {spec['backstory']}"
        )
    return "\n".join(lines)
