from sqlalchemy import String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    user_name: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[str] = mapped_column(default=True)

    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, username={self.user_name!r})"

    def __repr__(self) -> str:
        return str(self)
