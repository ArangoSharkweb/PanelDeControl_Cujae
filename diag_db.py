"""Diagnostico: lista esquemas/tablas reales y version de alembic."""
import pathlib
import re
import sys

env_path = pathlib.Path(__file__).with_name("backend") / ".env"
env = env_path.read_text(encoding="utf-8")


def valor(clave: str) -> str:
    m = re.search(rf"^{clave}=(.+)$", env, re.M)
    if not m:
        sys.exit(f"Falta {clave} en backend/.env")
    return m.group(1).strip()


url = valor("DATABASE_URL").replace("+asyncpg", "")
m = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)", url)
if not m:
    sys.exit(f"URL no parseable: {url}")
user, pw, host, puerto, dbname = m.groups()
puerto = puerto or "5432"

import psycopg2

conn = psycopg2.connect(user=user, password=pw, host=host, port=puerto, dbname=dbname)
conn.autocommit = True
cur = conn.cursor()

print(f"Conectado a: {host}:{puerto}/{dbname} (usuario {user})")

cur.execute(
    "SELECT table_schema, table_name FROM information_schema.tables "
    "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
    "ORDER BY table_schema, table_name"
)
filas = cur.fetchall()
print(f"\nObjetos ({len(filas)}):")
actual = None
for esquema, tabla in filas:
    if esquema != actual:
        actual = esquema
        print(f"  [{esquema}]")
    print(f"    {tabla}")

try:
    cur.execute("SELECT * FROM alembic_version")
    print("\nalembic_version:", cur.fetchall())
except Exception as e:
    print("\nalembic_version:", e)

# bases de datos disponibles en el servidor
cur.execute("SELECT datname FROM pg_database WHERE datallowconn ORDER BY 1")
print("\nBases en el servidor:", [r[0] for r in cur.fetchall()])

conn.close()
