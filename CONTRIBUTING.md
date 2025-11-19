# Contributing to Claude Plays Zelda

Thank you for your interest in contributing to Claude Plays Zelda! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and constructive. We welcome contributors of all skill levels.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/claude-plays-zelda.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black claude_plays_zelda/
isort claude_plays_zelda/

# Type checking
mypy claude_plays_zelda/
```

## Project Structure

```
claude_plays_zelda/
├── ai/          # AI agent and decision-making
├── core/        # Core orchestration
├── emulator/    # Emulator integration
├── game/        # Game-specific logic
├── vision/      # Computer vision
└── utils/       # Utilities
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions/classes
- Keep functions focused and small
- Use meaningful variable names

### Example

```python
def process_game_state(frame: np.ndarray, detector: GameStateDetector) -> Dict[str, Any]:
    """
    Process a game frame to extract state information.

    Args:
        frame: Game frame as numpy array
        detector: Initialized game state detector

    Returns:
        Dictionary containing game state information

    Raises:
        ValueError: If frame is invalid
    """
    if frame is None or frame.size == 0:
        raise ValueError("Invalid frame provided")

    state = detector.get_full_game_state(frame)
    return state
```

### Formatting

We use:
- **black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **flake8** for linting

Run before committing:
```bash
black .
isort .
mypy claude_plays_zelda/
flake8 claude_plays_zelda/
```

## Testing

### Writing Tests

- Write tests for new features
- Use pytest
- Aim for >80% code coverage
- Test edge cases and error conditions

### Example Test

```python
def test_game_state_detector():
    """Test game state detection."""
    detector = GameStateDetector()

    # Create mock frame
    frame = np.zeros((224, 256, 3), dtype=np.uint8)

    # Test detection
    state = detector.get_full_game_state(frame)

    assert "hearts" in state
    assert "rupees" in state
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_config.py

# With coverage
pytest --cov=claude_plays_zelda --cov-report=html
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Format code** with black/isort
5. **Update CHANGELOG** if applicable
6. **Write clear PR description**:
   - What does this change?
   - Why is it needed?
   - How was it tested?

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code formatted with black/isort
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Documentation updated
```

## Areas for Contribution

### High Priority

- 🐛 **Bug Fixes**: Fix known issues
- 📝 **Documentation**: Improve docs and examples
- 🧪 **Tests**: Increase test coverage
- 🎯 **Game Logic**: Improve AI strategies

### Medium Priority

- 🎨 **Computer Vision**: Better detection algorithms
- 🧠 **AI Improvements**: Smarter decision-making
- 📊 **Analytics**: Better statistics and tracking
- 🎮 **Emulator Support**: Additional emulators

### Lower Priority

- 🌐 **Web Dashboard**: Real-time monitoring UI
- 📹 **Streaming**: Twitch integration
- 🎬 **Highlights**: Automated clip generation
- 🗣️ **Commentary**: Voice generation

## Adding New Features

### New Vision Feature

1. Add to `claude_plays_zelda/vision/`
2. Implement class with clear interface
3. Add tests in `tests/`
4. Update orchestrator to use it
5. Document in README

### New Game Logic

1. Add to `claude_plays_zelda/game/`
2. Follow existing patterns
3. Integrate with game knowledge base
4. Add strategy tests
5. Update AI agent to use it

### New AI Strategy

1. Modify `claude_plays_zelda/ai/`
2. Update prompts if needed
3. Add to action planner
4. Test with actual gameplay
5. Document strategy

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.

    Longer description if needed. Can span multiple
    lines and include examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> function_name("test", 42)
        True
    """
```

### README Updates

When adding features:
- Update feature list
- Add usage examples
- Update architecture section if needed
- Add to roadmap or remove if completed

## Commit Messages

### Format

```
type(scope): short description

Longer description if needed.

Fixes #123
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting changes
- **refactor**: Code refactoring
- **test**: Adding tests
- **chore**: Maintenance tasks

### Examples

```
feat(vision): add enemy health detection

Implements health bar detection for enemies using
color-based segmentation.

Closes #45
```

```
fix(emulator): resolve window focus issue on macOS

Window focus was failing on macOS due to missing
permissions check.

Fixes #67
```

## Review Process

1. **Automated checks** run on PR
2. **Maintainer review** (usually within 3-7 days)
3. **Changes requested** if needed
4. **Approval** when ready
5. **Merge** by maintainer

## Questions?

- Check [README](README.md)
- Check [Setup Guide](SETUP_GUIDE.md)
- Open an [Issue](https://github.com/clduab11/claude-plays-zelda/issues)
- Start a [Discussion](https://github.com/clduab11/claude-plays-zelda/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎮🙏
