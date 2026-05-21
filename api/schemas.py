# Pydantic schemas
from pydantic import BaseModel, Field
from typing import Dict, List
from fallguard.core.types import JointCoords, SkeletonFrame

class JointInputSchema(BaseModel):
    """Pydantic schema for JointCoords."""
    coords: List[float] = Field(..., min_length=2, max_length=2, description="[x, y] coordinates.") 

    def to_core(self) -> JointCoords: # Data Mapping function
        """Convert to core JointCoords."""
        return JointCoords(x=self.coords[0], y=self.coords[1])

class SkeletonFrameSchema(BaseModel):
    """Pydantic schema for SkeletonFrame."""
    id: str = Field(..., min_length=1, description="Camera/room ID.")
    timestamp: int = Field(..., gt=0, description="Timestamp of frame capture.")
    keypts: Dict[str, JointInputSchema]

    def to_core(self) -> SkeletonFrame: # Data Mapping function 
        """Convert to core SkeletonFrame."""
        return SkeletonFrame(
            id = self.id,
            timestamp=self.timestamp,
            joints={name : kp.to_core() for name, kp in self.keypts.items()}
        )