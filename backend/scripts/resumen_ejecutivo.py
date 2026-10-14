"""Resumen ejecutivo en una sola pasada: SQL -> texto -> freellmpool -> narrativa.

Uso (desde cualquier directorio):
    python backend/scripts/resumen_ejecutivo.py

No escribe archivos intermedios: consulta la base, convierte el resultado a
texto en memoria y lo pasa directamente a la API Python de freellmpool.
"""
import pathlib
import re
import sys
import time

AQUI = pathlib.Path(__file__).resolve().parent.parent  # backend/

INSTRUCCION = (
    "Redacta la narrativa ejecutiva FINAL (sin razonamiento, sin intro) en espanol "
    "neutro, 150-250 palabras, tercera persona, sin emojis ni markdown, con estas 4 "
    "secciones numeradas exactas: 1) Titular: 1 frase con la conclusion principal. "
    "2) Que cambio y por que importa: 3-5 frases interpretando TODOS los indicadores "
    "de los datos (no te limites al primero); usa los valores, % de meta y variacion. "
    "Si un indicador dice sentido descendente, subir el valor es malo. "
    "3) Senales de alerta: 1-2 frases; menciona los semaforos en rojo o amarillo, "
    "variaciones fuera de lo esperado (>15% o <-15%) y cualquier (sin dato); "
    "sugiere una causa probable. 4) Proximos pasos: exactamente 3 acciones concretas, "
    "cada una asignada a un rol (Docencia, Investigacion y Direccion); prohibido "
    "responder solo con la frase seguir monitoreando. No inventes datos. "
    "IMPORTANTE: no muestres analisis, pasos intermedios ni razonamiento; tu respuesta "
    "COMIENZA literalmente con '1)' y termina en la seccion 4."
)

CONSULTA = """
    SELECT i.codigo,
           i.nombre,
           p.nombre AS proceso,
           i.periodicidad,
           i.sentido,
           i.unidad_medida,
           v.valor,
           m.valor_meta,
           v.porcentaje_meta,
           v.estado_semaforo,
           h.valor AS valor_anterior_2023_2024,
           CASE
               WHEN v.valor IS NOT NULL AND h.valor IS NOT NULL AND h.valor <> 0
               THEN round(((v.valor - h.valor) / h.valor * 100)::numeric, 1)
           END AS variacion_pct
    FROM indicadores.valores_indicadores v
    JOIN indicadores.indicadores i ON i.id = v.indicador_id
    LEFT JOIN config.procesos p ON p.id = i.proceso_id
    LEFT JOIN indicadores.metas_indicador m
           ON m.indicador_id = i.id AND m.curso_id = v.curso_id
    LEFT JOIN indicadores.historial_snapshot h
           ON h.indicador_id = i.id AND h.periodo = '2023-2024'
    WHERE v.vigente_hasta IS NULL
    ORDER BY i.codigo
"""


def consultar() -> list[dict]:
    """Ejecuta la consulta de metricas y devuelve filas como dicts."""
    env = (AQUI / ".env").read_text(encoding="utf-8")
    url = re.search(r"^DATABASE_URL=(.+)$", env, re.M).group(1).strip().replace("+asyncpg", "")
    m = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)", url)
    import psycopg2

    conn = psycopg2.connect(
        user=m.group(1),
        password=m.group(2),
        host=m.group(3),
        port=m.group(4) or "5432",
        dbname=m.group(5),
        connect_timeout=5,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(CONSULTA)
            columnas = [d[0] for d in cur.description]
            return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
    finally:
        conn.close()


def a_texto(filas: list[dict]) -> str:
    """Convierte las filas a una tabla compacta (sin archivo intermedio)."""
    lineas = [
        "Periodo actual 2024-2025; periodo anterior 2023-2024; "
        "%meta = cumplimiento; variacion_pct = cambio vs anterior.",
        "codigo | nombre | proceso | sentido | valor | meta | %meta | semaforo | anterior | variacion%",
    ]
    for f in filas:
        campo = lambda v: "(sin dato)" if v is None else str(v)  # noqa: E731
        lineas.append(
            " | ".join(
                [
                    f["codigo"],
                    f["nombre"],
                    f["proceso"] or "-",
                    f["sentido"],
                    campo(f["valor"]),
                    campo(f["valor_meta"]),
                    campo(f["porcentaje_meta"]),
                    campo(f["estado_semaforo"]),
                    campo(f["valor_anterior_2023_2024"]),
                    campo(f["variacion_pct"]),
                ]
            )
        )
    return "\n".join(lineas)


def narrar(datos: str) -> tuple[str, str]:
    """Invoca freellmpool (con cadena de respaldo de proveedores) y devuelve (texto, proveedor)."""
    from freellmpool import AllProvidersExhausted, Pool

    pool = Pool.from_default_config()
    intentos: list[list[str] | None] = [["pollinations"], None, ["llm7"], ["ovh"]]
    ultimo: Exception | None = None
    for proveedores in intentos:
        try:
            reply = pool.ask(
                datos,
                system=INSTRUCCION,
                max_tokens=1500,
                timeout=60.0,
                providers=proveedores,
            )
            origen = f"{reply.provider_id}/{reply.model}{' (cache)' if reply.cached else ''}"
            return reply.text, origen
        except AllProvidersExhausted as exc:
            ultimo = exc
    raise ultimo if ultimo else RuntimeError("sin proveedores")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    filas = consultar()
    datos = a_texto(filas)
    texto, proveedor = narrar(datos)
    print(texto, flush=True)
    elapsed = time.perf_counter() - t0
    print(f"\n[{elapsed:.1f}s | {len(filas)} indicadores | {proveedor}]", file=sys.stderr)


if __name__ == "__main__":
    main()

