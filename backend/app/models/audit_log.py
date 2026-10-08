from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    actor_id = Column(String(100), nullable=True, index=True)  # Future user/admin reference
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, verify, seed
    entity_type = Column(String(100), nullable=False, index=True)  # service, community_report, geographic_area, etc.
    entity_id = Column(Integer, nullable=False, index=True)
    previous_value = Column(Text, nullable=True)  # JSON or serialized before state
    new_value = Column(Text, nullable=True)  # JSON or serialized after state
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}#{self.entity_id}')>"
