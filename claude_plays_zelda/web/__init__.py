"""Web module for dashboard and API."""

from claude_plays_zelda.web.server import create_app, WebServer
from claude_plays_zelda.web.websocket_handler import SocketIOHandler

__all__ = ["create_app", "WebServer", "SocketIOHandler"]
