# FallGuard

Cloud-deployed fall detection from video.

FallGuard is a full-stack computer vision demo that streams webcam frames from the browser to a Google Cloud-hosted FastAPI backend. The backend uses MediaPipe Pose to extract key landmarks and applies lightweight temporal fall-detection logic over a one-second motion window.

## Live Demo

- Frontend: [fallguard-frontend](https://fallguard-frontend-1054611845093.europe-west4.run.app)
- Backend health check: [fallguard-api /health](https://fallguard-api-1054611845093.europe-west4.run.app/health)

## Author

- [Theodore Ioannidis](https://www.linkedin.com/in/theodoros-ioannidis/)
- Computer Vision / AI Engineer

## Features

- Browser-based webcam demo with live overlay rendering
- Google Cloud-hosted FastAPI inference backend
- MediaPipe Pose landmark extraction
- Motion-based fall-event logic using head and mid-hip tracking
- Real-time status panels for inference and motion metrics
- Homepage demo clip and production-style frontend presentation

## Architecture

```text
Browser webcam
  -> React / Vite frontend
  -> POST /api/v1/process_frame
  -> FastAPI route layer
  -> MediaPipe pose extraction
  -> Temporal motion analysis
  -> JSON response with fall state, joints, and optional metrics
  -> Frontend overlay and UI status updates
```

## Tech Stack

- **Frontend:** React, Vite, React Router
- **Backend:** FastAPI, Uvicorn, Pydantic
- **CV / ML:** OpenCV, MediaPipe Pose, NumPy
- **Cloud:** Google Cloud Run

## Repository Structure

```text
.
|- frontend/               React frontend
|- fallguard/              Backend package
|- main.py                 FastAPI app entrypoint
|- Dockerfile              Backend Cloud Run image
|- requirements.txt        Backend dependencies
`- tools/                  Utility scripts
```

## Local Development

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Configuration

### Backend

Important environment variables:

- `FALLGUARD_CORS_ALLOWED_ORIGINS`
- `FALLGUARD_MAX_UPLOAD_BYTES`
- `FALLGUARD_MAX_CAMERA_ID_LENGTH`
- `FALLGUARD_MAX_ACTIVE_CAMERAS`
- `FALLGUARD_FRAME_CACHE_WINDOW_MS`
- `FALLGUARD_TARGET_LOOKBACK_MS`
- `FALLGUARD_LOOKBACK_TOLERANCE_MS`
- `FALLGUARD_EXPOSE_DEBUG_METRICS`

### Frontend

Set:

- `VITE_API_URL`

Production currently points to the deployed Cloud Run backend.

## Deployment

Both services are deployed separately to Google Cloud Run:

- `fallguard-api` for inference
- `fallguard-frontend` for the web UI

This repo keeps both services together because they are tightly coupled and easier to understand as a single project.

## Security and Privacy Notes

- This demo sends webcam frames to a remote backend for inference.
- The current system is suitable for a portfolio demo, not a certified medical or safety product.
- The backend currently validates upload size, bounds session state, and uses per-session browser camera IDs.
- Fall-event image archival code exists in the backend, but it is not currently enabled.
- The public demo backend is publicly invokable on Cloud Run.

## Current Limitations

- Single-person tracking only
- No authentication on the public inference endpoint
- No production-grade rate limiting
- Not intended for real-world safety monitoring

## Roadmap Ideas

- Multi-person support
- Stronger authentication and abuse protection
- Browser-side pose inference for improved privacy
- Analytics dashboard and monitoring
- More robust deployment hardening

## License / Use

Standard MIT License. This is a personal project and demo, not intended for commercial use or production deployment without significant enhancements and security hardening.