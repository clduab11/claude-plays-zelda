# API Documentation

## Overview

This document provides comprehensive API documentation for the Claude Plays Zelda project. The API is organized into several modules, each responsible for specific functionality.

## Table of Contents

- [Core Module](#core-module)
- [AI Module](#ai-module)
- [Vision Module](#vision-module)
- [Game Module](#game-module)
- [Web Module](#web-module)
- [Streaming Module](#streaming-module)
- [Emulator Module](#emulator-module)

---

## Core Module

### Configuration Management

#### `Config`

Main configuration class using Pydantic for validation.

**Location**: `claude_plays_zelda.core.config`

```python
from claude_plays_zelda.core.config import Config

# Load configuration from environment
config = Config()

# Load from specific file
config = Config.from_file("custom_config.json")

# Save configuration
config.save_to_file("saved_config.json")
```

**Fields**:
- `anthropic_api_key` (str, required): Anthropic API key
- `claude_model` (str): Claude model to use (default: "claude-3-5-sonnet-20240620")
- `max_tokens` (int): Maximum tokens for responses (default: 4096)
- `emulator_path` (str): Path to emulator executable
- `rom_path` (str): Path to Zelda ROM file
- `action_delay` (float): Delay between actions in seconds (default: 0.5)
- `decision_interval` (float): Interval between AI decisions (default: 2.0)
- `log_level` (str): Logging level (default: "INFO")

### Configuration Validators

#### `ConfigValidators`

Static validators for configuration values.

**Location**: `claude_plays_zelda.core.validators`

```python
from claude_plays_zelda.core.validators import ConfigValidators

# Validate API key
validated_key = ConfigValidators.validate_api_key(
    key="your-api-key",
    key_name="Anthropic API Key"
)

# Validate port
port = ConfigValidators.validate_port(5000)

# Validate path
path = ConfigValidators.validate_path(
    "/path/to/file",
    must_exist=True,
    must_be_file=True
)

# Validate time interval
interval = ConfigValidators.validate_interval(
    0.5,
    name="action delay",
    min_seconds=0.1,
    max_seconds=10.0
)
```

---

## AI Module

### Claude Agent

#### `ClaudeAgent`

Main AI agent for decision-making and reasoning.

**Location**: `claude_plays_zelda.ai.claude_agent`

```python
from claude_plays_zelda.ai.claude_agent import ClaudeAgent

# Initialize agent
agent = ClaudeAgent(config={
    "api_key": "your-api-key",
    "model": "claude-3-5-sonnet-20240620",
    "max_tokens": 4096
})

# Make decision
game_state = {
    "hearts": {"current_hearts": 3, "max_hearts": 6},
    "rupees": 15,
    "enemies": [],
    "location": (10, 20)
}

decision = await agent.make_decision(game_state)
```

**Methods**:
- `make_decision(game_state: Dict) -> Dict`: Generate action decision
- `update_memory(experience: Dict)`: Update agent memory
- `get_reasoning() -> str`: Get AI reasoning explanation

### Action Planner

#### `ActionPlanner`

Plans and sequences actions for the AI agent.

**Location**: `claude_plays_zelda.ai.action_planner`

```python
from claude_plays_zelda.ai.action_planner import ActionPlanner

planner = ActionPlanner(config)

# Plan action sequence
actions = planner.plan_action_sequence(
    current_state=game_state,
    goal="reach_dungeon_entrance"
)
```

### Memory System

#### `MemorySystem`

Manages agent memory and learning.

**Location**: `claude_plays_zelda.ai.memory`

```python
from claude_plays_zelda.ai.memory import MemorySystem

memory = MemorySystem(config={
    "max_history": 100,
    "persistence_file": "agent_memory.json"
})

# Store experience
memory.store_experience({
    "action": "attack",
    "result": "enemy_defeated",
    "reward": 10
})

# Retrieve relevant memories
relevant = memory.retrieve_similar(current_context)
```

---

## Vision Module

### Game State Detector

#### `GameStateDetector`

Detects game state from screen captures.

**Location**: `claude_plays_zelda.vision.game_state_detector`

```python
from claude_plays_zelda.vision.game_state_detector import GameStateDetector
import numpy as np

detector = GameStateDetector()

# Analyze game screen
screen = np.array(...)  # Screen capture
state = detector.get_full_game_state(screen)

# Detect specific elements
hearts = detector.detect_hearts(screen)
rupees = detector.detect_rupees(screen)
```

**Returns**:
```python
{
    "hearts": {"current_hearts": 3, "max_hearts": 6},
    "rupees": 15,
    "current_item": "sword",
    "location": (10, 20),
    "timestamp": "2025-11-20T..."
}
```

### Vision Cache

#### `VisionCache`

LRU cache for vision processing optimization.

**Location**: `claude_plays_zelda.vision.cache`

```python
from claude_plays_zelda.vision.cache import VisionCache

cache = VisionCache(
    max_size=100,
    ttl_seconds=1.0,
    enable_stats=True
)

# Cached operation
result = cache.cached_operation(
    image=screen,
    operation="detect_hearts",
    func=lambda: detector.detect_hearts(screen)
)

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
```

### OCR Processor

#### `OCRProcessor`

Optical character recognition for in-game text.

**Location**: `claude_plays_zelda.vision.ocr`

```python
from claude_plays_zelda.vision.ocr import OCRProcessor

ocr = OCRProcessor()

# Extract text from image
text = ocr.extract_text(
    image=screen_region,
    confidence_threshold=60
)
```

### Object Detector

#### `ObjectDetector`

Detects enemies, items, and objects in game.

**Location**: `claude_plays_zelda.vision.object_detector`

```python
from claude_plays_zelda.vision.object_detector import ObjectDetector

detector = ObjectDetector()

# Detect enemies
enemies = detector.detect_enemies(screen)

# Detect items
items = detector.detect_items(screen)
```

---

## Web Module

### Web Server

#### `WebServer`

Flask-based web dashboard with WebSocket support.

**Location**: `claude_plays_zelda.web.server`

```python
from claude_plays_zelda.web.server import WebServer

# Initialize with security
server = WebServer(
    host="0.0.0.0",
    port=5000,
    config={
        "environment": "production",
        "api_keys": ["your-api-key"],
        "allowed_origins": ["https://yourdomain.com"],
        "rate_limit_per_minute": 60,
        "rate_limit_per_hour": 1000
    }
)

# Start server
server.start()

# Update game state
server.update_state({
    "hearts": {"current_hearts": 3, "max_hearts": 6},
    "rupees": 20
})

# Broadcast decision
server.update_decision({
    "action": "move_right",
    "reasoning": "Exploring new area"
})
```

### Security

#### `RateLimiter`

Rate limiting for API endpoints.

**Location**: `claude_plays_zelda.web.security`

```python
from claude_plays_zelda.web.security import RateLimiter

limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000
)

# Check if IP is rate limited
is_limited, reason = limiter.is_rate_limited("192.168.1.1")
```

#### `AuthenticationManager`

Token-based authentication.

```python
from claude_plays_zelda.web.security import AuthenticationManager

auth = AuthenticationManager(api_keys=["key1", "key2"])

# Check authentication
is_valid = auth.is_authenticated("key1")
```

### REST API Endpoints

#### `GET /api/state`

Get current game state.

**Response**:
```json
{
    "hearts": {"current_hearts": 3, "max_hearts": 6},
    "rupees": 15,
    "deaths": 2,
    "enemies_defeated": 10,
    "current_action": "exploring",
    "current_objective": "find dungeon"
}
```

#### `GET /api/stats`

Get game statistics.

**Response**:
```json
{
    "deaths": 2,
    "enemies_defeated": 10,
    "decisions_made": 150,
    "events_recorded": 75
}
```

#### `GET /api/decisions`

Get recent AI decisions (last 50).

**Response**:
```json
[
    {
        "action": "attack",
        "reasoning": "Enemy in range",
        "timestamp": "2025-11-20T10:30:00"
    }
]
```

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-11-20T10:30:00",
    "auth_enabled": true
}
```

### WebSocket Events

#### `connect`

Client connects to WebSocket.

**Server Response**: Sends current game state

#### `disconnect`

Client disconnects from WebSocket.

#### `request_state`

Client requests current state.

**Server Response**: `state_update` event

#### `state_update`

Server broadcasts state update.

**Payload**: Full game state

#### `decision`

Server broadcasts new AI decision.

**Payload**: Decision object

#### `event`

Server broadcasts game event.

**Payload**: Event object

---

## Game Module

### Combat AI

#### `CombatAI`

Combat strategies and enemy analysis.

**Location**: `claude_plays_zelda.game.combat_ai`

```python
from claude_plays_zelda.game.combat_ai import CombatAI

combat = CombatAI(config={
    "aggressive_mode": False,
    "dodge_priority": "high"
})

# Get combat action
action = combat.get_combat_action(
    enemies=detected_enemies,
    player_health=current_hearts,
    available_items=inventory
)
```

### Dungeon Navigator

#### `DungeonNavigator`

Navigation and pathfinding in dungeons.

**Location**: `claude_plays_zelda.game.dungeon_navigator`

```python
from claude_plays_zelda.game.dungeon_navigator import DungeonNavigator

navigator = DungeonNavigator(config={
    "pathfinding_algorithm": "a_star"
})

# Get path to target
path = navigator.find_path(
    start=(10, 20),
    goal=(50, 60),
    obstacles=obstacle_list
)
```

---

## Streaming Module

### Twitch Bot

#### `TwitchBot`

Twitch chat integration.

**Location**: `claude_plays_zelda.streaming.twitch_bot`

```python
from claude_plays_zelda.streaming.twitch_bot import TwitchBot

bot = TwitchBot(
    token="oauth:...",
    channel="your_channel"
)

# Start bot
await bot.start()
```

**Commands**:
- `!stats`: Display current statistics
- `!hearts`: Show current health
- `!help`: Show available commands

---

## Error Handling

All API methods raise appropriate exceptions:

- `ValueError`: Invalid input parameters
- `ConfigurationError`: Configuration issues
- `APIError`: External API errors
- `VisionError`: Computer vision processing errors

Example error handling:

```python
from claude_plays_zelda.core.config import Config

try:
    config = Config()
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Rate Limits

API endpoints are rate-limited:
- **Per minute**: 60 requests (default)
- **Per hour**: 1000 requests (default)

Rate limit headers:
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time until reset

---

## Authentication

Protected endpoints require authentication via:

1. **Authorization header**: `Authorization: Bearer <api-key>`
2. **X-API-Key header**: `X-API-Key: <api-key>`
3. **Query parameter**: `?api_key=<api-key>`

---

## Best Practices

1. **Configuration**: Always validate configuration before use
2. **Error Handling**: Catch and handle specific exceptions
3. **Rate Limiting**: Respect rate limits in production
4. **Caching**: Use vision cache for performance
5. **Security**: Never commit API keys to version control
6. **Logging**: Use appropriate log levels

---

## Examples

See `/examples` directory for complete usage examples:
- `basic_usage.py`: Simple AI agent setup
- `web_dashboard.py`: Web dashboard integration
- `vision_processing.py`: Computer vision examples
- `streaming_setup.py`: Twitch streaming configuration

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/clduab11/claude-plays-zelda/issues
- GitHub Repository: https://github.com/clduab11/claude-plays-zelda
