import base64
import numpy as np
import cv2


def decode_image_from_b64(image_b64: str) -> np.ndarray:
    payload = image_b64.split(",")[-1]
    data = base64.b64decode(payload)
    img_array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image payload")
    return image
