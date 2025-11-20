# 🚀 Setup Guide - Claude Plays Zelda

Complete step-by-step guide to get Claude playing Zelda on your system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB free space

### 2. Required Accounts

- **Anthropic API Key**: Sign up at [console.anthropic.com](https://console.anthropic.com/)
  - New users get free credits
  - API key looks like: `sk-ant-...`

### 3. Game Requirements

- **SNES Emulator**: Snes9x (recommended) or ZSNES
- **Legal ROM**: You must own The Legend of Zelda: A Link to the Past

## Installation Steps

### Step 1: Install Python

Check if Python is installed:

```bash
python --version
# or
python3 --version
```

If not installed, download from [python.org](https://www.python.org/downloads/)

**Important**: On Windows, check "Add Python to PATH" during installation.

### Step 2: Install Git (Optional but Recommended)

Download from [git-scm.com](https://git-scm.com/)

### Step 3: Clone or Download Repository

**With Git:**
```bash
git clone https://github.com/clduab11/claude-plays-zelda.git
cd claude-plays-zelda
```

**Without Git:**
- Download ZIP from GitHub
- Extract to a folder
- Open terminal in that folder

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 5: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take a few minutes.

### Step 6: Install System Dependencies

#### Install Tesseract OCR

**macOS (using Homebrew):**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows:**
1. Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer
3. Note installation path (usually `C:\Program Files\Tesseract-OCR`)
4. Add to PATH or set in code

**Verify Installation:**
```bash
tesseract --version
```

#### Install SNES Emulator

**Option 1: Snes9x (Recommended)**

**macOS:**
```bash
brew install snes9x
```

**Ubuntu/Debian:**
```bash
sudo apt-get install snes9x-gtk
```

**Windows:**
1. Download from [snes9x.com](https://www.snes9x.com/)
2. Extract to a folder (e.g., `C:\Program Files\Snes9x`)
3. Note the path to `snes9x.exe`

**Option 2: ZSNES**

Similar process, but Snes9x is more actively maintained.

### Step 7: Install Package

```bash
pip install -e .
```

This installs the `zelda-ai` command.

## Configuration

### Step 1: Get Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

### Step 2: Create Environment File

```bash
cp .env.example .env
```

### Step 3: Edit `.env` File

Open `.env` in a text editor and fill in:

```bash
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Required: Path to your emulator
# Windows example:
EMULATOR_PATH=C:\\Program Files\\Snes9x\\snes9x-x64.exe
# macOS example:
EMULATOR_PATH=/Applications/Snes9x.app/Contents/MacOS/Snes9x
# Linux example:
EMULATOR_PATH=/usr/bin/snes9x-gtk

# Required: Path to your ROM
# Windows example:
ROM_PATH=C:\\Games\\ROMs\\zelda_alttp.smc
# macOS/Linux example:
ROM_PATH=/Users/yourname/Games/zelda_alttp.smc

# Optional: Adjust these if needed
WINDOW_TITLE=Snes9x
DECISION_INTERVAL=2.0
LOG_LEVEL=INFO
```

**Important Notes:**
- Use double backslashes (`\\`) in Windows paths
- Ensure file paths exist and are correct
- Keep your API key secret (never commit to Git)

### Step 4: Verify Configuration

```bash
zelda-ai check-dependencies
```

You should see all green checkmarks ✅

## First Run

### Step 1: Test Emulator Connection

First, manually start your emulator with the Zelda ROM to ensure it works.

### Step 2: Run the AI Agent

**Basic Run:**
```bash
zelda-ai play
```

**With Specific Paths:**
```bash
zelda-ai play \
  --emulator-path "/path/to/snes9x" \
  --rom-path "/path/to/zelda.smc"
```

**With Limited Iterations (for testing):**
```bash
zelda-ai play --max-iterations 10
```

### Step 3: Monitor Output

You should see:
```
🎮 Starting Claude Plays Zelda...
[INFO] EmulatorManager initialized
[INFO] Starting emulator: /path/to/snes9x
[INFO] Claude Agent initialized
[INFO] Starting game loop...
```

### Step 4: Observe the AI Playing

- The emulator window will open
- The AI will start making decisions
- You'll see logs of actions in the terminal
- Screenshots are saved to `data/screenshots/`

### Step 5: Stop the Agent

Press `Ctrl+C` to stop gracefully.

## Troubleshooting

### Issue: "API key not found"

**Solution:**
- Check `.env` file exists
- Ensure `ANTHROPIC_API_KEY` is set
- Verify no spaces around the `=` sign
- Make sure API key is valid

### Issue: "Emulator path not found"

**Solution:**
- Check file path is correct
- Use absolute paths, not relative
- On Windows, use double backslashes (`\\`)
- Verify emulator executable exists at that path

### Issue: "Window not found" during screen capture

**Solution:**
- Ensure emulator is running
- Check window title matches `WINDOW_TITLE` in config
- Try: `--window-title "exact window title"`
- Don't minimize the emulator window

**To find exact window title:**
- **macOS**: Check Activity Monitor
- **Windows**: Check Task Manager → Details
- **Linux**: Use `wmctrl -l` or `xdotool search --name snes9x`

### Issue: "Tesseract not found"

**Solution:**
- Verify installation: `tesseract --version`
- Add Tesseract to PATH:
  - **Windows**: Add `C:\Program Files\Tesseract-OCR` to system PATH
  - **macOS/Linux**: Usually automatic with package manager
- Restart terminal after PATH changes

### Issue: "Screen capture not working" (macOS)

**Solution:**
- Grant screen recording permissions:
  1. System Preferences → Security & Privacy → Privacy
  2. Screen Recording
  3. Add Terminal or your IDE
  4. Restart application

### Issue: "Permission denied" on Linux

**Solution:**
```bash
chmod +x /path/to/snes9x
```

### Issue: "Import errors" or "Module not found"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
pip install -e .
```

### Issue: "API rate limit exceeded"

**Solution:**
- Increase `DECISION_INTERVAL` in `.env` (e.g., 5.0 seconds)
- Check your Anthropic dashboard for rate limits
- Consider upgrading your API plan

### Issue: Emulator controls not working

**Solution:**
- Ensure emulator window has focus
- Check emulator key bindings match the default SNES layout
- Try running emulator manually first to verify controls
- On Linux, may need X11 forwarding or additional permissions

### Issue: High CPU usage

**Solution:**
- Reduce `FRAME_RATE` in config (default 10 fps)
- Increase `DECISION_INTERVAL` (fewer decisions per second)
- Close other applications
- Use a lighter-weight emulator

### Issue: "ROM not loading"

**Solution:**
- Verify ROM file is not corrupted
- Try loading ROM manually in emulator first
- Check ROM file extension (`.smc` or `.sfc`)
- Ensure ROM is USA version (PAL may have differences)

## Getting Help

If you're still having issues:

1. Check the [README](README.md) for more information
2. Review logs in `data/logs/zelda_ai.log`
3. Search [GitHub Issues](https://github.com/clduab11/claude-plays-zelda/issues)
4. Open a new issue with:
   - Your OS and Python version
   - Full error message
   - Relevant log excerpts
   - Steps to reproduce

## Next Steps

Once everything is working:

1. **Experiment with settings** in `.env`
2. **Monitor the agent's progress** with `zelda-ai show-stats`
3. **Save checkpoints** - agent auto-saves every 5 minutes
4. **Review logs** in `data/logs/` for debugging
5. **Customize behavior** by modifying the code

## Performance Tips

1. **Reduce API calls**: Increase `DECISION_INTERVAL`
2. **Faster decisions**: Use `claude-3-haiku` model (cheaper, faster)
3. **Better decisions**: Use `claude-3-opus` model (more expensive, smarter)
4. **Save bandwidth**: Disable unused features (OCR, object detection)
5. **Local processing**: Future versions may support local ML models

## What the AI Can Do

Currently, the AI can:
- ✅ Navigate Hyrule
- ✅ Engage in combat
- ✅ Talk to NPCs
- ✅ Collect items
- ✅ Explore dungeons
- ✅ Solve simple puzzles
- ✅ Track progress and learn

The AI is still learning and may:
- ❌ Get stuck in corners
- ❌ Miss secrets
- ❌ Die to difficult enemies
- ❌ Struggle with complex puzzles

This is expected! The AI improves over time through its memory system.

## Advanced Configuration

For power users, see:
- `claude_plays_zelda/core/config.py` - All config options
- `claude_plays_zelda/ai/claude_agent.py` - AI behavior
- `claude_plays_zelda/game/` - Game-specific logic

---

**Happy Gaming! May the Triforce be with you! ⚔️🛡️✨**
