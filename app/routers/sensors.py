from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_sensor, get_session
from app.models import Sensor
from app.schemas import SensorCreate, SensorCreated, SensorRead, SensorUpdate
from app.security import generate_api_key, hash_api_key

router = APIRouter(prefix="/sensors", tags=["sensors"])


async def get_sensor_or_404(session: AsyncSession, sensor_id: int) -> Sensor:
    sensor = await session.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Сенсор не найден")
    return sensor


@router.post("", response_model=SensorCreated, status_code=201)
async def create_sensor(data: SensorCreate, session: AsyncSession = Depends(get_session)):
    api_key = generate_api_key()
    sensor = Sensor(
        name=data.name,
        x=data.x,
        y=data.y,
        api_key_hash=hash_api_key(api_key),
    )
    session.add(sensor)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Сенсор с таким именем уже существует")
    await session.refresh(sensor)
    # Ключ показывается только сейчас, потом его восстановить нельзя
    return SensorCreated(**SensorRead.model_validate(sensor).model_dump(), api_key=api_key)


@router.get("", response_model=list[SensorRead])
async def list_sensors(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Sensor).order_by(Sensor.id))
    return result.scalars().all()


# ВАЖНО: /me должен стоять ВЫШЕ /{sensor_id}, иначе me примется за id
@router.get("/me", response_model=SensorRead)
async def read_me(sensor: Sensor = Depends(get_current_sensor)):
    """Проверка ключа: сенсор спрашивает «кто я?»."""
    return sensor


@router.get("/{sensor_id}", response_model=SensorRead)
async def get_sensor(sensor_id: int, session: AsyncSession = Depends(get_session)):
    return await get_sensor_or_404(session, sensor_id)


@router.patch("/{sensor_id}", response_model=SensorRead)
async def update_sensor(
    sensor_id: int, data: SensorUpdate, session: AsyncSession = Depends(get_session)
):
    sensor = await get_sensor_or_404(session, sensor_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sensor, field, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Сенсор с таким именем уже существует")
    await session.refresh(sensor)
    return sensor


@router.post("/{sensor_id}/rotate-key", response_model=SensorCreated)
async def rotate_key(sensor_id: int, session: AsyncSession = Depends(get_session)):
    """Выдать сенсору новый ключ (старый перестаёт работать)."""
    sensor = await get_sensor_or_404(session, sensor_id)
    api_key = generate_api_key()
    sensor.api_key_hash = hash_api_key(api_key)
    await session.commit()
    await session.refresh(sensor)
    return SensorCreated(**SensorRead.model_validate(sensor).model_dump(), api_key=api_key)


@router.delete("/{sensor_id}", status_code=204)
async def delete_sensor(sensor_id: int, session: AsyncSession = Depends(get_session)):
    sensor = await get_sensor_or_404(session, sensor_id)
    try:
        await session.delete(sensor)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="У сенсора есть события телеметрии. Отключите его (is_active=false) вместо удаления",
        )