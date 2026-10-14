from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuarios import Usuario


async def get_by_username(session: AsyncSession, username: str) -> Usuario | None:
    """Busca usuario por username (query parametrizada).

    Args:
        session: sesion async.
        username: login exacto.

    Returns:
        Usuario o None.
    """
    res = await session.execute(select(Usuario).where(Usuario.username == username))
    return res.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: object) -> Usuario | None:
    """Busca usuario por UUID.

    Args:
        session: sesion async.
        user_id: UUID.

    Returns:
        Usuario o None.
    """
    return await session.get(Usuario, user_id)  # type: ignore[arg-type]
