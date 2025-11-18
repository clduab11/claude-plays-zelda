# Quick Start Guide

Get Claude playing Zelda in 5 minutes!

## Prerequisites

1. **Python 3.11+** installed
2. **SNES9x emulator** ([Download](https://www.snes9x.com/))
3. **The Legend of Zelda: A Link to the Past ROM** (legally obtained)
4. **Anthropic API key** ([Get one here](https://console.anthropic.com/))

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/clduab11/claude-plays-zelda.git
cd claude-plays-zelda

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Configure Settings

Edit `config.yaml`:

```yaml
emulator:
  executable_path: snes9x  # Path to SNES9x
  rom_path: /path/to/zelda_alttp.smc  # Your ROM path
```

### 5. Run!

```bash
python main.py
```

The AI will:
1. Start the SNES9x emulator
2. Load the game
3. Begin playing autonomously
4. Display live dashboard at http://localhost:5000

## Dashboard Features

Access the web dashboard to monitor Claude's gameplay:

- **Real-time game state** (health, rupees, location)
- **Live statistics** (rooms visited, enemies defeated)
- **Current action** being taken
- **Play time** and performance metrics

Visit: `http://localhost:5000`

## Basic Configuration

### Adjust AI Behavior

In `config.yaml`, customize:

```yaml
agent:
  decision_interval: 0.5  # Seconds between decisions (faster = more reactive)

game:
  combat:
    aggressive_mode: false  # Set true for more aggressive combat
    dodge_priority: high    # low/medium/high

  navigation:
    pathfinding_algorithm: a_star  # a_star, bfs, or dfs
```

### Enable Streaming

```yaml
streaming:
  enabled: true
  dashboard:
    port: 5000  # Change if port 5000 is in use
```

## Troubleshooting

### Issue: "Failed to start emulator"
- Check that SNES9x is installed and in PATH
- Verify the `executable_path` in `config.yaml`

### Issue: "Failed to capture screen"
- Ensure SNES9x window is visible
- Check window name matches `config.yaml` setting

### Issue: "No module named 'anthropic'"
- Run: `pip install -r requirements.txt`

### Issue: "ANTHROPIC_API_KEY not set"
- Verify `.env` file exists with your API key
- Key should start with `sk-ant-`

### Issue: Tests failing with display errors
- Tests require X11 display or run with mocked GUI
- Fixed in latest version with lazy-loaded GUI dependencies

## Usage Tips

### Save States
The system automatically manages save states in `save_states/` directory.

### Memory Persistence
Game progress is saved in `agent_memory.json` - delete to start fresh.

### Logs
Check `logs/claude_zelda.log` for detailed information.

### Statistics
Stats are saved to `stats.json` after each session.

## Advanced Usage

### Custom Combat Strategy

```python
from src.game.combat_ai import CombatStrategy

# In your code
combat_ai.set_strategy(CombatStrategy.AGGRESSIVE)
```

### Puzzle Solving

The AI automatically detects and solves common Zelda puzzles:
- Switch puzzles
- Block pushing
- Torch lighting
- Key/door puzzles

### Navigation

Pathfinding algorithms available:
- **A\*** - Best for shortest path
- **BFS** - Breadth-first search
- **DFS** - Depth-first search (exploration)

## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# With coverage
pytest tests/ --cov=src
```

## Next Steps

1. **Watch the dashboard** to see Claude's decision-making
2. **Adjust settings** to change behavior
3. **Monitor logs** for detailed insights
4. **Experiment** with different strategies

## Support

- **Issues**: [GitHub Issues](https://github.com/clduab11/claude-plays-zelda/issues)
- **Discussions**: [GitHub Discussions](https://github.com/clduab11/claude-plays-zelda/discussions)

## Credits

Built with:
- Anthropic's Claude API
- OpenCV for computer vision
- SNES9x emulator
- Flask for web dashboard

---

**Ready to see AI play Zelda? Run `python main.py` and visit http://localhost:5000!** 🎮✨
