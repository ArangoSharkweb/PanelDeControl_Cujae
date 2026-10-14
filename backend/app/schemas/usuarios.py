import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UsuarioIn(BaseModel):
    username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9._-]+$")
    password: str | None = Field(default=None, min_length=8, max_length=200)
    email: EmailStr | None = None
    rol: Literal["administrador", "alta_direccion", "directivo", "jefe_proceso", "auditor"]
    auth_type: Literal["ldap", "local"] = "local"
    alcance_tipo: Literal["institucional", "unidad", "proceso"] = "institucional"
    alcance_id: uuid.UUID | None = None
    activo: bool = True


class UsuarioOut(ORMModel):
    id: uuid.UUID
    username: str
    email: str | None
    rol: str
    auth_type: str
    alcance_tipo: str
    alcance_id: uuid.UUID | None
    activo: bool
    fecha_creacion: datetime


class PasswordResetIn(BaseModel):
    nueva_password: str = Field(min_length=8, max_length=200)
