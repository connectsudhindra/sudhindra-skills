from fastapi import APIRouter

import db

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    try:
        async with db.pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()
        return {"status": "healthy", "database": "up"}
    except Exception as exc:  # noqa: BLE001 - health check reports, never raises
        return {"status": "unhealthy", "database": "down", "detail": str(exc)}
