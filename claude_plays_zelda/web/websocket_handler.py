"""WebSocket handler for real-time data streaming."""

import json
import time
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from collections import deque
from flask_socketio import SocketIO
from loguru import logger


class SocketIOHandler:
    """Handles WebSocket communication for real-time updates."""

    def __init__(self, socketio: SocketIO, max_history: int = 100):
        """
        Initialize WebSocket handler.

        Args:
            socketio: Flask-SocketIO instance
            max_history: Maximum history items to keep
        """
        self.socketio = socketio
        self.max_history = max_history

        # Data stores
        self.decision_history: deque = deque(maxlen=max_history)
        self.event_history: deque = deque(maxlen=max_history * 2)
        self.frame_times: deque = deque(maxlen=60)  # Last 60 frame times for FPS

        # Metrics
        self.total_decisions = 0
        self.total_events = 0
        self.connected_clients = 0

        # Callbacks
        self.on_command_callbacks: Dict[str, Callable] = {}

        logger.info("SocketIOHandler initialized")

    def emit_state_update(self, state: Dict[str, Any]):
        """
        Emit game state update to all clients.

        Args:
            state: Current game state
        """
        try:
            self.socketio.emit("state_update", {
                "state": state,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error emitting state update: {e}")

    def emit_decision(self, decision: Dict[str, Any]):
        """
        Emit AI decision to all clients.

        Args:
            decision: Decision data
        """
        try:
            decision_data = {
                "decision": decision,
                "timestamp": datetime.now().isoformat(),
                "id": self.total_decisions,
            }

            self.decision_history.append(decision_data)
            self.total_decisions += 1

            self.socketio.emit("decision", decision_data)

        except Exception as e:
            logger.error(f"Error emitting decision: {e}")

    def emit_event(self, event_type: str, data: Dict[str, Any] = None):
        """
        Emit game event to all clients.

        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            event_data = {
                "type": event_type,
                "data": data or {},
                "timestamp": datetime.now().isoformat(),
                "id": self.total_events,
            }

            self.event_history.append(event_data)
            self.total_events += 1

            self.socketio.emit("event", event_data)

        except Exception as e:
            logger.error(f"Error emitting event: {e}")

    def emit_frame(self, frame_data: Dict[str, Any]):
        """
        Emit frame data for visualization.

        Args:
            frame_data: Frame information
        """
        try:
            # Track frame times for FPS calculation
            self.frame_times.append(time.time())

            self.socketio.emit("frame", {
                "data": frame_data,
                "fps": self._calculate_fps(),
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Error emitting frame: {e}")

    def emit_metrics(self, metrics: Dict[str, Any]):
        """
        Emit performance metrics.

        Args:
            metrics: Performance metrics
        """
        try:
            self.socketio.emit("metrics", {
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Error emitting metrics: {e}")

    def emit_highlight(self, highlight_data: Dict[str, Any]):
        """
        Emit highlight event notification.

        Args:
            highlight_data: Highlight information
        """
        try:
            self.socketio.emit("highlight", {
                "data": highlight_data,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Error emitting highlight: {e}")

    def emit_error(self, error_message: str, error_type: str = "general"):
        """
        Emit error notification.

        Args:
            error_message: Error message
            error_type: Type of error
        """
        try:
            self.socketio.emit("error", {
                "message": error_message,
                "type": error_type,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Error emitting error: {e}")

    def register_command_callback(self, command: str, callback: Callable):
        """
        Register callback for dashboard commands.

        Args:
            command: Command name
            callback: Callback function
        """
        self.on_command_callbacks[command] = callback
        logger.debug(f"Registered command callback: {command}")

    def handle_command(self, command: str, data: Dict[str, Any] = None):
        """
        Handle command from dashboard.

        Args:
            command: Command name
            data: Command data
        """
        if command in self.on_command_callbacks:
            try:
                self.on_command_callbacks[command](data)
                logger.debug(f"Executed command: {command}")
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
        else:
            logger.warning(f"Unknown command: {command}")

    def _calculate_fps(self) -> float:
        """Calculate current FPS from frame times."""
        if len(self.frame_times) < 2:
            return 0.0

        time_span = self.frame_times[-1] - self.frame_times[0]
        if time_span <= 0:
            return 0.0

        return (len(self.frame_times) - 1) / time_span

    def get_history(self) -> Dict[str, Any]:
        """Get decision and event history."""
        return {
            "decisions": list(self.decision_history),
            "events": list(self.event_history),
            "total_decisions": self.total_decisions,
            "total_events": self.total_events,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "connected_clients": self.connected_clients,
            "total_decisions": self.total_decisions,
            "total_events": self.total_events,
            "current_fps": self._calculate_fps(),
            "history_size": len(self.decision_history) + len(self.event_history),
        }

    def client_connected(self):
        """Track client connection."""
        self.connected_clients += 1
        logger.info(f"Client connected. Total: {self.connected_clients}")

    def client_disconnected(self):
        """Track client disconnection."""
        self.connected_clients = max(0, self.connected_clients - 1)
        logger.info(f"Client disconnected. Total: {self.connected_clients}")
