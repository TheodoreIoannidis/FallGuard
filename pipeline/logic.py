# Inference Logic
import math
from typing import Optional
from fallguard.core.types import SkeletonFrame, JointCoords

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
        velocity_threshold: float = 0.4, # pixels per milisecond
        distance_threshold: float = 80.0, # pixels
        ratio_threshold: float = 2.0 # wide horizontal layout
) -> bool:
    """Fall threshold system (Velocity + Distance + Aspect Ratio)"""

    head_velocity = calc_velocity(prev_frame, curr_frame)
    if head_velocity is None:
        return False  # abort safely

    prev_head = prev_frame.joints.get('head')
    curr_head = curr_frame.joints.get('head')

    aspect_ratio = calc_aspect_ratio(curr_frame)
    head_distance = calc_distance(prev_head, curr_head) if prev_head and curr_head else 0.0

    if (
        head_velocity >= velocity_threshold and
        head_distance >= distance_threshold and
        aspect_ratio > ratio_threshold
    ):
        return True
    
    return False