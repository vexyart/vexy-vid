#!/usr/bin/env bash
# publish.sh - Build, version, and publish vexy-vid
# Vexy Vid: High-performance video cropping and trimming CLI tool with automatic detection.
# Calls build.sh + install.sh, bumps version with gitnextver, then publishes to PyPI.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Running build..."
"$SCRIPT_DIR/build.sh"

echo "==> Running install..."
"$SCRIPT_DIR/install.sh"

echo "==> Bumping version with gitnextver..."
uvx gitnextver@latest

echo "==> Building distribution..."
uvx hatch build

echo "==> Publishing to PyPI..."
uv publish

echo "==> Publish complete."
