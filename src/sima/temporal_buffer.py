"""
Temporal buffer for creating filmstrip inputs to the VLM.

Maintains a sliding window of recent frames to provide temporal context
(motion, velocity) to the vision model.
"""

from collections import deque
from typing import List, Optional, Tuple
from PIL import Image
import io
import base64
from loguru import logger


class TemporalBuffer:
    """
    Manages a buffer of recent frames and creates filmstrip images.

    The filmstrip allows the VLM to detect:
    - Enemy movement directions
    - Projectile velocities
    - Link's motion state
    - Animation frames
    """

    def __init__(self, buffer_size: int = 3, filmstrip_orientation: str = "horizontal"):
        """
        Initialize temporal buffer.

        Args:
            buffer_size: Number of frames to keep (default: 3)
            filmstrip_orientation: 'horizontal' or 'vertical' stitching
        """
        self.buffer_size = buffer_size
        self.frame_buffer: deque[Image.Image] = deque(maxlen=buffer_size)
        self.orientation = filmstrip_orientation
        self.frame_count = 0

        logger.info(f"TemporalBuffer initialized: {buffer_size} frames, {filmstrip_orientation}")

    def add_frame(self, frame: Image.Image) -> None:
        """
        Add a frame to the buffer.

        Args:
            frame: PIL Image to add
        """
        self.frame_buffer.append(frame.copy())
        self.frame_count += 1

    def create_filmstrip(self) -> Optional[Image.Image]:
        """
        Create a filmstrip image from buffered frames.

        Returns:
            PIL Image with frames stitched together, or None if buffer empty
        """
        if not self.frame_buffer:
            logger.warning("Cannot create filmstrip: buffer is empty")
            return None

        # If buffer not full yet, pad with duplicates of the last frame
        frames = list(self.frame_buffer)
        if len(frames) < self.buffer_size and frames:
            last_frame = frames[-1]
            while len(frames) < self.buffer_size:
                frames.append(last_frame.copy())

        try:
            if self.orientation == "horizontal":
                return self._stitch_horizontal(frames)
            else:
                return self._stitch_vertical(frames)
        except Exception as e:
            logger.error(f"Failed to create filmstrip: {e}")
            # Return single frame as fallback
            return frames[-1] if frames else None

    def _stitch_horizontal(self, frames: List[Image.Image]) -> Image.Image:
        """
        Stitch frames horizontally [Frame T-2 | Frame T-1 | Frame T].

        Args:
            frames: List of PIL Images

        Returns:
            Stitched PIL Image
        """
        if not frames:
            raise ValueError("No frames to stitch")

        # Calculate dimensions
        widths = [f.width for f in frames]
        heights = [f.height for f in frames]
        total_width = sum(widths)
        max_height = max(heights)

        # Create filmstrip canvas
        filmstrip = Image.new('RGB', (total_width, max_height), color=(0, 0, 0))

        # Paste frames side by side
        x_offset = 0
        for i, frame in enumerate(frames):
            filmstrip.paste(frame, (x_offset, 0))
            x_offset += frame.width

        logger.debug(f"Created horizontal filmstrip: {total_width}x{max_height} from {len(frames)} frames")
        return filmstrip

    def _stitch_vertical(self, frames: List[Image.Image]) -> Image.Image:
        """
        Stitch frames vertically.

        Args:
            frames: List of PIL Images

        Returns:
            Stitched PIL Image
        """
        if not frames:
            raise ValueError("No frames to stitch")

        widths = [f.width for f in frames]
        heights = [f.height for f in frames]
        max_width = max(widths)
        total_height = sum(heights)

        filmstrip = Image.new('RGB', (max_width, total_height), color=(0, 0, 0))

        y_offset = 0
        for frame in frames:
            filmstrip.paste(frame, (0, y_offset))
            y_offset += frame.height

        logger.debug(f"Created vertical filmstrip: {max_width}x{total_height} from {len(frames)} frames")
        return filmstrip

    def get_filmstrip_base64(self, format: str = "PNG") -> Optional[str]:
        """
        Get filmstrip as base64-encoded string for API transmission.

        Args:
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64-encoded image string or None
        """
        filmstrip = self.create_filmstrip()
        if filmstrip is None:
            return None

        try:
            # Convert to base64
            buffer = io.BytesIO()
            filmstrip.save(buffer, format=format)
            buffer.seek(0)
            encoded = base64.b64encode(buffer.read()).decode('utf-8')

            logger.debug(f"Encoded filmstrip to base64 ({len(encoded)} chars)")
            return encoded
        except Exception as e:
            logger.error(f"Failed to encode filmstrip: {e}")
            return None

    def get_latest_frame(self) -> Optional[Image.Image]:
        """
        Get the most recent frame from the buffer.

        Returns:
            Latest PIL Image or None
        """
        if self.frame_buffer:
            return self.frame_buffer[-1]
        return None

    def clear(self) -> None:
        """Clear the frame buffer."""
        self.frame_buffer.clear()
        logger.debug("Frame buffer cleared")

    def is_ready(self) -> bool:
        """
        Check if buffer has enough frames for filmstrip creation.

        Returns:
            True if buffer has at least one frame
        """
        return len(self.frame_buffer) > 0

    def get_frame_count(self) -> int:
        """
        Get total number of frames processed.

        Returns:
            Total frame count
        """
        return self.frame_count

    def get_buffer_info(self) -> dict:
        """
        Get information about the current buffer state.

        Returns:
            Dictionary with buffer statistics
        """
        return {
            "buffer_size": self.buffer_size,
            "current_frames": len(self.frame_buffer),
            "total_frames_processed": self.frame_count,
            "orientation": self.orientation,
            "is_ready": self.is_ready()
        }

    def create_annotated_filmstrip(self, annotations: Optional[List[str]] = None) -> Optional[Image.Image]:
        """
        Create filmstrip with frame annotations (for debugging).

        Args:
            annotations: List of text labels for each frame

        Returns:
            Annotated filmstrip image
        """
        from PIL import ImageDraw, ImageFont

        filmstrip = self.create_filmstrip()
        if filmstrip is None:
            return None

        if annotations is None:
            annotations = [f"T-{self.buffer_size - 1 - i}" for i in range(len(self.frame_buffer))]

        try:
            draw = ImageDraw.Draw(filmstrip)

            # Try to use a font, fall back to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()

            # Add text labels
            if self.orientation == "horizontal":
                x_offset = 0
                for i, frame in enumerate(self.frame_buffer):
                    if i < len(annotations):
                        draw.text((x_offset + 10, 10), annotations[i], fill=(255, 255, 0), font=font)
                    x_offset += frame.width
            else:
                y_offset = 0
                for i, frame in enumerate(self.frame_buffer):
                    if i < len(annotations):
                        draw.text((10, y_offset + 10), annotations[i], fill=(255, 255, 0), font=font)
                    y_offset += frame.height

            return filmstrip
        except Exception as e:
            logger.error(f"Failed to create annotated filmstrip: {e}")
            return filmstrip
