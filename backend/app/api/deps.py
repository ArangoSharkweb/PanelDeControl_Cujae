from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security.rbac import RBAC
from app.security.jwt import decode_token
from app.repositories import usuario_repo
from app.schemas.auth import MeOut

bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_db),
) -> MeOut:
    """Resuelve el usuario del JWT.

    Args:
        creds: cabecera Authorization Bearer.
        session: sesion async.

    Raises:
        HTTPException 401: token invalido o usuario inactivo.

    Returns:
        Perfil del usuario autenticado.
    """
    try:
        payload = decode_token(creds.credentials)
        user_id = UUID(str(payload.get("sub")))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido")
    user = await usuario_repo.get_by_id(session, user_id)
    if user is None or not user.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario invalido")
    return MeOut(
        id=str(user.id),
        username=user.username,
        email=user.email,
        rol=user.rol,
        auth_type=user.auth_type,
        alcance_tipo=user.alcance_tipo,
        alcance_id=str(user.alcance_id) if user.alcance_id else None,
    )


def require(*permissions: str):
    """Fabrica dependencia RBAC: exige al menos una de las permisos dadas.

    Usa la matriz core.rbac.RBAC (RF-04).

    Args:
        *permissions: permisos requeridos ('tablero','indicadores','config',...).

    Returns:
        Dependencia FastAPI.
    """

    async def _check(me: MeOut = Depends(get_current_user)) -> MeOut:
        granted = RBAC.get(me.rol, set())
        if not any(p in granted for p in permissions):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin permiso para esta operacion")
        return me

    return _check


require_admin = require("usuarios", "config")
require_logs = require("logs")
require_indicadores = require("indicadores")
