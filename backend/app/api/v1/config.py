import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import MeOut, require
from app.database import get_db
from app.models.catalogos import ConfiguracionSistema
from app.schemas.catalogos import ConfigSistemaIn, ConfigSistemaOut
from app.services.log_service import write_audit, write_security_log
from app.services.scheduler import (
    CLAVE_HORA,
    CLAVE_INTERVALO,
    describir,
    parsear_intervalo,
    proxima_ejecucion,
    programar_desde_config,
)

router = APIRouter(prefix="/config", tags=["config"])

# Claves que el frontend puede leer sin autenticacion elevada
CLAVES_PUBLICAS = {"proveedor_ia", "limite_exportacion_mb"}


@router.get("", response_model=list[ConfigSistemaOut])
async def listar_config(
    _: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> list[ConfiguracionSistema]:
    """Lista parametros del sistema (solo administrador/alta direccion).

    Args:
        _: usuario con permiso de config.
        session: sesion async.

    Returns:
        Todos los parametros.
    """
    res = await session.execute(select(ConfiguracionSistema).order_by(ConfiguracionSistema.clave))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.get("/publica")
async def config_publica(session: AsyncSession = Depends(get_db)) -> dict:
    """Parametros seguros para el frontend sin sesión elevada.

    Args:
        session: sesion async.

    Returns:
        Dict de claves publicas.
    """
    res = await session.execute(
        select(ConfiguracionSistema).where(ConfiguracionSistema.clave.in_(CLAVES_PUBLICAS))
    )
    return {c.clave: c.valor for c in res.scalars().all()}


@router.get("/estado-calculo")
async def estado_calculo(
    _: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Estado de la programacion del recalculo de indicadores.

    Args:
        _: usuario con permiso de config.
        session: sesion async.

    Returns:
        Frecuencia programada, config subyacente y proxima ejecucion.
    """
    res = await session.execute(
        select(ConfiguracionSistema.clave, ConfiguracionSistema.valor).where(
            ConfiguracionSistema.clave.in_((CLAVE_INTERVALO, CLAVE_HORA))
        )
    )
    valores = dict(res.all())
    intervalo = parsear_intervalo(valores.get(CLAVE_INTERVALO))
    hora = valores.get(CLAVE_HORA)
    return {
        "frecuencia": describir(intervalo, hora),
        "intervalo_horas": intervalo,
        "hora_diaria": None if intervalo else (hora or "02:00"),
        "proxima_ejecucion": proxima_ejecucion(),
    }


@router.put("/{clave}", response_model=ConfigSistemaOut)
async def modificar_config(
    clave: str,
    data: ConfigSistemaIn,
    me: MeOut = Depends(require("config")),
    session: AsyncSession = Depends(get_db),
) -> ConfiguracionSistema:
    """Modifica un parametro (auditoria + reprograma scheduler si aplica).

    Args:
        clave: clave del parametro.
        data: nuevos valores.
        me: usuario con permiso.
        session: sesion async.

    Raises:
        HTTPException 404: clave inexistente.

    Returns:
        Parametro actualizado.
    """
    if clave != data.clave:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Clave no coincide")
    if clave == CLAVE_INTERVALO and parsear_intervalo(data.valor) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "intervalo_recalculo_horas debe ser un entero entre 1 y 168 horas",
        )
    res = await session.execute(select(ConfiguracionSistema).where(ConfiguracionSistema.clave == clave))
    config = res.scalar_one_or_none()
    if config is None:
        config = ConfiguracionSistema(clave=clave)
        session.add(config)
    antes = config.valor
    config.valor = data.valor
    if data.descripcion is not None:
        config.descripcion = data.descripcion
    config.ultima_modificacion_por = uuid.UUID(me.id)
    await session.commit()
    await session.refresh(config)

    if clave in (CLAVE_INTERVALO, CLAVE_HORA):
        await programar_desde_config(session)

    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="UPDATE",
        recurso_tipo="configuracion",
        recurso_id=config.id,
        detalles={"clave": clave, "antes": antes, "despues": data.valor},
    )
    await write_security_log(
        session,
        event_type="config_change",
        severity="WARNING",
        user={"user_id": me.id, "username": me.username, "role": me.rol},
        resource_type="configuracion",
        resource_id=str(config.id),
        operation="update",
        details={"clave": clave, "antes": antes, "despues": data.valor},
    )
    return config
