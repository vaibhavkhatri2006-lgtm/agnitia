from typing import List
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(150), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    role = relationship("Role", back_populates="users", lazy="joined")

    @property
    def role_name(self) -> str:
        return self.role.name if self.role else "citizen"

    @property
    def permission_codes(self) -> List[str]:
        if not self.role or not self.role.permissions:
            return []
        return [p.code for p in self.role.permissions]

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.permission_codes

    def has_role(self, role_name: str) -> bool:
        return self.role_name == role_name

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role_name}')>"
