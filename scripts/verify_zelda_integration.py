"""
Verification script for Advanced Agent integration.
Tests press_buttons, summarize_history, and multimodal ClaudeClient.
"""

import sys
import os
from unittest.mock import MagicMock
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.agent.action_planner import ActionPlanner, ActionType
    from src.agent.context_manager import ContextManager
    from src.agent.claude_client import ClaudeClient
    from src.emulator.input_controller import InputController, GameButton

    logger.info("Successfully imported components.")

    # 1. Test press_buttons in ActionPlanner
    mock_input = MagicMock(spec=InputController)
    planner = ActionPlanner(mock_input)
    
    # Test parsing
    # Manually create action as before
    from src.agent.action_planner import Action
    action = Action(ActionType.PRESS_BUTTONS, parameters={"buttons": ["A", "B"]}, duration=0.5)
    planner.execute_action(action)
    
    mock_input.combo_move.assert_called_with([GameButton.A, GameButton.B], [0.5, 0.5])
    logger.info("ActionPlanner press_buttons test passed.")

    # 2. Test summarize_history in ContextManager
    ctx_mgr = ContextManager(max_history=20)
    for i in range(15):
        ctx_mgr.add_entry(i, f"State {i}", f"Action {i}", f"Result {i}", importance=1)
    
    # Mark one as important
    ctx_mgr.mark_important(index=-2, importance=5) # Action 13
    
    logger.info(f"History length before summary: {len(ctx_mgr.history)}")
    ctx_mgr.summarize_history()
    logger.info(f"History length after summary: {len(ctx_mgr.history)}")
    
    assert len(ctx_mgr.history) == 10
    assert "Summarized" in ctx_mgr.summary
    logger.info("ContextManager summarize_history test passed.")

    # 3. Test ClaudeClient with image
    # We'll mock the Anthropic client
    mock_anthropic = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="ACTION: wait")]
    mock_anthropic.messages.create.return_value = mock_response
    
    client = ClaudeClient(api_key="dummy")
    client.client = mock_anthropic
    
    client.get_action("Game State", image_data="base64data")
    
    # Verify call arguments
    # Verify call arguments
    if not mock_anthropic.messages.create.called:
        logger.error("messages.create was not called")
        raise Exception("messages.create was not called")
        
    call_args = mock_anthropic.messages.create.call_args
    logger.info(f"Call args: {call_args}")
    
    if 'messages' not in call_args.kwargs:
        logger.error("messages arg not found in kwargs")
        raise Exception("messages arg not found")
        
    messages = call_args.kwargs['messages']
    content = messages[0]['content']
    logger.info(f"Content: {content}")
    
    assert isinstance(content, list), f"Content should be list, got {type(content)}"
    assert content[0]['type'] == 'image', f"First item type should be image, got {content[0].get('type')}"
    assert content[0]['source']['data'] == 'base64data', "Base64 data mismatch"
    logger.info("ClaudeClient multimodal test passed.")

    print("VERIFICATION PASSED")

except Exception as e:
    logger.error(f"Verification failed: {e}")
    print("VERIFICATION FAILED")
    sys.exit(1)
