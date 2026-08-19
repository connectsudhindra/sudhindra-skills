"""A single process-wide async connection pool, opened at startup and closed
at shutdown by main.py's lifespan handler. Routers pull a connection with
`async with db.pool.connection() as conn:` -- no per-router pool wiring.
"""
from __future__ import annotations

from psycopg_pool import AsyncConnectionPool

import config

pool: AsyncConnectionPool = AsyncConnectionPool(
    conninfo=config.DATABASE_URL,
    min_size=1,
    max_size=10,
    open=False,
    kwargs={"autocommit": True},
)
