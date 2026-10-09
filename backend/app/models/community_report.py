from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.types import SafeGeometry


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reporter_id = Column(String(100), nullable=True, index=True)  # Future user/reporter reference
    category_id = Column(Integer, ForeignKey("service_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    area_id = Column(Integer, ForeignKey("geographic_areas.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geometry = Column(SafeGeometry("POINT", srid=4326), nullable=False)
    severity = Column(String(50), nullable=False, default="medium", index=True)  # low, medium, high, critical
    status = Column(String(50), nullable=False, default="submitted", index=True)  # submitted, in_review, verified, resolved, dismissed
    source_type = Column(String(50), nullable=False, default="community", index=True)  # community, simulated_demo
    verification_status = Column(String(50), nullable=False, default="unverified", index=True)  # unverified, pending, verified, rejected
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("ServiceCategory", back_populates="reports")
    service = relationship("Service", back_populates="reports")
    area = relationship("GeographicArea", back_populates="reports")
    verifications = relationship("ReportVerification", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CommunityReport(id={self.id}, title='{self.title}', status='{self.status}')>"
