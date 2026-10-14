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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDMixin


class Auditoria(UUIDMixin, Base):
    """Registro append-only de operaciones (RF-51/52). Triggers bloquean UPDATE/DELETE."""

    __tablename__ = "auditoria"
    __table_args__ = (
        Index("idx_auditoria_timestamp", "timestamp"),
        Index("idx_auditoria_usuario", "usuario_id", "timestamp"),
        Index("idx_auditoria_accion", "accion"),
        {"schema": "auditoria"},
    )

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    recurso_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    recurso_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    detalles: Mapped[dict | None] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SecurityLog(Base):
    """Log estructurado JSON append-only (RFC de logs del sistema)."""

    __tablename__ = "security_logs"
    __table_args__ = (
        CheckConstraint("severity IN ('INFO','WARNING','CRITICAL')", name="ck_seclogs_severidad"),
        Index("idx_seclogs_ts", "ts"),
        Index("idx_seclogs_evento", "event_type", "ts"),
        {"schema": "auditoria"},
    )

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    usuario: Mapped[dict] = mapped_column(JSONB, nullable=False)
    session: Mapped[dict] = mapped_column(JSONB, nullable=False)
    action: Mapped[dict] = mapped_column(JSONB, nullable=False)
    system: Mapped[dict] = mapped_column(JSONB, nullable=False)


class LogAiAnalysis(Base):
    __tablename__ = "log_ai_analysis"
    __table_args__ = (
        CheckConstraint(
            "tipo_analisis IN ('logs','narrativa')", name="ck_ai_tipo"
        ),
        CheckConstraint(
            "estado IN ('ok','error','fallback')", name="ck_ai_estado"
        ),
        Index("idx_ai_analysis_tipo", "tipo_analisis", "creado_en"),
        {"schema": "auditoria"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tipo_analisis: Mapped[str] = mapped_column(String(30), nullable=False)
    proveedor: Mapped[str] = mapped_column(String(30), nullable=False)
    modelo: Mapped[str | None] = mapped_column(String(100))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    respuesta: Mapped[str | None] = mapped_column(Text)
    rango_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rango_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tokens_salida: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    costo_estimado: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    duracion_ms: Mapped[int | None] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    error: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Notificacion(UUIDMixin, Base):
    __tablename__ = "notificaciones"
    __table_args__ = (Index("idx_notif_usuario", "usuario_id", "leida"), {"schema": "auditoria"},)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config.usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    indicador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("indicadores.indicadores.id", ondelete="CASCADE")
    )
    leida: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
