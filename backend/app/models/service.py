from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.types import SafeGeometry


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("service_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(Integer, ForeignKey("geographic_areas.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geometry = Column(SafeGeometry("POINT", srid=4326), nullable=False)
    status = Column(String(50), nullable=False, default="operational", index=True)  # operational, temporarily_unavailable, degraded, closed
    source_type = Column(String(50), nullable=False, default="simulated_demo", index=True)  # osm, government, authority, community, admin, simulated_demo
    verification_status = Column(String(50), nullable=False, default="unverified", index=True)  # unverified, pending, verified, rejected
    confidence_score = Column(Float, default=1.0, nullable=False)
    operating_hours = Column(Text, nullable=True)  # Prepared for future operating-hours functionality
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("ServiceCategory", back_populates="services")
    area = relationship("GeographicArea", back_populates="services")
    capacity_record = relationship("ServiceCapacity", back_populates="service", uselist=False, cascade="all, delete-orphan")
    reports = relationship("CommunityReport", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', status='{self.status}')>"
