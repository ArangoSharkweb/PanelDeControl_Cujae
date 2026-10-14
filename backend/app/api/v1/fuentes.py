import base64
import hashlib
import uuid
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import MeOut, require
from app.config import settings
from app.database import get_db
from app.services.etl.strategies import construir_estrategia
from app.models.indicadores import FuenteDatos
from app.schemas.operaciones import DescubrimientoOut, FuenteIn, FuenteOut
from app.services.log_service import write_audit

router = APIRouter(prefix="/fuentes", tags=["fuentes"])


def _fernet() -> Fernet:
    """Clave derivada del JWT secret (no hardcodeada)."""
    clave = base64.urlsafe_b64encode(hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest())
    return Fernet(clave)


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode()).decode()


def descifrar(texto: str) -> str:
    return _fernet().decrypt(texto.encode()).decode()


@router.get("", response_model=list[FuenteOut])
async def listar(
    _: MeOut = Depends(require("fuentes")),
    session: AsyncSession = Depends(get_db),
) -> list[FuenteOut]:
    """Lista fuentes (credenciales excluidas, RNF-09).

    Args:
        _: usuario con permiso de fuentes.
        session: sesion async.

    Returns:
        Fuentes sin credenciales.
    """
    res = await session.execute(select(FuenteDatos).order_by(FuenteDatos.codigo))
    return [FuenteOut.model_validate(f) for f in res.scalars().all()]


@router.post("", response_model=FuenteOut, status_code=status.HTTP_201_CREATED)
async def crear(
    data: FuenteIn,
    me: MeOut = Depends(require("fuentes")),
    session: AsyncSession = Depends(get_db),
) -> FuenteOut:
    """Crea fuente con credenciales cifradas (nunca se almacenan en claro).

    Args:
        data: datos de conexion.
        me: usuario con permiso.
        session: sesion async.

    Returns:
        Fuente creada.
    """
    credenciales = None
    if data.usuario and data.password:
        credenciales = cifrar(f"{data.usuario}:{data.password}")
    fuente = FuenteDatos(
        codigo=data.codigo,
        nombre=data.nombre,
        tipo=data.tipo,
        motor=data.motor,
        host=data.host,
        puerto=data.puerto,
        database=data.database,
        credenciales_cifradas=credenciales,
        solo_lectura=True,
    )
    session.add(fuente)
    await session.commit()
    await session.refresh(fuente)
    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="CREATE",
        recurso_tipo="fuente",
        recurso_id=fuente.id,
        detalles={"codigo": fuente.codigo, "tipo": fuente.tipo},
    )
    return FuenteOut.model_validate(fuente)


@router.post("/{fuente_id}/probar", response_model=DescubrimientoOut)
async def probar_y_descubrir(
    fuente_id: uuid.UUID,
    me: MeOut = Depends(require("fuentes")),
    session: AsyncSession = Depends(get_db),
) -> DescubrimientoOut:
    """Prueba conexion y descubre esquema automaticamente (RF-17+).

    Solo lectura (RNF-10). Si falla, no afecta al resto (RNF-07):
    se marca estado_prueba y se retorna el error en 'errores'.

    Args:
        fuente_id: UUID de la fuente.
        me: usuario con permiso.
        session: sesion async.

    Returns:
        Tablas descubiertas y errores (si los hubo).
    """
    fuente = await session.get(FuenteDatos, fuente_id)
    if fuente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fuente no encontrada")
    if not fuente.activo:
        raise HTTPException(status.HTTP_409_CONFLICT, "Fuente inactiva")

    usuario, password = "", ""
    if fuente.credenciales_cifradas:
        usuario, password = descifrar(fuente.credenciales_cifradas).split(":", 1)

    errores: list[str] = []
    tablas: list[dict] = []
    try:
        estrategia = construir_estrategia(
            fuente.tipo,
            host=fuente.host or "",
            puerto=fuente.puerto or 5432,
            database=fuente.database or "",
            usuario=usuario,
            password=password,
        )
        tablas = await estrategia.discover_schema()
        fuente.estado_prueba = "ok"
    except Exception as exc:  # noqa: BLE001 - aislamiento de fallos por fuente
        fuente.estado_prueba = "error"
        errores.append(str(exc))
    fuente.ultima_prueba = datetime.now(timezone.utc)
    await session.commit()
    return DescubrimientoOut(fuente_id=fuente.id, tablas=tablas, errores=errores)
