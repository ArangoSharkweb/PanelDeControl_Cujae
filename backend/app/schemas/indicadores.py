import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FORMULA_ALLOWED = re.compile(r"^[A-Za-z0-9_+\-*/().,\s%]+$")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VariableIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=10, pattern=r"^[A-Za-z]$")
    fuente_id: uuid.UUID | None = None
    tabla: str | None = Field(default=None, max_length=100)
    columna: str | None = Field(default=None, max_length=100)
    funcion_agregacion: str | None = Field(
        default=None, pattern="^(COUNT|SUM|AVG|MIN|MAX)$"
    )
    filtros: dict = Field(default_factory=dict)


class VariableOut(ORMModel):
    id: uuid.UUID
    nombre: str
    fuente_id: uuid.UUID | None
    tabla: str | None
    columna: str | None
    funcion_agregacion: str | None
    filtros: dict


class MetaIn(BaseModel):
    curso_id: uuid.UUID
    valor_meta: Decimal = Field(gt=0, le=Decimal("999999999999.9999"))
    umbral_verde: Decimal = Field(default=Decimal(90), ge=0, le=100)
    umbral_amarillo: Decimal = Field(default=Decimal(70), ge=0, le=100)

    @field_validator("umbral_amarillo")
    @classmethod
    def _check_umbrales(cls, v: Decimal, info) -> Decimal:
        verde = info.data.get("umbral_verde")
        if verde is not None and v >= verde:
            raise ValueError("umbral_amarillo debe ser menor que umbral_verde")
        return v


class MetaOut(ORMModel):
    id: uuid.UUID
    curso_id: uuid.UUID
    valor_meta: Decimal
    umbral_verde: Decimal
    umbral_amarillo: Decimal


class IndicadorIn(BaseModel):
    codigo: str = Field(min_length=3, max_length=50, pattern=r"^IND-[A-Za-z0-9_-]+$")
    nombre: str = Field(min_length=5, max_length=300)
    descripcion: str | None = Field(default=None, max_length=5000)
    unidad_medida: str | None = Field(default=None, max_length=50)
    periodicidad: str = Field(default="anual", pattern="^(anual|semestral|trimestral|mensual)$")
    sentido: str = Field(pattern="^(ascendente|descendente)$")
    formula: str | None = Field(default=None, max_length=500)
    proceso_id: uuid.UUID
    metrica_id: uuid.UUID | None = None
    nivel: str = Field(default="Universidad", pattern="^(Universidad|Facultad|Direccion)$")
    esencial: bool = False
    activo: bool = True
    variables: list[VariableIn] = Field(default_factory=list, max_length=20)
    metas: list[MetaIn] = Field(default_factory=list, max_length=10)

    @field_validator("formula")
    @classmethod
    def _formula_segura(cls, v: str | None) -> str | None:
        """Whitelist de caracteres: evita inyeccion en el evaluador de formulas."""
        if v is not None and not FORMULA_ALLOWED.match(v):
            raise ValueError("Formula contiene caracteres no permitidos")
        return v


class IndicadorOut(ORMModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str | None
    unidad_medida: str | None
    periodicidad: str
    sentido: str
    formula: str | None
    proceso_id: uuid.UUID
    metrica_id: uuid.UUID | None
    nivel: str
    esencial: bool
    activo: bool
    created_at: datetime


class IndicadorDetalleOut(IndicadorOut):
    variables: list[VariableOut] = []
    metas: list[MetaOut] = []


class ValorOut(ORMModel):
    id: uuid.UUID
    indicador_id: uuid.UUID
    curso_id: uuid.UUID | None
    unidad_id: uuid.UUID | None
    valor: Decimal | None
    estado_semaforo: str | None
    porcentaje_meta: Decimal | None
    calculado_en: datetime | None
    fuente_origen: str | None


class TableroOut(BaseModel):
    indicador: IndicadorOut
    valor_actual: ValorOut | None
    valor_anterior: ValorOut | None
    meta: MetaOut | None
