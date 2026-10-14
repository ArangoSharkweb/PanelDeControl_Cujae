"""Evaluador de formulas de indicadores sin eval() nativo (seguridad).

Soporta: numeros, variables [A-Za-z], + - * / % ( ) y funciones basicas.
AST whitelist: evita ejecucion arbitraria (riesgo de inyeccion de codigo).
"""
import ast
import operator
from decimal import Decimal

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class FormulaError(ValueError):
    """Formula invalida o division por cero."""


def evaluar(formula: str, variables: dict[str, Decimal | float | int]) -> Decimal:
    """Evalua una formula de indicador con seguridad (AST whitelist).

    Args:
        formula: expresion matematica, ej "(A / B) * 100".
        variables: valores de las variables, ej {"A": 10, "B": 4}.

    Returns:
        Resultado como Decimal.

    Raises:
        FormulaError: si la expresion o una variable es invalida.
    """
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"Formula con sintaxis invalida: {exc}") from exc

    def _eval(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise FormulaError(f"Variable '{node.id}' sin valor")
            return Decimal(str(variables[node.id]))
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            left, right = _eval(node.left), _eval(node.right)
            try:
                result = _BINOPS[type(node.op)](left, right)
            except ZeroDivisionError as exc:
                raise FormulaError("Division por cero en la formula") from exc
            return Decimal(str(result))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](_eval(node.operand))
        raise FormulaError(f"Expresion no permitida: {type(node).__name__}")

    return _eval(tree)
