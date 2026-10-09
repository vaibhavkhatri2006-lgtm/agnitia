from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class ReportVerification(Base):
    __tablename__ = "report_verifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("community_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    verifier_id = Column(String(100), nullable=True, index=True)  # Future user/admin reference
    verification_status = Column(String(50), nullable=False)  # verified, rejected, inconclusive
    verification_type = Column(String(50), nullable=False)  # official_audit, peer_confirmation, algorithmic, simulated_demo
    notes = Column(Text, nullable=True)  # Notes/reason
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("CommunityReport", back_populates="verifications")

    def __repr__(self) -> str:
        return f"<ReportVerification(id={self.id}, report_id={self.report_id}, status='{self.verification_status}')>"
