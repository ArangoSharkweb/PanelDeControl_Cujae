from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.security.ldap import authenticate_ldap
from app.security.jwt import create_access_token, verify_password
from app.models.usuarios import Usuario
from app.repositories import usuario_repo
from app.services.log_service import write_audit, write_security_log


async def authenticate(
    session: AsyncSession,
    username: str,
    password: str,
    ip: str = "",
    user_agent: str = "",
) -> tuple[Usuario, str]:
    """Autentica contra cuenta local (bcrypt) o LDAP institucional y emite JWT.

    RF-01/02. Si el bind LDAP es exitoso y el usuario no existe en la BD,
    se aprovisiona con rol directivo por defecto (sin permisos elevados).

    Args:
        session: sesion async.
        username: login.
        password: clave en claro.
        ip: IP del cliente para logs.
        user_agent: User-Agent del cliente.

    Raises:
        HTTPException 401: credenciales invalidas o usuario inactivo.

    Returns:
        Tupla (usuario, token JWT).
    """
    user = await usuario_repo.get_by_username(session, username)
    if user is not None and not user.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inactivo")

    if user is not None and user.auth_type == "local":
        if not verify_password(password, user.password_hash):
            await _audit_fail(session, user, ip, user_agent, "failed_login")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
        token = create_access_token(user.id, user.username)
        await _audit_ok(session, user, ip, user_agent, "login")
        return user, token

    if await authenticate_ldap(username, password):
        if user is None:
            user = Usuario(username=username, auth_type="ldap", rol="directivo", activo=True)
            session.add(user)
            await session.flush()
        token = create_access_token(user.id, user.username)
        await _audit_ok(session, user, ip, user_agent, "login")
        return user, token

    if user is not None:
        await _audit_fail(session, user, ip, user_agent, "failed_login")
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")


def _payload(user: Usuario) -> dict:
    return {
        "user_id": str(user.id),
        "username": user.username,
        "role": user.rol,
        "auth_type": user.auth_type,
        "email": user.email,
    }


async def _audit_ok(
    session: AsyncSession, user: Usuario, ip: str, ua: str, event: str
) -> None:
    await write_security_log(
        session,
        event_type=event,
        user=_payload(user),
        ip=ip,
        user_agent=ua,
        resource_type="usuario",
        resource_id=str(user.id),
        operation="login",
    )
    await write_audit(
        session,
        usuario_id=user.id,
        accion="LOGIN",
        recurso_tipo="usuario",
        recurso_id=user.id,
        detalles={"ip": ip, "auth_type": user.auth_type},
    )


async def _audit_fail(
    session: AsyncSession, user: Usuario, ip: str, ua: str, event: str
) -> None:
    await write_security_log(
        session,
        event_type=event,
        severity="WARNING",
        user=_payload(user),
        ip=ip,
        user_agent=ua,
        resource_type="usuario",
        resource_id=str(user.id),
        operation="login",
    )
    await write_audit(
        session,
        usuario_id=user.id,
        accion="LOGIN_FAIL",
        recurso_tipo="usuario",
        recurso_id=user.id,
        detalles={"ip": ip},
    )
