"""Leveling policy: turns a user's recent heuristic scores into a level.

Deliberately reads only the heuristic score (see scoring/heuristic.py) --
it's synchronous and deterministic, so a user's level never depends on LLM
availability, latency, or cost. The LLM score is comparison-only.
"""
from __future__ import annotations

from dataclasses import dataclass

from psycopg import AsyncConnection

import config


@dataclass(frozen=True)
class LevelResult:
    level_num: int
    level_name: str
    rolling_composite: float | None
    leveled_up: bool


async def recompute_user_level(conn: AsyncConnection, user_id: str) -> LevelResult:
    """Call after inserting a new heuristic prompt_scores row, inside the same
    request. Sticky upward-only: a low-scoring stretch never demotes
    `users.current_level`; it only slows or halts further level-ups."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT ps.composite_score
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            WHERE p.user_id = %s AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
            ORDER BY p.submitted_at DESC
            LIMIT %s
            """,
            (user_id, config.ROLLING_WINDOW_SIZE),
        )
        rows = await cur.fetchall()

        await cur.execute("SELECT current_level FROM users WHERE id = %s", (user_id,))
        (current_level,) = await cur.fetchone()

        if len(rows) < config.MIN_SCORABLE_PROMPTS_TO_LEVEL:
            await cur.execute(
                "SELECT name FROM levels WHERE level_num = %s", (current_level,)
            )
            (name,) = await cur.fetchone()
            rolling = round(sum(r[0] for r in rows) / len(rows), 2) if rows else None
            return LevelResult(current_level, name, rolling, leveled_up=False)

        rolling_composite = round(sum(r[0] for r in rows) / len(rows), 2)

        await cur.execute(
            """
            SELECT level_num, name FROM levels
            WHERE min_score <= %s
            ORDER BY level_num DESC
            LIMIT 1
            """,
            (rolling_composite,),
        )
        earned_level, earned_name = await cur.fetchone()

        # Sticky upward-only: never move current_level down.
        new_level = max(current_level, earned_level)
        leveled_up = new_level > current_level

        if leveled_up:
            await cur.execute(
                "UPDATE users SET current_level = %s, updated_at = now() WHERE id = %s",
                (new_level, user_id),
            )
            await cur.execute(
                "INSERT INTO level_history (user_id, level_num) VALUES (%s, %s)",
                (user_id, new_level),
            )
            await cur.execute("SELECT name FROM levels WHERE level_num = %s", (new_level,))
            (new_name,) = await cur.fetchone()
        else:
            new_name = earned_name if new_level == earned_level else None
            if new_name is None:
                await cur.execute("SELECT name FROM levels WHERE level_num = %s", (new_level,))
                (new_name,) = await cur.fetchone()

        return LevelResult(new_level, new_name, rolling_composite, leveled_up)


async def compute_session_level(conn: AsyncConnection, session_id: str) -> int | None:
    """Independent of `users.current_level` -- captures how *this session alone*
    scored, so a dip is still visible per-session even though the user's
    overall badge never demotes."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT ps.composite_score
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            WHERE p.session_id = %s AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
            """,
            (session_id,),
        )
        rows = await cur.fetchall()
        if not rows:
            return None

        avg = sum(r[0] for r in rows) / len(rows)
        await cur.execute(
            "SELECT level_num FROM levels WHERE min_score <= %s ORDER BY level_num DESC LIMIT 1",
            (avg,),
        )
        row = await cur.fetchone()
        return row[0] if row else 1
