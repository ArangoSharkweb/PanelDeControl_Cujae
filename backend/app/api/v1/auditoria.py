"""Historial de auditoria (tabla append-only auditoria.auditoria)."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import MeOut, require_logs
from app.database import get_db
from app.models.auditoria import Auditoria
from app.schemas.operaciones import AuditoriaOut

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[AuditoriaOut])
async def listar_auditoria(
    accion: str | None = None,
    usuario_id: uuid.UUID | None = None,
    recurso_tipo: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limite: int = Query(default=100, ge=1, le=1000),
    _: MeOut = Depends(require_logs),
    session: AsyncSession = Depends(get_db),
) -> list[Auditoria]:
    """Historial de operaciones (solo administrador/auditor) con filtros.

    Args:
        accion: filtro por accion (CREATE/UPDATE/DELETE/LOGIN...).
        usuario_id: filtro por usuario.
        recurso_tipo: filtro por recurso afectado.
        desde: fecha inicio.
        hasta: fecha fin.
        limite: maximo de filas.
        _: usuario con permiso de logs.
        session: sesion async.

    Returns:
        Registros ordenados por timestamp descendente.
    """
    stmt = select(Auditoria).order_by(Auditoria.timestamp.desc()).limit(limite)
    if accion:
        stmt = stmt.where(Auditoria.accion == accion)
    if usuario_id:
        stmt = stmt.where(Auditoria.usuario_id == usuario_id)
    if recurso_tipo:
        stmt = stmt.where(Auditoria.recurso_tipo == recurso_tipo)
    if desde:
        stmt = stmt.where(Auditoria.timestamp >= desde)
    if hasta:
        stmt = stmt.where(Auditoria.timestamp <= hasta)
    res = await session.execute(stmt)
    return list(res.scalars().all())  # type: ignore[return-value]
