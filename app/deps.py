from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import Sensor
from app.security import hash_api_key

api_key_header = APIKeyHeader(name="X-API-Key")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Выдаёт сессию БД на время запроса и закрывает её после."""
    async with SessionLocal() as session:
        yield session


async def get_current_sensor(
    api_key: str = Depends(api_key_header),
    session: AsyncSession = Depends(get_session),
) -> Sensor:
    """Находит сенсор по ключу из заголовка X-API-Key."""
    key_hash = hash_api_key(api_key)
    result = await session.execute(
        select(Sensor).where(
            Sensor.api_key_hash == key_hash,
            Sensor.is_active.is_(True),
        )
    )
    sensor = result.scalars().first()
    if sensor is None:
        raise HTTPException(status_code=401, detail="Неверный или отключённый API-ключ")
    return sensor