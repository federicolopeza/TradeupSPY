PY=python
PIP=$(PY) -m pip

.PHONY: install dev test lint fmt precommit

install:
	$(PIP) install -e .

dev:
	$(PIP) install -e .[dev]

fmt:
	$(PY) -m black cs2_local_prices tests

lint:
	$(PY) -m ruff check cs2_local_prices tests
	$(PY) -m mypy cs2_local_prices

precommit:
	pre-commit install

test:
	$(PY) -m pytest -q
