import cv2
import numpy as np


def estimate_spoof_score(frame: np.ndarray) -> float:
    # Heuristic baseline: low texture variance often appears in screen/photo replays.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    normalized = max(0.0, min(1.0, 1.0 - (laplacian_var / 500.0)))
    return float(normalized)
