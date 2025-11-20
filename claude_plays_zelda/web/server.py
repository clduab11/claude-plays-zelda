"""Flask web server with SocketIO for real-time dashboard."""

import threading
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from loguru import logger

from .security import (
    RateLimiter,
    AuthenticationManager,
    generate_secret_key,
    require_auth,
    apply_rate_limit,
    get_cors_config,
)


def create_app(
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[Flask, SocketIO, AuthenticationManager, RateLimiter]:
    """
    Create Flask application with SocketIO with enhanced security.

    Args:
        config: Application configuration containing:
            - secret_key: Flask secret key (generated if not provided)
            - api_keys: List of valid API keys for authentication
            - environment: 'development' or 'production'
            - allowed_origins: List of allowed CORS origins
            - rate_limit_per_minute: Rate limit per minute (default: 60)
            - rate_limit_per_hour: Rate limit per hour (default: 1000)

    Returns:
        Tuple of (app, socketio, auth_manager, rate_limiter)
    """
    config = config or {}

    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Generate secure secret key
    secret_key = config.get("secret_key")
    if not secret_key:
        secret_key = os.environ.get("FLASK_SECRET_KEY")
        if not secret_key:
            secret_key = generate_secret_key()
            logger.warning(
                "No secret key provided, generated temporary key. "
                "Set FLASK_SECRET_KEY environment variable for production!"
            )

    app.config["SECRET_KEY"] = secret_key

    # Initialize security components
    environment = config.get("environment", "production")
    auth_manager = AuthenticationManager(api_keys=config.get("api_keys"))
    rate_limiter = RateLimiter(
        requests_per_minute=config.get("rate_limit_per_minute", 60),
        requests_per_hour=config.get("rate_limit_per_hour", 1000),
    )

    # Configure CORS based on environment
    cors_config = get_cors_config(
        environment=environment, allowed_origins=config.get("allowed_origins")
    )
    CORS(app, **cors_config)
    logger.info(f"CORS configured for {environment} environment")

    # Initialize SocketIO with security
    socketio_origins = cors_config["origins"]
    socketio = SocketIO(
        app,
        cors_allowed_origins=socketio_origins,
        async_mode="threading",
        ping_timeout=60,
        ping_interval=25,
    )

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

    # Store security components for use in routes
    app.auth_manager = auth_manager
    app.rate_limiter = rate_limiter

    # Routes
    @app.route("/")
    def index():
        """Serve dashboard page."""
        return render_template("dashboard.html")

    @app.route("/api/state")
    @require_auth(auth_manager)
    @apply_rate_limit(rate_limiter)
    def get_state():
        """Get current game state."""
        return jsonify(app.game_state)

    @app.route("/api/stats")
    @require_auth(auth_manager)
    @apply_rate_limit(rate_limiter)
    def get_stats():
        """Get game statistics."""
        return jsonify(
            {
                "deaths": app.game_state.get("deaths", 0),
                "enemies_defeated": app.game_state.get("enemies_defeated", 0),
                "decisions_made": len(app.game_state.get("decisions", [])),
                "events_recorded": len(app.game_state.get("events", [])),
            }
        )

    @app.route("/api/decisions")
    @require_auth(auth_manager)
    @apply_rate_limit(rate_limiter)
    def get_decisions():
        """Get recent decisions."""
        decisions = app.game_state.get("decisions", [])
        return jsonify(decisions[-50:])  # Last 50 decisions

    @app.route("/api/events")
    @require_auth(auth_manager)
    @apply_rate_limit(rate_limiter)
    def get_events():
        """Get recent events."""
        events = app.game_state.get("events", [])
        return jsonify(events[-100:])  # Last 100 events

    @app.route("/health")
    def health():
        """Health check endpoint (no rate limit)."""
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "auth_enabled": auth_manager.enabled,
            }
        )

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

    return app, socketio, auth_manager, rate_limiter


class WebServer:
    """Web server manager for the dashboard."""

    def __init__(
        self, host: str = "0.0.0.0", port: int = 5000, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize web server with enhanced security.

        Args:
            host: Server host (default "0.0.0.0" binds to all interfaces for 
                  containerized deployment; use "127.0.0.1" for local-only access)
            port: Server port
            config: Application configuration (see create_app for details)
        
        Security Note:
            Binding to 0.0.0.0 is intentional for Docker/container environments.
            For production deployments, ensure proper firewall rules and use the
            authentication/rate limiting features provided in the config.
        """
        self.host = host
        self.port = port
        self.app, self.socketio, self.auth_manager, self.rate_limiter = create_app(config)
        self._server_thread: Optional[threading.Thread] = None
        self.is_running = False

        logger.info(
            f"WebServer initialized (host={host}, port={port}, "
            f"auth={'enabled' if self.auth_manager.enabled else 'disabled'})"
        )

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
        self.app.game_state["enemies_defeated"] = (
            self.app.game_state.get("enemies_defeated", 0) + count
        )
        self.socketio.emit("state_update", self.app.game_state)

    def set_objective(self, objective: str):
        """Set current objective."""
        self.app.game_state["current_objective"] = objective
        self.socketio.emit("objective", {"objective": objective})
        self.socketio.emit("state_update", self.app.game_state)

    def get_url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"
