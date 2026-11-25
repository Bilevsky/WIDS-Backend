from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.models import WhitelistAP, WhitelistDevice
from app.schemas import (
    WhitelistAPCreate,
    WhitelistAPRead,
    WhitelistAPUpdate,
    WhitelistDeviceCreate,
    WhitelistDeviceRead,
)

router = APIRouter(prefix="/whitelist", tags=["whitelist"])


# ---------- Точки доступа ----------
async def get_ap_or_404(session: AsyncSession, ap_id: int) -> WhitelistAP:
    ap = await session.get(WhitelistAP, ap_id)
    if ap is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return ap


@router.post("/aps", response_model=WhitelistAPRead, status_code=201)
async def create_ap(data: WhitelistAPCreate, session: AsyncSession = Depends(get_session)):
    exists = await session.execute(
        select(WhitelistAP).where(
            WhitelistAP.ssid == data.ssid, WhitelistAP.mac == data.mac
        )
    )
    if exists.scalars().first():
        raise HTTPException(status_code=409, detail="Такая точка доступа уже есть в списке")
    ap = WhitelistAP(**data.model_dump())
    session.add(ap)
    await session.commit()
    await session.refresh(ap)
    return ap


@router.get("/aps", response_model=list[WhitelistAPRead])
async def list_aps(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(WhitelistAP).order_by(WhitelistAP.id))
    return result.scalars().all()


@router.get("/aps/{ap_id}", response_model=WhitelistAPRead)
async def get_ap(ap_id: int, session: AsyncSession = Depends(get_session)):
    return await get_ap_or_404(session, ap_id)


@router.patch("/aps/{ap_id}", response_model=WhitelistAPRead)
async def update_ap(
    ap_id: int, data: WhitelistAPUpdate, session: AsyncSession = Depends(get_session)
):
    ap = await get_ap_or_404(session, ap_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ap, field, value)
    await session.commit()
    await session.refresh(ap)
    return ap


@router.delete("/aps/{ap_id}", status_code=204)
async def delete_ap(ap_id: int, session: AsyncSession = Depends(get_session)):
    ap = await get_ap_or_404(session, ap_id)
    await session.delete(ap)
    await session.commit()


# Корпоративные устройства
@router.post("/devices", response_model=WhitelistDeviceRead, status_code=201)
async def create_device(
    data: WhitelistDeviceCreate, session: AsyncSession = Depends(get_session)
):
    exists = await session.execute(
        select(WhitelistDevice).where(WhitelistDevice.mac == data.mac)
    )
    if exists.scalars().first():
        raise HTTPException(status_code=409, detail="Устройство с таким MAC уже есть")
    device = WhitelistDevice(**data.model_dump())
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device


@router.get("/devices", response_model=list[WhitelistDeviceRead])
async def list_devices(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(WhitelistDevice).order_by(WhitelistDevice.id))
    return result.scalars().all()


@router.delete("/devices/{device_id}", status_code=204)
async def delete_device(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(WhitelistDevice, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    await session.delete(device)
    await session.commit()