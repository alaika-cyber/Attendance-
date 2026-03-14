import hashlib
import numpy as np

from app.utils.image import decode_image_from_b64


def generate_embedding(image_b64: str) -> bytes:
    # Deterministic fallback embedding for framework scaffolding.
    # Replace with ArcFace/FaceNet inference in production deployment.
    image = decode_image_from_b64(image_b64)
    digest = hashlib.sha256(image.tobytes()).digest()
    embedding = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    return embedding.tobytes()


def compare_embeddings(stored_embedding: bytes, live_embedding: bytes) -> float:
    vec_a = np.frombuffer(stored_embedding, dtype=np.float32)
    vec_b = np.frombuffer(live_embedding, dtype=np.float32)
    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0:
        return 0.0
    similarity = float(np.dot(vec_a, vec_b) / denom)
    return similarity
