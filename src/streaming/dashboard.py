"""Web dashboard for real-time monitoring."""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from typing import Dict, Any, Optional
from loguru import logger
import threading
import base64


class Dashboard:
    """Web dashboard for monitoring the AI's gameplay."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5000, enable_cors: bool = True):
        """
        Initialize the dashboard.

        Args:
            host: Host address
            port: Port number
            enable_cors: Whether to enable CORS
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        
        if enable_cors:
            CORS(self.app)
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        
        # Current state
        self.current_state: Dict[str, Any] = {
            "health": 0,
            "max_health": 0,
            "rupees": 0,
            "location": "Unknown",
            "action": "Initializing",
            "enemies": 0,
            "items": 0,
        }
        
        self.stats: Dict[str, Any] = {
            "play_time": 0,
            "rooms_visited": 0,
            "enemies_defeated": 0,
            "items_collected": 0,
            "deaths": 0,
        }
        
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Claude Plays Zelda - Live Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #1a1a1a;
                        color: #ffffff;
                        margin: 0;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    h1 {
                        text-align: center;
                        color: #00ff00;
                    }
                    .grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-top: 20px;
                    }
                    .card {
                        background-color: #2a2a2a;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    }
                    .card h2 {
                        margin-top: 0;
                        color: #00ff00;
                        font-size: 1.2em;
                    }
                    .stat {
                        display: flex;
                        justify-content: space-between;
                        margin: 10px 0;
                        padding: 8px;
                        background-color: #333;
                        border-radius: 4px;
                    }
                    .stat-label {
                        font-weight: bold;
                    }
                    .stat-value {
                        color: #00ff00;
                    }
                    #screenshot {
                        width: 100%;
                        border-radius: 4px;
                        background-color: #000;
                    }
                    .status-indicator {
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        border-radius: 50%;
                        background-color: #00ff00;
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.5; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>
                        <span class="status-indicator"></span>
                        Claude Plays The Legend of Zelda
                    </h1>
                    
                    <div class="grid">
                        <div class="card">
                            <h2>Game State</h2>
                            <div class="stat">
                                <span class="stat-label">Health:</span>
                                <span class="stat-value" id="health">0/0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Rupees:</span>
                                <span class="stat-value" id="rupees">0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Location:</span>
                                <span class="stat-value" id="location">Unknown</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Enemies Visible:</span>
                                <span class="stat-value" id="enemies">0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Items Visible:</span>
                                <span class="stat-value" id="items">0</span>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>AI Status</h2>
                            <div class="stat">
                                <span class="stat-label">Current Action:</span>
                                <span class="stat-value" id="action">Initializing...</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Play Time:</span>
                                <span class="stat-value" id="playtime">0:00:00</span>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Statistics</h2>
                            <div class="stat">
                                <span class="stat-label">Rooms Visited:</span>
                                <span class="stat-value" id="rooms">0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Enemies Defeated:</span>
                                <span class="stat-value" id="defeated">0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Items Collected:</span>
                                <span class="stat-value" id="collected">0</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Deaths:</span>
                                <span class="stat-value" id="deaths">0</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card" style="margin-top: 20px;">
                        <h2>Live Screen</h2>
                        <img id="screenshot" alt="Game screen will appear here">
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    
                    socket.on('connect', function() {
                        console.log('Connected to server');
                    });
                    
                    socket.on('state_update', function(data) {
                        document.getElementById('health').textContent = 
                            data.health + '/' + data.max_health;
                        document.getElementById('rupees').textContent = data.rupees;
                        document.getElementById('location').textContent = data.location;
                        document.getElementById('enemies').textContent = data.enemies;
                        document.getElementById('items').textContent = data.items;
                        document.getElementById('action').textContent = data.action;
                    });
                    
                    socket.on('stats_update', function(data) {
                        const hours = Math.floor(data.play_time / 3600);
                        const minutes = Math.floor((data.play_time % 3600) / 60);
                        const seconds = Math.floor(data.play_time % 60);
                        document.getElementById('playtime').textContent = 
                            hours + ':' + String(minutes).padStart(2, '0') + ':' + 
                            String(seconds).padStart(2, '0');
                        document.getElementById('rooms').textContent = data.rooms_visited;
                        document.getElementById('defeated').textContent = data.enemies_defeated;
                        document.getElementById('collected').textContent = data.items_collected;
                        document.getElementById('deaths').textContent = data.deaths;
                    });
                    
                    socket.on('screenshot', function(data) {
                        document.getElementById('screenshot').src = 
                            'data:image/png;base64,' + data.image;
                    });
                </script>
            </body>
            </html>
            '''
        
        @self.app.route('/api/state')
        def get_state():
            """Get current state via API."""
            return jsonify(self.current_state)
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get statistics via API."""
            return jsonify(self.stats)

    def start(self):
        """Start the dashboard server."""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Dashboard started at http://{self.host}:{self.port}")

    def _run_server(self):
        """Run the Flask server."""
        self.socketio.run(self.app, host=self.host, port=self.port, 
                         allow_unsafe_werkzeug=True, debug=False)

    def stop(self):
        """Stop the dashboard server."""
        self.running = False
        logger.info("Dashboard stopped")

    def update_state(self, state: Dict[str, Any]):
        """
        Update the current game state.

        Args:
            state: New game state
        """
        self.current_state.update(state)
        if self.running:
            self.socketio.emit('state_update', self.current_state)

    def update_stats(self, stats: Dict[str, Any]):
        """
        Update statistics.

        Args:
            stats: New statistics
        """
        self.stats.update(stats)
        if self.running:
            self.socketio.emit('stats_update', self.stats)

    def send_screenshot(self, image_bytes: bytes):
        """
        Send a screenshot to the dashboard.

        Args:
            image_bytes: PNG image bytes
        """
        if self.running:
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            self.socketio.emit('screenshot', {'image': image_b64})

    def log_action(self, action: str):
        """
        Log an action to the dashboard.

        Args:
            action: Action description
        """
        self.current_state["action"] = action
        if self.running:
            self.socketio.emit('state_update', self.current_state)
