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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Proceso(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "procesos"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('rectorado','direccion','vicerrectorado','facultad','proceso')",
            name="ck_procesos_tipo",
        ),
        {"schema": "config"},
    )

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    objetivos: Mapped[list["ObjetivoEstrategico"]] = relationship(
        back_populates="proceso", cascade="all, delete-orphan", passive_deletes=True
    )


class ObjetivoEstrategico(UUIDMixin, Base):
    __tablename__ = "objetivos_estrategicos"
    __table_args__ = (Index("idx_objetivos_proceso", "proceso_id"),{"schema": "config"},)

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.procesos.id", ondelete="CASCADE")
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    proceso: Mapped[Proceso | None] = relationship(back_populates="objetivos")


class MetricaProceso(UUIDMixin, Base):
    __tablename__ = "metricas_proceso"
    __table_args__ = ({"schema": "config"},)

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    proceso_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.procesos.id", ondelete="CASCADE")
    )


class UnidadOrganizativa(UUIDMixin, Base):
    __tablename__ = "unidades_organizativas"
    __table_args__ = ({"schema": "config"},)

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(50))
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    lng: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Curso(UUIDMixin, Base):
    __tablename__ = "cursos"
    __table_args__ = (
        Index(
            "uq_curso_actual",
            "es_curso_actual",
            unique=True,
            postgresql_where=text("es_curso_actual"),
        ),
        {"schema": "config"},
    )

    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    anio_inicio: Mapped[int | None] = mapped_column(Integer)
    anio_fin: Mapped[int | None] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    es_curso_actual: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"
    __table_args__ = ({"schema": "config"},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    ultima_modificacion_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    ultima_modificacion_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
