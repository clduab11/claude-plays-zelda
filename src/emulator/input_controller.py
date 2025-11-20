"""Controller for injecting input into the emulator."""

import time
from enum import Enum
from typing import List, Optional
from loguru import logger

# Lazy import for GUI dependencies (to support headless testing)
try:
    import pyautogui
    import keyboard
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False


class GameButton(Enum):
    """SNES controller buttons."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    A = "a"      # Sword
    B = "b"      # Item
    START = "return"
    SELECT = "shift"


class InputController:
    """Handles input injection into the emulator."""

    def __init__(self, window_name: str = "Snes9x"):
        """
        Initialize the input controller.

        Args:
            window_name: Name of the emulator window
        """
        self.window_name = window_name
        if GUI_AVAILABLE:
            pyautogui.PAUSE = 0.05  # Small pause between actions
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort

    def press_button(self, button: GameButton, duration: float = 0.1) -> None:
        """
        Press a button for a specified duration.

        Args:
            button: The button to press
            duration: How long to hold the button (seconds)
        """
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, simulating button press")
            time.sleep(duration)
            return
        
        try:
            key = button.value
            keyboard.press(key)
            time.sleep(duration)
            keyboard.release(key)
            logger.debug(f"Pressed {button.name} for {duration}s")
        except Exception as e:
            logger.error(f"Failed to press button {button.name}: {e}")

    def press_buttons(self, buttons: List[GameButton], duration: float = 0.1) -> None:
        """
        Press multiple buttons simultaneously.

        Args:
            buttons: List of buttons to press
            duration: How long to hold the buttons (seconds)
        """
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, simulating button press")
            time.sleep(duration)
            return
        
        try:
            keys = [btn.value for btn in buttons]
            for key in keys:
                keyboard.press(key)
            time.sleep(duration)
            for key in keys:
                keyboard.release(key)
            button_names = [btn.name for btn in buttons]
            logger.debug(f"Pressed {button_names} for {duration}s")
        except Exception as e:
            logger.error(f"Failed to press buttons: {e}")

    def tap_button(self, button: GameButton) -> None:
        """
        Quickly tap a button.

        Args:
            button: The button to tap
        """
        self.press_button(button, duration=0.05)

    def hold_button(self, button: GameButton, duration: float) -> None:
        """
        Hold a button for a longer duration.

        Args:
            button: The button to hold
            duration: How long to hold (seconds)
        """
        self.press_button(button, duration=duration)

    def move_direction(self, direction: GameButton, duration: float = 0.2) -> None:
        """
        Move in a direction.

        Args:
            direction: Direction to move (UP, DOWN, LEFT, RIGHT)
            duration: How long to move (seconds)
        """
        if direction not in [GameButton.UP, GameButton.DOWN, GameButton.LEFT, GameButton.RIGHT]:
            logger.warning(f"{direction} is not a valid direction")
            return
        self.press_button(direction, duration)

    def attack(self) -> None:
        """Perform an attack (A button - Sword)."""
        self.tap_button(GameButton.A)

    def use_item(self) -> None:
        """Use equipped item (B button)."""
        self.tap_button(GameButton.B)

    def open_menu(self) -> None:
        """Open the game menu (START button)."""
        self.tap_button(GameButton.START)

    # dash_attack removed as it is not present in NES Zelda

    def combo_move(self, buttons: List[GameButton], delays: Optional[List[float]] = None) -> None:
        """
        Execute a combo of button presses.

        Args:
            buttons: Sequence of buttons to press
            delays: Optional delays between button presses
        """
        if delays is None:
            delays = [0.1] * len(buttons)
        
        for button, delay in zip(buttons, delays):
            self.tap_button(button)
            time.sleep(delay)

    def wait(self, duration: float) -> None:
        """
        Wait for a specified duration without input.

        Args:
            duration: Time to wait (seconds)
        """
        time.sleep(duration)

    def release_all(self) -> None:
        """Release all currently pressed buttons."""
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, simulating release")
            return
        
        try:
            for button in GameButton:
                keyboard.release(button.value)
            logger.debug("Released all buttons")
        except Exception as e:
            logger.error(f"Failed to release all buttons: {e}")
