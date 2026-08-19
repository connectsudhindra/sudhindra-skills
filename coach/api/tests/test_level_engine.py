"""Integration tests for services/level_engine.py -- these need a live
Postgres with the schema applied (docker compose up postgres). Skipped
automatically if DATABASE_URL isn't reachable, so `pytest` still passes in
an environment with no Docker available; run `docker compose up -d postgres`
first to actually exercise this file.
"""
import os
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

import config  # noqa: E402
from services.level_engine import recompute_user_level  # noqa: E402


def _db_reachable() -> bool:
    try:
        with psycopg.connect(config.DATABASE_URL, connect_timeout=2):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_reachable(), reason="DATABASE_URL not reachable -- run `docker compose up -d postgres`"
)


@pytest_asyncio.fixture
async def conn():
    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL, autocommit=True) as c:
        yield c


@pytest_asyncio.fixture
async def test_user(conn):
    email = f"test-{uuid.uuid4()}@example.com"
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO users (name, email) VALUES ('Test User', %s) RETURNING id", (email,)
        )
        (user_id,) = await cur.fetchone()
        await cur.execute(
            "INSERT INTO sessions (user_id, claude_session_id) VALUES (%s, 'test-session') RETURNING id",
            (user_id,),
        )
        (session_id,) = await cur.fetchone()
    yield str(user_id), str(session_id)
    async with conn.cursor() as cur:
        # Respect FK order: prompt_scores -> prompts -> sessions/level_history -> users.
        await cur.execute(
            "DELETE FROM prompt_scores WHERE prompt_id IN (SELECT id FROM prompts WHERE user_id = %s)",
            (user_id,),
        )
        await cur.execute("DELETE FROM prompts WHERE user_id = %s", (user_id,))
        await cur.execute("DELETE FROM level_history WHERE user_id = %s", (user_id,))
        await cur.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
        await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


async def _insert_scored_prompt(conn, user_id: str, session_id: str, composite: float) -> None:
    """composite is a target average -- gives every dimension the same value
    so composite_score works out to exactly `composite`."""
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO prompts (session_id, user_id, prompt_text) VALUES (%s, %s, 'test') RETURNING id",
            (session_id, user_id),
        )
        (prompt_id,) = await cur.fetchone()
        await cur.execute(
            "INSERT INTO prompt_scores "
            "(prompt_id, scoring_method, goal_score, context_score, constraints_score, format_score) "
            "VALUES (%s, 'heuristic', %s, %s, %s, %s)",
            (prompt_id, composite, composite, composite, composite),
        )


@pytest.mark.asyncio
async def test_stays_at_level_1_below_minimum_prompt_count(conn, test_user):
    user_id, session_id = test_user
    for _ in range(3):  # fewer than MIN_SCORABLE_PROMPTS_TO_LEVEL
        await _insert_scored_prompt(conn, user_id, session_id, 95.0)

    result = await recompute_user_level(conn, user_id)
    assert result.level_num == 1
    assert result.leveled_up is False


@pytest.mark.asyncio
async def test_levels_up_once_minimum_prompts_and_score_reached(conn, test_user):
    user_id, session_id = test_user
    for _ in range(config.MIN_SCORABLE_PROMPTS_TO_LEVEL):
        await _insert_scored_prompt(conn, user_id, session_id, 70.0)  # Delegator threshold is 65

    result = await recompute_user_level(conn, user_id)
    assert result.level_num == 3
    assert result.level_name == "Delegator"
    assert result.leveled_up is True


@pytest.mark.asyncio
async def test_level_is_sticky_upward_only(conn, test_user):
    user_id, session_id = test_user
    for _ in range(config.MIN_SCORABLE_PROMPTS_TO_LEVEL):
        await _insert_scored_prompt(conn, user_id, session_id, 96.0)  # Architect threshold is 92
    first = await recompute_user_level(conn, user_id)
    assert first.level_num == 5

    # A sharp drop in recent scores must not demote the badge.
    for _ in range(config.ROLLING_WINDOW_SIZE):
        await _insert_scored_prompt(conn, user_id, session_id, 10.0)
    second = await recompute_user_level(conn, user_id)

    assert second.level_num == 5
    assert second.leveled_up is False
