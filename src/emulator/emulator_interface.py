"""Main interface for controlling the SNES9x emulator."""

import subprocess
import time
import psutil
from typing import Optional
from loguru import logger


class EmulatorInterface:
    """Manages the SNES9x emulator process and game state."""

    def __init__(self, executable_path: str, rom_path: str, save_state_dir: str = "save_states"):
        """
        Initialize the emulator interface.

        Args:
            executable_path: Path to SNES9x executable
            rom_path: Path to the game ROM file
            save_state_dir: Directory for save states
        """
        self.executable_path = executable_path
        self.rom_path = rom_path
        self.save_state_dir = save_state_dir
        self.process: Optional[subprocess.Popen] = None
        self._running = False

    def start(self) -> bool:
        """
        Start the emulator process.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("Emulator is already running")
            return True

        try:
            logger.info(f"Starting emulator with ROM: {self.rom_path}")
            self.process = subprocess.Popen(
                [self.executable_path, self.rom_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for emulator to initialize
            
            if self.process.poll() is None:
                self._running = True
                logger.info("Emulator started successfully")
                return True
            else:
                logger.error("Emulator process exited immediately")
                return False
        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            return False

    def stop(self) -> None:
        """Stop the emulator process."""
        if not self._running or self.process is None:
            return

        try:
            logger.info("Stopping emulator")
            self.process.terminate()
            self.process.wait(timeout=5)
            self._running = False
            logger.info("Emulator stopped")
        except subprocess.TimeoutExpired:
            logger.warning("Emulator did not terminate gracefully, forcing shutdown")
            self.process.kill()
            self._running = False
        except Exception as e:
            logger.error(f"Error stopping emulator: {e}")

    def is_running(self) -> bool:
        """
        Check if the emulator is currently running.

        Returns:
            bool: True if running, False otherwise
        """
        if not self._running or self.process is None:
            return False
        return self.process.poll() is None

    def save_state(self, slot: int = 0) -> bool:
        """
        Save the current game state.

        Args:
            slot: Save slot number (0-9)

        Returns:
            bool: True if saved successfully
        """
        if not self.is_running():
            logger.error("Cannot save state: emulator not running")
            return False

        try:
            logger.info(f"Saving state to slot {slot}")
            # SNES9x uses F1-F10 for save states (F1 = slot 0)
            # This is a placeholder - actual implementation would use keyboard input
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def load_state(self, slot: int = 0) -> bool:
        """
        Load a saved game state.

        Args:
            slot: Save slot number (0-9)

        Returns:
            bool: True if loaded successfully
        """
        if not self.is_running():
            logger.error("Cannot load state: emulator not running")
            return False

        try:
            logger.info(f"Loading state from slot {slot}")
            # SNES9x uses Shift+F1-F10 for load states
            # This is a placeholder - actual implementation would use keyboard input
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def reset(self) -> bool:
        """
        Reset the game.

        Returns:
            bool: True if reset successfully
        """
        if not self.is_running():
            logger.error("Cannot reset: emulator not running")
            return False

        try:
            logger.info("Resetting game")
            # Implement reset logic
            return True
        except Exception as e:
            logger.error(f"Failed to reset game: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
