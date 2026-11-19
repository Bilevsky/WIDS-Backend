from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """Пользователи WIDS-сервера (Admin / Analyst / Viewer)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="Viewer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Sensor(Base):
    """Сенсоры с координатами на плане помещения."""
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    api_key_hash: Mapped[str] = mapped_column(String(64))  # SHA 256
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WhitelistAP(Base):
    """Белый список легитимных точек доступа."""
    __tablename__ = "whitelist_aps"

    id: Mapped[int] = mapped_column(primary_key=True)
    ssid: Mapped[str] = mapped_column(String(64))
    mac: Mapped[str] = mapped_column(String(17))  # формат AA:BB:CC:DD:EE:FF
    encryption: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TelemetryEvent(Base):
    """Сырые события от сенсоров."""
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("sensors.id"))
    src_mac: Mapped[str] = mapped_column(String(17), index=True)
    dst_mac: Mapped[str] = mapped_column(String(17))
    rssi: Mapped[int] = mapped_column(Integer)
    ssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[int | None] = mapped_column(Integer, nullable=True)
    encryption: Mapped[str | None] = mapped_column(String(10), nullable=True)
    frame_type: Mapped[str] = mapped_column(String(30))
    vendor_ie: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Incident(Base):
    """Тревоги (обнаруженные атаки)."""
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(30))  # EVIL_TWIN / DEAUTH_FLOOD / ROGUE_DEVICE
    severity: Mapped[str] = mapped_column(String(20))  # LOW / MEDIUM / HIGH / CRITICAL
    status: Mapped[str] = mapped_column(String(20), default="NEW", index=True)
    source_mac: Mapped[str] = mapped_column(String(17), index=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IncidentComment(Base):
    """Комментарии аналитиков к инцидентам."""
    __tablename__ = "incident_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )