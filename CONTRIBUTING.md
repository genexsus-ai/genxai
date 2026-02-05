# Contributing to GenXAI

Thank you for your interest in contributing to GenXAI! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs
- Include detailed description and steps to reproduce
- Provide system information (OS, Python version, etc.)
- Include relevant code snippets or error messages

### Suggesting Features

- Open a GitHub Issue with the "enhancement" label
- Describe the feature and its use case
- Explain how it aligns with GenXAI's goals

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Update documentation
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📋 Development Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend development)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/irsal2012/GenXAI.git
cd GenXAI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (core)
pip install -e ".[dev,llm,storage,tools,api]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=genxai --cov-report=html

# Run specific test file
pytest tests/unit/test_graph.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black genxai/

# Lint code
ruff check genxai/

# Type check
mypy genxai/

# Run all checks
black genxai/ && ruff check genxai/ && mypy genxai/ && pytest
```

## 📝 Code Standards

### Python Code

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public APIs
- Keep functions focused and small
- Use meaningful variable names

### Example:

```python
async def process_task(task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Process a task with given context.
    
    Args:
        task: Task description
        context: Execution context
        
    Returns:
        Processing result
        
    Raises:
        ValueError: If task is invalid
    """
    # Implementation
    pass
```

### TypeScript Code

- Follow ESLint configuration
- Use TypeScript strict mode
- Define interfaces for all data structures
- Use functional components with hooks

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Example:
```
feat(tools): Add web scraper tool

Implemented WebScraperTool with BeautifulSoup integration.
Supports CSS selectors and link extraction.

Closes #123
```

## 🏗️ Project Structure

```
genxai/
├── genxai/              # Core framework
│   ├── core/           # Core components
│   ├── tools/          # Tool system
│   ├── llm/            # LLM providers
│   ├── observability/  # Logging & metrics (enterprise)
├── enterprise/         # Enterprise modules (studio, cli, connectors, triggers)
│   ├── backend/        # FastAPI backend
│   └── frontend/       # React frontend
├── tests/              # Tests
├── examples/           # Examples
└── docs/               # Documentation
```

## 🧪 Testing Guidelines

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Aim for 80%+ coverage
- Use descriptive test names

```python
def test_agent_creation_with_valid_config():
    """Test that agent is created successfully with valid config."""
    config = AgentConfig(role="Assistant", goal="Help users")
    agent = Agent(id="test", config=config)
    assert agent.id == "test"
    assert agent.config.role == "Assistant"
```

### Integration Tests

- Test component interactions
- Use test databases/services
- Clean up after tests

### End-to-End Tests

- Test complete workflows
- Validate user scenarios
- Use realistic data

## 📚 Documentation

### Code Documentation

- Write docstrings for all public APIs
- Include examples in docstrings
- Document parameters and return values
- Note any exceptions raised

### User Documentation

- Update relevant .md files
- Add examples for new features
- Keep documentation in sync with code

## 🔍 Code Review Process

All contributions go through code review:

1. **Automated Checks**: CI pipeline runs tests and linting
2. **Peer Review**: At least one maintainer reviews the code
3. **Discussion**: Address feedback and questions
4. **Approval**: Maintainer approves the PR
5. **Merge**: Code is merged to main branch

### Review Criteria

- Code quality and style
- Test coverage
- Documentation completeness
- Performance impact
- Breaking changes (if any)

## 🚀 Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## 💡 Areas for Contribution

### High Priority

- Additional built-in tools (web, database, communication)
- Long-term memory with vector DB integration
- Episodic memory with graph DB
- More LLM providers (Anthropic, Google, Cohere)
- Graph editor UI component
- Agent designer UI component

### Medium Priority

- Performance optimizations
- Additional examples
- Tutorial videos
- Integration guides
- Deployment guides

### Low Priority

- Additional agent types
- Advanced communication patterns
- Workflow templates
- Tool marketplace

## 🤔 Questions?

- Open a GitHub Discussion
- Join our Discord community
- Check existing issues and PRs

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🙏 Thank You!

Your contributions make GenXAI better for everyone. We appreciate your time and effort!

---

**Happy Contributing!** 🎉
