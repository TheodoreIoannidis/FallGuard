import math
from dataclasses import dataclass
from typing import Optional
from fallguard.core.types import SkeletonFrame, JointCoords


@dataclass(frozen=True)
class FallAnalysis:
    detected: bool
    head_velocity: float
    head_distance: float
    hip_velocity: float
    hip_distance: float
    aspect_ratio: float
    ratio_delta: float

def calc_distance(p1: JointCoords, p2: JointCoords) -> float:
    """Calculate the Euclidean distance between two joints."""
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def calc_velocity(
        prev_frame: SkeletonFrame,
        curr_frame: SkeletonFrame,
        joint_name: str = 'head',
) -> Optional[float]:
    """Calculate the velocity of a joint between two frames."""

    if joint_name not in prev_frame.joints or joint_name not in curr_frame.joints:
        return None  # Joint not found in one of the frames

    prev_joint = prev_frame.joints[joint_name]
    curr_joint = curr_frame.joints[joint_name]

    distance_y = curr_joint.y - prev_joint.y  # vertical distance (falling downwards increases y)
    time_diff = (curr_frame.timestamp - prev_frame.timestamp)  

    if time_diff <= 0:
        return 0.0  

    velocity = distance_y / time_diff
    return velocity

def calc_aspect_ratio(frame : SkeletonFrame,) -> float:
    """Calc aspect ratio of skeleton frame."""
    joints = frame.joints

    head, hip = joints.get('head'), joints.get('mid_hip')

    if not head or not hip:
        return 0.0 
    
    height = abs(head.y - hip.y)
    if height == 0:
        return 0.0
    
    x_coords = [joint.x for joint in joints.values()]
    width = max(x_coords) - min(x_coords)

    return width / height
    

def fall_detected(
        prev_frame: SkeletonFrame,
        curr_frame: SkeletonFrame,
        velocity_threshold: float = 0.08, # pixels per millisecond
        distance_threshold: float = 40.0, # pixels
        hip_velocity_threshold: float = 0.03, # pixels per millisecond
        hip_distance_threshold: float = 20.0, # pixels
        ratio_threshold: float = 0.65, # torso noticeably tilted/horizontal
        ratio_delta_threshold: float = 0.15, # meaningful posture change between frames
) -> bool:
    """Fall threshold system (Velocity + Distance + Aspect Ratio)"""
    return analyze_fall(
        prev_frame=prev_frame,
        curr_frame=curr_frame,
        velocity_threshold=velocity_threshold,
        distance_threshold=distance_threshold,
        hip_velocity_threshold=hip_velocity_threshold,
        hip_distance_threshold=hip_distance_threshold,
        ratio_threshold=ratio_threshold,
        ratio_delta_threshold=ratio_delta_threshold,
    ).detected


def analyze_fall(
        prev_frame: SkeletonFrame,
        curr_frame: SkeletonFrame,
        velocity_threshold: float = 0.08,
        distance_threshold: float = 40.0,
        hip_velocity_threshold: float = 0.03,
        hip_distance_threshold: float = 20.0,
        ratio_threshold: float = 0.65,
        ratio_delta_threshold: float = 0.15,
) -> FallAnalysis:
    """Return fall decision plus metrics used to make it."""

    head_velocity = calc_velocity(prev_frame, curr_frame)
    hip_velocity = calc_velocity(prev_frame, curr_frame, joint_name='mid_hip')
    if head_velocity is None or hip_velocity is None:
        return FallAnalysis(
            detected=False,
            head_velocity=0.0,
            head_distance=0.0,
            hip_velocity=0.0,
            hip_distance=0.0,
            aspect_ratio=0.0,
            ratio_delta=0.0,
        )

    prev_head = prev_frame.joints.get('head')
    curr_head = curr_frame.joints.get('head')
    prev_hip = prev_frame.joints.get('mid_hip')
    curr_hip = curr_frame.joints.get('mid_hip')

    prev_aspect_ratio = calc_aspect_ratio(prev_frame)
    aspect_ratio = calc_aspect_ratio(curr_frame)
    head_distance = calc_distance(prev_head, curr_head) if prev_head and curr_head else 0.0
    hip_distance = calc_distance(prev_hip, curr_hip) if prev_hip and curr_hip else 0.0
    ratio_delta = aspect_ratio - prev_aspect_ratio

    detected = (
        head_velocity >= velocity_threshold and
        head_distance >= distance_threshold and
        hip_velocity >= hip_velocity_threshold and
        hip_distance >= hip_distance_threshold and
        aspect_ratio >= ratio_threshold and
        ratio_delta >= ratio_delta_threshold
    )

    return FallAnalysis(
        detected=detected,
        head_velocity=head_velocity,
        head_distance=head_distance,
        hip_velocity=hip_velocity,
        hip_distance=hip_distance,
        aspect_ratio=aspect_ratio,
        ratio_delta=ratio_delta,
    )
