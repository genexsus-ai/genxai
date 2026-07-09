"""Unit tests for the reusable agent library."""

import pytest

from genxai.agents import (
    AGENT_LIBRARY,
    create_library_agent,
    export_library_yaml,
    library_agent_names,
    render_library_for_prompt,
    researcher,
)
from genxai.core.agent.config_io import import_agents_yaml


def test_every_library_agent_instantiates():
    names = library_agent_names()
    assert len(names) >= 12
    for name in names:
        agent = create_library_agent(name)
        assert agent.id == name
        assert agent.config.role
        assert agent.config.goal
        assert agent.config.backstory
        assert 0.0 <= agent.config.llm_temperature <= 1.0


def test_factory_functions_and_overrides():
    agent = researcher(
        id="market_researcher",
        goal="Research fintech competitors",
        tools=["web_scraper"],
        llm_temperature=0.2,
    )

    assert agent.id == "market_researcher"
    assert agent.config.goal == "Research fintech competitors"
    assert agent.config.tools == ["web_scraper"]
    assert agent.config.llm_temperature == 0.2
    # Non-overridden fields keep the library values.
    assert agent.config.role == AGENT_LIBRARY["researcher"]["role"]


def test_unknown_library_agent_raises():
    with pytest.raises(KeyError, match="Unknown library agent"):
        create_library_agent("time_traveler")


def test_yaml_export_roundtrips(tmp_path):
    path = export_library_yaml(tmp_path / "library_agents.yaml")

    agents = import_agents_yaml(path)

    assert {agent.id for agent in agents} == set(library_agent_names())
    loaded = next(agent for agent in agents if agent.id == "summarizer")
    assert loaded.config.role == AGENT_LIBRARY["summarizer"]["role"]


def test_render_library_for_prompt():
    rendered = render_library_for_prompt(["researcher", "editor"])

    assert "Research Specialist" in rendered
    assert "Editor and Critic" in rendered
    assert "Summarization Specialist" not in rendered
    assert "temperature 0.4" in rendered


@pytest.mark.asyncio
async def test_agent_designer_prompt_includes_library_exemplars(tmp_path):
    import json

    from genxai.builder.catalog import build_capability_catalog
    from genxai.builder.crew import run_agent_designer
    from genxai.builder.schemas import PlanStep, WorkflowPlan, WorkPacket
    from tests.utils.mock_llm import MockLLMProvider

    plan = WorkflowPlan(
        name="P",
        steps=[PlanStep(id="think", title="Thinker", description="Reason about input")],
    )
    packet = WorkPacket(id="p1", worker="agent_designer", objective="Design", step_ids=["think"])
    provider = MockLLMProvider(
        response_text=json.dumps(
            {"specs": [{"step_id": "think", "role": "R", "goal": "G", "tools": []}]}
        )
    )

    await run_agent_designer(packet, plan, build_capability_catalog(), llm_provider=provider)

    assert "Proven agent designs" in provider.prompts[0]
    assert "Research Specialist" in provider.prompts[0]
