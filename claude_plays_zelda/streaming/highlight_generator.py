"""Highlight clip generator for key moments."""

import os
import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from collections import deque
import numpy as np
import cv2
from loguru import logger


class HighlightGenerator:
    """Generates highlight clips from gameplay events."""

    def __init__(
        self,
        output_dir: str = "data/highlights",
        buffer_seconds: int = 30,
        fps: int = 30,
        resolution: tuple = (1280, 720),
    ):
        """
        Initialize highlight generator.

        Args:
            output_dir: Directory to save highlight clips
            buffer_seconds: Seconds of footage to keep in buffer
            fps: Frames per second for recordings
            resolution: Output video resolution
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.buffer_seconds = buffer_seconds
        self.fps = fps
        self.resolution = resolution

        # Frame buffer (circular buffer for recent frames)
        self.buffer_size = buffer_seconds * fps
        self.frame_buffer: deque = deque(maxlen=self.buffer_size)
        self.timestamp_buffer: deque = deque(maxlen=self.buffer_size)

        # Event tracking
        self.events: List[Dict[str, Any]] = []
        self.is_running = False

        # Recording state
        self.is_recording = False
        self.current_recording: List[np.ndarray] = []
        self.recording_start_time: Optional[datetime] = None

        # Event types and their importance
        self.event_priorities = {
            "boss_defeat": 10,
            "dungeon_complete": 9,
            "item_collected": 5,
            "puzzle_solve": 7,
            "death": 8,
            "combat_victory": 4,
            "secret_found": 6,
        }

        logger.info(f"HighlightGenerator initialized (buffer={buffer_seconds}s, output={output_dir})")

    def start(self):
        """Start the highlight generator."""
        self.is_running = True
        logger.info("HighlightGenerator started")

    def stop(self):
        """Stop the highlight generator."""
        self.is_running = False

        # Save any pending recording
        if self.is_recording:
            self._finish_recording()

        logger.info("HighlightGenerator stopped")

    def add_frame(self, frame: np.ndarray):
        """
        Add a frame to the buffer.

        Args:
            frame: Game frame (BGR format)
        """
        if not self.is_running:
            return

        # Resize frame if needed
        if frame.shape[:2] != self.resolution[::-1]:
            frame = cv2.resize(frame, self.resolution)

        # Add to buffer
        self.frame_buffer.append(frame.copy())
        self.timestamp_buffer.append(time.time())

        # Add to recording if active
        if self.is_recording:
            self.current_recording.append(frame.copy())

    def record_event(
        self,
        event_type: str,
        frame: Optional[np.ndarray] = None,
        metadata: Dict[str, Any] = None,
    ):
        """
        Record a highlight-worthy event.

        Args:
            event_type: Type of event
            frame: Current frame (optional)
            metadata: Additional event data
        """
        if not self.is_running:
            return

        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "priority": self.event_priorities.get(event_type, 1),
            "metadata": metadata or {},
        }

        self.events.append(event)
        logger.info(f"Highlight event recorded: {event_type}")

        # Auto-generate clip for high-priority events
        if event["priority"] >= 7:
            self._generate_clip_from_buffer(event_type)

        # Add frame if provided
        if frame is not None:
            self.add_frame(frame)

    def start_recording(self, event_name: str = "manual"):
        """
        Start recording a clip.

        Args:
            event_name: Name for the recording
        """
        if self.is_recording:
            return

        self.is_recording = True
        self.current_recording = []
        self.recording_start_time = datetime.now()

        # Include buffer frames at start
        self.current_recording.extend(list(self.frame_buffer))

        logger.info(f"Started recording: {event_name}")

    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save clip.

        Returns:
            Path to saved clip or None
        """
        if not self.is_recording:
            return None

        return self._finish_recording()

    def _finish_recording(self) -> Optional[str]:
        """Finish and save current recording."""
        self.is_recording = False

        if not self.current_recording:
            logger.warning("No frames to save")
            return None

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"highlight_{timestamp}.mp4"
        filepath = self.output_dir / filename

        # Save video
        success = self._save_video(self.current_recording, str(filepath))
        self.current_recording = []

        if success:
            logger.info(f"Highlight saved: {filepath}")
            return str(filepath)
        else:
            logger.error("Failed to save highlight")
            return None

    def _generate_clip_from_buffer(self, event_name: str) -> Optional[str]:
        """
        Generate a clip from the current buffer.

        Args:
            event_name: Name for the clip

        Returns:
            Path to saved clip or None
        """
        if not self.frame_buffer:
            logger.warning("Buffer empty, cannot generate clip")
            return None

        # Copy buffer
        frames = list(self.frame_buffer)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = event_name.replace(" ", "_").lower()
        filename = f"{safe_name}_{timestamp}.mp4"
        filepath = self.output_dir / filename

        # Save video
        success = self._save_video(frames, str(filepath))

        if success:
            logger.info(f"Clip generated: {filepath}")
            return str(filepath)
        else:
            logger.error(f"Failed to generate clip: {event_name}")
            return None

    def _save_video(self, frames: List[np.ndarray], filepath: str) -> bool:
        """
        Save frames as video file.

        Args:
            frames: List of frames
            filepath: Output path

        Returns:
            True if successful
        """
        if not frames:
            return False

        try:
            # Get frame dimensions
            height, width = frames[0].shape[:2]

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(filepath, fourcc, self.fps, (width, height))

            if not writer.isOpened():
                logger.error("Failed to open video writer")
                return False

            # Write frames
            for frame in frames:
                writer.write(frame)

            writer.release()
            return True

        except Exception as e:
            logger.error(f"Error saving video: {e}")
            return False

    def generate_reel(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a highlight reel from recorded events.

        Args:
            output_path: Output path (default: auto-generated)

        Returns:
            Path to generated reel or None
        """
        # Find all highlight clips
        clips = sorted(self.output_dir.glob("*.mp4"))

        if not clips:
            logger.warning("No clips found for highlight reel")
            return None

        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"reel_{timestamp}.mp4")

        try:
            # Read and concatenate clips
            all_frames = []

            for clip_path in clips:
                cap = cv2.VideoCapture(str(clip_path))
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # Resize if needed
                    if frame.shape[:2] != self.resolution[::-1]:
                        frame = cv2.resize(frame, self.resolution)
                    all_frames.append(frame)
                cap.release()

            if not all_frames:
                logger.warning("No frames collected for reel")
                return None

            # Save combined video
            if self._save_video(all_frames, output_path):
                logger.info(f"Highlight reel generated: {output_path}")
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Error generating reel: {e}")
            return None

    def get_event_count(self) -> int:
        """Get number of recorded events."""
        return len(self.events)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all recorded events."""
        return self.events.copy()

    def get_clip_list(self) -> List[str]:
        """Get list of generated clips."""
        return [str(p) for p in sorted(self.output_dir.glob("*.mp4"))]

    def clear_events(self):
        """Clear event history."""
        self.events.clear()

    def clear_buffer(self):
        """Clear frame buffer."""
        self.frame_buffer.clear()
        self.timestamp_buffer.clear()
