# AGENTS.md

## Python Environment & Package Management
- Use `uv` for all Python package management and virtual environment operations.
- To create a virtual environment: `uv venv .venv`
- To install dependencies: `uv pip install -r requirements.txt` or `uv pip install <package>`
- To run commands, use `uv run <command>` (no manual activation needed).

## Testing
- Run tests with `uv run pytest`.
- Example:
  ```sh
  uv venv .venv
  uv pip install pytest
  uv run pytest tests/
  ```

## Linting & Formatting
- Pre-commit hooks are configured with ruff and basic hygiene hooks. Install with:
  ```sh
  uv run pre-commit install
  uv run pre-commit run --all-files
  ```
- Ruff can also be run manually:
  ```sh
  uv pip install ruff
  uv run ruff check quando/
  uv run ruff format quando/
  ```

## General Guidelines
- Do not commit files listed in `.gitignore`.
- Keep dependencies minimal and documented in `pyproject.toml`.
- Use the provided pre-commit hooks for code quality.
- Use `uv` for all Python dependency and environment management.
