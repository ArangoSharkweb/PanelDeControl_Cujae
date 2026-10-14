"""Tests basicos: formula engine, semaforo y matriz RBAC."""
from decimal import Decimal

import pytest

from app.security.rbac import RBAC
from app.services.calculation_engine import semaforo
from app.utils.formula_engine import FormulaError, evaluar


def test_formula_basica():
    resultado = evaluar("(A / B) * 100", {"A": Decimal(35), "B": Decimal(100)})
    assert resultado == Decimal("35")


def test_formula_division_por_cero():
    with pytest.raises(FormulaError):
        evaluar("A / B", {"A": Decimal(10), "B": Decimal(0)})


def test_formula_rechaza_import():
    with pytest.raises(FormulaError):
        evaluar("__import__('os')", {"A": Decimal(1)})


def test_formula_variable_faltante():
    with pytest.raises(FormulaError):
        evaluar("A + B", {"A": Decimal(1)})


def test_semaforo_verde():
    assert semaforo(Decimal(95), Decimal(90), Decimal(70)) == "verde"


def test_semaforo_amarillo():
    assert semaforo(Decimal(75), Decimal(90), Decimal(70)) == "amarillo"


def test_semaforo_rojo():
    assert semaforo(Decimal(69), Decimal(90), Decimal(70)) == "rojo"


def test_rbac_5_roles():
    assert set(RBAC) == {"administrador", "alta_direccion", "directivo", "jefe_proceso", "auditor"}


def test_rbac_auditor_no_config():
    assert "config" not in RBAC["auditor"]
    assert "auditoria" in RBAC["auditor"]


def test_rbac_directivo_solo_consulta():
    assert RBAC["directivo"] == {"tablero", "indicadores"}
