"""Flask web server with SocketIO for real-time dashboard."""

import threading
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from loguru import logger


def create_app(config: Dict[str, Any] = None) -> tuple:
    """
    Create Flask application with SocketIO.

    Args:
        config: Application configuration

    Returns:
        Tuple of (app, socketio)
    """
    app = Flask(__name__,
                template_folder="templates",
                static_folder="static")

    # Configure app
    app.config["SECRET_KEY"] = config.get("secret_key", "zelda-ai-secret") if config else "zelda-ai-secret"

    # Enable CORS
    CORS(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Store for game state
    app.game_state = {
        "hearts": {"current_hearts": 0, "max_hearts": 0},
        "rupees": 0,
        "deaths": 0,
        "enemies_defeated": 0,
        "current_action": "Initializing...",
        "current_objective": "Starting adventure",
        "decisions": [],
        "events": [],
        "uptime": 0,
        "is_running": False,
    }

    # Routes
    @app.route("/")
    def index():
        """Serve dashboard page."""
        return render_template("dashboard.html")

    @app.route("/api/state")
    def get_state():
        """Get current game state."""
        return jsonify(app.game_state)

    @app.route("/api/stats")
    def get_stats():
        """Get game statistics."""
        return jsonify({
            "deaths": app.game_state.get("deaths", 0),
            "enemies_defeated": app.game_state.get("enemies_defeated", 0),
            "decisions_made": len(app.game_state.get("decisions", [])),
            "events_recorded": len(app.game_state.get("events", [])),
        })

    @app.route("/api/decisions")
    def get_decisions():
        """Get recent decisions."""
        decisions = app.game_state.get("decisions", [])
        return jsonify(decisions[-50:])  # Last 50 decisions

    @app.route("/api/events")
    def get_events():
        """Get recent events."""
        events = app.game_state.get("events", [])
        return jsonify(events[-100:])  # Last 100 events

    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    # SocketIO events
    @socketio.on("connect")
    def handle_connect():
        """Handle client connection."""
        logger.info("Client connected to WebSocket")
        emit("state_update", app.game_state)

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info("Client disconnected from WebSocket")

    @socketio.on("request_state")
    def handle_request_state():
        """Handle state request."""
        emit("state_update", app.game_state)

    return app, socketio


class WebServer:
    """Web server manager for the dashboard."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5000, config: Dict[str, Any] = None):
        """
        Initialize web server.

        Args:
            host: Server host
            port: Server port
            config: Application configuration
        """
        self.host = host
        self.port = port
        self.app, self.socketio = create_app(config)
        self._server_thread: Optional[threading.Thread] = None
        self.is_running = False

        logger.info(f"WebServer initialized (host={host}, port={port})")

    def start(self):
        """Start the web server in a background thread."""
        if self.is_running:
            logger.warning("Server already running")
            return

        def run_server():
            try:
                logger.info(f"Starting web server on http://{self.host}:{self.port}")
                self.socketio.run(
                    self.app,
                    host=self.host,
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    log_output=False,
                )
            except Exception as e:
                logger.error(f"Server error: {e}")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self.is_running = True

        logger.info(f"Web server started at http://{self.host}:{self.port}")

    def stop(self):
        """Stop the web server."""
        self.is_running = False
        logger.info("Web server stopped")

    def update_state(self, state: Dict[str, Any]):
        """
        Update game state and broadcast to clients.

        Args:
            state: New game state
        """
        self.app.game_state.update(state)
        self.socketio.emit("state_update", self.app.game_state)

    def update_decision(self, decision: Dict[str, Any]):
        """
        Add a decision and broadcast.

        Args:
            decision: Decision data
        """
        decision["timestamp"] = datetime.now().isoformat()
        self.app.game_state["decisions"].append(decision)

        # Keep only last 100 decisions
        if len(self.app.game_state["decisions"]) > 100:
            self.app.game_state["decisions"] = self.app.game_state["decisions"][-100:]

        self.app.game_state["current_action"] = f"{decision.get('action', 'unknown')}"

        self.socketio.emit("decision", decision)
        self.socketio.emit("state_update", self.app.game_state)

    def add_event(self, event: Dict[str, Any]):
        """
        Add an event and broadcast.

        Args:
            event: Event data
        """
        event["timestamp"] = datetime.now().isoformat()
        self.app.game_state["events"].append(event)

        # Keep only last 200 events
        if len(self.app.game_state["events"]) > 200:
            self.app.game_state["events"] = self.app.game_state["events"][-200:]

        self.socketio.emit("event", event)

    def record_death(self):
        """Record a death."""
        self.app.game_state["deaths"] = self.app.game_state.get("deaths", 0) + 1
        self.socketio.emit("death", {"total": self.app.game_state["deaths"]})
        self.socketio.emit("state_update", self.app.game_state)

    def record_enemy_defeated(self, count: int = 1):
        """Record enemies defeated."""
        self.app.game_state["enemies_defeated"] = self.app.game_state.get("enemies_defeated", 0) + count
        self.socketio.emit("state_update", self.app.game_state)

    def set_objective(self, objective: str):
        """Set current objective."""
        self.app.game_state["current_objective"] = objective
        self.socketio.emit("objective", {"objective": objective})
        self.socketio.emit("state_update", self.app.game_state)

    def get_url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"
