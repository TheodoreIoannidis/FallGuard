# structures and type definitions
from typing import Dict
from dataclasses import dataclass

# Immutable data structures (frozen) for 
# Joint Coords and Skeleton Frame so that
# no downstream module can modify them after creation.
@dataclass(frozen=True)
class JointCoords:
    """(x,y) pixel location of joint in image."""
    x: float
    y: float


@dataclass(frozen=True)
class SkeletonFrame:
    """A frame containing skeleton data."""
    joints: Dict[str, JointCoords] # joint name : coords 
    timestamp: int #  (ms) timestamp of frame capture
    id: str # camera/room id
