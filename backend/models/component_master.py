"""ORM model representing a master component record."""
from __future__ import annotations

from sqlalchemy import String, Integer, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class ComponentMaster(Base):
    """Table storing manufacturer component data and specs."""

    __tablename__ = "component_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    manufacturer: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    voltage: Mapped[float] = mapped_column(Float, nullable=True)
    current: Mapped[float] = mapped_column(Float, nullable=True)
    power: Mapped[float] = mapped_column(Float, nullable=True)
    specs: Mapped[dict] = mapped_column(JSON, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    availability: Mapped[int] = mapped_column(Integer, nullable=True)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False)

    # New fields for hierarchical modelling.  Ports, dependencies and
    # layer_affinity allow components to describe their physical
    # connection points, required sub-components and preferred canvas
    # layers.  See the README for more details about hierarchical
    # modelling and multi-layer design.
    ports: Mapped[list] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[dict] = mapped_column(JSON, nullable=True)
    layer_affinity: Mapped[list] = mapped_column(JSON, nullable=True)

    #: Optional nested sub-components.  Each entry in this list
    #: represents a child element (e.g. mounting bracket, rail or
    #: accessory) with its own part number, name and properties.  This
    #: hierarchical structure allows a component to represent an
    #: assembly of parts and enables the AI to explode single-line
    #: components into detailed layers.  Stored as JSON for flexibility.
    sub_elements: Mapped[list] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ComponentMaster(part_number={self.part_number!r}, manufacturer={self.manufacturer!r})"
