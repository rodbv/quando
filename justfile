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

# Bump version (usage: just bump VERSION=0.1.1)
bump VERSION:
	uv run bumpver update --set-version {{VERSION}}



# Release to PyPI via GitHub Actions (usage: just release VERSION=0.2.1)
release VERSION:
	uv run bumpver update --set-version {{VERSION}}
	git add pyproject.toml
	git commit -m "Release v{{VERSION}}"
	git tag v{{VERSION}}
	git push
	git push origin v{{VERSION}}
