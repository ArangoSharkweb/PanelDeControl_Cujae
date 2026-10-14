"""CRUD de indicadores con auditoria y transacciones ACID."""
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indicadores import Indicador, MetaIndicador, VariableIndicador
from app.schemas.indicadores import IndicadorIn
from app.services.log_service import write_audit, write_security_log

log = logging.getLogger("indicadores")


async def crear_indicador(
    session: AsyncSession, data: IndicadorIn, usuario_id: uuid.UUID
) -> Indicador:
    """Crea indicador con variables y metas en una unica transaccion.

    Args:
        session: sesion async.
        data: payload validado por Pydantic.
        usuario_id: responsable.

    Raises:
        HTTPException 409: codigo duplicado.

    Returns:
        Indicador creado.
    """
    from sqlalchemy import select

    res = await session.execute(select(Indicador).where(Indicador.codigo == data.codigo))
    if res.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Codigo {data.codigo} ya existe")

    indicador = Indicador(**data.model_dump(exclude={"variables", "metas"}))
    session.add(indicador)
    await session.flush()

    for var in data.variables:
        session.add(VariableIndicador(indicador_id=indicador.id, **var.model_dump()))
    for meta in data.metas:
        session.add(MetaIndicador(indicador_id=indicador.id, **meta.model_dump()))

    await session.commit()
    await session.refresh(indicador)

    await write_audit(
        session,
        usuario_id=usuario_id,
        accion="CREATE",
        recurso_tipo="indicador",
        recurso_id=indicador.id,
        detalles={"codigo": indicador.codigo, "nombre": indicador.nombre},
    )
    await write_security_log(
        session,
        event_type="indicator_create",
        user={"user_id": str(usuario_id)},
        resource_type="indicador",
        resource_id=str(indicador.id),
        operation="create",
        details={"codigo": indicador.codigo},
    )
    return indicador


async def actualizar_indicador(
    session: AsyncSession, indicador_id: uuid.UUID, data: IndicadorIn, usuario_id: uuid.UUID
) -> Indicador:
    """Actualiza indicador (auditando antes/desde).

    Args:
        session: sesion async.
        indicador_id: UUID a actualizar.
        data: payload validado.
        usuario_id: responsable.

    Raises:
        HTTPException 404: no encontrado.

    Returns:
        Indicador actualizado.
    """
    indicador = await session.get(Indicador, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador no encontrado")

    antes = {"nombre": indicador.nombre, "formula": indicador.formula, "activo": indicador.activo}
    for key, value in data.model_dump(exclude={"variables", "metas"}).items():
        setattr(indicador, key, value)
    await session.commit()
    await session.refresh(indicador)

    await write_audit(
        session,
        usuario_id=usuario_id,
        accion="UPDATE",
        recurso_tipo="indicador",
        recurso_id=indicador.id,
        detalles={"antes": antes, "despues": data.model_dump(exclude={"variables", "metas"})},
    )
    await write_security_log(
        session,
        event_type="indicator_modify",
        user={"user_id": str(usuario_id)},
        resource_type="indicador",
        resource_id=str(indicador.id),
        operation="update",
    )
    return indicador


async def desactivar_indicador(
    session: AsyncSession, indicador_id: uuid.UUID, usuario_id: uuid.UUID
) -> None:
    """Soft delete (RF): solo marca inactivo, nunca borra historial.

    Args:
        session: sesion async.
        indicador_id: UUID.
        usuario_id: responsable.

    Raises:
        HTTPException 404: no encontrado.
    """
    indicador = await session.get(Indicador, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador no encontrado")
    indicador.activo = False
    await session.commit()

    await write_audit(
        session,
        usuario_id=usuario_id,
        accion="DELETE",
        recurso_tipo="indicador",
        recurso_id=indicador.id,
        detalles={"codigo": indicador.codigo, "modo": "soft_delete"},
    )
    await write_security_log(
        session,
        event_type="indicator_delete",
        severity="WARNING",
        user={"user_id": str(usuario_id)},
        resource_type="indicador",
        resource_id=str(indicador.id),
        operation="delete",
    )
