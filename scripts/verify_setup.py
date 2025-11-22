import os
import sys
import time
import yaml
import subprocess
import pyautogui
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def verify_setup():
    print("Loading configuration...")
    config = load_config()
    
    emulator_path = config['emulator']['executable_path']
    rom_path = config['emulator']['rom_path']
    window_name = config['emulator']['window_name']
    
    print(f"Emulator: {emulator_path}")
    print(f"ROM: {rom_path}")
    
    if not os.path.exists(emulator_path):
        print(f"ERROR: Emulator not found at {emulator_path}")
        return
        
    if not os.path.exists(rom_path):
        print(f"ERROR: ROM not found at {rom_path}")
        return
        
    print("Launching emulator...")
    try:
        # Launch Mesen
        process = subprocess.Popen([emulator_path, rom_path])
        
        print("Waiting for emulator to start (5s)...")
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is not None:
            print("ERROR: Emulator process terminated unexpectedly.")
            return
            
        print(f"Attempting to focus window: {window_name}")
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(window_name)
            if windows:
                windows[0].activate()
                print("Window focused.")
            else:
                print(f"WARNING: Window '{window_name}' not found. Title might be different.")
                all_titles = gw.getAllTitles()
                print(f"Available windows: {[t for t in all_titles if t]}")
        except ImportError:
            print("pygetwindow not installed, skipping focus check.")
            
        # Take a screenshot
        print("Taking screenshot...")
        screenshot_path = "verification_screenshot.png"
        pyautogui.screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        print("Closing emulator...")
        process.terminate()
        
        print("Verification complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify_setup()
