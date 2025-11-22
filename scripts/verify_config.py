import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from claude_plays_zelda.core.config import Config

def test_config_loading():
    print("Testing config loading...")
    
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"ERROR: {config_path} not found.")
        return

    try:
        cfg = Config.from_file(config_path)
        print("Config loaded successfully.")
        print(f"Emulator Path: {cfg.emulator_path}")
        print(f"ROM Path: {cfg.rom_path}")
        
        if cfg.emulator_path and "Mesen" in cfg.emulator_path:
            print("SUCCESS: Emulator path matches expectation.")
        else:
            print("FAILURE: Emulator path does not match expectation.")
            
    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_loading()
