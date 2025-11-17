"""Main orchestrator that coordinates all subsystems."""

import time
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from claude_plays_zelda.core.config import Config
from claude_plays_zelda.emulator import EmulatorManager, ScreenCapture, InputController
from claude_plays_zelda.vision import GameOCR, ObjectDetector, GameStateDetector, MapAnalyzer
from claude_plays_zelda.ai import ClaudeAgent, ContextManager, ActionPlanner, AgentMemory
from claude_plays_zelda.game import CombatAI, DungeonNavigator, PuzzleSolver, ZeldaKnowledge


class GameOrchestrator:
    """Orchestrates all components of the AI agent system."""

    def __init__(self, config: Config):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.is_running = False
        self.session_start_time: Optional[datetime] = None

        # Initialize all subsystems
        logger.info("Initializing subsystems...")

        # Emulator
        self.emulator = EmulatorManager(
            emulator_path=config.emulator_path,
            rom_path=config.rom_path,
            window_title=config.window_title,
        )

        # Vision
        self.ocr = GameOCR() if config.enable_ocr else None
        self.object_detector = ObjectDetector() if config.enable_object_detection else None
        self.state_detector = GameStateDetector()
        self.map_analyzer = MapAnalyzer()

        # AI
        self.agent = ClaudeAgent(
            api_key=config.anthropic_api_key,
            model=config.claude_model,
            max_tokens=config.max_tokens,
        )

        # Game Logic
        self.combat_ai = CombatAI()
        self.dungeon_navigator = DungeonNavigator()
        self.puzzle_solver = PuzzleSolver()
        self.knowledge = ZeldaKnowledge()

        # State tracking
        self.previous_frame = None
        self.decision_count = 0
        self.last_decision_time = 0

        logger.info("GameOrchestrator initialized successfully")

    def start(self, auto_start_emulator: bool = True):
        """
        Start the AI agent system.

        Args:
            auto_start_emulator: Whether to auto-start the emulator
        """
        logger.info("Starting Claude Plays Zelda...")

        if auto_start_emulator:
            if not self.emulator.start_emulator():
                logger.error("Failed to start emulator")
                return

        # Load agent memory if exists
        if self.config.memory_file.exists():
            self.agent.memory.load_from_file(str(self.config.memory_file))

        self.is_running = True
        self.session_start_time = datetime.now()

        # Set initial objective
        self.agent.set_objective("Explore Hyrule and progress through the game")

        logger.info("System started successfully")

    def stop(self):
        """Stop the AI agent system."""
        logger.info("Stopping Claude Plays Zelda...")

        self.is_running = False

        # Save agent memory
        self.agent.memory.save_to_file(str(self.config.memory_file))

        # Cleanup
        self.emulator.cleanup()

        logger.info("System stopped")

    def process_frame(self) -> Dict[str, Any]:
        """
        Process a single frame and extract information.

        Returns:
            Dictionary with processed frame data
        """
        try:
            # Capture frame
            frame = self.emulator.get_current_frame()
            if frame is None:
                return {}

            # Extract game state
            game_state = self.state_detector.get_full_game_state(frame)

            # Detect objects if enabled
            observations = {}
            if self.object_detector:
                observations = self.object_detector.detect_all_objects(frame)

            # Check for dialogue
            dialogue = ""
            if self.ocr:
                dialogue = self.ocr.extract_dialogue(frame)

            # Map analysis
            room_changed = self.map_analyzer.has_room_changed(frame)
            if room_changed:
                room_id = self.map_analyzer.capture_room(frame)
                logger.info(f"Entered new room: {room_id}")

            processed_data = {
                "frame": frame,
                "game_state": game_state,
                "observations": observations,
                "dialogue": dialogue,
                "room_changed": room_changed,
                "timestamp": datetime.now().isoformat(),
            }

            self.previous_frame = frame
            return processed_data

        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {}

    def make_decision(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a decision based on current game state.

        Args:
            frame_data: Processed frame data

        Returns:
            Decision dictionary
        """
        try:
            game_state = frame_data.get("game_state", {})
            observations = frame_data.get("observations", {})

            # Get recent actions
            recent_actions = self.agent.context_manager.get_recent_actions()

            # Check if in combat
            enemies = observations.get("enemies", [])
            if enemies:
                # Use combat AI for tactical decisions
                combat_analysis = self.combat_ai.analyze_combat_situation(enemies, game_state)

                if combat_analysis["can_engage"]:
                    decision = self.combat_ai.get_combat_action(enemies, game_state)
                    decision["reasoning"] = f"Combat: {combat_analysis['recommended_strategy']}"
                    return decision

            # Check if in dungeon
            if self.dungeon_navigator.current_dungeon:
                # Use dungeon navigation
                decision = self.dungeon_navigator.suggest_navigation_action(
                    game_state, observations
                )
                decision["reasoning"] = "Dungeon exploration"
                return decision

            # Use Claude AI for high-level decisions
            decision = self.agent.decide_action(
                game_state=game_state,
                observations=observations,
                recent_actions=recent_actions,
            )

            self.decision_count += 1
            return decision

        except Exception as e:
            logger.error(f"Error making decision: {e}")
            return {
                "action": "wait",
                "parameters": {"duration": 1.0},
                "reasoning": f"Error: {str(e)}",
            }

    def execute_action(self, decision: Dict[str, Any]) -> bool:
        """
        Execute an action decided by the AI.

        Args:
            decision: Decision dictionary

        Returns:
            True if action executed successfully
        """
        try:
            action = decision.get("action", "wait")
            parameters = decision.get("parameters", {})
            reasoning = decision.get("reasoning", "")

            logger.info(f"Executing: {action} - {reasoning}")

            # Record action
            self.agent.context_manager.add_action(f"{action}({parameters})")

            # Execute via emulator
            self.emulator.execute_action(action, **parameters)

            return True

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return False

    def evaluate_outcome(self, frame_data_before: Dict[str, Any], frame_data_after: Dict[str, Any]):
        """
        Evaluate the outcome of an action.

        Args:
            frame_data_before: Frame data before action
            frame_data_after: Frame data after action
        """
        try:
            # Compare game states
            state_before = frame_data_before.get("game_state", {})
            state_after = frame_data_after.get("game_state", {})

            hearts_before = state_before.get("hearts", {}).get("current_hearts", 0)
            hearts_after = state_after.get("hearts", {}).get("current_hearts", 0)

            rupees_before = state_before.get("rupees", 0)
            rupees_after = state_after.get("rupees", 0)

            # Determine success/failure
            success = True
            result = {}

            if hearts_after < hearts_before:
                success = False
                result["damage_taken"] = hearts_before - hearts_after
                feedback = f"Took {result['damage_taken']} damage"
            elif hearts_after == 0:
                success = False
                result["death"] = True
                feedback = "Link died"
            elif rupees_after > rupees_before:
                result["rupees_gained"] = rupees_after - rupees_before
                feedback = f"Collected {result['rupees_gained']} rupees"
            else:
                feedback = "Action completed"

            # Update agent
            self.agent.update_from_outcome(success, result, feedback)

        except Exception as e:
            logger.error(f"Error evaluating outcome: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the system."""
        uptime = None
        if self.session_start_time:
            uptime = (datetime.now() - self.session_start_time).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "decision_count": self.decision_count,
            "emulator_status": self.emulator.get_diagnostics(),
            "agent_stats": self.agent.get_statistics(),
            "combat_stats": self.combat_ai.get_combat_stats(),
            "dungeon_progress": self.dungeon_navigator.get_dungeon_progress(),
        }

    def save_checkpoint(self, slot: int = 0):
        """
        Save a game checkpoint.

        Args:
            slot: Save slot number
        """
        try:
            # Save emulator state
            self.emulator.save_state(slot)

            # Save agent memory
            self.agent.memory.save_to_file(str(self.config.memory_file))

            logger.info(f"Checkpoint saved to slot {slot}")

        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def load_checkpoint(self, slot: int = 0):
        """
        Load a game checkpoint.

        Args:
            slot: Save slot number
        """
        try:
            # Load emulator state
            self.emulator.load_state(slot)

            # Load agent memory
            if self.config.memory_file.exists():
                self.agent.memory.load_from_file(str(self.config.memory_file))

            logger.info(f"Checkpoint loaded from slot {slot}")

        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
