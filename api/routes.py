# FastAPI endpoints
import cv2
import numpy as np
from typing import Dict
from fastapi import APIRouter, status, UploadFile, File, Form
from fallguard.core.types import SkeletonFrame
from fallguard.api.schemas import FallResponse
from fallguard.pipeline.pose import extract_pose
from fallguard.pipeline.logic import fall_detected

router = APIRouter(prefix="/api/v1", tags=["telemetry"])

FRAME_CACHE: Dict[str, SkeletonFrame] = {}

@router.post("/process_frame", status_code=status.HTTP_200_OK, response_model=FallResponse)
async def process_telemetry(
    camera_id: str = Form(...),
    frame_file: UploadFile = File(...), 
    time_ms: int = Form(...)
    ) -> FallResponse:
    """
    Ingests raw image from generic cameras, feeds them to Pose Estimation engine,
    and routes the calculated coords to the fall detection logic. 
    Returns JSON response with fall detection result.
    """
    
    contents = await frame_file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="Failed to decode image file."
        )
    
    joints = extract_pose(img)
    
    if "head" not in joints or "mid_hip" not in joints:
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="No human subject found in frame."
        )

    curr_frame = SkeletonFrame(joints=joints, timestamp=time_ms, id=camera_id)

    prev_frame = FRAME_CACHE.get(camera_id)

    if prev_frame is None:
        FRAME_CACHE[camera_id] = curr_frame
        # Cleaned up keys to match our new schema properties perfectly!
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="Initial raw frame processed and cached. Awaiting next frame stream."
        )
        
    fall = fall_detected(prev_frame, curr_frame)
    FRAME_CACHE[camera_id] = curr_frame

    return FallResponse(
        camera_id=camera_id,
        fall_detected=fall,
        status="Frame inference and physics processing completed successfully."
    )