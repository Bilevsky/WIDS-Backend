from fastapi import APIRouter, Depends
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session, rate_limited_sensor
from app.models import Sensor, TelemetryEvent
from app.schemas import TelemetryAccepted, TelemetryBatch

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/batch", response_model=TelemetryAccepted, status_code=201)
async def receive_batch(
    data: TelemetryBatch,
    sensor: Sensor = Depends(rate_limited_sensor),
    session: AsyncSession = Depends(get_session),
):
    """Принимает пачку событий от сенсора и записывает их в БД одной командой."""
    rows = [{**event.model_dump(), "sensor_id": sensor.id} for event in data.events]
    await session.execute(insert(TelemetryEvent), rows)
    await session.commit()
    return TelemetryAccepted(accepted=len(rows))