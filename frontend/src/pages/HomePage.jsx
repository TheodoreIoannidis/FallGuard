import { Link } from "react-router-dom";

const HERO_VIDEO_URL = "/media/test_fallguard_annotated_web.mp4";

const featureCards = [
  {
    title: "Webcam-to-API inference",
    body: "Sends selected video frames from the browser to a cloud-hosted FastAPI service for pose estimation and event analysis.",
  },
  {
    title: "Landmark-based motion analysis",
    body: "Uses MediaPipe head and mid-hip keypoints to estimate body movement, posture change, and rapid downward motion.",
  },
  {
    title: "In-frame fall alert",
    body: "Overlays a visible warning when the temporal motion logic detects a fall-like sequence.",
  },
  {
    title: "MediaPipe pose estimation",
    body: "Detects body landmarks from each submitted frame and extracts the keypoints required for motion-based fall reasoning.",
  },
  {
    title: "Physics-inspired event logic",
    body: "Evaluates short-term movement patterns, including head and hip displacement, to distinguish likely falls from normal posture changes.",
  },
  {
    title: "Google Cloud deployment",
    body: "Runs the inference backend as a deployed FastAPI service, keeping the frontend lightweight while centralizing pose estimation and fall detection logic.",
  },
];

export default function HomePage() {
  return (
    <main className="page-shell landing-shell">
      <div className="orb orb-left" />
      <div className="orb orb-right" />

      <section className="hero-grid">
        <div className="hero-copy">
          <h1>FallGuard</h1>
          <div className="author-block">
            <a
              className="author-link"
              href="https://www.linkedin.com/in/theodoros-ioannidis/"
              target="_blank"
              rel="noreferrer"
            >
              by Theodore Ioannidis
            </a>
            <p className="author-role">Computer Vision / AI Engineer</p>
          </div>
          <p className="subtitle">Cloud-deployed fall detection from webcam video</p>
          <p className="hero-description">
            FallGuard demonstrates a real-time computer vision pipeline for
            fall-event detection. The browser captures webcam frames and sends
            them to a Google Cloud-hosted FastAPI backend, where MediaPipe Pose
            extracts body landmarks and a lightweight temporal logic model
            analyzes head and mid-hip motion over a one-second window.
          </p>

          <div className="hero-actions">
            <Link className="primary-button" to="/demo">
              Try live demo
            </Link>
            <a
              className="secondary-button github-button"
              href="https://github.com/TheodoreIoannidis/FallGuard"
              target="_blank"
              rel="noreferrer"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="github-icon"
              >
                <path
                  fill="currentColor"
                  d="M12 2C6.48 2 2 6.59 2 12.25c0 4.53 2.87 8.38 6.84 9.73.5.1.68-.22.68-.49 0-.24-.01-1.04-.01-1.88-2.78.62-3.37-1.22-3.37-1.22-.45-1.18-1.11-1.49-1.11-1.49-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.57 2.35 1.12 2.92.86.09-.67.35-1.12.64-1.38-2.22-.26-4.56-1.14-4.56-5.09 0-1.13.39-2.05 1.03-2.77-.1-.26-.45-1.31.1-2.74 0 0 .84-.28 2.75 1.06A9.3 9.3 0 0 1 12 6.84c.85 0 1.7.12 2.5.36 1.9-1.34 2.74-1.06 2.74-1.06.56 1.43.21 2.48.11 2.74.64.72 1.03 1.64 1.03 2.77 0 3.96-2.35 4.83-4.58 5.08.36.32.69.95.69 1.92 0 1.39-.01 2.5-.01 2.84 0 .27.18.6.69.49A10.25 10.25 0 0 0 22 12.25C22 6.59 17.52 2 12 2Z"
                />
              </svg>
              GitHub
            </a>
          </div>
        </div>

        <div className="hero-preview">
          <div className="preview-frame">
            <div className="preview-topbar">
              <span className="preview-pill">Demo preview</span>
            </div>

            <div className="preview-body">
              <div className="preview-video preview-demo-video">
                <video
                  className="hero-preview-video"
                  src={HERO_VIDEO_URL}
                  autoPlay
                  muted
                  loop
                  playsInline
                />
              </div>
              <div className="preview-panel">
                <div className="metric-card">
                  <span className="metric-label">Inference path</span>
                  <strong>Browser webcam to cloud-hosted FastAPI backend</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Pose model</span>
                  <strong>MediaPipe landmarks with head and mid-hip tracking</strong>
                </div>
                <div className="metric-card critical">
                  <span className="metric-label">Detection logic</span>
                  <strong>One-second temporal analysis with in-frame fall alert</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="feature-section" id="how-it-works">
        {featureCards.map((card) => (
          <article className="feature-card" key={card.title}>
            <h2>{card.title}</h2>
            <p>{card.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
