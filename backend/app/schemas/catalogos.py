import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProcesoIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    nombre: str = Field(min_length=3, max_length=200)
    tipo: str = Field(pattern="^(rectorado|direccion|vicerrectorado|facultad|proceso)$")
    descripcion: str | None = Field(default=None, max_length=5000)
    responsable_id: uuid.UUID | None = None


class ProcesoOut(ORMModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: str
    descripcion: str | None
    responsable_id: uuid.UUID | None
    activo: bool
    created_at: datetime


class ObjetivoIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    nombre: str = Field(min_length=3, max_length=300)
    descripcion: str | None = None
    proceso_id: uuid.UUID | None = None


class ObjetivoOut(ORMModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str | None
    proceso_id: uuid.UUID | None
    activo: bool


class MetricaIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    nombre: str = Field(min_length=3, max_length=200)
    proceso_id: uuid.UUID | None = None


class MetricaOut(ORMModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    proceso_id: uuid.UUID | None


class UnidadIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=50)
    nombre: str = Field(min_length=3, max_length=200)
    tipo: str | None = Field(default=None, max_length=50)
    responsable_id: uuid.UUID | None = None
    lat: float | None = None
    lng: float | None = None


class UnidadOut(ORMModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    tipo: str | None
    responsable_id: uuid.UUID | None
    activo: bool


class CursoIn(BaseModel):
    nombre: str = Field(min_length=4, max_length=50)
    anio_inicio: int | None = Field(default=None, ge=2000, le=2100)
    anio_fin: int | None = Field(default=None, ge=2000, le=2100)
    activo: bool = True
    es_curso_actual: bool = False


class CursoOut(ORMModel):
    id: uuid.UUID
    nombre: str
    anio_inicio: int | None
    anio_fin: int | None
    activo: bool
    es_curso_actual: bool


class ConfigSistemaIn(BaseModel):
    clave: str = Field(min_length=3, max_length=100, pattern=r"^[a-z_]+$")
    valor: str = Field(min_length=1, max_length=500)
    descripcion: str | None = None


class ConfigSistemaOut(ORMModel):
    id: uuid.UUID
    clave: str
    valor: str
    descripcion: str | None
    ultima_modificacion_por: uuid.UUID | None
    ultima_modificacion_en: datetime
