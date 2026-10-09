from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.types import SafeGeometry


class PopulationCell(Base):
    __tablename__ = "population_cells"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    area_id = Column(Integer, ForeignKey("geographic_areas.id", ondelete="CASCADE"), nullable=False, index=True)
    geometry = Column(SafeGeometry("POLYGON", srid=4326), nullable=True)
    population = Column(Integer, default=0, nullable=False)
    demographics = Column(Text, nullable=True)  # JSON-encoded demographic values for equity analysis
    source_type = Column(String(50), nullable=False, default="simulated_demo")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    area = relationship("GeographicArea", back_populates="population_cells")

    def __repr__(self) -> str:
        return f"<PopulationCell(id={self.id}, area_id={self.area_id}, population={self.population})>"
