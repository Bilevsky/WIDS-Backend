import time

from app.config import settings
from app.redis_client import redis

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

async def rate_limited_sensor(sensor: Sensor = Depends(get_current_sensor)) -> Sensor:
    """Проверяет ключ и не пускает сенсор, который шлет слишком много запросов."""
    window = int(time.time() // 60)  # номер текущей минуты
    key = f"ratelimit:sensor:{sensor.id}:{window}"

    count = await redis.incr(key)  # +1 к счетчику
    if count == 1:
        await redis.expire(key, 60)  # через минуту ключ сам исчезнет

    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Слишком много запросов, попробуйте позже",
            headers={"Retry-After": "60"},
        )
    return sensor