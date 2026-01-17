# AGENTS.md - Qwen Code Proxy Development Guidelines

## Project Overview
Qwen Code Proxy is a lightweight, Dockerized middleware that allows using the Claude Code CLI and Opencode with the Qwen3-Coder-Plus backend via a LiteLLM proxy.

## Build Commands
- `uv sync` - Install dependencies from pyproject.toml and uv.lock
- `uv run python main.py` - Run the proxy directly for development
- `docker build .` - Build Docker image
- `docker compose up -d` - Start the proxy in production mode
- `QWEN_LOG_LEVEL=DEBUG uv run python main.py` - Run with debug logging

## Test Commands
- Since no dedicated test framework is configured, run manual tests by:
  - Starting the proxy locally: `uv run python main.py`
  - Testing with Claude CLI: `claude "test prompt"`
  - Testing with Opencode CLI: `opencode "test prompt"`
  - Using curl to test the proxy endpoint directly

## Single Test Execution
Currently no unit tests exist, but to test individual components:
- Test authentication: `python -c "from auth import get_api_key; print(get_api_key())"`
- Test configuration: `python -c "from config import get_settings; print(get_settings())"`

## Lint Commands
- `uv run ruff check .` - Check for code style issues
- `uv run ruff format .` - Format code according to standards
- `uv run mypy .` - Run type checking

## Code Style Guidelines

### Imports
- Import standard library modules first (alphabetically)
- Then third-party libraries
- Finally, local application modules
- Use explicit imports when possible: `from module import function`
- Group related imports and separate groups with blank lines

### Formatting
- Follow PEP 8 standards
- Use 4 space indentation
- Max line length of 88 characters (though 100 is acceptable for longer lines)
- Use double quotes for strings unless single quotes improve readability
- Use f-strings for string formatting

### Type Hints
- Use type hints for all function signatures
- Include return type annotations
- Use Union types like `str | None` instead of `Optional[str]`
- Use `typing` module for complex generic types

### Naming Conventions
- Use snake_case for functions, variables, and attributes
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Prefix private attributes/methods with underscore
- Use descriptive names that clearly indicate purpose

### Error Handling
- Use specific exception types when catching errors
- Log errors with appropriate severity levels using Python's logging module
- Validate inputs early and fail fast
- Provide meaningful error messages that help with debugging
- Handle permission and file not found errors appropriately

### Documentation
- Include docstrings for all public methods and classes using triple quotes
- Use Google-style or Sphinx-style docstrings with Args, Returns, and Raises sections
- Document complex logic with inline comments
- Use type hints instead of documenting types in docstrings when possible

### Security Considerings
- Use subprocess.Popen with parameter lists instead of shell=True to prevent injection
- Sanitize and validate all external inputs
- Mark security-sensitive code sections with # noqa: S603 where appropriate
- Use environment variables for sensitive configuration

### Architecture Patterns
- Use Pydantic for configuration management with validation
- Implement thread-safe caching for frequently accessed resources
- Follow separation of concerns with dedicated modules (auth, config, main)
- Use signal handlers for graceful shutdown procedures
- Implement retry logic for resilient operation

### Classes and Methods
- Keep methods focused on a single responsibility
- Use property decorators for computed attributes
- Implement context managers when managing resources
- Follow the constructor pattern of initializing attributes first

### Dependencies
- All dependencies should be declared in pyproject.toml
- Use uv for dependency management
- Keep the dependency footprint minimal
- Pin major versions but allow minor/patch updates where possible

## Development Workflow
1. Install dependencies: `uv sync`
2. Make changes to the code
3. Run the proxy locally to test: `uv run python main.py`
4. Format code: `uv run ruff format .`
5. Check types: `uv run mypy .`
6. Run linter: `uv run ruff check .`
7. Commit changes following conventional commit messages