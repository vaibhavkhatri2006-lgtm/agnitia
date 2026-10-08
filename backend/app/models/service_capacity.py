from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class ServiceCapacity(Base):
    __tablename__ = "service_capacities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    current_load = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="normal", index=True)  # normal, constrained, overloaded
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    service = relationship("Service", back_populates="capacity_record")

    def __repr__(self) -> str:
        return f"<ServiceCapacity(service_id={self.service_id}, capacity={self.capacity}, load={self.current_load})>"
