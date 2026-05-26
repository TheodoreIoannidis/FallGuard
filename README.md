# FallGuard Gateway Engine

FallGuard is an enterprise-grade, high-throughput AI computer vision and physics telemetry pipeline designed for continuous patient safety monitoring in healthcare environments. 

By centralizing the artificial intelligence layer on the server, FallGuard allows hospitals to deploy standard, low-cost security camera streams instead of expensive proprietary hardware. 
The backend processes raw incoming image frames, runs deep learning pose estimation to track human skeletons, and applies triple-threshold physical kinematics to identify critical fall events in real time.

---

## Architecture Overview

The engine is built on clean architecture principles, separating network concerns, machine learning frameworks, and pure physics logic into decoupled boundaries.

```text
  [ Generic IP Camera ] 
            │  
            │  (Sends HTTP POST multipart/form-data with binary image bytes)
            ▼
     [ Uvicorn Server ] 
            │  
            │  (Parses incoming raw network bytes into NumPy array buffers)
            ▼
    [ FastAPI Route Layer ] ──(State Tracking Cache)──► [ In-Memory DB Frame Cache ]
            │  
            │  (Passes OpenCV image matrix to AI Worker)
            ▼
[ pipeline/pose_engine.py ] ──(Google MediaPipe Neural Network)──► [ 33 Skeletal Keypoints ]
            │  
            │  (Normalizes spatial coordinates into Core System Types)
            ▼
   [ pipeline/logic.py ]  ──(Triple-Threshold Kinematics)──────► [ Fall: True / False ]
            │  
            ▼
  [ Hospital Dashboard ]  ◄──(Pydantic FallDetectionResponse)─── [ 200 OK Network Response ]
