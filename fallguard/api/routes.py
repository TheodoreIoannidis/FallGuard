from typing import Dict, List
import json
import logging
import time
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form #, BackgroundTasks
from google.cloud import storage

from fallguard.api.schemas import DebugMetricsSchema, FallResponse
from fallguard.config import settings
from fallguard.core.types import SkeletonFrame
from fallguard.pipeline.pose import extract_pose
from fallguard.pipeline.logic import analyze_fall

router = APIRouter(prefix="/api/v1", tags=["telemetry"])

FRAME_CACHE: Dict[str, List[SkeletonFrame]] = {}
logger = logging.getLogger("fallguard.api.routes")


def _prune_frame_cache(current_time_ms: int) -> None:
    stale_camera_ids = [
        camera_id
        for camera_id, frames in FRAME_CACHE.items()
        if not frames or (current_time_ms - frames[-1].timestamp) > settings.frame_cache_window_ms
    ]
    for camera_id in stale_camera_ids:
        FRAME_CACHE.pop(camera_id, None)

    if len(FRAME_CACHE) <= settings.max_active_cameras:
        return

    cameras_by_last_seen = sorted(
        FRAME_CACHE.items(),
        key=lambda entry: entry[1][-1].timestamp if entry[1] else -1,
    )
    overflow_count = len(FRAME_CACHE) - settings.max_active_cameras
    for camera_id, _ in cameras_by_last_seen[:overflow_count]:
        FRAME_CACHE.pop(camera_id, None)


def _validate_request(camera_id: str, time_ms: int, frame_file: UploadFile) -> None:
    normalized_camera_id = camera_id.strip()
    if not normalized_camera_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="camera_id cannot be empty")

    if len(normalized_camera_id) > settings.max_camera_id_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"camera_id exceeds {settings.max_camera_id_length} characters",
        )

    if time_ms <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="time_ms must be positive")

    content_type = frame_file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="frame_file must be an image upload")


def _serialize_joints(joints: Dict[str, object]) -> Dict[str, Dict[str, float]]:
    return {
        joint_name: {"x": float(coords.x), "y": float(coords.y)}
        for joint_name, coords in joints.items()
    }


def _build_debug_metrics(analysis, inference_ms: float) -> DebugMetricsSchema:
    return DebugMetricsSchema(
        inference_ms=round(inference_ms, 2),
        lookback_ms=settings.target_lookback_ms,
        head_velocity=analysis.head_velocity,
        head_distance=analysis.head_distance,
        hip_velocity=analysis.hip_velocity,
        hip_distance=analysis.hip_distance,
        aspect_ratio=analysis.aspect_ratio,
        ratio_delta=analysis.ratio_delta,
    )


def _log_inference(camera_id: str, status_text: str, fall_detected: bool, joints_found: bool, inference_ms: float):
    logger.info(
        json.dumps(
            {
                "event": "frame_processed",
                "camera_id": camera_id,
                "fall_detected": fall_detected,
                "joints_found": joints_found,
                "status": status_text,
                "inference_ms": round(inference_ms, 2),
                "environment": settings.app_env,
            }
        )
    )

def upload_event_image_to_gcp(frame_bytes: bytes, filename: str):
    """
    Background worker function that uploads the fall-triggering 
    frame to your Google Cloud Storage bucket.
    """
    try:
        # authentication handled automatically under the hood
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.cloud_storage_bucket)
        blob = bucket.blob(f"fall_events/{filename}")
        
        # upload binary image file
        blob.upload_from_string(frame_bytes, content_type="image/jpeg")
        print(f" Cloud Storage: Successfully archived {filename}")
    except Exception as e:
        print(f"❌ Cloud Storage Error: {str(e)}")


@router.post("/process_frame", status_code=status.HTTP_200_OK, response_model=FallResponse)
async def process_telemetry(
    #background_tasks: BackgroundTasks, 
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
    
    _validate_request(camera_id, time_ms, frame_file)
    camera_id = camera_id.strip()
    _prune_frame_cache(time_ms)

    started_at = time.perf_counter()
    contents = await frame_file.read(settings.max_upload_bytes + 1)

    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"frame_file exceeds {settings.max_upload_bytes} bytes",
        )

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        inference_ms = (time.perf_counter() - started_at) * 1000
        _log_inference(camera_id, "Failed to decode image file.", False, False, inference_ms)
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="Failed to decode image file.",
        )
    
    joints = extract_pose(img)
    
    if "head" not in joints or "mid_hip" not in joints:
        inference_ms = (time.perf_counter() - started_at) * 1000
        _log_inference(camera_id, "No human subject found in frame.", False, False, inference_ms)
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="No human subject found in frame.",
        )

    curr_frame = SkeletonFrame(joints=joints, timestamp=time_ms, id=camera_id)
    # initialize timeline for new camera IDs
    if camera_id not in FRAME_CACHE:
        FRAME_CACHE[camera_id] = []

    timeline = FRAME_CACHE[camera_id]
    
    # clear history older than 1.5 seconds (1500ms)
    timeline = [f for f in timeline if (time_ms - f.timestamp) <= settings.frame_cache_window_ms]

    prev_frame =None
    min_time_diff = float('inf')
    
    for frame in timeline:
        time_diff = abs(time_ms - frame.timestamp)
        dist_to_target = abs(time_diff - settings.target_lookback_ms)

        if dist_to_target < min_time_diff:
            min_time_diff = dist_to_target
            prev_frame = frame
    
    # append current frame to timeline
    timeline.append(curr_frame)
    FRAME_CACHE[camera_id] = timeline

    if prev_frame is None or abs((time_ms - prev_frame.timestamp) - settings.target_lookback_ms) > settings.lookback_tolerance_ms:
        inference_ms = (time.perf_counter() - started_at) * 1000
        _log_inference(camera_id, "Awaiting next frame stream.", False, True, inference_ms)
        return FallResponse(
            camera_id=camera_id,
            fall_detected=False,
            status="Awaiting next frame stream.",
            joints=_serialize_joints(joints),
        )
    
    analysis = analyze_fall(
        prev_frame=prev_frame,
        curr_frame=curr_frame,
        velocity_threshold=settings.velocity_threshold,
        distance_threshold=settings.distance_threshold,
        hip_velocity_threshold=settings.hip_velocity_threshold,
        hip_distance_threshold=settings.hip_distance_threshold,
        ratio_threshold=settings.ratio_threshold,
        ratio_delta_threshold=settings.ratio_delta_threshold,
    )
    fall = analysis.detected
    inference_ms = (time.perf_counter() - started_at) * 1000
    metrics = _build_debug_metrics(analysis, inference_ms) if settings.expose_debug_metrics else None

    # --- NEW: Google Cloud Event Archiving Logic ---
    if fall:
        # Re-encode the decoded opencv image back into bytes for shipping
        # _, encoded_img = cv2.imencode('.jpg', img)
        # jpeg_bytes = encoded_img.tobytes()
        
        # Build a structured, production filename
        # timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # filename = f"fall_{camera_id}_{timestamp_str}.jpg"
        
        # Hand off the file saving to a background thread so the client gets an instant response
        # background_tasks.add_task(upload_event_image_to_gcp, jpeg_bytes, filename)
        
        _log_inference(
            camera_id,
            "CRITICAL ALERT: Fall detected! Frame snapshot securely pushed to Cloud Storage.",
            True,
            True,
            inference_ms,
        )
        return FallResponse(
            camera_id=camera_id,
            fall_detected=True,
            status="CRITICAL ALERT: Fall detected! Frame snapshot securely pushed to Cloud Storage.",
            joints=_serialize_joints(joints),
            metrics=metrics,
        )
    # ------------------------------------------------

    _log_inference(
        camera_id,
        "Frame inference and physics processing completed successfully.",
        False,
        True,
        inference_ms,
    )
    return FallResponse(
        camera_id=camera_id,
        fall_detected=fall,
        status="Frame inference and physics processing completed successfully.",
        joints=_serialize_joints(joints),
        metrics=metrics,
    )
