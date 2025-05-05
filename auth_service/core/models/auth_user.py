from sqlalchemy import String, TIMESTAMP, func, Boolean, LargeBinary, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuthUser(Base):
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.user_id}, password={self.password!r})"

    def __repr__(self) -> str:
        return str(self)
