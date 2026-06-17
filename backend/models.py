import datetime as dt
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    jobs: Mapped[list["Job"]] = relationship(back_populates="owner")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued|running|done|failed
    result_code: Mapped[str] = mapped_column(Text, default="")
    result_tests: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="jobs")
