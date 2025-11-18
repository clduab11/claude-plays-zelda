"""Input controller for sending keypresses to the emulator."""

import time
from enum import Enum
from typing import List, Optional, Dict
import pyautogui

from loguru import logger


class SNESButton(Enum):
    """SNES controller button mappings."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    A = "a"
    B = "b"
    X = "x"
    Y = "y"
    L = "l"
    R = "r"
    START = "return"
    SELECT = "rshift"


class InputController:
    """Controls input to the emulator via keyboard simulation."""

    def __init__(
        self,
        key_map: Optional[Dict[SNESButton, str]] = None,
        default_press_duration: float = 0.1,
        default_delay_between_inputs: float = 0.05,
    ):
        """
        Initialize input controller.

        Args:
            key_map: Custom key mapping for SNES buttons
            default_press_duration: Default duration to hold keys (seconds)
            default_delay_between_inputs: Default delay between consecutive inputs
        """
        self.keyboard = Controller()
        self.default_press_duration = default_press_duration
        self.default_delay = default_delay_between_inputs

        # Default key mapping (can be customized)
        self.key_map = key_map or {
            SNESButton.UP: "up",
            SNESButton.DOWN: "down",
            SNESButton.LEFT: "left",
            SNESButton.RIGHT: "right",
            SNESButton.A: "x",  # Common Snes9x mapping
            SNESButton.B: "z",
            SNESButton.X: "s",
            SNESButton.Y: "a",
            SNESButton.L: "d",
            SNESButton.R: "c",
            SNESButton.START: "return",
            SNESButton.SELECT: "rshift",
        }

        self.currently_pressed: set = set()
        logger.info("InputController initialized")

    def press_button(
        self, button: SNESButton, duration: Optional[float] = None, delay_after: Optional[float] = None
    ) -> None:
        """
        Press a button for a specified duration.

        Args:
            button: SNES button to press
            duration: How long to hold the button (None = default)
            delay_after: Delay after releasing button (None = default)
        """
        try:
            key = self.key_map.get(button)
            if not key:
                logger.warning(f"No key mapping for button: {button}")
                return

            duration = duration or self.default_press_duration
            delay_after = delay_after if delay_after is not None else self.default_delay

            # Press and hold
            pyautogui.keyDown(key)
            self.currently_pressed.add(key)
            logger.debug(f"Pressed {button.name} ({key}) for {duration}s")

            time.sleep(duration)

            # Release
            pyautogui.keyUp(key)
            self.currently_pressed.discard(key)

            # Delay before next input
            time.sleep(delay_after)

        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")

    def press_buttons_simultaneously(
        self, buttons: List[SNESButton], duration: Optional[float] = None, delay_after: Optional[float] = None
    ) -> None:
        """
        Press multiple buttons simultaneously (e.g., diagonal movement).

        Args:
            buttons: List of SNES buttons to press together
            duration: How long to hold the buttons
            delay_after: Delay after releasing buttons
        """
        try:
            duration = duration or self.default_press_duration
            delay_after = delay_after if delay_after is not None else self.default_delay

            keys = [self.key_map.get(btn) for btn in buttons if self.key_map.get(btn)]

            # Press all keys
            for key in keys:
                pyautogui.keyDown(key)
                self.currently_pressed.add(key)

            logger.debug(f"Pressed buttons simultaneously: {[btn.name for btn in buttons]}")

            time.sleep(duration)

            # Release all keys
            for key in keys:
                pyautogui.keyUp(key)
                self.currently_pressed.discard(key)

            time.sleep(delay_after)

        except Exception as e:
            logger.error(f"Error pressing buttons simultaneously: {e}")

    def press_sequence(
        self,
        sequence: List[SNESButton],
        duration_per_button: Optional[float] = None,
        delay_between: Optional[float] = None,
    ) -> None:
        """
        Press a sequence of buttons in order.

        Args:
            sequence: List of buttons to press in sequence
            duration_per_button: Duration for each button press
            delay_between: Delay between button presses
        """
        logger.debug(f"Executing button sequence: {[btn.name for btn in sequence]}")
        for button in sequence:
            self.press_button(button, duration_per_button, delay_between)

    def move_direction(
        self, direction: str, duration: float = 0.2, run: bool = False
    ) -> None:
        """
        Move Link in a direction (with optional running).

        Args:
            direction: Direction to move (up, down, left, right)
            duration: How long to move
            run: Whether to hold B button to run
        """
        direction_map = {
            "up": SNESButton.UP,
            "down": SNESButton.DOWN,
            "left": SNESButton.LEFT,
            "right": SNESButton.RIGHT,
        }

        direction_button = direction_map.get(direction.lower())
        if not direction_button:
            logger.warning(f"Invalid direction: {direction}")
            return

        if run:
            # Hold B and direction to run
            self.press_buttons_simultaneously([SNESButton.B, direction_button], duration, 0.05)
        else:
            self.press_button(direction_button, duration, 0.05)

    def attack(self, charge: bool = False) -> None:
        """
        Perform an attack with Link's sword.

        Args:
            charge: Whether to charge the sword (hold longer)
        """
        duration = 1.5 if charge else 0.1
        self.press_button(SNESButton.Y, duration=duration)
        logger.debug(f"Attack executed (charged={charge})")

    def use_item(self) -> None:
        """Use the currently selected secondary item (A button)."""
        self.press_button(SNESButton.A, duration=0.1)
        logger.debug("Item used")

    def open_menu(self) -> None:
        """Open the game menu."""
        self.press_button(SNESButton.START, duration=0.1, delay_after=0.5)
        logger.debug("Menu opened")

    def release_all(self) -> None:
        """Release all currently pressed keys."""
        try:
            for key in list(self.currently_pressed):
                pyautogui.keyUp(key)
            self.currently_pressed.clear()
            logger.debug("All keys released")
        except Exception as e:
            logger.error(f"Error releasing keys: {e}")

    def wait(self, duration: float) -> None:
        """
        Wait for a specified duration without pressing any buttons.

        Args:
            duration: Time to wait in seconds
        """
        time.sleep(duration)

    def focus_window(self, window_title: str = "Snes9x") -> bool:
        """
        Attempt to focus the emulator window.

        Args:
            window_title: Title of window to focus

        Returns:
            True if window was focused successfully
        """
        try:
            import pygetwindow as gw

            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                windows[0].activate()
                time.sleep(0.2)
                logger.info(f"Focused window: {window_title}")
                return True
            else:
                logger.warning(f"Window not found: {window_title}")
                return False
        except ImportError:
            logger.warning("pygetwindow not available, cannot focus window")
            return False
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return False

    def cleanup(self):
        """Clean up and release all pressed keys."""
        self.release_all()
        logger.info("InputController cleaned up")
