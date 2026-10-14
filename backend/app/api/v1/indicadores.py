import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import MeOut, get_current_user, require
from app.database import get_db
from app.models.indicadores import Indicador
from app.repositories import indicador_repo
from app.schemas.indicadores import (
    IndicadorDetalleOut,
    IndicadorIn,
    IndicadorOut,
    ValorOut,
)
from app.services import calculation_engine, indicador_service

router = APIRouter(prefix="/indicadores", tags=["indicadores"])


@router.get("", response_model=list[IndicadorDetalleOut])
async def listar(
    proceso_id: uuid.UUID | None = None,
    esencial: bool | None = None,
    limite: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: MeOut = Depends(require("indicadores", "tablero")),
    session: AsyncSession = Depends(get_db),
) -> list[IndicadorDetalleOut]:
    """Lista indicadores con filtros por proceso y esencialidad.

    Args:
        proceso_id: filtro por proceso.
        esencial: filtra KPIs esenciales.
        limite: maximo de filas.
        offset: paginacion.
        _: usuario autenticado con permiso de tablero/indicadores.
        session: sesion async.

    Returns:
        Lista de indicadores.
    """
    items = await indicador_repo.list_indicadores(
        session, proceso_id=proceso_id, esencial=esencial, limite=limite, offset=offset
    )
    return [IndicadorDetalleOut.model_validate(i) for i in items]


@router.get("/{indicador_id}", response_model=IndicadorDetalleOut)
async def detalle(
    indicador_id: uuid.UUID,
    _: MeOut = Depends(require("indicadores", "tablero")),
    session: AsyncSession = Depends(get_db),
) -> IndicadorDetalleOut:
    """Detalle de indicador con variables y metas.

    Args:
        indicador_id: UUID.
        _: usuario autenticado.
        session: sesion async.

    Raises:
        HTTPException 404: no encontrado.

    Returns:
        Indicador con relaciones.
    """
    indicador = await indicador_repo.get_indicador(session, indicador_id)
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador no encontrado")
    return IndicadorDetalleOut.model_validate(indicador)


@router.post("", response_model=IndicadorOut, status_code=status.HTTP_201_CREATED)
async def crear(
    data: IndicadorIn,
    me: MeOut = Depends(require("indicadores")),
    session: AsyncSession = Depends(get_db),
) -> IndicadorOut:
    """Crea indicador (RF-28+). Transaccion ACID + auditoria.

    Args:
        data: payload validado.
        me: usuario autenticado con permiso de indicadores.
        session: sesion async.

    Returns:
        Indicador creado.
    """
    indicador = await indicador_service.crear_indicador(session, data, uuid.UUID(me.id))
    return IndicadorOut.model_validate(indicador)


@router.put("/{indicador_id}", response_model=IndicadorOut)
async def actualizar(
    indicador_id: uuid.UUID,
    data: IndicadorIn,
    me: MeOut = Depends(require("indicadores")),
    session: AsyncSession = Depends(get_db),
) -> IndicadorOut:
    """Actualiza indicador con auditoria.

    Args:
        indicador_id: UUID.
        data: payload validado.
        me: usuario autenticado.
        session: sesion async.

    Returns:
        Indicador actualizado.
    """
    indicador = await indicador_service.actualizar_indicador(
        session, indicador_id, data, uuid.UUID(me.id)
    )
    return IndicadorOut.model_validate(indicador)


@router.delete("/{indicador_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    indicador_id: uuid.UUID,
    me: MeOut = Depends(require("indicadores")),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete: preserva historial y valores (RF).

    Args:
        indicador_id: UUID.
        me: usuario autenticado.
        session: sesion async.
    """
    await indicador_service.desactivar_indicador(session, indicador_id, uuid.UUID(me.id))


@router.get("/{indicador_id}/valores", response_model=list[ValorOut])
async def valores(
    indicador_id: uuid.UUID,
    _: MeOut = Depends(require("indicadores", "tablero")),
    session: AsyncSession = Depends(get_db),
) -> list[ValorOut]:
    """Historial de valores (incluye periodos cerrados).

    Args:
        indicador_id: UUID.
        _: usuario autenticado.
        session: sesion async.

    Returns:
        Valores ordenados por calculo reciente.
    """
    from app.models.indicadores import ValorIndicador

    res = await session.execute(
        select(ValorIndicador)
        .where(ValorIndicador.indicador_id == indicador_id)
        .order_by(ValorIndicador.calculado_en.desc())
        .limit(200)
    )
    return [ValorOut.model_validate(v) for v in res.scalars().all()]


@router.post("/recalculo", status_code=status.HTTP_202_ACCEPTED)
async def recalcular_manual(
    me: MeOut = Depends(require("recalcular")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Recalculo manual bajo demanda (solo alta direccion).

    Args:
        me: usuario autenticado.
        session: sesion async.

    Returns:
        Estadisticas del recalculo.
    """
    return await calculation_engine.recalcular_todos(session)
