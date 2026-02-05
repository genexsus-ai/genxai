"""Connection pooling for GenXAI performance optimization."""

import asyncio
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager, contextmanager
import queue
import threading


class ConnectionPool:
    """Generic connection pool."""
    
    def __init__(
        self,
        create_connection,
        min_size: int = 5,
        max_size: int = 20,
        timeout: float = 30.0
    ):
        """Initialize connection pool.
        
        Args:
            create_connection: Function to create new connection
            min_size: Minimum pool size
            max_size: Maximum pool size
            timeout: Connection timeout
        """
        self.create_connection = create_connection
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout
        
        self._pool = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize pool with minimum connections."""
        for _ in range(self.min_size):
            conn = await self.create_connection()
            await self._pool.put(conn)
            self._size += 1
    
    async def acquire(self):
        """Acquire connection from pool."""
        try:
            # Try to get existing connection
            conn = await asyncio.wait_for(
                self._pool.get(),
                timeout=self.timeout
            )
            return conn
        except asyncio.TimeoutError:
            # Create new connection if under max size
            async with self._lock:
                if self._size < self.max_size:
                    conn = await self.create_connection()
                    self._size += 1
                    return conn
            
            # Wait for available connection
            conn = await self._pool.get()
            return conn
    
    async def release(self, conn):
        """Release connection back to pool."""
        await self._pool.put(conn)
    
    async def close(self):
        """Close all connections."""
        while not self._pool.empty():
            conn = await self._pool.get()
            if hasattr(conn, 'close'):
                await conn.close()
        self._size = 0
    
    @asynccontextmanager
    async def connection(self):
        """Context manager for connection."""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)


class DatabaseConnectionPool:
    """Database connection pool."""
    
    def __init__(
        self,
        db_url: str,
        min_size: int = 5,
        max_size: int = 20
    ):
        """Initialize database connection pool.
        
        Args:
            db_url: Database URL
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.db_url = db_url
        self.min_size = min_size
        self.max_size = max_size
        self._pool = None
    
    async def initialize(self):
        """Initialize pool."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self.db_url,
                min_size=self.min_size,
                max_size=self.max_size
            )
        except ImportError:
            raise ImportError("asyncpg not installed. Install with: pip install asyncpg")
    
    @asynccontextmanager
    async def connection(self):
        """Get connection from pool."""
        async with self._pool.acquire() as conn:
            yield conn
    
    async def close(self):
        """Close pool."""
        if self._pool:
            await self._pool.close()


class HTTPConnectionPool:
    """HTTP connection pool using aiohttp."""
    
    def __init__(
        self,
        connector_limit: int = 100,
        connector_limit_per_host: int = 30
    ):
        """Initialize HTTP connection pool.
        
        Args:
            connector_limit: Total connection limit
            connector_limit_per_host: Per-host connection limit
        """
        self.connector_limit = connector_limit
        self.connector_limit_per_host = connector_limit_per_host
        self._session = None
    
    async def initialize(self):
        """Initialize session."""
        try:
            import aiohttp
            connector = aiohttp.TCPConnector(
                limit=self.connector_limit,
                limit_per_host=self.connector_limit_per_host
            )
            self._session = aiohttp.ClientSession(connector=connector)
        except ImportError:
            raise ImportError("aiohttp not installed. Install with: pip install aiohttp")
    
    async def get(self, url: str, **kwargs):
        """GET request."""
        async with self._session.get(url, **kwargs) as response:
            return await response.json()
    
    async def post(self, url: str, **kwargs):
        """POST request."""
        async with self._session.post(url, **kwargs) as response:
            return await response.json()
    
    async def close(self):
        """Close session."""
        if self._session:
            await self._session.close()


class VectorStoreConnectionPool:
    """Vector store connection pool."""
    
    def __init__(
        self,
        store_type: str,
        config: Dict[str, Any],
        pool_size: int = 10
    ):
        """Initialize vector store connection pool.
        
        Args:
            store_type: Vector store type (chromadb, pinecone, weaviate)
            config: Store configuration
            pool_size: Pool size
        """
        self.store_type = store_type
        self.config = config
        self.pool_size = pool_size
        self._connections = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
    
    def initialize(self):
        """Initialize pool."""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._connections.put(conn)
    
    def _create_connection(self):
        """Create vector store connection."""
        if self.store_type == "chromadb":
            import chromadb
            return chromadb.Client(self.config)
        elif self.store_type == "pinecone":
            import pinecone
            pinecone.init(**self.config)
            return pinecone
        elif self.store_type == "weaviate":
            import weaviate
            return weaviate.Client(**self.config)
        else:
            raise ValueError(f"Unknown store type: {self.store_type}")
    
    @contextmanager
    def connection(self):
        """Get connection from pool."""
        conn = self._connections.get(timeout=30)
        try:
            yield conn
        finally:
            self._connections.put(conn)
    
    def close(self):
        """Close all connections."""
        while not self._connections.empty():
            conn = self._connections.get()
            if hasattr(conn, 'close'):
                conn.close()


# Global pools
_db_pool = None
_http_pool = None
_vector_pool = None


async def get_db_pool() -> DatabaseConnectionPool:
    """Get global database pool."""
    global _db_pool
    
    if _db_pool is None:
        import os
        db_url = os.getenv("POSTGRES_URL", "postgresql://localhost/genxai")
        _db_pool = DatabaseConnectionPool(db_url)
        await _db_pool.initialize()
    
    return _db_pool


async def get_http_pool() -> HTTPConnectionPool:
    """Get global HTTP pool."""
    global _http_pool
    
    if _http_pool is None:
        _http_pool = HTTPConnectionPool()
        await _http_pool.initialize()
    
    return _http_pool


def get_vector_pool(store_type: str = "chromadb") -> VectorStoreConnectionPool:
    """Get global vector store pool."""
    global _vector_pool
    
    if _vector_pool is None:
        import os
        config = {}
        
        if store_type == "pinecone":
            config = {
                "api_key": os.getenv("PINECONE_API_KEY"),
                "environment": os.getenv("PINECONE_ENV", "us-west1-gcp")
            }
        elif store_type == "weaviate":
            config = {
                "url": os.getenv("WEAVIATE_URL", "http://localhost:8080")
            }
        
        _vector_pool = VectorStoreConnectionPool(store_type, config)
        _vector_pool.initialize()
    
    return _vector_pool
