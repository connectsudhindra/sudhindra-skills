"""Get-or-create helpers for users and sessions. Both prompts.py and
sessions.py need "find this user/session, or create it on first sight" --
factored here once rather than duplicated in each router.
"""
from __future__ import annotations

from psycopg import AsyncConnection


async def get_or_create_user(conn: AsyncConnection, email: str, name: str | None) -> str:
    async with conn.cursor() as cur:
        await cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        row = await cur.fetchone()
        if row:
            return str(row[0])

        await cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (name or email.split("@")[0], email),
        )
        (user_id,) = await cur.fetchone()
        return str(user_id)


async def get_or_create_session(
    conn: AsyncConnection, user_id: str, claude_session_id: str
) -> str:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT id FROM sessions WHERE user_id = %s AND claude_session_id = %s",
            (user_id, claude_session_id),
        )
        row = await cur.fetchone()
        if row:
            return str(row[0])

        await cur.execute(
            "INSERT INTO sessions (user_id, claude_session_id) VALUES (%s, %s) RETURNING id",
            (user_id, claude_session_id),
        )
        (session_id,) = await cur.fetchone()
        return str(session_id)
