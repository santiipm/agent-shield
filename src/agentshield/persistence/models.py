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



class McpRun(Base):
    """A single MCP tool-poisoning run."""

    __tablename__ = "mcp_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    model: Mapped[str] = mapped_column(String)
    json_path: Mapped[str] = mapped_column(String)

    mcp_results: Mapped[list["McpResultRow"]] = relationship(
        back_populates="mcp_run",
    )

    def __repr__(self) -> str:
        return f"<McpRun id={self.id} model={self.model!r}>"


class McpResultRow(Base):
    """Summary of a single MCP tool-poisoning result (details live in JSON)."""

    __tablename__ = "mcp_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mcp_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("mcp_runs.id"))
    attack_name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    compromised: Mapped[bool] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(String, nullable=True)

    mcp_run: Mapped["McpRun"] = relationship(back_populates="mcp_results")

    def __repr__(self) -> str:
        return f"<McpResultRow attack_name={self.attack_name!r}>"
