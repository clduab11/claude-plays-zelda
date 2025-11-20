"""
Verification script for SIMA 2 scaffolds.
Checks if new components can be imported and instantiated.
"""

import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.agent.reasoning_engine import ReasoningEngine
    from src.agent.multimodal_interface import MultimodalInterface
    from src.learning.strategy_bank import StrategyBank
    from src.agent.claude_client import ClaudeClient

    logger.info("Successfully imported SIMA 2 components.")

    # Mock Claude Client
    class MockClaudeClient:
        pass

    claude = MockClaudeClient()

    # Instantiate Reasoning Engine
    reasoning = ReasoningEngine(claude)
    logger.info("ReasoningEngine instantiated.")
    
    # Instantiate Multimodal Interface
    multimodal = MultimodalInterface(claude)
    logger.info("MultimodalInterface instantiated.")

    # Instantiate Strategy Bank
    strategy_bank = StrategyBank("data/test_strategies.json")
    logger.info("StrategyBank instantiated.")
    
    # Test Strategy Bank save/load
    strategy_bank.save_strategy("test_situation", "test_action", "test_outcome", 0.9)
    logger.info("StrategyBank save test passed.")

    print("VERIFICATION PASSED")

except Exception as e:
    logger.error(f"Verification failed: {e}")
    print("VERIFICATION FAILED")
    sys.exit(1)
