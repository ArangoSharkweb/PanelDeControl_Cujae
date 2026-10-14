import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FuenteIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=50)
    nombre: str = Field(min_length=3, max_length=100)
    tipo: Literal["postgresql", "sqlserver", "excel"]
    motor: str | None = Field(default=None, max_length=50)
    host: str | None = Field(default=None, max_length=255)
    puerto: int | None = Field(default=None, ge=1, le=65535)
    database: str | None = Field(default=None, max_length=100)
    usuario: str | None = None
    password: str | None = None  # se cifra; nunca se retorna


class FuenteOut(ORMModel):
    """RNF-09: credenciales jamas expuestas."""

    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: str
    motor: str | None
    host: str | None
    puerto: int | None
    database: str | None
    credenciales_cifradas: str | None = Field(default=None, exclude=True)
    activo: bool
    solo_lectura: bool
    ultima_prueba: datetime | None
    estado_prueba: str | None


class DescubrimientoOut(BaseModel):
    fuente_id: uuid.UUID
    tablas: list[dict]
    errores: list[str] = []


class AuditoriaOut(ORMModel):
    id: uuid.UUID
    usuario_id: uuid.UUID | None
    accion: str
    recurso_tipo: str
    recurso_id: uuid.UUID | None
    detalles: dict | None
    timestamp: datetime


class SecurityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: uuid.UUID
    ts: datetime
    event_type: str
    severity: str
    usuario: dict
    session: dict
    action: dict
    system: dict
