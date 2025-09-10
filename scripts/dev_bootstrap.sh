#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"

# Create venv
$PYTHON_BIN -m venv .venv
# Activate
source .venv/bin/activate

# Upgrade tooling
python -m pip install --upgrade pip wheel setuptools

# Install project (dev)
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

echo "Bootstrap completo. Activá el entorno con: source .venv/bin/activate"
