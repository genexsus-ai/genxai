"""Semantic memory implementation for storing facts and knowledge."""

from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
import logging
import uuid

from genxai.core.memory.persistence import (
    JsonMemoryStore,
    MemoryPersistenceConfig,
    SqliteMemoryStore,
    create_memory_store,
)

logger = logging.getLogger(__name__)


class Fact:
    """Represents a single fact in semantic memory."""

    def __init__(
        self,
        id: str,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize fact.

        Args:
            id: Unique fact ID
            subject: Subject entity
            predicate: Relationship/property
            object: Object entity/value
            confidence: Confidence score (0.0 to 1.0)
            source: Source of the fact
            timestamp: When fact was learned
            metadata: Additional metadata
        """
        self.id = id
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.confidence = confidence
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_triple(self) -> Tuple[str, str, str]:
        """Convert to RDF-style triple."""
        return (self.subject, self.predicate, self.object)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fact":
        """Create fact from dictionary."""
        return cls(
            id=data["id"],
            subject=data["subject"],
            predicate=data["predicate"],
            object=data["object"],
            confidence=data.get("confidence", 1.0),
            source=data.get("source"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Fact({self.subject} {self.predicate} {self.object})"


class SemanticMemory:
    """Semantic memory for storing facts and knowledge.
    
    Stores structured knowledge as subject-predicate-object triples:
    - Facts about entities
    - Relationships between entities
    - Properties and attributes
    - General knowledge
    """

    def __init__(
        self,
        graph_db: Optional[Any] = None,
        persistence: Optional[MemoryPersistenceConfig] = None,
    ) -> None:
        """Initialize semantic memory.

        Args:
            graph_db: Graph database client (Neo4j, etc.)
        """
        self._graph_db = graph_db
        self._use_graph = graph_db is not None
        self._persistence = persistence
        if persistence:
            self._store = create_memory_store(persistence)
        else:
            self._store = None
        
        # Fallback to in-memory storage
        self._facts: Dict[str, Fact] = {}
        self._subject_index: Dict[str, Set[str]] = {}  # subject -> fact_ids
        self._predicate_index: Dict[str, Set[str]] = {}  # predicate -> fact_ids
        self._object_index: Dict[str, Set[str]] = {}  # object -> fact_ids
        
        if self._use_graph:
            logger.info("Initialized semantic memory with graph database")
        else:
            logger.warning(
                "Graph database not provided. Using in-memory storage. "
                "Facts will not persist across restarts."
            )

        if self._store and self._persistence and self._persistence.enabled:
            self._load_from_disk()

    async def store_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Fact:
        """Store a new fact.

        Args:
            subject: Subject entity
            predicate: Relationship/property
            object: Object entity/value
            confidence: Confidence score
            source: Source of the fact
            metadata: Additional metadata

        Returns:
            Created fact
        """
        # Check if fact already exists
        existing = await self._find_exact_fact(subject, predicate, object)
        if existing:
            # Update confidence if higher
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.timestamp = datetime.now()
                logger.debug(f"Updated fact confidence: {existing}")
            return existing

        # Create new fact
        fact = Fact(
            id=str(uuid.uuid4()),
            subject=subject,
            predicate=predicate,
            object=object,
            confidence=confidence,
            source=source,
            metadata=metadata,
        )

        if self._use_graph:
            await self._store_in_graph(fact)
        else:
            # In-memory storage
            self._facts[fact.id] = fact
            
            # Update indexes
            if subject not in self._subject_index:
                self._subject_index[subject] = set()
            self._subject_index[subject].add(fact.id)
            
            if predicate not in self._predicate_index:
                self._predicate_index[predicate] = set()
            self._predicate_index[predicate].add(fact.id)
            
            if object not in self._object_index:
                self._object_index[object] = set()
            self._object_index[object].add(fact.id)

        self._persist()

        logger.debug(f"Stored fact: {fact}")
        return fact

    async def retrieve_by_subject(
        self,
        subject: str,
        predicate: Optional[str] = None,
    ) -> List[Fact]:
        """Retrieve facts about a subject.

        Args:
            subject: Subject entity
            predicate: Optional predicate filter

        Returns:
            List of facts
        """
        if self._use_graph:
            return await self._retrieve_by_subject_from_graph(subject, predicate)

        # In-memory retrieval
        fact_ids = self._subject_index.get(subject, set())
        facts = [self._facts[fid] for fid in fact_ids]

        if predicate:
            facts = [f for f in facts if f.predicate == predicate]

        return facts

    async def retrieve_by_predicate(
        self,
        predicate: str,
        subject: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Fact]:
        """Retrieve facts with a specific predicate.

        Args:
            predicate: Predicate/relationship
            subject: Optional subject filter
            object: Optional object filter

        Returns:
            List of facts
        """
        if self._use_graph:
            return await self._retrieve_by_predicate_from_graph(
                predicate, subject, object
            )

        # In-memory retrieval
        fact_ids = self._predicate_index.get(predicate, set())
        facts = [self._facts[fid] for fid in fact_ids]

        if subject:
            facts = [f for f in facts if f.subject == subject]
        if object:
            facts = [f for f in facts if f.object == object]

        return facts

    async def retrieve_by_object(
        self,
        object: str,
        predicate: Optional[str] = None,
    ) -> List[Fact]:
        """Retrieve facts with a specific object.

        Args:
            object: Object entity/value
            predicate: Optional predicate filter

        Returns:
            List of facts
        """
        if self._use_graph:
            return await self._retrieve_by_object_from_graph(object, predicate)

        # In-memory retrieval
        fact_ids = self._object_index.get(object, set())
        facts = [self._facts[fid] for fid in fact_ids]

        if predicate:
            facts = [f for f in facts if f.predicate == predicate]

        return facts

    async def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[Fact]:
        """Query facts with flexible filters.

        Args:
            subject: Optional subject filter
            predicate: Optional predicate filter
            object: Optional object filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching facts
        """
        facts = list(self._facts.values())

        # Apply filters
        if subject:
            facts = [f for f in facts if f.subject == subject]
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        if object:
            facts = [f for f in facts if f.object == object]
        if min_confidence > 0.0:
            facts = [f for f in facts if f.confidence >= min_confidence]

        return facts

    async def get_related_entities(
        self,
        entity: str,
        max_depth: int = 2,
    ) -> Set[str]:
        """Get entities related to a given entity.

        Args:
            entity: Starting entity
            max_depth: Maximum relationship depth

        Returns:
            Set of related entities
        """
        related = set()
        to_explore = {entity}
        explored = set()

        for _ in range(max_depth):
            if not to_explore:
                break

            current = to_explore.pop()
            explored.add(current)

            # Get facts where entity is subject
            subject_facts = await self.retrieve_by_subject(current)
            for fact in subject_facts:
                related.add(fact.object)
                if fact.object not in explored:
                    to_explore.add(fact.object)

            # Get facts where entity is object
            object_facts = await self.retrieve_by_object(current)
            for fact in object_facts:
                related.add(fact.subject)
                if fact.subject not in explored:
                    to_explore.add(fact.subject)

        return related - {entity}

    async def get_entity_properties(
        self,
        entity: str,
    ) -> Dict[str, Any]:
        """Get all properties of an entity.

        Args:
            entity: Entity to get properties for

        Returns:
            Dictionary of properties
        """
        facts = await self.retrieve_by_subject(entity)
        
        properties = {}
        for fact in facts:
            if fact.predicate not in properties:
                properties[fact.predicate] = []
            properties[fact.predicate].append({
                "value": fact.object,
                "confidence": fact.confidence,
                "source": fact.source,
            })

        return properties

    async def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact by ID.

        Args:
            fact_id: Fact ID

        Returns:
            True if deleted, False if not found
        """
        if fact_id not in self._facts:
            return False

        fact = self._facts[fact_id]

        # Remove from indexes
        self._subject_index[fact.subject].discard(fact_id)
        self._predicate_index[fact.predicate].discard(fact_id)
        self._object_index[fact.object].discard(fact_id)

        # Remove fact
        del self._facts[fact_id]

        self._persist()

        logger.debug(f"Deleted fact: {fact}")
        return True

    async def clear(self) -> None:
        """Clear all facts."""
        self._facts.clear()
        self._subject_index.clear()
        self._predicate_index.clear()
        self._object_index.clear()
        logger.info("Cleared all facts")

        self._persist()

    async def get_stats(self) -> Dict[str, Any]:
        """Get semantic memory statistics.

        Returns:
            Statistics dictionary
        """
        if not self._facts:
            return {
                "total_facts": 0,
                "backend": "graph" if self._use_graph else "in-memory",
                "persistence": bool(self._persistence and self._persistence.enabled),
            }

        facts = list(self._facts.values())

        return {
            "total_facts": len(facts),
            "unique_subjects": len(self._subject_index),
            "unique_predicates": len(self._predicate_index),
            "unique_objects": len(self._object_index),
            "avg_confidence": sum(f.confidence for f in facts) / len(facts),
            "oldest_fact": min(f.timestamp for f in facts).isoformat(),
            "newest_fact": max(f.timestamp for f in facts).isoformat(),
            "backend": "graph" if self._use_graph else "in-memory",
            "persistence": bool(self._persistence and self._persistence.enabled),
        }

    def _persist(self) -> None:
        if not self._store:
            return
        self._store.save_list("semantic_memory.json", [fact.to_dict() for fact in self._facts.values()])

    def _load_from_disk(self) -> None:
        if not self._store:
            return
        data = self._store.load_list("semantic_memory.json")
        if not data:
            return
        self._facts = {}
        self._subject_index = {}
        self._predicate_index = {}
        self._object_index = {}
        for item in data:
            fact = Fact.from_dict(item)
            self._facts[fact.id] = fact
            self._subject_index.setdefault(fact.subject, set()).add(fact.id)
            self._predicate_index.setdefault(fact.predicate, set()).add(fact.id)
            self._object_index.setdefault(fact.object, set()).add(fact.id)

    def _materialize_fact(self, fact: Fact) -> None:
        self._facts[fact.id] = fact
        self._subject_index.setdefault(fact.subject, set()).add(fact.id)
        self._predicate_index.setdefault(fact.predicate, set()).add(fact.id)
        self._object_index.setdefault(fact.object, set()).add(fact.id)

    def _decode_metadata(self, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
                return decoded if isinstance(decoded, dict) else {}
            except Exception:
                return {}
        return value if isinstance(value, dict) else {}

    def _fact_from_graph_payload(self, payload: Dict[str, Any]) -> Fact:
        return Fact(
            id=str(payload.get("id", "")),
            subject=str(payload.get("subject", "")),
            predicate=str(payload.get("predicate", "")),
            object=str(payload.get("object", "")),
            confidence=float(payload.get("confidence", 1.0)),
            source=payload.get("source"),
            timestamp=datetime.fromisoformat(str(payload.get("timestamp"))) if payload.get("timestamp") else None,
            metadata=self._decode_metadata(payload.get("metadata_json")),
        )

    def _records_to_facts(self, records: Any) -> List[Fact]:
        facts: List[Fact] = []
        for record in records:
            if isinstance(record, dict):
                node = record.get("f") or record
            else:
                try:
                    node = record.get("f")
                except Exception:
                    node = None
            if not node:
                continue
            payload = dict(node)
            try:
                fact = self._fact_from_graph_payload(payload)
            except Exception:
                continue
            self._materialize_fact(fact)
            facts.append(fact)
        return facts

    async def _find_exact_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
    ) -> Optional[Fact]:
        """Find exact matching fact."""
        for fact in self._facts.values():
            if (fact.subject == subject and 
                fact.predicate == predicate and 
                fact.object == object):
                return fact
        return None

    async def _store_in_graph(self, fact: Fact) -> None:
        """Store fact in graph database."""
        try:
            query = """
            MERGE (f:Fact {id: $id})
            SET f.subject = $subject,
                f.predicate = $predicate,
                f.object = $object,
                f.confidence = $confidence,
                f.source = $source,
                f.timestamp = $timestamp,
                f.metadata_json = $metadata_json
            """
            with self._graph_db.session() as session:
                session.run(
                    query,
                    id=fact.id,
                    subject=fact.subject,
                    predicate=fact.predicate,
                    object=fact.object,
                    confidence=fact.confidence,
                    source=fact.source,
                    timestamp=fact.timestamp.isoformat(),
                    metadata_json=json.dumps(fact.metadata, default=str),
                )
        except Exception as exc:
            logger.warning("Failed graph fact storage, fallback to in-memory: %s", exc)

        self._materialize_fact(fact)

    async def _retrieve_by_subject_from_graph(
        self,
        subject: str,
        predicate: Optional[str],
    ) -> List[Fact]:
        """Retrieve facts by subject from graph database."""
        try:
            query = """
            MATCH (f:Fact {subject: $subject})
            WHERE ($predicate IS NULL OR f.predicate = $predicate)
            RETURN f
            """
            with self._graph_db.session() as session:
                records = list(session.run(query, subject=subject, predicate=predicate))
            return self._records_to_facts(records)
        except Exception as exc:
            logger.warning("Failed graph subject query, fallback to in-memory: %s", exc)

        fact_ids = self._subject_index.get(subject, set())
        facts = [self._facts[fid] for fid in fact_ids]
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        return facts

    async def _retrieve_by_predicate_from_graph(
        self,
        predicate: str,
        subject: Optional[str],
        object: Optional[str],
    ) -> List[Fact]:
        """Retrieve facts by predicate from graph database."""
        try:
            query = """
            MATCH (f:Fact {predicate: $predicate})
            WHERE ($subject IS NULL OR f.subject = $subject)
              AND ($object IS NULL OR f.object = $object)
            RETURN f
            """
            with self._graph_db.session() as session:
                records = list(
                    session.run(
                        query,
                        predicate=predicate,
                        subject=subject,
                        object=object,
                    )
                )
            return self._records_to_facts(records)
        except Exception as exc:
            logger.warning("Failed graph predicate query, fallback to in-memory: %s", exc)

        fact_ids = self._predicate_index.get(predicate, set())
        facts = [self._facts[fid] for fid in fact_ids]
        if subject:
            facts = [f for f in facts if f.subject == subject]
        if object:
            facts = [f for f in facts if f.object == object]
        return facts

    async def _retrieve_by_object_from_graph(
        self,
        object: str,
        predicate: Optional[str],
    ) -> List[Fact]:
        """Retrieve facts by object from graph database."""
        try:
            query = """
            MATCH (f:Fact {object: $object})
            WHERE ($predicate IS NULL OR f.predicate = $predicate)
            RETURN f
            """
            with self._graph_db.session() as session:
                records = list(session.run(query, object=object, predicate=predicate))
            return self._records_to_facts(records)
        except Exception as exc:
            logger.warning("Failed graph object query, fallback to in-memory: %s", exc)

        fact_ids = self._object_index.get(object, set())
        facts = [self._facts[fid] for fid in fact_ids]
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        return facts

    def __len__(self) -> int:
        """Get number of stored facts."""
        return len(self._facts)

    def __repr__(self) -> str:
        """String representation."""
        backend = "Graph" if self._use_graph else "In-Memory"
        return f"SemanticMemory(backend={backend}, facts={len(self._facts)})"
