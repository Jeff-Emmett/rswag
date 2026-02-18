"""Product override model."""

from datetime import datetime

from sqlalchemy import String, Boolean, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductOverride(Base):
    """Product override model for visibility and price overrides."""

    __tablename__ = "product_overrides"

    slug: Mapped[str] = mapped_column(String(100), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    price_override: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
