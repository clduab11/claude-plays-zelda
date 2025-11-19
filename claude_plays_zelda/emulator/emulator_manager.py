"""Emulator manager for coordinating screen capture and input control."""

import subprocess
import time
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from claude_plays_zelda.emulator.screen_capture import ScreenCapture
from claude_plays_zelda.emulator.input_controller import InputController


class EmulatorManager:
    """Manages the emulator process and coordinates capture/input systems."""

    def __init__(
        self,
        emulator_path: Optional[str] = None,
        rom_path: Optional[str] = None,
        window_title: str = "Snes9x",
        auto_start: bool = False,
    ):
        """
        Initialize emulator manager.

        Args:
            emulator_path: Path to the SNES emulator executable
            rom_path: Path to the Zelda ROM file
            window_title: Expected window title of the emulator
            auto_start: Whether to automatically start the emulator
        """
        self.emulator_path = emulator_path
        self.rom_path = rom_path
        self.window_title = window_title
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False

        # Initialize subsystems
        self.screen_capture = ScreenCapture(window_title=window_title)
        self.input_controller = InputController()

        logger.info("EmulatorManager initialized")

        if auto_start and emulator_path and rom_path:
            self.start_emulator()

    def start_emulator(
        self, emulator_path: Optional[str] = None, rom_path: Optional[str] = None
    ) -> bool:
        """
        Start the emulator with the specified ROM.

        Args:
            emulator_path: Path to emulator (overrides constructor value)
            rom_path: Path to ROM (overrides constructor value)

        Returns:
            True if emulator started successfully
        """
        try:
            emu_path = emulator_path or self.emulator_path
            rom = rom_path or self.rom_path

            if not emu_path or not rom:
                logger.error("Emulator path and ROM path must be specified")
                return False

            # Validate paths
            if not Path(emu_path).exists():
                logger.error(f"Emulator not found: {emu_path}")
                return False

            if not Path(rom).exists():
                logger.error(f"ROM not found: {rom}")
                return False

            # Start emulator process
            logger.info(f"Starting emulator: {emu_path} with ROM: {rom}")
            self.process = subprocess.Popen(
                [emu_path, rom],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for window to appear
            time.sleep(2)

            # Try to focus the window
            self.input_controller.focus_window(self.window_title)

            # Verify capture is working
            time.sleep(1)
            frame = self.screen_capture.capture_frame()
            if frame is None:
                logger.warning("Unable to capture frame, emulator may not be ready")

            self.is_running = True
            logger.info("Emulator started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting emulator: {e}")
            return False

    def stop_emulator(self) -> bool:
        """
        Stop the emulator process.

        Returns:
            True if emulator stopped successfully
        """
        try:
            if self.process:
                logger.info("Stopping emulator...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Emulator didn't terminate, killing process")
                    self.process.kill()
                    self.process.wait()

                self.process = None
                self.is_running = False
                logger.info("Emulator stopped")
                return True
            else:
                logger.warning("No emulator process to stop")
                return False

        except Exception as e:
            logger.error(f"Error stopping emulator: {e}")
            return False

    def is_emulator_running(self) -> bool:
        """
        Check if the emulator is currently running.

        Returns:
            True if emulator process is active
        """
        if self.process:
            return self.process.poll() is None
        return False

    def save_state(self, slot: int = 0) -> None:
        """
        Save game state to a slot.

        Args:
            slot: Save slot number (0-9)
        """
        try:
            # Snes9x uses F1-F10 for save states
            if 0 <= slot <= 9:
                key = f"F{slot + 1}"
                import pyautogui
                pyautogui.press(key)
                logger.info(f"Saved state to slot {slot}")
            else:
                logger.warning(f"Invalid save slot: {slot}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def load_state(self, slot: int = 0) -> None:
        """
        Load game state from a slot.

        Args:
            slot: Save slot number (0-9)
        """
        try:
            # Snes9x uses Shift+F1-F10 for loading states
            if 0 <= slot <= 9:
                key = f"F{slot + 1}"
                import pyautogui
                pyautogui.hotkey('shift', key)
                logger.info(f"Loaded state from slot {slot}")
            else:
                logger.warning(f"Invalid save slot: {slot}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def get_current_frame(self):
        """Get the current game frame."""
        return self.screen_capture.capture_frame()

    def execute_action(self, action: str, **kwargs) -> None:
        """
        Execute a game action via the input controller.

        Args:
            action: Action name (e.g., 'move', 'attack', 'use_item')
            **kwargs: Additional parameters for the action
        """
        try:
            action_map = {
                "move": self.input_controller.move_direction,
                "attack": self.input_controller.attack,
                "use_item": self.input_controller.use_item,
                "open_menu": self.input_controller.open_menu,
                "wait": self.input_controller.wait,
            }

            if action in action_map:
                action_map[action](**kwargs)
            else:
                logger.warning(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get diagnostic information about the emulator state.

        Returns:
            Dictionary with diagnostic information
        """
        return {
            "is_running": self.is_emulator_running(),
            "window_title": self.window_title,
            "capture_fps": self.screen_capture.get_fps(),
            "frame_count": self.screen_capture.frame_count,
            "emulator_path": self.emulator_path,
            "rom_path": self.rom_path,
        }

    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up EmulatorManager...")
        self.input_controller.cleanup()
        self.screen_capture.cleanup()
        self.stop_emulator()
        logger.info("EmulatorManager cleanup complete")
