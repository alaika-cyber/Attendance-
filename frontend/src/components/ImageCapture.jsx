import { useEffect, useRef, useState } from "react";

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function ImageCapture({ label, onChange }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [preview, setPreview] = useState("");
  const [cameraOn, setCameraOn] = useState(false);
  const [streamReady, setStreamReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  async function startCamera() {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera API not supported");
      }

      stopCamera();
      setStreamReady(false);

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });

      streamRef.current = stream;
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        video.onloadedmetadata = async () => {
          try {
            await video.play();
          } catch {
            // Browser may still block autoplay in rare cases.
          }
          setStreamReady(true);
        };
      }
      setCameraOn(true);
      setError("");
    } catch {
      setError("Camera access failed. Use upload as fallback.");
    }
  }

  function stopCamera() {
    const stream = streamRef.current || videoRef.current?.srcObject;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
    setCameraOn(false);
    setStreamReady(false);
  }

  function captureFrame() {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video.videoWidth || !video.videoHeight) {
      setError("Live preview is not ready yet. Please wait a moment and try again.");
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64 = canvas.toDataURL("image/jpeg", 0.92);
    setPreview(base64);
    onChange(base64);
    stopCamera();
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const base64 = await fileToBase64(file);
    setPreview(base64);
    onChange(base64);
  }

  return (
    <div className="capture-card">
      <p className="field-label">{label}</p>

      <div className="capture-actions">
        {!cameraOn ? (
          <button type="button" className="btn ghost" onClick={startCamera}>
            Start Camera
          </button>
        ) : (
          <>
            <button type="button" className="btn" onClick={captureFrame}>
              Capture Photo
            </button>
            <button type="button" className="btn ghost" onClick={stopCamera}>
              Stop
            </button>
          </>
        )}

        <label className="btn ghost upload-btn">
          Upload Image
          <input type="file" accept="image/*" onChange={handleUpload} hidden />
        </label>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      {cameraOn ? (
        <>
          {!streamReady ? <p className="muted">Starting live preview...</p> : null}
          <video ref={videoRef} autoPlay muted playsInline className="camera-preview" />
        </>
      ) : null}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {preview ? <img src={preview} alt="Captured preview" className="image-preview" /> : null}
    </div>
  );
}
