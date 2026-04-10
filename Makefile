.PHONY: install run test lint format typecheck clean

install:
	uv sync --extra dev

run:
	uv run elevator-sim input/sample_requests2.csv --elevators 15

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist
