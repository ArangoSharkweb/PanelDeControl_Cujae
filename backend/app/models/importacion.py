import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDMixin


class RegistroImportado(UUIDMixin, Base):
    __tablename__ = "registros_importados"
    __table_args__ = (
        Index("idx_registros_fuente", "fuente_id", "importado_en"),
        Index(
            "idx_registros_pendientes",
            "normalizado",
            "conciliado",
            postgresql_where=text("normalizado = false OR conciliado = false"),
        ),
        {"schema": "importacion"},
    )

    fuente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicadores.fuentes_datos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tabla_origen: Mapped[str | None] = mapped_column(String(100))
    fila_original: Mapped[int | None] = mapped_column(Integer)
    datos: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalizado: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    importado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("config.usuarios.id", ondelete="SET NULL")
    )
    error_validacion: Mapped[str | None] = mapped_column(Text)
