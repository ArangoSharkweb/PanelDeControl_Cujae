import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class FuenteDatos(UUIDMixin, Base):
    __tablename__ = "fuentes_datos"
    __table_args__ = (
        CheckConstraint("tipo IN ('postgresql','sqlserver','excel')", name="ck_fuentes_tipo"),
        {"schema": "indicadores"},
    )

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    motor: Mapped[str | None] = mapped_column(String(50))
    host: Mapped[str | None] = mapped_column(String(255))
    puerto: Mapped[int | None] = mapped_column(Integer)
    database: Mapped[str | None] = mapped_column(String(100))
    credenciales_cifradas: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    solo_lectura: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    ultima_prueba: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado_prueba: Mapped[str | None] = mapped_column(String(20))


class Indicador(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "indicadores"
    __table_args__ = (
        CheckConstraint(
            "periodicidad IN ('anual','semestral','trimestral','mensual')",
            name="ck_indicadores_periodicidad",
        ),
        CheckConstraint(
            "sentido IN ('ascendente','descendente')", name="ck_indicadores_sentido"
        ),
        CheckConstraint(
            "nivel IN ('Universidad','Facultad','Direccion')", name="ck_indicadores_nivel"
        ),
        Index("idx_indicadores_proceso", "proceso_id"),
        Index("idx_indicadores_activo", "activo"),
        {"schema": "indicadores"},
    )

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    unidad_medida: Mapped[str | None] = mapped_column(String(50))
    periodicidad: Mapped[str] = mapped_column(String(20), nullable=False, default="anual")
    sentido: Mapped[str] = mapped_column(String(20), nullable=False, default="ascendente")
    formula: Mapped[str | None] = mapped_column(String(500))
    proceso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config.procesos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    metrica_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.metricas_proceso.id", ondelete="SET NULL")
    )
    nivel: Mapped[str] = mapped_column(String(20), nullable=False, default="Universidad")
    esencial: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    variables: Mapped[list["VariableIndicador"]] = relationship(
        back_populates="indicador", cascade="all, delete-orphan", passive_deletes=True
    )
    metas: Mapped[list["MetaIndicador"]] = relationship(
        back_populates="indicador", cascade="all, delete-orphan", passive_deletes=True
    )
    valores: Mapped[list["ValorIndicador"]] = relationship(
        back_populates="indicador", cascade="all, delete-orphan", passive_deletes=True
    )


class VariableIndicador(UUIDMixin, Base):
    __tablename__ = "variables_indicador"
    __table_args__ = (
        UniqueConstraint("indicador_id", "nombre", name="uq_variables_indicador_nombre"),
        CheckConstraint(
            "funcion_agregacion IN ('COUNT','SUM','AVG','MIN','MAX')",
            name="ck_variables_funcion",
        ),
        {"schema": "indicadores"},
    )

    indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.indicadores.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(10), nullable=False)
    fuente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("indicadores.fuentes_datos.id", ondelete="RESTRICT")
    )
    tabla: Mapped[str | None] = mapped_column(String(100))
    columna: Mapped[str | None] = mapped_column(String(100))
    funcion_agregacion: Mapped[str | None] = mapped_column(String(20))
    filtros: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    indicador: Mapped[Indicador] = relationship(back_populates="variables")


class MetaIndicador(UUIDMixin, Base):
    __tablename__ = "metas_indicador"
    __table_args__ = (
        UniqueConstraint("indicador_id", "curso_id", name="uq_metas_indicador_curso"),
        {"schema": "indicadores"},
    )

    indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.indicadores.id", ondelete="CASCADE"),
        nullable=False,
    )
    curso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config.cursos.id", ondelete="CASCADE"),
        nullable=False,
    )
    valor_meta: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    umbral_verde: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=90, server_default="90"
    )
    umbral_amarillo: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=70, server_default="70"
    )

    indicador: Mapped[Indicador] = relationship(back_populates="metas")


class HistorialSnapshot(UUIDMixin, Base):
    __tablename__ = "historial_snapshot"
    __table_args__ = (
        UniqueConstraint("indicador_id", "periodo", name="uq_snapshot_periodo"),
        CheckConstraint(
            "estado_semaforo IN ('verde','amarillo','rojo')", name="ck_snapshot_semaforo"
        ),
        {"schema": "indicadores"},
    )

    indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.indicadores.id", ondelete="CASCADE"),
        nullable=False,
    )
    periodo: Mapped[str] = mapped_column(String(30), nullable=False)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(15, 4))
    estado_semaforo: Mapped[str | None] = mapped_column(String(10))


class ValorIndicador(UUIDMixin, Base):
    __tablename__ = "valores_indicadores"
    __table_args__ = (
        UniqueConstraint(
            "indicador_id", "curso_id", "unidad_id", "vigente_hasta",
            name="uq_valores_vigencia",
        ),
        CheckConstraint(
            "estado_semaforo IN ('verde','amarillo','rojo')", name="ck_valores_semaforo"
        ),
        Index("idx_valores_indicador", "indicador_id", "calculado_en"),
        Index("idx_valores_vigencia", "vigente_hasta"),
        {"schema": "indicadores"},
    )

    indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.indicadores.id", ondelete="CASCADE"),
        nullable=False,
    )
    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.cursos.id", ondelete="RESTRICT")
    )
    unidad_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.unidades_organizativas.id", ondelete="CASCADE")
    )
    valor: Mapped[Decimal | None] = mapped_column(Numeric(15, 4))
    estado_semaforo: Mapped[str | None] = mapped_column(String(10))
    porcentaje_meta: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    calculado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vigente_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fuente_origen: Mapped[str | None] = mapped_column(String(50))

    indicador: Mapped[Indicador] = relationship(back_populates="valores")


class NarrativaIA(Base):
    __tablename__ = "narrativas_ia"
    __table_args__ = ({"schema": "indicadores"},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    valor_indicador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.valores_indicadores.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    proveedor: Mapped[str | None] = mapped_column(String(30))
    modelo: Mapped[str | None] = mapped_column(String(100))
    tokens_entrada: Mapped[int | None] = mapped_column(Integer)
    tokens_salida: Mapped[int | None] = mapped_column(Integer)
    es_fallback: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
