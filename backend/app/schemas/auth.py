from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address or username", json_schema_extra={"example": "citizen@example.com"})
    password: str = Field(..., min_length=1, description="Account password", json_schema_extra={"example": "Citizen123!"})


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    role: str = Field(..., description="Assigned role name (e.g. citizen, community, authority, admin)")
    permissions: List[str] = Field(default_factory=list, description="List of granted permission codes")
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserResponse


class RoleVerificationResponse(BaseModel):
    status: str
    message: str
    role: str
    user_id: int
    user_email: str
    granted_permissions: List[str]
