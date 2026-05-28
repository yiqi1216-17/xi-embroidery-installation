import cv2
import numpy as np


def resize_max_side(image: np.ndarray, max_size: int) -> np.ndarray:
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= max_size:
        return image
    scale = max_size / longest
    return cv2.resize(
        image,
        (int(width * scale), int(height * scale)),
        interpolation=cv2.INTER_AREA,
    )


def resize_to_fit(
    image: np.ndarray,
    max_width: int,
    max_height: int,
) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height, 1.0)
    if scale >= 1.0:
        return image
    return cv2.resize(
        image,
        (int(width * scale), int(height * scale)),
        interpolation=cv2.INTER_AREA,
    )
