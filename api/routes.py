from typing import Dict, List
from datetime import datetime
import cv2
import numpy as np
from fastapi import APIRouter, status, UploadFile, File, Form, BackgroundTasks
from google.cloud import storage

from fallguard.core.types import SkeletonFrame
from fallguard.api.schemas import FallResponse
from fallguard.pipeline.pose import extract_pose
from fallguard.pipeline.logic import fall_detected

router = APIRouter(prefix="/api/v1", tags=["telemetry"])

FRAME_CACHE: Dict[str, List[SkeletonFrame]] = {}

# Define your bucket name from earlier
BUCKET_NAME = "fallguard-event-clips-9401"

def upload_event_image_to_gcp(frame_bytes: bytes, filename: str):
    """
    Background worker function that uploads the fall-triggering 
    frame to your Google Cloud Storage bucket.
    """
    try:
        # authentication handled automatically under the hood
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"fall_events/{filename}")
        
        # upload binary image file
        blob.upload_from_string(frame_bytes, content_type="image/jpeg")
        print(f" Cloud Storage: Successfully archived {filename}")
    except Exception as e:
        print(f"❌ Cloud Storage Error: {str(e)}")


@router.post("/process_frame", status_code=status.HTTP_200_OK, response_model=FallResponse)
async def process_telemetry(
    background_tasks: BackgroundTasks, 
    camera_id: str = Form(...),
    frame_file: UploadFile = File(...), 
    time_ms: int = Form(...)
) -> FallResponse:
    """
    Ingests raw image from generic cameras, feeds them to Pose Estimation engine,
    and routes the calculated coords to the fall detection logic. 
    Returns JSON response with fall detection result.
    If a fall is detected, pushes the critical frame to Google Cloud Storage.
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
    # initialize timeline for new camera IDs
    if camera_id not in FRAME_CACHE:
        FRAME_CACHE[camera_id] = []

    timeline = FRAME_CACHE[camera_id]
    
    # clear history older than 1.5 seconds (1500ms)
    timeline = [f for f in timeline if (time_ms - f.timestamp) <= 1500]

    TARGET_LOOKBACK = 1000 # ms
    prev_frame =None
    min_time_diff = float('inf')
    
    for frame in timeline:
        time_diff = abs(time_ms - frame.timestamp)
        dist_to_target = abs(time_diff - TARGET_LOOKBACK)

        if dist_to_target < min_time_diff:
            min_time_diff = dist_to_target
            prev_frame = frame
    
    # append current frame to timeline
    timeline.append(curr_frame)
    FRAME_CACHE[camera_id] = timeline

    if prev_frame is None or abs((time_ms - prev_frame.timestamp) - TARGET_LOOKBACK) > 200:
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="Awaiting next frame stream."
        )
    
    # physics logic 
    fall = fall_detected(prev_frame, curr_frame)

    # --- NEW: Google Cloud Event Archiving Logic ---
    if fall:
        # Re-encode the decoded opencv image back into bytes for shipping
        _, encoded_img = cv2.imencode('.jpg', img)
        jpeg_bytes = encoded_img.tobytes()
        
        # Build a structured, production filename
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"fall_{camera_id}_{timestamp_str}.jpg"
        
        # Hand off the file saving to a background thread so the client gets an instant response
        background_tasks.add_task(upload_event_image_to_gcp, jpeg_bytes, filename)
        
        return FallResponse(
            camera_id=camera_id,
            fall_detected=True,
            status="CRITICAL ALERT: Fall detected! Frame snapshot securely pushed to Cloud Storage."
        )
    # ------------------------------------------------

    return FallResponse(
        camera_id=camera_id,
        fall_detected=fall,
        status="Frame inference and physics processing completed successfully."
    )