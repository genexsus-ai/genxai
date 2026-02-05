"""Procedural memory implementation for storing learned skills and procedures."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import uuid

from genxai.core.memory.persistence import JsonMemoryStore, MemoryPersistenceConfig

logger = logging.getLogger(__name__)


class Procedure:
    """Represents a learned procedure or skill."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
        success_count: int = 0,
        failure_count: int = 0,
        avg_duration: float = 0.0,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize procedure.

        Args:
            id: Unique procedure ID
            name: Procedure name
            description: Description of what the procedure does
            steps: List of steps to execute
            preconditions: Conditions that must be true before execution
            postconditions: Expected conditions after execution
            success_count: Number of successful executions
            failure_count: Number of failed executions
            avg_duration: Average execution duration
            timestamp: When procedure was learned
            metadata: Additional metadata
        """
        self.id = id
        self.name = name
        self.description = description
        self.steps = steps
        self.preconditions = preconditions or []
        self.postconditions = postconditions or []
        self.success_count = success_count
        self.failure_count = failure_count
        self.avg_duration = avg_duration
        self.timestamp = timestamp or datetime.now()
        self.last_used = timestamp or datetime.now()
        self.metadata = metadata or {}

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    @property
    def total_executions(self) -> int:
        """Get total number of executions."""
        return self.success_count + self.failure_count

    def record_execution(
        self,
        success: bool,
        duration: float,
    ) -> None:
        """Record an execution of this procedure.

        Args:
            success: Whether execution was successful
            duration: Execution duration in seconds
        """
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        # Update average duration
        total = self.total_executions
        self.avg_duration = (
            (self.avg_duration * (total - 1) + duration) / total
        )

        self.last_used = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "avg_duration": self.avg_duration,
            "timestamp": self.timestamp.isoformat(),
            "last_used": self.last_used.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Procedure":
        """Create procedure from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            steps=data["steps"],
            preconditions=data.get("preconditions", []),
            postconditions=data.get("postconditions", []),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            avg_duration=data.get("avg_duration", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Procedure({self.name}, success_rate={self.success_rate:.2f})"


class ProceduralMemory:
    """Procedural memory for storing and retrieving learned procedures.
    
    Stores:
    - Step-by-step procedures
    - Learned skills
    - Execution statistics
    - Success/failure patterns
    """

    def __init__(
        self,
        max_procedures: int = 100,
        persistence: Optional[MemoryPersistenceConfig] = None,
    ) -> None:
        """Initialize procedural memory.

        Args:
            max_procedures: Maximum number of procedures to store
        """
        self._max_procedures = max_procedures
        self._procedures: Dict[str, Procedure] = {}
        self._name_index: Dict[str, str] = {}  # name -> procedure_id
        self._persistence = persistence
        self._store = JsonMemoryStore(persistence) if persistence else None

        if self._store and self._persistence and self._persistence.enabled:
            self._load_from_disk()
        
        logger.info("Initialized procedural memory")

    async def store_procedure(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Procedure:
        """Store a new procedure.

        Args:
            name: Procedure name
            description: Description
            steps: List of steps
            preconditions: Required preconditions
            postconditions: Expected postconditions
            metadata: Additional metadata

        Returns:
            Created procedure
        """
        # Check if procedure with same name exists
        if name in self._name_index:
            existing_id = self._name_index[name]
            existing = self._procedures[existing_id]
            logger.debug(f"Procedure '{name}' already exists, updating...")
            
            # Update existing procedure
            existing.description = description
            existing.steps = steps
            existing.preconditions = preconditions or []
            existing.postconditions = postconditions or []
            existing.metadata = metadata or {}
            existing.timestamp = datetime.now()
            
            return existing

        # Create new procedure
        procedure = Procedure(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            steps=steps,
            preconditions=preconditions,
            postconditions=postconditions,
            metadata=metadata,
        )

        # Store procedure
        self._procedures[procedure.id] = procedure
        self._name_index[name] = procedure.id

        # Enforce max procedures limit
        if len(self._procedures) > self._max_procedures:
            # Remove least successful procedure
            least_successful = min(
                self._procedures.values(),
                key=lambda p: (p.success_rate, p.total_executions)
            )
            await self.delete_procedure(least_successful.id)

        logger.debug(f"Stored procedure: {procedure}")
        self._persist()
        return procedure

    async def retrieve_procedure(
        self,
        procedure_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Procedure]:
        """Retrieve a procedure by ID or name.

        Args:
            procedure_id: Procedure ID
            name: Procedure name

        Returns:
            Procedure if found, None otherwise
        """
        if procedure_id:
            return self._procedures.get(procedure_id)
        
        if name and name in self._name_index:
            procedure_id = self._name_index[name]
            return self._procedures.get(procedure_id)
        
        return None

    async def retrieve_all(
        self,
        min_success_rate: float = 0.0,
        sort_by: str = "success_rate",
    ) -> List[Procedure]:
        """Retrieve all procedures.

        Args:
            min_success_rate: Minimum success rate filter
            sort_by: Sort key ("success_rate", "executions", "recent")

        Returns:
            List of procedures
        """
        procedures = list(self._procedures.values())

        # Filter by success rate
        if min_success_rate > 0.0:
            procedures = [
                p for p in procedures
                if p.success_rate >= min_success_rate
            ]

        # Sort
        if sort_by == "success_rate":
            procedures.sort(key=lambda p: p.success_rate, reverse=True)
        elif sort_by == "executions":
            procedures.sort(key=lambda p: p.total_executions, reverse=True)
        elif sort_by == "recent":
            procedures.sort(key=lambda p: p.last_used, reverse=True)

        return procedures

    async def search_procedures(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Procedure]:
        """Search procedures by name or description.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching procedures
        """
        query_lower = query.lower()
        matches = []

        for procedure in self._procedures.values():
            # Check name and description
            if (query_lower in procedure.name.lower() or
                query_lower in procedure.description.lower()):
                matches.append(procedure)

        # Sort by success rate
        matches.sort(key=lambda p: p.success_rate, reverse=True)

        return matches[:limit]

    async def record_execution(
        self,
        procedure_id: str,
        success: bool,
        duration: float,
    ) -> bool:
        """Record an execution of a procedure.

        Args:
            procedure_id: Procedure ID
            success: Whether execution was successful
            duration: Execution duration

        Returns:
            True if recorded, False if procedure not found
        """
        procedure = self._procedures.get(procedure_id)
        if not procedure:
            return False

        procedure.record_execution(success, duration)
        self._persist()
        logger.debug(
            f"Recorded execution for {procedure.name}: "
            f"success={success}, duration={duration:.2f}s"
        )
        return True

    async def get_best_procedures(
        self,
        limit: int = 10,
        min_executions: int = 3,
    ) -> List[Procedure]:
        """Get best performing procedures.

        Args:
            limit: Maximum number of procedures
            min_executions: Minimum number of executions required

        Returns:
            List of best procedures
        """
        procedures = [
            p for p in self._procedures.values()
            if p.total_executions >= min_executions
        ]

        # Sort by success rate, then by executions
        procedures.sort(
            key=lambda p: (p.success_rate, p.total_executions),
            reverse=True
        )

        return procedures[:limit]

    async def delete_procedure(self, procedure_id: str) -> bool:
        """Delete a procedure.

        Args:
            procedure_id: Procedure ID

        Returns:
            True if deleted, False if not found
        """
        if procedure_id not in self._procedures:
            return False

        procedure = self._procedures[procedure_id]
        
        # Remove from indexes
        if procedure.name in self._name_index:
            del self._name_index[procedure.name]
        
        # Remove procedure
        del self._procedures[procedure_id]

        self._persist()

        logger.debug(f"Deleted procedure: {procedure}")
        return True

    async def clear(self) -> None:
        """Clear all procedures."""
        self._procedures.clear()
        self._name_index.clear()
        logger.info("Cleared all procedures")

        self._persist()

    async def get_stats(self) -> Dict[str, Any]:
        """Get procedural memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._procedures:
            return {
                "total_procedures": 0,
                "persistence": bool(self._persistence and self._persistence.enabled),
            }

        procedures = list(self._procedures.values())
        
        total_executions = sum(p.total_executions for p in procedures)
        total_successes = sum(p.success_count for p in procedures)

        return {
            "total_procedures": len(procedures),
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_failures": total_executions - total_successes,
            "overall_success_rate": total_successes / total_executions if total_executions > 0 else 0.0,
            "avg_success_rate": sum(p.success_rate for p in procedures) / len(procedures),
            "most_used": max(procedures, key=lambda p: p.total_executions).name,
            "most_successful": max(procedures, key=lambda p: p.success_rate).name,
            "oldest_procedure": min(p.timestamp for p in procedures).isoformat(),
            "newest_procedure": max(p.timestamp for p in procedures).isoformat(),
            "persistence": bool(self._persistence and self._persistence.enabled),
        }

    def _persist(self) -> None:
        if not self._store:
            return
        payload = {
            "procedures": [proc.to_dict() for proc in self._procedures.values()],
            "name_index": self._name_index,
        }
        self._store.save_mapping("procedural_memory.json", payload)

    def _load_from_disk(self) -> None:
        if not self._store:
            return
        data = self._store.load_mapping("procedural_memory.json")
        if not data:
            return
        procedures = data.get("procedures", [])
        self._procedures = {proc["id"]: Procedure.from_dict(proc) for proc in procedures}
        self._name_index = data.get("name_index", {})

    def __len__(self) -> int:
        """Get number of stored procedures."""
        return len(self._procedures)

    def __repr__(self) -> str:
        """String representation."""
        return f"ProceduralMemory(procedures={len(self._procedures)})"
