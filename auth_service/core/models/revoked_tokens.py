from sqlalchemy import String, TIMESTAMP, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RevokedToken(Base):
    id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    revoked_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, token={self.token}, revoked_at={self.revoked_at})"

    def __repr__(self) -> str:
        return str(self)
