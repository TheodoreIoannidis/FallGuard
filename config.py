import os
from dataclasses import dataclass
from typing import List


def _parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_env: str
    cors_allowed_origins: List[str]
    cloud_storage_bucket: str
    frame_cache_window_ms: int
    target_lookback_ms: int
    lookback_tolerance_ms: int
    velocity_threshold: float
    distance_threshold: float
    hip_velocity_threshold: float
    hip_distance_threshold: float
    ratio_threshold: float
    ratio_delta_threshold: float
    expose_debug_metrics: bool


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("FALLGUARD_APP_NAME", "FallGuard Gateway Engine"),
        app_version=os.getenv("FALLGUARD_APP_VERSION", "0.1.0"),
        app_env=os.getenv("FALLGUARD_ENV", "development"),
        cors_allowed_origins=_parse_csv(
            os.getenv(
                "FALLGUARD_CORS_ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
            )
        ),
        cloud_storage_bucket=os.getenv("FALLGUARD_CLOUD_STORAGE_BUCKET", "fallguard-event-clips-9401"),
        frame_cache_window_ms=int(os.getenv("FALLGUARD_FRAME_CACHE_WINDOW_MS", "1500")),
        target_lookback_ms=int(os.getenv("FALLGUARD_TARGET_LOOKBACK_MS", "1000")),
        lookback_tolerance_ms=int(os.getenv("FALLGUARD_LOOKBACK_TOLERANCE_MS", "200")),
        velocity_threshold=float(os.getenv("FALLGUARD_VELOCITY_THRESHOLD", "0.08")),
        distance_threshold=float(os.getenv("FALLGUARD_DISTANCE_THRESHOLD", "40.0")),
        hip_velocity_threshold=float(os.getenv("FALLGUARD_HIP_VELOCITY_THRESHOLD", "0.03")),
        hip_distance_threshold=float(os.getenv("FALLGUARD_HIP_DISTANCE_THRESHOLD", "20.0")),
        ratio_threshold=float(os.getenv("FALLGUARD_RATIO_THRESHOLD", "0.65")),
        ratio_delta_threshold=float(os.getenv("FALLGUARD_RATIO_DELTA_THRESHOLD", "0.15")),
        expose_debug_metrics=_parse_bool(os.getenv("FALLGUARD_EXPOSE_DEBUG_METRICS"), default=False),
    )


settings = get_settings()
