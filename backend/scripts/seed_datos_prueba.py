"""Puebla las tablas del proyecto con datos de prueba de la CUJAE.

Uso (desde backend/):  python scripts/seed_datos_prueba.py
Requiere backend/.env con DATABASE_URL (o DATABASE_URL_SYNC).
Idempotente: trunca las tablas involucradas y vuelve a insertar.
"""
import pathlib
import re
import sys

import psycopg2

AQUI = pathlib.Path(__file__).resolve().parent.parent  # backend/
env = (AQUI / ".env").read_text(encoding="utf-8")


def valor(clave: str, opcional: str | None = None) -> str:
    m = re.search(rf"^{clave}=(.+)$", env, re.M)
    if m:
        return m.group(1).strip()
    if opcional:
        return opcional
    sys.exit(f"Falta {clave} en backend/.env")


url = valor("DATABASE_URL").replace("+asyncpg", "")
m = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)", url)
user, pw, host, puerto, dbname = m.groups()

conn = psycopg2.connect(user=user, password=pw, host=host, port=puerto or "5432", dbname=dbname)
conn.autocommit = False
cur = conn.cursor()

# --- Limpieza (orden inverso a dependencias; CASCADE cubre el resto) ---
for tabla in (
    "auditoria.notificaciones",
    "auditoria.log_ai_analysis",
    "auditoria.security_logs",
    "auditoria.auditoria",
    "importacion.registros_importados",
    "indicadores.narrativas_ia",
    "indicadores.valores_indicadores",
    "indicadores.historial_snapshot",
    "indicadores.metas_indicador",
    "indicadores.variables_indicador",
    "indicadores.indicadores",
    "indicadores.fuentes_datos",
    "config.unidades_organizativas",
    "config.metricas_proceso",
    "config.objetivos_estrategicos",
    "config.cursos",
    "config.procesos",
    "config.configuracion_sistema",
):
    cur.execute(f"TRUNCATE {tabla} RESTART IDENTITY CASCADE")

# --- Usuarios extra (misma password_hash que el admin) ---
cur.execute("SELECT password_hash FROM config.usuarios WHERE username = 'admin'")
fila = cur.fetchone()
hash_admin = fila[0] if fila else None
if not hash_admin:
    print("AVISO: el admin no tiene password_hash; los usuarios extra quedan sin hash.")

usuarios = [
    ("directivo", "directivo@cujae.edu.cu", "directivo", None, None),
    ("dir_docencia", "dir_docencia@cujae.edu.cu", "alta_direccion", "unidad", None),
    ("jefe_doc", "jefe_doc@cujae.edu.cu", "jefe_proceso", "proceso", "cccccccc-0000-0000-0000-000000000001"),
    ("jefe_inv", "jefe_inv@cujae.edu.cu", "jefe_proceso", "proceso", "cccccccc-0000-0000-0000-000000000002"),
    ("auditor", "auditor@cujae.edu.cu", "auditor", None, None),
]
cur.executemany(
    """
    INSERT INTO config.usuarios (username, password_hash, email, rol, auth_type, alcance_tipo, alcance_id)
    VALUES (%s, %s, %s, %s, 'local', %s, NULL)
    ON CONFLICT (username) DO NOTHING
    """,
    [(u, hash_admin, e, r, at) for u, e, r, at, _ in usuarios],
)
# alcance_id de jefes: se resuelve tras insertar procesos (ver mas abajo)

# --- Cursos ---
cur.execute(
    """
    INSERT INTO config.cursos (id, nombre, anio_inicio, anio_fin, activo, es_curso_actual)
    VALUES
        ('aaaaaaaa-0000-0000-0000-000000000001', '2024-2025', 2024, 2025, true, true),
        ('aaaaaaaa-0000-0000-0000-000000000002', '2023-2024', 2023, 2024, true, false)
    """
)
CURSO_ACTUAL = "aaaaaaaa-0000-0000-0000-000000000001"
CURSO_ANTERIOR = "aaaaaaaa-0000-0000-0000-000000000002"

# --- Procesos ---
procesos = [
    ("cccccccc-0000-0000-0000-000000000001", "PRO-D01", "Docencia de Pregrado", "proceso"),
    ("cccccccc-0000-0000-0000-000000000002", "PRO-I01", "Investigacion Cientifica", "proceso"),
    ("cccccccc-0000-0000-0000-000000000003", "PRO-E01", "Extension Universitaria", "proceso"),
    ("cccccccc-0000-0000-0000-000000000004", "PRO-G01", "Gestion Academica", "proceso"),
    ("cccccccc-0000-0000-0000-000000000005", "PRO-A01", "Apoyo Institucional", "proceso"),
]
cur.executemany(
    """
    INSERT INTO config.procesos (id, codigo, nombre, tipo, activo)
    VALUES (%s, %s, %s, %s, true)
    """,
    procesos,
)
# alcance de los jefes de proceso
cur.execute("UPDATE config.usuarios SET alcance_id = 'cccccccc-0000-0000-0000-000000000001' WHERE username = 'jefe_doc'")
cur.execute("UPDATE config.usuarios SET alcance_id = 'cccccccc-0000-0000-0000-000000000002' WHERE username = 'jefe_inv'")

# --- Unidades ---
cur.executemany(
    """
    INSERT INTO config.unidades_organizativas (id, codigo, nombre, tipo, activo)
    VALUES (%s, %s, %s, %s, true)
    """,
    [
        ("bbbbbbbb-0000-0000-0000-000000000001", "FIU", "Facultad de Ingenieria Universidad", "facultad"),
        ("bbbbbbbb-0000-0000-0000-000000000002", "FQ", "Facultad de Quimica", "facultad"),
        ("bbbbbbbb-0000-0000-0000-000000000003", "FAD", "Facultad de Arquitectura", "facultad"),
        ("bbbbbbbb-0000-0000-0000-000000000004", "DIR-DOC", "Direccion de Docencia", "direccion"),
    ],
)

# --- Indicadores: (id, codigo, nombre, proceso, periodicidad, sentido, unidad, esencial) ---
indicadores = [
    ("dddddddd-0000-0000-0000-000000000001", "GRAD-01", "Tasa de graduacion oportuna", "cccccccc-0000-0000-0000-000000000001", "anual", "ascendente", "%", True),
    ("dddddddd-0000-0000-0000-000000000002", "MAT-01", "Matricula de pregrado", "cccccccc-0000-0000-0000-000000000001", "anual", "ascendente", "estudiantes", True),
    ("dddddddd-0000-0000-0000-000000000003", "APR-01", "Tasa de aprobacion en asignaturas", "cccccccc-0000-0000-0000-000000000001", "semestral", "ascendente", "%", True),
    ("dddddddd-0000-0000-0000-000000000004", "POS-01", "Docentes con posgrado", "cccccccc-0000-0000-0000-000000000004", "anual", "ascendente", "%", True),
    ("dddddddd-0000-0000-0000-000000000005", "ART-01", "Articulos en revistas indexadas", "cccccccc-0000-0000-0000-000000000002", "anual", "ascendente", "articulos", True),
    ("dddddddd-0000-0000-0000-000000000006", "PRO-01", "Proyectos de investigacion financiados", "cccccccc-0000-0000-0000-000000000002", "anual", "ascendente", "proyectos", False),
    ("dddddddd-0000-0000-0000-000000000007", "HOR-01", "Horas de servicio comunitario", "cccccccc-0000-0000-0000-000000000003", "anual", "ascendente", "horas", False),
    ("dddddddd-0000-0000-0000-000000000008", "SAT-01", "Satisfaccion de estudiantes", "cccccccc-0000-0000-0000-000000000004", "semestral", "ascendente", "puntos (1-5)", True),
    ("dddddddd-0000-0000-0000-000000000009", "EME-01", "Egresados con empleo a 12 meses", "cccccccc-0000-0000-0000-000000000003", "anual", "ascendente", "%", False),
    ("dddddddd-0000-0000-0000-000000000010", "COS-01", "Costo por estudiante", "cccccccc-0000-0000-0000-000000000005", "anual", "descendente", "CUC/estudiante", False),
]
cur.executemany(
    """
    INSERT INTO indicadores.indicadores
        (id, codigo, nombre, descripcion, unidad_medida, periodicidad, sentido, formula,
         proceso_id, nivel, esencial, activo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, '(A)', %s, 'Universidad', %s, true)
    """,
    [
        (
            iid, cod, nom,
            f"Indicador de prueba para {nom.lower()}",
            uni, per, sen, pid, es,
        )
        for iid, cod, nom, pid, per, sen, uni, es in indicadores
    ],
)

# --- Fuente de prueba + variables del motor de calculo ---
# Cada indicador tiene una variable 'A' con columna propia en los registros
# importados (mas abajo), lo que permite recalcular con el motor real.
cur.execute(
    """
    INSERT INTO indicadores.fuentes_datos
        (id, codigo, nombre, tipo, motor, host, puerto, database, credenciales_cifradas,
         activo, solo_lectura)
    VALUES ('eeeeeeee-0000-0000-0000-000000000001', 'FTE-PRUEBA',
            'Fuente de datos de prueba (local)', 'postgresql', 'postgresql',
            'localhost', 6512, 'cujae_tablero', NULL, true, true)
    """
)
FUENTE_PRUEBA = "eeeeeeee-0000-0000-0000-000000000001"
SIN_VARIABLE = "dddddddd-0000-0000-0000-000000000009"  # EME-01: dato faltante deliberado
cur.executemany(
    """
    INSERT INTO indicadores.variables_indicador
        (id, indicador_id, nombre, fuente_id, tabla, columna, funcion_agregacion, filtros)
    VALUES (%s, %s, 'A', %s, 'datos_prueba', %s, 'SUM', '{}')
    """,
    [
        (
            f"ffffffff-0000-0000-0000-{n:012d}",
            iid,
            FUENTE_PRUEBA,
            f"valor_{cod.lower()}",
        )
        for n, (iid, cod, *_resto) in enumerate(indicadores, start=1)
        if iid != SIN_VARIABLE
    ],
)

# --- Configuracion del recalculo (vista Calculo de indicadores) ---
cur.executemany(
    """
    INSERT INTO config.configuracion_sistema (clave, valor, descripcion, ultima_modificacion_en)
    VALUES (%s, %s, %s, now())
    """,
    [
        (
            "intervalo_recalculo_horas",
            "6",
            "Cada cuantos horas se ejecuta el recalculo de indicadores",
        ),
        ("hora_recalculo", "02:00", "Hora diaria de recalculo (modo fallback)"),
    ],
)

# --- Metas (curso actual) y valores actuales ---
# (indicador, meta, valor, porcentaje_meta, estado)
filas_valores = [
    ("dddddddd-0000-0000-0000-000000000001", 85.0, 78.4, 92.24, "verde"),
    ("dddddddd-0000-0000-0000-000000000002", 12000.0, 11450.0, 95.42, "verde"),
    ("dddddddd-0000-0000-0000-000000000003", 80.0, 68.3, 85.38, "amarillo"),
    ("dddddddd-0000-0000-0000-000000000004", 60.0, 41.0, 68.33, "rojo"),
    ("dddddddd-0000-0000-0000-000000000005", 120.0, 74.0, 61.67, "rojo"),
    ("dddddddd-0000-0000-0000-000000000006", 30.0, 28.0, 93.33, "verde"),
    ("dddddddd-0000-0000-0000-000000000007", 50000.0, 47500.0, 95.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000008", 4.2, 3.9, 92.86, "verde"),
    ("dddddddd-0000-0000-0000-000000000009", 70.0, None, None, None),  # dato faltante: alerta deliberada
    ("dddddddd-0000-0000-0000-000000000010", 3500.0, 3850.0, 90.91, "verde"),  # sentido descendente: 3500/3850
]
cur.executemany(
    """
    INSERT INTO indicadores.metas_indicador (indicador_id, curso_id, valor_meta, umbral_verde, umbral_amarillo)
    VALUES (%s, %s, %s, 90, 70)
    """,
    [(iid, CURSO_ACTUAL, meta) for iid, meta, *_ in filas_valores],
)
cur.executemany(
    """
    INSERT INTO indicadores.valores_indicadores
        (indicador_id, curso_id, valor, estado_semaforo, porcentaje_meta, calculado_en, fuente_origen)
    VALUES (%s, %s, %s, %s, %s, now(), 'etl_manual')
    """,
    [(iid, CURSO_ACTUAL, val, est, pct) for iid, meta, val, pct, est in filas_valores],
)

# --- Registros de prueba (una fila por indicador, columna propia) ---
codigos = {iid: cod for iid, cod, *_ in indicadores}
cur.executemany(
    """
    INSERT INTO importacion.registros_importados
        (fuente_id, tabla_origen, fila_original, datos, normalizado, conciliado)
    VALUES (%s, 'datos_prueba', %s, %s::jsonb, true, true)
    """,
    [
        (FUENTE_PRUEBA, n, '{"valor_%s": %s}' % (codigos[iid].lower(), val))
        for n, (iid, _meta, val, _pct, _est) in enumerate(filas_valores, start=1)
        if val is not None
    ],
)

# --- Historial del periodo anterior (para variacion) ---
anteriores = [
    ("dddddddd-0000-0000-0000-000000000001", 81.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000002", 11980.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000003", 74.5, "verde"),
    ("dddddddd-0000-0000-0000-000000000004", 38.5, "verde"),
    ("dddddddd-0000-0000-0000-000000000005", 145.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000006", 25.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000007", 43000.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000008", 4.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000009", 62.0, "verde"),
    ("dddddddd-0000-0000-0000-000000000010", 3600.0, "verde"),
]
cur.executemany(
    """
    INSERT INTO indicadores.historial_snapshot (indicador_id, periodo, valor, estado_semaforo)
    VALUES (%s, '2023-2024', %s, %s)
    """,
    anteriores,
)

# --- Notificaciones de alerta ---
cur.executemany(
    """
    INSERT INTO auditoria.notificaciones (usuario_id, tipo, mensaje, indicador_id, leida)
    SELECT u.id, 'alerta_semaforo', %s, %s, false
    FROM config.usuarios u WHERE u.username = %s
    """,
    [
        ("Semáforo en rojo: Docentes con posgrado (68.3% de la meta)", "dddddddd-0000-0000-0000-000000000004", "directivo"),
        ("Semáforo en rojo: Artículos indexados (61.7% de la meta)", "dddddddd-0000-0000-0000-000000000005", "directivo"),
        ("Dato faltante: Egresados con empleo a 12 meses", "dddddddd-0000-0000-0000-000000000009", "jefe_doc"),
    ],
)

conn.commit()
cur.execute("SELECT count(*) FROM indicadores.indicadores")
print(f"OK: {cur.fetchone()[0]} indicadores insertados en {dbname}")
cur.execute(
    "SELECT count(*) FROM indicadores.valores_indicadores WHERE valor IS NULL"
)
print(f"Valores nulos (alerta deliberada): {cur.fetchone()[0]}")
conn.close()
