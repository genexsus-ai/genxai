"""Seed Studio database with agents from YAML files."""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio.backend.services.db import init_db, execute, fetch_one, json_dumps
from genxai.core.agent.config_io import import_agents_yaml


def seed_agents_from_yaml(yaml_path: Path) -> int:
    """Import agents from a YAML file into the Studio database.
    
    Returns the number of agents imported.
    """
    import yaml
    
    # Load YAML directly and parse agent data
    data = yaml.safe_load(yaml_path.read_text())
    if not isinstance(data, dict) or "agents" not in data:
        raise ValueError("Invalid YAML format for agents list")
    
    agents_data = data["agents"]
    if not isinstance(agents_data, list):
        raise ValueError("Invalid YAML format for agents list")
    
    count = 0
    
    for agent_data in agents_data:
        agent_id = agent_data.get("id")
        if not agent_id:
            print(f"  ✗ Skipping agent without id")
            continue
        
        # Extract agent fields
        role = agent_data.get("role", "Agent")
        goal = agent_data.get("goal", "Process tasks")
        backstory = agent_data.get("backstory", "")
        llm_model = agent_data.get("llm_model") or agent_data.get("llm") or "gpt-4"
        tools = agent_data.get("tools", [])
        
        # Build metadata from additional fields
        metadata = agent_data.get("metadata", {})
        if "llm_provider" in agent_data:
            metadata["llm_provider"] = agent_data["llm_provider"]
        if "llm_temperature" in agent_data:
            metadata["llm_temperature"] = agent_data["llm_temperature"]
        if "memory" in agent_data:
            metadata["memory"] = agent_data["memory"]
        if "behavior" in agent_data:
            metadata["behavior"] = agent_data["behavior"]
        
        # Check if agent already exists
        existing = fetch_one("SELECT id FROM agents WHERE id = ?", (agent_id,))
        
        if existing:
            # Update existing agent
            execute(
                """
                UPDATE agents
                SET role = ?, goal = ?, backstory = ?, llm_model = ?, tools = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    role,
                    goal,
                    backstory,
                    llm_model,
                    json_dumps(tools),
                    json_dumps(metadata),
                    agent_id,
                ),
            )
            print(f"✓ Updated agent: {agent_id} ({role})")
        else:
            # Insert new agent
            execute(
                """
                INSERT INTO agents (id, role, goal, backstory, llm_model, tools, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    role,
                    goal,
                    backstory,
                    llm_model,
                    json_dumps(tools),
                    json_dumps(metadata),
                ),
            )
            print(f"✓ Created agent: {agent_id} ({role})")
        
        count += 1
    
    return count


def main():
    """Seed all agents from examples/nocode/agents/ directory."""
    # Initialize database
    init_db()
    print("Database initialized.\n")
    
    # Get agents directory
    agents_dir = Path(__file__).resolve().parent.parent / "examples" / "nocode" / "agents"
    
    if not agents_dir.exists():
        print(f"Error: Agents directory not found: {agents_dir}")
        sys.exit(1)
    
    # Find all YAML files
    yaml_files = list(agents_dir.glob("*.yaml"))
    
    if not yaml_files:
        print(f"No YAML files found in {agents_dir}")
        sys.exit(1)
    
    print(f"Found {len(yaml_files)} agent definition files:\n")
    
    total_count = 0
    for yaml_file in sorted(yaml_files):
        print(f"Processing {yaml_file.name}...")
        try:
            count = seed_agents_from_yaml(yaml_file)
            total_count += count
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
        print()
    
    print(f"✓ Successfully seeded {total_count} agents into Studio database.")
    print(f"  Database location: {Path(__file__).resolve().parent.parent / 'studio' / 'backend' / 'genxai_studio.db'}")


if __name__ == "__main__":
    main()
