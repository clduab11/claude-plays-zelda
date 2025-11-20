"""
Verification script for NES Transition.
Checks configuration, InputController, and ActionPlanner for NES compatibility.
"""

import sys
import os
import yaml
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.emulator.input_controller import InputController, GameButton
    from src.agent.action_planner import ActionPlanner, ActionType
    from src.cv.game_state_analyzer import GameStateAnalyzer

    logger.info("Starting NES Transition Verification...")

    # 1. Verify Config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    assert config["emulator"]["type"] == "fceux", "Emulator type must be fceux"
    assert config["emulator"]["rom_path"] == "zelda_nes.nes", "ROM path must be zelda_nes.nes"
    assert config["cv"]["screen_capture"]["resolution"] == [256, 240], "Resolution must be 256x240"
    assert config["claude"]["model"] == "${CLAUDE_MODEL}", "Claude model must use env var"
    logger.info("Config verification passed.")

    # 2. Verify InputController (NES Buttons)
    # Check that SNES buttons are NOT in GameButton (or at least not used)
    # We removed them from the enum definition in the file, so accessing them should fail or they shouldn't exist
    # But since it's an Enum, we can iterate
    
    buttons = [b.name for b in GameButton]
    logger.info(f"Available buttons: {buttons}")
    
    forbidden_buttons = ["X", "Y", "L", "R"]
    for btn in forbidden_buttons:
        assert btn not in buttons, f"Button {btn} should not be present for NES"
    
    assert "A" in buttons and "B" in buttons, "A and B buttons must be present"
    logger.info("InputController verification passed.")

    # 3. Verify ActionPlanner (No DASH)
    actions = [a.name for a in ActionType]
    logger.info(f"Available actions: {actions}")
    
    assert "DASH" not in actions, "DASH action should be removed"
    logger.info("ActionPlanner verification passed.")

    print("VERIFICATION PASSED")

except Exception as e:
    logger.error(f"Verification failed: {e}")
    print("VERIFICATION FAILED")
    sys.exit(1)
