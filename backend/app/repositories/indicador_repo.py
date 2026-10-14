import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalogos import Curso
from app.models.indicadores import Indicador, MetaIndicador, ValorIndicador


async def list_indicadores(
    session: AsyncSession,
    *,
    proceso_id: uuid.UUID | None = None,
    solo_activos: bool = True,
    esencial: bool | None = None,
    limite: int = 100,
    offset: int = 0,
) -> list[Indicador]:
    """Lista indicadores con filtros (nunca SELECT *: solo entidades).

    Args:
        session: sesion async.
        proceso_id: filtro por proceso.
        solo_activos: excluye inactivos si True.
        esencial: filtra KPIs esenciales si se indica.
        limite: maximo de filas.
        offset: desplazamiento.

    Returns:
        Lista de indicadores.
    """
    stmt = select(Indicador).options(
        selectinload(Indicador.metas), selectinload(Indicador.variables)
    )
    if solo_activos:
        stmt = stmt.where(Indicador.activo.is_(True))
    if proceso_id is not None:
        stmt = stmt.where(Indicador.proceso_id == proceso_id)
    if esencial is not None:
        stmt = stmt.where(Indicador.esencial.is_(esencial))
    stmt = stmt.order_by(Indicador.codigo).limit(limite).offset(offset)
    res = await session.execute(stmt)
    return list(res.scalars().unique().all())


async def get_indicador(session: AsyncSession, indicador_id: uuid.UUID) -> Indicador | None:
    """Obtiene indicador con variables y metas.

    Args:
        session: sesion async.
        indicador_id: UUID.

    Returns:
        Indicador o None.
    """
    stmt = (
        select(Indicador)
        .where(Indicador.id == indicador_id)
        .options(selectinload(Indicador.variables), selectinload(Indicador.metas))
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_valor_vigente(
    session: AsyncSession, indicador_id: uuid.UUID, curso_id: uuid.UUID | None
) -> ValorIndicador | None:
    """Ultimo valor vigente del indicador.

    Args:
        session: sesion async.
        indicador_id: UUID del indicador.
        curso_id: UUID del curso academico.

    Returns:
        ValorIndicador o None.
    """
    stmt = select(ValorIndicador).where(
        ValorIndicador.indicador_id == indicador_id,
        ValorIndicador.curso_id == curso_id,
        ValorIndicador.vigente_hasta.is_(None),
    )
    res = await session.execute(stmt)
    return res.scalars().first()


async def get_valor_anterior(
    session: AsyncSession, indicador_id: uuid.UUID, curso_id: uuid.UUID | None
) -> ValorIndicador | None:
    """Valor vigente del curso academico previo (para comparativa de narrativa).

    Args:
        session: sesion async.
        indicador_id: UUID del indicador.
        curso_id: UUID del curso actual.

    Returns:
        Valor del periodo anterior o None.
    """
    actual = await session.get(Curso, curso_id) if curso_id else None
    if actual is None:
        return None
    prev = await session.execute(
        select(Curso)
        .where(Curso.anio_fin.is_not(None), Curso.anio_fin < (actual.anio_fin or 0))
        .order_by(Curso.anio_fin.desc())
        .limit(1)
    )
    previo = prev.scalars().first()
    if previo is None:
        return None
    return await get_valor_vigente(session, indicador_id, previo.id)


async def get_meta(
    session: AsyncSession, indicador_id: uuid.UUID, curso_id: uuid.UUID | None
) -> MetaIndicador | None:
    """Meta y umbrales del indicador para el curso dado.

    Args:
        session: sesion async.
        indicador_id: UUID.
        curso_id: UUID del curso.

    Returns:
        MetaIndicador o None.
    """
    if curso_id is None:
        return None
    res = await session.execute(
        select(MetaIndicador).where(
            MetaIndicador.indicador_id == indicador_id, MetaIndicador.curso_id == curso_id
        )
    )
    return res.scalar_one_or_none()


async def get_curso_actual(session: AsyncSession) -> Curso | None:
    """Curso academico marcado como actual.

    Args:
        session: sesion async.

    Returns:
        Curso o None.
    """
    res = await session.execute(select(Curso).where(Curso.es_curso_actual.is_(True)))
    return res.scalars().first()
