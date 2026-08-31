"""SQLAlchemy ORM models for persistence."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Run(Base):
    """A single evaluation run."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    model: Mapped[str] = mapped_column(String)
    json_path: Mapped[str] = mapped_column(String)

    attack_results: Mapped[list["AttackResultRow"]] = relationship(
        back_populates="run",
    )

    def __repr__(self) -> str:
        return f"<Run id={self.id} model={self.model!r}>"


class AttackResultRow(Base):
    """Summary of a single attack result (details live in JSON)."""

    __tablename__ = "attack_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id"))
    attack_name: Mapped[str] = mapped_column(String)
    attack_category: Mapped[str] = mapped_column(String)
    success: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[float] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(String, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="attack_results")

    def __repr__(self) -> str:
        return f"<AttackResultRow attack_name={self.attack_name!r}>"
