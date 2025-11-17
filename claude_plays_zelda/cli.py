"""Command-line interface for claude-plays-zelda."""

import click
from pathlib import Path
from loguru import logger

from claude_plays_zelda.core.config import Config
from claude_plays_zelda.core.game_loop import GameLoop


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Claude Plays Zelda - AI agent for playing Legend of Zelda games."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--emulator-path",
    "-e",
    type=click.Path(exists=True),
    help="Path to SNES emulator executable",
)
@click.option(
    "--rom-path",
    "-r",
    type=click.Path(exists=True),
    help="Path to Zelda ROM file",
)
@click.option(
    "--max-iterations",
    "-i",
    type=int,
    default=None,
    help="Maximum number of iterations to run",
)
def play(config, emulator_path, rom_path, max_iterations):
    """Start playing Zelda with the AI agent."""
    try:
        # Load configuration
        if config:
            cfg = Config.from_file(config)
        else:
            cfg = Config()

        # Override with CLI arguments
        if emulator_path:
            cfg.emulator_path = emulator_path
        if rom_path:
            cfg.rom_path = rom_path

        # Validate required settings
        if not cfg.emulator_path or not Path(cfg.emulator_path).exists():
            click.echo("Error: Emulator path not found. Use --emulator-path or set in config.")
            return

        if not cfg.rom_path or not Path(cfg.rom_path).exists():
            click.echo("Error: ROM path not found. Use --rom-path or set in config.")
            return

        # Create and run game loop
        click.echo("🎮 Starting Claude Plays Zelda...")
        game_loop = GameLoop(cfg)
        game_loop.run(max_iterations=max_iterations)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Error running game")


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="config.json",
    help="Output configuration file path",
)
def init_config(output):
    """Initialize a configuration file with default values."""
    try:
        # Create config with defaults (will prompt for API key via environment)
        click.echo("Creating configuration file...")

        # Create a template config
        template = {
            "anthropic_api_key": "your-api-key-here",
            "emulator_path": "/path/to/snes9x",
            "rom_path": "/path/to/zelda.smc",
            "claude_model": "claude-3-5-sonnet-20241022",
            "window_title": "Snes9x",
            "action_delay": 0.5,
            "decision_interval": 2.0,
            "log_level": "INFO",
        }

        import json

        with open(output, "w") as f:
            json.dump(template, f, indent=2)

        click.echo(f"✅ Configuration template created: {output}")
        click.echo("Edit the file and add your API key and paths.")

    except Exception as e:
        click.echo(f"Error creating config: {e}", err=True)


@main.command()
@click.option(
    "--memory-file",
    "-m",
    type=click.Path(exists=True),
    default="data/saves/agent_memory.json",
    help="Path to agent memory file",
)
def show_stats(memory_file):
    """Show statistics from agent memory."""
    try:
        from claude_plays_zelda.ai.memory import AgentMemory

        memory = AgentMemory()
        memory.load_from_file(memory_file)

        stats = memory.get_statistics()

        click.echo("\n📊 Agent Statistics:")
        click.echo(f"  Total Decisions: {stats['total_decisions']}")
        click.echo(f"  Success Rate: {stats['success_rate']:.1%}")
        click.echo(f"  Deaths: {stats['deaths']}")
        click.echo(f"  Enemies Defeated: {stats['enemies_defeated']}")
        click.echo(f"  Items Collected: {stats['items_collected']}")

        click.echo("\n" + memory.summarize())

    except FileNotFoundError:
        click.echo("No memory file found. Play some games first!")
    except Exception as e:
        click.echo(f"Error loading stats: {e}", err=True)


@main.command()
def check_dependencies():
    """Check if all required dependencies are installed."""
    click.echo("Checking dependencies...\n")

    dependencies = {
        "anthropic": "Anthropic API client",
        "cv2": "OpenCV (computer vision)",
        "PIL": "Pillow (image processing)",
        "pytesseract": "Tesseract OCR",
        "numpy": "NumPy (numerical computing)",
        "mss": "Screen capture",
        "pyautogui": "Input control",
        "flask": "Web dashboard",
        "loguru": "Logging",
    }

    all_ok = True

    for module, description in dependencies.items():
        try:
            __import__(module)
            click.echo(f"✅ {module:20s} - {description}")
        except ImportError:
            click.echo(f"❌ {module:20s} - {description} (NOT INSTALLED)")
            all_ok = False

    if all_ok:
        click.echo("\n✅ All dependencies are installed!")
    else:
        click.echo("\n❌ Some dependencies are missing. Run: pip install -r requirements.txt")


@main.command()
def version():
    """Show version information."""
    click.echo("claude-plays-zelda v0.1.0")
    click.echo("An AI agent for playing Legend of Zelda: A Link to the Past")


if __name__ == "__main__":
    main()
