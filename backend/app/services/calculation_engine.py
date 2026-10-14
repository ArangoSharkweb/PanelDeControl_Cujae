"""Motor de calculo de indicadores (RF-36 a RF-40).

- Evalua formula con AST whitelist (formula_engine).
- Determina semaforo con umbrales de la meta.
- Escribe valor nuevo, vigencia anterior en NULL y snapshot (ACID).
- Aislamiento de fallos: un indicador fallido no detiene el recalc (RNF-07).
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalogos import Curso, Proceso
from app.models.importacion import RegistroImportado
from app.models.indicadores import (
    HistorialSnapshot,
    Indicador,
    ValorIndicador,
    VariableIndicador,
)
from app.utils.formula_engine import FormulaError, evaluar
from app.services.log_service import write_audit

log = logging.getLogger("calculo")

FUNC_SQL = {"COUNT": func.count, "SUM": func.sum, "AVG": func.avg, "MIN": func.min, "MAX": func.max}


async def valor_variable(session: AsyncSession, var: VariableIndicador) -> Decimal:
    """Calcula una variable agregando sobre registros_importados.

    Args:
        session: sesion async.
        var: variable del indicador.

    Returns:
        Decimal agregado.
    """
    if var.fuente_id is None or not var.columna or not var.funcion_agregacion:
        return Decimal(0)
    from sqlalchemy import Numeric, cast

    expr = cast(RegistroImportado.datos.op("->>")(var.columna), Numeric)
    stmt = select(FUNC_SQL[var.funcion_agregacion](expr)).where(
        RegistroImportado.fuente_id == var.fuente_id,
        RegistroImportado.normalizado.is_(True),
    )
    res = await session.execute(stmt)
    valor = res.scalar()
    return Decimal(str(valor or 0))


def semaforo(porcentaje: Decimal, verde: Decimal, amarillo: Decimal) -> str:
    """Clasifica estado del indicador (verde >=90, amarillo >=70, rojo <70 por defecto).

    Args:
        porcentaje: % de cumplimiento de meta.
        verde: umbral verde.
        amarillo: umbral amarillo.

    Returns:
        'verde' | 'amarillo' | 'rojo'.
    """
    if porcentaje >= verde:
        return "verde"
    if porcentaje >= amarillo:
        return "amarillo"
    return "rojo"


async def calcular_indicador(
    session: AsyncSession, indicador: Indicador, curso: Curso | None
) -> ValorIndicador | None:
    """Calcula y persiste un valor del indicador en transaccion ACID.

    Args:
        session: sesion async.
        indicador: indicador activo.
        curso: curso academico actual.

    Raises:
        FormulaError: formula invalida (capturado por recalcular_todos).

    Returns:
        ValorIndicador creado o None si no hay meta.
    """
    from app.repositories import indicador_repo

    meta = await indicador_repo.get_meta(session, indicador.id, curso.id if curso else None)
    if meta is None:
        return None

    if not indicador.variables:
        raise FormulaError(f"{indicador.codigo}: sin variables configuradas (dato faltante)")

    variables: dict[str, Decimal] = {}
    for var in indicador.variables:
        variables[var.nombre.upper()] = await valor_variable(session, var)

    formula = indicador.formula or "(A)"
    resultado = evaluar(formula, variables)
    if indicador.sentido == "descendente" and meta.valor_meta != 0:
        pct = (meta.valor_meta / resultado * 100) if resultado != 0 else Decimal(0)
    else:
        pct = (resultado / meta.valor_meta * 100) if meta.valor_meta != 0 else Decimal(0)
    pct = min(pct, Decimal(999.99))
    estado = semaforo(pct, meta.umbral_verde, meta.umbral_amarillo)
    ahora = datetime.now(timezone.utc)

    # Cerrar vigencia anterior en la misma transaccion (ACID)
    await session.execute(
        update(ValorIndicador)
        .where(
            ValorIndicador.indicador_id == indicador.id,
            ValorIndicador.curso_id == (curso.id if curso else None),
            ValorIndicador.vigente_hasta.is_(None),
        )
        .values(vigente_hasta=ahora)
    )
    valor = ValorIndicador(
        indicador_id=indicador.id,
        curso_id=curso.id if curso else None,
        valor=resultado,
        estado_semaforo=estado,
        porcentaje_meta=pct.quantize(Decimal("0.01")),
        calculado_en=ahora,
        fuente_origen="Calculo",
    )
    session.add(valor)
    await session.flush()

    periodo = curso.nombre if curso else ahora.strftime("%Y-%m")
    snap = await session.execute(
        select(HistorialSnapshot).where(
            HistorialSnapshot.indicador_id == indicador.id,
            HistorialSnapshot.periodo == periodo,
        )
    )
    existente = snap.scalar_one_or_none()
    if existente:
        existente.valor = resultado
        existente.estado_semaforo = estado
    else:
        session.add(
            HistorialSnapshot(
                indicador_id=indicador.id,
                periodo=periodo,
                valor=resultado,
                estado_semaforo=estado,
            )
        )
    await session.commit()
    return valor


async def recalcular_todos(session: AsyncSession) -> dict:
    """Recalcula todos los indicadores activos aislando fallos por indicador (RNF-07).

    Args:
        session: sesion async.

    Returns:
        Estadisticas {"calculados": n, "errores": n, "detalles": [...]}.
    """
    res = await session.execute(
        select(Indicador, Proceso)
        .join(Proceso, Indicador.proceso_id == Proceso.id)
        .where(Indicador.activo.is_(True))
        .options(selectinload(Indicador.variables))
    )
    pairs = list(res.all())
    curso_res = await session.execute(select(Curso).where(Curso.es_curso_actual.is_(True)))
    curso = curso_res.scalars().first()

    # Detach con relaciones ya cargadas: cada iteracion hace commit/rollback
    # y los objetos no deben volver a tocar la BD (async -> MissingGreenlet).
    for indicador, _ in pairs:
        session.expunge(indicador)
    if curso is not None:
        session.expunge(curso)

    calculados = errores = 0
    detalles: list[str] = []
    for indicador, _ in pairs:
        codigo = indicador.codigo
        try:
            valor = await calcular_indicador(session, indicador, curso)
            if valor is not None:
                calculados += 1
        except Exception as exc:  # noqa: BLE001 - aislamiento RNF-07
            errores += 1
            detalles.append(f"{codigo}: {exc}")
            await session.rollback()
            log.error("Fallo calculo %s: %s", codigo, exc)

    await write_audit(
        session,
        usuario_id=None,
        accion="RECALC",
        recurso_tipo="indicador",
        detalles={"calculados": calculados, "errores": errores},
    )
    return {"calculados": calculados, "errores": errores, "detalles": detalles}
