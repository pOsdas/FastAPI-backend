from sqlalchemy import MetaData
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
)

from utils import camel_case_to_snake_case
from user_service.core.config import settings


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(
        naming_convention=settings.db.naming_conventions,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        return camel_case_to_snake_case(cls.__name__)

    id: Mapped[int] = mapped_column(primary_key=True)

