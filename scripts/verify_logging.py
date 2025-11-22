import sys
import os
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from claude_plays_zelda.core.config import Config
from claude_plays_zelda.core.orchestrator import GameOrchestrator

def test_logging():
    print("Testing logging...")
    
    # Mock config
    config = Config()
    # Set paths to known existing files to avoid init errors
    config.emulator_path = r"C:\ai-playground\nes-emulator-test\Mesen.exe"
    config.rom_path = r"C:\ai-playground\nes-emulator-test\roms\Legend of Zelda, The (USA) (Rev 1).nes"
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Initialize orchestrator (this sets up the logger)
    try:
        print("Initializing orchestrator...")
        # We wrap in try/except because other components might fail init (e.g. CV) but we only care about logger
        orchestrator = GameOrchestrator(config)
        
        # Manually log a thought to test the sink
        thought_msg = (
            f"\n{'='*60}\n"
            f"🧠 THOUGHT:\nTesting the thought logger.\n\n"
            f"⚡ ACTION: test_action\n"
            f"🔧 PARAMS: {{'test': True}}\n"
            f"{'='*60}"
        )
        logger.bind(is_thought=True).info(thought_msg)
        
        print("Logged a thought.")
        
        # Check if file exists
        if os.path.exists("logs/thoughts.log"):
            print("logs/thoughts.log created.")
            with open("logs/thoughts.log", "r", encoding="utf-8") as f:
                content = f.read()
                print("Content preview:")
                print(content)
        else:
            print("ERROR: logs/thoughts.log not found.")
            
    except Exception as e:
        print(f"Error during test: {e}")
        # Even if orchestrator init failed, if it failed AFTER logger setup, we might still be good?
        # But logger setup is at the beginning of init.

if __name__ == "__main__":
    test_logging()
