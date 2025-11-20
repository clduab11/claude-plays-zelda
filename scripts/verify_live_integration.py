"""
Verification script for Live API integration.
Tests ClaudeClient with real Anthropic API calls.
WARNING: This script consumes API credits.
"""

import sys
import os
import base64
from dotenv import load_dotenv
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.agent.claude_client import ClaudeClient

    # Load environment variables
    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment or .env file.")
        logger.info("Please create a .env file with your API key.")
        sys.exit(1)

    logger.info("Successfully loaded API key.")

    # Initialize Client
    model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
    client = ClaudeClient(api_key=api_key, model=model)
    logger.info(f"Initialized ClaudeClient with model: {model}")

    # Test 1: Simple Text Action
    logger.info("Test 1: Requesting simple text action...")
    game_state = "Link is standing in the middle of a field. There is a Octorok to the right."
    action = client.get_action(game_state)
    logger.info(f"Received action: {action}")
    
    if not action or action == "wait":
        logger.warning("Received 'wait' or empty action. This might be valid but check logic.")
    else:
        logger.info("Test 1 Passed: Received valid action.")

    # Test 2: Multimodal Action (if image provided)
    # We'll create a dummy small red pixel image for testing
    logger.info("Test 2: Requesting multimodal action...")
    # Valid 1x1 red pixel PNG
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    action_mm = client.get_action(game_state, image_data=base64_image)
    logger.info(f"Received multimodal action: {action_mm}")

    if not action_mm or action_mm == "wait":
        logger.warning("Received 'wait' or empty action for multimodal test.")
    else:
        logger.info("Test 2 Passed: Received valid multimodal action.")

    print("LIVE VERIFICATION PASSED")

except Exception as e:
    logger.error(f"Verification failed: {e}")
    print("LIVE VERIFICATION FAILED")
    sys.exit(1)
