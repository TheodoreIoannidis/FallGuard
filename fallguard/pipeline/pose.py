from typing import Dict
import cv2
import mediapipe as mp
from fallguard.core.types import JointCoords

mp_pose = mp.solutions.pose
pose_estimator = mp_pose.Pose(
    static_image_mode = False,
    model_complexity = 1,
    enable_segmentation = False,
    min_detection_confidence = 0.5,
    min_tracking_confidence = 0.5
)

def extract_pose(img: cv2.Mat) -> Dict[str, JointCoords]:
    """
    Pose estimation using MediaPipe pose
    """
    joint_dict: Dict[str, JointCoords] = {}

    if img is None:
        return joint_dict
    
    # OpenCV uses BGR format, while MediaPipe expects RGB
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = pose_estimator.process(rgb_img)

    if not results.pose_landmarks:
        return joint_dict
    
    height, width, _ = img.shape
    landmarks = results.pose_landmarks.landmark

    # Mediapipe provides 33 landmarks
    # 0: Nose/Head
    head = landmarks[mp_pose.PoseLandmark.NOSE]
    
    joint_dict['head'] = JointCoords(
        x=float(head.x * width),
        y=float(head.y * height),
    )

    # Get mid hip from left and right hip landmarks
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

    mid_hip_x = ((left_hip.x + right_hip.x) / 2) * width
    mid_hip_y = ((left_hip.y + right_hip.y) / 2) * height

    joint_dict['mid_hip'] = JointCoords(
        x=float(mid_hip_x),
        y=float(mid_hip_y)
    )

    return joint_dict

