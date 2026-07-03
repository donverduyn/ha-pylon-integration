#!/usr/bin/env bash
# Remove Python/pytest/ruff cache artifacts from the repo tree.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -not -path "./.git/*" -prune -exec rm -rf {} +

echo "Removing *.pyc / *.pyo files..."
find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./.git/*" -delete

echo "Removing .pytest_cache..."
rm -rf .pytest_cache

echo "Removing .ruff_cache..."
rm -rf .ruff_cache

echo "Removing .mypy_cache..."
rm -rf .mypy_cache

echo "Removing coverage artifacts..."
rm -rf .coverage .coverage.* coverage.xml htmlcov coverage_annotated

echo "Done."
