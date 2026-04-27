# Common development commands for quando

# Setup virtual environment
venv:
	uv venv .venv

# Install dependencies
install:
	uv sync

# Run all tests (accepts extra args)
test *ARGS:
	uv run pytest tests/ {{ARGS}}

# Run all pre-commit hooks
lint:
	uv run pre-commit run --all-files

# Run Ruff linter
ruff:
	uv run ruff check quando/

# Run Ruff formatter
format:
	uv run ruff format quando/
