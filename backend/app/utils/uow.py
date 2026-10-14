from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Garantiza transacciones ACID en operaciones multi-tabla."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.session.rollback()

    async def commit(self) -> None:
        await self.session.commit()
