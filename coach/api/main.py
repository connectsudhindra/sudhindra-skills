"""FastAPI entrypoint. Run directly (`uvicorn main:app`) or via
coach/docker-compose.yml's `api` service.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row

import config
import db
from routers import dashboard, health, levels, prompts, score, sessions, teams, users
from services.coaching import compose_end_of_session_summary
from services.level_engine import compute_session_level

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coach")


async def _sweep_stale_sessions() -> None:
    """Closes out sessions whose SessionEnd hook never fired -- a crash or
    force-quit shouldn't leave end-of-session coaching undelivered forever.
    Runs on a plain interval loop; this process is the only writer, so no
    locking is needed."""
    while True:
        await asyncio.sleep(config.SWEEP_INTERVAL_SECONDS)
        try:
            async with db.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        """
                        SELECT id, user_id FROM sessions
                        WHERE ended_at IS NULL
                          AND id IN (
                            SELECT session_id FROM prompts
                            GROUP BY session_id
                            HAVING max(submitted_at) < now() - (%s || ' minutes')::interval
                          )
                        """,
                        (config.STALE_SESSION_MINUTES,),
                    )
                    stale = await cur.fetchall()

                for row in stale:
                    session_id, user_id = row["id"], row["user_id"]
                    session_level = await compute_session_level(conn, session_id)
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "UPDATE sessions SET ended_at = now(), session_level = %s WHERE id = %s",
                            (session_level, session_id),
                        )
                        await cur.execute(
                            "SELECT coaching_mode FROM users WHERE id = %s", (user_id,)
                        )
                        (mode,) = await cur.fetchone()

                    if mode == "end_of_session":
                        summary = await compose_end_of_session_summary(conn, user_id, session_id)
                        if summary:
                            async with conn.cursor() as cur:
                                await cur.execute(
                                    "INSERT INTO coaching_feedback "
                                    "(session_id, user_id, feedback_type, feedback_text) "
                                    "VALUES (%s, %s, 'end_of_session', %s)",
                                    (session_id, user_id, summary),
                                )

                if stale:
                    logger.info("swept %d stale session(s)", len(stale))
        except Exception:  # noqa: BLE001 - the sweep must never crash the process
            logger.exception("stale-session sweep failed; will retry next interval")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.pool.open()
    sweep_task = asyncio.create_task(_sweep_stale_sessions())
    try:
        yield
    finally:
        sweep_task.cancel()
        await db.pool.close()


app = FastAPI(title="GCCF Prompt Coach", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(prompts.router)
app.include_router(score.router)
app.include_router(sessions.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(levels.router)
app.include_router(dashboard.router)
