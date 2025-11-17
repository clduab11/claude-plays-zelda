"""Screen capture functionality for the emulator."""

import time
from typing import Optional, Tuple
import numpy as np
import pyautogui
from PIL import Image
import cv2
from loguru import logger


class ScreenCapture:
    """Captures screenshots from the emulator window."""

    def __init__(self, window_name: str = "Snes9x", target_resolution: Tuple[int, int] = (256, 224)):
        """
        Initialize the screen capture.

        Args:
            window_name: Name of the emulator window
            target_resolution: Expected SNES resolution (width, height)
        """
        self.window_name = window_name
        self.target_resolution = target_resolution
        self.last_capture: Optional[np.ndarray] = None
        self.last_capture_time: float = 0

    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture the current screen from the emulator.

        Returns:
            numpy.ndarray: Captured image in BGR format, or None if capture failed
        """
        try:
            # Capture the entire screen (in a real implementation, we'd focus on the window)
            screenshot = pyautogui.screenshot()
            
            # Convert PIL Image to numpy array (RGB)
            img_rgb = np.array(screenshot)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
            self.last_capture = img_bgr
            self.last_capture_time = time.time()
            
            return img_bgr
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capture a specific region of the screen.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Width of region
            height: Height of region

        Returns:
            numpy.ndarray: Captured region in BGR format
        """
        try:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            img_rgb = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            return img_bgr
        except Exception as e:
            logger.error(f"Failed to capture region: {e}")
            return None

    def get_last_capture(self) -> Optional[np.ndarray]:
        """
        Get the last captured screen.

        Returns:
            numpy.ndarray: Last captured image, or None if no capture exists
        """
        return self.last_capture

    def resize_to_target(self, image: np.ndarray) -> np.ndarray:
        """
        Resize an image to the target resolution.

        Args:
            image: Input image

        Returns:
            numpy.ndarray: Resized image
        """
        return cv2.resize(image, self.target_resolution, interpolation=cv2.INTER_AREA)

    def save_screenshot(self, filename: str, image: Optional[np.ndarray] = None) -> bool:
        """
        Save a screenshot to file.

        Args:
            filename: Output filename
            image: Image to save (uses last capture if None)

        Returns:
            bool: True if saved successfully
        """
        try:
            img = image if image is not None else self.last_capture
            if img is None:
                logger.error("No image to save")
                return False
            
            cv2.imwrite(filename, img)
            logger.info(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return False

    def get_grayscale(self, image: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """
        Convert image to grayscale.

        Args:
            image: Input image (uses last capture if None)

        Returns:
            numpy.ndarray: Grayscale image
        """
        try:
            img = image if image is not None else self.last_capture
            if img is None:
                return None
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            logger.error(f"Failed to convert to grayscale: {e}")
            return None

    def get_roi(self, image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """
        Extract region of interest from image.

        Args:
            image: Input image
            x: Left coordinate
            y: Top coordinate
            width: Width of ROI
            height: Height of ROI

        Returns:
            numpy.ndarray: Extracted region
        """
        return image[y:y+height, x:x+width]

    def compare_frames(self, frame1: np.ndarray, frame2: np.ndarray, threshold: float = 0.95) -> bool:
        """
        Compare two frames for similarity.

        Args:
            frame1: First frame
            frame2: Second frame
            threshold: Similarity threshold (0-1)

        Returns:
            bool: True if frames are similar
        """
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Compute structural similarity
            # Simple pixel comparison for now
            diff = cv2.absdiff(gray1, gray2)
            similarity = 1.0 - (np.sum(diff) / (gray1.size * 255))
            
            return similarity >= threshold
        except Exception as e:
            logger.error(f"Failed to compare frames: {e}")
            return False

    def detect_motion(self, previous_frame: np.ndarray, current_frame: np.ndarray, 
                     threshold: int = 25) -> bool:
        """
        Detect motion between two frames.

        Args:
            previous_frame: Previous frame
            current_frame: Current frame
            threshold: Motion detection threshold

        Returns:
            bool: True if motion detected
        """
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            # Compute absolute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
            
            # Count non-zero pixels
            motion_pixels = cv2.countNonZero(thresh)
            
            return motion_pixels > 100  # Arbitrary threshold
        except Exception as e:
            logger.error(f"Failed to detect motion: {e}")
            return False
