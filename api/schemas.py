from typing import Dict, Optional
from pydantic import BaseModel, Field


class JointSchema(BaseModel):
    x: float
    y: float


class DebugMetricsSchema(BaseModel):
    inference_ms: float = Field(..., description="Time spent processing the request in milliseconds")
    lookback_ms: int = Field(..., description="Target temporal comparison window in milliseconds")
    head_velocity: float = Field(..., description="Vertical head velocity in pixels per millisecond")
    head_distance: float = Field(..., description="Head displacement in pixels")
    hip_velocity: float = Field(..., description="Vertical hip velocity in pixels per millisecond")
    hip_distance: float = Field(..., description="Hip displacement in pixels")
    aspect_ratio: float = Field(..., description="Current pose width-to-height ratio")
    ratio_delta: float = Field(..., description="Change in aspect ratio from previous frame")


class FallResponse(BaseModel):
    """Pydantic outbound schema for fall detection API response."""
    camera_id: str = Field(..., description="ID of the camera/room")
    fall_detected: bool = Field(..., description="Whether a fall was detected")
    status: str = Field(..., description="Processing status message")
    joints: Optional[Dict[str, JointSchema]] = Field(default=None, description="Extracted joint coordinates for visualization")
    metrics: Optional[DebugMetricsSchema] = Field(default=None, description="Optional internal debug metrics for tuning")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health state")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Deployment environment")
