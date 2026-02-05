"""Episodic memory implementation for storing agent experiences."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import uuid

from genxai.core.memory.base import Memory, MemoryType
from genxai.core.memory.persistence import (
    JsonMemoryStore,
    MemoryPersistenceConfig,
    SqliteMemoryStore,
    create_memory_store,
)

logger = logging.getLogger(__name__)


class Episode:
    """Represents a single episode in agent's experience."""

    def __init__(
        self,
        id: str,
        agent_id: str,
        task: str,
        actions: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        timestamp: datetime,
        duration: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize episode.

        Args:
            id: Unique episode ID
            agent_id: ID of the agent
            task: Task description
            actions: List of actions taken
            outcome: Final outcome
            timestamp: When episode occurred
            duration: Duration in seconds
            success: Whether episode was successful
            metadata: Additional metadata
        """
        self.id = id
        self.agent_id = agent_id
        self.task = task
        self.actions = actions
        self.outcome = outcome
        self.timestamp = timestamp
        self.duration = duration
        self.success = success
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task": self.task,
            "actions": self.actions,
            "outcome": self.outcome,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "success": self.success,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        """Create episode from dictionary."""
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            task=data["task"],
            actions=data["actions"],
            outcome=data["outcome"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration=data["duration"],
            success=data["success"],
            metadata=data.get("metadata", {}),
        )


class EpisodicMemory:
    """Episodic memory for storing and retrieving agent experiences.
    
    Stores complete episodes of agent behavior including:
    - Tasks attempted
    - Actions taken
    - Outcomes achieved
    - Success/failure patterns
    """

    def __init__(
        self,
        graph_db: Optional[Any] = None,
        max_episodes: int = 1000,
        persistence: Optional[MemoryPersistenceConfig] = None,
    ) -> None:
        """Initialize episodic memory.

        Args:
            graph_db: Graph database client (Neo4j, etc.)
            max_episodes: Maximum number of episodes to store
        """
        self._graph_db = graph_db
        self._max_episodes = max_episodes
        self._use_graph = graph_db is not None
        self._persistence = persistence
        if persistence:
            self._store = create_memory_store(persistence)
        else:
            self._store = None
        
        # Fallback to in-memory storage
        self._episodes: Dict[str, Episode] = {}
        
        if self._use_graph:
            logger.info("Initialized episodic memory with graph database")
        else:
            logger.warning(
                "Graph database not provided. Using in-memory storage. "
                "Episodes will not persist across restarts."
            )

        if self._store and self._persistence and self._persistence.enabled:
            self._load_from_disk()

    async def store_episode(
        self,
        agent_id: str,
        task: str,
        actions: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        duration: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Episode:
        """Store a new episode.

        Args:
            agent_id: ID of the agent
            task: Task description
            actions: List of actions taken
            outcome: Final outcome
            duration: Duration in seconds
            success: Whether episode was successful
            metadata: Additional metadata

        Returns:
            Created episode
        """
        episode = Episode(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            task=task,
            actions=actions,
            outcome=outcome,
            timestamp=datetime.now(),
            duration=duration,
            success=success,
            metadata=metadata,
        )

        if self._use_graph:
            await self._store_in_graph(episode)
        else:
            # In-memory storage
            self._episodes[episode.id] = episode
            
            # Enforce max episodes limit
            if len(self._episodes) > self._max_episodes:
                # Remove oldest episode
                oldest_id = min(
                    self._episodes.keys(),
                    key=lambda k: self._episodes[k].timestamp
                )
                del self._episodes[oldest_id]

        self._persist()

        logger.debug(f"Stored episode {episode.id} for agent {agent_id}")
        return episode

    async def retrieve_episode(self, episode_id: str) -> Optional[Episode]:
        """Retrieve an episode by ID.

        Args:
            episode_id: Episode ID

        Returns:
            Episode if found, None otherwise
        """
        if self._use_graph:
            return await self._retrieve_from_graph(episode_id)
        
        return self._episodes.get(episode_id)

    async def retrieve_by_agent(
        self,
        agent_id: str,
        limit: int = 10,
        success_only: bool = False,
    ) -> List[Episode]:
        """Retrieve episodes for a specific agent.

        Args:
            agent_id: Agent ID
            limit: Maximum number of episodes
            success_only: Only return successful episodes

        Returns:
            List of episodes
        """
        if self._use_graph:
            return await self._retrieve_by_agent_from_graph(
                agent_id, limit, success_only
            )

        # In-memory retrieval
        episodes = [
            ep for ep in self._episodes.values()
            if ep.agent_id == agent_id
        ]

        if success_only:
            episodes = [ep for ep in episodes if ep.success]

        # Sort by timestamp (most recent first)
        episodes.sort(key=lambda ep: ep.timestamp, reverse=True)

        return episodes[:limit]

    async def retrieve_similar_tasks(
        self,
        task: str,
        limit: int = 5,
    ) -> List[Episode]:
        """Retrieve episodes with similar tasks.

        Args:
            task: Task description
            limit: Maximum number of episodes

        Returns:
            List of similar episodes
        """
        if self._use_graph:
            return await self._retrieve_similar_from_graph(task, limit)

        # Simple in-memory similarity (keyword matching)
        task_lower = task.lower()
        episodes = []

        for episode in self._episodes.values():
            if any(word in episode.task.lower() for word in task_lower.split()):
                episodes.append(episode)

        # Sort by success and recency
        episodes.sort(
            key=lambda ep: (ep.success, ep.timestamp),
            reverse=True
        )

        return episodes[:limit]

    async def get_success_rate(
        self,
        agent_id: Optional[str] = None,
        task_pattern: Optional[str] = None,
    ) -> float:
        """Calculate success rate for episodes.

        Args:
            agent_id: Filter by agent ID (optional)
            task_pattern: Filter by task pattern (optional)

        Returns:
            Success rate (0.0 to 1.0)
        """
        episodes = list(self._episodes.values())

        # Apply filters
        if agent_id:
            episodes = [ep for ep in episodes if ep.agent_id == agent_id]

        if task_pattern:
            pattern_lower = task_pattern.lower()
            episodes = [
                ep for ep in episodes
                if pattern_lower in ep.task.lower()
            ]

        if not episodes:
            return 0.0

        successful = sum(1 for ep in episodes if ep.success)
        return successful / len(episodes)

    async def get_patterns(
        self,
        agent_id: Optional[str] = None,
        min_occurrences: int = 3,
    ) -> List[Dict[str, Any]]:
        """Extract patterns from episodes.

        Args:
            agent_id: Filter by agent ID (optional)
            min_occurrences: Minimum occurrences to be considered a pattern

        Returns:
            List of patterns with statistics
        """
        episodes = list(self._episodes.values())

        if agent_id:
            episodes = [ep for ep in episodes if ep.agent_id == agent_id]

        # Group by task
        task_groups: Dict[str, List[Episode]] = {}
        for episode in episodes:
            task_key = episode.task.lower()
            if task_key not in task_groups:
                task_groups[task_key] = []
            task_groups[task_key].append(episode)

        # Extract patterns
        patterns = []
        for task, task_episodes in task_groups.items():
            if len(task_episodes) >= min_occurrences:
                successful = sum(1 for ep in task_episodes if ep.success)
                patterns.append({
                    "task": task,
                    "occurrences": len(task_episodes),
                    "success_rate": successful / len(task_episodes),
                    "avg_duration": sum(ep.duration for ep in task_episodes) / len(task_episodes),
                    "last_seen": max(ep.timestamp for ep in task_episodes).isoformat(),
                })

        # Sort by occurrences
        patterns.sort(key=lambda p: p["occurrences"], reverse=True)

        return patterns

    async def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear episodes.

        Args:
            agent_id: Clear only episodes for this agent (optional)
        """
        if agent_id:
            # Clear specific agent's episodes
            self._episodes = {
                k: v for k, v in self._episodes.items()
                if v.agent_id != agent_id
            }
            logger.info(f"Cleared episodes for agent {agent_id}")
        else:
            # Clear all episodes
            self._episodes.clear()
            logger.info("Cleared all episodes")

        self._persist()

    async def get_stats(self) -> Dict[str, Any]:
        """Get episodic memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._episodes:
            return {
                "total_episodes": 0,
                "backend": "graph" if self._use_graph else "in-memory",
                "persistence": bool(self._persistence and self._persistence.enabled),
            }

        episodes = list(self._episodes.values())
        successful = sum(1 for ep in episodes if ep.success)

        return {
            "total_episodes": len(episodes),
            "successful_episodes": successful,
            "failed_episodes": len(episodes) - successful,
            "success_rate": successful / len(episodes),
            "avg_duration": sum(ep.duration for ep in episodes) / len(episodes),
            "unique_agents": len(set(ep.agent_id for ep in episodes)),
            "oldest_episode": min(ep.timestamp for ep in episodes).isoformat(),
            "newest_episode": max(ep.timestamp for ep in episodes).isoformat(),
            "backend": "graph" if self._use_graph else "in-memory",
            "persistence": bool(self._persistence and self._persistence.enabled),
        }

    def _persist(self) -> None:
        if not self._store:
            return
        self._store.save_list("episodic_memory.json", [ep.to_dict() for ep in self._episodes.values()])

    def _load_from_disk(self) -> None:
        if not self._store:
            return
        data = self._store.load_list("episodic_memory.json")
        if not data:
            return
        self._episodes = {item["id"]: Episode.from_dict(item) for item in data}

    async def _store_in_graph(self, episode: Episode) -> None:
        """Store episode in graph database (placeholder)."""
        # TODO: Implement Neo4j storage
        logger.warning("Graph database storage not yet implemented")
        # Fallback to in-memory
        self._episodes[episode.id] = episode

    async def _retrieve_from_graph(self, episode_id: str) -> Optional[Episode]:
        """Retrieve episode from graph database (placeholder)."""
        # TODO: Implement Neo4j retrieval
        return self._episodes.get(episode_id)

    async def _retrieve_by_agent_from_graph(
        self,
        agent_id: str,
        limit: int,
        success_only: bool,
    ) -> List[Episode]:
        """Retrieve episodes from graph database (placeholder)."""
        # TODO: Implement Neo4j query
        return await self.retrieve_by_agent(agent_id, limit, success_only)

    async def _retrieve_similar_from_graph(
        self,
        task: str,
        limit: int,
    ) -> List[Episode]:
        """Retrieve similar episodes from graph database (placeholder)."""
        # TODO: Implement Neo4j similarity query
        return await self.retrieve_similar_tasks(task, limit)

    def __len__(self) -> int:
        """Get number of stored episodes."""
        return len(self._episodes)

    def __repr__(self) -> str:
        """String representation."""
        backend = "Graph" if self._use_graph else "In-Memory"
        return f"EpisodicMemory(backend={backend}, episodes={len(self._episodes)})"
