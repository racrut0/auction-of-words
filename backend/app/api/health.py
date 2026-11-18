from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Liveness/readiness probe including a database round-trip."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
