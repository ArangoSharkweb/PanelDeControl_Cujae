import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import MeOut, require
from app.database import get_db
from app.models.catalogos import (
    Curso,
    MetricaProceso,
    ObjetivoEstrategico,
    Proceso,
    UnidadOrganizativa,
)
from app.schemas.catalogos import (
    CursoIn,
    CursoOut,
    MetricaIn,
    MetricaOut,
    ObjetivoIn,
    ObjetivoOut,
    ProcesoIn,
    ProcesoOut,
    UnidadIn,
    UnidadOut,
)
from app.services.log_service import write_audit, write_security_log

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


async def _crear(session: AsyncSession, modelo, data, me: MeOut, recurso: str):
    """Crea entidad de catalogo con auditoria generica.

    Args:
        session: sesion async.
        modelo: clase SQLAlchemy.
        data: payload Pydantic.
        me: usuario autenticado.
        recurso: nombre del recurso para auditoria.

    Returns:
        Entidad creada.
    """
    entidad = modelo(**data.model_dump())
    session.add(entidad)
    await session.commit()
    await session.refresh(entidad)
    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="CREATE",
        recurso_tipo=recurso,
        recurso_id=entidad.id,
        detalles=data.model_dump(),
    )
    await write_security_log(
        session,
        event_type="config_change",
        user={"user_id": me.id, "username": me.username, "role": me.rol},
        resource_type=recurso,
        resource_id=str(entidad.id),
        operation="create",
    )
    return entidad


async def _eliminar(session: AsyncSession, entidad, me: MeOut, recurso: str) -> None:
    """Soft delete si tiene 'activo', si no elimina con CASCADE respetado.

    Args:
        session: sesion async.
        entidad: instancia a eliminar.
        me: usuario autenticado.
        recurso: nombre del recurso.

    Raises:
        HTTPException 409: si hay hijos (FK RESTRICT).
    """
    if hasattr(entidad, "activo"):
        entidad.activo = False
    else:
        session.delete(entidad)
    try:
        await session.commit()
    except Exception as exc:  # noqa: BLE001 - violacion FK
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No se puede eliminar: tiene registros asociados"
        ) from exc
    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="DELETE",
        recurso_tipo=recurso,
        recurso_id=entidad.id,
        detalles={"id": str(entidad.id)},
    )


@router.get("/procesos", response_model=list[ProcesoOut])
async def listar_procesos(
    _: MeOut = Depends(require("tablero", "indicadores", "catalogos")),
    session: AsyncSession = Depends(get_db),
) -> list[Proceso]:
    res = await session.execute(select(Proceso).order_by(Proceso.codigo))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("/procesos", response_model=ProcesoOut, status_code=status.HTTP_201_CREATED)
async def crear_proceso(
    data: ProcesoIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> Proceso:
    return await _crear(session, Proceso, data, me, "proceso")


@router.delete("/procesos/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_proceso(
    proceso_id: uuid.UUID,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> None:
    entidad = await session.get(Proceso, proceso_id)
    if entidad is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proceso no encontrado")
    await _eliminar(session, entidad, me, "proceso")


@router.get("/objetivos", response_model=list[ObjetivoOut])
async def listar_objetivos(
    _: MeOut = Depends(require("tablero", "indicadores", "catalogos")),
    session: AsyncSession = Depends(get_db),
) -> list[ObjetivoEstrategico]:
    res = await session.execute(select(ObjetivoEstrategico))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("/objetivos", response_model=ObjetivoOut, status_code=status.HTTP_201_CREATED)
async def crear_objetivo(
    data: ObjetivoIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> ObjetivoEstrategico:
    return await _crear(session, ObjetivoEstrategico, data, me, "objetivo")


@router.get("/metricas", response_model=list[MetricaOut])
async def listar_metricas(
    _: MeOut = Depends(require("tablero", "indicadores", "catalogos")),
    session: AsyncSession = Depends(get_db),
) -> list[MetricaProceso]:
    res = await session.execute(select(MetricaProceso))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("/metricas", response_model=MetricaOut, status_code=status.HTTP_201_CREATED)
async def crear_metrica(
    data: MetricaIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> MetricaProceso:
    return await _crear(session, MetricaProceso, data, me, "metrica")


@router.get("/unidades", response_model=list[UnidadOut])
async def listar_unidades(
    _: MeOut = Depends(require("tablero", "indicadores", "catalogos")),
    session: AsyncSession = Depends(get_db),
) -> list[UnidadOrganizativa]:
    res = await session.execute(select(UnidadOrganizativa).order_by(UnidadOrganizativa.nombre))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("/unidades", response_model=UnidadOut, status_code=status.HTTP_201_CREATED)
async def crear_unidad(
    data: UnidadIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> UnidadOrganizativa:
    return await _crear(session, UnidadOrganizativa, data, me, "unidad")


@router.get("/cursos", response_model=list[CursoOut])
async def listar_cursos(
    _: MeOut = Depends(require("tablero", "indicadores", "catalogos")),
    session: AsyncSession = Depends(get_db),
) -> list[Curso]:
    res = await session.execute(select(Curso).order_by(Curso.anio_inicio.desc()))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("/cursos", response_model=CursoOut, status_code=status.HTTP_201_CREATED)
async def crear_curso(
    data: CursoIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> Curso:
    if data.es_curso_actual:
        res = await session.execute(select(Curso).where(Curso.es_curso_actual.is_(True)))
        actual = res.scalars().first()
        if actual is not None:
            actual.es_curso_actual = False
            await session.flush()
    return await _crear(session, Curso, data, me, "curso")
