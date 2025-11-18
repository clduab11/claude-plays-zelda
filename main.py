"""Main application entry point for Claude Plays Zelda."""

import os
import time
import yaml
from dotenv import load_dotenv
from loguru import logger
import sys

from src.emulator import EmulatorInterface, InputController, ScreenCapture
from src.cv import GameStateAnalyzer
from src.agent import ClaudeClient, ContextManager, ActionPlanner, MemorySystem
from src.game import CombatAI, PuzzleSolver, Navigator
from src.streaming import Dashboard, StatsTracker


class ClaudeZeldaAI:
    """Main AI controller for playing Zelda."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the AI system.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        logger.info("Initializing Claude Plays Zelda AI...")
        
        # Emulator
        self.emulator = EmulatorInterface(
            executable_path=self.config['emulator']['executable_path'],
            rom_path=self.config['emulator']['rom_path'],
            save_state_dir=self.config['emulator']['save_state_dir']
        )
        self.input_controller = InputController(
            window_name=self.config['emulator']['window_name']
        )
        self.screen_capture = ScreenCapture(
            window_name=self.config['emulator']['window_name'],
            target_resolution=tuple(self.config['cv']['screen_capture']['resolution'])
        )
        
        # Computer Vision
        self.game_state_analyzer = GameStateAnalyzer()
        
        # AI Agent
        api_key = os.getenv('ANTHROPIC_API_KEY', self.config['claude']['api_key'])
        self.claude_client = ClaudeClient(
            api_key=api_key,
            model=self.config['claude']['model'],
            max_tokens=self.config['claude']['max_tokens'],
            temperature=self.config['claude']['temperature']
        )
        
        self.context_manager = ContextManager(
            max_history=self.config['agent']['memory']['max_history'],
            max_tokens=self.config['agent']['context']['max_tokens'],
            summarize_threshold=self.config['agent']['context']['summarize_threshold']
        )
        
        self.action_planner = ActionPlanner(self.input_controller)
        
        self.memory_system = MemorySystem(
            persistence_file=self.config['agent']['memory']['persistence_file']
        )
        
        # Game Logic
        self.combat_ai = CombatAI(
            aggressive_mode=self.config['game']['combat']['aggressive_mode'],
            dodge_priority=self.config['game']['combat']['dodge_priority']
        )
        
        self.puzzle_solver = PuzzleSolver()
        self.navigator = Navigator(
            pathfinding_algorithm=self.config['game']['navigation']['pathfinding_algorithm'],
            revisit_threshold=self.config['game']['navigation']['revisit_threshold']
        )
        
        # Streaming
        self.dashboard = None
        self.stats_tracker = StatsTracker(
            update_interval=self.config['streaming']['stats']['update_interval']
        )
        
        if self.config['streaming']['enabled']:
            self.dashboard = Dashboard(
                host=self.config['streaming']['dashboard']['host'],
                port=self.config['streaming']['dashboard']['port'],
                enable_cors=self.config['streaming']['dashboard']['enable_cors']
            )
        
        self.running = False
        self.decision_interval = self.config['agent']['decision_interval']

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config['logging']
        
        # Remove default handler
        logger.remove()
        
        # Add console handler
        if log_config['console']:
            logger.add(
                sys.stderr,
                level=log_config['level'],
                format=log_config['format']
            )
        
        # Add file handler
        logger.add(
            log_config['file'],
            level=log_config['level'],
            format=log_config['format'],
            rotation="10 MB"
        )

    def start(self):
        """Start the AI system."""
        logger.info("Starting Claude Plays Zelda AI")
        
        # Start dashboard if enabled
        if self.dashboard:
            self.dashboard.start()
        
        # Start emulator
        if not self.emulator.start():
            logger.error("Failed to start emulator")
            return
        
        # Load memory
        self.memory_system.load()
        
        # Start stats tracking
        self.stats_tracker.start_session()
        
        self.running = True
        logger.info("AI system started successfully")
        
        # Main game loop
        try:
            self.game_loop()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
        finally:
            self.stop()

    def game_loop(self):
        """Main game loop."""
        logger.info("Entering main game loop")
        
        last_decision_time = 0
        
        while self.running:
            current_time = time.time()
            
            # Capture screen
            screen = self.screen_capture.capture_screen()
            if screen is None:
                logger.warning("Failed to capture screen")
                time.sleep(0.5)
                continue
            
            # Analyze game state
            game_state = self.game_state_analyzer.analyze(screen)
            state_summary = self.game_state_analyzer.get_state_summary(game_state)
            
            # Update dashboard
            if self.dashboard:
                self.dashboard.update_state({
                    "health": game_state.health,
                    "max_health": game_state.max_health,
                    "rupees": game_state.rupees,
                    "location": game_state.location.region if game_state.location else "Unknown",
                    "enemies": len(game_state.enemies_visible),
                    "items": len(game_state.items_visible),
                })
            
            # Make decision at intervals
            if current_time - last_decision_time >= self.decision_interval:
                decision_start = time.time()
                
                # Get context
                context = self.context_manager.get_context(num_recent=10)
                memory_context = self.memory_system.export_for_context()
                full_context = f"{context}\n\n{memory_context}"
                
                # Get action from Claude
                action_response = self.claude_client.get_action(state_summary, full_context)
                parsed_action = self.claude_client.parse_action_response(action_response)
                
                decision_time = time.time() - decision_start
                self.stats_tracker.record_decision_time(decision_time)
                
                logger.info(f"Action: {parsed_action['action']} - {parsed_action['reason']}")
                
                # Execute action
                action = self.action_planner.parse_action(parsed_action['action'])
                if action:
                    success = self.action_planner.execute_action(action)
                    self.stats_tracker.record_action(success)
                    
                    # Update context
                    self.context_manager.add_entry(
                        timestamp=current_time,
                        game_state=state_summary,
                        action_taken=parsed_action['action'],
                        result="success" if success else "failed",
                        importance=1
                    )
                    
                    # Update dashboard
                    if self.dashboard:
                        self.dashboard.log_action(parsed_action['action'])
                
                last_decision_time = current_time
            
            # Update statistics
            if self.stats_tracker.should_update() and self.dashboard:
                stats = self.stats_tracker.get_current_stats()
                self.dashboard.update_stats(stats)
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

    def stop(self):
        """Stop the AI system."""
        logger.info("Stopping Claude Plays Zelda AI")
        
        self.running = False
        
        # Save memory
        self.memory_system.save()
        
        # End stats tracking
        self.stats_tracker.end_session()
        
        # Save stats
        self.stats_tracker.save_to_file("stats.json")
        
        # Stop emulator
        self.emulator.stop()
        
        # Stop dashboard
        if self.dashboard:
            self.dashboard.stop()
        
        logger.info("AI system stopped")


def main():
    """Main entry point."""
    logger.info("Claude Plays The Legend of Zelda")
    logger.info("=" * 50)
    
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        logger.info("Please set it in .env file or environment")
        return
    
    # Initialize and start AI
    ai = ClaudeZeldaAI()
    ai.start()


if __name__ == "__main__":
    main()
