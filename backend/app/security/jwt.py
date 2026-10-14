from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from app.config import settings

PWD_CONTEXT_SCHEME = "bcrypt"


def hash_password(password: str) -> str:
    """Genera hash bcrypt para cuentas locales.

    Args:
        password: clave en claro.

    Returns:
        Hash para almacenar en usuarios.password_hash.
    """
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    """Compara clave en claro contra hash.

    Args:
        password: clave en claro.
        password_hash: hash almacenado.

    Returns:
        True si coincide.
    """
    import bcrypt

    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_access_token(user_id: UUID, username: str) -> str:
    """Crea JWT HS256 con sub=id y username.

    Args:
        user_id: id del usuario.
        username: login.

    Returns:
        Token firmado.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "exp": expire},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Valida JWT y devuelve payload.

    Args:
        token: JWT del header Bearer.

    Raises:
        JWTError: si es inválido o expiró.

    Returns:
        Payload decodificado.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
