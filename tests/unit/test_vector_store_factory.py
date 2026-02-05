"""Unit tests for vector store factory."""

from genxai.core.memory.vector_store import VectorStore, VectorStoreFactory


class DummyVectorStore(VectorStore):
    async def store(self, memory, embedding):
        return None

    async def search(self, query_embedding, limit=10, filters=None):
        return []

    async def delete(self, memory_id: str) -> bool:
        return True

    async def clear(self) -> None:
        return None

    async def get_stats(self):
        return {"backend": "dummy"}


def test_vector_store_factory_register_and_create() -> None:
    VectorStoreFactory.register("dummy", DummyVectorStore)
    store = VectorStoreFactory.create("dummy")
    assert isinstance(store, DummyVectorStore)
    assert "dummy" in VectorStoreFactory.list_backends()
