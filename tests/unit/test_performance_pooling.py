"""Unit tests for connection pooling utilities."""

import asyncio

import pytest

from genxai.performance.pooling import ConnectionPool


@pytest.mark.asyncio
async def test_connection_pool_acquire_release() -> None:
    created = []

    async def create_connection():
        conn = {"id": len(created)}
        created.append(conn)
        return conn

    pool = ConnectionPool(create_connection=create_connection, min_size=1, max_size=2)
    await pool.initialize()

    conn = await pool.acquire()
    assert conn in created
    await pool.release(conn)

    async with pool.connection() as ctx_conn:
        assert ctx_conn in created

    await pool.close()
