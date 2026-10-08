from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    message: str = Field(..., description="Human readable error explanation")
    error_code: str = Field(..., description="Machine readable error code")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the error")


class HTTPErrorResponse(BaseModel):
    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Standard error identifier")
    status_code: Optional[int] = Field(None, description="HTTP status code")
