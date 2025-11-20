"""
Example: Using the SIMA 2-inspired Pixels-to-Actions Agent

This script demonstrates how to use the new VLM-based agent
to play Zelda directly from pixel inputs.
"""

import asyncio
import os
from PIL import Image
from loguru import logger

# Import SIMA agent
from src.sima import PixelsToActionsAgent


async def demo_basic_usage():
    """Basic usage example."""
    print("=" * 80)
    print("SIMA Agent - Basic Usage Demo")
    print("=" * 80)

    # Initialize agent
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    agent = PixelsToActionsAgent(
        api_key=api_key,
        model="claude-3-5-sonnet-20241022",
        enable_critic=True
    )

    # Set objective
    agent.set_objective("Explore the starting area and find the first dungeon")

    print("\n[1] Agent initialized")
    print(f"   Model: {agent.model}")
    print(f"   Critic: {'enabled' if agent.memory_critic.enable_critic else 'disabled'}")

    # Simulate game loop (with mock frames for demo)
    print("\n[2] Simulating game loop...")

    # In real usage, you would capture actual game frames
    # For demo, we'll use a mock frame
    mock_frame = Image.new('RGB', (256, 224), color='green')

    print("\n[3] Making first decision...")
    decision = await agent.decide_action(
        current_frame=mock_frame,
        health=3,
        max_health=6,
        metadata={
            "location": "Overworld - Starting area",
            "rupees": 0
        }
    )

    print("\n[4] Decision received:")
    print(f"   Observation: {decision.visual_observation[:100]}...")
    print(f"   Threat Level: {decision.threat_assessment.value}")
    print(f"   Strategic Goal: {decision.strategic_goal}")
    print(f"   Tactic: {decision.immediate_tactic}")
    print(f"   Controller: {decision.controller_output.buttons} ({decision.controller_output.duration_ms}ms)")
    print(f"   Confidence: {decision.confidence:.2f}")

    # Simulate a few more decisions
    print("\n[5] Making 3 more decisions...")
    for i in range(3):
        decision = await agent.decide_action(
            current_frame=mock_frame,
            health=3 - i,  # Simulate health loss
            max_health=6
        )
        print(f"   Decision {i+2}: {decision.immediate_tactic[:50]}... (confidence: {decision.confidence:.2f})")

    # Get statistics
    print("\n[6] Agent statistics:")
    stats = agent.get_statistics()
    print(f"   Total decisions: {stats['total_decisions']}")
    print(f"   Avg decision time: {stats['avg_decision_time_ms']:.1f}ms")
    print(f"   Temporal buffer: {stats['temporal_buffer']['current_frames']}/{stats['temporal_buffer']['buffer_size']} frames")

    # Cleanup
    await agent.close()
    print("\n[7] Agent closed")
    print("\n" + "=" * 80)


async def demo_death_detection():
    """Demonstrate death detection and learning."""
    print("\n" + "=" * 80)
    print("SIMA Agent - Death Detection & Learning Demo")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    agent = PixelsToActionsAgent(
        api_key=api_key,
        enable_critic=True
    )

    # Simulate gameplay leading to death
    print("\n[1] Simulating risky gameplay...")
    mock_frame = Image.new('RGB', (256, 224), color='red')

    for i in range(5):
        await agent.decide_action(
            current_frame=mock_frame,
            health=1,  # Critical health
            max_health=6,
            metadata={"location": "Dungeon Level 1", "enemies_nearby": True}
        )

    # Trigger death analysis
    print("\n[2] Death detected! Analyzing failure...")
    await agent.on_death_detected(context="Dungeon Level 1 - Enemy room")

    # Check lessons learned
    print("\n[3] Lessons learned:")
    stats = agent.get_statistics()
    memory_stats = stats['memory']
    print(f"   Total failures analyzed: {memory_stats['total_failures']}")
    print(f"   Lessons in memory: {memory_stats['lessons_in_memory']}")

    if memory_stats['lessons_in_memory'] > 0:
        # Export lessons
        agent.export_lessons("demo_lessons.txt")
        print("\n[4] Lessons exported to demo_lessons.txt")

    await agent.close()
    print("\n" + "=" * 80)


async def demo_with_adapter():
    """Demonstrate using the adapter for legacy integration."""
    print("\n" + "=" * 80)
    print("SIMA Agent - Adapter Demo (Legacy Compatibility)")
    print("=" * 80)

    from src.agent.sima_adapter import SimaAgentAdapter
    import numpy as np

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    # Create adapter
    adapter = SimaAgentAdapter(
        api_key=api_key,
        enable_async=True
    )

    print("\n[1] Adapter initialized (compatible with legacy code)")

    # Use adapter with numpy arrays (like legacy code)
    mock_screen = np.zeros((224, 256, 3), dtype=np.uint8)
    mock_screen[:, :, 1] = 128  # Green channel

    game_state = {
        "health": 4,
        "max_health": 6,
        "rupees": 10,
        "location": "Overworld"
    }

    print("\n[2] Calling adapter.get_action() (sync interface)...")
    response = adapter.get_action(mock_screen, game_state)

    print("\n[3] Response (legacy format):")
    print(f"   Action: {response['action']}")
    print(f"   Reason: {response['reason']}")
    print(f"   Confidence: {response['confidence']:.2f}")

    # Parse action (legacy compatibility)
    parsed = adapter.parse_action_response(response)
    print(f"\n[4] Parsed action: {parsed['action']}")

    adapter.close()
    print("\n[5] Adapter closed")
    print("\n" + "=" * 80)


def main():
    """Run all demos."""
    print("\n🎮 SIMA 2-Inspired Agent Demos")
    print("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        print("\nRunning demos in mock mode...\n")

    # Run demos
    asyncio.run(demo_basic_usage())

    # Uncomment to run other demos
    # asyncio.run(demo_death_detection())
    # asyncio.run(demo_with_adapter())

    print("\n✅ Demos complete!")
    print("\nNext steps:")
    print("1. Integrate with your game loop")
    print("2. Enable critic for self-improvement")
    print("3. Review thought process in logs/agent_thought_process.log")
    print("4. Check learned lessons in data/knowledge_base/lessons.json")


if __name__ == "__main__":
    main()
