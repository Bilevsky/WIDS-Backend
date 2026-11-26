import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Encryption = Literal["Open", "WEP", "WPA2", "WPA3"]

MAC_RE = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")


def normalize_mac(value: str) -> str:
    """Приводим MAC к виду AA:BB:CC:DD:EE:FF и проверяем формат."""
    value = value.strip().upper().replace("-", ":")
    if not MAC_RE.match(value):
        raise ValueError("MAC должен быть в формате AA:BB:CC:DD:EE:FF")
    return value


# Сенсоры
class SensorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    x: float
    y: float


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    x: float | None = None
    y: float | None = None
    is_active: bool | None = None


class SensorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    x: float
    y: float
    is_active: bool
    created_at: datetime


class SensorCreated(SensorRead):
    """Ответ при создании: то же самое + ключ (показывается один раз)."""
    api_key: str


# Белый список: точки доступа
class WhitelistAPCreate(BaseModel):
    ssid: str = Field(min_length=1, max_length=32)
    mac: str
    encryption: Encryption

    @field_validator("mac")
    @classmethod
    def check_mac(cls, v: str) -> str:
        return normalize_mac(v)


class WhitelistAPUpdate(BaseModel):
    ssid: str | None = Field(default=None, min_length=1, max_length=32)
    mac: str | None = None
    encryption: Encryption | None = None

    @field_validator("mac")
    @classmethod
    def check_mac(cls, v: str | None) -> str | None:
        return normalize_mac(v) if v is not None else v


class WhitelistAPRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ssid: str
    mac: str
    encryption: str
    created_at: datetime


# Белый список: устройства
class WhitelistDeviceCreate(BaseModel):
    mac: str
    description: str | None = Field(default=None, max_length=200)

    @field_validator("mac")
    @classmethod
    def check_mac(cls, v: str) -> str:
        return normalize_mac(v)


class WhitelistDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mac: str
    description: str | None
    created_at: datetime

# Телеметрия

FrameType = Literal["Beacon", "Probe Request", "Deauthentication"]


class TelemetryEventIn(BaseModel):
    src_mac: str
    dst_mac: str
    rssi: int = Field(ge=-120, le=0)  # уровень сигнала в dBm
    ssid: str | None = Field(default=None, max_length=32)
    channel: int | None = Field(default=None, ge=1, le=196)
    encryption: Encryption | None = None
    frame_type: FrameType
    vendor_ie: dict | None = None

    @field_validator("src_mac", "dst_mac")
    @classmethod
    def check_mac(cls, v: str) -> str:
        return normalize_mac(v)


class TelemetryBatch(BaseModel):
    events: list[TelemetryEventIn] = Field(min_length=1, max_length=500)


class TelemetryAccepted(BaseModel):
    accepted: int