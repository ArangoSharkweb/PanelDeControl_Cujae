import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDMixin

ROLES_VALIDOS = ("administrador", "alta_direccion", "directivo", "jefe_proceso", "auditor")


class Usuario(UUIDMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('administrador','alta_direccion','directivo','jefe_proceso','auditor')",
            name="ck_usuarios_rol",
        ),
        CheckConstraint("auth_type IN ('ldap','local')", name="ck_usuarios_auth"),
        CheckConstraint("alcance_tipo IN ('institucional','unidad','proceso')", name="ck_usuarios_alcance"),
        {"schema": "config"},
    )

    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(10), nullable=False, default="local")
    alcance_tipo: Mapped[str] = mapped_column(String(20), default="institucional")
    alcance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ultima_modificacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
