from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import cv2

from fallguard.config import settings
from fallguard.core.types import JointCoords, SkeletonFrame
from fallguard.pipeline.logic import analyze_fall
from fallguard.pipeline.pose import extract_pose


@dataclass
class FrameAnalysis:
    joints: Dict[str, JointCoords]
    fall_detected: bool
    status: str


def find_prev_frame(
    timeline: List[SkeletonFrame],
    time_ms: int,
) -> Optional[SkeletonFrame]:
    prev_frame = None
    min_time_diff = float("inf")

    for frame in timeline:
        time_diff = abs(time_ms - frame.timestamp)
        dist_to_target = abs(time_diff - settings.target_lookback_ms)
        if dist_to_target < min_time_diff:
            min_time_diff = dist_to_target
            prev_frame = frame

    if prev_frame is None:
        return None

    if abs((time_ms - prev_frame.timestamp) - settings.target_lookback_ms) > settings.lookback_tolerance_ms:
        return None

    return prev_frame


def analyze_frame(
    frame,
    timestamp_ms: int,
    timeline: List[SkeletonFrame],
) -> FrameAnalysis:
    joints = extract_pose(frame)
    timeline[:] = [f for f in timeline if (timestamp_ms - f.timestamp) <= settings.frame_cache_window_ms]

    if "head" not in joints or "mid_hip" not in joints:
        return FrameAnalysis(joints=joints, fall_detected=False, status="No human subject found.")

    curr_frame = SkeletonFrame(joints=joints, timestamp=timestamp_ms, id="demo_video")
    prev_frame = find_prev_frame(timeline, timestamp_ms)
    timeline.append(curr_frame)

    if prev_frame is None:
        return FrameAnalysis(joints=joints, fall_detected=False, status="Awaiting temporal comparison.")

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

    if analysis.detected:
        return FrameAnalysis(joints=joints, fall_detected=True, status="Fall detected")

    return FrameAnalysis(joints=joints, fall_detected=False, status="Monitoring posture")


def draw_joint(frame, coords: JointCoords, color) -> None:
    center = (int(coords.x), int(coords.y))
    cv2.circle(frame, center, 26, color, 1, lineType=cv2.LINE_AA)
    cv2.circle(frame, center, 11, color, -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, center, 20, (245, 247, 251), 2, lineType=cv2.LINE_AA)


def annotate_frame(frame, analysis: FrameAnalysis) -> None:
    joints = analysis.joints
    head = joints.get("head")
    mid_hip = joints.get("mid_hip")

    if head and mid_hip:
        cv2.line(
            frame,
            (int(head.x), int(head.y)),
            (int(mid_hip.x), int(mid_hip.y)),
            (120, 235, 225),
            5,
            lineType=cv2.LINE_AA,
        )

    if head:
        draw_joint(frame, head, (255, 200, 90))

    if mid_hip:
        draw_joint(frame, mid_hip, (120, 235, 225))

    overlay = frame.copy()
    cv2.rectangle(overlay, (24, 24), (460, 88), (8, 16, 24), -1)
    cv2.addWeighted(overlay, 0.66, frame, 0.34, 0, frame)
    status_color = (205, 214, 224) if not analysis.fall_detected else (255, 214, 196)
    cv2.putText(
        frame,
        analysis.status,
        (46, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.86,
        status_color,
        2,
        lineType=cv2.LINE_AA,
    )

    if analysis.fall_detected:
        cv2.rectangle(overlay, (24, 102), (318, 158), (92, 112, 255), -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
        cv2.putText(
            frame,
            "FALL DETECTED",
            (42, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.98,
            (9, 14, 20),
            3,
            lineType=cv2.LINE_AA,
        )


def render_video(input_path: Path, output_path: Path) -> None:
    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open input video: {input_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    timeline: List[SkeletonFrame] = []
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        timestamp_ms = int((frame_index / fps) * 1000)
        analysis = analyze_frame(frame, timestamp_ms, timeline)
        annotate_frame(frame, analysis)
        writer.write(frame)
        frame_index += 1

    capture.release()
    writer.release()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render an annotated FallGuard demo video.")
    parser.add_argument("input", type=Path, help="Path to the source mp4 file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("frontend/public/media/test_fallguard_annotated_web.mp4"),
        help="Output path for the annotated mp4",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_video(args.input, args.output)


if __name__ == "__main__":
    main()
