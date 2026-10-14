from typing import Literal

# RF-04: 5 roles institucionales
RoleName = Literal[
    "administrador",
    "alta_direccion",
    "directivo",
    "jefe_proceso",
    "auditor",
]

ALL_ROLES: tuple[str, ...] = (
    "administrador",
    "alta_direccion",
    "directivo",
    "jefe_proceso",
    "auditor",
)

# Matriz RBAC: rol -> endpoints/acciones permitidas
RBAC: dict[str, set[str]] = {
    "administrador": {"usuarios", "catalogos", "fuentes", "config", "recalcular", "logs"},
    "alta_direccion": {"tablero", "indicadores", "fuentes", "config", "recalcular", "logs"},
    "directivo": {"tablero", "indicadores"},
    "jefe_proceso": {"tablero", "indicadores", "cargar_datos"},
    "auditor": {"tablero", "indicadores", "auditoria", "logs"},
}
