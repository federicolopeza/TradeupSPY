# PowerShell bootstrap for development environment
# Creates venv, installs deps, and sets up pre-commit

param(
    [string]$Python = "python",
    [switch]$NoPreCommit
)

$ErrorActionPreference = 'Stop'

# Create venv
& $Python -m venv .venv

# Activate
$venvActivate = Join-Path .venv 'Scripts\Activate.ps1'
. $venvActivate

# Upgrade pip
python -m pip install --upgrade pip wheel setuptools

# Install project (dev extras)
pip install -e .[dev]

if (-not $NoPreCommit) {
    pre-commit install
}

Write-Host "Bootstrap completo. Activa el entorno con: .\.venv\Scripts\Activate.ps1"
