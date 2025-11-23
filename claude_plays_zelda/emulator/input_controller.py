"""Input controller for sending keypresses to the emulator."""

import time
from enum import Enum
from typing import List, Optional, Dict
import pyautogui
from pynput.keyboard import Controller, Key
from loguru import logger


class NESButton(Enum):
    """NES controller button mappings."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    A = "a"
    B = "b"
    START = "start"
    SELECT = "select"


class InputController:
    """Controls input to the emulator via keyboard simulation."""

    def __init__(
        self,
        key_map: Optional[Dict[NESButton, str]] = None,
        default_press_duration: float = 0.1,
        default_delay_between_inputs: float = 0.05,
    ):
        """
        Initialize input controller.

        Args:
            key_map: Custom key mapping for NES buttons
            default_press_duration: Default duration to hold keys (seconds)
            default_delay_between_inputs: Default delay between consecutive inputs
        """
        self.keyboard = Controller()
        self.default_press_duration = default_press_duration
        self.default_delay = default_delay_between_inputs

        # Default key mapping for Mesen
        self.key_map = key_map or {
            NESButton.UP: "up",
            NESButton.DOWN: "down",
            NESButton.LEFT: "left",
            NESButton.RIGHT: "right",
            NESButton.A: "x",      # Mesen default for A
            NESButton.B: "z",      # Mesen default for B
            NESButton.START: "enter", # Mesen default for Start
            NESButton.SELECT: "shiftright", # Mesen default for Select
        }

        self.currently_pressed: set = set()
        logger.info("InputController initialized for NES")

    def press_button(
        self, button: NESButton, duration: Optional[float] = None, delay_after: Optional[float] = None
    ) -> None:
        """
        Press a button for a specified duration.

        Args:
            button: NES button to press
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
        self, buttons: List[NESButton], duration: Optional[float] = None, delay_after: Optional[float] = None
    ) -> None:
        """
        Press multiple buttons simultaneously (e.g., diagonal movement).

        Args:
            buttons: List of NES buttons to press together
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
        sequence: List[NESButton],
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
        self, direction: str, duration: float = 0.2
    ) -> None:
        """
        Move Link in a direction.

        Args:
            direction: Direction to move (up, down, left, right)
            duration: How long to move
        """
        direction_map = {
            "up": NESButton.UP,
            "down": NESButton.DOWN,
            "left": NESButton.LEFT,
            "right": NESButton.RIGHT,
        }

        direction_button = direction_map.get(direction.lower())
        if not direction_button:
            logger.warning(f"Invalid direction: {direction}")
            return

        self.press_button(direction_button, duration, 0.05)

    def attack(self) -> None:
        """
        Perform an attack with Link's sword (A button in NES Zelda usually, or B? 
        Actually in NES Zelda: A is Sword, B is Item. Wait, let me double check.
        Standard: A = Sword, B = Item. 
        """
        # In NES Zelda: A is Sword, B is Item.
        self.press_button(NESButton.A, duration=0.1)
        logger.debug("Attack executed")

    def use_item(self) -> None:
        """Use the currently selected secondary item (B button)."""
        self.press_button(NESButton.B, duration=0.1)
        logger.debug("Item used")

    def open_menu(self) -> None:
        """Open the game menu (Start)."""
        self.press_button(NESButton.START, duration=0.1, delay_after=0.5)
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

    def focus_window(self, window_title: str = "Mesen") -> bool:
        """
        Attempt to focus the emulator window.

        Args:
            window_title: Title of window to focus
        """
        try:
            import pygetwindow as gw

            # Mesen window title often contains the ROM name, so we search for substring
            windows = gw.getAllWindows()
            target_window = None
            
            for window in windows:
                if window_title.lower() in window.title.lower():
                    target_window = window
                    break
            
            if target_window:
                target_window.activate()
                time.sleep(0.2)
                logger.info(f"Focused window: {target_window.title}")
                return True
            else:
                logger.warning(f"Window containing '{window_title}' not found")
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
