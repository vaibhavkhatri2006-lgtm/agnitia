from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.types import SafeGeometry


class GeographicArea(Base):
    __tablename__ = "geographic_areas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    area_type = Column(String(50), nullable=False, index=True)  # local, neighbourhood, ward, district, city, region, country
    parent_id = Column(Integer, ForeignKey("geographic_areas.id", ondelete="SET NULL"), nullable=True, index=True)
    geometry = Column(SafeGeometry("MULTIPOLYGON", srid=4326), nullable=True)
    population = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Hierarchy relationship
    parent = relationship("GeographicArea", remote_side=[id], backref="children")
    services = relationship("Service", back_populates="area", cascade="all, delete-orphan")
    population_cells = relationship("PopulationCell", back_populates="area", cascade="all, delete-orphan")
    reports = relationship("CommunityReport", back_populates="area")

    def __repr__(self) -> str:
        return f"<GeographicArea(id={self.id}, name='{self.name}', type='{self.area_type}')>"
