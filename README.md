# 🎮 Claude Plays Zelda

> **An AI agent that autonomously plays The Legend of Zelda (1986, NES) using computer vision, reinforcement learning, SIMA 2, and Claude AI for decision-making.**

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)

**Claude takes on Hyrule!** Watch as an AI agent explores, fights, solves puzzles, and progresses through one of the greatest games of all time.

## ✨ Key Features

- 🤖 **Intelligent AI Agent**: Powered by Claude API for human-like decision-making
- 👁️ **Computer Vision**: Real-time OCR, object detection, and game state analysis
- ⚔️ **Combat AI**: Smart enemy engagement with pattern recognition
- 🗺️ **Dungeon Navigation**: Systematic exploration and puzzle-solving
- 🧠 **Learning System**: Tracks progress, learns from failures, improves over time
- 💾 **Save States**: Automatic checkpointing and progress tracking
- 📊 **Analytics Dashboard**: Real-time statistics and performance monitoring
- 🎮 **Full Emulator Integration**: Seamless SNES9x/ZSNES control

## 🎥 Demo

_(Coming soon - AI gameplay videos)_

## 🔴 Watch Live

Claude plays Zelda live on Twitch! Join the chat to interact with the AI, ask questions, and influence the gameplay.

[**👉 Watch on Twitch**](https://twitch.tv/claudeplayszelda)

## 🤝 Support the Stream

If you enjoy watching an AI struggle through water temples, consider supporting the project!

- [**GitHub Sponsors**](https://github.com/sponsors/clduab11)
- [**Ko-fi**](https://ko-fi.com/claudeplayszelda)

## 💬 Interact with Claude

You can talk to Claude directly through Twitch chat!

| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask Claude a question about the game or its strategy |
| `!stats` | View current health, rupees, and items |
| `!progress` | See current objective and uptime |
| `!deaths` | Check the death counter (it happens!) |

## 📋 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/clduab11/claude-plays-zelda.git
cd claude-plays-zelda

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure (add your API key and paths)
cp .env.example .env
nano .env

# 4. Run!
zelda-ai play --emulator-path /path/to/snes9x --rom-path /path/to/zelda.smc
```

📖 **[Full Setup Guide](docs/SETUP_GUIDE.md)** for detailed instructions.

## 🔧 Requirements

- **Python 3.9+**
- **SNES Emulator** (Snes9x recommended)
- **Tesseract OCR**
- **Anthropic API Key** ([Get one free](https://console.anthropic.com/))
- **Legal ROM** of The Legend of Zelda

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Game Orchestrator                     │
└────────┬──────────────────────────────────────┬─────────┘
         │                                      │
    ┌────▼─────┐                          ┌────▼─────┐
    │ Emulator │                          │ AI Agent │
    │ Manager  │                          │ (Claude) │
    └────┬─────┘                          └────┬─────┘
         │                                      │
    ┌────▼─────────┐                     ┌────▼──────┐
    │ Screen       │                     │ Context   │
    │ Capture      │────────────────────▶│ Manager   │
    └──────────────┘                     └───────────┘
         │                                      │
    ┌────▼──────────┐                    ┌────▼────────┐
    │ Computer      │                    │ Action      │
    │ Vision System │───────────────────▶│ Planner     │
    └───────────────┘                    └─────┬───────┘
         │                                      │
    ┌────▼─────────┐                     ┌────▼──────┐
    │ Game State   │                     │ Memory &  │
    │ Detector     │────────────────────▶│ Learning  │
    └──────────────┘                     └───────────┘
```

### Core Components

| Module                   | Description                                                 |
| ------------------------ | ----------------------------------------------------------- |
| **Emulator Integration** | Screen capture, input control, process management           |
| **Computer Vision**      | OCR, object detection, state analysis, map recognition      |
| **AI Agent**             | Claude API integration, decision-making, context management |
| **Game Logic**           | Combat strategies, dungeon navigation, puzzle solving       |
| **Memory System**        | Progress tracking, learned strategies, statistics           |
| **Reasoning Engine**     | High-level planning, chain-of-thought reflection (SIMA 2)   |
| **Multimodal Interface** | Visual goal understanding, sketch parsing (SIMA 2)          |
| **Strategy Bank**        | Self-improvement via learned strategies (SIMA 2)            |

### SIMA 2 Integration (New!)

Inspired by Google DeepMind's SIMA 2, this agent is evolving to "play, reason, and learn":

1. **Reasoning**: Uses Chain-of-Thought to plan complex sequences before acting.
2. **Multimodal**: Can understand goals from images (e.g., "Go to this location" from a screenshot).
3. **Self-Improvement**: Learns from its own gameplay, storing successful strategies in a `StrategyBank`.

## 💻 Usage Examples

### Basic Usage

```bash
# Play with default settings
zelda-ai play

# Play with custom configuration
zelda-ai play --config my_config.json

# Run for limited time (testing)
zelda-ai play --max-iterations 50
```

### Python API

```python
from claude_plays_zelda.core import Config, GameLoop

# Configure
config = Config(
    anthropic_api_key="your-key",
    emulator_path="/path/to/snes9x",
    rom_path="/path/to/zelda.smc",
    decision_interval=2.0
)

# Run
game_loop = GameLoop(config)
game_loop.run()
```

### Advanced Control

```python
from claude_plays_zelda.core import GameOrchestrator

orchestrator = GameOrchestrator(config)
orchestrator.start()

while orchestrator.is_running:
    frame_data = orchestrator.process_frame()
    decision = orchestrator.make_decision(frame_data)
    orchestrator.execute_action(decision)

orchestrator.stop()
```

## 🎯 What the AI Can Do

✅ **Exploration**

- Navigate the overworld
- Enter buildings and caves
- Track visited locations
- Discover secrets

✅ **Combat**

- Engage enemies strategically
- Learn attack patterns
- Use different weapons
- Manage health

✅ **Progression**

- Complete dungeons
- Solve puzzles
- Talk to NPCs
- Collect items

✅ **Learning**

- Remember strategies
- Learn from deaths
- Track progress
- Optimize gameplay

## 📊 Monitoring & Statistics

```bash
# View agent statistics
zelda-ai show-stats

# Output:
# 📊 Agent Statistics:
#   Total Decisions: 1,234
#   Success Rate: 78.5%
#   Deaths: 12
#   Enemies Defeated: 145
#   Items Collected: 23
#   Rooms Explored: 67
```

Statistics are saved in `data/saves/agent_memory.json` and automatically updated.

## 🔒 Legal Notice

### ⚠️ ROM Requirements

**You MUST legally own The Legend of Zelda (1986) to use this software.**

Legal ways to obtain a ROM:

- Dump from your own NES cartridge
- Purchase digital copy (e.g., Nintendo Switch Online)
- Extract from legally purchased compilation

**This project does NOT provide ROMs.**

### Fair Use

This is an educational and research project demonstrating:

- AI decision-making in complex environments
- Computer vision applications in gaming
- Reinforcement learning concepts

_The Legend of Zelda is a registered trademark of Nintendo. This project is not affiliated with or endorsed by Nintendo._

## 🤝 Contributing

Contributions welcome! Please see our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black claude_plays_zelda/
isort claude_plays_zelda/

# Type checking
mypy claude_plays_zelda/
```

## 🐛 Common Issues

| Issue                 | Solution                                     |
| --------------------- | -------------------------------------------- |
| "Window not found"    | Check `WINDOW_TITLE` matches emulator window |
| "API key invalid"     | Verify key in `.env` file                    |
| "Tesseract not found" | Install Tesseract OCR and add to PATH        |
| Screen capture fails  | Grant screen recording permissions (macOS)   |

📖 See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed troubleshooting.

## 📚 Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Installation and configuration
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Detailed technical overview
- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[API Documentation](docs/)** - Code reference (coming soon)
- **[Architecture](docs/ARCHITECTURE.md)** - System design (coming soon)
- **[Contributing](CONTRIBUTING.md)** - Development guide (coming soon)

## 🚧 Roadmap

- [ ] Web dashboard for real-time monitoring
- [x] Twitch streaming integration
- [ ] Deep learning models for improved vision
- [ ] Support for other Zelda games
- [ ] SIMA 2: Full implementation of Reasoning Engine
- [ ] SIMA 2: Full implementation of Multimodal Interface
- [ ] SIMA 2: Full implementation of Self-Improvement Loop
- [ ] Support for other Zelda games
- [ ] Reinforcement learning optimizations
- [ ] Voice commentary generation
- [ ] Speedrun mode

## 🙏 Acknowledgments

- Inspired by [ClaudePlaysPokemonStarter](https://github.com/davidhershey/ClaudePlaysPokemonStarter)
- Powered by [Anthropic Claude API](https://www.anthropic.com/)
- Built with [Snes9x](https://www.snes9x.com/) emulator
- Computer vision: OpenCV, Tesseract OCR

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/clduab11/claude-plays-zelda/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/clduab11/claude-plays-zelda/discussions)
- 📧 **Contact**: See GitHub profile

## ⭐ Star History

If you find this project interesting, please give it a star! It helps others discover it.

---

<div align="center">

**Made with ❤️ and AI**

[Report Bug](https://github.com/clduab11/claude-plays-zelda/issues) · [Request Feature](https://github.com/clduab11/claude-plays-zelda/issues) · [Documentation](SETUP_GUIDE.md)

</div>
