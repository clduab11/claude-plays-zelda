"""Image processing utilities."""

from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PIL import Image
from loguru import logger


def save_image(image: np.ndarray, filepath: str, create_dirs: bool = True) -> bool:
    """
    Save an image to disk.

    Args:
        image: Image array (BGR or RGB)
        filepath: Path to save the image
        create_dirs: Whether to create parent directories

    Returns:
        True if successful
    """
    try:
        if create_dirs:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(filepath, image)
        logger.debug(f"Image saved: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False


def load_image(filepath: str) -> Optional[np.ndarray]:
    """
    Load an image from disk.

    Args:
        filepath: Path to image file

    Returns:
        Image array or None if failed
    """
    try:
        if not Path(filepath).exists():
            logger.error(f"Image file not found: {filepath}")
            return None

        image = cv2.imread(filepath)
        return image

    except Exception as e:
        logger.error(f"Error loading image: {e}")
        return None


def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Resize an image.

    Args:
        image: Input image
        width: Target width
        height: Target height

    Returns:
        Resized image
    """
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)


def crop_image(
    image: np.ndarray, x: int, y: int, width: int, height: int
) -> np.ndarray:
    """
    Crop a region from an image.

    Args:
        image: Input image
        x: X coordinate
        y: Y coordinate
        width: Width of region
        height: Height of region

    Returns:
        Cropped image
    """
    return image[y : y + height, x : x + width]
