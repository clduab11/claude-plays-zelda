"""Screen capture system for reading game state from emulator."""

import time
from typing import Optional, Tuple
import numpy as np
import cv2
from PIL import Image
import mss
from loguru import logger


class ScreenCapture:
    """Captures and processes screen data from the emulator window."""

    def __init__(
        self,
        window_title: str = "Snes9x",
        capture_region: Optional[dict] = None,
        scale_factor: float = 1.0,
    ):
        """
        Initialize screen capture system.

        Args:
            window_title: Title of the emulator window to capture
            capture_region: Optional dict with keys: top, left, width, height
            scale_factor: Scale factor for captured images
        """
        self.window_title = window_title
        self.capture_region = capture_region
        self.scale_factor = scale_factor
        self.sct = mss.mss()
        self.last_frame: Optional[np.ndarray] = None
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()

        logger.info(f"ScreenCapture initialized for window: {window_title}")

    def find_window(self) -> Optional[dict]:
        """
        Find the emulator window and return its coordinates.

        Returns:
            Dictionary with window coordinates or None if not found
        """
        try:
            import pygetwindow as gw

            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                logger.warning(f"Window '{self.window_title}' not found")
                return None

            window = windows[0]
            return {
                "top": window.top,
                "left": window.left,
                "width": window.width,
                "height": window.height,
            }
        except ImportError:
            logger.warning("pygetwindow not available, using manual region")
            return self.capture_region
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return self.capture_region

    def capture_frame(self, region: Optional[dict] = None) -> Optional[np.ndarray]:
        """
        Capture a single frame from the emulator.

        Args:
            region: Optional region to capture, defaults to auto-detected window

        Returns:
            Captured frame as numpy array (BGR format) or None if capture fails
        """
        try:
            # Use provided region or auto-detect
            if region is None:
                region = self.capture_region or self.find_window()

            if region is None:
                logger.error("No capture region available")
                return None

            # Capture screen
            screenshot = self.sct.grab(region)
            frame = np.array(screenshot)

            # Convert BGRA to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # Apply scaling if needed
            if self.scale_factor != 1.0:
                new_width = int(frame.shape[1] * self.scale_factor)
                new_height = int(frame.shape[0] * self.scale_factor)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

            self.last_frame = frame
            self.frame_count += 1
            self._update_fps()

            return frame

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None

    def capture_frame_pil(self, region: Optional[dict] = None) -> Optional[Image.Image]:
        """
        Capture a frame and return as PIL Image.

        Args:
            region: Optional region to capture

        Returns:
            PIL Image or None if capture fails
        """
        frame = self.capture_frame(region)
        if frame is not None:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None

    def capture_region_of_interest(
        self, x: int, y: int, width: int, height: int
    ) -> Optional[np.ndarray]:
        """
        Capture a specific region of interest from the game screen.

        Args:
            x: X coordinate (relative to game window)
            y: Y coordinate (relative to game window)
            width: Width of region
            height: Height of region

        Returns:
            Cropped frame or None if capture fails
        """
        frame = self.capture_frame()
        if frame is not None:
            return frame[y : y + height, x : x + width]
        return None

    def get_frame_diff(self, threshold: int = 30) -> Optional[np.ndarray]:
        """
        Calculate difference between current and last frame.

        Args:
            threshold: Threshold for considering pixels as changed

        Returns:
            Difference mask or None if no previous frame
        """
        current_frame = self.capture_frame()
        if current_frame is None or self.last_frame is None:
            return None

        # Convert to grayscale
        gray1 = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)

        # Apply threshold
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        return thresh

    def has_screen_changed(self, threshold: int = 30, min_changed_pixels: int = 100) -> bool:
        """
        Check if the screen has changed significantly since last frame.

        Args:
            threshold: Pixel difference threshold
            min_changed_pixels: Minimum number of changed pixels to consider as change

        Returns:
            True if screen has changed significantly
        """
        diff = self.get_frame_diff(threshold)
        if diff is None:
            return True

        changed_pixels = np.sum(diff > 0)
        return changed_pixels > min_changed_pixels

    def save_frame(self, filepath: str, frame: Optional[np.ndarray] = None) -> bool:
        """
        Save a frame to disk.

        Args:
            filepath: Path to save the image
            frame: Optional frame to save, defaults to last captured frame

        Returns:
            True if save was successful
        """
        try:
            frame_to_save = frame if frame is not None else self.last_frame
            if frame_to_save is None:
                logger.error("No frame to save")
                return False

            cv2.imwrite(filepath, frame_to_save)
            logger.debug(f"Frame saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving frame: {e}")
            return False

    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:
            fps = self.fps_counter / elapsed
            logger.debug(f"Capture FPS: {fps:.2f}")
            self.fps_counter = 0
            self.last_fps_time = current_time

    def get_fps(self) -> float:
        """Get current capture FPS."""
        elapsed = time.time() - self.last_fps_time
        if elapsed > 0:
            return self.fps_counter / elapsed
        return 0.0

    def cleanup(self):
        """Clean up resources."""
        try:
            self.sct.close()
            logger.info("ScreenCapture cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
