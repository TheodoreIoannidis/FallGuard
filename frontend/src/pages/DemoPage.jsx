import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1/process_frame";
const SAMPLE_INTERVAL_MS = 100;

function formatMetric(value, digits = 2) {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

function getEndpointLabel(apiUrl) {
  try {
    return new URL(apiUrl).pathname;
  } catch {
    return "/process_frame";
  }
}

function createSessionCameraId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `browser-${crypto.randomUUID()}`;
  }

  return `browser-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function DemoPage() {
  const videoRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const captureCanvasRef = useRef(null);
  const loopActiveRef = useRef(false);
  const cameraIdRef = useRef(createSessionCameraId());

  const [cameraState, setCameraState] = useState("idle");
  const [analysisState, setAnalysisState] = useState("idle");
  const [hasCameraStream, setHasCameraStream] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [backendStatus, setBackendStatus] = useState("Waiting to start live analysis.");
  const [fallDetected, setFallDetected] = useState(false);
  const [joints, setJoints] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState("");
  const [showKeypoints, setShowKeypoints] = useState(true);

  const stateLabel = useMemo(() => {
    if (cameraState === "error") {
      return "Camera unavailable";
    }
    if (cameraState === "requesting") {
      return "Requesting access";
    }
    if (cameraState === "live" && analysisState === "error") {
      return "Waiting for inference response";
    }
    if (cameraState === "live" && fallDetected) {
      return "Possible fall detected";
    }
    if (cameraState === "live") {
      return "Monitoring movement";
    }
    return "Camera inactive";
  }, [cameraState, analysisState, fallDetected]);

  useEffect(() => {
    captureCanvasRef.current = document.createElement("canvas");

    return () => {
      loopActiveRef.current = false;
      stopTracks();
    };
  }, []);

  useEffect(() => {
    syncOverlayCanvas();
    drawOverlay();
  }, [joints, fallDetected, cameraState, showKeypoints]);

  useEffect(() => {
    if (cameraState !== "live") {
      loopActiveRef.current = false;
      return undefined;
    }

    setAnalysisState("running");
    loopActiveRef.current = true;

    const loop = async () => {
      while (loopActiveRef.current) {
        await processFrame();
        await new Promise((resolve) => window.setTimeout(resolve, SAMPLE_INTERVAL_MS));
      }
    };

    loop();

    return () => {
      loopActiveRef.current = false;
    };
  }, [cameraState]);

  function stopTracks() {
    const stream = videoRef.current?.srcObject;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  }

  function syncOverlayCanvas() {
    const video = videoRef.current;
    const overlayCanvas = overlayCanvasRef.current;

    if (!video || !overlayCanvas || !video.videoWidth || !video.videoHeight) {
      return;
    }

    if (
      overlayCanvas.width !== video.videoWidth ||
      overlayCanvas.height !== video.videoHeight
    ) {
      overlayCanvas.width = video.videoWidth;
      overlayCanvas.height = video.videoHeight;
    }
  }

  function drawOverlay() {
    const canvas = overlayCanvasRef.current;
    if (!canvas) {
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    context.clearRect(0, 0, canvas.width, canvas.height);

    if (!joints) {
      return;
    }

    const head = joints.head;
    const midHip = joints.mid_hip;
    const accentColor = fallDetected ? "#ff7b6b" : "#7ce4d8";

    if (showKeypoints) {
      context.lineWidth = 6;
      context.strokeStyle = fallDetected
        ? "rgba(255, 123, 107, 0.9)"
        : "rgba(124, 228, 216, 0.85)";
      context.fillStyle = accentColor;
      context.font = "600 22px 'Source Sans 3', sans-serif";

      if (head && midHip) {
        context.beginPath();
        context.moveTo(head.x, head.y);
        context.lineTo(midHip.x, midHip.y);
        context.stroke();
      }

      drawJoint(context, head, "Head", accentColor);
      drawJoint(context, midHip, "Mid-hip", fallDetected ? "#ffb0a8" : "#aaf7ef");
    }

    if (fallDetected) {
      context.fillStyle = "rgba(255, 123, 107, 0.92)";
      context.fillRect(28, 28, 260, 54);
      context.fillStyle = "#07111a";
      context.font = "700 28px 'Space Grotesk', sans-serif";
      context.fillText("FALL DETECTED", 44, 64);
    }
  }

  function drawJoint(context, joint, label, color) {
    if (!joint) {
      return;
    }

    context.beginPath();
    context.arc(joint.x, joint.y, 11, 0, Math.PI * 2);
    context.fillStyle = color;
    context.fill();

    context.beginPath();
    context.lineWidth = 4;
    context.strokeStyle = "rgba(255, 255, 255, 0.88)";
    context.arc(joint.x, joint.y, 18, 0, Math.PI * 2);
    context.stroke();

    context.fillStyle = "#f4f7fb";
    context.font = "600 20px 'Source Sans 3', sans-serif";
    context.fillText(label, joint.x + 18, joint.y - 18);
  }

  async function startCamera() {
    setErrorMessage("");
    setCameraState("requesting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      syncOverlayCanvas();
      setHasCameraStream(true);
      setBackendStatus(
        "Pose landmarks are being estimated and evaluated for fall-like movement patterns.",
      );
      setCameraState("live");
      setAnalysisState("running");
    } catch (error) {
      setCameraState("error");
      setAnalysisState("idle");
      setHasCameraStream(false);
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to access webcam.",
      );
      setBackendStatus("Webcam access failed.");
    }
  }

  function stopCamera() {
    loopActiveRef.current = false;
    stopTracks();

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraState("idle");
    setAnalysisState("idle");
    setHasCameraStream(false);
    setErrorMessage("");
    setBackendStatus("Live analysis stopped.");
    setFallDetected(false);
    setJoints(null);
    setMetrics(null);
    setLatencyMs(null);
    setLastUpdatedAt("");
    drawOverlay();
  }

  async function processFrame() {
    const video = videoRef.current;
    const captureCanvas = captureCanvasRef.current;

    if (
      !video ||
      !captureCanvas ||
      video.readyState < 2 ||
      !video.videoWidth ||
      !video.videoHeight
    ) {
      return;
    }

    syncOverlayCanvas();

    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;

    const captureContext = captureCanvas.getContext("2d");
    if (!captureContext) {
      return;
    }

    captureContext.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

    const blob = await new Promise((resolve) => {
      captureCanvas.toBlob(resolve, "image/jpeg", 0.86);
    });

    if (!blob) {
      return;
    }

    const requestStartedAt = performance.now();
    const formData = new FormData();
    formData.append("camera_id", cameraIdRef.current);
    formData.append("time_ms", String(Date.now()));
    formData.append("frame_file", blob, "frame.jpg");

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const payload = await response.json();
      setLatencyMs(performance.now() - requestStartedAt);
      setBackendStatus(payload.status ?? "Frame processed.");
      setFallDetected(Boolean(payload.fall_detected));
      setJoints(payload.joints ?? null);
      setMetrics(payload.metrics ?? null);
      setLastUpdatedAt(new Date().toLocaleTimeString());
      setAnalysisState("running");
    } catch (error) {
      setBackendStatus("Unable to reach backend inference service.");
      setFallDetected(false);
      setJoints(null);
      setMetrics(null);
      setLatencyMs(null);
      setAnalysisState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "An unexpected request error occurred.",
      );
      loopActiveRef.current = false;
    }
  }

  return (
    <main className="page-shell demo-shell">
      <header className="demo-header">
        <div>
          <p className="eyebrow">FallGuard live demo</p>
          <h1>Real-time webcam inference</h1>
        </div>

        <Link className="secondary-button" to="/">
          Back to overview
        </Link>
      </header>

      <section className="demo-grid">
        <div className="video-card">
          <div className="video-topbar">
            <div className="video-status-group">
              <span className={`status-dot status-${cameraState}`} />
              <span>{stateLabel}</span>
            </div>
            <label className="overlay-toggle">
              <input
                type="checkbox"
                checked={showKeypoints}
                onChange={() => setShowKeypoints((current) => !current)}
              />
              <span>Show keypoints</span>
            </label>
            {latencyMs !== null && (
              <span className="latency-chip">{Math.round(latencyMs)} ms</span>
            )}
          </div>

          <div className="video-stage">
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="webcam-video"
            />
            <canvas ref={overlayCanvasRef} className="overlay-canvas" />

            {!hasCameraStream && (
              <div className="video-placeholder">
                <h2>Start live analysis</h2>
                <p>
                  Webcam frames are sent to the FastAPI backend for MediaPipe
                  pose estimation and motion-based fall analysis. Results are
                  rendered directly over the live video.
                </p>
              </div>
            )}
          </div>

          <div className="demo-actions">
            <button className="primary-button" type="button" onClick={startCamera}>
              Start live analysis
            </button>
            <button className="ghost-button" type="button" onClick={stopCamera}>
              Stop session
            </button>
          </div>
        </div>

        <aside className="status-card">
          <div className={`status-panel ${fallDetected ? "critical-panel" : ""}`}>
            <span className="metric-label">System status</span>
            <strong>
              {fallDetected
                ? "Possible fall event detected"
                : cameraState === "live"
                  ? "Live single-person monitoring"
                  : "Ready for single-person monitoring"}
            </strong>
            <p>
              {fallDetected
                ? "Recent head and mid-hip motion matched the fall-event logic."
                : cameraState === "live"
                  ? "Pose landmarks are being estimated and evaluated for fall-like movement patterns."
                  : "Start the webcam to begin pose estimation and motion-based fall analysis."}
            </p>
          </div>

          <div className="status-panel">
            <span className="metric-label">Live session</span>
            <div className="metrics-grid">
              <div>
                <small>Backend</small>
                <strong>Google Cloud FastAPI</strong>
              </div>
              <div>
                <small>Endpoint</small>
                <strong>{getEndpointLabel(API_URL)}</strong>
              </div>
              <div>
                <small>Frame interval</small>
                <strong>{SAMPLE_INTERVAL_MS} ms</strong>
              </div>
              <div>
                <small>Last response</small>
                <strong>{lastUpdatedAt || "Waiting"}</strong>
              </div>
              <div>
                <small>Latency</small>
                <strong>{latencyMs !== null ? `${Math.round(latencyMs)} ms` : "—"}</strong>
              </div>
            </div>
          </div>

          <div className="status-panel">
            <span className="metric-label">Tracked signals</span>
            <ul className="signal-list">
              <li>Head and mid-hip keypoints</li>
              <li>One-second motion history</li>
              <li>Fall-event status</li>
              <li>Pose landmark overlay</li>
              <li>Inference latency when available</li>
            </ul>
          </div>

          <div className="status-panel">
            <span className="metric-label">Motion metrics</span>
            <div className="metrics-grid">
              <div>
                <small>Fall state</small>
                <strong>{cameraState === "live" ? (fallDetected ? "Detected" : "Monitoring") : "Waiting"}</strong>
              </div>
              <div>
                <small>Lookback window</small>
                <strong>{metrics ? `${(metrics.lookback_ms / 1000).toFixed(1)} s` : "Waiting"}</strong>
              </div>
              <div>
                <small>Head velocity</small>
                <strong>{metrics ? formatMetric(metrics.head_velocity, 3) : "—"}</strong>
              </div>
              <div>
                <small>Head displacement</small>
                <strong>{metrics ? formatMetric(metrics.head_distance, 1) : "—"}</strong>
              </div>
              <div>
                <small>Hip velocity</small>
                <strong>{metrics ? formatMetric(metrics.hip_velocity, 3) : "—"}</strong>
              </div>
              <div>
                <small>Hip displacement</small>
                <strong>{metrics ? formatMetric(metrics.hip_distance, 1) : "—"}</strong>
              </div>
              <div>
                <small>Body ratio</small>
                <strong>{metrics ? formatMetric(metrics.aspect_ratio, 2) : "—"}</strong>
              </div>
              <div>
                <small>Ratio change</small>
                <strong>{metrics ? formatMetric(metrics.ratio_delta, 2) : "—"}</strong>
              </div>
            </div>
          </div>

          <div className="status-panel warning-panel">
            <span className="metric-label">Privacy note</span>
            <p>
              Webcam frames are sent to a Google Cloud-hosted FastAPI backend
              for pose estimation and fall-event analysis. This demo is
              intended for technical evaluation only and is not a certified
              safety or medical monitoring system.
            </p>
          </div>

          {errorMessage && (
            <div className="status-panel error-panel">
              <span className="metric-label">Camera or network error</span>
              <p>{errorMessage}</p>
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}
