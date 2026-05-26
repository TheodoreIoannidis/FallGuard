# Pydantic schemas
from pydantic import BaseModel, Field

class FallResponse(BaseModel):
    """Pydantic outbound schema for fall detection API response."""
    camera_id: str = Field(..., description="ID of the camera/room")
    fall_detected: bool = Field(..., description="Whether a fall was detected")
    status: str = Field(..., description="Processing status message")