#!/usr/bin/env bash
# install.sh - Install vexy-vid in editable mode
# Vexy Vid: High-performance video cropping and trimming CLI tool with automatic detection.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing vexy-vid in editable mode..."
uv pip install --system -e .

echo "==> Install complete."
