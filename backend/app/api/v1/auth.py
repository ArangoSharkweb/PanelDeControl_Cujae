import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.auth import LoginIn, MeOut, TokenOut
from app.services import auth_service

router = APIRouter(prefix="/auth")

_attempts: dict[str, list[float]] = {}

LOGIN_LIMIT = 5
LOGIN_WINDOW = 60


def _rate_limit(key: str, limit: int = LOGIN_LIMIT, window: int = LOGIN_WINDOW) -> None:
    """Rate limiting RNF-08: maximo 5 intentos de login por minuto por IP+usuario.

    Args:
        key: clave compuesta ip:username.
        limit: intentos maximos.
        window: ventana en segundos.

    Raises:
        HTTPException 429: si se supera el limite.
    """
    now = time.monotonic()
    hits = [t for t in _attempts.get(key, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos de login")
    hits.append(now)
    _attempts[key] = hits


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, session: AsyncSession = Depends(get_db)) -> TokenOut:
    """Autentica (local o LDAP) y emite JWT con rate limiting.

    Args:
        body: credenciales.
        request: request HTTP para obtener IP.
        session: sesion async.

    Returns:
        Token bearer.
    """
    ip = request.client.host if request.client else "unknown"
    _rate_limit(f"{ip}:{body.username}")
    _, token = await auth_service.authenticate(
        session,
        body.username,
        body.password,
        ip=ip,
        user_agent=request.headers.get("user-agent", ""),
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
async def me(current: MeOut = Depends(get_current_user)) -> MeOut:
    """Devuelve perfil y rol del token actual.

    Args:
        current: usuario resuelto del JWT.

    Returns:
        Perfil.
    """
    return current
