"""Patron Strategy para fuentes heterogeneas (RF-17 a RF-19).

TODAS las estrategias son SOLO LECTURA (RNF-10): nunca ejecutan DML sobre
SIGENU, SPI ni RRHH.
"""
import asyncio
import logging
from typing import Protocol

import pandas as pd

log = logging.getLogger("etl")


class DataSourceStrategy(Protocol):
    """Interfaz comun de fuentes de datos."""

    async def execute_query(self, query: str) -> pd.DataFrame: ...

    async def discover_schema(self, limite: int = 50) -> list[dict]: ...


class PostgresStrategy:
    """Lectura de PostgreSQL (SIGENU, SPI) con asyncpg."""

    def __init__(self, host: str, puerto: int, database: str, usuario: str, password: str) -> None:
        self._dsn = f"postgresql://{usuario}:{password}@{host}:{puerto}/{database}"

    async def execute_query(self, query: str) -> pd.DataFrame:
        import asyncpg

        async def _run() -> pd.DataFrame:
            conn = await asyncpg.connect(self._dsn, timeout=10)
            try:
                # Fuerza transaccion de solo lectura
                async with conn.transaction(readonly=True):
                    rows = await conn.fetch(query)
                    return pd.DataFrame([dict(r) for r in rows])
            finally:
                await conn.close()

        return await asyncio.wait_for(_run(), timeout=30)

    async def discover_schema(self, limite: int = 50) -> list[dict]:
        df = await self.execute_query(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
            f"ORDER BY table_name, ordinal_position LIMIT {int(limite * 50)}"
        )
        tablas: dict[str, list[str]] = {}
        for _, row in df.iterrows():
            tablas.setdefault(row["table_name"], []).append(row["column_name"])
        return [{"tabla": t, "columnas": c[:20]} for t, c in list(tablas.items())[:limite]]


class SqlServerStrategy:
    """Lectura de SQL Server (RRHH) con pyodbc en thread (no bloquea el loop)."""

    def __init__(self, host: str, puerto: int, database: str, usuario: str, password: str) -> None:
        self._conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host},{puerto};"
            f"DATABASE={database};UID={usuario};PWD={password};TrustServerCertificate=yes;"
            "ApplicationIntent=ReadOnly;"
        )

    def _query_sync(self, query: str) -> pd.DataFrame:
        import pyodbc

        with pyodbc.connect(self._conn_str, autocommit=True, timeout=10) as conn:
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            return pd.read_sql(query, conn)

    async def execute_query(self, query: str) -> pd.DataFrame:
        return await asyncio.wait_for(
            asyncio.to_thread(self._query_sync, query), timeout=30
        )

    async def discover_schema(self, limite: int = 50) -> list[dict]:
        df = await self.execute_query(
            "SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna FROM INFORMATION_SCHEMA.COLUMNS "
            f"ORDER BY TABLE_NAME, ORDINARY_POSITION LIMIT {int(limite * 50)}"
        )
        tablas: dict[str, list[str]] = {}
        for _, row in df.iterrows():
            tablas.setdefault(row["tabla"], []).append(row["columna"])
        return [{"tabla": t, "columnas": c[:20]} for t, c in list(tablas.items())[:limite]]


class ExcelStrategy:
    """Lectura de Excel/CSV (Movilidad Internacional, CTI indicadores)."""

    def __init__(self, ruta: str) -> None:
        self._ruta = ruta

    def _leer(self, hoja: str | int = 0) -> pd.DataFrame:
        if self._ruta.endswith(".csv"):
            return pd.read_csv(self._ruta)
        return pd.read_excel(self._ruta, sheet_name=hoja)

    async def execute_query(self, query: str) -> pd.DataFrame:
        """Excel no soporta SQL: la 'consulta' es la hoja nombre."""
        df = await asyncio.to_thread(self._leer, query or 0)
        return df

    async def discover_schema(self, limite: int = 50) -> list[dict]:
        df = await asyncio.to_thread(self._leer, 0)
        return [{"tabla": self._ruta.split("/")[-1], "columnas": list(df.columns)[:limite]}]


def construir_estrategia(
    tipo: str,
    *,
    host: str = "",
    puerto: int = 5432,
    database: str = "",
    usuario: str = "",
    password: str = "",
    ruta: str = "",
) -> DataSourceStrategy:
    """Factory de estrategias (OCP: agregar nuevas fuentes sin cambiar el caller).

    Args:
        tipo: postgresql|sqlserver|excel.
        host: servidor.
        puerto: puerto.
        database: base.
        usuario: usuario.
        password: password.
        ruta: archivo para Excel.

    Raises:
        ValueError: tipo desconocido.

    Returns:
        Estrategia lista para usar.
    """
    if tipo == "postgresql":
        return PostgresStrategy(host, puerto, database, usuario, password)
    if tipo == "sqlserver":
        return SqlServerStrategy(host, puerto, database, usuario, password)
    if tipo == "excel":
        return ExcelStrategy(ruta)
    raise ValueError(f"Tipo de fuente desconocido: {tipo}")
