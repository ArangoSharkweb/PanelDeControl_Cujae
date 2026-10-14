import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import MeOut, require
from app.database import get_db
from app.security.jwt import hash_password
from app.models.usuarios import Usuario
from app.schemas.usuarios import PasswordResetIn, UsuarioIn, UsuarioOut
from app.services.log_service import write_audit, write_security_log

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
async def listar(
    _: MeOut = Depends(require("usuarios")),
    session: AsyncSession = Depends(get_db),
) -> list[Usuario]:
    """Lista usuarios (solo administrador).

    Args:
        _: usuario administrador.
        session: sesion async.

    Returns:
        Todos los usuarios.
    """
    res = await session.execute(select(Usuario).order_by(Usuario.username))
    return list(res.scalars().all())  # type: ignore[return-value]


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def crear(
    data: UsuarioIn,
    me: MeOut = Depends(require("usuarios")),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    """Crea usuario local o LDAP.

    Args:
        data: payload validado (password >= 8 chars).
        me: administrador.
        session: sesion async.

    Raises:
        HTTPException 409: username duplicado o cuenta local sin password.

    Returns:
        Usuario creado.
    """
    res = await session.execute(select(Usuario).where(Usuario.username == data.username))
    if res.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username ya existe")
    if data.auth_type == "local" and not data.password:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Password requerido para cuenta local"
        )

    payload = data.model_dump(exclude={"password"})
    usuario = Usuario(**payload)
    if data.password:
        usuario.password_hash = hash_password(data.password)
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)

    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="CREATE",
        recurso_tipo="usuario",
        recurso_id=usuario.id,
        detalles={"username": usuario.username, "rol": usuario.rol},
    )
    await write_security_log(
        session,
        event_type="user_create",
        user={"user_id": me.id, "username": me.username, "role": me.rol},
        resource_type="usuario",
        resource_id=str(usuario.id),
        operation="create",
        details={"username": usuario.username, "rol": usuario.rol},
    )
    return usuario


@router.put("/{usuario_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    usuario_id: uuid.UUID,
    data: PasswordResetIn,
    me: MeOut = Depends(require("usuarios")),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Reset de password por administrador (auditado).

    Args:
        usuario_id: UUID del usuario.
        data: nueva password.
        me: administrador.
        session: sesion async.

    Raises:
        HTTPException 404: usuario no encontrado.
    """
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    usuario.password_hash = hash_password(data.nueva_password)
    usuario.auth_type = "local"
    await session.commit()

    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="PASSWORD_RESET",
        recurso_tipo="usuario",
        recurso_id=usuario.id,
        detalles={"target": usuario.username},
    )
    await write_security_log(
        session,
        event_type="password_reset",
        severity="WARNING",
        user={"user_id": me.id, "username": me.username, "role": me.rol},
        resource_type="usuario",
        resource_id=str(usuario.id),
        operation="update",
    )


@router.put("/{usuario_id}", response_model=UsuarioOut)
async def modificar(
    usuario_id: uuid.UUID,
    data: UsuarioIn,
    me: MeOut = Depends(require("usuarios")),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    """Modifica usuario (rol, alcance, estado).

    Args:
        usuario_id: UUID.
        data: payload validado.
        me: administrador.
        session: sesion async.

    Raises:
        HTTPException 404: no encontrado.

    Returns:
        Usuario modificado.
    """
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    antes = {"rol": usuario.rol, "activo": usuario.activo}
    for key, value in data.model_dump(exclude={"password"}).items():
        setattr(usuario, key, value)
    await session.commit()
    await session.refresh(usuario)

    await write_audit(
        session,
        usuario_id=uuid.UUID(me.id),
        accion="UPDATE",
        recurso_tipo="usuario",
        recurso_id=usuario.id,
        detalles={"antes": antes, "despues": {"rol": usuario.rol, "activo": usuario.activo}},
    )
    await write_security_log(
        session,
        event_type="user_modify",
        user={"user_id": me.id, "username": me.username, "role": me.rol},
        resource_type="usuario",
        resource_id=str(usuario.id),
        operation="update",
    )
    return usuario
