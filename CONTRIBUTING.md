# Contributing to Claude Plays Zelda

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/claude-plays-zelda.git
cd claude-plays-zelda
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

4. **Set up pre-commit hooks** (optional)
```bash
pip install pre-commit
pre-commit install
```

## Project Structure

```
claude-plays-zelda/
├── src/
│   ├── emulator/      # Emulator control
│   ├── cv/            # Computer vision
│   ├── agent/         # AI agent (Claude)
│   ├── game/          # Game logic
│   └── streaming/     # Dashboard & stats
├── tests/
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── config.yaml        # Configuration
└── main.py           # Entry point
```

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists
2. Include:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe:
   - Use case
   - Proposed solution
   - Alternative approaches considered

### Pull Requests

1. **Create a branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Follow the coding style (PEP 8)
   - Add tests for new features
   - Update documentation

3. **Run tests**
```bash
pytest tests/
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add new feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Formatting
- `chore:` - Maintenance

5. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Add docstrings for public methods
- Maximum line length: 100 characters

```python
def example_function(param: str, optional: int = 0) -> bool:
    """
    Brief description.

    Args:
        param: Description of param
        optional: Description of optional param

    Returns:
        Description of return value
    """
    return True
```

### Testing

- Write tests for new features
- Aim for >80% code coverage
- Use descriptive test names

```python
def test_action_planner_parses_move_up_correctly():
    """Test that action planner correctly parses 'move_up' command."""
    planner = ActionPlanner(mock_controller)
    action = planner.parse_action("move_up")
    assert action.action_type == ActionType.MOVE_UP
```

### Documentation

- Update README for user-facing changes
- Add docstrings for new modules/classes
- Include code examples where helpful

## Areas for Contribution

### Easy (Good First Issues)

- Add more unit tests
- Improve documentation
- Fix typos
- Add code comments

### Medium

- Enhance object detection accuracy
- Improve puzzle-solving algorithms
- Add new combat strategies
- Optimize performance

### Advanced

- Implement Twitch streaming
- Add ML-based object detection
- Multi-game support
- Speedrun optimization mode

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_action_planner.py

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Verbose output
pytest tests/ -v
```

### Writing Tests

1. **Unit Tests** - Test individual components
   - Location: `tests/unit/`
   - Use mocks for dependencies
   - Fast execution

2. **Integration Tests** - Test component interactions
   - Location: `tests/integration/`
   - May require setup/teardown
   - Slower execution

## Code Review Process

1. **Automated checks must pass**
   - Tests
   - Linting
   - Code coverage

2. **Review criteria**
   - Code quality
   - Test coverage
   - Documentation
   - Performance impact

3. **Response time**
   - We aim to review PRs within 3-5 days
   - Be patient and responsive to feedback

## Getting Help

- **Discord**: [Join our server](https://discord.gg/example)
- **GitHub Discussions**: For questions and ideas
- **Issues**: For bugs and feature requests

## Recognition

Contributors will be:
- Listed in the README
- Mentioned in release notes
- Credited in documentation

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

**Positive behavior:**
- Using welcoming language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior:**
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other unethical or unprofessional conduct

### Enforcement

Instances of abusive behavior may be reported to project maintainers. All complaints will be reviewed and investigated.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Claude Plays Zelda!** 🎮✨
