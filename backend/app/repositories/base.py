from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import UUIDMixin

T = TypeVar("T", bound=UUIDMixin)


class BaseRepository(Generic[T]):
    """Repositorio genérico. Aísla SQLAlchemy de la capa servicio."""

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get(self, id: UUID) -> T | None:
        return await self._session.get(self._model, id)

    async def list(self, limit: int = 100, offset: int = 0) -> list[T]:
        res = await self._session.execute(select(self._model).limit(limit).offset(offset))
        return list(res.scalars().all())
