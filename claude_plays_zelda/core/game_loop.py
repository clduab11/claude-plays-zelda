"""Main game loop for running the AI agent."""

import time
from typing import Optional
from loguru import logger

from claude_plays_zelda.core.config import Config
from claude_plays_zelda.core.orchestrator import GameOrchestrator
from claude_plays_zelda.emulator.input_controller import SNESButton


from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()

class GameLoop:
    """Main game loop that runs the AI agent."""

    def __init__(self, config: Config):
        """
        Initialize game loop.

        Args:
            config: Configuration object
        """
        self.config = config
        self.orchestrator = GameOrchestrator(config)
        self.is_paused = False
        self.frame_count = 0
        self.last_save_time = time.time()
        self.state = GameState.MENU
        self.consecutive_hud_frames = 0

        logger.info("GameLoop initialized")

    def run(self, max_iterations: Optional[int] = None):
        """
        Run the main game loop.

        Args:
            max_iterations: Maximum iterations (None = infinite)
        """
        logger.info("Starting game loop...")

        # Start orchestrator
        self.orchestrator.start(auto_start_emulator=True)

        iteration = 0
        last_decision_time = 0

        try:
            while self.orchestrator.is_running:
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"Reached max iterations: {max_iterations}")
                    break

                # Check if paused
                if self.is_paused:
                    time.sleep(0.1)
                    continue

                # Process frame
                frame_data = self.orchestrator.process_frame()
                if not frame_data:
                    time.sleep(0.1)
                    continue

                self.frame_count += 1
                
                # Update State Machine
                is_title = frame_data.get("is_title_screen", False)
                is_in_game = frame_data.get("is_in_game", False)
                
                if is_in_game:
                    self.consecutive_hud_frames += 1
                else:
                    self.consecutive_hud_frames = 0
                    
                # Transition Logic
                if self.state == GameState.MENU:
                    if self.consecutive_hud_frames > 5: # Require 5 stable frames of HUD
                        logger.info("HUD detected consistently. Transitioning to PLAYING state.")
                        self.state = GameState.PLAYING
                        
                elif self.state == GameState.PLAYING:
                    if is_title:
                        logger.info("Title screen detected. Transitioning to MENU state.")
                        self.state = GameState.MENU
                        self.consecutive_hud_frames = 0

                # Make decision at intervals
                current_time = time.time()
                if current_time - last_decision_time >= self.config.decision_interval:
                    
                    if self.state == GameState.MENU:
                        # MENU LOGIC: Hardcoded navigation
                        logger.info("State: MENU - Executing start sequence...")
                        self.orchestrator.emulator.input_controller.press_button(SNESButton.START)
                        # Wait a bit longer in menu
                        last_decision_time = time.time() + 1.0 
                        continue
                        
                    elif self.state == GameState.PLAYING:
                        # GAMEPLAY LOGIC: AI Agent
                        decision = self.orchestrator.make_decision(frame_data)

                        # Execute action
                        frame_data_before = frame_data
                        self.orchestrator.execute_action(decision)

                        # Wait for action to complete
                        time.sleep(self.config.action_delay)

                        # Evaluate outcome
                        frame_data_after = self.orchestrator.process_frame()
                        self.orchestrator.evaluate_outcome(frame_data_before, frame_data_after)

                        last_decision_time = current_time

                # Auto-save periodically
                if current_time - self.last_save_time >= self.config.auto_save_interval:
                    self.orchestrator.save_checkpoint(slot=0)
                    self.last_save_time = current_time

                # Small delay to control frame rate
                time.sleep(1.0 / self.config.frame_rate)

                iteration += 1

        except KeyboardInterrupt:
            logger.info("Game loop interrupted by user")
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
        finally:
            self.stop()

    def pause(self):
        """Pause the game loop."""
        self.is_paused = True
        logger.info("Game loop paused")

    def resume(self):
        """Resume the game loop."""
        self.is_paused = False
        logger.info("Game loop resumed")

    def stop(self):
        """Stop the game loop."""
        logger.info("Stopping game loop...")
        self.orchestrator.stop()
        logger.info("Game loop stopped")

    def get_statistics(self):
        """Get game loop statistics."""
        return {
            "frame_count": self.frame_count,
            "is_paused": self.is_paused,
            "orchestrator_status": self.orchestrator.get_status(),
        }
