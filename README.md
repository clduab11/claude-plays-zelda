# Claude Plays The Legend of Zelda

An AI system that autonomously plays The Legend of Zelda: A Link to the Past using Claude API and computer vision.

## Overview

This project creates an AI agent powered by Anthropic's Claude that can play The Legend of Zelda: A Link to the Past on SNES9x emulator. The AI uses computer vision to analyze the game state, makes decisions using Claude's reasoning capabilities, and executes actions in real-time.

## Features

### 🎮 Core Modules

1. **Emulator Interface**
   - SNES9x process control and management
   - Real-time screen capture
   - Keyboard input injection for controller emulation
   - Save state management

2. **Computer Vision System**
   - OCR for reading in-game text and dialog
   - Object detection for enemies, items, hearts, and rupees
   - Map recognition and location tracking
   - Health and inventory monitoring from HUD

3. **AI Agent (Claude Integration)**
   - Claude API integration for decision making
   - Context management system with summarization
   - Action planning and execution
   - Persistent memory system for game progress

4. **Game Logic**
   - Combat AI with strategic decision making
   - Puzzle solving algorithms
   - Navigation and pathfinding (A*, BFS, DFS)
   - Quest and objective tracking

5. **Streaming & Dashboard**
   - Real-time web dashboard for monitoring
   - Live statistics and metrics
   - Event logging and tracking
   - Optional Twitch streaming support

## Requirements

- Python 3.11+
- SNES9x emulator
- The Legend of Zelda: A Link to the Past ROM
- Anthropic API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/clduab11/claude-plays-zelda.git
cd claude-plays-zelda
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (for text recognition):
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Create a `.env` file with your API key:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

5. Configure `config.yaml`:
   - Set the path to your SNES9x executable
   - Set the path to your Zelda ROM file
   - Adjust other settings as needed

## Usage

### Basic Usage

Run the AI with default settings:
```bash
python main.py
```

### With Dashboard

The web dashboard starts automatically if enabled in `config.yaml`:
```yaml
streaming:
  enabled: true
  dashboard:
    host: 0.0.0.0
    port: 5000
```

Access the dashboard at `http://localhost:5000`

### Configuration

Edit `config.yaml` to customize:
- Claude model and parameters
- Emulator settings
- Computer vision thresholds
- AI decision intervals
- Combat and exploration strategies
- Dashboard settings

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Main Controller                 │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
┌───────▼─────┐ ┌▼─────────▼┐ ┌──────────────┐
│  Emulator   │ │    CV      │ │  AI Agent    │
│  Interface  │ │  System    │ │   (Claude)   │
├─────────────┤ ├────────────┤ ├──────────────┤
│ • SNES9x    │ │ • OCR      │ │ • Decision   │
│ • Screen    │ │ • Detection│ │ • Context    │
│ • Input     │ │ • Maps     │ │ • Memory     │
└─────────────┘ └────────────┘ └──────────────┘
        │         │         │
        └─────────┼─────────┘
                  │
        ┌─────────▼─────────┐
        │   Game Logic      │
        ├───────────────────┤
        │ • Combat AI       │
        │ • Puzzle Solver   │
        │ • Navigation      │
        └───────────────────┘
                  │
        ┌─────────▼─────────┐
        │    Streaming      │
        ├───────────────────┤
        │ • Dashboard       │
        │ • Statistics      │
        └───────────────────┘
```

## Project Structure

```
claude-plays-zelda/
├── src/
│   ├── emulator/          # Emulator control
│   │   ├── emulator_interface.py
│   │   ├── input_controller.py
│   │   └── screen_capture.py
│   ├── cv/                # Computer vision
│   │   ├── ocr_engine.py
│   │   ├── object_detector.py
│   │   ├── map_recognizer.py
│   │   └── game_state_analyzer.py
│   ├── agent/             # AI agent
│   │   ├── claude_client.py
│   │   ├── context_manager.py
│   │   ├── action_planner.py
│   │   └── memory_system.py
│   ├── game/              # Game logic
│   │   ├── combat_ai.py
│   │   ├── puzzle_solver.py
│   │   └── navigation.py
│   └── streaming/         # Streaming & dashboard
│       ├── dashboard.py
│       └── stats_tracker.py
├── tests/                 # Test suite
│   ├── unit/
│   └── integration/
├── logs/                  # Log files
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
├── main.py               # Entry point
└── README.md             # This file
```

## How It Works

1. **Screen Capture**: Continuously captures the game screen
2. **State Analysis**: Computer vision analyzes the screen to extract:
   - Current health, rupees, and inventory
   - Visible enemies and items
   - Location and map position
   - Dialog text
3. **Decision Making**: Claude receives the game state and decides on the next action
4. **Action Execution**: The action planner converts high-level decisions into specific button inputs
5. **Memory & Learning**: The system tracks progress, learns patterns, and maintains context

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines. Format code with:
```bash
black src/ tests/
```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Limitations

- Requires SNES9x emulator to be installed and configured
- Computer vision detection accuracy depends on screen quality
- Claude API usage incurs costs based on token usage
- Performance varies based on game complexity and AI decisions

## Future Enhancements

- [ ] Twitch streaming integration
- [ ] Machine learning for object detection
- [ ] Advanced puzzle solving with pattern recognition
- [ ] Multi-game support (other Zelda titles)
- [ ] Voice commentary generation
- [ ] Speedrun optimization mode

## License

This project is for educational and research purposes. The Legend of Zelda is property of Nintendo.

## Acknowledgments

- Anthropic for Claude API
- SNES9x emulator team
- The Zelda community

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This AI plays Zelda autonomously using computer vision and Claude's reasoning. It's a demonstration of AI capabilities in game playing and decision making.
